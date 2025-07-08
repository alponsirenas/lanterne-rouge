"""
Analysis & Mapping Agent for Fiction Mode

Maps user's ride data to official stage events and assigns a narrative role.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from .data_ingestion import RideData, StageRaceData, RaceEvent


@dataclass
class MappedEvent:
    """A user effort mapped to a race event"""
    user_minute: int
    race_event: RaceEvent
    user_power: Optional[float]
    user_hr: Optional[float]
    mapping_confidence: float  # 0.0 to 1.0
    narrative_description: str


@dataclass
class RiderRole:
    """User's assigned role for the stage"""
    role_type: str  # 'breakaway', 'peloton', 'domestique', 'chase_group', 'dropped'
    position_in_race: str  # 'front_group', 'main_bunch', 'grupetto', etc.
    tactical_description: str
    effort_level: str  # 'easy', 'moderate', 'hard', 'maximal'


@dataclass
class AnalysisResult:
    """Complete analysis of user's ride mapped to race events"""
    ride_data: RideData
    stage_data: StageRaceData
    rider_role: RiderRole
    mapped_events: List[MappedEvent]
    performance_summary: Dict[str, Any]
    narrative_timeline: List[Dict[str, Any]]


class AnalysisMappingAgent:
    """Maps user ride data to race events and assigns narrative role"""

    def __init__(self):
        self.power_zones = {
            'recovery': (0.0, 0.55),
            'endurance': (0.56, 0.75),
            'tempo': (0.76, 0.90),
            'lactate_threshold': (0.91, 1.05),
            'vo2_max': (1.06, 1.20),
            'anaerobic': (1.21, 1.50),
            'neuromuscular': (1.51, 3.00)
        }

    def analyze_ride_intensity(self, ride_data: RideData) -> Dict[str, Any]:
        """Analyze overall ride intensity and effort distribution"""

        duration_minutes = ride_data.duration_seconds / 60
        avg_power = ride_data.avg_power or 0
        max_power = ride_data.max_power or 0

        # Estimate FTP for power zone calculations (would be from user profile)
        estimated_ftp = avg_power * 1.2 if avg_power > 0 else 250

        # Calculate intensity factor
        if_value = avg_power / estimated_ftp if estimated_ftp > 0 else 0

        # Categorize overall effort
        effort_level = 'easy'
        if if_value > 0.85:
            effort_level = 'maximal'
        elif if_value > 0.75:
            effort_level = 'hard'
        elif if_value > 0.65:
            effort_level = 'moderate'

        # Analyze high-effort intervals
        high_efforts = len([i for i in ride_data.high_effort_intervals
                           if i.get('avg_power', 0) > estimated_ftp * 0.9])

        return {
            'duration_minutes': duration_minutes,
            'estimated_ftp': estimated_ftp,
            'intensity_factor': if_value,
            'effort_level': effort_level,
            'high_effort_count': high_efforts,
            'avg_power_pct_ftp': (avg_power / estimated_ftp * 100) if estimated_ftp > 0 else 0,
            'max_power_pct_ftp': (max_power / estimated_ftp * 100) if estimated_ftp > 0 else 0
        }

    def assign_rider_role(self, ride_analysis: Dict[str, Any], stage_data: StageRaceData) -> RiderRole:
        """Assign user a plausible role in the stage based on their effort"""

        effort_level = ride_analysis['effort_level']
        high_efforts = ride_analysis['high_effort_count']
        duration_minutes = ride_analysis['duration_minutes']
        stage_type = stage_data.stage_type

        # Role assignment logic based on effort pattern and stage type
        if high_efforts >= 3 and effort_level in ['hard', 'maximal']:
            # High effort with multiple surges = breakaway or aggressive racing
            if stage_type == 'flat':
                role_type = 'breakaway'
                position = 'front_group'
                tactical = "joined the early break, working to stay clear"
            else:
                role_type = 'chase_group'
                position = 'front_group'
                tactical = "responded to attacks, tried to bridge to leaders"

        elif effort_level == 'moderate' and high_efforts <= 2:
            # Controlled effort = protected rider in peloton
            role_type = 'peloton'
            position = 'main_bunch'
            tactical = "rode defensively in the peloton, conserving energy"

        elif effort_level == 'hard' and high_efforts == 1:
            # Single big effort = domestique work or sprint lead-out
            if stage_type == 'flat':
                role_type = 'domestique'
                position = 'main_bunch'
                tactical = "worked for the team, setting tempo or protecting leaders"
            else:
                role_type = 'peloton'
                position = 'main_bunch'
                tactical = "followed moves, stayed alert in the bunch"

        elif duration_minutes < 120 or effort_level == 'easy':
            # Short or easy ride = dropped or tactical day
            role_type = 'dropped'
            position = 'grupetto'
            tactical = "struggled with the pace, finished in the gruppetto"

        else:
            # Default: safe in the bunch
            role_type = 'peloton'
            position = 'main_bunch'
            tactical = "stayed attentive in the peloton, finished safely"

        return RiderRole(
            role_type=role_type,
            position_in_race=position,
            tactical_description=tactical,
            effort_level=effort_level
        )

    def map_efforts_to_events(self, ride_data: RideData, stage_data: StageRaceData) -> List[MappedEvent]:
        """Map user's effort intervals to race events"""

        mapped_events = []
        race_events = stage_data.events
        user_intervals = ride_data.high_effort_intervals

        if not race_events or not user_intervals:
            return mapped_events

        # Sort events by time
        race_events_sorted = sorted([e for e in race_events if e.time_km or e.time_minutes],
                                  key=lambda x: x.time_km if x.time_km else x.time_minutes or 0)

        # Map user intervals to race events based on timing
        for i, interval in enumerate(user_intervals):
            user_minute = interval.get('start_minute', 0)

            # Find closest race event (simple mapping)
            if i < len(race_events_sorted):
                race_event = race_events_sorted[i]

                # Calculate mapping confidence based on timing alignment
                confidence = 0.7  # Default medium confidence

                # Create narrative description
                event_desc = race_event.description.lower()
                user_power = interval.get('avg_power', 0)

                if 'breakaway' in event_desc:
                    narrative = f"responded to the breakaway formation, pushing {user_power:.0f}W"
                elif 'attack' in event_desc:
                    narrative = f"followed the attacks, sustaining {user_power:.0f}W for {interval.get('duration_minutes', 0)} minutes"
                elif 'sprint' in event_desc:
                    narrative = f"positioned for the sprint finish, hitting {user_power:.0f}W"
                elif 'crash' in event_desc:
                    narrative = f"navigated around the crash, maintaining {user_power:.0f}W"
                else:
                    narrative = f"responded to race situation with {user_power:.0f}W effort"

                mapped_events.append(MappedEvent(
                    user_minute=user_minute,
                    race_event=race_event,
                    user_power=user_power,
                    user_hr=interval.get('avg_hr'),
                    mapping_confidence=confidence,
                    narrative_description=narrative
                ))

        return mapped_events

    def create_narrative_timeline(self, mapped_events: List[MappedEvent],
                                rider_role: RiderRole,
                                stage_data: StageRaceData) -> List[Dict[str, Any]]:
        """Create a timeline for narrative generation"""

        timeline = []

        # Start of stage
        timeline.append({
            'minute': 0,
            'event': 'Stage start',
            'description': f"The peloton rolls out from {stage_data.stage_name.split(' > ')[0]}",
            'user_action': f"settles into the {rider_role.position_in_race}, {rider_role.tactical_description}",
            'narrative_focus': 'setting, atmosphere, initial positioning'
        })

        # Mapped events
        for mapped_event in sorted(mapped_events, key=lambda x: x.user_minute):
            timeline.append({
                'minute': mapped_event.user_minute,
                'event': mapped_event.race_event.event_type,
                'description': mapped_event.race_event.description,
                'user_action': mapped_event.narrative_description,
                'narrative_focus': 'action, effort, tactical decision'
            })

        # Finish
        finish_description = f"crosses the line in {stage_data.stage_name.split(' > ')[1]}"
        if rider_role.role_type == 'breakaway':
            finish_description = f"fights to the finish, giving everything in {stage_data.stage_name.split(' > ')[1]}"
        elif rider_role.role_type == 'dropped':
            finish_description = f"rolls in with the gruppetto in {stage_data.stage_name.split(' > ')[1]}"

        timeline.append({
            'minute': int((stage_data.distance_km / 40) * 60),  # Estimate finish time
            'event': 'Stage finish',
            'description': f"{stage_data.winner} wins the stage",
            'user_action': finish_description,
            'narrative_focus': 'resolution, reflection, preparation for tomorrow'
        })

        return timeline

    def analyze_and_map(self, ride_data: RideData, stage_data: StageRaceData) -> AnalysisResult:
        """Complete analysis and mapping of ride to stage events"""

        # Analyze ride intensity
        ride_analysis = self.analyze_ride_intensity(ride_data)

        # Assign rider role
        rider_role = self.assign_rider_role(ride_analysis, stage_data)

        # Map efforts to events
        mapped_events = self.map_efforts_to_events(ride_data, stage_data)

        # Create narrative timeline
        timeline = self.create_narrative_timeline(mapped_events, rider_role, stage_data)

        # Performance summary
        performance_summary = {
            **ride_analysis,
            'role_assigned': rider_role.role_type,
            'mapped_events_count': len(mapped_events),
            'stage_type': stage_data.stage_type,
            'weather_conditions': stage_data.weather,
            'key_challenge': self._identify_key_challenge(rider_role, stage_data, mapped_events)
        }

        return AnalysisResult(
            ride_data=ride_data,
            stage_data=stage_data,
            rider_role=rider_role,
            mapped_events=mapped_events,
            performance_summary=performance_summary,
            narrative_timeline=timeline
        )

    def _identify_key_challenge(self, rider_role: RiderRole,
                              stage_data: StageRaceData,
                              mapped_events: List[MappedEvent]) -> str:
        """Identify the key challenge/story arc for the stage"""

        if rider_role.role_type == 'breakaway':
            return "fighting to stay clear of the peloton"
        elif rider_role.role_type == 'dropped':
            return "struggling to make the time cut"
        elif any('crash' in event.race_event.description.lower() for event in mapped_events):
            return "navigating through crashes and chaos"
        elif stage_data.weather and ('wind' in stage_data.weather.lower() or 'rain' in stage_data.weather.lower()):
            return "battling difficult weather conditions"
        elif stage_data.stage_type == 'flat':
            return "surviving the nervous sprint stage"
        else:
            return "staying alert and conserving energy in the bunch"
