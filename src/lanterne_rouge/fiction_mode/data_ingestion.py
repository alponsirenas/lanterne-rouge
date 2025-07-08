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

        moving_time = activity.get('moving_time', 0)
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
            duration_seconds=validated_activity.get('moving_time', 0),
            distance_meters=validated_activity.get('distance', 0),
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
        """Scrape stage report from letour.fr"""

        # For now, return mock data based on the real stage 3 report we fetched
        # In full implementation, this would scrape dynamically

        stage_reports = {
            1: """
            Stage 1: Lille Métropole > Boulogne-sur-Mer (186km)

            The opening stage of the 2025 Tour de France delivered the expected sprint finish,
            with Jasper Philipsen (Alpecin-Deceuninck) taking his first opening stage victory.

            Early break formed at km 15 with 4 riders getting clear: Pacher, Bouchard, Declercq, and Mollema.
            They built a maximum gap of 3'20" before being steadily reeled in by the peloton.

            The break was caught with 25km to go as the sprint teams organized their trains.
            Final sprint was clean with Philipsen edging Groenewegen in a tight finish.

            Weather: Overcast, 18°C, light winds
            """,

            2: """
            Stage 2: Lauwin-Planque > Mûr-de-Bretagne (199km)

            Mathieu van der Poel (Alpecin-Deceuninck) captured the stage win and yellow jersey
            on the punchy uphill finish to Mûr-de-Bretagne.

            The stage featured two categorized climbs and multiple uncategorized rises.
            A 6-man break escaped early but was controlled throughout by the peloton.

            Van der Poel launched his winning attack with 300m to go on the 2km climb,
            dropping the remaining sprinters and puncheurs.

            Weather: Partly cloudy, 16°C, moderate crosswinds in exposed sections
            """,

            3: """
            Stage 3: Valenciennes > Dunkerque (177km)

            Tim Merlier (Soudal Quick-Step) seized his opportunity as he powered to victory
            in Dunkirk, edging Jonathan Milan (Lidl-Trek) right on the line.

            Without much conviction, Jonas Rickaert moved to the front early, accompanied
            by Matej Mohoric, but they ended their breakaway after less than 10km.

            The intensity picked up approaching the intermediate sprint in Isbergues (km 95.3)
            as Jasper Philipsen stepped on his pedals to defend his green jersey. A contact
            with Bryan Coquard sent Philipsen to the ground at high speed, forcing him to retire.

            Tim Wellens attacked ahead of Mont Cassel (km 147.4) to chase the KOM point,
            building a gap of 1'45" before being caught with 27km to go.

            Weather: Clear skies, 19°C, headwind in final kilometers
            """
        }

        return stage_reports.get(stage_number)

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
        """Get top 10 stage results"""

        # Mock results - in full implementation this would scrape live results
        results = {
            1: [
                {'position': '1', 'rider': 'Jasper Philipsen', 'team': 'Alpecin-Deceuninck', 'time': '4h12\'34"'},
                {'position': '2', 'rider': 'Dylan Groenewegen', 'team': 'Jayco-AlUla', 'time': 'ST'},
                {'position': '3', 'rider': 'Arnaud De Lie', 'team': 'Lotto Dstny', 'time': 'ST'},
            ],
            2: [
                {'position': '1', 'rider': 'Mathieu van der Poel', 'team': 'Alpecin-Deceuninck', 'time': '4h45\'23"'},
                {'position': '2', 'rider': 'Wout van Aert', 'team': 'Visma-lease a Bike', 'time': 'ST'},
                {'position': '3', 'rider': 'Mads Pedersen', 'team': 'Lidl-Trek', 'time': 'ST'},
            ],
            3: [
                {'position': '1', 'rider': 'Tim Merlier', 'team': 'Soudal Quick-Step', 'time': '4h01\'15"'},
                {'position': '2', 'rider': 'Jonathan Milan', 'team': 'Lidl-Trek', 'time': 'ST'},
                {'position': '3', 'rider': 'Phil Bauhaus', 'team': 'Bahrain Victorious', 'time': 'ST'},
            ]
        }

        return results.get(stage_number, [])

    def fetch_stage_data(self, stage_number: int, stage_date: datetime) -> Optional[StageRaceData]:
        """Fetch complete race data for a stage"""

        # Get stage report
        stage_report = self.scrape_letour_stage_report(stage_number)
        if not stage_report:
            return None

        # Parse events from report
        events = self.parse_stage_events(stage_report, stage_number)

        # Get results
        results = self.get_stage_results(stage_number)

        # Determine winner and stage type
        winner = results[0]['rider'] if results else 'Unknown'
        winning_team = results[0]['team'] if results else 'Unknown'

        # Classify stage type based on report content
        stage_type = 'flat'  # default
        if 'mountain' in stage_report.lower() or 'climb' in stage_report.lower():
            stage_type = 'hilly'
        if 'sprint' in stage_report.lower():
            stage_type = 'flat'

        # Stage names mapping
        stage_names = {
            1: 'Lille Métropole > Boulogne-sur-Mer',
            2: 'Lauwin-Planque > Mûr-de-Bretagne',
            3: 'Valenciennes > Dunkerque'
        }

        # Stage distances
        stage_distances = {
            1: 186.0,
            2: 199.0,
            3: 177.0
        }

        return StageRaceData(
            stage_number=stage_number,
            stage_name=stage_names.get(stage_number, f'Stage {stage_number}'),
            date=stage_date,
            distance_km=stage_distances.get(stage_number, 180.0),
            stage_type=stage_type,
            winner=winner,
            winning_team=winning_team,
            weather=self._extract_weather(stage_report),
            events=events,
            stage_report=stage_report,
            results_top10=results
        )

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
