import sys
import os

# Add src/ to PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from lanterne_rouge import tour_coach