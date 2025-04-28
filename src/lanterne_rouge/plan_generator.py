# plan-generator.py


from datetime import datetime, timedelta


def generate_14_day_plan(start_date=None):
    """
    Generate a 14-day training plan starting from the given start_date.
    If no start_date is provided, it starts today.
    """
    if start_date is None:
        start_date = datetime.today().date()

    plan = []
    for i in range(14):
        day = start_date + timedelta(days=i)
        workout = {}
        weekday = day.weekday()  # Monday = 0, Sunday = 6

        # Map weekdays to workout types
        if weekday == 0:  # Monday
            workout = {
                "name": "Rest",
                "description": "Strength Day (no cycling)",
                "tss": 0,
                "duration_sec": 0,
            }
        elif weekday == 1:  # Tuesday
            workout = {
                "name": "Threshold Intervals",
                "description": "3x10min @ 95–98% FTP",
                "tss": 75,
                "duration_sec": 3600,
            }
        elif weekday == 2:  # Wednesday
            workout = {
                "name": "Recovery Ride",
                "description": "45 min easy spin @ Zone 1–2",
                "tss": 25,
                "duration_sec": 2700,
            }
        elif weekday == 3:  # Thursday
            workout = {
                "name": "Rest",
                "description": "Strength Day (no cycling)",
                "tss": 0,
                "duration_sec": 0,
            }
        elif weekday == 4:  # Friday
            workout = {
                "name": "Climb Simulation",
                "description": "4x6min climbs @ 105% FTP",
                "tss": 80,
                "duration_sec": 3600,
            }
        elif weekday == 5:  # Saturday
            workout = {
                "name": "Rest",
                "description": "Optional recovery or off day",
                "tss": 0,
                "duration_sec": 0,
            }
        elif weekday == 6:  # Sunday
            workout = {
                "name": "Long Endurance Ride",
                "description": "2hr @ Zone 2–3 with surges @ Zone 4",
                "tss": 90,
                "duration_sec": 7200,
            }

        # Append with date attached
        plan.append(
            {
                "date": day.strftime("%Y-%m-%d"),
                **workout,
            }
        )

    return plan
