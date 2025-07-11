# Lanterne Rouge — Agentic AI for Every Athlete

Named after the iconic "lanterne rouge" — the rider who finishes last at the Tour de France — this project embodies resilience, consistency, and intelligent endurance. It's not about being first; it's about finishing your own race, every stage, every day.

Lanterne Rouge started with the idea of [using AI to train](docs/training_strategy.md) for an AI generated indoor [simulation of the Tour de France 2025](docs/simulation_event.md).

Designed to observe your recovery, reason about your daily readiness, and adapt dynamically to your life and training, Lanterne Rouge plans your next steps without losing sight of your long-term goals.

## How It Works

Lanterne Rouge integrates data from your Oura Ring and Strava to understand your fitness, fatigue, and recovery. Each day, it analyzes this information to generate a personalized coaching report and update your training schedule. This ensures your plan adapts to your progress and needs.

The system provides two complementary experiences:

**🏋️ Classic Coaching Mode**: AI-powered daily analysis with personalized training recommendations, recovery monitoring, and adaptive planning based on your physiological data and performance metrics.

**📖 Fiction Mode**: Transform your training data into immersive cycling narratives, creating compelling stories from your TDF simulation rides with AI-powered event generation and personalized literary styles.

By integrating with your existing tools, Lanterne Rouge helps you stay consistent without adding complexity. Whether you follow structured workouts, use cycling platforms, or ride by feel, the application adapts to keep you moving forward.

All observations and decisions are stored in a lightweight SQLite database (`memory/lanterne.db`). This memory lets the LLM‑powered planner reference recent history when crafting each day's workout.

## Quick Start

**For daily AI coaching and TDF simulation:**

```bash
git clone https://github.com/alponsirenas/lanterne-rouge.git
cd lanterne-rouge
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# Configure your .env file with API keys (Oura, Strava, OpenAI)
python scripts/daily_run.py
```

**For Fiction Mode storytelling:**

```bash
python scripts/configure_rider_profile.py example
python scripts/utils/test_fiction_mode.py
```

## Getting Started

Follow these steps to set up Lanterne Rouge:

### Setup Instructions

1. **Clone the repository:**

   ```bash
   git clone https://github.com/alponsirenas/lanterne-rouge.git
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

4. **Configure your rider profile for Fiction Mode (Optional but recommended):**

   ```bash
   python scripts/configure_rider_profile.py example
   python scripts/configure_rider_profile.py edit
   ```

5. **Initialize the SQLite database:**

   ```bash
   python -c "from lanterne_rouge.mission_config import bootstrap; bootstrap('missions/tdf_sim_2025.toml')"
   ```
   This creates `memory/lanterne.db` seeded with your mission config. It will also be generated automatically the first time you run `daily_run.py`.

6. **Configure your `.env` file with your API credentials and notification settings:**

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

7. **Run your agent daily:**

   - Locally:
     ```bash
     python scripts/daily_run.py
     ```
   - Automatically via GitHub Actions:
     Copy your mission config (for example `missions/tdf_sim_2025.toml`) into `missions/` and then enable the `.github/workflows/daily.yml` workflow to trigger `scripts/daily_run.py` each morning.

8. **Review your coaching report:**
   - Check the daily coaching report to understand your readiness and training focus.
   - Ride, recover, and let the AI adapt your plan as you progress.

9. **Experience Fiction Mode (Enhanced):**
   - Configure your rider profile and generate immersive cycling narratives:
     ```bash
     python scripts/configure_rider_profile.py example
     python scripts/utils/test_fiction_mode.py
     python scripts/run_fiction_mode.py --style krabbe
     ```
   - See [Fiction Mode Documentation](docs/fiction_mode.md) for full details.

10. **Review and update documentation:**
    - Regularly review the project documentation to ensure it remains accurate and up-to-date.
    - The documentation website is available at [https://alponsirenas.github.io/lanterne-rouge/](https://alponsirenas.github.io/lanterne-rouge/)

This system is designed to fit into your routine, helping you build consistency and resilience without overwhelm.

## Current Version: v0.7.0

**🎉 Major Release: Complete Fiction Mode Integration & Codebase Reorganization**

Release highlights:
- **🚀 Complete Fiction Mode System** - Full dynamic event generation with personalized rider profiles and literary narrative styles
- **🏋️ Enhanced Core Coaching** - Improved daily analysis, recovery monitoring, and adaptive training recommendations
- **🗂️ Professional Project Structure** - Comprehensive reorganization with proper separation of concerns
- **📚 Enhanced Documentation** - Complete release notes and improved project documentation with automated updates
- **🎭 Immersive TDF Simulation** - AI-powered storytelling that adapts to your riding style and creates compelling race narratives
- **⚡ Enhanced Reasoning System** - Multiple analysis modes for deeper insights and better coaching recommendations
- **🔧 Better Developer Experience** - Clean, maintainable codebase with improved organization
- **📦 Production Ready** - Professional structure suitable for scaling and continued development

### Core Features (v0.7.0)

**🏋️ AI-Powered Coaching System:**
- **Daily Analysis**: Comprehensive readiness assessment using Oura Ring recovery data
- **Adaptive Training Plans**: Dynamic workout adjustments based on your fitness and fatigue levels
- **Performance Tracking**: Power-based analysis with IF, TSS, and FTP calculations
- **Recovery Monitoring**: Sleep, HRV, and stress analysis for optimal training timing
- **Smart Notifications**: Morning briefings and evening updates via email/SMS

**🏆 TDF Simulation Experience:**
- **21-Stage Tour**: Complete Tour de France 2025 indoor simulation
- **Points & Classifications**: KOM, Sprint, GC, and stage victory tracking
- **Strategic Gameplay**: Tactical decisions that affect your virtual race position
- **Real Performance Integration**: Your actual power data drives simulation results
- **Live Documentation**: Automatically updated simulation status and stage-by-stage progress

### Fiction Mode Features
- **Personalized Rider Profiles**: Create custom profiles with literary voice, goals, and preferences
- **Dynamic Event Generation**: AI creates realistic race scenarios based on your performance data
- **Literary Narrative Styles**: Choose from various writing styles (Tim Krabbé, etc.) for your race stories
- **Real-time Storytelling**: Transform your indoor TDF simulation into compelling cycling literature
- **Strategic Analysis**: Combine performance data with narrative context for deeper insights
- **Automated Integration**: Narratives automatically appear in documentation website

### Project Organization Improvements
- **`scripts/utils/`**: Diagnostic and utility tools consolidated from root directory
- **`docs/`**: Comprehensive documentation moved from root
- **`docs_src/`**: Source files for the documentation website with automated content updates
- **`src/lanterne_rouge/fiction_mode/`**: Core Fiction Mode functionality with proper module structure
- **Clean Root Directory**: Only essential project files remain in the root

See the full [Release Notes for v0.7.0](docs/RELEASE_NOTES_v0.7.0.md) for detailed information.

## Project Structure

```
lanterne-rouge/
├── src/lanterne_rouge/          # Core application modules
│   ├── fiction_mode/            # Fiction Mode system
│   ├── ai/                      # AI clients and reasoning
│   └── ...                      # Other core modules
├── scripts/                     # Executable scripts
│   ├── utils/                   # Diagnostic and utility scripts
│   └── *.py                     # Main CLI scripts
├── docs/                        # Documentation files
├── docs_src/                    # Documentation website source
│   ├── tdf-simulation/          # TDF simulation documentation
│   │   ├── stages/              # Stage-by-stage progress
│   │   └── tdf-2025-hallucinations/  # Fiction Mode narratives
│   ├── ai-coach/                # AI coaching documentation
│   └── documentation/           # General project docs
├── tests/                       # Test suite
├── config/                      # Configuration files
├── missions/                    # Mission definitions
└── output/                      # Generated reports
```

## Key Features & Capabilities

### 🏋️ **Core Coaching System**
- **AI-Powered Daily Analysis**: LLM-driven coaching with personalized recommendations based on recovery and performance data
- **Adaptive Training Plans**: Dynamic workout adjustments that respond to your readiness and life circumstances  
- **Recovery Integration**: Oura Ring sleep, HRV, and readiness data combined with Strava performance metrics
- **Scientific Training Load**: Power-based analysis using Intensity Factor (IF), Training Stress Score (TSS), and FTP calculations
- **Smart Periodization**: Automatic plan adjustments for optimal training progression and recovery

### 🏆 **Tour de France Simulation**
- **Complete 21-Stage Experience**: Full TDF 2025 simulation with realistic stage profiles and tactics
- **Multiple Classifications**: General Classification (GC), King of the Mountains (KOM), Sprint points, and stage victories
- **Strategic Gameplay**: Tactical decisions (attacks, positioning, pacing) that influence your virtual race results
- **Real Performance Integration**: Your actual power data and training efforts directly impact simulation outcomes
- **Achievement System**: Unlock jerseys, stage wins, and special recognition based on your riding
- **Live Progress Tracking**: Automatically updated documentation shows current status and completed stages

### 📖 **Fiction Mode** 
- **Immersive Storytelling**: Transform your rides into compelling cycling literature with customizable narrative styles
- **Personalized Rider Profiles**: Create custom profiles with literary voice, goals, and racing preferences
- **Dynamic Event Generation**: AI creates realistic race scenarios and dramatic moments based on your performance data
- **Literary Narrative Styles**: Choose from various writing styles (Tim Krabbé, etc.) for your race stories
- **Real-time Story Development**: Your training data becomes the foundation for evolving cycling narratives
- **Integrated Documentation**: Stories automatically integrate into your documentation website

### ⚡ **Automation & Integration**
- **GitHub Actions Workflows**: Automated daily runs, morning briefings, and evening analysis
- **Multi-platform Notifications**: Email, SMS, and GitHub integration for seamless updates
- **Data Pipeline**: Seamless integration between Oura Ring, Strava, and AI analysis
- **Memory System**: SQLite database maintains training history and context for intelligent recommendations
- **Documentation Website**: Live updates to simulation status, narratives, and progress tracking

### 📚 **Documentation & Monitoring**
- **Live Documentation Website**: Automatically updated with current simulation status and progress
- **Stage-by-Stage Tracking**: Detailed progress through each TDF stage with plans and results
- **Fiction Mode Integration**: AI-generated narratives seamlessly integrated into documentation
- **Automated Status Updates**: Current points, completion rate, and strategy automatically maintained

## Looking Ahead

With version **v0.7.0**, Lanterne Rouge delivers a mature, professional-grade agent-based coaching system with comprehensive Fiction Mode capabilities, clean project organization, and enhanced storytelling features. The project now provides both sophisticated training analysis and immersive narrative experiences with live documentation updates.

In our roadmap:
- Refining recommendations and data visualization
- Exploration of n8n for workflow orchestration
- Deeper trend analysis and smarter plan adaptations
- Enhanced personalization to support your endurance journey

You can track upcoming features and roadmap progress on the [Lanterne Rouge Project Board](https://github.com/users/alponsirenas/projects/2).

## Documentation

Visit the **[Lanterne Rouge Documentation Website](https://alponsirenas.github.io/lanterne-rouge/)** for:

- **Getting Started Guide**: Complete setup instructions and configuration
- **TDF 2025 Simulation**: Live progress tracking, stage-by-stage breakdown, and points system
- **The Indoor Rider**: AI-generated cycling narratives from your actual rides
- **AI Coach Features**: Daily briefings, recovery monitoring, and training recommendations
- **API Reference**: Technical documentation for developers

## License

Lanterne Rouge is licensed under the [Apache License 2.0](LICENSE).

You are welcome to use, modify, and share this project under the terms of the license.  
Your journey, your race, your victory.
