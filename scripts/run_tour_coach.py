import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from lanterne_rouge import tour_coach


# New function to run daily logic
def run_daily_logic():
    # Assuming tour_coach.run() returns a tuple: (summary: str, log: dict)
    return tour_coach.run()