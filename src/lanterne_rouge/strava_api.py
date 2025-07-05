# strava_api.py

import os
import json
import requests
import threading
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

# Thread safety: Add locks to protect global variable access
_token_lock = threading.Lock()
_athlete_id_lock = threading.Lock()

# Try to load updated tokens from tokens.json if it exists and USE_TOKEN_CACHE is True
if USE_TOKEN_CACHE and os.path.exists("tokens.json"):
    with open("tokens.json", "r", encoding="utf-8") as f:
        tokens = json.load(f)
    with _token_lock:
        STRAVA_ACCESS_TOKEN = tokens["access_token"]
        STRAVA_REFRESH_TOKEN = tokens["refresh_token"]


# ---------------------------------------------------------------------------
# Athlete‑ID helper
# ---------------------------------------------------------------------------
# We avoid storing the athlete ID in MissionConfig files; instead we fetch it
# once per run and memoise it here.  Down‑stream modules can call
# `get_athlete_id()` whenever they need the numeric Strava user identifier.

_ATHLETE_ID_CACHE: int | None = None


def get_athlete_id() -> int:
    """
    Return the numeric athlete ID associated with the current access token.

    We fetch it once via `/athlete` and cache the result for the remainder of
    the Python process.  If the access token is expired, we auto‑refresh first.
    Thread-safe implementation with proper locking.
    """
    global _ATHLETE_ID_CACHE, STRAVA_ACCESS_TOKEN

    # Check cache first with lock protection
    with _athlete_id_lock:
        if _ATHLETE_ID_CACHE is not None:
            return _ATHLETE_ID_CACHE

    # Get current access token safely
    with _token_lock:
        current_token = STRAVA_ACCESS_TOKEN

    headers = {"Authorization": f"Bearer {current_token}"}
    url = f"{STRAVA_BASE_URL}/athlete"

    response = requests.get(url, headers=headers, timeout=10)

    # Handle token expiry transparently
    if response.status_code == 401:
        refreshed_token, _ = refresh_strava_token()
        if refreshed_token is None:
            raise RuntimeError("Failed to refresh Strava access token.")
        headers["Authorization"] = f"Bearer {refreshed_token}"
        response = requests.get(url, headers=headers, timeout=10)

    response.raise_for_status()
    athlete_id = response.json()["id"]
    
    # Cache the result safely
    with _athlete_id_lock:
        _ATHLETE_ID_CACHE = athlete_id
        
    print(f"✅ Fetched athlete ID {athlete_id} (cached)")
    return athlete_id


def refresh_strava_token():
    """
    Refresh the Strava Access Token using the Refresh Token and save to
    tokens.json. Thread-safe implementation with proper locking.
    """
    global STRAVA_ACCESS_TOKEN
    global STRAVA_REFRESH_TOKEN

    print("🔄 Refreshing Strava Access Token...")
    
    # Get current tokens safely
    with _token_lock:
        current_client_id = STRAVA_CLIENT_ID
        current_client_secret = STRAVA_CLIENT_SECRET
        current_refresh_token = STRAVA_REFRESH_TOKEN

    token_url = "https://www.strava.com/oauth/token"
    payload = {
        "client_id": current_client_id,
        "client_secret": current_client_secret,
        "grant_type": "refresh_token",
        "refresh_token": current_refresh_token,
    }
    response = requests.post(token_url, data=payload, timeout=10)
    if response.status_code == 200:
        tokens = response.json()
        new_access_token = tokens['access_token']
        new_refresh_token = tokens['refresh_token']
        expires_at = tokens['expires_at']

        # Update global tokens safely
        with _token_lock:
            STRAVA_ACCESS_TOKEN = new_access_token
            STRAVA_REFRESH_TOKEN = new_refresh_token

        print(
            f"✅ Refreshed! New Access Token Expires At: {expires_at}"
        )

        # Save updated tokens to tokens.json if USE_TOKEN_CACHE is True
        if USE_TOKEN_CACHE:
            with open("tokens.json", "w", encoding="utf-8") as f:
                json.dump(tokens, f, indent=2)

        return new_access_token, new_refresh_token
    print(f"❌ Failed to refresh token: {response.text}")
    return None, None


def strava_get(endpoint):
    """
    Perform a GET request to Strava API with current Access Token.
    Thread-safe implementation.
    """
    global STRAVA_ACCESS_TOKEN
    
    # Get current token safely
    with _token_lock:
        current_token = STRAVA_ACCESS_TOKEN
        
    headers = {
        "Authorization": f"Bearer {current_token}"
    }
    url = f"{STRAVA_BASE_URL}/{endpoint}"

    response = requests.get(url, headers=headers, timeout=10)

    # If token expired, refresh and retry once
    if response.status_code == 401:
        refreshed_access_token, refreshed_refresh_token = refresh_strava_token()
        if refreshed_access_token:
            headers["Authorization"] = f"Bearer {refreshed_access_token}"
            response = requests.get(url, headers=headers, timeout=10)

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
    Thread-safe implementation.
    """
    global STRAVA_ACCESS_TOKEN
    
    # Get current token safely
    with _token_lock:
        current_token = STRAVA_ACCESS_TOKEN
        
    headers = {
        "Authorization": f"Bearer {current_token}",
        "Content-Type": "application/json"
    }
    url = f"{STRAVA_BASE_URL}/{endpoint}"

    response = requests.post(url, headers=headers, json=payload, timeout=10)

    # If token expired, refresh and retry once
    if response.status_code == 401:
        refreshed_access_token, refreshed_refresh_token = refresh_strava_token()
        if refreshed_access_token:
            headers["Authorization"] = f"Bearer {refreshed_access_token}"
            response = requests.post(url, headers=headers, json=payload, timeout=10)

    return response.json()
