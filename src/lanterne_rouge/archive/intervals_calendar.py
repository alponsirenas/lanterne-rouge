# intervals-calendar.py

import base64
import os

import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


# Setup API keys and headers
INTERVALS_API_KEY = os.getenv("INTERVALS_API_KEY")
ATHLETE_ID = os.getenv("ATHLETE_ID")
INTERVALS_BASE_URL = "https://intervals.icu/api/v1"


# Safety checks
if not INTERVALS_API_KEY:
    raise EnvironmentError(
        "❌ Missing INTERVALS_API_KEY. Check your .env file or GitHub Secrets."
    )
if not ATHLETE_ID:
    raise EnvironmentError(
        "❌ Missing ATHLETE_ID. Check your .env file or GitHub Secrets."
    )


# Prepare Basic Auth header
# MUST encode "API_KEY:API_KEY"
api_key_with_colon = f"{INTERVALS_API_KEY}:{INTERVALS_API_KEY}"
api_key_encoded = base64.b64encode(api_key_with_colon.encode()).decode()


headers = {
    "Authorization": f"Basic {api_key_encoded}",
    "Content-Type": "application/json"
}


# --- Pull existing planned workouts ---


def get_planned_workouts():
    """
    Fetch planned workouts from Intervals.icu.
    """
    try:
        url = f"{INTERVALS_BASE_URL}/athlete/{ATHLETE_ID}/workouts"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            print(
                f"Warning: Could not fetch workouts (Status {response.status_code})"
            )
            return []
    except Exception as e:
        print(f"Error fetching workouts: {e}")
        return []


# --- Upload a new planned workout ---


def upload_workout(workout):
    """
    Upload a new planned workout to Intervals.icu calendar.
    """
    try:
        url = f"{INTERVALS_BASE_URL}/athlete/{ATHLETE_ID}/workouts"

        payload = {
            "date": workout["date"],  # Must be "YYYY-MM-DD"
            "plannedStress": float(workout.get("icu_training_load", 0)),
            "duration": int(workout.get("duration_sec", 0)),
            "name": workout.get("name", "Planned Workout"),
            "description": workout.get("description", "Planned session")
        }

        print("DEBUG: Upload payload:", payload)

        response = requests.post(url, headers=headers, json=payload)

        if response.status_code == 200:
            print(f"✅ Uploaded workout for {workout['date']}: {payload['name']}")
        else:
            try:
                error_info = response.json()
                error_message = error_info.get("error", "Unknown error")
            except Exception:
                error_message = response.text  # fallback if not JSON

            print(
                f"❌ Failed to upload workout for {workout['date']}: "
                f"{response.status_code} - {error_message}"
            )

    except Exception as e:
        print(f"Error uploading workout: {e}")
