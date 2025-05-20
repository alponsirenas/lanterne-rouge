import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from lanterne_rouge import tour_coach
from pathlib import Path
from lanterne_rouge.mission_config import bootstrap
import streamlit as st

# Boot on import
_mission_cfg = bootstrap(Path("missions/tdf_sim_2025.toml"))

st.json(_mission_cfg.dict())


# New function to run daily logic
def run_daily_logic():
    # Pass the loaded mission configuration into the tour_coach runner
    return tour_coach.run(_mission_cfg)