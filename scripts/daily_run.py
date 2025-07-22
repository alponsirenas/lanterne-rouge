import sys
import os
import subprocess
from dotenv import load_dotenv
from pathlib import Path
from datetime import date

# Add the project root directory to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

from scripts.notify import send_email, send_sms
from lanterne_rouge.strava_api import refresh_strava_token
from lanterne_rouge.monitor import get_oura_readiness, get_ctl_atl_tsb, get_recent_workout_analysis, get_performance_trends
from lanterne_rouge.tour_coach import TourCoach
from lanterne_rouge.mission_config import bootstrap

load_dotenv()


def run_daily_logic():
    """Execute the new agent-based Tour Coach logic for the day."""
    # Load mission configuration
    mission_cfg = bootstrap(Path("missions/tdf_sim_2025.toml"))

    # Determine reasoning mode from environment
    use_llm_reasoning = os.getenv("USE_LLM_REASONING", "true").lower() == "true"
    llm_model = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")

    # Initialize the Tour Coach orchestrator with configurable reasoning
    coach = TourCoach(mission_cfg, use_llm_reasoning=use_llm_reasoning, llm_model=llm_model)

    # Get current metrics (similar to run_tour_coach function)
    readiness, *_ = get_oura_readiness()
    ctl, atl, tsb = get_ctl_atl_tsb()
    
    # Get recent workout analysis from core monitor system
    recent_workout_analysis = get_recent_workout_analysis()
    performance_trends = get_performance_trends(recent_workout_analysis)

    # Create metrics dictionary for the recommendation generator
    # Note: readiness_score is now a scalar integer, not a dictionary
    metrics = {
        "readiness_score": readiness,
        "ctl": ctl,
        "atl": atl,
        "tsb": tsb
    }

    # Check if TDF simulation is active and use appropriate coaching logic
    current_date = date.today()
    if coach._is_tdf_active(current_date):
        # Load TDF context data
        from lanterne_rouge.tdf_tracker import TDFTracker
        tracker = TDFTracker()
        
        # Get recent workout analysis from core monitor system
        recent_workout_analysis = get_recent_workout_analysis()
        performance_trends = get_performance_trends(recent_workout_analysis)
        
        # Check for rest days
        rest_days = []
        if hasattr(mission_cfg, 'tdf_simulation') and hasattr(mission_cfg.tdf_simulation, 'rest_days'):
            rest_days = [date.fromisoformat(day) for day in mission_cfg.tdf_simulation.rest_days]
        
        is_rest_day = current_date in rest_days
        rest_day_number = rest_days.index(current_date) + 1 if is_rest_day else None
        
        # Calculate days into TDF for competition context (not training context)
        tdf_start = date.fromisoformat("2025-07-05")
        days_into_tdf = (current_date - tdf_start).days + 1
        
        tdf_data = {
            "points_status": tracker.get_points_status(),
            "stage_completed_today": tracker.is_stage_completed_today(current_date),
            "recent_workout_analysis": recent_workout_analysis,
            "performance_trends": performance_trends,
            "is_rest_day": is_rest_day,
            "rest_day_number": rest_day_number,
            "days_into_tdf": days_into_tdf,
            "competition_phase": "ACTIVE_COMPETITION"  # Not training!
        }
        print("🏆 TDF simulation active - generating TDF-specific coaching")
        summary = coach.generate_tdf_recommendation(metrics, tdf_data)
    else:
        # Use regular daily coaching when TDF is not active - include workout analysis
        print("📅 Regular training mode - generating standard coaching with workout analysis")
        
        # Enhanced metrics for regular training too
        enhanced_metrics = {
            **metrics,
            "recent_workout_analysis": recent_workout_analysis,
            "performance_trends": performance_trends
        }
        summary = coach.generate_daily_recommendation(enhanced_metrics)

    # Return summary and extract metrics for logging
    log = {
        'date': str(date.today()),
        'readiness': readiness,  # Readiness is now a scalar integer value
        'ctl': ctl,
        'atl': atl,
        'tsb': tsb,
        'reasoning_mode': 'LLM' if use_llm_reasoning else 'Rule-based'
    }

    return summary, log

if __name__ == "__main__":
    summary, log = run_daily_logic()  # summary: str, log: dict

    # Refresh token and make it available to the updater
    _, refresh_token = refresh_strava_token()
    os.environ["STRAVA_REFRESH_TOKEN"] = refresh_token

    # Update GitHub secret with new token
    subprocess.run(["python", "scripts/update_github_secret.py"], check=True, shell=False)

    # Update TDF documentation if simulation is active
    try:
        subprocess.run(["python", "scripts/integrate_tdf_docs.py"], check=True, shell=False)
    except subprocess.CalledProcessError as e:
        print(f"⚠️  TDF documentation update failed: {e}")

    subject = "Lanterne Rouge: Daily Training Plan"
    email_recipient = os.getenv("TO_EMAIL")
    sms_recipient = os.getenv("TO_PHONE")

    send_email(subject, summary, email_recipient)
    send_sms(summary, sms_recipient, use_twilio=os.getenv("USE_TWILIO", "false").lower() == "true")
    print(summary)

    # Save metrics to reasoning log
    reasoning_log_path = "output/reasoning_log.csv"
    import csv
    headers = [
        "day", "readiness_score", "activity_balance", "body_temperature", "hrv_balance",
        "previous_day_activity", "previous_night", "recovery_index", "resting_heart_rate",
        "sleep_balance", "explanation"
    ]
    if not os.path.exists(reasoning_log_path):
        with open(reasoning_log_path, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=headers)
            writer.writeheader()
    with open(reasoning_log_path, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        row = {
            "day": log.get('date', ''),
            "readiness_score": log.get('readiness', ''),  # readiness is now a scalar value
            "activity_balance": '',  # These fields no longer come from readiness dict
            "body_temperature": '',  # They're now tracked separately in readiness_score_log.csv
            "hrv_balance": '',       # which is maintained by record_readiness_contributors
            "previous_day_activity": log.get('previous_day_activity', ''),
            "previous_night": log.get('previous_night', ''),
            "recovery_index": log.get('recovery_index', ''),
            "resting_heart_rate": log.get('resting_heart_rate', ''),
            "sleep_balance": log.get('sleep_balance', ''),
            "explanation": summary  # Use full summary as explanation
        }
        writer.writerow(row)
