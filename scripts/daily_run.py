import sys
import os
from dotenv import load_dotenv

# Add the project root directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.run_tour_coach import run_daily_logic
from scripts.notify import send_email, send_sms
from lanterne_rouge.strava_api import refresh_strava_token
import subprocess

# P2e0b
from lanterne_rouge.mission_config import load_config, cache_to_sqlite

load_dotenv()

if __name__ == "__main__":
    # P3f5d
    mission_config = load_config(os.getenv("MISSION_CONFIG_PATH", "missions/tdf_sim_2025.toml"))
    # Pf489
    cache_to_sqlite(mission_config)

    summary, log = run_daily_logic(mission_config)  # summary: str, log: dict

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
