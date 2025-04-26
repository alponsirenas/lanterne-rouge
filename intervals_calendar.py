# intervals-calendar.py

import requests
import os
from dotenv import load_dotenv
import base64

# Load environment variables
load_dotenv()

# Read API key
INTERVALS_API_KEY = os.getenv("INTERVALS_API_KEY")
INTERVALS_BASE_URL = "https://intervals.icu/api/v1"

# Safety check
if not INTERVALS_API_KEY:
    raise EnvironmentError("❌ Missing INTERVALS_API_KEY. Check your .env file or GitHub Secrets.")

# Prepare API Key properly for Basic Auth
api_key_with_colon = INTERVALS_API_KEY + ":"
api_key_encoded = base64.b64encode(api_key_with_colon.encode()).decode()

headers = {
    "Authorization": f"Basic {api_key_encoded}"
}

# --- Pull existing planned workouts ---
def get_planned_workouts():
    """
    Fetch planned workouts from Intervals.icu.
    """
    try:
        url = f"{INTERVALS_BASE_URL}/athlete/workouts"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Warning: Could not fetch workouts (Status {response.status_code})")
            return []
    except Exception as e:
        print(f"Error fetching workouts: {e}")
        return []

# --- Upload a new workout ---
def upload_workout(workout):
    """
    Upload a new workout to Intervals.icu calendar.
    workout = {
        'date': 'YYYY-MM-DD',
        'name': 'Workout Title',
        'description': 'Workout Description',
        'icu_training_load': int (TSS estimate),
        'duration': int (duration in seconds)
    }
    """
    try:
        url = f"{INTERVALS_BASE_URL}/athlete/workout"
        response = requests.post(url, headers=headers, json=workout)
        if response.status_code == 200:
            print(f"✅ Uploaded workout for {workout['date']}: {workout['name']}")
        else:
            print(f"❌ Failed to upload workout for {workout['date']}: {response.text}")
    except Exception as e:
        print(f"Error uploading workout: {e}")