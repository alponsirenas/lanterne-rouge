# Quick Start

Get Lanterne Rouge up and running in minutes with this streamlined setup guide.

## Prerequisites

- Python 3.8 or higher
- Git
- API access to:
  - Oura Ring (personal access token)
  - Strava (API credentials)
  - OpenAI (API key)

## Installation

=== "macOS/Linux"

    ```bash
    # Clone the repository
    git clone https://github.com/alponsirenas/lanterne-rouge.git
    cd lanterne-rouge

    # Create virtual environment
    python3 -m venv .venv
    source .venv/bin/activate

    # Install dependencies
    pip install -r requirements.txt
    ```

=== "Windows"

    ```cmd
    # Clone the repository
    git clone https://github.com/alponsirenas/lanterne-rouge.git
    cd lanterne-rouge

    # Create virtual environment
    python -m venv .venv
    .venv\Scripts\activate

    # Install dependencies
    pip install -r requirements.txt
    ```

## Basic Configuration

1. **Create environment file:**
   ```bash
   cp .env.example .env
   ```

2. **Add your API credentials to `.env`:**
   ```env
   OURA_TOKEN=your_oura_personal_access_token
   STRAVA_CLIENT_ID=your_strava_client_id
   STRAVA_CLIENT_SECRET=your_strava_client_secret
   STRAVA_REFRESH_TOKEN=your_strava_refresh_token
   OPENAI_API_KEY=your_openai_api_key
   ```

## First Run

1. **Initialize the database:**
   ```bash
   python -c "from lanterne_rouge.mission_config import bootstrap; bootstrap('missions/tdf_sim_2025.toml')"
   ```

2. **Run your first coaching session:**
   ```bash
   python scripts/daily_run.py
   ```

3. **Optional: Set up Fiction Mode:**
   ```bash
   python scripts/configure_rider_profile.py example
   python scripts/run_fiction_mode.py --preview
   ```

## What's Next?

- 📖 Read the [complete installation guide](installation.md) for detailed setup
- ⚙️ Learn about [configuration options](configuration.md)
- 🏆 Explore the [TDF simulation features](../features/tdf-simulation.md)
- 📚 Set up [Fiction Mode](../guides/fiction-mode-setup.md) for storytelling

!!! tip "Daily Automation"
    Once you're comfortable with manual runs, consider setting up [GitHub Actions](../guides/github-actions.md) for automated daily coaching reports.

## Need Help?

Check our [troubleshooting guide](../guides/troubleshooting.md) or [open an issue](https://github.com/alponsirenas/lanterne-rouge/issues) on GitHub.
