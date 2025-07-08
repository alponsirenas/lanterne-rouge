"""
Writer Agent for Fiction Mode

Generates literary cycling narratives in various styles from analyzed ride data.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass

from ..ai_clients import call_llm
from .analysis import AnalysisResult, MappedEvent


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
                         user_bio: Optional[str] = None) -> str:
        """Generate complete narrative from analysis"""

        style = self.styles.get(style_name, self.styles['krabbe'])

        # Build the prompt
        prompt = self._build_writer_prompt(analysis, style, user_bio)

        # Generate narrative using LLM
        try:
            messages = [
                {
                    "role": "system",
                    "content": self._get_system_prompt(style)
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

            return narrative.strip()

        except Exception as e:
            print(f"Error generating narrative: {e}")
            return self._generate_fallback_narrative(analysis, style)

    def _get_system_prompt(self, style: NarrativeStyle) -> str:
        """Get system prompt for the narrative style"""

        if style.name == 'Tim Krabbé':
            return """You are the Writer Agent for the Fiction Mode cycling narrative generator.

You write in the style of Tim Krabbé's "The Rider" - spare, intelligent, present-tense prose
with sharp attention to detail, calculation, and atmosphere. Your voice is slightly detached
but deeply observant, focused on the internal experience of cycling and the tactical flow of racing.

Key characteristics:
- Third person, present tense
- Spare, economical prose
- Focus on calculation, technique, and internal state
- Wry, intelligent observations
- Vivid but not flowery descriptions
- Attention to the tactical and psychological aspects of racing
- Show the rider's sensations and decision-making process

Write immersive narratives that blend the user's real effort data with the stage's actual events,
referencing real riders, results, and weather. The story should feel authentic to the world of
professional cycling while capturing the user's experience within that context."""

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
                           user_bio: Optional[str]) -> str:
        """Build the detailed prompt for narrative generation"""

        # Extract key information
        stage_data = analysis.stage_data
        rider_role = analysis.rider_role
        timeline = analysis.narrative_timeline
        performance = analysis.performance_summary

        # Build character description
        character_name = "Ana Luisa"  # Default name, could be from user bio
        if user_bio:
            # Character description logic here
            character_desc = "Character: Ana Luisa, an experienced cyclist with unique qualities"
        else:
            character_desc = "Character: Ana Luisa, an experienced cyclist"

        prompt = """Generate a cycling narrative for this Tour de France stage:

STAGE INFORMATION:
- Stage: {stage_data.stage_name}
- Date: {stage_data.date.strftime('%B %d, %Y')}
- Distance: {stage_data.distance_km}km
- Type: {stage_data.stage_type}
- Winner: {stage_data.winner} ({stage_data.winning_team})
- Weather: {stage_data.weather or 'Not specified'}

RIDER'S ROLE & PERFORMANCE:
- Role: {rider_role.role_type} - {rider_role.tactical_description}
- Position: {rider_role.position_in_race}
- Effort Level: {rider_role.effort_level}
- Duration: {performance['duration_minutes']:.0f} minutes
- Average Power: {analysis.ride_data.avg_power or 'N/A'}W
- Key Challenge: {performance['key_challenge']}

NARRATIVE TIMELINE:
"""

        # Add timeline events
        for event in timeline:
            prompt += f"- Minute {event['minute']}: {event['description']} -> {event['user_action']}\n"

        prompt += """

MAPPED EVENTS:
"""

        # Add mapped events with specific details
        for mapped_event in analysis.mapped_events:
            prompt += f"- {mapped_event.narrative_description}\n"

        prompt += """

STAGE REPORT EXCERPT:
{stage_data.stage_report[:500]}...

WRITING INSTRUCTIONS:
Write a complete narrative (800-1200 words) that:
1. Opens with the stage start and atmosphere
2. Incorporates the rider's specific efforts and mapped events
3. References real riders, results, and stage events accurately
4. Shows the tactical flow and decision-making
5. Captures the physical and mental experience of the ride
6. Ends with the finish and reflection on the day

Use the character name {character_name} throughout. The narrative should feel like the reader
is experiencing this stage as part of the actual Tour de France peloton."""

        return prompt

    def _generate_fallback_narrative(self, analysis: AnalysisResult, style: NarrativeStyle) -> str:
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

    def get_available_styles(self) -> List[str]:
        """Get list of available narrative styles"""
        return list(self.styles.keys())

    def get_style_description(self, style_name: str) -> Optional[str]:
        """Get description of a narrative style"""
        style = self.styles.get(style_name)
        return style.description if style else None
