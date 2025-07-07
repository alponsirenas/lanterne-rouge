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
   # Optional: override the default model (default: gpt-4-turbo-preview)
   # Use a model that supports JSON response format such as:
   # gpt-4-turbo-preview, gpt-4o, gpt-4o-mini, gpt-4-0125-preview, or gpt-3.5-turbo-1106
   OPENAI_MODEL=gpt-4-turbo-preview
   # Optional: control reasoning mode (default: true)
   USE_LLM_REASONING=true

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

## Current Version: v0.5.0

Release highlights:
- **Power-Based Activity Analysis** - Scientific training load assessment using Intensity Factor (IF) and Training Stress Score (TSS)
- **LLM-Powered TDF Simulation** - Intelligent stage analysis with AI-driven performance evaluation
- **Enhanced Security & Validation** - Robust input validation and sanitization for all LLM interactions
- **Smart Ride Mode Detection** - GC vs Breakaway classification based on power zones and athlete FTP
- **Comprehensive Post-Stage Analysis** - Strategic guidance and recovery recommendations
- **Fallback Reliability** - Rule-based analysis when LLM services are unavailable
- **TDF Points System** - 21-stage gamified Tour de France simulation
- **Automated Workflows** - Morning briefings and evening points tracking
- **Achievement Bonuses** - 5 bonus categories with strategic gameplay
- **GitHub Actions Integration** - Complete automation with 4 new workflows
- **Backwards Compatibility** - Existing coaching system unchanged

### New Power Analysis Features
- **FTP-Based Calculations**: All power metrics relative to individual athlete's Functional Threshold Power
- **Scientific Accuracy**: Uses established sports science metrics instead of subjective suffer scores
- **Intelligent Classification**: LLM analyzes power data contextually for strategic recommendations
- **Training Load Management**: TSS-based recovery recommendations and strategic planning

See the full [Release Notes for v0.5.0](RELEASE_NOTES_v0.5.0.md) for detailed information.

## Looking Ahead

With version **v0.5.0**, Lanterne Rouge delivers a sophisticated agent-based coaching system with LLM-powered reasoning at its core, now enhanced with the gamified TDF Points System for engaging, goal-oriented training experiences.

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
