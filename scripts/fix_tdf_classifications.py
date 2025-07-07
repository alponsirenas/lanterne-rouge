#!/usr/bin/env python3
"""
Fix TDF stage misclassifications and update the database.
"""

import sys
import os
import json
from pathlib import Path
from datetime import date

# Add project paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from lanterne_rouge.tdf_tracker import TDFTracker
from lanterne_rouge.mission_config import bootstrap


def fix_tdf_classifications():
    """Fix the misclassified TDF stages."""
    print("🔧 TDF STAGE CLASSIFICATION FIX")
    print("=" * 45)
    
    # Load tracker
    tracker = TDFTracker()
    
    # Load current data
    try:
        with open("output/tdf_points.json", "r", encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("❌ TDF points file not found!")
        return
    
    print(f"📊 CURRENT STATUS:")
    print(f"   • Stages: {len(data.get('stages', []))}")
    print(f"   • Total points: {data.get('total_points', 0)}")
    
    # Define corrections
    corrections = [
        {
            'stage_number': 1,
            'stage_date': '2025-07-05',
            'old_mode': 'breakaway',
            'old_points': 8,
            'new_mode': 'gc',
            'new_points': 5,
            'stage_type': 'flat'
        },
        {
            'stage_number': 2,
            'stage_date': '2025-07-06',
            'old_mode': 'breakaway',
            'old_points': 11,
            'new_mode': 'gc',
            'new_points': 7,
            'stage_type': 'hilly'
        }
    ]
    
    print(f"\n🔧 APPLYING CORRECTIONS:")
    
    # Apply corrections
    stages = data.get('stages', {})
    total_adjustment = 0
    
    for correction in corrections:
        # Find the stage to correct using date key
        stage_date = correction['stage_date']
        if stage_date in stages:
            stage = stages[stage_date]
            old_points = stage.get('points_earned', 0)
            old_mode = stage.get('ride_mode', 'unknown')
            
            print(f"   • Stage {correction['stage_number']}: {old_mode.upper()} ({old_points} pts) → {correction['new_mode'].upper()} ({correction['new_points']} pts)")
            
            # Update the stage
            stage['ride_mode'] = correction['new_mode']
            stage['points_earned'] = correction['new_points']
            
            # Track adjustment
            point_adjustment = correction['new_points'] - old_points
            total_adjustment += point_adjustment
        else:
            print(f"   ⚠️ Stage {correction['stage_number']} ({stage_date}) not found in database")
    
    # Update total points
    old_total = data.get('total_points', 0)
    new_total = old_total + total_adjustment
    data['total_points'] = new_total
    
    # Update counts (need to recalculate since we changed classifications)
    breakaway_count = 0
    gc_count = 0
    for stage_data in data.get('stages', {}).values():
        mode = stage_data.get('ride_mode', '')
        if mode == 'breakaway':
            breakaway_count += 1
        elif mode == 'gc':
            gc_count += 1
    
    data['breakaway_count'] = breakaway_count
    data['gc_count'] = gc_count
    
    print(f"\n📊 SUMMARY:")
    print(f"   • Total point adjustment: {total_adjustment:+d}")
    print(f"   • Old total: {old_total}")
    print(f"   • New total: {new_total}")
    
    # Save corrected data
    print(f"\n💾 Saving corrections...")
    try:
        with open("output/tdf_points.json", "w", encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"   ✅ Database updated successfully!")
        
        # Verify the fix
        print(f"\n🔍 VERIFICATION:")
        verified_tracker = TDFTracker()
        
        # Check if tracker can load the data properly
        stages_data = verified_tracker._load_stages()
        verified_total = sum(stage.get('points_earned', 0) for stage in stages_data.get('stages', {}).values())
        
        print(f"   • Verified total points: {verified_total}")
        print(f"   • Database integrity: {'✅ GOOD' if verified_total == new_total else '❌ MISMATCH'}")
        
    except Exception as e:
        print(f"   ❌ Failed to save: {e}")
        return
    
    print(f"\n🎉 Classification fix complete!")
    print(f"Your TDF points have been corrected from {old_total} to {new_total}.")


if __name__ == "__main__":
    fix_tdf_classifications()
