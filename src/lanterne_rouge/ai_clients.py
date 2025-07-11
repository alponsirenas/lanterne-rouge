"""
Communication Agent and AI client interfaces for Lanterne Rouge.

This module provides utilities for interacting with AI models like OpenAI,
generating empathetic summaries, and handling structured output.
"""
import os
import json
from typing import Dict, Any
from datetime import date

import openai

from .memory_bus import fetch_recent_memories

# Models that natively support the `response_format={"type": "json_object"}` parameter
_MODELS_WITH_JSON_SUPPORT = {
    "gpt-4o-preview",
    "gpt-4o-mini",
    "gpt-4o",
    "gpt-4-turbo-preview",
    "gpt-4-0125-preview",
    "gpt-4-1106-preview",
    "gpt-3.5-turbo-1106",
    "gpt-3.5-turbo-0125",
    "gpt-4o-2024-05-13",
}

def _model_supports_json(model: str) -> bool:
    """
    Return True if the specified model supports the structured JSON response
    format. This lets us add the `response_format` parameter only when it's
    accepted by the model to avoid HTTP 400 errors.
    """
    # Check if model is in our explicit list or has specific prefixes that indicate JSON support
    return (model in _MODELS_WITH_JSON_SUPPORT or
            model.endswith("-json") or
            model.startswith(("gpt-4-turbo", "gpt-4o")))


# Initialize OpenAI API key from environment
openai.api_key = os.getenv("OPENAI_API_KEY")


def generate_workout_adjustment(
    readiness_score: float,
    readiness_details: dict,
    ctl: float,
    atl: float,
    tsb: float,
    mission_cfg,
    memories_limit: int = 5,
    *,
    model: str | None = None,
) -> list[str]:
    """
    Generate workout adjustment using LLM, seeded with recent memories.

    Args:
        readiness_score: numeric readiness score from Oura.
        readiness_details: dict of all readiness contributor values.
        ctl: current Chronic Training Load.
        atl: current Acute Training Load.
        tsb: current Training Stress Balance.
        mission_cfg: your MissionConfig instance (to extract plan targets).
        memories_limit: how many past memories to include.
        model: Optional model name to pass to the LLM. If omitted, the
            default from ``call_llm`` will be used.

    Returns:
        List of GPT-written adjustment recommendation lines.
        Each line has leading hyphens and whitespace stripped.
    """
    # Build a structured 'plan' dict out of your mission config
    try:
        current_plan = mission_cfg.dict()
    except Exception:
        current_plan = {}

    # Aggregate all metrics together
    combined_metrics = {
        "readiness_score": readiness_score,
        **readiness_details,
        "ctl": ctl,
        "atl": atl,
        "tsb": tsb,
    }

    # Pull in recent memories to provide richer context
    recent_memories = fetch_recent_memories(limit=memories_limit)

    # Kick things off with a clear system prompt
    messages = [
        {
            "role": "system",
            "content": (
                "You are a smart cycling coach AI. Based on the mission targets, today's plan, "
                "and recent performance/readiness, propose any adjustments."
            ),
        }
    ]
    if recent_memories:
        mem_lines = [json.dumps(m) for m in recent_memories]
        messages.append(
            {
                "role": "system",
                "content": "Recent observations & decisions:\n" + "\n".join(mem_lines),
            }
        )

    # Now give the AI the current plan and fresh metrics
    user_content = (
        f"Mission plan:\n{current_plan}\n\n"
        f"Today's metrics:\n{combined_metrics}\n\n"
        "Please suggest workout modifications or validate the plan."
    )
    messages.append({"role": "user", "content": user_content})

    try:
        # Always call with force_json=False to avoid API compatibility issues
        raw_response = call_llm(messages, model=model, force_json=False)

        # Try to parse the response - first check if it's a bullet list
        if raw_response.lstrip().startswith("-"):
            lines = parse_llm_list(raw_response)
            return lines

        # Then try to parse as JSON if it looks like JSON
        if raw_response.strip().startswith("{") and raw_response.strip().endswith("}"):
            try:
                parsed = json.loads(raw_response)
                if isinstance(parsed, list):
                    lines = [str(line).strip("- \t") for line in parsed if str(line).strip()]
                    return lines
                if isinstance(parsed, dict) and "recommendations" in parsed:
                    if isinstance(parsed["recommendations"], list):
                        lines = [
                            str(line).strip("- \t")
                            for line in parsed["recommendations"]
                            if str(line).strip()
                        ]
                        return lines
            except json.JSONDecodeError:
                pass  # Failed to parse as JSON, continue to fallback

        # Try generic parsing of any free-text response
        lines = parse_llm_list(raw_response)
        if lines:
            return lines

        # If all else fails, provide a generic recommendation
        return ["Plan looks good. Continue with scheduled workout."]

    except (ValueError, json.JSONDecodeError) as e:
        print(f"Error generating workout adjustment: {e}")
        return ["Unable to generate recommendations. Proceed with scheduled workout."]
    except Exception as e:
        print(f"Unexpected error in workout adjustment: {e}")
        return ["System error encountered. Proceed with scheduled workout."]


def parse_llm_list(raw_response: str) -> list[str]:
    """
    Parse the raw LLM response into a list of cleaned recommendation lines.

    Args:
        raw_response: The raw text response from the LLM.

    Returns:
        A list of non-empty, cleaned lines with bullets and extra whitespace removed.
    """
    lines = [
        line.lstrip("-0123456789. \t").strip()
        for line in raw_response.splitlines()
    ]
    return [line for line in lines if line]


def call_llm(
    messages: list[dict],
    model: str | None = None,
    *,
    temperature: float = 0.7,
    max_tokens: int = 512,
    force_json: bool = False,  # Changed default to False for better compatibility
) -> str:
    """
    Send a chat completion request to the OpenAI API.

    Args:
        messages: A list of message dicts, each with 'role' ('system', 'user', 'assistant') and 'content'.
        model: The OpenAI model to use. Defaults to the value of the
            ``OPENAI_MODEL`` environment variable or ``"gpt-3.5-turbo"`` if unset.
        temperature: Sampling temperature (default 0.7).
        max_tokens: Maximum number of tokens in the response (default 512).
        force_json: If True, will request a structured JSON response
            from models that support it. If False (default), lets the model reply in freeform text.

    Returns:
        The assistant's reply content.
    """
    # Resolve model
    if model is None:
        # Default to a model that can handle JSON
        model = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")

    # Set up request parameters
    response_kwargs = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    # Only add response_format for models that explicitly support it
    if force_json and _model_supports_json(model):
        response_kwargs["response_format"] = {"type": "json_object"}

    try:
        # Use the new OpenAI client API
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(**response_kwargs)

        # Get the content from the response
        content = response.choices[0].message.content

        # Handle empty responses
        if content is None or content.strip() == "":
            return "- No valid response received from the model."

        return content

    except Exception as e:
        print(f"❌ OpenAI request failed: {e}")
        return "- Error: Could not get a response from the LLM."


class CommunicationAgent:
    """Generates natural language summaries of training recommendations."""

    def generate_summary(
        self,
        decision,  # TrainingDecision
        workout,   # WorkoutPlan
        metrics: Dict[str, Any],
        config,    # MissionConfig
        current_date: date
    ) -> str:
        """Generate a complete, empathetic training summary."""

        # Get training context
        phase = config.training_phase(current_date)
        next_phase_start = config.next_phase_start(current_date)
        days_to_next_phase = (next_phase_start - current_date).days if next_phase_start else None
        days_to_goal = (config.goal_date - current_date).days

        # Build sections
        sections = []

        # 1. Training Phase Context
        phase_section = self._generate_phase_context(phase, days_to_next_phase, days_to_goal)
        sections.append(phase_section)

        # 2. Current Metrics
        metrics_section = self._generate_metrics_summary(metrics)
        sections.append(metrics_section)

        # 3. Today's Reasoning
        reasoning_section = self._generate_reasoning_summary(decision)
        sections.append(reasoning_section)

        # 4. Workout Plan
        workout_section = self._generate_workout_summary(workout)
        sections.append(workout_section)

        return "\n\n".join(sections)

    def _generate_phase_context(self, phase: str, days_to_next: int, days_to_goal: int) -> str:
        """Generate training phase context."""
        lines = [f"🏆 Training Phase: {phase}"]

        if days_to_next:
            lines.append(f"📅 Days until next phase: {days_to_next}")

        lines.append(f"🎯 Days to goal: {days_to_goal}")

        # Add phase-specific context
        if phase == "Base":
            lines.append("Building your aerobic foundation with steady, sustainable efforts.")
        elif phase == "Build":
            lines.append("Developing racing fitness with structured interval work.")
        elif phase == "Peak":
            lines.append("Sharpening your fitness for peak performance.")
        elif phase == "Taper":
            lines.append("Maintaining fitness while reducing fatigue for the big day.")

        return "\n".join(lines)

    def _generate_metrics_summary(self, metrics: Dict[str, Any]) -> str:
        """Generate current metrics summary."""
        lines = ["📊 Current Fitness Metrics:"]
        lines.append(f"• Readiness Score: {metrics.get('readiness_score', 'N/A')}")
        lines.append(f"• CTL (Fitness): {metrics.get('ctl', 'N/A')}")
        lines.append(f"• ATL (Fatigue): {metrics.get('atl', 'N/A')}")
        lines.append(f"• TSB (Form): {metrics.get('tsb', 'N/A')}")

        return "\n".join(lines)

    def _generate_reasoning_summary(self, decision) -> str:
        """Generate reasoning summary."""
        lines = ["🧠 Today's Training Logic:"]
        lines.append(f"• Decision: {decision.action.title()}")
        lines.append(f"• Reasoning: {decision.reason}")
        lines.append(f"• Recommended Intensity: {decision.intensity_recommendation.title()}")

        return "\n".join(lines)

    def _generate_workout_summary(self, workout) -> str:
        """Generate workout summary with zones."""
        lines = ["🚴 Today's Workout Plan:"]
        lines.append(f"• Type: {workout.workout_type}")
        lines.append(f"• Description: {workout.description}")
        lines.append(f"• Duration: {workout.duration_minutes} minutes")
        lines.append(f"• Estimated Load: {workout.estimated_load}")

        if workout.zones:
            lines.append("• Time in Zones:")
            for zone, minutes in workout.zones.items():
                lines.append(f"  - {zone}: {minutes} min")

        return "\n".join(lines)

    def generate_tdf_summary(
        self,
        tdf_decision,  # TDFDecision
        metrics: Dict[str, Any],
        config,        # MissionConfig
        current_date: date,
        tdf_data: Dict[str, Any] = None
    ) -> str:
        """Generate a TDF-specific training summary with ride mode recommendation."""

        # Get stage and points information
        stage_info = tdf_data.get('stage_info', {}) if tdf_data else {}
        points_status = tdf_data.get('points_status', {}) if tdf_data else {}

        # Build TDF-specific sections
        sections = []

        # 1. TDF Stage Header
        stage_section = self._generate_tdf_stage_header(stage_info, tdf_decision)
        sections.append(stage_section)

        # 2. Current Metrics & Recommendation
        metrics_section = self._generate_tdf_metrics_summary(metrics, tdf_decision)
        sections.append(metrics_section)

        # 3. Points Strategy
        points_section = self._generate_tdf_points_summary(tdf_decision, points_status, config)
        sections.append(points_section)

        # 4. Reasoning & Strategy
        reasoning_section = self._generate_tdf_reasoning_summary(tdf_decision)
        sections.append(reasoning_section)

        # 5. Motivational close
        motivation_section = self._generate_tdf_motivation(tdf_decision, stage_info)
        sections.append(motivation_section)

        return "\n\n".join(sections)

    def _generate_tdf_stage_header(self, stage_info: Dict[str, Any], tdf_decision) -> str:
        """Generate TDF stage header matching documentation format."""
        stage_number = stage_info.get('number', 1)
        stage_type = stage_info.get('type', 'flat')

        # Stage type mapping to match documentation
        stage_type_map = {
            'flat': ('�', 'Flat Sprint Stage'),
            'hilly': ('⛰️', 'Hilly Punchy Stage'),
            'mountain': ('🏔️', 'Mountain Stage'),
            'itt': ('⏱️', 'Individual Time Trial')
        }
        
        emoji, description = stage_type_map.get(stage_type, ('🏁', 'Stage'))

        lines = [
            f"\t### 🏆 Stage {stage_number} TDF Morning Briefing",
            "",
            f"\t**{emoji} Stage Type**: {description}"
        ]

        return "\n".join(lines)

    def _generate_tdf_metrics_summary(self, metrics: Dict[str, Any], tdf_decision) -> str:
        """Generate TDF metrics and recommendation summary matching documentation format."""
        lines = [
            "\t#### 📊 Readiness Check:",
            f"\t- Readiness Score: {metrics.get('readiness_score', 'N/A')}/100",
            f"\t- TSB (Form): {metrics.get('tsb', 'N/A')}",
            f"\t- CTL (Fitness): {metrics.get('ctl', 'N/A')}",
            "",
            "\t#### 🎯 Today's Recommendation:",
            f"\t- **Ride Mode**: {tdf_decision.recommended_ride_mode.upper()}",
            f"\t- **Expected Points**: {tdf_decision.expected_points}",
            f"\t- **Rationale**: {tdf_decision.mode_rationale}"
        ]

        return "\n".join(lines)

    def _generate_tdf_points_summary(self, tdf_decision, points_status: Dict[str, Any], config) -> str:
        """Generate points and bonus summary matching documentation format."""
        lines = [
            "\t#### 📈 Points Status:",
            f"\t- Current Total: {points_status.get('total_points', 0)} points",
            f"\t- Stages Completed: {points_status.get('stages_completed', 0)}/21",
            "",
            "\t#### 🏆 Bonus Opportunities:",
            "\t- 10 Breakaway Stages",
            "\t- All Mountains in Breakaway"
        ]

        # Show bonus progress
        consecutive = points_status.get('consecutive_stages', 0)
        breakaway_count = points_status.get('breakaway_count', 0)

        lines.extend([
            "",
            "\t#### 🎖️ Bonus Progress:",
            f"\t- 5 consecutive: {consecutive}/5",
            f"\t- 10 breakaways: {breakaway_count}/10"
        ])

        return "\n".join(lines)

    def _generate_tdf_reasoning_summary(self, tdf_decision) -> str:
        """Generate TDF reasoning summary matching documentation format."""
        # Generate strategic notes based on stage type and mode
        stage_type = getattr(tdf_decision, 'stage_type', 'flat')
        ride_mode = tdf_decision.recommended_ride_mode
        
        # Use same notes structure as populate_briefings.py
        notes = {
            'flat': {
                'GC': "Stay protected in the peloton, avoid crashes, and conserve energy. Let the sprinters' teams control the pace.",
                'BREAKAWAY': "Fight for the early break, work together to build a gap, and push hard until the sprinters' teams reel you in."
            },
            'hilly': {
                'GC': "Positioning is key on the climbs. Stay near the front on the ascents to avoid getting gapped by sudden accelerations.",
                'BREAKAWAY': "Perfect terrain for breakaway success. Attack on the climbs, work the descents, and fight for KOM points."
            },
            'mountain': {
                'GC': "Big points available but manage effort carefully. This is where the Tour can be won or lost - balance ambition with sustainability.",
                'BREAKAWAY': "Mountain stages reward the brave. Go early, collect KOM points, and chase the stage dream."
            },
            'itt': {
                'GC': "Pure effort against the clock. Pace evenly, stay aero, and focus on smooth power delivery throughout.",
                'BREAKAWAY': "Time to take risks! Ride above threshold early and see if you can post a surprise result."
            }
        }
        
        strategic_note = notes.get(stage_type, {}).get(ride_mode.upper(), tdf_decision.reason)
        
        lines = [
            "\t#### 📝 Strategic Notes:",
            f"\t{strategic_note}"
        ]

        return "\n".join(lines)

    def _generate_tdf_motivation(self, tdf_decision, stage_info: Dict[str, Any]) -> str:
        """Generate motivational closing - remove this as it's not in docs format."""
        return ""  # Empty return to avoid extra content


# Keep existing functions for backward compatibility
