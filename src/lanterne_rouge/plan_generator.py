"""Workout Planning Agent - Generates structured workout plans with time in zones."""
from __future__ import annotations

import logging
from typing import Dict, Any
from dataclasses import dataclass
from datetime import date

from .mission_config import MissionConfig
from .reasoner import TrainingDecision, ReasoningAgent
from .monitor import get_oura_readiness, get_ctl_atl_tsb

logger = logging.getLogger(__name__)


@dataclass
class WorkoutPlan:
    """Structured workout plan with zones and timing."""
    workout_type: str
    description: str
    duration_minutes: int
    zones: Dict[str, int]  # Zone name -> minutes
    estimated_load: int
    intensity_factor: float
    source: str  # "LLM", "template", "fallback"


class WorkoutPlanner:
    """Generates structured workout plans based on training decisions."""

    def __init__(self, config: MissionConfig):
        self.config = config
        self.workout_templates = self._load_workout_templates()

    def _load_workout_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load workout templates for different scenarios."""
        return {
            "recovery": {
                "duration": 60,
                "zones": {"Zone 1": 50, "Zone 2": 10},
                "load": 45,
                "if": 0.6,
                "description": "Easy spinning to promote recovery"
            },
            "endurance": {
                "duration": 90,
                "zones": {"Zone 2": 70, "Zone 3": 20},
                "load": 75,
                "if": 0.7,
                "description": "Steady aerobic effort to maintain fitness"
            },
            "threshold": {
                "duration": 75,
                "zones": {"Zone 2": 45, "Zone 4": 20, "Zone 1": 10},
                "load": 95,
                "if": 0.85,
                "description": "Structured intervals to build racing fitness"
            },
            "vo2max": {
                "duration": 60,
                "zones": {"Zone 2": 30, "Zone 5": 15, "Zone 1": 15},
                "load": 105,
                "if": 0.9,
                "description": "High-intensity work to sharpen racing fitness"
            }
        }

    def generate_workout(self, decision: TrainingDecision, training_phase: str) -> WorkoutPlan:
        """Generate a workout plan based on training decision and phase."""
        # Select base workout type based on decision and phase
        if decision.action == "recover":
            template_key = "recovery"
            workout_type = "Recovery Ride"
        elif decision.action == "ease":
            template_key = "endurance"
            workout_type = "Endurance Ride"
        elif training_phase == "Base":
            template_key = "endurance"
            workout_type = "Base Endurance"
        elif training_phase == "Build":
            template_key = "threshold" if decision.action != "push" else "vo2max"
            workout_type = "Threshold Work" if template_key == "threshold" else "VO2max Intervals"
        elif training_phase == "Peak":
            template_key = "vo2max"
            workout_type = "Peak Power"
        else:  # Taper
            template_key = "endurance"
            workout_type = "Taper Ride"

        # Get template and create workout
        template = self.workout_templates[template_key]

        # Adjust duration based on phase
        duration = template["duration"]
        if training_phase == "Taper":
            duration = int(duration * 0.8)  # Reduce by 20%

        return WorkoutPlan(
            workout_type=workout_type,
            description=template["description"],
            duration_minutes=duration,
            zones=template["zones"].copy(),
            estimated_load=template["load"],
            intensity_factor=template["if"],
            source="template"
        )


# Legacy function for backward compatibility
# All imports now at the module level

def generate_workout_plan(mission_cfg: MissionConfig, _: dict) -> dict:
    """
    Legacy function - use WorkoutPlanner.generate_workout() instead.

    Generate today's workout plan based on mission and current metrics.
    Returns a dict conforming to workout_plan.schema.json.
    """

    print("Generating workout plan...")

    # Gather current metrics
    readiness, *_ = get_oura_readiness()
    ctl, atl, tsb = get_ctl_atl_tsb()
    metrics = {"readiness": readiness, "ctl": ctl, "atl": atl, "tsb": tsb}

    # Make decision using reasoning agent
    reasoning_agent = ReasoningAgent()
    decision = reasoning_agent.make_decision(metrics)

    # Generate workout using planner
    planner = WorkoutPlanner(mission_cfg)
    training_phase = mission_cfg.training_phase(date.today())
    workout = planner.generate_workout(decision, training_phase)

    # Convert to legacy format
    return {
        "today": {
            "type": workout.workout_type,
            "details": workout.description,
            "duration_minutes": workout.duration_minutes,
            "zones": workout.zones,
            "load": workout.estimated_load,
            "intensity_factor": workout.intensity_factor
        },
        "adjustments": [decision.reason]
    }
