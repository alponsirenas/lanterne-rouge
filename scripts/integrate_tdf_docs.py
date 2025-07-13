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
        # Show all tabs: Recommended, Completed (with fresh data), Planned
        new_lines.extend(get_recommended_tab_content(stage_num))
        new_lines.extend(get_completed_tab_with_data(content, stage_num))
        new_lines.extend(get_existing_tab_content(content, 'Planned'))
    elif status == 'current':
        # Show Recommended (with current briefing), Planned (no Completed until stage is done)
        new_lines.extend(get_recommended_tab_content(stage_num))
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


def get_recommended_tab_content(stage_num):
    """Generate Recommended tab with fresh morning briefing data."""
    tab_lines = []
    tab_lines.append('=== "Recommended"')
    tab_lines.append('')
    
    # Try to read morning briefing file
    briefing_file = Path("output/morning_tdf_briefing.txt")
    if briefing_file.exists():
        try:
            with open(briefing_file, 'r') as f:
                briefing_content = f.read().strip()
            
            # Check if this briefing is for the current stage
            if f"Stage {stage_num} TDF Morning Briefing" in briefing_content:
                # Get mission config to determine correct stage type
                from lanterne_rouge.mission_config import bootstrap
                try:
                    mission_cfg = bootstrap("missions/tdf_sim_2025.toml")
                    tdf_config = getattr(mission_cfg, 'tdf_simulation', {})
                    stage_types = tdf_config.get('stages', {})
                    correct_stage_type = stage_types.get(stage_num, 'flat')
                    
                    # Map stage types to display format
                    stage_type_display = {
                        'flat': 'Flat Stage',
                        'hilly': 'Hilly Stage', 
                        'mountain': 'Mountain Stage',
                        'itt': 'Individual Time Trial',
                        'mtn_itt': 'Mountain Time Trial'
                    }
                    display_type = stage_type_display.get(correct_stage_type, correct_stage_type.title())
                    
                    # Map stage types to emoji
                    stage_emoji = {
                        'flat': '🏁',
                        'hilly': '⛰️',
                        'mountain': '🏔️',
                        'itt': '🕐',
                        'mtn_itt': '🏔️'
                    }
                    emoji = stage_emoji.get(correct_stage_type, '🏁')
                    
                    # Replace incorrect stage type in briefing with correct one
                    briefing_content = briefing_content.replace(
                        "**🏔️ Stage Type**: Mountain Stage",
                        f"**{emoji} Stage Type**: {display_type}"
                    ).replace(
                        "**⛰️ Stage Type**: Hilly Punchy Stage", 
                        f"**{emoji} Stage Type**: {display_type}"
                    )
                    
                except Exception as e:
                    print(f"⚠️ Could not load mission config: {e}")
                
                # Indent the briefing content for markdown tabs
                briefing_lines = briefing_content.split('\n')
                for line in briefing_lines:
                    if line.strip():
                        tab_lines.append(f'\t{line}')
                    else:
                        tab_lines.append('')
            else:
                # No briefing for this stage, add placeholder
                tab_lines.append('\t### 🏆 Morning Briefing')
                tab_lines.append('')
                tab_lines.append('\t*Briefing not yet available for this stage.*')
                tab_lines.append('')
        except Exception as e:
            print(f"⚠️ Error reading briefing: {e}")
            tab_lines.append('\t### 🏆 Morning Briefing')
            tab_lines.append('')
            tab_lines.append('\t*Error loading briefing data.*')
            tab_lines.append('')
    else:
        # No briefing file, add placeholder
        tab_lines.append('\t### 🏆 Morning Briefing')
        tab_lines.append('')
        tab_lines.append('\t*Morning briefing not yet available.*')
        tab_lines.append('')
    
    return tab_lines


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


def update_simulation_status():
    """Update the Current Status section in the main TDF simulation index."""
    index_file = Path("docs_src/tdf-simulation/index.md")
    
    if not index_file.exists():
        print("⚠️  TDF simulation index not found")
        return False
    
    try:
        # Get latest data from tdf_points.json
        points_file = Path("output/tdf_points.json")
        if not points_file.exists():
            print("⚠️  TDF points data not found")
            return False
            
        with open(points_file, 'r') as f:
            data = json.load(f)
        
        # Calculate current values
        total_points = data.get("total_points", 0)
        stages_completed = data.get("stages_completed", 0)
        bonuses_earned = data.get("bonuses_earned", [])
        gc_count = data.get("gc_count", 0)
        breakaway_count = data.get("breakaway_count", 0)
        
        # Calculate completion percentage
        completion_percent = (stages_completed / 21) * 100
        
        # Determine strategy description
        if breakaway_count == 0:
            strategy_desc = "All GC mode so far - consistent and sustainable approach"
        elif gc_count == 0:
            strategy_desc = "All breakaway mode - high-risk, high-reward approach"
        else:
            strategy_desc = f"Mixed strategy: {gc_count} GC, {breakaway_count} breakaway rides"
        
        # Calculate bonus points and descriptions
        bonus_points = 0
        bonus_descriptions = []
        for bonus in bonuses_earned:
            if bonus == "consecutive_5":
                bonus_points += 5
                bonus_descriptions.append("5 Consecutive Stages (+5 points)")
            elif bonus == "consecutive_10":
                bonus_points += 10
                bonus_descriptions.append("10 Consecutive Stages (+10 points)")
            elif bonus == "breakaway_10_stages":
                bonus_points += 15
                bonus_descriptions.append("Breakaway Specialist (+15 points)")
            elif bonus == "all_mountains_breakaway":
                bonus_points += 10
                bonus_descriptions.append("Mountain King (+10 points)")
            elif bonus == "final_week_complete":
                bonus_points += 10
                bonus_descriptions.append("Final Week Complete (+10 points)")
            elif bonus == "all_gc_mode":
                bonus_points += 25
                bonus_descriptions.append("GC Mode Purist (+25 points)")
        
        bonus_text = ", ".join(bonus_descriptions) if bonus_descriptions else "None yet"
        
        # Get current date
        today = datetime.date.today()
        date_str = today.strftime("%B %d, %Y")
        
        # Read current index file
        with open(index_file, 'r') as f:
            content = f.read()
        
        # Find the Current Status section
        lines = content.split('\n')
        start_idx = None
        end_idx = None
        
        for i, line in enumerate(lines):
            if line.strip() == "## 🎮 Current Status":
                start_idx = i
            elif start_idx is not None and line.startswith("## ") and "Current Status" not in line:
                end_idx = i
                break
        
        if start_idx is None:
            print("⚠️  Current Status section not found in index")
            return False
        
        # If no end found, assume it goes to the next major section (look for ---)
        if end_idx is None:
            for i in range(start_idx + 1, len(lines)):
                if lines[i].strip() == "---":
                    end_idx = i
                    break
        
        if end_idx is None:
            print("⚠️  Could not determine end of Current Status section")
            return False
        
        # Create new status section
        new_status = [
            "## 🎮 Current Status",
            "",
            f"### {date_str}",
            f"- **📈 Total Points**: {total_points} points across {stages_completed} completed stages",
            f"- **🏆 Bonuses Achieved**: {bonus_text}",
            f"- **📊 Completion Rate**: {stages_completed}/21 stages ({completion_percent:.1f}% complete)",
            f"- **💪 My Strategy**: {strategy_desc}",
            ""
        ]
        
        # Replace the section
        new_lines = lines[:start_idx] + new_status + lines[end_idx:]
        new_content = '\n'.join(new_lines)
        
        # Write back to file
        with open(index_file, 'w') as f:
            f.write(new_content)
        
        print(f"✅ Updated simulation status: {total_points} points, {stages_completed} stages")
        return True
        
    except Exception as e:
        print(f"❌ Error updating simulation status: {e}")
        return False


def update_mkdocs_navigation():
    """Update mkdocs.yml navigation to include all available narrative files."""
    mkdocs_file = Path("mkdocs.yml")
    
    if not mkdocs_file.exists():
        print("⚠️  mkdocs.yml not found")
        return False
    
    try:
        # Get list of existing narrative files
        narrative_dir = Path("docs_src/tdf-simulation/tdf-2025-hallucinations")
        if not narrative_dir.exists():
            print("⚠️  Narratives directory not found")
            return False
        
        narrative_files = sorted([f for f in narrative_dir.glob("stage*.md") if f.name.startswith("stage")])
        
        # Extract stage numbers and sort them
        stages_with_narratives = []
        for file in narrative_files:
            try:
                stage_num = int(file.stem.replace("stage", ""))
                stages_with_narratives.append(stage_num)
            except ValueError:
                continue
        
        stages_with_narratives.sort()
        
        if not stages_with_narratives:
            print("⚠️  No narrative files found")
            return False
        
        # Read current mkdocs.yml
        with open(mkdocs_file, 'r') as f:
            content = f.read()
        
        lines = content.split('\n')
        
        # Find "The Indoor Rider" section
        indoor_rider_start = None
        indoor_rider_end = None
        
        for i, line in enumerate(lines):
            if "- The Indoor Rider:" in line:
                indoor_rider_start = i
            elif indoor_rider_start is not None and line.strip().startswith("- ") and ":" in line and "tdf-simulation" not in line:
                # Found the next main section
                indoor_rider_end = i
                break
        
        if indoor_rider_start is None:
            print("⚠️  'The Indoor Rider' section not found in mkdocs.yml")
            return False
        
        # If no end found, assume it goes to the next main section
        if indoor_rider_end is None:
            # Look for the next section that starts with "- " and has a ":" but isn't indented
            for i in range(indoor_rider_start + 1, len(lines)):
                line = lines[i]
                if line.startswith("  - ") and ":" in line and not line.strip().startswith("- Stage"):
                    indoor_rider_end = i
                    break
        
        if indoor_rider_end is None:
            print("⚠️  Could not determine end of 'The Indoor Rider' section")
            return False
        
        # Generate new Indoor Rider section
        new_indoor_rider_lines = [
            "      - The Indoor Rider:",
            "        - tdf-simulation/tdf-2025-hallucinations/index.md"
        ]
        
        for stage_num in stages_with_narratives:
            new_indoor_rider_lines.append(f"        - Stage {stage_num}: tdf-simulation/tdf-2025-hallucinations/stage{stage_num}.md")
        
        # Replace the section
        new_lines = lines[:indoor_rider_start] + new_indoor_rider_lines + lines[indoor_rider_end:]
        new_content = '\n'.join(new_lines)
        
        # Write back to file
        with open(mkdocs_file, 'w') as f:
            f.write(new_content)
        
        print(f"✅ Updated mkdocs navigation with {len(stages_with_narratives)} narrative stages")
        return True
        
    except Exception as e:
        print(f"❌ Error updating mkdocs navigation: {e}")
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
            
            # Update the simulation status in the index
            update_simulation_status()
            
            # Update mkdocs navigation to reflect new narratives
            update_mkdocs_navigation()
            
            print("🎯 Documentation update complete!")
            
        else:
            print("⏸️  TDF simulation not active - skipping documentation update")
            
    except Exception as e:
        print(f"❌ Error in TDF documentation update: {e}")


if __name__ == "__main__":
    main()
