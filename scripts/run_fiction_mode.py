#!/usr/bin/env python3
"""
Fiction Mode Runner

Run the Fiction Mode pipeline to generate cycling narratives from Strava rides.
"""

import sys
import os
import argparse
from pathlib import Path
from typing import Optional

# Add project paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from lanterne_rouge.fiction_mode.pipeline import FictionModeOrchestrator, FictionModeConfig
from lanterne_rouge.fiction_mode.delivery import DeliveryOptions


def run_fiction_mode(activity_id: Optional[int] = None,
                    stage_number: Optional[int] = None,
                    style: str = 'krabbe',
                    format: str = 'markdown',
                    user_feedback: Optional[str] = None,
                    preview_only: bool = False):
    """Run Fiction Mode pipeline"""
    
    # Configure Fiction Mode
    config = FictionModeConfig(
        narrative_style=style,
        delivery_format=format,
        include_metadata=True,
        save_to_archive=True,
        auto_detect_stage=True
    )
    
    # Initialize orchestrator
    orchestrator = FictionModeOrchestrator(config)
    
    if preview_only:
        print("🔍 Running analysis preview...")
        analysis = orchestrator.preview_analysis(activity_id)
        
        if not analysis:
            print("❌ Could not analyze ride")
            return
        
        print(f"\n📊 ANALYSIS PREVIEW")
        print(f"Stage: {analysis.stage_data.stage_name}")
        print(f"Winner: {analysis.stage_data.winner}")
        print(f"Your Role: {analysis.rider_role.role_type}")
        print(f"Tactical Description: {analysis.rider_role.tactical_description}")
        print(f"Effort Level: {analysis.rider_role.effort_level}")
        print(f"Key Challenge: {analysis.performance_summary.get('key_challenge', 'N/A')}")
        print(f"Mapped Events: {len(analysis.mapped_events)}")
        
        print(f"\n📋 TIMELINE:")
        for event in analysis.narrative_timeline[:5]:  # Show first 5 events
            print(f"  {event['minute']}min: {event['description']}")
            print(f"    → {event['user_action']}")
        
        return
    
    # Run full pipeline
    if activity_id and stage_number:
        result = orchestrator.process_specific_activity(activity_id, stage_number, user_feedback)
    else:
        result = orchestrator.process_todays_ride(user_feedback)
    
    if result.success:
        print(f"\n🎉 SUCCESS! Narrative generated in {result.processing_time_seconds:.1f}s")
        
        if result.delivered_narrative and result.delivered_narrative.file_path:
            print(f"📄 Saved to: {result.delivered_narrative.file_path}")
        
        # Show quality scores
        if result.editing_report:
            print(f"\n📊 QUALITY SCORES:")
            print(f"  Style Consistency: {result.editing_report.style_consistency_score:.2f}")
            print(f"  Factual Accuracy: {result.editing_report.factual_accuracy_score:.2f}")
            print(f"  Readability: {result.editing_report.readability_score:.2f}")
        
        # Show preview of narrative
        if result.narrative:
            print(f"\n📖 NARRATIVE PREVIEW:")
            words = result.narrative.split()
            preview = ' '.join(words[:50]) + '...' if len(words) > 50 else result.narrative
            print(preview)
    
    else:
        print(f"\n❌ FAILED: {result.error_message}")
        return 1
    
    return 0


def main():
    parser = argparse.ArgumentParser(description="Generate Fiction Mode cycling narratives")
    
    parser.add_argument('--activity-id', type=int, 
                       help='Specific Strava activity ID to process')
    parser.add_argument('--stage', type=int,
                       help='TDF stage number (required with --activity-id)')
    parser.add_argument('--style', default='krabbe', 
                       choices=['krabbe', 'journalistic', 'dramatic'],
                       help='Narrative style (default: krabbe)')
    parser.add_argument('--format', default='markdown',
                       choices=['markdown', 'html', 'email', 'json'],
                       help='Output format (default: markdown)')
    parser.add_argument('--feedback', type=str,
                       help='User feedback for narrative editing')
    parser.add_argument('--preview', action='store_true',
                       help='Preview analysis without generating narrative')
    parser.add_argument('--list-styles', action='store_true',
                       help='List available narrative styles')
    
    args = parser.parse_args()
    
    if args.list_styles:
        config = FictionModeConfig()
        orchestrator = FictionModeOrchestrator(config)
        styles = orchestrator.get_available_styles()
        print("Available narrative styles:")
        for style in styles:
            description = orchestrator.writer_agent.get_style_description(style)
            print(f"  {style}: {description}")
        return 0
    
    if args.activity_id and not args.stage:
        print("❌ --stage is required when using --activity-id")
        return 1
    
    return run_fiction_mode(
        activity_id=args.activity_id,
        stage_number=args.stage,
        style=args.style,
        format=args.format,
        user_feedback=args.feedback,
        preview_only=args.preview
    )


if __name__ == "__main__":
    sys.exit(main())
