"""
Tour Coach - Orchestrates training agents to generate daily recommendations.

This module coordinates the Reasoning Agent, Workout Planner, and Communication Agent
to produce cohesive, high-quality daily training recommendations.
"""

import os
from datetime import date
from typing import Dict, Any

from dotenv import load_dotenv

from .mission_config import MissionConfig, bootstrap
from .monitor import get_oura_readiness, get_ctl_atl_tsb
from .reasoner import ReasoningAgent, TDFDecision
from .plan_generator import WorkoutPlanner
from .ai_clients import CommunicationAgent
from .memory_bus import log_observation, log_decision, log_reflection

load_dotenv()


class TourCoach:
    """Orchestrates specialized agents to generate cohesive training recommendations."""

    def __init__(self, config: MissionConfig, use_llm_reasoning: bool = True, llm_model: str = None):
        """Initialize the Tour Coach with configurable reasoning mode.

        Args:
            config: Mission configuration
            use_llm_reasoning: If True, use LLM-based reasoning. If False, use rule-based reasoning. Default: True.
            llm_model: Optional model name for LLM-based reasoning.
        """
        self.config = config
        self.reasoning_agent = ReasoningAgent(use_llm=use_llm_reasoning, model=llm_model)
        self.workout_planner = WorkoutPlanner(config)
        self.communication_agent = CommunicationAgent()

    def generate_daily_recommendation(self, metrics: Dict[str, Any]) -> str:
        """Generate a complete daily training recommendation."""
        current_date = date.today()
        training_phase = self.config.training_phase(current_date)

        # Step 1: Make training decision (with mission config and date for LLM context)
        decision = self.reasoning_agent.make_decision(metrics, self.config, current_date)

        # Step 2: Generate workout plan
        workout = self.workout_planner.generate_workout(decision, training_phase)

        # Step 3: Generate natural language summary
        summary = self.communication_agent.generate_summary(
            decision, workout, metrics, self.config, current_date
        )

        # Log to memory
        log_observation(metrics)
        log_decision({
            "action": decision.action,
            "reason": decision.reason,
            "confidence": decision.confidence
        })
        log_reflection({"summary": summary})

        return summary

    def generate_tdf_recommendation(
        self, 
        metrics: Dict[str, Any], 
        tdf_data: Dict[str, Any] = None
    ) -> str:
        """Generate a TDF-specific training recommendation with ride mode."""
        current_date = date.today()
        
        # Check if TDF simulation is enabled and active
        if not self._is_tdf_active(current_date):
            return self.generate_daily_recommendation(metrics)
        
        # Get current stage information
        stage_info = self._get_current_stage_info(current_date)
        if not stage_info:
            return self.generate_daily_recommendation(metrics)
            
        # Enhance tdf_data with stage info
        if tdf_data is None:
            tdf_data = {}
        tdf_data['stage_info'] = stage_info
        
        # Make TDF decision
        tdf_decision = self.reasoning_agent.make_tdf_decision(
            metrics, self.config, current_date, tdf_data
        )
        
        # Generate TDF-specific summary
        summary = self.communication_agent.generate_tdf_summary(
            tdf_decision, metrics, self.config, current_date, tdf_data
        )
        
        # Log TDF decision
        log_observation(metrics)
        log_decision({
            "action": tdf_decision.action,
            "reason": tdf_decision.reason,
            "confidence": tdf_decision.confidence,
            "tdf_mode": tdf_decision.recommended_ride_mode,
            "stage_type": tdf_decision.stage_type,
            "expected_points": tdf_decision.expected_points
        })
        log_reflection({"tdf_summary": summary})
        
        return summary
    
    def _is_tdf_active(self, current_date: date) -> bool:
        """Check if TDF simulation is enabled and currently active."""
        try:
            tdf_config = getattr(self.config, 'tdf_simulation', {})
            if not tdf_config.get('enabled', False):
                return False
                
            start_date = tdf_config.get('start_date')
            end_date = tdf_config.get('end_date')
            
            if isinstance(start_date, str):
                from datetime import datetime
                start_date = datetime.fromisoformat(start_date).date()
            if isinstance(end_date, str):
                from datetime import datetime
                end_date = datetime.fromisoformat(end_date).date()
                
            return start_date <= current_date <= end_date
        except (AttributeError, TypeError, ValueError):
            return False
    
    def _get_current_stage_info(self, current_date: date) -> Dict[str, Any]:
        """Get information about the current TDF stage."""
        try:
            tdf_config = getattr(self.config, 'tdf_simulation', {})
            start_date = tdf_config.get('start_date')
            
            if isinstance(start_date, str):
                from datetime import datetime
                start_date = datetime.fromisoformat(start_date).date()
            
            # Calculate stage number (1-based)
            days_since_start = (current_date - start_date).days
            stage_number = days_since_start + 1
            
            # Validate stage number
            if stage_number < 1 or stage_number > tdf_config.get('total_stages', 21):
                return None
                
            # Get stage type from configuration
            stages_config = tdf_config.get('stages', {})
            stage_type = stages_config.get(str(stage_number), 'flat')
            
            return {
                'number': stage_number,
                'type': stage_type,
                'date': current_date
            }
        except (AttributeError, TypeError, ValueError):
            return None


def get_version():
    """Get the agent version from VERSION file."""
    try:
        with open("VERSION", "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        return "Unknown"


def run_tour_coach(use_llm_reasoning: bool = None, llm_model: str = None):
    """Main function to run the tour coach and generate daily recommendations.

    Args:
        use_llm_reasoning: If True, use LLM-based reasoning. If None, check environment variable.
        llm_model: Optional model name for LLM-based reasoning.
    """
    # Determine reasoning mode
    if use_llm_reasoning is None:
        use_llm_reasoning = os.getenv("USE_LLM_REASONING", "true").lower() == "true"

    if llm_model is None:
        llm_model = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")

    # Gather current metrics
    readiness, *_ = get_oura_readiness()
    ctl, atl, tsb = get_ctl_atl_tsb()

    metrics = {
        "readiness_score": readiness,
        "ctl": ctl,
        "atl": atl,
        "tsb": tsb
    }

    # Load mission configuration
    cfg = bootstrap("missions/tdf_sim_2025.toml")

    # Create tour coach with specified reasoning mode
    coach = TourCoach(cfg, use_llm_reasoning=use_llm_reasoning, llm_model=llm_model)
    summary = coach.generate_daily_recommendation(metrics)

    # Ensure output directory exists
    os.makedirs("output", exist_ok=True)

    # Write to file
    with open("output/tour_coach_update.txt", "w", encoding="utf-8") as f:
        f.write(summary)

    version = get_version()
    reasoning_mode = "LLM" if use_llm_reasoning else "Rule-based"
    print(f"✅ Tour Coach Agent v{version} daily update generated ({reasoning_mode}): output/tour_coach_update.txt")

    return summary


if __name__ == "__main__":
    run_tour_coach()
