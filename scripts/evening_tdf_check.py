#!/usr/bin/env python3
"""
Day 1 TDF Evening Check - Manual script to run after completing a stage.

Simple implementation that works immediately with existing codebase.
Usage: python scripts/evening_tdf_check.py
"""

import sys
import os
from pathlib import Path
from datetime import date, datetime, timedelta
import json

# Add project paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from lanterne_rouge.strava_api import strava_get
from scripts.notify import send_email, send_sms

# TDF Simulation Configuration
TDF_START_DATE = date(2025, 7, 5)  # July 5, 2025
POINTS_FILE = project_root / "output" / "tdf_points.json"

# Stage schedule (21 stages)
STAGE_TYPES = {
    1: 'flat', 2: 'hilly', 3: 'hilly', 4: 'flat', 5: 'hilly',
    6: 'mountain', 7: 'flat', 8: 'hilly', 9: 'mountain', 10: 'hilly',
    11: 'mountain', 12: 'hilly', 13: 'itt', 14: 'hilly', 15: 'mountain',
    16: 'mountain', 17: 'hilly', 18: 'mountain', 19: 'hilly', 20: 'mtn_itt', 21: 'flat'
}

# Points table
POINTS_TABLE = {
    'flat': {'gc': 5, 'breakaway': 8},
    'hilly': {'gc': 7, 'breakaway': 11}, 
    'mountain': {'gc': 10, 'breakaway': 15},
    'itt': {'gc': 4, 'breakaway': 6},
    'mtn_itt': {'gc': 6, 'breakaway': 9}
}

def get_current_stage() -> tuple[int, str] | None:
    """Get current stage number and type based on today's date."""
    today = date.today()
    days_elapsed = (today - TDF_START_DATE).days + 1
    
    if days_elapsed < 1 or days_elapsed > 21:
        return None
        
    stage_number = days_elapsed
    stage_type = STAGE_TYPES.get(stage_number)
    
    return stage_number, stage_type

def load_points_data() -> dict:
    """Load existing points data from file."""
    if POINTS_FILE.exists():
        with open(POINTS_FILE, 'r') as f:
            return json.load(f)
    return {
        "total_points": 0,
        "stages_completed": [],
        "consecutive_stages": 0,
        "breakaway_stages": 0,
        "gc_stages": 0,
        "bonuses_earned": []
    }

def save_points_data(data: dict):
    """Save points data to file."""
    POINTS_FILE.parent.mkdir(exist_ok=True)
    with open(POINTS_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def get_todays_activity() -> dict | None:
    """Get today's cycling activity from Strava."""
    print("🔍 Checking for today's activity...")
    
    activities = strava_get("athlete/activities?per_page=10")
    if not activities:
        print("❌ No activities found")
        return None
    
    today = date.today()
    
    for activity in activities:
        # Parse activity date
        try:
            activity_date = datetime.fromisoformat(
                activity["start_date_local"].replace("Z", "")
            ).date()
            
            if (activity_date == today and 
                activity.get("sport_type") in ["Ride", "VirtualRide"]):
                return activity
                
        except (ValueError, KeyError):
            continue
    
    print("❌ No cycling activity found for today")
    return None

def determine_ride_mode(activity: dict) -> str:
    """Determine ride mode based on activity intensity."""
    # Simple heuristic based on suffer score / relative effort
    intensity = activity.get("suffer_score") or activity.get("relative_effort") or 0
    duration_minutes = activity.get("moving_time", 0) / 60
    
    # Basic classification
    if intensity > 100 or duration_minutes > 60:
        return "breakaway"
    else:
        return "gc"

def calculate_points(stage_type: str, ride_mode: str) -> int:
    """Calculate points for stage completion."""
    return POINTS_TABLE[stage_type][ride_mode]

def check_bonuses(points_data: dict, stage_number: int, stage_type: str, ride_mode: str) -> list:
    """Check for bonus achievements."""
    bonuses = []
    
    # 5 consecutive stages bonus
    if (points_data["consecutive_stages"] == 4 and 
        stage_number not in points_data["stages_completed"]):
        bonuses.append(("5 Consecutive Stages", 5))
    
    # 10 breakaway stages bonus
    if (ride_mode == "breakaway" and 
        points_data["breakaway_stages"] == 9 and
        "10_breakaway" not in points_data["bonuses_earned"]):
        bonuses.append(("10 Breakaway Stages", 15))
    
    # All mountains in breakaway mode
    mountain_stages = [6, 9, 11, 15, 16, 18]
    if (stage_type == "mountain" and ride_mode == "breakaway"):
        completed_mountain_breakaways = sum(1 for s in points_data["stages_completed"] 
                                          if s in mountain_stages and 
                                          points_data.get(f"stage_{s}_mode") == "breakaway")
        if completed_mountain_breakaways == len(mountain_stages) - 1:  # This is the last one
            bonuses.append(("All Mountains in Breakaway", 10))
    
    return bonuses

def generate_summary(stage_number: int, stage_type: str, ride_mode: str, 
                    points_earned: int, total_points: int, bonuses: list) -> str:
    """Generate evening summary message."""
    
    lines = [
        f"🎉 TDF Stage {stage_number} Complete!",
        "",
        f"🏔️ Stage Type: {stage_type.title()}",
        f"🚴 Mode Completed: {ride_mode.upper()}",
        f"⭐ Points Earned: +{points_earned}",
        ""
    ]
    
    if bonuses:
        lines.append("🏆 BONUS ACHIEVEMENTS:")
        for bonus_name, bonus_points in bonuses:
            lines.append(f"   • {bonus_name}: +{bonus_points} points")
        lines.append("")
    
    lines.extend([
        f"📊 Total Points: {total_points}",
        f"📈 Stages Completed: {stage_number}/21",
        "",
        f"Tomorrow: Stage {stage_number + 1} ({STAGE_TYPES.get(stage_number + 1, 'Rest Day')})",
        "",
        "Keep crushing it! 🚀"
    ])
    
    return "\n".join(lines)

def main():
    """Main evening check workflow."""
    print("🏆 TDF Evening Points Check")
    print("=" * 40)
    
    # Check if we're in TDF period
    stage_info = get_current_stage()
    if not stage_info:
        print("❌ Not currently in TDF simulation period")
        return
    
    stage_number, stage_type = stage_info
    print(f"📅 Today: Stage {stage_number} ({stage_type})")
    
    # Load existing points data
    points_data = load_points_data()
    
    # Check if stage already completed today
    if stage_number in points_data["stages_completed"]:
        print(f"✅ Stage {stage_number} already completed today")
        print(f"Current total: {points_data['total_points']} points")
        return
    
    # Get today's activity
    activity = get_todays_activity()
    if not activity:
        print("❌ No qualifying activity found for today")
        print("Complete a cycling workout and upload to Strava, then run this script again.")
        return
    
    print(f"✅ Found activity: {activity.get('name', 'Cycling')} ({activity.get('moving_time', 0)//60:.0f} min)")
    
    # Determine ride mode
    ride_mode = determine_ride_mode(activity)
    print(f"🎯 Detected mode: {ride_mode.upper()}")
    
    # Calculate points
    points_earned = calculate_points(stage_type, ride_mode)
    
    # Check for bonuses
    bonuses = check_bonuses(points_data, stage_number, stage_type, ride_mode)
    bonus_points = sum(bonus[1] for bonus in bonuses)
    
    # Update points data
    points_data["stages_completed"].append(stage_number)
    points_data["total_points"] += points_earned + bonus_points
    points_data[f"stage_{stage_number}_mode"] = ride_mode
    
    if ride_mode == "breakaway":
        points_data["breakaway_stages"] += 1
    else:
        points_data["gc_stages"] += 1
    
    # Update consecutive stages counter
    if len(points_data["stages_completed"]) == 1 or stage_number == max(points_data["stages_completed"][:-1]) + 1:
        points_data["consecutive_stages"] += 1
    else:
        points_data["consecutive_stages"] = 1
    
    # Record bonuses
    for bonus_name, _ in bonuses:
        if bonus_name not in points_data["bonuses_earned"]:
            points_data["bonuses_earned"].append(bonus_name)
    
    # Save updated data
    save_points_data(points_data)
    
    # Generate summary
    summary = generate_summary(
        stage_number, stage_type, ride_mode,
        points_earned + bonus_points, points_data["total_points"], bonuses
    )
    
    print("\n" + summary)
    
    # Send notifications
    try:
        email_recipient = os.getenv("TO_EMAIL")
        sms_recipient = os.getenv("TO_PHONE")
        
        if email_recipient:
            send_email("🎉 TDF Stage Complete", summary, email_recipient)
            print("📧 Email notification sent")
        
        if sms_recipient:
            # Send shortened SMS version
            sms_summary = f"🎉 Stage {stage_number} Complete! {ride_mode.upper()} mode: +{points_earned + bonus_points} pts. Total: {points_data['total_points']}"
            send_sms(sms_summary, sms_recipient, 
                    use_twilio=os.getenv("USE_TWILIO", "false").lower() == "true")
            print("📱 SMS notification sent")
            
    except Exception as e:
        print(f"⚠️ Notification error: {e}")
    
    print("\n✅ Evening check complete!")

if __name__ == "__main__":
    main()