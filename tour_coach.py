# tour_coach.py

from monitor import get_oura_readiness, get_weekly_tss, get_mock_hrv_data
from reasoner import decide_adjustment
from datetime import datetime
from peloton_matcher import match_peloton_class

# 1. Pull today's data
readiness = get_oura_readiness()
tss_week = get_weekly_tss()
today_hrv, rolling_hrv = get_mock_hrv_data()

# 2. Decide if we need to adjust today's plan
recommendations = decide_adjustment(readiness, today_hrv, rolling_hrv, tss_week)

# 3. Define today's planned workout
# (Later we could pull from Intervals.icu Calendar, for now we hardcode for simplicity)
today_workout_type = "Threshold Intervals"
today_workout_details = "3x10min @ 95–98% FTP"

# 4. Match to Peloton class
peloton_class = match_peloton_class(today_workout_type)

# 5. Write the daily update
today_date = datetime.now().strftime("%A, %B %d, %Y")

with open("tour_coach_update.txt", "w") as f:
    f.write(f"Date: {today_date}\n\n")
    f.write("Planned Workout:\n")
    f.write(f"- {today_workout_type} ({today_workout_details})\n\n")

    f.write("Readiness and Recovery:\n")
    f.write(f"- Readiness Score: {readiness if readiness else 'Unavailable'}\n")
    f.write(f"- HRV Today: {today_hrv}\n")
    f.write(f"- 7-day Avg HRV: {rolling_hrv}\n")
    f.write(f"- Weekly TSS: {tss_week if tss_week else 'Unavailable'}\n\n")

    f.write("Recommendation:\n")
    for rec in recommendations:
        f.write(f"- {rec}\n")

    f.write("\nPeloton Class Suggestion:\n")
    f.write(f"- {peloton_class}\n\n")

    f.write("Notes:\n")
    f.write("- Adjust fueling based on today's effort. Stay hydrated and recover smart.\n")

print("✅ Tour Coach daily update generated: tour_coach_update.txt")