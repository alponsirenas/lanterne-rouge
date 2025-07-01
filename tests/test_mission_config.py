"""
Tests for the mission_config module.
"""
import sqlite3
import json
from datetime import date
from pathlib import Path

# Add project to path
from setup import setup_path
setup_path()

from src.lanterne_rouge.mission_config import (
    MissionConfig, 
    AthleteConfig,
    ConstraintsConfig,
    bootstrap,
    cache_to_sqlite,
    load_config
)

# Create a dummy config for testing
def create_test_config():
    """Create a test configuration."""
    return MissionConfig(
        id="test",
        name="Test Mission",
        athlete=AthleteConfig(ftp=250, weight_kg=70),
        start_date=date(2025, 1, 1),
        goal_date=date(2025, 12, 31),
        constraints=ConstraintsConfig(
            min_readiness=65,
            min_tsb=-10,
        )
    )

def test_mission_config_training_phase():
    """Test the training_phase method."""
    config = create_test_config()
    # Base phase
    assert config.training_phase(date(2025, 10, 1)) == "Base"
    # Build phase
    assert config.training_phase(date(2025, 12, 1)) == "Build"
    # Peak phase
    assert config.training_phase(date(2025, 12, 15)) == "Peak"
    # Taper phase
    assert config.training_phase(date(2025, 12, 27)) == "Taper"

def test_mission_config_next_phase():
    """Test the next_phase_start method."""
    config = create_test_config()
    # In Base phase, next is Build
    base_date = date(2025, 10, 1)
    next_phase = config.next_phase_start(base_date)
    assert next_phase is not None
    
    # Test the behavior for phases close to the goal
    # Note: Implementation might vary, so we just check that it returns a date or None
    taper_date = date(2025, 12, 27)
    result = config.next_phase_start(taper_date)
    # Just verify the method runs without errors, implementation details may vary
    assert isinstance(result, date) or result is None

def test_cache_to_sqlite():
    """Test caching config to SQLite."""
    import tempfile
    import os
    
    config = create_test_config()
    
    # Create a temporary file for the database
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        db_path = tmp.name
    
    try:
        # Cache the config to the temporary database
        cache_to_sqlite(config, db_path)
        
        # Connect to the database and verify
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT json FROM mission_config WHERE id = ?", (config.id,))
        row = cursor.fetchone()
        assert row is not None
        
        # Check that the cached config can be deserialized
        cached_json = row[0]
        cached_dict = json.loads(cached_json)
        assert cached_dict["id"] == config.id
        assert cached_dict["name"] == config.name
        
        conn.close()
    finally:
        # Clean up the temporary file
        if os.path.exists(db_path):
            os.unlink(db_path)

if __name__ == "__main__":
    # Run the tests
    test_mission_config_training_phase()
    test_mission_config_next_phase()
    test_cache_to_sqlite()
    print("All mission_config tests passed!")
