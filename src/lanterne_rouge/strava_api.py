# strava_api.py

import requests
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

USE_TOKEN_CACHE = os.getenv("USE_TOKEN_CACHE", "true").lower() == "true"

# Load Strava credentials
STRAVA_CLIENT_ID = os.getenv("STRAVA_CLIENT_ID")
STRAVA_CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")
STRAVA_ACCESS_TOKEN = os.getenv("STRAVA_ACCESS_TOKEN")
STRAVA_REFRESH_TOKEN = os.getenv("STRAVA_REFRESH_TOKEN")
STRAVA_BASE_URL = "https://www.strava.com/api/v3"

# Try to load updated tokens from tokens.json if it exists and USE_TOKEN_CACHE is True
if USE_TOKEN_CACHE and os.path.exists("tokens.json"):
    with open("tokens.json", "r") as f:
        tokens = json.load(f)
    STRAVA_ACCESS_TOKEN = tokens["access_token"]
    STRAVA_REFRESH_TOKEN = tokens["refresh_token"]


def refresh_strava_token():
    """
    Refresh the Strava Access Token using the Refresh Token and save to
    tokens.json.
    """
    global STRAVA_ACCESS_TOKEN
    global STRAVA_REFRESH_TOKEN

    print("🔄 Refreshing Strava Access Token...")
    token_url = "https://www.strava.com/oauth/token"
    payload = {
        "client_id": STRAVA_CLIENT_ID,
        "client_secret": STRAVA_CLIENT_SECRET,
        "grant_type": "refresh_token",
        "refresh_token": STRAVA_REFRESH_TOKEN,
    }
    response = requests.post(token_url, data=payload)
    if response.status_code == 200:
        tokens = response.json()
        STRAVA_ACCESS_TOKEN = tokens['access_token']
        STRAVA_REFRESH_TOKEN = tokens['refresh_token']
        expires_at = tokens['expires_at']

        print(
            f"✅ Refreshed! New Access Token Expires At: {expires_at}"
        )

        # Save updated tokens to tokens.json if USE_TOKEN_CACHE is True
        if USE_TOKEN_CACHE:
            with open("tokens.json", "w") as f:
                json.dump(tokens, f, indent=2)

        return STRAVA_ACCESS_TOKEN, STRAVA_REFRESH_TOKEN
    else:
        print(f"❌ Failed to refresh token: {response.text}")
        return None, None


def strava_get(endpoint):
    """
    Perform a GET request to Strava API with current Access Token.
    """
    global STRAVA_ACCESS_TOKEN
    headers = {
        "Authorization": f"Bearer {STRAVA_ACCESS_TOKEN}"
    }
    url = f"{STRAVA_BASE_URL}/{endpoint}"

    response = requests.get(url, headers=headers)

    # If token expired, refresh and retry once
    if response.status_code == 401:
        STRAVA_ACCESS_TOKEN, STRAVA_REFRESH_TOKEN = refresh_strava_token()
        headers["Authorization"] = f"Bearer {STRAVA_ACCESS_TOKEN}"
        response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"❌ Strava API error {response.status_code}: {response.text}")
        return []

    if not response.content:
        print("⚠️ Strava API returned empty response.")
        return []

    try:
        return response.json()
    except json.JSONDecodeError:
        print("❌ Failed to decode JSON from Strava response.")
        return []


def strava_post(endpoint, payload):
    """
    Perform a POST request to Strava API with current Access Token.
    """
    global STRAVA_ACCESS_TOKEN
    headers = {
        "Authorization": f"Bearer {STRAVA_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    url = f"{STRAVA_BASE_URL}/{endpoint}"

    response = requests.post(url, headers=headers, json=payload)

    # If token expired, refresh and retry once
    if response.status_code == 401:
        STRAVA_ACCESS_TOKEN, STRAVA_REFRESH_TOKEN = refresh_strava_token()
        headers["Authorization"] = f"Bearer {STRAVA_ACCESS_TOKEN}"
        response = requests.post(url, headers=headers, json=payload)

    return response.json()
