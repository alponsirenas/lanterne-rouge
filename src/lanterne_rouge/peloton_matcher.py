# peloton-matcher.py

def match_peloton_class(workout_type):
    """
    Given a workout type, suggest a matching Peloton class.
    """
    mapping = {
        "Threshold Intervals": "60 min Power Zone Max Ride with Matt Wilpers",
        "Climb Simulation": "45 min Climb Ride with Sam Yo",
        "Tempo Ride": (
            "60 min Power Zone Endurance Ride with Denis Morton"
        ),
        "Recovery Ride": "20 min Low Impact Ride with Hannah Corbin",
        "Long Endurance Ride": (
            "90 min Power Zone Endurance Ride with Matt Wilpers"
        ),
        "Strength": "30 min Total Strength with Andy Speer",
        "Rest": "20 min Yoga Recovery Flow with Kristin McGee"
    }

    return mapping.get(workout_type, "No matching Peloton class found.")
