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

    def llm_edit_narrative(self, narrative: str, analysis: AnalysisResult) -> str:
        """Edit narrative using LLM with the documented Editor Agent prompt"""
        
        # Use the exact prompt from context/tdf_fiction_mode.md
        prompt = f"""You are the Editor Agent for the Fiction Mode cycling narrative generator.
You will receive a draft narrative for a Tour de France stage, written in the style of Tim Krabbé, The Rider.

DRAFT NARRATIVE:
{narrative}

Instructions:
1. Review the narrative for consistency with the Krabbé style: spare prose, wry insight, interiority, a sense of calculation and detachment.
2. Ensure all references to real race events are factually accurate and appear in correct sequence (breaks, crashes, winner).
3. Check for smooth narrative flow, cycling-appropriate terminology, and elimination of awkward phrasing or unnecessary repetition.
4. Make light improvements to voice and clarity, but preserve the unique style and literary quality.
5. Output the edited narrative, ready for delivery.

CRITICAL FACT-CHECKING REQUIREMENTS:
- Stage Winner: MUST be {analysis.stage_data.winner}
- Stage Route: MUST be {analysis.stage_data.stage_name}
- Stage Distance: {analysis.stage_data.distance_km}km
- Key Events: {self._format_stage_events_for_editor(analysis.stage_data.events)}
- DO NOT invent rider names, breakaway details, or race events not provided
- If TDF simulation progress is mentioned, ensure it's accurate for Stage {analysis.stage_data.stage_number} (this should be stage {analysis.stage_data.stage_number} of 21, not referring to previous consecutive days unless accurate)

Edit the narrative to improve style, flow, and accuracy while maintaining the Tim Krabbé literary voice. Return only the edited narrative."""

        try:
            messages = [
                {
                    "role": "system", 
                    "content": "You are an expert literary editor specializing in cycling literature. You understand Tim Krabbé's spare, intelligent style and can polish narratives while preserving their unique voice."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]

            edited_narrative = call_llm(
                messages=messages,
                model="gpt-4",
                temperature=0.3,
                max_tokens=2500
            )

            return edited_narrative.strip()

        except Exception as e:
            print(f"Error in LLM editing: {e}")
            return narrative  # Return original if editing fails

    def _format_stage_events_for_editor(self, events) -> str:
        """Format stage events for editor context"""
        if not events:
            return "No specific events recorded"
        
        event_list = []
        for event in events[:5]:  # Limit to key events
            time_info = f"{event.time_km}km" if event.time_km else f"{event.time_minutes}min"
            event_list.append(f"- {time_info}: {event.description}")
        
        return "\n".join(event_list)

    def edit_narrative(self, narrative: str,
                      analysis: AnalysisResult,
                      style_name: str = 'krabbe',
                      user_feedback: Optional[str] = None,
                      use_llm: bool = True,
                      quality_threshold: float = 0.9,
                      max_iterations: int = 2) -> EditingReport:
        """Complete editing pass on the narrative with quality standards"""

        original_narrative = narrative
        current_narrative = narrative
        iteration_count = 0
        all_improvements = []

        while iteration_count < max_iterations:
            iteration_count += 1
            
            # Use LLM editing if requested (default for high-quality output)
            if use_llm:
                current_narrative = self.llm_edit_narrative(current_narrative, analysis)
            
            # Run all editing checks on the current version
            style_score = self._check_style_consistency(current_narrative, style_name)
            accuracy_score = self._check_factual_accuracy(current_narrative, analysis)
            readability_score = self._check_readability(current_narrative)

            # Check if quality meets threshold
            min_score = min(style_score, accuracy_score, readability_score)
            
            if min_score >= quality_threshold:
                # Quality is acceptable, break out of loop
                all_improvements.append(f"Quality threshold met after {iteration_count} iteration(s)")
                break
            elif iteration_count < max_iterations:
                # Quality below threshold, generate specific feedback for improvement
                feedback = self._generate_quality_feedback(
                    current_narrative, analysis, style_score, accuracy_score, readability_score, quality_threshold
                )
                all_improvements.append(f"Iteration {iteration_count}: {feedback}")
                
                # Request rewrite with specific feedback
                current_narrative = self._request_narrative_rewrite(current_narrative, analysis, feedback)
            else:
                # Max iterations reached
                all_improvements.append(f"Max iterations ({max_iterations}) reached. Final scores: Style {style_score:.2f}, Accuracy {accuracy_score:.2f}, Readability {readability_score:.2f}")

        # Find errors and suggestions for final version
        errors = self._find_errors(current_narrative, analysis)
        suggestions = self._generate_suggestions(current_narrative, style_name, analysis)

        # If user feedback provided, incorporate it
        if user_feedback:
            current_narrative = self._incorporate_user_feedback(current_narrative, user_feedback, analysis)

        return EditingReport(
            original_narrative=original_narrative,
            edited_narrative=current_narrative,
            style_consistency_score=style_score,
            factual_accuracy_score=accuracy_score,
            readability_score=readability_score,
            suggestions=suggestions,
            errors_found=errors,
            improvements_made=all_improvements
        )

    def _generate_quality_feedback(self, narrative: str, analysis: AnalysisResult, 
                                  style_score: float, accuracy_score: float, readability_score: float,
                                  threshold: float) -> str:
        """Generate specific feedback for improving narrative quality"""
        
        feedback_parts = []
        
        if style_score < threshold:
            if 'rolled out' in narrative or 'crossed the line' in narrative:
                feedback_parts.append("Use present tense for Tim Krabbé style")
            if ' I ' in narrative or 'my ' in narrative:
                feedback_parts.append("Maintain third person perspective")
            if len([word for word in narrative.split() if word.lower() in ['very', 'extremely', 'incredibly']]) > 2:
                feedback_parts.append("Use more spare, economical prose - reduce excessive adjectives")
            if not any(word in narrative.lower() for word in ['watts', 'power', 'cadence', 'heart']):
                feedback_parts.append("Include more technical cycling details for authenticity")
        
        if accuracy_score < threshold:
            if analysis.stage_data.winner not in narrative:
                feedback_parts.append(f"Must mention stage winner: {analysis.stage_data.winner}")
            stage_parts = analysis.stage_data.stage_name.split(' > ')
            if len(stage_parts) == 2:
                start_city, finish_city = stage_parts[0].strip(), stage_parts[1].strip()
                if start_city not in narrative:
                    feedback_parts.append(f"Include start location: {start_city}")
                if finish_city not in narrative:
                    feedback_parts.append(f"Include finish location: {finish_city}")
            if str(analysis.stage_data.distance_km) not in narrative and f"{analysis.stage_data.distance_km:.0f}" not in narrative:
                feedback_parts.append(f"Consider mentioning stage distance: {analysis.stage_data.distance_km}km")
        
        if readability_score < threshold:
            word_count = len(narrative.split())
            if word_count < 300:
                feedback_parts.append("Expand narrative with more detail and atmosphere")
            elif word_count > 600:
                feedback_parts.append("Condense narrative to focus on key moments")
            
            # Check for repetitive words
            words = narrative.lower().split()
            word_freq = {}
            for word in words:
                if len(word) > 4:  # Only check longer words
                    word_freq[word] = word_freq.get(word, 0) + 1
            
            repetitive = [word for word, count in word_freq.items() if count > 4]
            if repetitive:
                feedback_parts.append(f"Reduce repetition of words: {', '.join(repetitive[:3])}")
        
        if not feedback_parts:
            feedback_parts.append("General quality improvements needed")
        
        return "; ".join(feedback_parts)

    def _request_narrative_rewrite(self, narrative: str, analysis: AnalysisResult, feedback: str) -> str:
        """Request a rewrite with specific feedback"""
        
        try:
            prompt = f"""You are revising a Tim Krabbé style cycling narrative that needs improvement.

CURRENT NARRATIVE:
{narrative}

EDITOR FEEDBACK FOR IMPROVEMENT:
{feedback}

CRITICAL REQUIREMENTS:
- Stage Winner: {analysis.stage_data.winner}
- Stage Route: {analysis.stage_data.stage_name}
- Distance: {analysis.stage_data.distance_km}km
- Maintain Tim Krabbé style: spare, intelligent, introspective prose
- Third person perspective
- Present tense when appropriate

Please rewrite the narrative addressing the specific feedback while maintaining literary quality and factual accuracy. Return only the improved narrative."""

            messages = [
                {
                    "role": "system", 
                    "content": "You are an expert editor improving cycling narratives. Focus on the specific feedback provided while maintaining Tim Krabbé's distinctive literary style."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]

            improved_narrative = call_llm(
                messages=messages,
                model="gpt-4",
                temperature=0.7,
                max_tokens=2500
            )

            return improved_narrative.strip()

        except Exception as e:
            print(f"Error in narrative rewrite: {e}")
            return narrative  # Return original if rewrite fails

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

        # Check stage winner (most important)
        if stage_data.winner not in narrative:
            score -= 0.4

        # Check stage locations - be more flexible with route names
        stage_name_lower = stage_data.stage_name.lower()
        narrative_lower = narrative.lower()
        
        # For routes like "Lille Métropole > Lille Métropole", check if key city names appear
        stage_parts = stage_data.stage_name.split(' > ')
        if len(stage_parts) >= 2:
            start_city = stage_parts[0].strip()
            finish_city = stage_parts[1].strip()
            
            # Be more flexible - check for partial matches
            start_found = any(word.lower() in narrative_lower for word in start_city.split() if len(word) > 3)
            finish_found = any(word.lower() in narrative_lower for word in finish_city.split() if len(word) > 3)
            
            if not start_found:
                score -= 0.15
            if not finish_found and finish_city != start_city:  # Don't double-penalize circular routes
                score -= 0.15
        
        # Check for key events mentioned in stage data
        events_mentioned = 0
        total_events = len(analysis.stage_data.events)
        if total_events > 0:
            for event in analysis.stage_data.events[:3]:  # Check first 3 events
                if any(word.lower() in narrative_lower for word in event.description.split() if len(word) > 4):
                    events_mentioned += 1
            
            # Deduct if no key events mentioned
            if events_mentioned == 0:
                score -= 0.2
        
        # Weather check - be more lenient
        if stage_data.weather:
            weather_mentioned = any(weather_word in narrative_lower
                                  for weather_word in ['wind', 'rain', 'sun', 'cloud', 'weather', 'crosswind', 'breeze'])
            if not weather_mentioned:
                score -= 0.05  # Reduced penalty

        # Distance check - be more lenient (good to have but not critical)
        distance_mentioned = (str(int(stage_data.distance_km)) in narrative or 
                            f"{stage_data.distance_km}" in narrative or
                            "km" in narrative)
        if not distance_mentioned:
            score -= 0.02  # Very small penalty

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
        """Apply automatic edits where safe to do"""

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
