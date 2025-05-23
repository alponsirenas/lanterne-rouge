import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from lanterne_rouge import tour_coach
from pathlib import Path
from lanterne_rouge.mission_config import bootstrap
import streamlit as st
from lanterne_rouge.ai_clients import generate_workout_adjustment

# Boot on import
_mission_cfg = bootstrap(Path("missions/tdf_sim_2025.toml"))

# Only output the mission configuration when running via Streamlit
if (
    os.environ.get("RUN_WITH_STREAMLIT")
    or getattr(st, "runtime", None) and st.runtime.exists()
):
    st.json(_mission_cfg.dict())


# New function to run daily logic
def run_daily_logic():
    """Execute the Tour Coach logic for the day."""
    # Pass the loaded mission configuration into the tour_coach runner
    summary, log = tour_coach.run(_mission_cfg)
    
    # Generate LLM-based summaries
    llm_summaries = generate_workout_adjustment(
        readiness_score=log["readiness"]["score"],
        readiness_details=log["readiness"],
        ctl=log["ctl"],
        atl=log["atl"],
        tsb=log["tsb"],
        mission_cfg=_mission_cfg
    )
    
    # Append LLM summaries to the summary
    summary += "\n\nLLM-Generated Summaries:\n"
    for line in llm_summaries:
        summary += f"- {line}\n"
    
    return summary, log
