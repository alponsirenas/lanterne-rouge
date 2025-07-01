#!/usr/bin/env python3
"""
Setup utilities for Lanterne Rouge tests.
Provides path configuration to import modules from src.
"""

import sys
from pathlib import Path

def setup_path():
    """Add the src directory to the Python path."""
    # Get the directory of this file
    current_dir = Path(__file__).parent
    
    # Add the project root to the path
    project_root = current_dir.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
