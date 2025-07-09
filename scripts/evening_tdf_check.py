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

    from datetime import timedelta
    today = date.today()
    yesterday = today - timedelta(days=1)
    
    print(f"📅 Checking for activities on {today} (or {yesterday} due to timezone)")

    for activity in activities:
        try:
            # Parse activity date (this is in athlete's local time)
            activity_date = datetime.fromisoformat(
                activity["start_date_local"].replace("Z", "")
            ).date()

            # Check if it's today OR yesterday (to handle timezone differences)
            # When GitHub Actions runs in UTC, "today" might be tomorrow for the athlete
            if (activity_date in [today, yesterday] and
                activity.get("sport_type") in ["Ride", "VirtualRide"]):

                # Check minimum duration (from mission config)
                duration_minutes = activity.get("moving_time", 0) / 60
                if duration_minutes >= 30:  # Minimum stage duration
                    print(f"✅ Found qualifying activity: {activity.get('name')} ({activity_date})")
                    return activity

        except (ValueError, KeyError):
            continue

    print("❌ No qualifying cycling activity found for today or yesterday")
    print("   (Need cycling activity >30 minutes uploaded to Strava)")
    return None


def analyze_activity_with_llm(activity, stage_info, mission_cfg):
    """Use LLM to analyze activity and determine ride mode with intelligent reasoning."""
    from lanterne_rouge.ai_clients import call_llm
    from lanterne_rouge.validation import validate_llm_json_response, validate_ride_mode, validate_confidence_score, validate_activity_data, calculate_power_metrics
    
    # Validate and prepare activity data
    activity_data = validate_activity_data(activity)
    
    # Ensure we preserve the original activity ID
    activity_data['id'] = activity.get('id')
    
    # Calculate power-based metrics using athlete's FTP
    ftp = getattr(mission_cfg.athlete, 'ftp', 200)  # Default to 200W if not set
    power_metrics = calculate_power_metrics(activity_data, ftp)
    
    # Merge power metrics into activity data
    activity_data.update(power_metrics)
    
    # Get detection thresholds and points info from mission config
    tdf_config = getattr(mission_cfg, 'tdf_simulation', {})
    detection_config = tdf_config.get('detection', {})
    points_config = tdf_config.get('points', {})
    
    stage_type = stage_info.get('type', 'flat')
    stage_number = stage_info.get('number', 1)
    stage_points = points_config.get(stage_type, {'gc': 5, 'breakaway': 8})
    
    # Check if LLM is available and enabled
    use_llm = (os.getenv("USE_LLM_REASONING", "true").lower() == "true" and 
               os.getenv("OPENAI_API_KEY"))
    
    if use_llm:
        try:
            # Build comprehensive system prompt for intelligent analysis
            system_prompt = f"""Classify this TDF stage effort with intelligent analysis. Be encouraging and informative.

JSON format:
{{
  "ride_mode": "gc|breakaway|rest",
  "confidence": 0.8,
  "rationale": "Informative coaching feedback addressing the rider directly with power insights",
  "performance_indicators": ["IF", "TSS", "duration"],
  "effort_assessment": "conservative|moderate|aggressive"
}}

Rules: BREAKAWAY if IF≥{detection_config.get('breakaway_intensity_threshold', 0.85)} AND TSS≥{detection_config.get('breakaway_tss_threshold', 60)}, GC if IF≥{detection_config.get('gc_intensity_threshold', 0.70)}, REST otherwise.

Rationale guidelines:
- Be encouraging and personal (use "you/your")
- Explain WHY it's classified as breakaway/GC/rest
- Include key power metrics (IF, TSS, duration) in context
- Mention performance highlights or areas for improvement
- Target 300-400 characters for informative feedback
- Examples: "Excellent breakaway effort! Your IF of 0.87 and 85 TSS show you sustained high intensity perfectly for this stage type.", "Solid GC pacing! Your steady 0.74 IF over 90 minutes shows great endurance control."
"""

            # Build user prompt with activity data
            user_prompt = f"""Analyze this Stage {stage_number} ride:

YOUR POWER DATA:
• Duration: {activity_data['duration_minutes']:.1f} minutes
• Power: {activity_data['normalized_power']}W (vs {ftp}W FTP)
• Intensity Factor: {activity_data['intensity_factor']:.3f}
• Training Load: {activity_data['tss']:.1f} TSS
• Effort Zone: {activity_data['effort_level']}

RIDE DETAILS:
• Distance: {activity_data['distance_km']:.1f}km
• Elevation: {activity_data.get('total_elevation_gain', 'N/A')}m
• Activity: "{activity_data['name']}"

What's your verdict - was this a GC effort, breakaway attempt, or recovery ride?"""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]

            # Call LLM with JSON mode
            response = call_llm(messages, model=os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview"), force_json=True)
            print("✅ LLM activity analysis completed")

            # Safely parse and validate LLM response
            try:
                required_fields = ["ride_mode", "rationale"]
                analysis = validate_llm_json_response(response, required_fields)
                
                # Validate specific fields
                ride_mode = validate_ride_mode(analysis.get("ride_mode", "gc"))
                confidence = validate_confidence_score(analysis.get("confidence", 0.7))
                rationale = analysis.get("rationale", "LLM-based analysis")
                
                # Enhance rationale with confidence and indicators
                enhanced_rationale = f"{rationale} (Confidence: {confidence:.1f})"
                
                # Allow for more informative feedback - limit to ~450 characters max
                if len(enhanced_rationale) > 450:
                    # Truncate but keep the confidence info
                    base_rationale = rationale[:400] + "..."
                    enhanced_rationale = f"{base_rationale} (Confidence: {confidence:.1f})"
                
                if analysis.get("performance_indicators"):
                    indicators = analysis["performance_indicators"][:3]  # Allow up to 3 indicators
                    if len(enhanced_rationale) < 400:  # Only add if we have space
                        enhanced_rationale += f" Key: {', '.join(indicators)}"
                
                return ride_mode, enhanced_rationale, activity_data
                
            except (json.JSONDecodeError, ValueError) as e:
                print(f"⚠️ LLM response validation failed: {e}, falling back to rule-based analysis")
                # Fall through to rule-based analysis
                
        except Exception as e:
            print(f"⚠️ LLM analysis failed: {e}, falling back to rule-based analysis")
            # Fall through to rule-based analysis
    
    # Fallback: Rule-based analysis with power-based logic
    print("🤖 Using rule-based activity analysis with power metrics")
    
    # Get power-based metrics
    intensity_factor = activity_data.get("intensity_factor", 0)
    tss = activity_data.get("tss", 0)
    effort_level = activity_data.get("effort_level", "recovery")
    duration_minutes = activity_data["duration_minutes"]
    
    # Get power-based thresholds from config
    breakaway_if_threshold = detection_config.get('breakaway_intensity_threshold', 0.85)
    breakaway_tss_threshold = detection_config.get('breakaway_tss_threshold', 60)
    gc_if_threshold = detection_config.get('gc_intensity_threshold', 0.70)
    gc_tss_threshold = detection_config.get('gc_tss_threshold', 40)
    
    # Power-based classification
    if intensity_factor >= breakaway_if_threshold and tss >= breakaway_tss_threshold:
        ride_mode = "breakaway"
        rationale = f"You nailed a breakaway effort! Your IF {intensity_factor:.2f} and TSS {tss:.0f} show you pushed hard in the {effort_level} zone."
    elif intensity_factor >= gc_if_threshold and tss >= gc_tss_threshold:
        ride_mode = "gc"
        rationale = f"Solid GC effort! Your IF {intensity_factor:.2f} and TSS {tss:.0f} show consistent {effort_level} zone riding."
    elif intensity_factor >= gc_if_threshold or tss >= gc_tss_threshold:
        ride_mode = "gc"
        rationale = f"Good steady effort! IF {intensity_factor:.2f}, TSS {tss:.0f} in {effort_level} zone - smart pacing."
    else:
        # Fallback to suffer score if power data is insufficient
        suffer_score = activity_data.get("suffer_score", 0) or 0
        fallback_threshold = detection_config.get('fallback_suffer_threshold', 100)
        
        if suffer_score > fallback_threshold and duration_minutes > 60:
            ride_mode = "gc"
            rationale = f"Decent GC effort based on your {suffer_score} effort score over {duration_minutes:.0f} minutes."
        else:
            ride_mode = "gc"  # Default to GC for completion
            rationale = f"Easy completion ride - IF {intensity_factor:.2f}, TSS {tss:.0f}. Good recovery work!"
    
    return ride_mode, rationale, activity_data


def calculate_stage_points(stage_type, ride_mode, mission_cfg):
    """Calculate points based on stage type and ride mode using mission config."""
    tdf_config = getattr(mission_cfg, 'tdf_simulation', {})
    points_config = tdf_config.get('points', {})
    
    stage_points_config = points_config.get(stage_type, {'gc': 5, 'breakaway': 8})
    return stage_points_config.get(ride_mode, 5)


def generate_llm_stage_evaluation(stage_info, ride_mode, points_earned, total_points, bonuses, rationale, activity_data, mission_cfg):
    """Generate LLM-powered post-stage performance evaluation and strategic advice."""
    from lanterne_rouge.ai_clients import call_llm
    
    # Check if LLM is available
    use_llm = (os.getenv("USE_LLM_REASONING", "true").lower() == "true" and 
               os.getenv("OPENAI_API_KEY"))
    
    if not use_llm:
        # Fallback to simple summary
        return generate_completion_summary(stage_info, ride_mode, points_earned, total_points, bonuses, rationale)
    
    try:
        # Get TDF context for strategic analysis
        tdf_config = getattr(mission_cfg, 'tdf_simulation', {})
        total_stages = tdf_config.get('total_stages', 21)
        stage_number = stage_info.get('number', 1)
        stage_type = stage_info.get('type', 'flat')
        
        # Calculate remaining stages and strategic context
        stages_remaining = total_stages - stage_number
        completion_percentage = (stage_number / total_stages) * 100
        
        # Build comprehensive system prompt
        system_prompt = """You're a cycling coach giving a post-stage TDF debrief. Keep it personal, informative, and actionable.

Write a brief evaluation (under 300 words) covering:
1. How you performed today (mention specific power metrics)
2. Your points position and strategy
3. Recovery needs for tomorrow
4. Quick motivation and what to focus on next

Use "you/your" throughout. Be encouraging but realistic. Include relevant power data insights. Be specific about what the numbers tell us."""

        # Build detailed user prompt
        user_prompt = f"""STAGE {stage_number} COMPLETE! 

Your Performance:
• Mode: {ride_mode.upper()} (+{points_earned} points)
• Total Points: {total_points}
• Power: {activity_data.get('normalized_power', 'N/A')}W, IF {activity_data.get('intensity_factor', 0):.2f}
• Training Load: {activity_data.get('tss', 0):.0f} TSS
• Duration: {activity_data.get('duration_minutes', 0):.0f} minutes

Campaign Status:
• Progress: {stage_number}/{total_stages} stages ({completion_percentage:.0f}% done)
• Stages remaining: {stages_remaining}"""

        if bonuses:
            user_prompt += f"\n• BONUSES: {len(bonuses)} unlocked this stage! 🏆"
        else:
            user_prompt += "\n• No bonuses this stage"

        user_prompt += f"""

Analysis: {rationale}

Give me your quick coach debrief - how did I do and what's next?"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        # Call LLM for evaluation
        response = call_llm(messages, model=os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview"))
        print("✅ LLM stage evaluation completed")
        
        # Format the response with header
        evaluation = f"""🎉 TDF Stage {stage_number} Complete!
{'=' * 50}

{response}

{'=' * 50}
📊 STAGE SUMMARY:
• Points Earned: +{points_earned}
• Total Points: {total_points}
• Mode: {ride_mode.upper()}
• Progress: {stage_number}/{total_stages} stages
"""
        
        if bonuses:
            evaluation += "\n🏆 BONUSES UNLOCKED:\n"
            for bonus in bonuses:
                evaluation += f"   • {bonus['type']}: +{bonus['points']} points\n"
                
        return evaluation
        
    except Exception as e:
        print(f"⚠️ LLM evaluation failed: {e}, using standard summary")
        # Fallback to standard summary
        return generate_completion_summary(stage_info, ride_mode, points_earned, total_points, bonuses, rationale)


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
    
    # Debug: Show LLM configuration
    use_llm = os.getenv("USE_LLM_REASONING", "true").lower() == "true"
    llm_model = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
    has_openai_key = bool(os.getenv("OPENAI_API_KEY"))
    
    print(f"🤖 LLM Mode: {'ENABLED' if use_llm else 'DISABLED'}")
    print(f"🧠 Model: {llm_model}")
    print(f"🔑 OpenAI API Key: {'SET' if has_openai_key else 'MISSING'}")
    print()
    
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
        print("📅 Today: TDF stage analysis")
        
        # Initialize TDF tracker
        tracker = TDFTracker()
        
        # Check if stage already completed today
        if tracker.is_stage_completed_today(today):
            print("✅ Stage already completed today")
            print("   Points tracking up to date")
            return
        
        # Get today's cycling activity
        activity = get_todays_cycling_activity()
        if not activity:
            print("❌ No qualifying activity found")
            print("   Complete a cycling workout (>30 min) and upload to Strava")
            return
        
        # Log activity detection without any sensitive details
        print("✅ Qualifying cycling activity found")
        
        # Analyze activity to determine ride mode
        ride_mode, rationale, activity_data = analyze_activity_with_llm(
            activity, stage_info, mission_cfg
        )
        # Log mode detection without any sensitive data
        print("🎯 Activity analysis complete")
        
        # Calculate points
        points_earned = calculate_stage_points(stage_type, ride_mode, mission_cfg)
        print("⭐ Points calculation complete")
        
        # Record stage completion (variables processed internally, not logged)
        try:
            result = tracker.add_stage_completion(
                stage_date=today,
                stage_number=stage_number,
                stage_type=stage_type,
                ride_mode=ride_mode,
                points_earned=points_earned,
                activity_data=activity_data
            )
        except Exception:
            result = {"error": "Processing failed"}
        
        if "error" in result:
            print("❌ Error processing stage completion")
            return
        
        bonuses_earned = result.get('bonuses_earned', [])
        new_total = result.get('new_total', points_earned)
        
        if bonuses_earned:
            print("🏆 BONUS ACHIEVEMENTS UNLOCKED:")
            print("   • Bonus achievements earned")
        
        # Log stage completion without any sensitive data
        print("\n✅ Stage completion summary generated")
        print("📊 Points processing complete")
        
        # Debug mode notification (no sensitive data processing in logs)
        if os.getenv("DEBUG_TDF", "false").lower() == "true":
            print("🐛 Debug mode enabled - detailed data available via notifications")
        
        # Send notifications
        try:
            email_recipient = os.getenv("TO_EMAIL")
            sms_recipient = os.getenv("TO_PHONE")
            
            if email_recipient:
                # Generate comprehensive LLM-powered evaluation for notifications
                try:
                    notification_summary = generate_llm_stage_evaluation(
                        stage_info, ride_mode, points_earned, new_total, bonuses_earned, 
                        rationale, activity_data, mission_cfg
                    )
                    subject = f"🎉 TDF Stage {stage_number} Complete - LLM Analysis"
                    send_email(subject, notification_summary, email_recipient)
                    print("📧 Email notification sent with LLM analysis")
                except Exception:
                    print("📧 Email notification failed")
            
            if sms_recipient:
                # Shortened SMS version
                bonus_text = f" +{len(bonuses_earned)} bonus!" if bonuses_earned else ""
                sms_summary = f"🎉 TDF Stage {stage_number} done! +{points_earned} pts (Total: {new_total}){bonus_text}"
                send_sms(sms_summary, sms_recipient, 
                        use_twilio=os.getenv("USE_TWILIO", "false").lower() == "true")
                print("📱 SMS notification sent")
                
        except Exception as e:
            print("⚠️ Notification error occurred")
        
        print("\n✅ Evening check complete!")
        
    except Exception as e:
        print("❌ Error in evening check - operation failed")
        return


if __name__ == "__main__":
    main()
