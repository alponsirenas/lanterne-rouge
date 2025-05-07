import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from lanterne_rouge import tour_coach
from pathlib import Path
from lanterne_rouge.mission_config import bootstrap
import streamlit as st
from lanterne_rouge.mission_config import load_config, cache_to_sqlite

cfg = load_config("missions/ana_may24.toml")
st.json(cfg.dict())


# New function to run daily logic
def run_daily_logic():
    # Assuming tour_coach.run() returns a tuple: (summary: str, log: dict)
    return tour_coach.run()

# Boot on import
_mission_cfg = bootstrap(Path("missions/ana_may24.toml"))