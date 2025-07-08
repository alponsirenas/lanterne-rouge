#!/usr/bin/env python3
"""
Add missing Stage 2 to the TDF database.
"""

import sys
import os
import json
from pathlib import Path
from datetime import date, datetime

# Add project paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from lanterne_rouge.validation import validate_activity_data, calculate_power_metrics
from lanterne_rouge.mission_config import bootstrap


def add_missing_stage2():
    """Add the missing Stage 2 to the database."""
    print("➕ ADDING MISSING STAGE 2")
    print("=" * 35)
    
    # Load current data
    try:
        with open("output/tdf_points.json", "r", encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("❌ TDF points file not found!")
        return
    
    # Define Stage 2 data
    stage2_activity = {
        'name': 'Stage 2 TDF 2025 indoor simulation GC',
        'moving_time': 3600,  # 60.0 minutes
        'distance': 24500,    # 24.5km
        'weighted_average_watts': 87,
        'average_watts': 87,
        'total_elevation_gain': 100,
        'suffer_score': 55
    }
    
    # Process the activity data to get correct classification
    mission_cfg = bootstrap("missions/tdf_sim_2025.toml")
    ftp = getattr(mission_cfg.athlete, 'ftp', 200)
    
    activity_data = validate_activity_data(stage2_activity)
    power_metrics = calculate_power_metrics(activity_data, ftp)
    activity_data.update(power_metrics)
    
    # Determine correct classification (should be GC based on our analysis)
    stage2_data = {
        "stage_number": 2,
        "stage_type": "hilly",
        "ride_mode": "gc",
        "points_earned": 7,  # hilly GC = 7 points
        "completed_at": "2025-07-06T20:00:00.000000",  # Approximate evening time
        "activity_data": {
            "duration_minutes": activity_data.get("duration_minutes", 60.0),
            "distance_km": activity_data.get("distance_km", 24.5),
            "normalized_power": activity_data.get("normalized_power", 87),
            "intensity_factor": activity_data.get("intensity_factor", 0.680),
            "tss": activity_data.get("tss", 46.2),
            "effort_level": activity_data.get("effort_level", "aerobic")
        }
    }
    
    print(f"📊 STAGE 2 ANALYSIS:")
    print(f"   • Power: {activity_data.get('normalized_power')}W")
    print(f"   • IF: {activity_data.get('intensity_factor', 0):.3f}")
    print(f"   • TSS: {activity_data.get('tss', 0):.1f}")
    print(f"   • Classification: {stage2_data['ride_mode'].upper()}")
    print(f"   • Points: {stage2_data['points_earned']}")
    
    # Add Stage 2 to the database
    stage_date = "2025-07-06"
    data['stages'][stage_date] = stage2_data
    
    # Update totals
    old_total = data.get('total_points', 0)
    old_stages = data.get('stages_completed', 0)
    old_consecutive = data.get('consecutive_stages', 0)
    old_gc_count = data.get('gc_count', 0)
    
    new_total = old_total + stage2_data['points_earned']
    new_stages = old_stages + 1
    new_consecutive = old_consecutive + 1  # Consecutive since Stage 1 was also completed
    new_gc_count = old_gc_count + 1
    
    data['total_points'] = new_total
    data['stages_completed'] = new_stages
    data['consecutive_stages'] = new_consecutive
    data['gc_count'] = new_gc_count
    data['last_updated'] = datetime.now().isoformat()
    
    print(f"\n📊 DATABASE UPDATE:")
    print(f"   • Stages: {old_stages} → {new_stages}")
    print(f"   • Total points: {old_total} → {new_total}")
    print(f"   • Consecutive: {old_consecutive} → {new_consecutive}")
    print(f"   • GC count: {old_gc_count} → {new_gc_count}")
    
    # Save updated data
    print(f"\n💾 Saving Stage 2...")
    try:
        with open("output/tdf_points.json", "w", encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"   ✅ Stage 2 added successfully!")
        
    except Exception as e:
        print(f"   ❌ Failed to save: {e}")
        return
    
    print(f"\n🎉 Stage 2 recovery complete!")
    print(f"Your TDF status is now:")
    print(f"   • Stages completed: 2/21")
    print(f"   • Total points: {new_total}")
    print(f"   • Stage 1: GC (5 pts)")
    print(f"   • Stage 2: GC (7 pts)")


if __name__ == "__main__":
    add_missing_stage2()
