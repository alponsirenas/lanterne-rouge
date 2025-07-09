#!/usr/bin/env python3
"""
Test script to verify that points accumulation works correctly
when a new stage is added to the existing database.
"""

import sys
from pathlib import Path
from datetime import date
import json

# Add project paths
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from lanterne_rouge.tdf_tracker import TDFTracker

def test_points_accumulation():
    """Test that points accumulate correctly when adding a new stage."""
    print("🧪 Testing TDF Points Accumulation")
    print("=" * 40)
    
    # Initialize tracker with existing data
    tracker = TDFTracker()
    
    # Show current state
    current_status = tracker.get_points_status()
    print(f"Current state:")
    print(f"  Total Points: {current_status['total_points']}")
    print(f"  Stages Completed: {current_status['stages_completed']}")
    print(f"  GC Count: {current_status['gc_count']}")
    print(f"  Breakaway Count: {current_status['breakaway_count']}")
    print()
    
    # Simulate adding Stage 3 (July 8, 2025)
    print("Simulating Stage 3 completion...")
    test_date = date(2025, 7, 8)
    
    # Check if stage already exists
    if tracker.is_stage_completed_today(test_date):
        print("❌ Stage 3 already completed - cannot test accumulation")
        return
    
    # Add Stage 3 as GC effort (worth 7 points)
    result = tracker.add_stage_completion(
        stage_date=test_date,
        stage_number=3,
        stage_type="hilly",
        ride_mode="gc",
        points_earned=7,
        activity_data={
            "duration_minutes": 90.0,
            "distance_km": 35.2,
            "normalized_power": 165.0,
            "intensity_factor": 0.75,
            "tss": 67.5,
            "effort_level": "tempo"
        }
    )
    
    if "error" in result:
        print(f"❌ Error: {result['error']}")
        return
    
    # Show new state
    new_status = tracker.get_points_status()
    print(f"New state after Stage 3:")
    print(f"  Total Points: {new_status['total_points']} (was {current_status['total_points']})")
    print(f"  Stages Completed: {new_status['stages_completed']} (was {current_status['stages_completed']})")
    print(f"  GC Count: {new_status['gc_count']} (was {current_status['gc_count']})")
    print()
    
    # Verify accumulation
    expected_total = current_status['total_points'] + 7
    if new_status['total_points'] == expected_total:
        print("✅ Points accumulation working correctly!")
        print(f"   Expected: {expected_total}, Got: {new_status['total_points']}")
    else:
        print("❌ Points accumulation FAILED!")
        print(f"   Expected: {expected_total}, Got: {new_status['total_points']}")
        return
    
    # Show Stage 3 data
    stage_3_data = tracker.get_stage_info_for_date(test_date)
    if stage_3_data:
        print(f"Stage 3 details:")
        print(f"  Mode: {stage_3_data['ride_mode'].upper()}")
        print(f"  Points: {stage_3_data['points_earned']}")
        print(f"  Power: {stage_3_data['activity_data']['normalized_power']}W")
        print(f"  IF: {stage_3_data['activity_data']['intensity_factor']}")
    
    print("\n🎯 Test Summary:")
    print(f"   Original Total: {current_status['total_points']} points")
    print(f"   Stage 3 Added: +7 points")
    print(f"   New Total: {new_status['total_points']} points")
    print("   ✅ Accumulation verified!")

if __name__ == "__main__":
    test_points_accumulation()
