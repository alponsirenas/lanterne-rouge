#!/usr/bin/env python3
"""
Integrated TDF Documentation Updater

This script integrates with the existing daily workflow to automatically update 
stage documentation based on TDF simulation progress. It should be called 
after the main daily_run.py to update documentation tabs.
"""

import sys
import os
import json
import datetime
import os
from pathlib import Path
import json
import subprocess

# Add project paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))


def get_tdf_status():
    """Get current TDF status from existing tracker."""
    try:
        from lanterne_rouge.tdf_tracker import TDFTracker
        tracker = TDFTracker()
        points_status = tracker.get_points_status()
        
        return {
            "completed_stages": points_status.get("stages_completed", 0),
            "total_points": points_status.get("total_points", 0),
            "current_stage": points_status.get("stages_completed", 0) + 1
        }
    except Exception as e:
        print(f"⚠️  Error getting TDF status: {e}")
        return {"completed_stages": 0, "total_points": 0, "current_stage": 1}


def has_new_briefing():
    """Check if there's a new morning briefing (indicates current stage)."""
    briefing_file = Path("output/morning_tdf_briefing.txt")
    return briefing_file.exists()


def get_briefing_stage():
    """Extract stage number from current briefing."""
    briefing_file = Path("output/morning_tdf_briefing.txt")
    if briefing_file.exists():
        try:
            with open(briefing_file, 'r') as f:
                content = f.read()
                import re
                match = re.search(r'Stage (\d+)', content)
                if match:
                    return int(match.group(1))
        except Exception as e:
            print(f"⚠️  Error reading briefing: {e}")
    return None


def update_stage_tabs(stage_num, status):
    """Update stage documentation tabs based on status."""
    stage_file = Path(f"docs_src/tdf-simulation/stages/stage{stage_num}.md")
    
    if not stage_file.exists():
        return
    
    print(f"📄 Updating Stage {stage_num} tabs for status: {status}")
    
    with open(stage_file, 'r') as f:
        content = f.read()
    
    lines = content.split('\n')
    
    # Find Stage Report section
    report_idx = None
    for i, line in enumerate(lines):
        if '## Stage Report' in line:
            report_idx = i
            break
    
    if report_idx is None:
        return
    
    # Keep content before Stage Report
    new_lines = lines[:report_idx + 1]
    new_lines.append('')
    
    # Add appropriate tabs based on status
    if status == 'completed':
        # Show all tabs: Completed (with fresh data), Recommended, Planned
        new_lines.extend(get_completed_tab_with_data(content, stage_num))
        new_lines.extend(get_existing_tab_content(content, 'Recommended'))
        new_lines.extend(get_existing_tab_content(content, 'Planned'))
    elif status == 'current':
        # Show Recommended, Planned (no Completed until stage is done)
        new_lines.extend(get_existing_tab_content(content, 'Recommended'))
        new_lines.extend(get_existing_tab_content(content, 'Planned'))
    else:  # future
        # Show only Planned
        new_lines.extend(get_existing_tab_content(content, 'Planned'))
    
    # Write updated content
    with open(stage_file, 'w') as f:
        f.write('\n'.join(new_lines))


def get_existing_tab_content(content, tab_name):
    """Extract existing tab content from stage file."""
    lines = content.split('\n')
    tab_lines = []
    in_tab = False
    
    for line in lines:
        if f'=== "{tab_name}"' in line:
            in_tab = True
            tab_lines.append(line)
            continue
        elif in_tab and line.startswith('=== '):
            break
        elif in_tab:
            tab_lines.append(line)
    
    return tab_lines


def get_completed_tab_with_data(content, stage_num):
    """Generate Completed tab with fresh performance data."""
    tab_lines = []
    tab_lines.append('=== "Completed"')
    tab_lines.append('')
    
    # Try to get fresh data from TDF points
    try:
        tdf_points_path = os.path.join(os.path.dirname(__file__), '..', 'output', 'tdf_points.json')
        if os.path.exists(tdf_points_path):
            with open(tdf_points_path) as f:
                tdf_data = json.load(f)
            
            stage_key = f"stage{stage_num}"
            if stage_key in tdf_data:
                stage_data = tdf_data[stage_key]
                
                # Performance Summary
                tab_lines.append('    ### Performance Summary')
                tab_lines.append('')
                tab_lines.append(f'    **Stage Result:** {stage_data.get("stage_completion", "Completed")}')
                
                if 'points_earned' in stage_data:
                    tab_lines.append(f'    **Points Earned:** {stage_data["points_earned"]}')
                    
                if 'gc_position' in stage_data:
                    tab_lines.append(f'    **GC Position:** {stage_data["gc_position"]}')
                    
                if 'time_behind' in stage_data:
                    tab_lines.append(f'    **Time Behind Leader:** {stage_data["time_behind"]}')
                
                tab_lines.append('')
                
                # Activity Details
                if 'activity_summary' in stage_data:
                    tab_lines.append('    ### Activity Details')
                    tab_lines.append('')
                    summary = stage_data['activity_summary']
                    
                    if 'distance' in summary:
                        tab_lines.append(f'    **Distance:** {summary["distance"]}km')
                    if 'moving_time' in summary:
                        tab_lines.append(f'    **Moving Time:** {summary["moving_time"]}')
                    if 'elevation_gain' in summary:
                        tab_lines.append(f'    **Elevation Gain:** {summary["elevation_gain"]}m')
                    if 'average_power' in summary:
                        tab_lines.append(f'    **Average Power:** {summary["average_power"]}W')
                    
                    tab_lines.append('')
                
                # LLM Analysis (if available from recent evening check)
                evening_analysis = get_latest_evening_analysis(stage_num)
                if evening_analysis:
                    tab_lines.append('    ### Coach Analysis')
                    tab_lines.append('')
                    tab_lines.append(f'    {evening_analysis}')
                    tab_lines.append('')
                
    except Exception as e:
        print(f"Warning: Could not load fresh stage data: {e}")
        # Fall back to existing content
        return get_existing_tab_content(content, 'Completed')
    
    # If no fresh data, use existing content
    if len(tab_lines) <= 2:
        return get_existing_tab_content(content, 'Completed')
    
    return tab_lines


def get_latest_evening_analysis(stage_num):
    """Get the latest LLM analysis from evening check for this stage."""
    try:
        # Look for recent analysis in output directory
        output_dir = os.path.join(os.path.dirname(__file__), '..', 'output')
        analysis_file = os.path.join(output_dir, f'stage{stage_num}_analysis.txt')
        
        if os.path.exists(analysis_file):
            with open(analysis_file) as f:
                return f.read().strip()
    except Exception:
        pass
    
    return None


def update_all_stages():
    """Update all stage files based on current TDF status."""
    tdf_status = get_tdf_status()
    briefing_stage = get_briefing_stage() if has_new_briefing() else None
    
    completed_stages = tdf_status["completed_stages"]
    
    print(f"🏆 TDF Status: {completed_stages} stages completed")
    if briefing_stage:
        print(f"📋 Current briefing for Stage {briefing_stage}")
    
    # Update stages 1-21 based on status
    for stage_num in range(1, 22):
        if stage_num <= completed_stages:
            status = 'completed'
        elif stage_num == briefing_stage:
            status = 'current'
        elif stage_num == completed_stages + 1 and not briefing_stage:
            status = 'future'  # Next stage without briefing
        else:
            status = 'future'
        
        update_stage_tabs(stage_num, status)
    
    print("✅ Stage documentation updated")


def update_stage_data_if_completed():
    """Run stage data population if new stages were completed."""
    try:
        # Check if there are new completions by running the populate script
        result = subprocess.run(
            ["python", "scripts/populate_stage_data.py"],
            capture_output=True,
            text=True,
            cwd=project_root
        )
        
        if result.returncode == 0 and "Updated Stage" in result.stdout:
            print("📊 Stage completion data updated")
            return True
    except Exception as e:
        print(f"⚠️  Error updating stage data: {e}")
    
    return False


def main():
    """Main integration function - should be called after daily_run.py."""
    print("🚴 TDF Documentation Update Integration")
    print("=" * 45)
    
    # Check if we're in TDF period
    from datetime import date
    from lanterne_rouge.mission_config import bootstrap
    
    try:
        mission_cfg = bootstrap("missions/tdf_sim_2025.toml")
        start_date = mission_cfg.start_date
        goal_date = mission_cfg.goal_date
        today = date.today()
        
        # For TDF simulation, we're active between start_date and goal_date
        if start_date <= today <= goal_date:
            print("✅ TDF simulation active - updating documentation")
            
            # Update stage completion data if needed
            stage_data_updated = update_stage_data_if_completed()
            
            # Update all stage tabs based on current status
            update_all_stages()
            
            # If morning briefing exists, ensure it's reflected in documentation
            if has_new_briefing():
                briefing_stage = get_briefing_stage()
                if briefing_stage:
                    print(f"📋 Morning briefing active for Stage {briefing_stage}")
            
            print("🎯 Documentation update complete!")
            
        else:
            print("⏸️  TDF simulation not active - skipping documentation update")
            
    except Exception as e:
        print(f"❌ Error in TDF documentation update: {e}")


if __name__ == "__main__":
    main()
