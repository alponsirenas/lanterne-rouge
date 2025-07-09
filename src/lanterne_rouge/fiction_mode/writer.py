"""
Writer Agent for Fiction Mode

Generates literary cycling narratives in various styles from analyzed ride data.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import re

from ..ai_clients import call_llm
from .analysis import AnalysisResult, MappedEvent
from .rider_profile import get_rider_prompt_context, get_rider_context


@dataclass
class NarrativeStyle:
    """Configuration for narrative writing style"""
    name: str
    description: str
    voice: str  # 'first_person', 'third_person', 'third_person_limited'
    tense: str  # 'present', 'past'
    tone: str   # 'spare', 'lyrical', 'journalistic', 'dramatic'
    reference_author: Optional[str]
    sample_phrases: List[str]


class WriterAgent:
    """Generates literary cycling narratives from analyzed ride data"""

    def __init__(self):
        self.styles = self._load_narrative_styles()

    def _load_narrative_styles(self) -> Dict[str, NarrativeStyle]:
        """Load available narrative styles"""

        styles = {
            'krabbe': NarrativeStyle(
                name='Tim Krabbé',
                description='Spare, intelligent, introspective prose with attention to calculation and atmosphere',
                voice='third_person',
                tense='present',
                tone='spare',
                reference_author='Tim Krabbé',
                sample_phrases=[
                    'The peloton rolls out in a hush',
                    'She reads the wind, the posture of rivals',
                    'The Tour\'s relentless reinvention',
                    'cadence steady as a metronome',
                    'The discipline of restraint'
                ]
            ),

            'journalistic': NarrativeStyle(
                name='Race Report',
                description='Clear, factual race reporting with tactical analysis',
                voice='third_person',
                tense='past',
                tone='journalistic',
                reference_author='Cycling journalism',
                sample_phrases=[
                    'launched a decisive attack',
                    'the gap steadily increased',
                    'positioned perfectly for the sprint',
                    'tactical masterclass',
                    'controlled the race from start to finish'
                ]
            ),

            'dramatic': NarrativeStyle(
                name='Epic',
                description='Dramatic, emotional storytelling emphasizing struggle and triumph',
                voice='third_person',
                tense='past',
                tone='dramatic',
                reference_author='Epic sports writing',
                sample_phrases=[
                    'summoned every ounce of strength',
                    'the road rose up to meet them',
                    'glory beckoned from beyond',
                    'pushed through the wall of pain',
                    'moment of pure cycling poetry'
                ]
            )
        }

        return styles

    def generate_narrative(self, analysis: AnalysisResult,
                         style_name: str = 'krabbe',
                         stage_number: Optional[int] = None) -> str:
        """Generate complete narrative from analysis with rider profile context"""

        style = self.styles.get(style_name, self.styles['krabbe'])

        # Get rider profile context
        rider_context = get_rider_context(stage_number)
        rider_prompt_context = get_rider_prompt_context(stage_number)

        # Build the prompt with rider context
        prompt = self._build_writer_prompt(analysis, style, rider_context, rider_prompt_context)

        # Generate narrative using LLM
        try:
            messages = [
                {
                    "role": "system",
                    "content": self._get_system_prompt(style, rider_context['rider_profile'])
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]

            narrative = call_llm(
                messages=messages,
                model="gpt-4",
                temperature=0.8,
                max_tokens=2000
            )

            # Post-process to replace any remaining template variables
            narrative = self._replace_template_variables(narrative, analysis, rider_context)

            return narrative.strip()

        except Exception as e:
            print(f"Error generating narrative: {e}")
            return self._generate_fallback_narrative(analysis, style, rider_context)

    def _get_system_prompt(self, style: NarrativeStyle, rider_profile: Dict[str, Any]) -> str:
        """Get system prompt for the narrative style"""

        if style.name == 'Tim Krabbé':
            return f"""You are the Writer Agent for the Fiction Mode cycling narrative generator.

You write in the style of Tim Krabbé's "The Rider" - spare, intelligent, present-tense prose
with sharp attention to detail, calculation, and atmosphere. Your voice is slightly detached
but deeply observant, focused on the internal experience of cycling and the tactical flow of racing.

RIDER CONTEXT:
- Name: {rider_profile.get('name', 'Ana Luisa')}
- Bio: {rider_profile.get('bio', 'An experienced cyclist')}
- Style: {rider_profile.get('literary_voice', 'Tim Krabbé style')}

Key characteristics:
- Third person, present tense
- Spare, economical prose
- Focus on calculation, technique, and internal state
- Wry, intelligent observations
- Vivid but not flowery descriptions
- Attention to the tactical and psychological aspects of racing
- Show the rider's sensations and decision-making process

CRITICAL: Write actual narrative prose, never template code or {{}} placeholders.
Use real names, dates, and specific details from the provided data."""

        elif style.name == 'Race Report':
            return """You are a professional cycling journalist writing a detailed race report.

Your writing is clear, factual, and focuses on tactical analysis. You explain what happened
and why, with attention to team strategies, key moments, and the dynamics of the race.
Write in past tense, third person, with authoritative tone."""

        else:  # Epic/Dramatic
            return """You are writing an epic cycling narrative with dramatic flair.

Your prose is emotional and evocative, emphasizing the struggle, pain, and triumph of cycling.
Use vivid imagery and dramatic language to capture the intensity and passion of the sport.
Write in past tense with rich, descriptive language."""

    def _build_writer_prompt(self, analysis: AnalysisResult,
                           style: NarrativeStyle,
                           rider_context: Dict[str, Any],
                           rider_prompt_context: str) -> str:
        """Build the detailed prompt for narrative generation using documented prompt"""

        # Extract key information
        stage_data = analysis.stage_data
        rider_role = analysis.rider_role
        timeline = analysis.narrative_timeline
        performance = analysis.performance_summary
        rider_profile = rider_context.get('rider_profile', {})

        # Format mapped timeline and virtual role (from Analysis & Mapping Agent)
        mapped_timeline = []
        for event in timeline:
            mapped_timeline.append(f"Minute {event['minute']}: {event['description']} -> {event['user_action']}")
        
        # Format user's ride summary
        ride_summary = f"""Effort Level: {rider_role.effort_level}
Duration: {performance.get('duration_minutes', 0):.0f} minutes
Average Power: {analysis.ride_data.avg_power or 'N/A'}W
Max Power: {analysis.ride_data.max_power or 'N/A'}W
Heart Rate: {analysis.ride_data.avg_hr or 'N/A'} bpm (avg)
Key Efforts: {len(analysis.mapped_events)} significant intervals"""

        # Format official stage report
        stage_report_summary = f"""Timeline: {stage_data.stage_name} - {stage_data.distance_km}km
Main Events: {self._format_stage_events_for_writer(stage_data.events)}
Winner: {stage_data.winner}
Weather: {stage_data.weather or 'Clear conditions'}
Stage Report: {stage_data.stage_report[:300]}..."""

        # Use the exact prompt from context/tdf_fiction_mode.md
        prompt = f"""You are the Writer Agent for the Fiction Mode cycling narrative generator.
You will receive:
- The mapped timeline and virtual role from the Analysis & Mapping Agent
- The user's ride summary (effort level, surges, HR, etc.)
- The official stage report (timeline of the race, main events, winner, weather, etc.)
- The user's chosen literary style: "Tim Krabbé, The Rider" (third person, spare, wry, introspective, vivid)

{rider_prompt_context}

MAPPED TIMELINE AND VIRTUAL ROLE:
Role: {rider_role.role_type} - {rider_role.tactical_description}
Position: {rider_role.position_in_race}
Timeline:
{chr(10).join(mapped_timeline)}

USER'S RIDE SUMMARY:
{ride_summary}

OFFICIAL STAGE REPORT:
{stage_report_summary}

USER'S CHOSEN LITERARY STYLE: "Tim Krabbé, The Rider" (third person, spare, wry, introspective, vivid)

Instructions:
1. Write a third-person narrative of the stage from the user's perspective, weaving together their ride data, their virtual role, and the day's real race events.
2. Reference real happenings (breakaway names, crashes, winner, weather) in the correct timeline.
3. Evoke Krabbé's literary style—sharp, spare, intelligent, focused on detail and calculation, sometimes ironic or detached.
4. Show the user's sensations (effort, calculation, fear, relief) and how their ride fits into the Tour's drama.
5. The narrative should not be about "winning" but about living the day as part of the peloton's world, finishing in character.
6. When narratively appropriate, subtly reference the user's Tour simulation progress (stages completed, consecutive days, overall goals) as part of their mental state and motivation.

Character Name: {rider_profile.get('name', 'Ana Luisa')}

Write a complete narrative that reads like a literary stage recap with the added rider character experiencing the events firsthand. Include specific stage facts, rider names, and race details."""

        return prompt

    def _format_stage_events_for_writer(self, events) -> str:
        """Format stage events for writer prompt"""
        if not events:
            return "No specific events recorded"
        
        event_list = []
        for event in events[:5]:  # Limit to key events
            time_info = f"{event.time_km}km" if event.time_km else f"{event.time_minutes}min"
            event_list.append(f"- {time_info}: {event.description}")
        
        return "\n".join(event_list)

    def _generate_fallback_narrative(self, analysis: AnalysisResult, style: NarrativeStyle, rider_context: Dict[str, Any]) -> str:
        """Generate a simple fallback narrative if LLM fails"""

        stage_data = analysis.stage_data
        rider_role = analysis.rider_role

        fallback = """Stage {stage_data.stage_number} — {stage_data.stage_name}

{stage_data.date.strftime('%B %d, %Y')}

The peloton rolls out under {stage_data.weather or 'typical racing conditions'} for another day of the Tour de France. Ana Luisa settles into position, {rider_role.tactical_description}.

Today's challenge: {analysis.performance_summary['key_challenge']}. Over {analysis.performance_summary['duration_minutes']:.0f} minutes and {stage_data.distance_km}km, she navigates the tactical flow of the race.

"""

        # Add key events
        for event in analysis.narrative_timeline[:3]:  # First few events
            fallback += f"At {event['minute']} minutes, as {event['description']}, she {event['user_action']}.\n\n"

        fallback += """In the end, {stage_data.winner} takes the stage victory. Ana Luisa crosses the line having completed another day in the world's greatest bike race. The tour continues."""

        return fallback

    def _replace_template_variables(self, narrative: str, analysis: AnalysisResult, rider_context: Dict[str, Any]) -> str:
        """Replace template variables in the narrative with actual values"""
        
        stage_data = analysis.stage_data
        rider_role = analysis.rider_role
        performance = analysis.performance_summary
        rider_profile = rider_context.get('rider_profile', {})
        
        # Create replacement mapping
        replacements = {
            '{stage_data.stage_number}': str(stage_data.stage_number),
            '{stage_data.stage_name}': stage_data.stage_name,
            '{stage_data.date.strftime(\'%B %d, %Y\')}': stage_data.date.strftime('%B %d, %Y'),
            '{stage_data.weather or \'typical racing conditions\'}': stage_data.weather or 'typical racing conditions',
            '{stage_data.distance_km}': str(stage_data.distance_km),
            '{stage_data.winner}': stage_data.winner,
            '{rider_role.tactical_description}': rider_role.tactical_description,
            '{analysis.performance_summary[\'key_challenge\']}': performance.get('key_challenge', 'tactical positioning'),
            '{analysis.performance_summary[\'duration_minutes\']:.0f}': str(int(performance.get('duration_minutes', 0))),
            '{character_name}': rider_profile.get('name', 'Ana Luisa'),
            '{analysis.ride_data.avg_power or \'N/A\'}': f"{analysis.ride_data.avg_power}W" if analysis.ride_data.avg_power else 'N/A'
        }
        
        # Apply replacements
        result = narrative
        for template, value in replacements.items():
            result = result.replace(template, value)
        
        return result

    def get_available_styles(self) -> List[str]:
        """Get list of available narrative styles"""
        return list(self.styles.keys())

    def get_style_description(self, style_name: str) -> Optional[str]:
        """Get description of a narrative style"""
        style = self.styles.get(style_name)
        return style.description if style else None
