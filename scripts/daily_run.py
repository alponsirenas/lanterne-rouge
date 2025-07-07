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
    from lanterne_rouge.monitor import get_oura_readiness, get_ctl_atl_tsb

    readiness, *_ = get_oura_readiness()
    ctl, atl, tsb = get_ctl_atl_tsb()

    # Create metrics dictionary for the recommendation generator
    # Note: readiness_score is now a scalar integer, not a dictionary
    metrics = {
        "readiness_score": readiness,
        "ctl": ctl,
        "atl": atl,
        "tsb": tsb
    }

    # Run the daily logic to get the complete summary
    summary = coach.generate_daily_recommendation(metrics)

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
