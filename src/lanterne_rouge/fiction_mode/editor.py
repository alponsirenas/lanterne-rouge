"""
Editor Agent for Fiction Mode

Reviews and polishes generated narratives for style, accuracy, and quality.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import re

from ..ai_clients import call_llm
from .analysis import AnalysisResult


@dataclass
class EditSuggestion:
    """A suggested edit to the narrative"""
    line_number: Optional[int]
    original_text: str
    suggested_text: str
    reason: str
    priority: str  # 'high', 'medium', 'low'


@dataclass
class EditingReport:
    """Complete editing analysis and suggestions"""
    original_narrative: str
    edited_narrative: str
    style_consistency_score: float  # 0.0 to 1.0
    factual_accuracy_score: float
    readability_score: float
    suggestions: List[EditSuggestion]
    errors_found: List[str]
    improvements_made: List[str]


class EditorAgent:
    """Reviews and edits generated cycling narratives"""

    def __init__(self):
        self.cycling_terms = self._load_cycling_terminology()
        self.common_errors = self._load_common_errors()

    def _load_cycling_terminology(self) -> Dict[str, str]:
        """Load correct cycling terminology"""
        return {
            'peloton': 'peloton (not pack or field)',
            'gruppetto': 'gruppetto (not group)',
            'domestique': 'domestique (not helper)',
            'directeur sporti': 'directeur sportif (not team director)',
            'maillot jaune': 'maillot jaune (not yellow jersey when being literary)',
            'echelon': 'echelon (for crosswind formation)',
            'breakaway': 'breakaway (not break)',
            'general classification': 'general classification or GC',
        }

    def _load_common_errors(self) -> List[str]:
        """Load common errors to watch for"""
        return [
            'misuse of "bike" instead of "bicycle" in literary context',
            'incorrect stage distances or times',
            'wrong rider names or team affiliations',
            'anachronistic language',
            'clichéd sports writing phrases',
            'inconsistent tense or voice',
            'repetitive sentence structure',
            'missing cycling context or atmosphere'
        ]

    def edit_narrative(self, narrative: str,
                      analysis: AnalysisResult,
                      style_name: str = 'krabbe',
                      user_feedback: Optional[str] = None) -> EditingReport:
        """Complete editing pass on the narrative"""

        # Run all editing checks
        style_score = self._check_style_consistency(narrative, style_name)
        accuracy_score = self._check_factual_accuracy(narrative, analysis)
        readability_score = self._check_readability(narrative)

        # Find errors and suggestions
        errors = self._find_errors(narrative, analysis)
        suggestions = self._generate_suggestions(narrative, style_name, analysis)

        # Apply automatic edits
        edited_narrative, improvements = self._apply_automatic_edits(narrative, suggestions)

        # If user feedback provided, incorporate it
        if user_feedback:
            edited_narrative = self._incorporate_user_feedback(edited_narrative, user_feedback, analysis)

        return EditingReport(
            original_narrative=narrative,
            edited_narrative=edited_narrative,
            style_consistency_score=style_score,
            factual_accuracy_score=accuracy_score,
            readability_score=readability_score,
            suggestions=suggestions,
            errors_found=errors,
            improvements_made=improvements
        )

    def _check_style_consistency(self, narrative: str, style_name: str) -> float:
        """Check consistency with chosen narrative style"""

        score = 1.0

        if style_name == 'krabbe':
            # Check for Tim Krabbé style characteristics

            # Present tense check
            if 'rolled out' in narrative or 'crossed the line' in narrative:
                score -= 0.2  # Should be present tense

            # Third person check
            if ' I ' in narrative or 'my ' in narrative:
                score -= 0.3  # Should be third person

            # Spare prose check (avoid excessive adjectives)
            adjective_density = len(re.findall(r'\b(very|extremely|incredibly|absolutely)\b', narrative, re.IGNORECASE))
            if adjective_density > 3:
                score -= 0.1

            # Check for calculation/tactical elements
            if not any(word in narrative.lower() for word in ['watts', 'power', 'cadence', 'heart', 'calculate']):
                score -= 0.2

        elif style_name == 'journalistic':
            # Check for journalistic style
            if not re.search(r'\b(attacked|responded|finished|won)\b', narrative):
                score -= 0.2

            # Past tense check
            if 'rolls out' in narrative or 'throws his bike' in narrative:
                score -= 0.2  # Should be past tense

        return max(0.0, score)

    def _check_factual_accuracy(self, narrative: str, analysis: AnalysisResult) -> float:
        """Check factual accuracy against stage data"""

        score = 1.0
        stage_data = analysis.stage_data

        # Check stage winner
        if stage_data.winner not in narrative:
            score -= 0.3

        # Check stage locations
        stage_parts = stage_data.stage_name.split(' > ')
        if len(stage_parts) == 2:
            start_city = stage_parts[0].strip()
            finish_city = stage_parts[1].strip()

            if start_city not in narrative:
                score -= 0.2
            if finish_city not in narrative:
                score -= 0.2

        # Check weather consistency
        if stage_data.weather:
            weather_mentioned = any(weather_word in narrative.lower()
                                  for weather_word in ['wind', 'rain', 'sun', 'cloud', 'weather'])
            if not weather_mentioned:
                score -= 0.1

        # Check distance reasonableness
        if f"{stage_data.distance_km}" not in narrative:
            # Not necessarily wrong, but good to mention
            score -= 0.05

        return max(0.0, score)

    def _check_readability(self, narrative: str) -> float:
        """Check readability and flow"""

        score = 1.0

        # Check paragraph structure
        paragraphs = narrative.split('\n\n')
        if len(paragraphs) < 3:
            score -= 0.2  # Too few paragraphs

        # Check sentence variety
        sentences = re.split(r'[.!?]+', narrative)
        avg_sentence_length = sum(len(s.split()) for s in sentences if s.strip()) / len([s for s in sentences if s.strip()])

        if avg_sentence_length > 25:
            score -= 0.1  # Sentences too long
        elif avg_sentence_length < 8:
            score -= 0.1  # Sentences too short

        # Check for repetitive words
        words = narrative.lower().split()
        word_counts = {}
        for word in words:
            if len(word) > 6:  # Only check longer words
                word_counts[word] = word_counts.get(word, 0) + 1

        repeated_words = [word for word, count in word_counts.items() if count > 4]
        if repeated_words:
            score -= 0.1 * len(repeated_words)

        return max(0.0, score)

    def _find_errors(self, narrative: str, analysis: AnalysisResult) -> List[str]:
        """Find specific errors in the narrative"""

        errors = []

        # Check for common cycling terminology errors
        if 'pack' in narrative.lower() and 'peloton' not in narrative.lower():
            errors.append("Use 'peloton' instead of 'pack' for the main group")

        if 'bike' in narrative and 'bicycle' not in narrative:
            errors.append("Consider using 'bicycle' instead of 'bike' for literary tone")

        # Check for anachronistic terms
        modern_terms = ['GPS', 'power meter', 'Strava', 'smartphone']
        for term in modern_terms:
            if term.lower() in narrative.lower():
                errors.append(f"Remove anachronistic term: '{term}'")

        # Check for clichés
        cliches = ['dig deep', 'leave it all on the road', 'pain cave', 'empty the tank']
        for cliche in cliches:
            if cliche.lower() in narrative.lower():
                errors.append(f"Avoid cliché: '{cliche}'")

        return errors

    def _generate_suggestions(self, narrative: str, style_name: str, analysis: AnalysisResult) -> List[EditSuggestion]:
        """Generate editing suggestions"""

        suggestions = []

        # Style-specific suggestions
        if style_name == 'krabbe':
            # Suggest more specific cycling details
            if 'power' not in narrative.lower():
                suggestions.append(EditSuggestion(
                    line_number=None,
                    original_text="",
                    suggested_text="Add power/watts reference for technical authenticity",
                    reason="Krabbé style includes technical cycling details",
                    priority="medium"
                ))

            # Check for present tense consistency
            past_tense_verbs = re.findall(r'\b(rolled|finished|crossed|attacked)\b', narrative)
            if past_tense_verbs:
                suggestions.append(EditSuggestion(
                    line_number=None,
                    original_text=f"Past tense verbs: {', '.join(set(past_tense_verbs))}",
                    suggested_text="Convert to present tense for Krabbé style",
                    reason="Tim Krabbé uses present tense",
                    priority="high"
                ))

        # Factual accuracy suggestions
        stage_data = analysis.stage_data
        if stage_data.winner not in narrative:
            suggestions.append(EditSuggestion(
                line_number=None,
                original_text="",
                suggested_text=f"Mention stage winner: {stage_data.winner}",
                reason="Should reference actual stage winner",
                priority="high"
            ))

        return suggestions

    def _apply_automatic_edits(self, narrative: str, suggestions: List[EditSuggestion]) -> Tuple[str, List[str]]:
        """Apply automatic edits where safe to do so"""

        edited_text = narrative
        improvements = []

        # Simple automatic fixes
        replacements = {
            ' pack ': ' peloton ',
            ' the pack,': ' the peloton,',
            ' bike ': ' bicycle ',
            'his bike': 'his bicycle',
            'her bike': 'her bicycle'
        }

        for old, new in replacements.items():
            if old in edited_text:
                edited_text = edited_text.replace(old, new)
                improvements.append(f"Replaced '{old.strip()}' with '{new.strip()}'")

        return edited_text, improvements

    def _incorporate_user_feedback(self, narrative: str, feedback: str, analysis: AnalysisResult) -> str:
        """Incorporate user feedback using LLM"""

        try:
            prompt = """Please revise this cycling narrative based on the user's feedback:

ORIGINAL NARRATIVE:
{narrative}

USER FEEDBACK:
{feedback}

STAGE CONTEXT:
- Stage: {analysis.stage_data.stage_name}
- Winner: {analysis.stage_data.winner}
- User's role: {analysis.rider_role.role_type}

Please make the requested changes while maintaining the narrative style and factual accuracy."""

            messages = [
                {
                    "role": "system",
                    "content": "You are an expert editor for cycling narratives. Make the requested changes while preserving style and accuracy."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]

            revised_narrative = call_llm(
                messages=messages,
                model="gpt-4",
                temperature=0.3,
                max_tokens=2000
            )

            return revised_narrative.strip()

        except Exception as e:
            print(f"Error incorporating user feedback: {e}")
            return narrative  # Return original if editing fails

    def suggest_improvements(self, narrative: str, style_name: str) -> List[str]:
        """Suggest specific improvements for the narrative"""

        improvements = []

        # Length check
        word_count = len(narrative.split())
        if word_count < 500:
            improvements.append("Consider expanding the narrative - add more detail about the stage atmosphere and tactics")
        elif word_count > 1500:
            improvements.append("Consider condensing the narrative - focus on the most important moments")

        # Structure check
        if '⸻' not in narrative:
            improvements.append("Consider adding section breaks (⸻) for better visual structure")

        # Dialog check
        if '"' not in narrative:
            improvements.append("Consider adding brief dialog or race radio excerpts for authenticity")

        # Technical detail check
        technical_terms = ['watts', 'cadence', 'heart rate', 'power', 'tempo']
        if not any(term in narrative.lower() for term in technical_terms):
            improvements.append("Add more technical cycling details for authenticity")

        return improvements
