#!/usr/bin/env python3
"""
Script to populate stage documentation with actual data from TDF simulation logs.
"""

import json
import re
from pathlib import Path
from datetime import datetime


def load_tdf_points():
    """Load the TDF points data from the output file."""
    points_file = Path("output/tdf_points.json")
    if not points_file.exists():
        print(f"Error: {points_file} not found")
        return None
    
    with open(points_file, 'r') as f:
        return json.load(f)


def format_duration(minutes):
    """Convert minutes to human-readable format."""
    if minutes is None:
        return "N/A"
    
    hours = int(minutes // 60)
    mins = int(minutes % 60)
    if hours > 0:
        return f"{hours}h {mins}m"
    else:
        return f"{mins}m"


def format_date(date_str):
    """Format date string to readable format."""
    try:
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return dt.strftime("%B %d, %Y")
    except:
        return date_str


def update_stage_file(stage_num, stage_data, total_points_at_stage):
    """Update a stage markdown file with actual data."""
    stage_file = Path(f"docs_src/tdf-simulation/stages/stage{stage_num}.md")
    
    if not stage_file.exists():
        print(f"Warning: {stage_file} not found")
        return
    
    # Read the current file
    with open(stage_file, 'r') as f:
        content = f.read()
    
    # Extract activity data
    activity_data = stage_data.get('activity_data', {})
    
    # Determine if we have real activity data or test data
    has_real_data = 'moving_time' in activity_data or 'duration_minutes' in activity_data
    
    # Map stage types to emojis
    stage_type_emojis = {
        'flat': '🏁',
        'hilly': '⛰️',
        'mountain': '🏔️',
        'itt': '⏱️'
    }
    
    stage_emoji = stage_type_emojis.get(stage_data['stage_type'], '🏁')
    
    if has_real_data:
        # Real activity data available
        duration = format_duration(activity_data.get('duration_minutes', activity_data.get('moving_time', 0) / 60))
        distance = f"{activity_data.get('distance_km', activity_data.get('distance', 0) / 1000):.1f} km"
        avg_power = f"{activity_data.get('average_watts', 'N/A')} W"
        weighted_power = f"{activity_data.get('normalized_power', activity_data.get('weighted_average_watts', 'N/A'))} W"
        avg_hr = f"{activity_data.get('average_heartrate', 'N/A')} bpm"
        tss = f"{activity_data.get('tss', 'N/A')}"
        effort_level = activity_data.get('effort_level', 'N/A').title()
        activity_id = stage_data.get('activity_id', 'N/A')
        
        analysis = f"Stage {stage_num} completed in {stage_data['ride_mode'].upper()} mode earning {stage_data['points_earned']} points. "
        
        # Add stage-specific analysis based on type
        stage_type = stage_data['stage_type']
        if stage_type == 'flat':
            analysis += "Flat stage completed successfully with controlled effort in the peloton."
        elif stage_type == 'hilly':
            analysis += "Hilly stage navigated well with appropriate pacing on the climbs."
        elif stage_type == 'mountain':
            analysis += "Mountain stage conquered with strong climbing performance."
        elif stage_type == 'itt':
            analysis += "Individual time trial completed with sustained high-intensity effort."
        
    else:
        # Test data only
        duration = "N/A (test data)"
        distance = "N/A (test data)"
        avg_power = "N/A (test data)"
        weighted_power = "N/A (test data)"
        avg_hr = "N/A (test data)"
        tss = "N/A (test data)"
        effort_level = "N/A (test data)"
        activity_id = "Test Data"
        
        analysis = f"Stage {stage_num} completed in {stage_data['ride_mode'].upper()} mode with {stage_data['points_earned']} points earned. Test data was used for this stage - full activity metrics available from Stage 4 onwards."
    
    # Format the completion date
    completed_date = format_date(stage_data['completed_at'])
    
    # Create the replacement text for the "Completed" tab
    replacement_completed = f'''	{stage_emoji} **Stage Type:** {stage_data['stage_type'].title()}  
	🚴 **Mode Completed:** {stage_data['ride_mode'].upper()}  
	⭐ **Points Earned:** {stage_data['points_earned']}  
	📊 **Total Points:** {total_points_at_stage}

	#### 📈 Performance Metrics:
	* **Duration:** {duration}
	* **Distance:** {distance}
	* **Average Power:** {avg_power}
	* **Weighted Power:** {weighted_power}
	* **Average HR:** {avg_hr}
	* **TSS:** {tss}
	* **Effort Level:** {effort_level}

	#### 🏆 Stage Analysis:
	{analysis}

	---
	**Stage completed on:** {completed_date}  
	**Activity ID:** {activity_id}'''
    
    # Find and replace the completed section - more flexible pattern
    # Look for the stage type line with emoji and replace until the next tab or end
    pattern = r'(	[🏁⛰️🏔️⏱️] \*\*Stage Type:\*\*.*?\n	\*\*Activity ID:\*\* .*?)(?=\n\n=== "Recommended"|\n\n### |$)'
    
    if re.search(pattern, content, re.DOTALL):
        content = re.sub(pattern, replacement_completed, content, flags=re.DOTALL)
        
        # Write the updated content back
        with open(stage_file, 'w') as f:
            f.write(content)
        
        print(f"✅ Updated Stage {stage_num} with actual data")
    else:
        print(f"⚠️  Could not find completed section pattern in Stage {stage_num}")
        # Debug: show what we're looking for
        print(f"   Looking for pattern starting with: {stage_emoji} **Stage Type:**")


def main():
    """Main function to populate all stage files."""
    print("🚴 Populating TDF stage files with actual data from logs...")
    
    # Load the points data
    tdf_data = load_tdf_points()
    if tdf_data is None:
        print("❌ Failed to load TDF points data")
        return
    
    # Track cumulative points
    running_total = 0
    
    # Process stages in order
    stages_by_date = sorted(tdf_data['stages'].items())
    
    for date, stage_data in stages_by_date:
        stage_num = stage_data['stage_number']
        running_total += stage_data['points_earned']
        
        print(f"Processing Stage {stage_num}...")
        update_stage_file(stage_num, stage_data, running_total)
    
    print(f"\n🎉 Completed updating {len(stages_by_date)} stage files!")
    print(f"📊 Total points in simulation: {tdf_data['total_points']}")
    print(f"🏁 Stages completed: {tdf_data['stages_completed']}/21")


if __name__ == "__main__":
    main()
