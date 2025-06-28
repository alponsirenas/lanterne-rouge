"""Script to run the Tour Coach application for daily training guidance."""

import os
import sys
from pathlib import Path

# Add the project root directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

try:
    import streamlit as st
except ImportError:
    # Create a mock st object if streamlit is not installed
    class StreamlitMock:
        """Mock Streamlit class for environments where Streamlit is not installed."""
        runtime = None

        def json(self, data):
            """Mock json display method."""
            return None

    st = StreamlitMock()

from lanterne_rouge import tour_coach
from lanterne_rouge.ai_clients import generate_workout_adjustment
from lanterne_rouge.mission_config import bootstrap


# Function to get fresh mission config on each run
def get_mission_config():
    """Reload mission config each time to ensure latest values are used."""
    return bootstrap(Path("missions/tdf_sim_2025.toml"))


# Only output the mission configuration when running via Streamlit
if (
    os.environ.get("RUN_WITH_STREAMLIT")
    or getattr(st, "runtime", None) and st.runtime.exists()
):
    _mission_cfg = get_mission_config()
    st.json(_mission_cfg.model_dump())


# New function to run daily logic
def run_daily_logic():
    """Execute the Tour Coach logic for the day."""
    # Get the latest mission config
    mission_cfg = get_mission_config()

    # Pass the loaded mission configuration into the tour_coach runner
    summary, log = tour_coach.run()

    # Generate LLM-based summaries
    llm_summaries = generate_workout_adjustment(
        readiness_score=log["readiness"]["score"],
        readiness_details=log["readiness"],
        ctl=log["ctl"],
        atl=log["atl"],
        tsb=log["tsb"],
        mission_cfg=mission_cfg
    )

    # Append LLM summaries to the summary
    summary += "\n\nLLM-Generated Summaries:\n"
    for line in llm_summaries:
        summary += f"- {line}\n"

    return summary, log
