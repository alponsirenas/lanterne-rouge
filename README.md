# Lanterne Rouge — Agentic AI for Every Athlete

Named after the iconic "lanterne rouge" — the rider who finishes last at the Tour de France — this project embodies resilience, consistency, and intelligent endurance. It’s not about being first; it’s about finishing your own race, every stage, every day.

Lanterne Rouge started with the idea of [using AI to train](/docs/training_strategy.md) for an AI generated indoor [simulation of the Tour de France 2025](/docs/simulation_event.md).

Designed to observe your recovery, reason about your daily readiness, and adapt dynamically to your life and training, Lanterne Rouge plans your next steps without losing sight of your long-term goals.

## How It Works

Lanterne Rouge integrates data from your Oura Ring and Strava to understand your fitness, fatigue, and recovery. Each day, it analyzes this information to generate a personalized coaching report and update your training schedule. This ensures your plan adapts to your progress and needs.

By integrating with your existing tools, Lanterne Rouge helps you stay consistent without adding complexity. Whether you follow structured workouts, use cycling platforms, or ride by feel, the application adapts to keep you moving forward.

All observations and decisions are stored in a lightweight SQLite database (`memory/lanterne.db`).
This memory lets the LLM‑powered planner reference recent history when crafting each day’s workout.

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

4. **Initialize the SQLite database:**

   ```bash
   python -c "from lanterne_rouge.mission_config import bootstrap; bootstrap('missions/tdf_sim_2025.toml')"
   ```
   This creates `memory/lanterne.db` seeded with your mission config. It will also be generated automatically the first time you run `daily_run.py`.

5. **Configure your `.env` file with your API credentials and notification settings:**

   ```env
   # Oura API
   OURA_TOKEN=your_oura_personal_access_token

   # Strava API
   STRAVA_CLIENT_ID=your_strava_client_id
   STRAVA_CLIENT_SECRET=your_strava_client_secret
   STRAVA_REFRESH_TOKEN=your_strava_refresh_token

   # OpenAI
   OPENAI_API_KEY=your_openai_api_key
   # Optional: override the default model
   # Use a model that supports JSON response format such as:
   # gpt-4-turbo-preview, gpt-4o, gpt-4-0125-preview, or gpt-3.5-turbo-1106
   OPENAI_MODEL=gpt-4-turbo-preview

   # Notification settings
   EMAIL_ADDRESS=your_email_address_for_notifications
   EMAIL_PASS=your_email_app_password
   TO_EMAIL=recipient_email_address
   TO_PHONE=recipient_phone_sms_gateway (e.g., 1234567890@txt.att.net)
   USE_TWILIO=false  # set to true to use Twilio SMS instead of email gateway

   # GitHub integration (for auto secret updates)
   GH_PAT=your_github_personal_access_token
   ```

6. **Run your agent daily:**

   - Locally:
     ```bash
     python scripts/daily_run.py
     ```
   - Automatically via GitHub Actions:
     Copy your mission config (for example `missions/tdf_sim_2025.toml`) into `missions/` and then enable the `.github/workflows/daily.yml` workflow to trigger `scripts/daily_run.py` each morning.

7. **Review your coaching report:**
   - Check the daily coaching report to understand your readiness and training focus.
   - Ride, recover, and let the AI adapt your plan as you progress.

8. **Review and update documentation:**
   - Regularly review the project documentation to ensure it remains accurate and up-to-date.
   - Follow the Documentation Review Process outlined below to make necessary updates.

This system is designed to fit into your routine, helping you build consistency and resilience without overwhelm.

## Current Version: v0.3.1

Release highlights:
- Fixed OpenAI API compatibility issues with the latest API versions
- Updated client initialization to use new OpenAI client interface
- Enhanced model compatibility checks for response formats
- Improved error handling and response parsing for API calls
- Set appropriate default models that properly support JSON generation
- Enhanced daily coaching and notifications for a more responsive training experience.
- Introduction of the Reasoning Module v1.0 with large language model (LLM) integration for generating user-friendly explanations.
- Added mission-specific configuration and improved integration with daily reasoning decisions.
- Improved error handling, streamlined configuration, and updated documentation.
- Expanded test coverage and upgraded dependencies (e.g., Streamlit 1.45.x).

## Looking Ahead

With version **v0.3.1**, Lanterne Rouge provides a solid foundation for AI-powered coaching, combining data-driven insights with mission-aware training recommendations.

In our TO DO:
- Refining recommendations and data visualization.
- Exploration of n8n for workflow orchestration.
- Deeper trend analysis.
- Smarter plan adaptations.
- Enhanced personalization to support your endurance journey.

You can track upcoming features and roadmap progress on the [Lanterne Rouge Project Board](https://github.com/users/alponsirenas/projects/2).

## License

Lanterne Rouge is licensed under the [Apache License 2.0](LICENSE).

You are welcome to use, modify, and share this project under the terms of the license.  
Your journey, your race, your victory.
