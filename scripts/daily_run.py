import sys
import os
from dotenv import load_dotenv

# Add the project root directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.run_tour_coach import run_daily_logic
from scripts.notify import send_email, send_sms
from lanterne_rouge.strava_api import refresh_strava_token
import subprocess

load_dotenv()

if __name__ == "__main__":
    summary, log = run_daily_logic()  # summary: str, log: dict

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

    # Ensure output/reasoning_log.csv includes an explanation field for the generated summaries
    reasoning_log_path = "output/reasoning_log.csv"
    if not os.path.exists(reasoning_log_path):
        with open(reasoning_log_path, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([
                "day", "readiness_score", "activity_balance", "body_temperature",
                "hrv_balance", "previous_day_activity", "previous_night",
                "recovery_index", "resting_heart_rate", "sleep_balance", "explanation"
            ])

    with open(reasoning_log_path, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([
            log["readiness"]["day"], log["readiness"]["score"], log["readiness"].get("activity_balance", ""),
            log["readiness"].get("body_temperature", ""), log["readiness"].get("hrv_balance", ""),
            log["readiness"].get("previous_day_activity", ""), log["readiness"].get("previous_night", ""),
            log["readiness"].get("recovery_index", ""), log["readiness"].get("resting_heart_rate", ""),
            log["readiness"].get("sleep_balance", ""), "\n".join(log["recommendations"])
        ])
