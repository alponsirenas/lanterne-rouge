"""
Analysis & Mapping Agent for Fiction Mode

Maps user's ride data to official stage events and assigns a narrative role.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from .data_ingestion import RideData, StageRaceData, RaceEvent
from ..ai_clients import call_llm
from ..validation import calculate_power_metrics
from ..monitor import get_current_ftp


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
        """Analyze overall ride intensity and effort distribution using existing power metrics"""

        # Get current athlete FTP
        ftp = get_current_ftp()
        
        # Convert RideData to activity_data format for calculate_power_metrics
        activity_data = {
            'weighted_average_watts': ride_data.avg_power or 0,
            'duration_minutes': (ride_data.duration_seconds or 0) / 60,
            'max_watts': ride_data.max_power or 0
        }
        
        # Use existing power metrics calculation
        power_metrics = calculate_power_metrics(activity_data, ftp)
        
        # Analyze high-effort intervals
        high_efforts = len([i for i in ride_data.high_effort_intervals
                           if i.get('avg_power', 0) > ftp * 0.9])

        return {
            'duration_minutes': activity_data['duration_minutes'],
            'ftp': ftp,
            'intensity_factor': power_metrics['intensity_factor'],
            'tss': power_metrics['tss'],
            'effort_level': power_metrics['effort_level'],
            'normalized_power': power_metrics['normalized_power'],
            'high_effort_count': high_efforts,
            'avg_power_pct_ftp': (ride_data.avg_power / ftp * 100) if ftp > 0 and ride_data.avg_power else 0,
            'max_power_pct_ftp': (ride_data.max_power / ftp * 100) if ftp > 0 and ride_data.max_power else 0
        }

    def assign_rider_role(self, ride_analysis: Dict[str, Any], stage_data: StageRaceData) -> RiderRole:
        """Assign user a plausible role in the stage based on their effort"""
        
        # Prepare data for LLM analysis
        analysis_prompt = self._build_analysis_prompt(ride_analysis, stage_data)
        
        try:
            messages = [
                {"role": "system", "content": "You are an expert cycling analyst who assigns tactical roles based on rider effort patterns."},
                {"role": "user", "content": analysis_prompt}
            ]
            response = call_llm(messages, model="gpt-4", force_json=True)
            
            # Parse LLM response to extract role assignment
            role_data = self._parse_role_response(response)
            
            return RiderRole(
                role_type=role_data.get('role_type', 'peloton'),
                position_in_race=role_data.get('position', 'main_bunch'),
                tactical_description=role_data.get('tactical', 'rode conservatively in the bunch'),
                effort_level=ride_analysis['effort_level']
            )
            
        except Exception as e:
            # Fallback to rule-based logic if LLM fails
            return self._fallback_role_assignment(ride_analysis, stage_data)
    
    def _build_analysis_prompt(self, ride_analysis: Dict[str, Any], stage_data: StageRaceData) -> str:
        """Build prompt for LLM role assignment using documented prompt"""
        
        # Get rider context including TDF simulation progress
        from .rider_profile import get_rider_prompt_context
        rider_context = get_rider_prompt_context(stage_data.stage_number)
        
        # Format ride data summary exactly as specified in the documentation
        ride_summary = f"""Duration: {ride_analysis['duration_minutes']:.0f} minutes
Distance: {stage_data.distance_km}km
Average Power: {ride_analysis.get('avg_power', 'N/A')}W
Max Power: {ride_analysis.get('max_power', 'N/A')}W
Heart Rate: {ride_analysis.get('avg_hr', 'N/A')} bpm (avg)
Intensity Factor: {ride_analysis['intensity_factor']:.2f}
High Effort Intervals: {ride_analysis['high_effort_count']}
Power Profile: Avg {ride_analysis['avg_power_pct_ftp']:.0f}% FTP, Max {ride_analysis['max_power_pct_ftp']:.0f}% FTP"""

        # Format stage report summary
        stage_summary = f"""Stage: {stage_data.stage_name}
Stage Type: {stage_data.stage_type}
Timeline: Start to finish over {stage_data.distance_km}km
Key Events: {self._format_stage_events(stage_data.events)}
Winner: {stage_data.winner}
Weather: {stage_data.weather or 'Clear conditions'}"""

        # Use the exact prompt from context/tdf_fiction_mode.md
        prompt = f"""You are the Analysis & Mapping Agent for the Fiction Mode cycling narrative generator. You will receive two inputs:
- The user's ride data summary for a Tour de France stage (duration, distance, average power, max power, cadence, heart rate, and time-stamped intervals of high effort or surges).
- A summary of the actual stage's official race report, including timeline, key events (breaks, crashes, attacks, winner), and weather.

{rider_context}

USER'S RIDE DATA SUMMARY:
{ride_summary}

ACTUAL STAGE'S OFFICIAL RACE REPORT SUMMARY:
{stage_summary}

Instructions:
1. Consider the stage type (flat/hilly/mountain for road stages, tt/itt/mtn_itt for time trials)
2. For time trial stages: Focus on solo pacing, power management, and aerodynamic position - no peloton dynamics
3. For road stages: Identify high-effort intervals in the user's ride (e.g., surges, sustained efforts, or rest periods)
4. Map these intervals to real events in the stage (e.g., a surge at 35 min corresponds to the crosswind split at 60 km; a steady block matches a period when the peloton chased the break)
5. Assign the user a plausible "virtual role" for the stage based on their performance, effort profile, and stage type
6. For time trials, use roles like "time_trial_aggressive" or "time_trial_steady"
7. For road stages, use roles like "breakaway", "peloton", "domestique", "chase_group"
8. Annotate key moments where the user's data aligns with actual race events
9. Output a timeline of the user's ride mapped to stage events and a brief characterization of their day's role in the race

Respond with JSON format:
{{
  "role_type": "protected rider in the peloton",
  "position": "main_bunch", 
  "tactical": "rode defensively, responding to the day's crosswinds and chaos, finishing safely in the bunch",
  "reasoning": "Based on moderate effort with controlled responses, suitable for tactical riding in peloton"
}}"""
        
        return prompt
    
    def _format_stage_events(self, events: List[RaceEvent]) -> str:
        """Format stage events for prompt"""
        if not events:
            return "No specific events recorded"
        
        event_list = []
        for event in events[:5]:  # Limit to key events
            time_info = f"{event.time_km}km" if event.time_km else f"{event.time_minutes}min"
            event_list.append(f"- {time_info}: {event.description}")
        
        return "\n".join(event_list)
    
    def _parse_role_response(self, response: str) -> Dict[str, str]:
        """Parse LLM response to extract role data"""
        import json
        import re
        
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except Exception:
            pass
        
        # Fallback parsing
        role_type = 'peloton'
        if 'breakaway' in response.lower():
            role_type = 'breakaway'
        elif 'dropped' in response.lower() or 'gruppetto' in response.lower():
            role_type = 'dropped'
        elif 'domestique' in response.lower():
            role_type = 'domestique'
        elif 'chase' in response.lower():
            role_type = 'chase_group'
        
        return {
            'role_type': role_type,
            'position': 'main_bunch',
            'tactical': 'responded to race dynamics'
        }
    
    def _fallback_role_assignment(self, ride_analysis: Dict[str, Any], stage_data: StageRaceData) -> RiderRole:
        """Fallback rule-based role assignment"""
        effort_level = ride_analysis['effort_level']
        high_efforts = ride_analysis['high_effort_count']
        duration_minutes = ride_analysis['duration_minutes']
        stage_type = stage_data.stage_type

        # Time trial stages are fundamentally different - individual effort against the clock
        if stage_type in ['tt', 'itt', 'mtn_itt', 'time_trial']:
            # Time trials: solo effort, no peloton dynamics
            if effort_level in ['hard', 'maximal']:
                role_type = 'time_trial_aggressive'
                position = 'solo'
                tactical = "pushing hard in the time trial, going for a strong result"
            else:
                role_type = 'time_trial_steady'
                position = 'solo'
                tactical = "riding a controlled time trial, focusing on sustainable power"
        
        # Road race stages with peloton dynamics
        elif high_efforts >= 3 and effort_level in ['hard', 'maximal']:
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
        """Map user's effort intervals to race events using LLM intelligence"""

        mapped_events = []
        race_events = stage_data.events
        user_intervals = ride_data.high_effort_intervals

        if not race_events or not user_intervals:
            return mapped_events

        # Use LLM to intelligently map efforts to events
        mapping_prompt = self._build_mapping_prompt(ride_data, stage_data)
        
        try:
            messages = [
                {"role": "system", "content": "You are an expert cycling analyst who maps rider efforts to race events for narrative purposes."},
                {"role": "user", "content": mapping_prompt}
            ]
            response = call_llm(messages, model="gpt-4", force_json=True)
            mapped_events = self._parse_mapping_response(response, user_intervals, race_events)
        except Exception as e:
            print(f"LLM mapping failed, using fallback: {e}")
            # Fallback to simple time-based mapping
            mapped_events = self._fallback_effort_mapping(user_intervals, race_events)

        return mapped_events

    def _build_mapping_prompt(self, ride_data: RideData, stage_data: StageRaceData) -> str:
        """Build prompt for LLM effort-to-event mapping"""
        
        # Format user efforts
        effort_summary = []
        for i, interval in enumerate(ride_data.high_effort_intervals):
            effort_summary.append(
                f"Effort {i+1}: {interval.get('start_minute', 0)}-{interval.get('end_minute', 0)}min, "
                f"{interval.get('avg_power', 0):.0f}W avg, {interval.get('max_power', 0):.0f}W max"
            )
        
        # Format race events
        event_summary = []
        for i, event in enumerate(stage_data.events[:10]):  # Limit to key events
            time_info = f"{event.time_km}km" if event.time_km else f"{event.time_minutes}min"
            event_summary.append(f"Event {i+1}: {time_info} - {event.description}")
        
        prompt = f"""You are the Analysis & Mapping Agent for Fiction Mode cycling narratives.

TASK: Map the user's effort intervals to plausible race events for narrative purposes.

STAGE CONTEXT:
- Stage: {stage_data.stage_name}
- Type: {stage_data.stage_type}
- Distance: {stage_data.distance_km}km
- Winner: {stage_data.winner}

USER EFFORT INTERVALS:
{chr(10).join(effort_summary)}

RACE EVENTS:
{chr(10).join(event_summary)}

INSTRUCTIONS:
1. Analyze the timing and intensity of user efforts vs race events
2. Create plausible narrative connections (doesn't need to be exact timing)
3. Consider that users might respond to race action, not initiate it
4. Match high-intensity efforts to exciting race moments
5. Provide confidence scores (0.0-1.0) for each mapping

Respond with JSON array format:
[
  {{
    "user_effort_index": 0,
    "race_event_index": 1,
    "confidence": 0.8,
    "narrative_description": "responded to the early breakaway formation with a surge to 320W"
  }},
  ...
]

Focus on creating compelling narrative connections rather than precise timing matches."""
        
        return prompt

    def _parse_mapping_response(self, response: str, user_intervals: List[Dict], race_events: List[RaceEvent]) -> List[MappedEvent]:
        """Parse LLM mapping response into MappedEvent objects"""
        import json
        import re
        
        mapped_events = []
        
        try:
            # Extract JSON from response
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                mappings = json.loads(json_match.group())
                
                for mapping in mappings:
                    user_idx = mapping.get('user_effort_index', 0)
                    event_idx = mapping.get('race_event_index', 0)
                    
                    if (user_idx < len(user_intervals) and event_idx < len(race_events)):
                        interval = user_intervals[user_idx]
                        event = race_events[event_idx]
                        
                        mapped_events.append(MappedEvent(
                            user_minute=interval.get('start_minute', 0),
                            race_event=event,
                            user_power=interval.get('avg_power'),
                            user_hr=interval.get('avg_hr'),
                            mapping_confidence=mapping.get('confidence', 0.5),
                            narrative_description=mapping.get('narrative_description', 
                                                            f"responded with {interval.get('avg_power', 0):.0f}W effort")
                        ))
        
        except Exception as e:
            print(f"Failed to parse LLM mapping response: {e}")
            # Return empty list, fallback will be used
        
        return mapped_events

    def _fallback_effort_mapping(self, user_intervals: List[Dict], race_events: List[RaceEvent]) -> List[MappedEvent]:
        """Fallback simple time-based effort mapping"""
        mapped_events = []
        
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
                confidence = 0.6  # Default medium confidence for fallback

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
