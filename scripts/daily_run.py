"""Script to run the daily training plan generation and notification process."""
import csv
import os
import subprocess
import sys

from dotenv import load_dotenv

# Add the project root directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

load_dotenv()

# Import after dotenv and path setup
from lanterne_rouge.strava_api import refresh_strava_token
from scripts.notify import send_email, send_sms
from scripts.run_tour_coach import run_daily_logic


def extract_explanation(content):
    """Extract explanation from the summary."""
    explanation_start = content.find("LLM-Generated Summaries:")
    if explanation_start != -1:
        return content[explanation_start:]
    return ""


if __name__ == "__main__":
    summary, log = run_daily_logic()  # summary: str, log: dict

    # Refresh token and make it available to the updater
    _, refresh_token = refresh_strava_token()
    os.environ["STRAVA_REFRESH_TOKEN"] = refresh_token

    # Update GitHub secret with new token
    subprocess.run(["python", "scripts/update_github_secret.py"], check=True)

    # Constants for notification
    SUBJECT = "Lanterne Rouge: Daily Training Plan"
    email_recipient = os.getenv("TO_EMAIL")
    sms_recipient = os.getenv("TO_PHONE")

    send_email(SUBJECT, summary, email_recipient)
    send_sms(summary, sms_recipient, use_twilio=os.getenv("USE_TWILIO", "false").lower() == "true")
    print(summary)

    # Save explanation to reasoning log
    explanation = extract_explanation(summary)
    REASONING_LOG_PATH = "output/reasoning_log.csv"
    headers = [
        "day", "readiness_score", "activity_balance", "body_temperature", "hrv_balance",
        "previous_day_activity", "previous_night", "recovery_index", "resting_heart_rate",
        "sleep_balance", "explanation"
    ]
    if not os.path.exists(REASONING_LOG_PATH):
        with open(REASONING_LOG_PATH, mode='w', newline='', encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=headers)
            writer.writeheader()
    with open(REASONING_LOG_PATH, mode='a', newline='', encoding="utf-8") as file:
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
            "explanation": explanation
        }
        writer.writerow(row)
