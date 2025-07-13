"""
Data Ingestion Agents for Fiction Mode

RideDataIngestionAgent: Fetches and processes user's Strava ride data
RaceDataIngestionAgent: Scrapes and processes official race reports
"""

import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from ..strava_api import strava_get, get_athlete_id
from ..validation import validate_activity_data
from ..ai_clients import call_llm
from ..mission_config import MissionConfig, bootstrap


@dataclass
@dataclass
class RideData:
    """Structured ride data from Strava"""
    activity_id: int
    start_time: datetime
    duration_seconds: int
    distance_meters: float
    avg_power: Optional[float]
    max_power: Optional[float]
    avg_hr: Optional[float]
    max_hr: Optional[float]
    cadence: Optional[float]
    tss: Optional[float]
    intensity_factor: Optional[float]
    activity_name: str
    description: Optional[str]
    high_effort_intervals: List[Dict[str, Any]]
    metadata: Dict[str, Any]


@dataclass
class RaceEvent:
    """Single race event (breakaway, attack, crash, etc.)"""
    time_km: Optional[float]
    time_minutes: Optional[int]
    event_type: str  # 'breakaway', 'attack', 'crash', 'sprint', 'finish'
    description: str
    riders: List[str]


@dataclass
class StageRaceData:
    """Complete race data for a stage"""
    stage_number: int
    stage_name: str
    date: datetime
    distance_km: float
    stage_type: str  # 'flat', 'hilly', 'mountain', 'tt'
    winner: str
    winning_team: str
    weather: Optional[str]
    events: List[RaceEvent]
    stage_report: str
    results_top10: List[Dict[str, str]]


class RideDataIngestionAgent:
    """Fetches and processes user's Strava ride data for Fiction Mode"""

    def __init__(self):
        self.athlete_id = None

    def detect_tdf_activity(self, activity: Dict[str, Any]) -> Optional[int]:
        """
        Detect if an activity is a TDF stage simulation.
        Returns stage number if detected, None otherwise.
        """
        name = activity.get('name', '').lower()
        description = activity.get('description', '').lower() if activity.get('description') else ''

        # Look for stage indicators in name or description
        stage_patterns = [
            r'stage\s*(\d+)',
            r'tdf\s*stage\s*(\d+)',
            r'tour\s*de\s*france\s*stage\s*(\d+)',
            r'#tdf2025\s*stage\s*(\d+)',
            r'étape\s*(\d+)'
        ]

        for pattern in stage_patterns:
            match = re.search(pattern, name + ' ' + description)
            if match:
                return int(match.group(1))

        return None

    def extract_effort_intervals(self, activity: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract high-effort intervals from detailed activity streams using LLM analysis.
        Uses actual power/HR data streams for intelligent pattern detection.
        """
        activity_id = activity.get('id')
        if not activity_id:
            return []

        # Get detailed streams data
        stream_types = ['time', 'watts', 'heartrate', 'cadence', 'velocity_smooth']
        streams_param = ','.join(stream_types)
        
        try:
            streams = strava_get(f'activities/{activity_id}/streams?keys={streams_param}&key_by_type=true')
            if not streams or 'time' not in streams:
                return self._fallback_effort_extraction(activity)
            
            # Extract stream data
            time_data = streams['time']['data']
            watts_data = streams.get('watts', {}).get('data', [])
            hr_data = streams.get('heartrate', {}).get('data', [])
            
            if not watts_data and not hr_data:
                return self._fallback_effort_extraction(activity)
            
            # Use LLM to analyze the effort patterns
            intervals = self._analyze_efforts_with_llm(time_data, watts_data, hr_data, activity)
            
            if intervals:
                return intervals
                
        except Exception as e:
            print(f"Failed to get streams data for activity {activity_id}: {e}")
        
        # Fallback to basic analysis
        return self._fallback_effort_extraction(activity)

    def _analyze_efforts_with_llm(self, time_data: List[int], watts_data: List[float], 
                                  hr_data: List[float], activity: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Use LLM to analyze effort patterns from streams data"""
        
        if not time_data:
            return []
        
        # Prepare summary statistics for LLM
        total_minutes = max(time_data) / 60 if time_data else 0
        
        # Calculate power statistics
        power_stats = {}
        if watts_data:
            power_stats = {
                'avg_power': sum(watts_data) / len(watts_data),
                'max_power': max(watts_data),
                'min_power': min(watts_data)
            }
        
        # Calculate HR statistics  
        hr_stats = {}
        if hr_data and any(hr > 0 for hr in hr_data):
            valid_hr = [hr for hr in hr_data if hr > 0]
            if valid_hr:
                hr_stats = {
                    'avg_hr': sum(valid_hr) / len(valid_hr),
                    'max_hr': max(valid_hr),
                    'min_hr': min(valid_hr)
                }
        
        # Create 10-minute segment summaries for LLM analysis
        segment_minutes = 10
        segments = []
        
        for segment_start in range(0, int(total_minutes), segment_minutes):
            segment_end = min(segment_start + segment_minutes, total_minutes)
            segment_indices = [i for i, t in enumerate(time_data) 
                              if segment_start*60 <= t < segment_end*60]
            
            if segment_indices:
                segment_data = {
                    'start_min': segment_start,
                    'end_min': segment_end,
                }
                
                if watts_data:
                    segment_powers = [watts_data[i] for i in segment_indices]
                    segment_data.update({
                        'avg_power': sum(segment_powers) / len(segment_powers),
                        'max_power': max(segment_powers)
                    })
                
                if hr_data:
                    segment_hrs = [hr_data[i] for i in segment_indices if hr_data[i] > 0]
                    if segment_hrs:
                        segment_data.update({
                            'avg_hr': sum(segment_hrs) / len(segment_hrs),
                            'max_hr': max(segment_hrs)
                        })
                
                segments.append(segment_data)
        
        # Build LLM prompt for effort analysis
        effort_prompt = self._build_effort_analysis_prompt(
            activity, power_stats, hr_stats, segments, total_minutes
        )
        
        try:
            messages = [
                {"role": "system", "content": "You are an expert cycling data analyst specializing in effort pattern recognition."},
                {"role": "user", "content": effort_prompt}
            ]
            response = call_llm(messages, model="gpt-4", force_json=True)
            intervals = self._parse_effort_response(response)
            return intervals
            
        except Exception as e:
            print(f"LLM effort analysis failed: {e}")
            return []

    def _build_effort_analysis_prompt(self, activity: Dict[str, Any], power_stats: Dict, 
                                     hr_stats: Dict, segments: List[Dict], total_minutes: float) -> str:
        """Build prompt for LLM effort interval analysis"""
        
        activity_name = activity.get('name', 'Unknown')
        
        prompt = f"""You are the Ride Data Ingestion Agent for Fiction Mode cycling narratives.

TASK: Analyze this ride's effort patterns to identify key intervals for narrative purposes.

ACTIVITY: {activity_name}
DURATION: {total_minutes:.1f} minutes

OVERALL STATS:"""
        
        if power_stats:
            prompt += f"""
POWER: Avg {power_stats['avg_power']:.0f}W, Max {power_stats['max_power']:.0f}W"""
        
        if hr_stats:
            prompt += f"""
HEART RATE: Avg {hr_stats['avg_hr']:.0f}bpm, Max {hr_stats['max_hr']:.0f}bpm"""
        
        prompt += f"""

10-MINUTE SEGMENTS:"""
        
        for segment in segments:
            prompt += f"""
{segment['start_min']}-{segment['end_min']}min:"""
            if 'avg_power' in segment:
                prompt += f" Power {segment['avg_power']:.0f}W (max {segment['max_power']:.0f}W)"
            if 'avg_hr' in segment:
                prompt += f" HR {segment['avg_hr']:.0f}bpm (max {segment['max_hr']:.0f}bpm)"
        
        prompt += f"""

INSTRUCTIONS:
1. Identify 2-5 significant effort intervals that could represent race events
2. Look for power/HR surges, sustained efforts, or tactical moments
3. Consider the activity name for context (TDF stage simulation, training, etc.)
4. Each interval should be meaningful for cycling narrative purposes

Respond with JSON array:
[
  {{
    "start_minute": 25.5,
    "duration_minutes": 2.3,
    "avg_power": 105,
    "max_power": 114,
    "avg_hr": 145,
    "effort_type": "surge",
    "description": "Mid-ride power surge - possible attack response"
  }}
]

Effort types: surge, sustained, recovery, sprint, climb, tempo
Focus on intervals that tell a story about the rider's tactical choices."""
        
        return prompt

    def _parse_effort_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse LLM response into effort interval objects"""
        import json
        import re
        
        intervals = []
        
        try:
            # Extract JSON from response
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                intervals_data = json.loads(json_match.group())
                
                for interval_data in intervals_data:
                    intervals.append({
                        'start_minute': interval_data.get('start_minute', 0),
                        'duration_minutes': interval_data.get('duration_minutes', 1),
                        'avg_power': interval_data.get('avg_power'),
                        'max_power': interval_data.get('max_power'),
                        'avg_hr': interval_data.get('avg_hr'),
                        'effort_type': interval_data.get('effort_type', 'effort'),
                        'description': interval_data.get('description', 'Effort interval')
                    })
        
        except Exception as e:
            print(f"Failed to parse LLM effort response: {e}")
        
        return intervals

    def _fallback_effort_extraction(self, activity: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fallback effort extraction using basic activity summary data"""
        intervals = []

        moving_time = activity.get('moving_time', 0) or 0
        avg_power = activity.get('average_watts')
        max_power = activity.get('max_watts')

        if moving_time > 1800:  # 30+ min rides
            total_minutes = moving_time / 60

            # Create basic intervals for longer rides
            if total_minutes > 45:
                intervals = [
                    {
                        'start_minute': total_minutes * 0.25,
                        'duration_minutes': 3,
                        'avg_power': max_power * 0.8 if max_power else None,
                        'description': 'Early effort period'
                    },
                    {
                        'start_minute': total_minutes * 0.65,
                        'duration_minutes': 5,
                        'avg_power': max_power * 0.9 if max_power else None,
                        'description': 'Late-ride push'
                    }
                ]

        return intervals

    def fetch_ride_data(self, activity_id: int) -> Optional[RideData]:
        """Fetch detailed ride data for a specific activity"""

        # Get detailed activity data
        activity = strava_get(f"activities/{activity_id}")
        if not activity:
            return None

        # Validate the activity data
        validated_activity = validate_activity_data(activity)

        # Parse start time
        start_time_str = activity.get('start_date_local', '')
        try:
            start_time = datetime.fromisoformat(start_time_str.replace('Z', ''))
        except Exception:
            start_time = datetime.now()

        # Extract effort intervals
        intervals = self.extract_effort_intervals(validated_activity)

        return RideData(
            activity_id=activity['id'],
            start_time=start_time,
            duration_seconds=validated_activity.get('moving_time') or 0,
            distance_meters=validated_activity.get('distance') or 0,
            avg_power=validated_activity.get('average_watts'),
            max_power=validated_activity.get('max_watts'),
            avg_hr=validated_activity.get('average_heartrate'),
            max_hr=validated_activity.get('max_heartrate'),
            cadence=validated_activity.get('average_cadence'),
            tss=validated_activity.get('suffer_score'),  # Strava's TSS equivalent
            intensity_factor=validated_activity.get('intensity_factor'),
            activity_name=activity.get('name', ''),
            description=activity.get('description'),
            high_effort_intervals=intervals,
            metadata={
                'sport_type': activity.get('sport_type'),
                'trainer': activity.get('trainer', False),
                'commute': activity.get('commute', False),
                'total_elevation_gain': validated_activity.get('total_elevation_gain', 0)
            }
        )

    def find_todays_tdf_ride(self) -> Optional[RideData]:
        """Find today's TDF simulation ride"""

        # Get recent activities
        activities = strava_get("athlete/activities?per_page=20")
        if not activities:
            return None

        today = datetime.now().date()

        for activity in activities:
            # Check if it's today's activity
            start_time_str = activity.get('start_date_local', '')
            try:
                activity_date = datetime.fromisoformat(start_time_str.replace('Z', '')).date()
                if activity_date != today:
                    continue
            except Exception:
                continue

            # Check if it's a cycling activity
            if activity.get('sport_type') not in ['Ride', 'VirtualRide']:
                continue

            # Check minimum duration (30 minutes)
            if activity.get('moving_time', 0) < 1800:
                continue

            # Check if it's a TDF stage
            stage_num = self.detect_tdf_activity(activity)
            if stage_num:
                return self.fetch_ride_data(activity['id'])

        return None


class RaceDataIngestionAgent:
    """Scrapes and processes official race reports from letour.fr and other sources"""

    def __init__(self):
        self.base_urls = {
            'letour': 'https://www.letour.fr/en',
            'procyclingstats': 'https://www.procyclingstats.com'
        }

    def scrape_letour_stage_report(self, stage_number: int, year: int = 2025) -> Optional[str]:
        """Fetch stage report from letour.fr using intelligent URL discovery"""
        
        try:
            print(f"Fetching stage {stage_number} report from official letour.fr...")
            
            # Step 1: Try to use fetch_webpage tool if available (best approach)
            content = self._try_fetch_webpage_tool(stage_number, year)
            if content:
                print(f"✅ Successfully fetched stage {stage_number} report using fetch_webpage tool")
                return content
            
            # Step 2: Use the base pattern we know works with intelligent discovery
            base_url = f"https://www.letour.fr/en/news/{year}/stage-{stage_number}"
            
            stage_content = self._fetch_stage_content_with_discovery(base_url, stage_number, year)
            if stage_content:
                print(f"✅ Successfully fetched stage {stage_number} report from letour.fr")
                return stage_content
            
            print(f"❌ Could not fetch stage {stage_number} report from letour.fr")
            return None
            
        except Exception as e:
            print(f"Failed to fetch stage report for stage {stage_number}: {e}")
            return None

    def _fetch_stage_content_with_discovery(self, base_url: str, stage_number: int, year: int) -> Optional[str]:
        """Use LLM-based approach to discover and fetch the correct stage URL"""
        
        # This method will use the fetch_webpage tool when available in the runtime context
        # For now, we implement a pattern-based approach with intelligent fallbacks
        
        try:
            # Try the base URL pattern first
            import requests
            from bs4 import BeautifulSoup
            
            response = requests.get(base_url, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Check if this is a valid stage page or a listing page
                text_content = soup.get_text()
                
                # If it's a listing page, try to find the actual stage article link
                if "stage" in text_content.lower() and str(stage_number) in text_content:
                    # Look for links to the actual stage report
                    links = soup.find_all('a', href=True)
                    
                    for link in links:
                        href = link.get('href', '')
                        link_text = link.get_text().lower()
                        
                        # Look for stage-specific article links
                        if (f'stage-{stage_number}' in href or 
                            (f'stage {stage_number}' in link_text and len(link_text) > 10)):
                            
                            # Construct full URL if relative
                            if href.startswith('/'):
                                article_url = f"https://www.letour.fr{href}"
                            else:
                                article_url = href
                            
                            # Fetch the actual article
                            try:
                                article_response = requests.get(article_url, timeout=10)
                                if article_response.status_code == 200:
                                    article_soup = BeautifulSoup(article_response.content, 'html.parser')
                                    article_text = article_soup.get_text()
                                    
                                    if len(article_text.strip()) > 1000:
                                        print(f"✅ Found stage article at: {article_url}")
                                        return article_text
                                        
                            except Exception as e:
                                print(f"Failed to fetch article from {article_url}: {e}")
                                continue
                
                # If direct page has good content, return it
                if len(text_content.strip()) > 1000:
                    return text_content
                    
        except Exception as e:
            print(f"Content discovery failed: {e}")
        
        return None

    def parse_stage_events(self, stage_report: str, stage_number: int) -> List[RaceEvent]:
        """Parse stage report text to extract key events using LLM intelligence"""

        if not stage_report or not stage_report.strip():
            return self._fallback_stage_events(stage_number)

        # Use LLM to intelligently extract race events
        events_prompt = self._build_events_extraction_prompt(stage_report, stage_number)
        
        try:
            messages = [
                {"role": "system", "content": "You are an expert cycling race analyst who extracts key events from race reports."},
                {"role": "user", "content": events_prompt}
            ]
            response = call_llm(messages, model="gpt-4", force_json=True)
            events = self._parse_events_response(response)
            
            if events:
                return events
        
        except Exception as e:
            print(f"LLM event extraction failed, using fallback: {e}")
        
        # Fallback to rule-based parsing
        return self._fallback_stage_events(stage_number)

    def _build_events_extraction_prompt(self, stage_report: str, stage_number: int) -> str:
        """Build prompt for LLM race event extraction"""
        
        prompt = f"""You are the Race Data Ingestion Agent for Fiction Mode cycling narratives.

TASK: Extract key race events from this stage report for narrative purposes.

STAGE REPORT:
{stage_report[:2000]}  # Limit text length

INSTRUCTIONS:
1. Identify key race events: breakaways, attacks, crashes, sprints, climbs, etc.
2. Extract timing information (km markers or time) when available
3. Note important riders involved
4. Focus on dramatic moments suitable for narrative

Respond with JSON array format:
[
  {{
    "time_km": 45.5,
    "time_minutes": null,
    "event_type": "breakaway",
    "description": "Five riders escape: Pacher, Bouchard, Declercq break clear",
    "riders": ["Pacher", "Bouchard", "Declercq"]
  }},
  {{
    "time_km": null,
    "time_minutes": 180,
    "event_type": "attack",
    "description": "Pogačar attacks on the final climb",
    "riders": ["Pogačar"]
  }}
]

Event types: breakaway, attack, crash, sprint, climb, catch, finish
Extract maximum 8 key events for narrative focus."""
        
        return prompt

    def _parse_events_response(self, response: str) -> List[RaceEvent]:
        """Parse LLM response into RaceEvent objects"""
        import json
        import re
        
        events = []
        
        try:
            # Extract JSON from response
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                events_data = json.loads(json_match.group())
                
                for event_data in events_data:
                    events.append(RaceEvent(
                        time_km=event_data.get('time_km'),
                        time_minutes=event_data.get('time_minutes'), 
                        event_type=event_data.get('event_type', 'race_action'),
                        description=event_data.get('description', 'Race event occurred'),
                        riders=event_data.get('riders', [])
                    ))
        
        except Exception as e:
            print(f"Failed to parse LLM events response: {e}")
        
        return events

    def _fallback_stage_events(self, stage_number: int) -> List[RaceEvent]:
        """Fallback rule-based event generation when LLM fails"""
        
        events = []

        # Generate some basic events based on stage number patterns
        if stage_number <= 3:  # Early stages - sprints
            events.extend([
                RaceEvent(
                    time_km=15.0,
                    time_minutes=None,
                    event_type='breakaway',
                    description='Early breakaway formation with 3-4 riders',
                    riders=['Breakaway riders']
                ),
                RaceEvent(
                    time_km=None,
                    time_minutes=None,
                    event_type='sprint',
                    description='Bunch sprint finish',
                    riders=[]
                )
            ])
        elif stage_number >= 15:  # Mountain stages
            events.extend([
                RaceEvent(
                    time_km=50.0,
                    time_minutes=None,
                    event_type='attack',
                    description='GC contenders attack on the climb',
                    riders=['GC riders']
                ),
                RaceEvent(
                    time_km=None,
                    time_minutes=None,
                    event_type='finish',
                    description='Mountain stage finish',
                    riders=[]
                )
            ])
        else:  # Mid-stage variety
            events.extend([
                RaceEvent(
                    time_km=25.0,
                    time_minutes=None,
                    event_type='breakaway',
                    description='Day-long breakaway establishes',
                    riders=['Break riders']
                ),
                RaceEvent(
                    time_km=None,
                    time_minutes=None,
                    event_type='catch',
                    description='Peloton controls and catches the break',
                    riders=[]
                )
            ])

        return events

    def get_stage_results(self, stage_number: int) -> List[Dict[str, str]]:
        """Get top 10 stage results from official sources"""
        
        try:
            # Construct URLs for stage results
            results_urls = [
                f"https://www.letour.fr/en/rankings/stage-{stage_number}",
                f"https://www.procyclingstats.com/race/tour-de-france/2025/stage-{stage_number}/result",
                f"https://www.cyclingnews.com/races/tour-de-france-2025/stage-{stage_number}/results"
            ]
            
            print(f"Fetching stage {stage_number} results from official sources...")
            
            # Try to use web scraping if available
            try:
                import requests
                from bs4 import BeautifulSoup
                
                for url in results_urls:
                    try:
                        response = requests.get(url, timeout=10)
                        if response.status_code == 200:
                            soup = BeautifulSoup(response.content, 'html.parser')
                            text_content = soup.get_text()
                            if len(text_content.strip()) > 100:
                                # Use LLM to extract structured results
                                results = self._extract_results_with_llm(text_content, stage_number)
                                if results:
                                    print(f"✅ Successfully fetched stage {stage_number} results")
                                    return results
                    except Exception as e:
                        print(f"Failed to fetch results from {url}: {e}")
                        continue
                        
            except ImportError:
                print("Web scraping libraries not available (requests, beautifulsoup4)")
            except Exception as e:
                print(f"Web scraping failed: {e}")
            
            print(f"❌ Could not fetch official stage results for stage {stage_number}")
            return []
            
        except Exception as e:
            print(f"Failed to scrape stage results for stage {stage_number}: {e}")
            return []

    def _extract_results_with_llm(self, results_content: str, stage_number: int) -> List[Dict[str, str]]:
        """Extract structured results from webpage content using LLM"""
        
        # Clean up the content and limit size
        content_text = results_content
        if len(content_text) > 2000:
            # Look for likely results section
            content_text = content_text[:2000]
        
        prompt = f"""Extract the top 10 stage results from this Tour de France 2025 stage {stage_number} webpage.

WEBPAGE CONTENT:
{content_text}

TASK: Find stage results/rankings and return as JSON array:
[
  {{"position": "1", "rider": "Rider Full Name", "team": "Team Name", "time": "0:00"}},
  {{"position": "2", "rider": "Rider Full Name", "team": "Team Name", "time": "+0:05"}},
  {{"position": "3", "rider": "Rider Full Name", "team": "Team Name", "time": "+0:05"}}
]

INSTRUCTIONS:
- Find results/classification section in the content
- Extract rider names, team names, and time gaps
- Winner gets time "0:00", others get "+gap" format
- Return exactly the top 10 if available, fewer if not
- If no results found, return empty array []

Return ONLY valid JSON array, no other text."""

        try:
            messages = [
                {"role": "system", "content": "You are an expert cycling results extractor. Return only valid JSON array."},
                {"role": "user", "content": prompt}
            ]
            response = call_llm(messages, model="gpt-4", force_json=True)
            
            import json
            import re
            
            # Handle empty or whitespace-only responses
            if not response or not response.strip():
                print(f"Empty response from LLM for stage {stage_number} results extraction")
                return []
            
            # Try to extract JSON from response
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                results = json.loads(json_match.group())
            else:
                # Try to parse the entire response as JSON
                try:
                    results = json.loads(response)
                except json.JSONDecodeError:
                    # If response contains text but no valid JSON, it likely means no results found
                    print(f"LLM returned non-JSON response for stage {stage_number}: {response[:100]}...")
                    return []
            
            # Validate that it's a list
            if isinstance(results, list):
                # Validate structure of first result if any exist
                if len(results) > 0 and isinstance(results[0], dict):
                    required_fields = ['position', 'rider', 'team', 'time']
                    if all(field in results[0] for field in required_fields):
                        return results[:10]  # Ensure max 10 results
                elif len(results) == 0:
                    return []  # Empty results is valid
            
            print(f"Invalid results format from LLM for stage {stage_number}")
            return []
                
        except json.JSONDecodeError as e:
            print(f"JSON decode error in results extraction for stage {stage_number}: {e}")
            print(f"Response was: {response[:200] if response else 'None'}...")
            return []
        except Exception as e:
            print(f"Failed to extract results with LLM for stage {stage_number}: {e}")
            return []

    def fetch_stage_data(self, stage_number: int, stage_date: datetime) -> Optional[StageRaceData]:
        """Fetch complete race data for a stage from official sources"""
        
        # Step 1: Try to get stage type from mission config first
        stage_config = self._get_stage_config(stage_number)
        if stage_config:
            print(f"✅ Using stage type from mission config: {stage_config['stage_type']}")
        
        # Step 2: Try to scrape stage report from letour.fr
        stage_report = self.scrape_letour_stage_report(stage_number, 2025)
        if not stage_report:
            print(f"Warning: Could not fetch stage report for stage {stage_number}")
            return None
        
        # Step 3: Extract stage details using LLM from the scraped report
        stage_details = self._extract_stage_details_with_llm(stage_report, stage_number, stage_date)
        if not stage_details:
            print(f"Warning: Could not extract stage details for stage {stage_number}")
            return None
        
        # Step 4: Override stage type with mission config if available
        if stage_config and 'stage_type' in stage_config:
            print(f"🔧 Overriding stage type: {stage_details['stage_type']} → {stage_config['stage_type']}")
            stage_details['stage_type'] = stage_config['stage_type']
        
        # Step 5: Parse events from the report
        events = self.parse_stage_events(stage_report, stage_number)
        
        # Step 6: Get results
        results = self.get_stage_results(stage_number)
        
        return StageRaceData(
            stage_number=stage_number,
            stage_name=stage_details['stage_name'],
            date=stage_date,
            distance_km=stage_details['distance_km'],
            stage_type=stage_details['stage_type'],
            winner=stage_details['winner'],
            winning_team=stage_details['winning_team'],
            weather=stage_details['weather'],
            events=events,
            stage_report=stage_report,
            results_top10=results
        )

    def _extract_stage_details_with_llm(self, stage_report: str, stage_number: int, stage_date: datetime) -> Optional[Dict[str, Any]]:
        """Extract key stage details from scraped report using LLM"""
        
        # Clean up and focus on the most relevant content
        report_text = stage_report
        
        # Look for key sections in letour.fr content
        # Often the stage details are in the page title, headers, or interview content
        lines = report_text.split('\n')
        relevant_lines = []
        
        for line in lines:
            line = line.strip()
            if (len(line) > 10 and 
                any(keyword in line.lower() for keyword in 
                    ['stage', 'étape', 'km', 'victory', 'winner', 'wins', 'beats', 
                     'pogacar', 'vingegaard', 'van der poel', 'philipsen', 'merlier',
                     'amiens', 'rouen', 'lille', 'valenciennes', 'dunkerque'])):
                relevant_lines.append(line)
        
        # Use the most relevant content, limited to reasonable size
        focused_text = '\n'.join(relevant_lines[:50])  # Top 50 relevant lines
        
        if len(focused_text.strip()) < 100:
            # Fallback to a middle section of the full text
            start_pos = len(report_text) // 4
            focused_text = report_text[start_pos:start_pos + 2000]
        
        prompt = f"""You are extracting Tour de France 2025 stage {stage_number} details from letour.fr content.

LETOUR.FR CONTENT:
{focused_text}

CONTEXT: This is from the official letour.fr website for stage {stage_number} on {stage_date.strftime('%Y-%m-%d')}.

TASK: Extract stage information and return as JSON:
{{
  "stage_name": "Start City > Finish City",
  "distance_km": 174.2,
  "stage_type": "flat",
  "winner": "Tadej Pogacar",
  "winning_team": "UAE Team Emirates", 
  "weather": "Clear conditions or null"
}}

EXTRACTION RULES:
- stage_name: Look for city names like "Amiens > Rouen" or similar route format
- distance_km: Look for "174.2 km", "177km", etc. Extract the number
- stage_type: "flat" for sprint stages, "hilly" for punchy, "mountain" for climbs, "tt" for time trial
- winner: Look for names like "Tadej Pogacar", "Mathieu van der Poel", etc.
- winning_team: Look for team names like "UAE Team Emirates", "Alpecin-Deceuninck", etc.
- weather: Extract if mentioned, otherwise null

FALLBACKS if not found:
- stage_name: "Stage {stage_number}"
- distance_km: 175.0
- stage_type: "flat"
- winner: "TBD"
- winning_team: "TBD"
- weather: null

Return ONLY valid JSON."""

        try:
            messages = [
                {"role": "system", "content": "You are an expert at extracting cycling race data from letour.fr content. Focus on concrete details and return only valid JSON."},
                {"role": "user", "content": prompt}
            ]
            response = call_llm(messages, model="gpt-4", force_json=True)
            
            import json
            stage_details = json.loads(response)
            
            # Validate and enhance the data
            if not isinstance(stage_details, dict):
                print(f"Invalid response format for stage {stage_number}")
                return self._fallback_stage_details(stage_number)
            
            # Clean up the extracted data
            if stage_details.get('winner') == 'TBD' and 'pogacar' in focused_text.lower():
                stage_details['winner'] = 'Tadej Pogacar'
                stage_details['winning_team'] = 'UAE Team Emirates'
            elif stage_details.get('winner') == 'TBD' and 'van der poel' in focused_text.lower():
                stage_details['winner'] = 'Mathieu van der Poel'
                stage_details['winning_team'] = 'Alpecin-Deceuninck'
            elif stage_details.get('winner') == 'TBD' and 'philipsen' in focused_text.lower():
                stage_details['winner'] = 'Jasper Philipsen'
                stage_details['winning_team'] = 'Alpecin-Deceuninck'
            
            # Ensure required fields exist with fallbacks
            stage_details.setdefault('stage_name', f'Stage {stage_number}')
            stage_details.setdefault('distance_km', 175.0)
            stage_details.setdefault('stage_type', 'flat')
            stage_details.setdefault('winner', 'TBD')
            stage_details.setdefault('winning_team', 'TBD')
            stage_details.setdefault('weather', None)
            
            return stage_details
                
        except Exception as e:
            print(f"Failed to extract stage details with LLM for stage {stage_number}: {e}")
            return self._fallback_stage_details(stage_number)

    def _fallback_stage_details(self, stage_number: int) -> Dict[str, Any]:
        """Provide fallback stage details when extraction fails"""
        return {
            'stage_name': f'Stage {stage_number}',
            'distance_km': 175.0,
            'stage_type': 'flat',
            'winner': 'TBD',
            'winning_team': 'TBD',
            'weather': None
        }

    def _extract_weather(self, stage_report: str) -> Optional[str]:
        """Extract weather information from stage report"""

        # Look for weather patterns
        weather_patterns = [
            r'Weather:\s*([^\n]+)',
            r'weather:\s*([^\n]+)',
            r'(\d+°C[^.]+)',
        ]

        for pattern in weather_patterns:
            match = re.search(pattern, stage_report, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return None

    def _try_fetch_webpage_tool(self, stage_number: int, year: int = 2025) -> Optional[str]:
        """Use cleaner URL pattern to find stage content"""
        
        try:
            # Use the cleaner URL pattern
            stage_url = f"https://www.letour.fr/en/stage-{stage_number}"
            
            print(f"🔍 Attempting to fetch stage {stage_number} content from: {stage_url}")
            
            # Use the discovery process with the clean URL
            return self._simulate_fetch_webpage_discovery(stage_url, stage_number, year)
            
        except Exception as e:
            print(f"Clean URL discovery failed: {e}")
            return None

    def _simulate_fetch_webpage_discovery(self, base_url: str, stage_number: int, year: int) -> Optional[str]:
        """Use the clean stage URL pattern and find the stage summary link"""
        
        try:
            import requests
            from bs4 import BeautifulSoup
            
            # Use the cleaner URL pattern: https://www.letour.fr/en/stage-{n}
            stage_url = f"https://www.letour.fr/en/stage-{stage_number}"
            
            print(f"🔍 Fetching stage page: {stage_url}")
            
            # Fetch the main stage page
            response = requests.get(stage_url, timeout=10)
            if response.status_code != 200:
                print(f"❌ Failed to fetch stage page: {response.status_code}")
                return None
                
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for stage summary/report links on the page
            links = soup.find_all('a', href=True)
            
            stage_report_candidates = []
            
            for link in links:
                href = link.get('href', '')
                link_text = link.get_text().lower().strip()
                
                # Look for stage summary/report links
                if any(keyword in link_text for keyword in 
                       ['stage summary', 'summary', 'stage report', 'report', 'stage film', 'the stage']):
                    
                    # Prioritize stage summary and report links
                    priority = 0
                    if 'stage summary' in link_text:
                        priority = 5
                    elif 'summary' in link_text:
                        priority = 4  
                    elif 'stage report' in link_text:
                        priority = 4
                    elif 'report' in link_text:
                        priority = 3
                    elif 'stage film' in link_text:
                        priority = 3
                    else:
                        priority = 2
                    
                    stage_report_candidates.append((priority, href, link_text))
            
            # Sort by priority and try the best candidates
            stage_report_candidates.sort(key=lambda x: x[0], reverse=True)
            
            print(f"🔍 Found {len(stage_report_candidates)} stage report candidates")
            
            for priority, href, link_text in stage_report_candidates[:3]:  # Try top 3
                try:
                    # Construct full URL if relative
                    if href.startswith('/'):
                        report_url = f"https://www.letour.fr{href}"
                    elif href.startswith('http'):
                        report_url = href
                    else:
                        continue  # Skip invalid URLs
                    
                    print(f"📄 Trying stage report (priority {priority}): {link_text[:60]}...")
                    print(f"    URL: {report_url}")
                    
                    # Fetch the stage report
                    report_response = requests.get(report_url, timeout=10)
                    if report_response.status_code == 200:
                        report_soup = BeautifulSoup(report_response.content, 'html.parser')
                        report_text = report_soup.get_text()
                        
                        # Check if this looks like a substantial stage report
                        if (len(report_text.strip()) > 1000 and
                            any(keyword in report_text.lower() for keyword in 
                                ['stage', 'race', 'finish', 'winner', 'km', 'distance', 'peloton'])):
                            
                            print(f"✅ Found excellent stage report content: {len(report_text)} characters")
                            return report_text
                        else:
                            print(f"⚠️  Content not substantial enough ({len(report_text)} chars)")
                            
                except Exception as e:
                    print(f"Failed to fetch report from {href}: {e}")
                    continue
            
            # If no stage report found, look for any race-related content on the main stage page
            print(f"📝 No dedicated report found, checking main stage page content...")
            
            base_text = soup.get_text()
            if (len(base_text.strip()) > 1000 and
                any(keyword in base_text.lower() for keyword in 
                    ['stage', 'race', 'finish', 'winner', 'km'])):
                print(f"📝 Using main stage page content as fallback")
                return base_text
                
        except Exception as e:
            print(f"Stage discovery failed: {e}")
        
        return None

    def _get_stage_config(self, stage_number: int) -> Optional[Dict[str, Any]]:
        """Get stage configuration from mission config if available"""
        try:
            # Bootstrap config from the standard mission config path
            config_path = "missions/tdf_sim_2025.toml"
            config = bootstrap(config_path)
            if not config or not config.tdf_simulation:
                return None
            
            tdf_config = config.tdf_simulation
            stages_config = tdf_config.get('stages', {})
            stage_type = stages_config.get(str(stage_number))
            
            if stage_type:
                return {'stage_type': stage_type}
            
            return None
        except Exception as e:
            print(f"Could not load stage config for stage {stage_number}: {e}")
            return None
