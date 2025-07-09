#!/usr/bin/env python3
"""
Diagnostic tool to re-analyze TDF stages and fix incorrect classifications.
"""

import sys
import os
from pathlib import Path
from datetime import date, datetime
import json

# Add project paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from lanterne_rouge.mission_config import bootstrap
from lanterne_rouge.tdf_tracker import TDFTracker
from lanterne_rouge.validation import validate_activity_data, calculate_power_metrics
from scripts.evening_tdf_check import analyze_activity_with_llm, calculate_stage_points


def diagnose_stage(stage_date, stage_number, stage_type, activity_data):
    """Diagnose a single stage's classification."""
    print(f"\n🔍 DIAGNOSING STAGE {stage_number} ({stage_date})")
    print("=" * 50)
    
    # Load mission config
    mission_cfg = bootstrap("missions/tdf_sim_2025.toml")
    ftp = getattr(mission_cfg.athlete, 'ftp', 200)
    
    # Process activity data
    processed_data = validate_activity_data(activity_data)
    power_metrics = calculate_power_metrics(processed_data, ftp)
    processed_data.update(power_metrics)
    
    print(f"📊 POWER ANALYSIS:")
    print(f"   • FTP: {ftp}W")
    print(f"   • Average Power: {processed_data.get('average_watts', 'N/A')}W")
    print(f"   • Normalized Power: {processed_data.get('normalized_power', 'N/A')}W")
    print(f"   • Intensity Factor: {processed_data.get('intensity_factor', 0):.3f}")
    print(f"   • TSS: {processed_data.get('tss', 0):.1f}")
    print(f"   • Effort Level: {processed_data.get('effort_level', 'unknown')}")
    print(f"   • Duration: {processed_data.get('duration_minutes', 0):.1f} minutes")
    
    # Get thresholds
    tdf_config = getattr(mission_cfg, 'tdf_simulation', {})
    detection_config = tdf_config.get('detection', {})
    
    breakaway_if_threshold = detection_config.get('breakaway_intensity_threshold', 0.85)
    breakaway_tss_threshold = detection_config.get('breakaway_tss_threshold', 60)
    gc_if_threshold = detection_config.get('gc_intensity_threshold', 0.70)
    gc_tss_threshold = detection_config.get('gc_tss_threshold', 40)
    
    print(f"\n🎯 THRESHOLD ANALYSIS:")
    print(f"   • Breakaway: IF ≥ {breakaway_if_threshold} AND TSS ≥ {breakaway_tss_threshold}")
    print(f"   • GC: IF ≥ {gc_if_threshold} AND TSS ≥ {gc_tss_threshold}")
    
    # Determine correct classification
    intensity_factor = processed_data.get("intensity_factor", 0)
    tss = processed_data.get("tss", 0)
    
    if intensity_factor >= breakaway_if_threshold and tss >= breakaway_tss_threshold:
        correct_mode = "breakaway"
        reason = f"IF {intensity_factor:.3f} ≥ {breakaway_if_threshold} AND TSS {tss:.1f} ≥ {breakaway_tss_threshold}"
    elif intensity_factor >= gc_if_threshold and tss >= gc_tss_threshold:
        correct_mode = "gc"
        reason = f"IF {intensity_factor:.3f} ≥ {gc_if_threshold} AND TSS {tss:.1f} ≥ {gc_tss_threshold}"
    elif intensity_factor >= gc_if_threshold or tss >= gc_tss_threshold:
        correct_mode = "gc"
        reason = f"IF {intensity_factor:.3f} ≥ {gc_if_threshold} OR TSS {tss:.1f} ≥ {gc_tss_threshold}"
    else:
        # Check suffer score fallback
        suffer_score = processed_data.get("suffer_score", 0) or 0
        fallback_threshold = detection_config.get('fallback_suffer_threshold', 100)
        duration_minutes = processed_data.get("duration_minutes", 0)
        
        if suffer_score > fallback_threshold and duration_minutes > 60:
            correct_mode = "gc"
            reason = f"Suffer score {suffer_score} > {fallback_threshold} (fallback)"
        else:
            correct_mode = "gc"
            reason = f"Default classification (power insufficient)"
    
    print(f"\n✅ CORRECT CLASSIFICATION:")
    print(f"   • Mode: {correct_mode.upper()}")
    print(f"   • Reason: {reason}")
    
    # Calculate points
    correct_points = calculate_stage_points(stage_type, correct_mode, mission_cfg)
    print(f"   • Correct Points: {correct_points}")
    
    return correct_mode, correct_points, processed_data


def main():
    """Main diagnostic function."""
    print("🏥 TDF STAGE DIAGNOSTIC TOOL")
    print("=" * 45)
    
    # Define the problematic stages
    stages_to_check = [
        {
            'date': date(2025, 7, 5),
            'number': 1,
            'type': 'flat',
            'activity': {
                'name': 'Stage 1 GC TDF indoor simulation',
                'moving_time': 3618,  # 60.3 minutes
                'distance': 24200,    # 24.2km
                'weighted_average_watts': 85,
                'average_watts': 85,
                'total_elevation_gain': 0,
                'suffer_score': 50
            },
            'reported_mode': 'breakaway',
            'reported_points': 8
        },
        {
            'date': date(2025, 7, 6),
            'number': 2,
            'type': 'hilly',
            'activity': {
                'name': 'Stage 2 TDF 2025 indoor simulation GC',
                'moving_time': 3600,  # 60.0 minutes
                'distance': 24500,    # 24.5km
                'weighted_average_watts': 87,
                'average_watts': 87,
                'total_elevation_gain': 100,
                'suffer_score': 55
            },
            'reported_mode': 'breakaway',
            'reported_points': 11
        }
    ]
    
    print(f"Checking {len(stages_to_check)} stages for classification errors...\n")
    
    corrections_needed = []
    
    for stage in stages_to_check:
        correct_mode, correct_points, activity_data = diagnose_stage(
            stage['date'], stage['number'], stage['type'], stage['activity']
        )
        
        print(f"\n📋 COMPARISON:")
        print(f"   • Reported: {stage['reported_mode'].upper()} ({stage['reported_points']} pts)")
        print(f"   • Correct:  {correct_mode.upper()} ({correct_points} pts)")
        
        if stage['reported_mode'] != correct_mode:
            print(f"   ❌ MISCLASSIFICATION DETECTED!")
            corrections_needed.append({
                'stage_number': stage['number'],
                'stage_date': stage['date'],
                'stage_type': stage['type'],
                'reported_mode': stage['reported_mode'],
                'reported_points': stage['reported_points'],
                'correct_mode': correct_mode,
                'correct_points': correct_points,
                'activity_data': activity_data
            })
        else:
            print(f"   ✅ Classification correct")
    
    print(f"\n🏥 DIAGNOSTIC SUMMARY:")
    print("=" * 45)
    print(f"Stages checked: {len(stages_to_check)}")
    print(f"Misclassifications: {len(corrections_needed)}")
    
    if corrections_needed:
        print(f"\n🔧 CORRECTIONS NEEDED:")
        total_point_difference = 0
        for correction in corrections_needed:
            point_diff = correction['correct_points'] - correction['reported_points']
            total_point_difference += point_diff
            print(f"   • Stage {correction['stage_number']}: {correction['reported_mode']} → {correction['correct_mode']} ({point_diff:+d} pts)")
        
        print(f"\n📊 TOTAL POINT ADJUSTMENT: {total_point_difference:+d} points")
        
        # Offer to fix the database
        print(f"\n💾 Would you like to correct the TDF tracker database?")
        print(f"This will update the points and classifications to the correct values.")
        
        # For now, just show what would be corrected
        print(f"\n🛠️ CORRECTION PLAN:")
        tracker = TDFTracker()
        current_total = tracker.get_total_points()
        new_total = current_total + total_point_difference
        print(f"   • Current total: {current_total} points")
        print(f"   • Corrected total: {new_total} points")
        
    else:
        print("   ✅ All stages correctly classified!")


if __name__ == "__main__":
    main()
