# This script generates a daily update for the Tour Coach program, including workout plans,
# readiness scores, and recommendations based on the user's data from Oura and Strava.

from dotenv import load_dotenv
load_dotenv()

from monitor import get_oura_readiness, get_ctl_atl_tsb
from reasoner import decide_adjustment
from plan_generator import generate_14_day_plan
from peloton_matcher import match_peloton_class
from datetime import datetime

# 1. Pull today's data
readiness_score, hrv_balance, readiness_day = get_oura_readiness ()
ctl, atl, tsb = get_ctl_atl_tsb ()

# 2. Decide if we need to adjust today's plan
recommendations = decide_adjustment(readiness_score, ctl, atl, tsb)

# 3. Get today's planned workout from plan_generator
plan = generate_14_day_plan()
today_date = datetime.now().strftime("%Y-%m-%d")
today_workout = next((w for w in plan if w["date"] == today_date), None)

if not today_workout:
    print("⚠️ No workout found for today. Exiting.")
    exit()

today_workout_type = today_workout["name"]
today_workout_details = today_workout["description"]

# 4. Match to Peloton class
peloton_class = match_peloton_class(today_workout_type)

# 5. Write the daily update
today_display_date = datetime.now().strftime("%A, %B %d, %Y")

with open("tour_coach_update.txt", "w") as f:
    f.write(f"Date: {today_display_date}\n\n")
    f.write("Planned Workout:\n")
    f.write(f"- {today_workout_type} ({today_workout_details})\n\n")

    f.write("Readiness and Recovery:\n")
    f.write(f"- Readiness Score: {readiness_score if readiness_score else 'Unavailable'}\n")
    f.write(f"- Readiness Day: {readiness_day if readiness_day else 'Unavailable'}\n")
    f.write(f"- CTL (Fitness): {ctl if ctl else 'Unavailable'}\n")
    f.write(f"- ATL (Fatigue): {atl if atl else 'Unavailable'}\n")
    f.write(f"- TSB (Form): {tsb if tsb else 'Unavailable'}\n\n")

    f.write("Recommendation:\n")
    for rec in recommendations:
        f.write(f"- {rec}\n")

    f.write("\nPeloton Class Suggestion:\n")
    f.write(f"- {peloton_class}\n\n")

    f.write("Notes:\n")
    f.write("- Adjust fueling based on today's effort. Stay hydrated and recover smart.\n")

print("✅ Tour Coach daily update generated: tour_coach_update.txt")