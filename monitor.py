# monitor.py

import os
import requests
import json
import csv
from datetime import datetime, timedelta
from dotenv import load_dotenv
from strava_api import strava_get

# Load environment variables
load_dotenv()

OURA_TOKEN = os.getenv("OURA_TOKEN")
USER_FTP = int(os.getenv("USER_FTP", 250))  # Optional for future use

def record_readiness_contributors(day_entry):
    """
    Save Oura readiness score and HRV balance to a CSV file for future analysis.
    """
    filename = "readiness_score_log.csv"
    fieldnames = ["day", "readiness_score", "hrv_balance"]

    contributors = day_entry.get('contributors', {})

    row = {
        "day": day_entry.get('day'),
        "readiness_score": day_entry.get('score'),
        "hrv_balance": contributors.get('hrv_balance')
    }

    file_exists = os.path.isfile(filename)

    with open(filename, mode='a', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)

    print(f"✅ Saved readiness and HRV balance for {row['day']}.")

def get_oura_readiness():
    """
    Pull today's Readiness Score and HRV Balance Score from Oura API.
    Return readiness_score, hrv_balance, and readiness_day.
    """
    try:
        today = datetime.now().date()
        start_date = today - timedelta(days=6)

        url = "https://api.ouraring.com/v2/usercollection/daily_readiness"
        headers = {"Authorization": f"Bearer {OURA_TOKEN}"}
        params = {
            "start_date": start_date.isoformat(),
            "end_date": today.isoformat()
        }

        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 200:
            full_response = response.json()
            print("🧠 Raw Oura API Response:", json.dumps(full_response, indent=2))  # Debugging

            data = full_response.get('data', [])

            if not data:
                print("⚠️ No readiness data returned in last 7 days.")
                return None, None, None

            # Sort by day, newest first
            data_sorted = sorted(data, key=lambda x: x['day'], reverse=True)

            for day_entry in data_sorted:
                readiness_score = day_entry.get('score')
                contributors = day_entry.get('contributors', {})
                hrv_balance = contributors.get('hrv_balance')

                if readiness_score is not None:
                    print(f"✅ Using readiness score from {day_entry['day']}")
                    record_readiness_contributors(day_entry)
                    return readiness_score, hrv_balance, day_entry.get('day')  # <-- 3 values returned!

            print("❌ No valid readiness and HRV balance data found in past 7 days.")
            return None, None, None

        else:
            try:
                error_info = response.json()
                error_message = error_info.get('message', response.text)
            except Exception:
                error_message = response.text

            print(f"❌ Oura API error {response.status_code}: {error_message}")
            return None, None, None

    except Exception as e:
        print(f"Error fetching readiness and HRV balance from Oura: {e}")
        return None, None, None

def get_ctl_atl_tsb():
    """
    Pull activities from Strava, calculate CTL (Fitness), ATL (Fatigue), and TSB (Form).
    """
    print("🔍 Pulling activities from Strava for CTL/ATL/TSB calculation...")

    activities = strava_get("athlete/activities?per_page=200")

    today = datetime.now()
    days = 45
    start_day = today - timedelta(days=days)

    daily_tss = {}

    for activity in activities:
        if not isinstance(activity, dict):
            continue

        activity_date = datetime.strptime(activity["start_date_local"], "%Y-%m-%dT%H:%M:%SZ")
        if activity_date < start_day:
            continue

        date_key = activity_date.strftime("%Y-%m-%d")
        effort_score = activity.get("relative_effort") or activity.get("suffer_score") or 0

        if date_key in daily_tss:
            daily_tss[date_key] += effort_score
        else:
            daily_tss[date_key] = effort_score

    tss_series = []
    for day_offset in range(days):
        day = (start_day + timedelta(days=day_offset)).strftime("%Y-%m-%d")
        tss_series.append(daily_tss.get(day, 0))

    ctl = 0
    atl = 0
    ctl_constant = 1 / 42
    atl_constant = 1 / 7

    for tss in tss_series:
        ctl += ctl_constant * (tss - ctl)
        atl += atl_constant * (tss - atl)

    tsb = ctl - atl

    print(f"✅ Calculated: CTL={ctl:.1f}, ATL={atl:.1f}, TSB={tsb:.1f}")
    return ctl, atl, tsb