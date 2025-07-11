#!/usr/bin/env python3
"""
Fiction Mode Utilities - Helper functions for narrative management
"""

import json
from pathlib import Path
from typing import Optional

def get_latest_completed_stage() -> Optional[dict]:
    """Get the most recently completed stage from TDF points data"""
    points_file = Path("output/tdf_points.json")
    
    if not points_file.exists():
        return None
    
    try:
        with open(points_file, 'r') as f:
            data = json.load(f)
        
        stages = data.get('stages', {})
        if not stages:
            return None
        
        # Get the most recent stage (highest stage number)
        latest_stage = None
        latest_stage_num = 0
        
        for stage_date, stage_data in stages.items():
            stage_num = stage_data.get('stage_number', 0)
            if stage_num > latest_stage_num:
                latest_stage_num = stage_num
                latest_stage = {
                    'stage_number': stage_num,
                    'stage_date': stage_date,
                    'activity_id': stage_data.get('activity_id'),
                    'stage_type': stage_data.get('stage_type'),
                    'ride_mode': stage_data.get('ride_mode')
                }
        
        return latest_stage
        
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Error reading TDF points data: {e}")
        return None

def narrative_already_exists(stage_number: int) -> bool:
    """Check if a narrative already exists for the given stage number"""
    narrative_file = Path(f"docs/tdf-2025-hallucinations/stage{stage_number}.md")
    return narrative_file.exists()

def list_existing_narratives() -> list:
    """List all existing narrative files"""
    fiction_dir = Path("docs/tdf-2025-hallucinations")
    if not fiction_dir.exists():
        return []
    
    narrative_files = list(fiction_dir.glob("stage*.md"))
    return sorted([f.name for f in narrative_files])

def get_narrative_status() -> dict:
    """Get status of all completed stages and their narratives"""
    latest_stage = get_latest_completed_stage()
    existing_narratives = list_existing_narratives()
    
    status = {
        'latest_completed_stage': latest_stage,
        'existing_narratives': existing_narratives,
        'narrative_needed': False
    }
    
    if latest_stage:
        stage_num = latest_stage['stage_number']
        narrative_file = f"stage{stage_num}.md"
        
        if narrative_file not in existing_narratives:
            status['narrative_needed'] = True
            status['missing_stage'] = stage_num
    
    return status

if __name__ == "__main__":
    # Print current status
    status = get_narrative_status()
    
    print("🎭 Fiction Mode Status:")
    print(f"   Latest completed stage: {status['latest_completed_stage']}")
    print(f"   Existing narratives: {status['existing_narratives']}")
    print(f"   Narrative needed: {status['narrative_needed']}")
    
    if status['narrative_needed']:
        print(f"   ➡️  Missing narrative for stage {status['missing_stage']}")
    else:
        print("   ✅ All completed stages have narratives")
