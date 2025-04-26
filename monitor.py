# monitor.py

import requests
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

# Read API tokens
OURA_TOKEN = os.getenv("OURA_TOKEN")
INTERVALS_API_KEY = os.getenv("INTERVALS_API_KEY")

# Safety checks
if not OURA_TOKEN:
    raise EnvironmentError("❌ Missing OURA_TOKEN. Check your .env file or GitHub Secrets.")
if not INTERVALS_API_KEY:
    raise EnvironmentError("❌ Missing INTERVALS_API_KEY. Check your .env file or GitHub Secrets.")

# --- Pull Readiness from Oura ---
def get_oura_readiness():
    url = "https://api.ouraring.com/v2/usercollection/daily_readiness"
    headers = {"Authorization": f"Bearer {OURA_TOKEN}"}
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    params = {"start_date": yesterday, "end_date": yesterday}
    
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            if data['data']:
                return data['data'][0]['score']
        else:
            print(f"Warning: Oura API returned status {response.status_code}")
    except Exception as e:
        print(f"Error fetching Oura readiness: {e}")
    return None

# --- Pull Weekly TSS from Intervals.icu ---
def get_weekly_tss():
    url = "https://intervals.icu/api/v1/athlete/activities"
    headers = {"Authorization": f"Basic {INTERVALS_API_KEY}"}
    seven_days_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    today = datetime.now().strftime("%Y-%m-%d")
    params = {"after": seven_days_ago, "before": today}

    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            activities = response.json()
            tss_sum = sum(activity.get("icu_training_load", 0) for activity in activities)
            return tss_sum
        else:
            print(f"Warning: Intervals.icu API returned status {response.status_code}")
    except Exception as e:
        print(f"Error fetching Intervals.icu activities: {e}")
    return None

# --- Temporary Mock HRV Data ---
def get_mock_hrv_data():
    """
    Simulated HRV data for now.
    Replace with real Oura HRV pull later if needed.
    """
    today_hrv = 75  # Example today's HRV
    rolling_hrv = 90  # Example 7-day average HRV
    return today_hrv, rolling_hrv