#!/usr/bin/env bash
# Codex environment setup for the Lanterne Rouge project
set -euo pipefail

# Upgrade pip and install required Python packages
python -m pip install --upgrade pip
if [ -f requirements.txt ]; then
    pip install -r requirements.txt
fi

# Provision a .env file with placeholder secrets if none exists
if [ ! -f .env ]; then
cat <<'ENV' > .env
# Sample configuration for local testing
EMAIL_ADDRESS=test@example.com
EMAIL_PASS=changeme
TO_EMAIL=test@example.com
TO_PHONE=1234567890@txt.att.net
USE_TWILIO=false

OURA_TOKEN=dummy_oura_token
STRAVA_CLIENT_ID=dummy_client_id
STRAVA_CLIENT_SECRET=dummy_client_secret
STRAVA_ACCESS_TOKEN=dummy_access_token
STRAVA_REFRESH_TOKEN=dummy_refresh_token
STRAVA_ATHLETE_ID=123456

REPO_OWNER=local
REPO_NAME=lanterne-rouge
GH_PAT=dummy
REPO_PUSH_PAT=dummy
SMS_GATEWAY_DOMAIN=txt.att.net
TWILIO_SID=dummy
TWILIO_AUTH=dummy
TWILIO_PHONE=dummy
ENV
fi
