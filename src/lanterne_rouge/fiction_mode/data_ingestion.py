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
        Extract high-effort intervals from activity data.
        This is a simplified version - full implementation would analyze
        power/HR streams to detect surges.
        """
        intervals = []

        # Use available summary data to estimate effort periods
        moving_time = activity.get('moving_time', 0)
        avg_power = activity.get('average_watts')
        max_power = activity.get('max_watts')

        if avg_power and max_power and moving_time > 1800:  # 30+ min rides
            # Estimate high-effort periods based on power data
            # This is simplified - real implementation would use streams API
            total_minutes = moving_time / 60

            # Assume 3-5 high effort intervals for typical stage simulation
            if total_minutes > 90:  # Long stage
                intervals = [
                    {
                        'start_minute': 15,
                        'duration_minutes': 5,
                        'avg_power': max_power * 0.85,
                        'description': 'Early breakaway response'
                    },
                    {
                        'start_minute': int(total_minutes * 0.4),
                        'duration_minutes': 8,
                        'avg_power': max_power * 0.90,
                        'description': 'Mid-stage effort'
                    },
                    {
                        'start_minute': int(total_minutes * 0.8),
                        'duration_minutes': 10,
                        'avg_power': max_power * 0.95,
                        'description': 'Final surge'
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
        """Parse stage report text to extract key events"""

        events = []

        # Simple parsing based on common patterns
        # Full implementation would use more sophisticated NLP

        if "break" in stage_report.lower() and "km" in stage_report.lower():
            events.append(RaceEvent(
                time_km=15.0,
                time_minutes=None,
                event_type='breakaway',
                description='Early breakaway formation',
                riders=['Pacher', 'Bouchard', 'Declercq']
            ))

        if "caught" in stage_report.lower():
            events.append(RaceEvent(
                time_km=None,
                time_minutes=None,
                event_type='catch',
                description='Breakaway caught by peloton',
                riders=[]
            ))

        if "sprint" in stage_report.lower():
            events.append(RaceEvent(
                time_km=None,
                time_minutes=None,
                event_type='sprint',
                description='Final sprint finish',
                riders=[]
            ))

        if "crash" in stage_report.lower():
            events.append(RaceEvent(
                time_km=95.3,
                time_minutes=None,
                event_type='crash',
                description='High-speed crash at intermediate sprint',
                riders=['Philipsen', 'Coquard']
            ))

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
