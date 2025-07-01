"""
Reasoning Agent - Makes structured training decisions based on athlete data.

This module provides the core reasoning engine that analyzes athlete metrics
and makes structured training decisions with clear rationale. Supports both
rule-based and LLM-based reasoning modes.
"""
from __future__ import annotations

import json
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import date

from .memory_bus import fetch_recent_memories
from .ai_clients import call_llm


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
    
    def make_decision(self, metrics: Dict[str, Any], mission_config=None, current_date: date = None) -> TrainingDecision:
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
        else:
            return self._make_rule_based_decision(metrics, mission_config, current_date)
    
    def _make_rule_based_decision(self, metrics: Dict[str, Any], mission_config=None, current_date: date = None) -> TrainingDecision:
        """Make a rule-based training decision."""
        readiness = metrics.get('readiness_score', 75)
        tsb = metrics.get('tsb', 0)
        ctl = metrics.get('ctl', 30)
        atl = metrics.get('atl', 35)
        
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
        elif "negative_tsb" in flags:
            return TrainingDecision(
                action="ease",
                reason=f"TSB at {tsb:.1f} suggests moderate fatigue",
                intensity_recommendation="moderate",
                flags=flags,
                confidence=0.8
            )
        elif tsb > self.decision_rules["tsb_thresholds"]["positive"]:
            return TrainingDecision(
                action="push",
                reason=f"TSB at {tsb:.1f} indicates good recovery state",
                intensity_recommendation="high",
                flags=flags,
                confidence=0.8
            )
        else:
            return TrainingDecision(
                action="maintain",
                reason="Metrics indicate steady training state",
                intensity_recommendation="moderate",
                flags=flags,
                confidence=0.7
            )
    
    def _make_llm_decision(self, metrics: Dict[str, Any], mission_config=None, current_date: date = None) -> TrainingDecision:
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
            system_prompt = """You are an expert cycling coach AI speaking directly to your athlete. Analyze their metrics and training context to make a structured training decision.

You must respond with a valid JSON object containing:
{
  "action": "recover|ease|maintain|push",
  "reason": "detailed explanation of your decision speaking directly to the athlete in first person (use 'you', 'your')",
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
