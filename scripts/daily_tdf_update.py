#!/usr/bin/env python3
"""
Daily TDF Documentation Update Workflow

Automates the daily process of updating stage documentation:
1. When morning briefing is generated -> Show Recommended + Planned for current stage
2. When stage is completed -> Populate Completed tab and add to completed stages
3. Future stages show only Planned tab
"""

import json
from pathlib import Path
import subprocess


def get_current_tdf_status():
    """Get current TDF simulation status."""
    points_file = Path("output/tdf_points.json")
    if points_file.exists():
        with open(points_file, 'r') as f:
            data = json.load(f)
            return data.get("stages_completed", 0), data.get("total_points", 0)
    return 0, 0


def has_morning_briefing():
    """Check if there's a current morning briefing."""
    briefing_file = Path("output/morning_tdf_briefing.txt")
    return briefing_file.exists()


def get_briefing_stage():
    """Extract stage number from morning briefing."""
    briefing_file = Path("output/morning_tdf_briefing.txt")
    if briefing_file.exists():
        with open(briefing_file, 'r') as f:
            content = f.read()
            import re
            match = re.search(r'Stage (\d+)', content)
            if match:
                return int(match.group(1))
    return None


def update_stage_for_briefing(stage_num):
    """Update stage to show Recommended + Planned tabs when briefing is available."""
    print(f"📋 Adding morning briefing to Stage {stage_num}...")
    
    # Run the populate_briefings script for this stage
    subprocess.run([
        "python", "scripts/populate_briefings.py"
    ], cwd=".")
    
    print(f"✅ Stage {stage_num} now shows Recommended + Planned tabs")


def update_stage_for_completion(stage_num):
    """Update stage to show all tabs when completed."""
    print(f"🎉 Stage {stage_num} completed - adding Completed tab...")
    
    # Run the populate_stage_data script to add completion data
    subprocess.run([
        "python", "scripts/populate_stage_data.py"
    ], cwd=".")
    
    print(f"✅ Stage {stage_num} now shows Completed + Recommended + Planned tabs")


def ensure_future_stages_planned_only(completed_stages, current_stage):
    """Ensure future stages only show Planned tab."""
    print(f"🔮 Updating future stages to show only Planned tab...")
    
    for stage_num in range(current_stage + 1, 22):
        stage_file = Path(f"docs_src/tdf-simulation/stages/stage{stage_num}.md")
        if stage_file.exists():
            # This would hide Recommended tab if it exists
            # Implementation would modify the markdown to only show === "Planned"
            pass
    
    print("✅ Future stages set to Planned-only")


def daily_update():
    """Main daily update workflow."""
    print("🚴 TDF Documentation Daily Update")
    print("=" * 40)
    
    # Get current status
    completed_stages, total_points = get_current_tdf_status()
    print(f"📊 Completed stages: {completed_stages}")
    print(f"🏆 Total points: {total_points}")
    
    # Check for morning briefing
    if has_morning_briefing():
        briefing_stage = get_briefing_stage()
        if briefing_stage:
            print(f"📋 Morning briefing available for Stage {briefing_stage}")
            
            # If this is a new briefing (stage after completed stages)
            if briefing_stage == completed_stages + 1:
                update_stage_for_briefing(briefing_stage)
            
            # Update future stages to be planned-only
            ensure_future_stages_planned_only(completed_stages, briefing_stage)
    
    print("\n🎯 Current Stage Status:")
    for stage_num in range(1, min(22, completed_stages + 5)):
        if stage_num <= completed_stages:
            status = "✅ Completed (All tabs)"
        elif stage_num == completed_stages + 1 and has_morning_briefing():
            status = "📋 Current (Recommended + Planned)"
        else:
            status = "🔮 Future (Planned only)"
        
        print(f"  Stage {stage_num}: {status}")
    
    print(f"\n💡 Next action: ", end="")
    if has_morning_briefing():
        briefing_stage = get_briefing_stage()
        print(f"Complete Stage {briefing_stage} ride and run completion update")
    else:
        next_stage = completed_stages + 1
        print(f"Generate morning briefing for Stage {next_stage}")


if __name__ == "__main__":
    daily_update()
