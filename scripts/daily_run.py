"""Script to run the daily training plan generation and notification process."""
import csv
import os
import subprocess
import sys

from dotenv import load_dotenv

# Add the project root directory to Python path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, PROJECT_ROOT)
print(f"Added Python path: {PROJECT_ROOT}")

# Also add src directory explicitly to ensure module can be found
SRC_DIR = os.path.join(PROJECT_ROOT, 'src')
if os.path.exists(SRC_DIR):
    sys.path.insert(0, SRC_DIR)
    print(f"Added src directory to path: {SRC_DIR}")

print(f"Current Python path: {sys.path}")

# Load environment variables
load_dotenv()

# Verify lanterne_rouge module can be found
try:
    import importlib.util
    module_path = os.path.join(SRC_DIR, 'lanterne_rouge', '__init__.py')
    if os.path.exists(module_path):
        print(f"Found lanterne_rouge module at {module_path}")
    else:
        print(f"Warning: lanterne_rouge module not found at {module_path}")
        print(f"Contents of {os.path.dirname(module_path)}: {os.listdir(os.path.dirname(module_path)) if os.path.exists(os.path.dirname(module_path)) else 'Directory not found'}")
except Exception as e:
    print(f"Error checking module path: {e}")

# Import after dotenv and path setup
try:
    from lanterne_rouge.strava_api import refresh_strava_token
    print("Successfully imported lanterne_rouge module")
except ModuleNotFoundError as e:
    print(f"Error importing lanterne_rouge module: {e}")
    print(f"Available modules in src: {os.listdir(SRC_DIR) if os.path.exists(SRC_DIR) else 'src directory not found'}")
    raise
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
