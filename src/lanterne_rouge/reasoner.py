"""
Reasoning Agent - Makes structured training decisions based on athlete data.

This module provides the core reasoning engine that analyzes athlete metrics
and makes structured training decisions with clear rationale. Supports both
rule-based and LLM-based reasoning modes.
"""
from __future__ import annotations

import json
import os
from typing import Dict, List, Any
from dataclasses import dataclass
from datetime import date

from .memory_bus import fetch_recent_memories
from .ai_clients import call_llm


@dataclass
class TDFDecision:
    """Extended decision structure for TDF simulation."""
    # Base decision fields
    action: str  # "recover", "maintain", "push", "ease"
    reason: str  # Human-readable explanation
    intensity_recommendation: str  # "low", "moderate", "high"
    flags: List[str]  # ["low_readiness", "negative_tsb", etc.]
    confidence: float  # 0.0 to 1.0

    # TDF-specific fields
    recommended_ride_mode: str  # 'gc', 'breakaway', 'rest'
    mode_rationale: str  # Explanation for ride mode choice
    stage_type: str  # Current stage type
    expected_points: int  # Points available for recommended mode
    bonus_opportunities: List[str]  # Available bonus achievements
    strategic_notes: str  # Additional strategic context


@dataclass
class TrainingDecision:
    """Structured output from reasoning agent."""
    action: str  # "recover", "maintain", "push", "ease"
    reason: str  # Human-readable explanation
    intensity_recommendation: str  # "low", "moderate", "high"
    flags: List[str]  # ["low_readiness", "negative_tsb", etc.]
    confidence: float  # 0.0 to 1.0


class ReasoningAgent:
    """Makes structured training decisions based on athlete metrics.

    Supports both rule-based and LLM-based reasoning modes.
    """

    def __init__(self, use_llm: bool = True, model: str = None):
        """Initialize the reasoning agent.

        Args:
            use_llm: If True, use LLM-based reasoning. If False, use rule-based reasoning. Default: True.
            model: Optional model name for LLM-based reasoning.
        """
        self.use_llm = use_llm
        self.model = model
        self.decision_rules = self._load_decision_rules()

    def _load_decision_rules(self) -> Dict[str, Any]:
        """Load decision rules for training recommendations."""
        return {
            "readiness_thresholds": {
                "low": 70,
                "moderate": 80,
                "high": 90
            },
            "tsb_thresholds": {
                "very_negative": -20,
                "negative": -10,
                "neutral": 5,
                "positive": 15
            },
            "ctl_growth_limits": {
                "max_weekly_increase": 0.1  # 10% per week
            }
        }

    def make_decision(
        self,
        metrics: Dict[str, Any],
        mission_config=None,
        current_date: date = None
    ) -> TrainingDecision:
        """Make a structured training decision based on current metrics.

        Args:
            metrics: Dictionary of athlete metrics (readiness_score, tsb, ctl, atl, etc.)
            mission_config: Optional mission configuration for context
            current_date: Current date for training phase context

        Returns:
            TrainingDecision with structured reasoning output
        """
        if self.use_llm and os.getenv("OPENAI_API_KEY"):
            return self._make_llm_decision(metrics, mission_config, current_date)
        return self._make_rule_based_decision(metrics, mission_config, current_date)

    def _make_rule_based_decision(self, metrics: Dict[str, Any], mission_config=None, current_date: date = None) -> TrainingDecision:
        """Make a rule-based training decision."""
        readiness = metrics.get('readiness_score', 75)
        tsb = metrics.get('tsb', 0)
        # CTL and ATL are logged but not currently used in decision logic
        # They may be used for future enhancements

        flags = []

        # Analyze readiness
        if readiness < self.decision_rules["readiness_thresholds"]["low"]:
            flags.append("low_readiness")

        # Analyze TSB (Training Stress Balance)
        if tsb < self.decision_rules["tsb_thresholds"]["very_negative"]:
            flags.append("very_negative_tsb")
        elif tsb < self.decision_rules["tsb_thresholds"]["negative"]:
            flags.append("negative_tsb")

        # Make decision based on flags
        if "low_readiness" in flags or "very_negative_tsb" in flags:
            return TrainingDecision(
                action="recover",
                reason=f"Readiness at {readiness} and TSB at {tsb:.1f} indicate need for recovery",
                intensity_recommendation="low",
                flags=flags,
                confidence=0.9
            )
        if "negative_tsb" in flags:
            return TrainingDecision(
                action="ease",
                reason=f"TSB at {tsb:.1f} suggests moderate fatigue",
                intensity_recommendation="moderate",
                flags=flags,
                confidence=0.8
            )
        if tsb > self.decision_rules["tsb_thresholds"]["positive"]:
            return TrainingDecision(
                action="push",
                reason=f"TSB at {tsb:.1f} indicates good recovery state",
                intensity_recommendation="high",
                flags=flags,
                confidence=0.8
            )
        return TrainingDecision(
            action="maintain",
            reason="Metrics indicate steady training state",
            intensity_recommendation="moderate",
            flags=flags,
                confidence=0.7
            )

    def _make_llm_decision(
        self,
        metrics: Dict[str, Any],
        mission_config=None,
        current_date: date = None
    ) -> TrainingDecision:
        """Make an LLM-based training decision."""
        try:
            # Get recent memories for context
            recent_memories = fetch_recent_memories(limit=5)

            # Build training context
            training_context = ""
            if mission_config and current_date:
                phase = mission_config.training_phase(current_date)
                next_phase_start = mission_config.next_phase_start(current_date)
                days_to_next = (next_phase_start - current_date).days if next_phase_start else None
                days_to_goal = (mission_config.goal_date - current_date).days

                training_context = f"""
Training Phase: {phase}
Days to next phase: {days_to_next}
Days to goal: {days_to_goal}
"""

            # Build system prompt
            system_prompt = """You are an expert cycling coach AI speaking directly to your athlete. \
Analyze their metrics and training context to make a structured training decision.

You must respond with a valid JSON object containing:
{
  "action": "recover|ease|maintain|push",
  "reason": "detailed explanation speaking directly to the athlete (use 'you', 'your')",
  "intensity_recommendation": "low|moderate|high",
  "flags": ["flag1", "flag2"],
  "confidence": 0.8
}

Guidelines for the reason field:
- Address the athlete directly using "you" and "your"
- Use plain, conversational language (avoid jargon when possible)
- Be encouraging and supportive
- Explain WHY this decision helps them reach their goals
- Keep technical terms simple or explain them briefly

Consider:
- Readiness score (0-100): Below 70 suggests recovery need
- TSB (Training Stress Balance): Negative values indicate fatigue
- CTL (Chronic Training Load): Long-term fitness
- ATL (Acute Training Load): Recent fatigue
- Training phase and proximity to goals"""

            # Build user prompt
            user_prompt = f"""My current metrics:
{json.dumps(metrics, indent=2)}

{training_context}

My recent training history:
{json.dumps(recent_memories, indent=2) if recent_memories else "No recent history available"}

Please provide a structured training decision based on my metrics and context. Remember to speak to me directly and explain your reasoning in plain language."""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]

            # Call LLM with JSON mode
            response = call_llm(messages, model=self.model, force_json=True)
            print(f"✅ LLM Response received from {self.model or 'default model'} for training decision")

            # Parse JSON response
            try:
                decision_data = json.loads(response)
                return TrainingDecision(
                    action=decision_data.get("action", "maintain"),
                    reason=decision_data.get("reason", "LLM-based decision"),
                    intensity_recommendation=decision_data.get("intensity_recommendation", "moderate"),
                    flags=decision_data.get("flags", []),
                    confidence=decision_data.get("confidence", 0.7)
                )
            except json.JSONDecodeError:
                # Fallback to rule-based if JSON parsing fails
                return self._make_rule_based_decision(metrics, mission_config, current_date)

        except Exception as e:
            print(f"Error in LLM decision making: {e}")
            # Fallback to rule-based decision
            return self._make_rule_based_decision(metrics, mission_config, current_date)

    def make_tdf_decision(
        self,
        metrics: Dict[str, Any],
        mission_config=None,
        current_date: date = None,
        tdf_data: Dict[str, Any] = None
    ) -> TDFDecision:
        """Make a TDF-specific decision including ride mode recommendation.

        Args:
            metrics: Dictionary of athlete metrics
            mission_config: Mission configuration with TDF settings
            current_date: Current date
            tdf_data: TDF-specific data (current points, stage info, etc.)

        Returns:
            TDFDecision with both training and ride mode recommendations
        """
        if self.use_llm and os.getenv("OPENAI_API_KEY"):
            return self._make_llm_tdf_decision(metrics, mission_config, current_date, tdf_data)
        return self._make_rule_based_tdf_decision(metrics, mission_config, current_date, tdf_data)

    def _make_rule_based_tdf_decision(
        self,
        metrics: Dict[str, Any],
        mission_config=None,
        current_date: date = None,
        tdf_data: Dict[str, Any] = None
    ) -> TDFDecision:
        """Make a rule-based TDF decision."""
        # First get base training decision
        base_decision = self._make_rule_based_decision(metrics, mission_config, current_date)

        # Extract TDF configuration
        tdf_config = getattr(mission_config, 'tdf_simulation', {}) if mission_config else {}
        safety_config = tdf_config.get('safety', {})

        readiness = metrics.get('readiness_score', 75)
        tsb = metrics.get('tsb', 0)

        # Determine stage info
        stage_info = tdf_data.get('stage_info', {}) if tdf_data else {}
        stage_type = stage_info.get('type', 'flat')
        stage_number = stage_info.get('number', 1)

        # Get points for this stage type
        points_config = tdf_config.get('points', {}).get(stage_type, {'gc': 5, 'breakaway': 8})

        # Rule-based ride mode decision
        if (readiness < safety_config.get('force_rest_readiness', 60) or
            tsb < safety_config.get('force_rest_tsb', -20)):
            ride_mode = 'rest'
            expected_points = 0
            mode_rationale = f"Safety first - readiness {readiness} or TSB {tsb:.1f} requires rest"
        elif (readiness < safety_config.get('prefer_gc_readiness', 75) or
              tsb < safety_config.get('prefer_gc_tsb', -10)):
            ride_mode = 'gc'
            expected_points = points_config.get('gc', 5)
            mode_rationale = f"Conservative GC mode - readiness {readiness}, TSB {tsb:.1f}"
        elif (readiness > safety_config.get('prefer_breakaway_readiness', 80) and
              tsb > safety_config.get('prefer_breakaway_tsb', -5)):
            ride_mode = 'breakaway'
            expected_points = points_config.get('breakaway', 8)
            mode_rationale = f"Aggressive breakaway mode - excellent readiness {readiness}, TSB {tsb:.1f}"
        else:
            ride_mode = 'gc'
            expected_points = points_config.get('gc', 5)
            mode_rationale = f"Balanced GC mode - readiness {readiness}, TSB {tsb:.1f}"

        # Analyze bonus opportunities (simplified for rule-based)
        bonus_opportunities = []
        points_status = tdf_data.get('points_status', {}) if tdf_data else {}
        consecutive = points_status.get('consecutive_stages', 0)
        if consecutive == 4:
            bonus_opportunities.append("5 consecutive stages (1 more needed!)")

        return TDFDecision(
            action=base_decision.action,
            reason=base_decision.reason,
            intensity_recommendation=base_decision.intensity_recommendation,
            flags=base_decision.flags,
            confidence=base_decision.confidence,
            recommended_ride_mode=ride_mode,
            mode_rationale=mode_rationale,
            stage_type=stage_type,
            expected_points=expected_points,
            bonus_opportunities=bonus_opportunities,
            strategic_notes=f"Stage {stage_number} ({stage_type}) - {mode_rationale}"
        )

    def _make_llm_tdf_decision(
        self,
        metrics: Dict[str, Any],
        mission_config=None,
        current_date: date = None,
        tdf_data: Dict[str, Any] = None
    ) -> TDFDecision:
        """Make an LLM-based TDF decision with ride mode recommendation."""
        try:
            # Get recent memories for context
            recent_memories = fetch_recent_memories(limit=7)

            # Extract TDF context
            tdf_config = getattr(mission_config, 'tdf_simulation', {}) if mission_config else {}
            stage_info = tdf_data.get('stage_info', {}) if tdf_data else {}
            points_status = tdf_data.get('points_status', {}) if tdf_data else {}

            # Build training context
            training_context = ""
            if mission_config and current_date:
                phase = mission_config.training_phase(current_date)
                days_to_goal = (mission_config.goal_date - current_date).days
                training_context = f"Training Phase: {phase}\nDays to goal: {days_to_goal}\n"

            # Build TDF context
            tdf_context = ""
            if stage_info:
                stage_number = stage_info.get('number', 1)
                stage_type = stage_info.get('type', 'flat')
                points_for_stage = tdf_config.get('points', {}).get(stage_type, {'gc': 5, 'breakaway': 8})

                tdf_context = f"""
TDF SIMULATION STAGE {stage_number}:
- Stage Type: {stage_type.title()}
- Points Available: GC Mode = {points_for_stage.get('gc', 5)}, Breakaway Mode = {points_for_stage.get('breakaway', 8)}
- Current Total Points: {points_status.get('total_points', 0)}
- Stages Completed: {points_status.get('stages_completed', 0)}/21
- Consecutive Stages: {points_status.get('consecutive_stages', 0)}
- Breakaway Stages: {points_status.get('breakaway_count', 0)}

BONUS OPPORTUNITIES:
- 5 Consecutive Stages: {points_status.get('consecutive_stages', 0)}/5 (+5 points)
- 10 Breakaway Stages: {points_status.get('breakaway_count', 0)}/10 (+15 points)
- All Mountains in Breakaway: Progress tracked
- Complete Final Week: Available in stages 16-21
- All GC Mode: Alternative strategy (+25 points)
"""

            # Build enhanced system prompt for TDF
            system_prompt = f"""You are an expert cycling coach AI for the Tour de France Indoor Simulation. You're speaking directly to your athlete about today's stage.

You must respond with a valid JSON object containing:
{{
  "action": "recover|ease|maintain|push",
  "reason": "explanation for training decision (use 'you', 'your')",
  "intensity_recommendation": "low|moderate|high",
  "flags": ["flag1", "flag2"],
  "confidence": 0.8,
  "recommended_ride_mode": "rest|gc|breakaway",
  "mode_rationale": "explanation for ride mode choice (use 'you', 'your')",
  "stage_type": "{stage_info.get('type', 'flat')}",
  "expected_points": 0,
  "bonus_opportunities": ["opportunity1", "opportunity2"],
  "strategic_notes": "additional strategic context"
}}

RIDE MODES:
- REST: Force recovery day (0 points) - use when readiness <60 or TSB <-20
- GC MODE: Conservative completion focus (base points only)
- BREAKAWAY MODE: Aggressive performance focus (higher points + bonuses)

DECISION FACTORS:
- Athlete Safety: Priority #1 - never compromise health for points
- Physiological State: Readiness score (0-100), TSB (training stress balance)
- Strategic Context: Current points position, bonus opportunities, remaining stages
- Stage Type: Different points available for flat/hilly/mountain/ITT stages

COMMUNICATION STYLE:
- Address athlete directly ("you", "your")
- Be encouraging and supportive
- Explain WHY this strategy helps their TDF campaign
- Balance performance with safety"""

            # Build user prompt with rest day check
            rest_day_info = ""
            if tdf_data and tdf_data.get('is_rest_day'):
                rest_day_num = tdf_data.get('rest_day_number', 1)
                rest_day_info = f"""

🛌 IMPORTANT: TODAY IS REST DAY {rest_day_num}
- This is an official Tour de France rest day
- NO stage recommendation should be given
- Focus on recovery, analysis, and strategic planning
- Recommended ride mode: REST (0 points)
- Provide recovery advice and preparation for tomorrow's stage"""

            user_prompt = f"""My current metrics:
{json.dumps(metrics, indent=2)}

{training_context}

{tdf_context}

{rest_day_info}

My recent training history:
{json.dumps(recent_memories[-5:], indent=2) if recent_memories else "No recent history available"}

Please provide both a training decision AND a ride mode recommendation for today's TDF stage. Remember to speak to me directly and explain your reasoning for both the training approach and the strategic ride mode choice."""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]

            # Call LLM with JSON mode
            response = call_llm(messages, model=self.model, force_json=True)
            print(f"✅ LLM Response received from {self.model or 'default model'} for TDF decision")

            # Parse JSON response
            try:
                decision_data = json.loads(response)
                return TDFDecision(
                    action=decision_data.get("action", "maintain"),
                    reason=decision_data.get("reason", "LLM-based training decision"),
                    intensity_recommendation=decision_data.get("intensity_recommendation", "moderate"),
                    flags=decision_data.get("flags", []),
                    confidence=decision_data.get("confidence", 0.7),
                    recommended_ride_mode=decision_data.get("recommended_ride_mode", "gc"),
                    mode_rationale=decision_data.get("mode_rationale", "LLM-based ride mode decision"),
                    stage_type=decision_data.get("stage_type", stage_info.get('type', 'flat')),
                    expected_points=decision_data.get("expected_points", 5),
                    bonus_opportunities=decision_data.get("bonus_opportunities", []),
                    strategic_notes=decision_data.get("strategic_notes", "")
                )
            except json.JSONDecodeError:
                # Fallback to rule-based if JSON parsing fails
                return self._make_rule_based_tdf_decision(metrics, mission_config, current_date, tdf_data)

        except Exception as e:
            print(f"Error in LLM TDF decision making: {e}")
            # Fallback to rule-based decision
            return self._make_rule_based_tdf_decision(metrics, mission_config, current_date, tdf_data)


# Legacy function for backward compatibility


def decide_adjustment(
    readiness_score: float,
    readiness_details: dict[str, float],
    ctl: float,
    atl: float,
    tsb: float,
    cfg=None,
    *,
    mission_cfg=None,
) -> list[str]:
    """Legacy function - use ReasoningAgent.make_decision() instead."""
    reasoning_agent = ReasoningAgent()
    metrics = {
        'readiness_score': readiness_score,
        'ctl': ctl,
        'atl': atl,
        'tsb': tsb
    }
    decision = reasoning_agent.make_decision(metrics)
    return [decision.reason]
