#!/usr/bin/env python3
"""
Evening TDF Check - LLM-powered activity analysis and points calculation.

Uses the TDFTracker and mission configuration for intelligent stage completion
and bonus tracking.
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

from lanterne_rouge.strava_api import strava_get
from lanterne_rouge.mission_config import bootstrap
from lanterne_rouge.tdf_tracker import TDFTracker
from lanterne_rouge.tour_coach import TourCoach
from scripts.notify import send_email, send_sms


def get_todays_cycling_activity():
    """Get today's cycling activity from Strava."""
    print("🔍 Checking for today's cycling activity...")
    
    activities = strava_get("athlete/activities?per_page=10")
    if not activities:
        print("❌ No activities found")
        return None
    
    today = date.today()
    
    for activity in activities:
        try:
            # Parse activity date
            activity_date = datetime.fromisoformat(
                activity["start_date_local"].replace("Z", "")
            ).date()
            
            # Check if it's today and is cycling
            if (activity_date == today and 
                activity.get("sport_type") in ["Ride", "VirtualRide"]):
                
                # Check minimum duration (from mission config)
                duration_minutes = activity.get("moving_time", 0) / 60
                if duration_minutes >= 30:  # Minimum stage duration
                    return activity
                    
        except (ValueError, KeyError):
            continue
    
    print("❌ No qualifying cycling activity found for today")
    print("   (Need cycling activity >30 minutes uploaded to Strava)")
    return None


def analyze_activity_with_llm(activity, stage_info, mission_cfg):
    """Use LLM to analyze activity and determine ride mode."""
    # Prepare activity data for LLM analysis
    activity_data = {
        "duration_minutes": activity.get("moving_time", 0) / 60,
        "distance_km": activity.get("distance", 0) / 1000,
        "average_power": activity.get("average_watts"),
        "suffer_score": activity.get("suffer_score"),
        "intensity_factor": activity.get("intensity_factor"),
        "average_heartrate": activity.get("average_heartrate"),
        "max_heartrate": activity.get("max_heartrate"),
        "total_elevation_gain": activity.get("total_elevation_gain"),
        "name": activity.get("name", "Cycling"),
        "description": activity.get("description", "")
    }
    
    # Get detection thresholds from mission config
    tdf_config = getattr(mission_cfg, 'tdf_simulation', {})
    detection_config = tdf_config.get('detection', {})
    
    duration_minutes = activity_data["duration_minutes"]
    suffer_score = activity_data.get("suffer_score", 0) or 0
    
    # Simple classification based on mission config thresholds
    breakaway_intensity_threshold = detection_config.get('breakaway_intensity_threshold', 100)
    breakaway_duration_threshold = detection_config.get('breakaway_duration_threshold', 60)
    
    if (suffer_score > breakaway_intensity_threshold or 
        duration_minutes > breakaway_duration_threshold):
        ride_mode = "breakaway"
        rationale = f"Aggressive ride detected: {suffer_score} suffer score, {duration_minutes:.0f} min duration"
    else:
        ride_mode = "gc"
        rationale = f"Conservative ride detected: {suffer_score} suffer score, {duration_minutes:.0f} min duration"
    
    return ride_mode, rationale, activity_data


def calculate_stage_points(stage_type, ride_mode, mission_cfg):
    """Calculate points based on stage type and ride mode using mission config."""
    tdf_config = getattr(mission_cfg, 'tdf_simulation', {})
    points_config = tdf_config.get('points', {})
    
    stage_points_config = points_config.get(stage_type, {'gc': 5, 'breakaway': 8})
    return stage_points_config.get(ride_mode, 5)


def generate_completion_summary(stage_info, ride_mode, points_earned, total_points, bonuses, rationale):
    """Generate completion summary."""
    stage_number = stage_info.get('number', 1)
    stage_type = stage_info.get('type', 'flat')
    
    lines = [
        f"🎉 TDF Stage {stage_number} Complete!",
        "",
        f"🏔️ Stage Type: {stage_type.title()}",
        f"🚴 Mode Completed: {ride_mode.upper()}",
        f"⭐ Points Earned: +{points_earned}",
        f"📊 Total Points: {total_points}",
        ""
    ]
    
    if bonuses:
        lines.append("🏆 BONUS ACHIEVEMENTS:")
        for bonus in bonuses:
            lines.append(f"   • {bonus['type']}: +{bonus['points']} points")
        lines.append("")
    
    lines.extend([
        f" Stages Completed: {stage_number}/21",
        "",
        f"🤖 Analysis: {rationale}",
        "",
        "Tomorrow: Next stage awaits!",
        "",
        "Keep crushing it! 🚀"
    ])
    
    return "\n".join(lines)


def main():
    """Main evening check workflow."""
    print("🏆 LLM-Powered TDF Evening Check")
    print("=" * 45)
    
    try:
        # Load mission configuration
        mission_cfg = bootstrap("missions/tdf_sim_2025.toml")
        
        # Create TourCoach to check if TDF is active
        coach = TourCoach(mission_cfg)
        today = date.today()
        
        if not coach._is_tdf_active(today):
            print(f"❌ TDF simulation not active today ({today})")
            print("   TDF period: July 5-27, 2025")
            return
        
        # Get current stage information
        stage_info = coach._get_current_stage_info(today)
        if not stage_info:
            print("❌ Could not determine current stage information")
            return
            
        stage_number = stage_info['number']
        stage_type = stage_info['type']
        print(f"📅 Today: Stage {stage_number} ({stage_type.title()})")
        
        # Initialize TDF tracker
        tracker = TDFTracker()
        
        # Check if stage already completed today
        if tracker.is_stage_completed_today(today):
            print(f"✅ Stage {stage_number} already completed today")
            summary = tracker.get_summary()
            print(f"   Current total: {summary['total_points']} points")
            return
        
        # Get today's cycling activity
        activity = get_todays_cycling_activity()
        if not activity:
            print("❌ No qualifying activity found")
            print("   Complete a cycling workout (>30 min) and upload to Strava")
            return
        
        print(f"✅ Found activity: {activity.get('name', 'Cycling')}")
        print(f"   Duration: {activity.get('moving_time', 0)//60:.0f} minutes")
        
        # Analyze activity to determine ride mode
        ride_mode, rationale, activity_data = analyze_activity_with_llm(
            activity, stage_info, mission_cfg
        )
        print(f"🎯 Detected mode: {ride_mode.upper()}")
        print(f"   Rationale: {rationale}")
        
        # Calculate points
        points_earned = calculate_stage_points(stage_type, ride_mode, mission_cfg)
        print(f"⭐ Points earned: {points_earned}")
        
        # Record stage completion
        result = tracker.add_stage_completion(
            stage_date=today,
            stage_number=stage_number,
            stage_type=stage_type,
            ride_mode=ride_mode,
            points_earned=points_earned,
            activity_data=activity_data
        )
        
        if "error" in result:
            print(f"❌ Error: {result['error']}")
            return
        
        bonuses_earned = result.get('bonuses_earned', [])
        new_total = result.get('new_total', points_earned)
        
        if bonuses_earned:
            print("🏆 BONUS ACHIEVEMENTS UNLOCKED:")
            for bonus in bonuses_earned:
                print(f"   • {bonus['type']}: +{bonus['points']} points")
        
        # Generate summary
        summary = generate_completion_summary(
            stage_info, ride_mode, points_earned, new_total, bonuses_earned, rationale
        )
        
        print("\n" + "="*50)
        print(summary)
        print("="*50)
        
        # Send notifications
        try:
            email_recipient = os.getenv("TO_EMAIL")
            sms_recipient = os.getenv("TO_PHONE")
            
            if email_recipient:
                subject = f"🎉 TDF Stage {stage_number} Complete - Points Summary"
                send_email(subject, summary, email_recipient)
                print("📧 Email notification sent")
            
            if sms_recipient:
                # Shortened SMS version
                sms_summary = f"🎉 Stage {stage_number} Complete! {ride_mode.upper()}: +{points_earned} pts. Total: {new_total}"
                send_sms(sms_summary, sms_recipient, 
                        use_twilio=os.getenv("USE_TWILIO", "false").lower() == "true")
                print("📱 SMS notification sent")
                
        except Exception as e:
            print(f"⚠️ Notification error: {e}")
        
        print("\n✅ Evening check complete!")
        
    except Exception as e:
        print(f"❌ Error in evening check: {e}")
        return


if __name__ == "__main__":
    main()