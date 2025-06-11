import sys
import os
from dotenv import load_dotenv
import argparse
import json
from pathlib import Path

# Add the project root directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.run_tour_coach import run_daily_logic
from scripts.notify import send_email, send_sms
from lanterne_rouge.strava_api import refresh_strava_token
import subprocess

load_dotenv()

# ------------------------------------------------------------------
# Runtime writable directories (ignored by git)
# ------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parents[1]  # repo root
DATA_DIR = BASE_DIR / "data"
LOG_DIR = DATA_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

def extract_explanation(summary):
    """Extract explanation from the summary."""
    explanation_start = summary.find("LLM-Generated Summaries:")
    if explanation_start != -1:
        return summary[explanation_start:]
    return ""

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Tour Coach daily logic.")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print summary and log as JSON (in addition to normal actions).",
    )
    args = parser.parse_args()

    summary, log = run_daily_logic()  # summary: str, log: dict

    # If --json flag is set, print structured output for n8n or other callers
    if args.json:
        print(json.dumps({"summary": summary, "log": log}, ensure_ascii=False))

    # Refresh token and make it available to the updater
    _, refresh_token = refresh_strava_token()
    os.environ["STRAVA_REFRESH_TOKEN"] = refresh_token

    # Update GitHub secret with new token
    subprocess.run(["python", "scripts/update_github_secret.py"], check=True)

    subject = "Lanterne Rouge: Daily Training Plan"
    email_recipient = os.getenv("TO_EMAIL")
    sms_recipient = os.getenv("TO_PHONE")

    send_email(subject, summary, email_recipient)
    send_sms(summary, sms_recipient, use_twilio=os.getenv("USE_TWILIO", "false").lower() == "true")
    print(summary)

    # Save explanation to reasoning log
    reasoning_log_path = LOG_DIR / "reasoning_log.csv"
    import csv
    headers = [
        "day", "readiness_score", "activity_balance", "body_temperature", "hrv_balance",
        "previous_day_activity", "previous_night", "recovery_index", "resting_heart_rate",
        "sleep_balance", "explanation"
    ]
    if not os.path.exists(reasoning_log_path):
        with open(reasoning_log_path, mode='w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=headers)
            writer.writeheader()
    with open(reasoning_log_path, mode='a', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        row = {
            "day": log.get('date', ''),
            "readiness_score": log.get('readiness', {}).get('score', ''),
            "activity_balance": log.get('readiness', {}).get('activity_balance', ''),
            "body_temperature": log.get('readiness', {}).get('body_temperature', ''),
            "hrv_balance": log.get('readiness', {}).get('hrv_balance', ''),
            "previous_day_activity": log.get('previous_day_activity', ''),
            "previous_night": log.get('previous_night', ''),
            "recovery_index": log.get('recovery_index', ''),
            "resting_heart_rate": log.get('resting_heart_rate', ''),
            "sleep_balance": log.get('sleep_balance', ''),
            "explanation": extract_explanation(summary)
        }
        writer.writerow(row)
