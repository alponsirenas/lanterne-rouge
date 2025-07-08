#!/usr/bin/env python3
"""
Fiction Mode Integration for Evening TDF Check

Integrates Fiction Mode with the existing evening TDF workflow.
"""

import sys
import os
from pathlib import Path

# Add project paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from lanterne_rouge.fiction_mode.pipeline import FictionModeOrchestrator, FictionModeConfig


def run_fiction_mode_for_evening_check():
    """Run Fiction Mode as part of evening TDF check"""
    
    print("🎬 Checking for Fiction Mode opportunity...")
    
    try:
        # Configure Fiction Mode for evening run
        config = FictionModeConfig(
            narrative_style='krabbe',
            delivery_format='markdown',
            include_metadata=True,
            save_to_archive=True,
            auto_detect_stage=True,
            require_min_duration=30
        )
        
        # Initialize orchestrator
        orchestrator = FictionModeOrchestrator(config)
        
        # Run pipeline for today's ride
        result = orchestrator.process_todays_ride()
        
        if result.success:
            print("✅ Fiction Mode narrative generated!")
            if result.delivered_narrative and result.delivered_narrative.file_path:
                print(f"📄 Saved to: {result.delivered_narrative.file_path}")
            
            # Return summary for integration with evening workflow
            return {
                'success': True,
                'narrative_title': result.delivered_narrative.title if result.delivered_narrative else 'Generated',
                'word_count': len(result.narrative.split()) if result.narrative else 0,
                'rider_role': result.analysis.rider_role.role_type if result.analysis else 'unknown',
                'stage_name': result.analysis.stage_data.stage_name if result.analysis else 'unknown',
                'file_path': result.delivered_narrative.file_path if result.delivered_narrative else None
            }
        
        else:
            print(f"ℹ️  Fiction Mode not available: {result.error_message}")
            return {
                'success': False,
                'reason': result.error_message
            }
    
    except Exception as e:
        print(f"❌ Fiction Mode error: {e}")
        return {
            'success': False,
            'reason': f"Error: {str(e)}"
        }


def check_fiction_mode_availability():
    """Quick check if Fiction Mode can run today"""
    
    try:
        config = FictionModeConfig()
        orchestrator = FictionModeOrchestrator(config)
        
        # Preview analysis to check availability
        analysis = orchestrator.preview_analysis()
        
        if analysis:
            return {
                'available': True,
                'stage_number': analysis.stage_data.stage_number,
                'stage_name': analysis.stage_data.stage_name,
                'rider_role': analysis.rider_role.role_type,
                'duration_minutes': analysis.ride_data.duration_seconds / 60
            }
        else:
            return {
                'available': False,
                'reason': 'No qualifying TDF ride found'
            }
    
    except Exception as e:
        return {
            'available': False,
            'reason': f'Error: {str(e)}'
        }


if __name__ == "__main__":
    # Check availability first
    availability = check_fiction_mode_availability()
    
    if availability['available']:
        print(f"🎯 Fiction Mode available for Stage {availability['stage_number']}")
        print(f"   Role: {availability['rider_role']}")
        print(f"   Duration: {availability['duration_minutes']:.0f} minutes")
        
        # Run Fiction Mode
        result = run_fiction_mode_for_evening_check()
        
        if result['success']:
            print(f"🎉 Generated: {result['narrative_title']}")
        else:
            print(f"❌ Failed: {result['reason']}")
    
    else:
        print(f"ℹ️  Fiction Mode not available: {availability['reason']}")
