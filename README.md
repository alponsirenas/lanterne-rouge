# Lanterne Rouge — Agentic AI for Every Athlete

Named after the iconic "lanterne rouge" — the rider who finishes last at the Tour de France — this project embodies resilience, consistency, and intelligent endurance. It’s not about being first; it’s about finishing your own race, every stage, every day.

Lanterne Rouge is your AI-powered training partner, designed to observe your recovery, reason about your readiness, plan your next steps, and adapt dynamically to your life and training.

## How It Works

Lanterne Rouge integrates data from your Oura Ring and Strava to understand your fitness, fatigue, and recovery. Each day, it analyzes this information to generate a personalized coaching report and update your training schedule on Intervals.icu. This ensures your plan adapts to your progress and needs.

By seamlessly integrating with your existing tools, Lanterne Rouge helps you stay consistent without adding complexity. Whether you follow structured workouts, use cycling platforms, or ride by feel, Lanterne Rouge adapts to keep you moving forward.

## Getting Started

Follow these steps to set up Lanterne Rouge:

### Setup Instructions

1. **Clone the repository:**

   ```bash
   git clone https://github.com/your-username/lanterne-rouge.git
   cd lanterne-rouge
   ```

2. **Create and activate your Python environment:**

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure your `.env` file with your API credentials:**

   ```env
   OURA_TOKEN=your_oura_personal_access_token
   STRAVA_CLIENT_ID=your_strava_client_id
   STRAVA_CLIENT_SECRET=your_strava_client_secret
   STRAVA_ACCESS_TOKEN=your_strava_access_token
   STRAVA_REFRESH_TOKEN=your_strava_refresh_token
   ```

5. **Run your agent daily:**

   ```bash
   python run_tour_coach.py
   ```

   Each day, Lanterne Rouge will:
   - Analyze your recovery and fitness data.
   - Adjust your training plan based on your progress.
   - Generate a coaching report (`output/tour_coach_update.txt`).
   - Log readiness scores for future analysis (`output/readiness_score_log.csv`).

6. **Review your coaching report:**
   - Check the daily coaching report to understand your readiness and training focus.
   - Ride, recover, and let the AI adapt your plan as you progress.

This system is designed to fit into your routine, helping you build consistency and resilience without overwhelm.


## Looking Ahead

With version **v0.2.1**, Lanterne Rouge provides a solid foundation for AI-powered coaching, combining data-driven insights with user-focused design.

In future versions expect:
- Deeper trend analysis.
- Smarter plan adaptations.
- Enhanced personalization to support your endurance journey.

You can track upcoming features and roadmap progress on the [Lanterne Rouge Project Board](https://github.com/users/alponsirenas/projects/1).

## License

Lanterne Rouge is licensed under the [Apache License 2.0](LICENSE).

You are welcome to use, modify, and share this project under the terms of the license.  
Your journey, your race, your victory.