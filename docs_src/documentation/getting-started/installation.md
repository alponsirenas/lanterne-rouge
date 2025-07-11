# Installation Guide

Complete installation and setup instructions for Lanterne Rouge.

## System Requirements

- **Python**: 3.8 or higher
- **Operating System**: macOS, Linux, or Windows
- **Memory**: 2GB RAM minimum
- **Storage**: 500MB free space
- **Internet**: Required for API access and updates

## API Prerequisites

Before installing Lanterne Rouge, you'll need API access to:

### Required APIs
- **Oura Ring**: Personal Access Token
- **Strava**: Application credentials (Client ID, Secret, Refresh Token)
- **OpenAI**: API key for GPT models

### Optional APIs
- **Twilio**: For SMS notifications (alternative to email)
- **GitHub**: Personal Access Token for automated workflows

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/alponsirenas/lanterne-rouge.git
cd lanterne-rouge
```

### 2. Set Up Python Environment

=== "Using venv (Recommended)"

    ```bash
    python3 -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```

=== "Using conda"

    ```bash
    conda create -n lanterne-rouge python=3.11
    conda activate lanterne-rouge
    ```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

For documentation development:
```bash
pip install -r requirements-docs.txt
```

### 4. Configuration

1. **Copy environment template:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` with your credentials:**
   ```env
   # Required APIs
   OURA_TOKEN=your_oura_personal_access_token
   STRAVA_CLIENT_ID=your_strava_client_id
   STRAVA_CLIENT_SECRET=your_strava_client_secret
   STRAVA_REFRESH_TOKEN=your_strava_refresh_token
   OPENAI_API_KEY=your_openai_api_key
   
   # Optional: Model configuration
   OPENAI_MODEL=gpt-4-turbo-preview
   USE_LLM_REASONING=true
   
   # Notifications
   EMAIL_ADDRESS=your_email@example.com
   EMAIL_PASS=your_app_password
   TO_EMAIL=recipient@example.com
   TO_PHONE=1234567890@txt.att.net
   
   # Optional: Twilio SMS
   USE_TWILIO=false
   TWILIO_ACCOUNT_SID=your_twilio_sid
   TWILIO_AUTH_TOKEN=your_twilio_token
   TWILIO_FROM_PHONE=your_twilio_number
   
   # GitHub integration
   GH_PAT=your_github_personal_access_token
   ```

### 5. Initialize Database

```bash
python -c "from lanterne_rouge.mission_config import bootstrap; bootstrap('missions/tdf_sim_2025.toml')"
```

This creates the SQLite database (`memory/lanterne.db`) with your mission configuration.

### 6. Verify Installation

Run a test to ensure everything is working:

```bash
python scripts/daily_run.py --dry-run
```

## API Setup Guides

### Oura Ring API

1. Visit [Oura Developer Portal](https://cloud.ouraring.com/personal-access-tokens)
2. Log in with your Oura account
3. Generate a Personal Access Token
4. Copy the token to your `.env` file

### Strava API

1. Go to [Strava API Settings](https://www.strava.com/settings/api)
2. Create a new application
3. Note your Client ID and Client Secret
4. Follow the OAuth flow to get a Refresh Token
5. Add all credentials to your `.env` file

### OpenAI API

1. Visit [OpenAI API Keys](https://platform.openai.com/api-keys)
2. Create a new API key
3. Add to your `.env` file
4. Ensure you have sufficient credits/usage limits

## Troubleshooting

### Common Issues

**Permission Denied on macOS/Linux:**
```bash
chmod +x scripts/*.py
```

**Python Module Not Found:**
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Database Initialization Fails:**
- Check that `missions/tdf_sim_2025.toml` exists
- Verify Python path in import statement
- Ensure database directory is writable

**API Connection Issues:**
- Verify all API tokens are valid and active
- Check internet connectivity
- Review API rate limits and quotas

### Getting Help

- Check our [troubleshooting guide](../guides/troubleshooting.md)
- Review [GitHub Issues](https://github.com/alponsirenas/lanterne-rouge/issues)
- Join discussions in [GitHub Discussions](https://github.com/alponsirenas/lanterne-rouge/discussions)

## Next Steps

Once installation is complete:

1. **First Run**: Execute `python scripts/daily_run.py`
2. **Fiction Mode**: Set up with `python scripts/configure_rider_profile.py example`
3. **Automation**: Configure [GitHub Actions](../guides/github-actions.md) for daily runs
4. **Customization**: Explore [configuration options](configuration.md)
