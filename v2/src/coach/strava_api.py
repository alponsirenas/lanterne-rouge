# strava_api.py
# Minimal Strava token management and GET helper.
# Unchanged from original — token refresh and thread safety are still needed.

import json
import os
import threading

import requests
from dotenv import load_dotenv

load_dotenv()

STRAVA_CLIENT_ID = os.getenv("STRAVA_CLIENT_ID")
STRAVA_CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")
STRAVA_ACCESS_TOKEN = os.getenv("STRAVA_ACCESS_TOKEN")
STRAVA_REFRESH_TOKEN = os.getenv("STRAVA_REFRESH_TOKEN")

STRAVA_BASE_URL = "https://www.strava.com/api/v3"

_token_lock = threading.Lock()

# Load cached tokens if available
if os.path.exists("tokens.json"):
    with open("tokens.json", "r", encoding="utf-8") as f:
        _cached = json.load(f)
    with _token_lock:
        STRAVA_ACCESS_TOKEN = _cached["access_token"]
        STRAVA_REFRESH_TOKEN = _cached["refresh_token"]


def refresh_strava_token() -> tuple[str | None, str | None]:
    global STRAVA_ACCESS_TOKEN, STRAVA_REFRESH_TOKEN

    with _token_lock:
        cid, csecret, rtoken = STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET, STRAVA_REFRESH_TOKEN

    resp = requests.post(
        "https://www.strava.com/oauth/token",
        data={"client_id": cid, "client_secret": csecret,
              "grant_type": "refresh_token", "refresh_token": rtoken},
        timeout=10,
    )
    if resp.status_code != 200:
        print(f"❌ Token refresh failed: {resp.text}")
        return None, None

    tokens = resp.json()
    with _token_lock:
        STRAVA_ACCESS_TOKEN = tokens["access_token"]
        STRAVA_REFRESH_TOKEN = tokens["refresh_token"]

    with open("tokens.json", "w", encoding="utf-8") as f:
        json.dump(tokens, f, indent=2)

    return tokens["access_token"], tokens["refresh_token"]


def strava_get(endpoint: str) -> list | dict:
    global STRAVA_ACCESS_TOKEN

    with _token_lock:
        token = STRAVA_ACCESS_TOKEN

    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{STRAVA_BASE_URL}/{endpoint}", headers=headers, timeout=10)

    if resp.status_code == 401:
        new_token, _ = refresh_strava_token()
        if new_token:
            headers["Authorization"] = f"Bearer {new_token}"
            resp = requests.get(f"{STRAVA_BASE_URL}/{endpoint}", headers=headers, timeout=10)

    if resp.status_code != 200:
        print(f"❌ Strava API error {resp.status_code}: {resp.text}")
        return []

    try:
        return resp.json()
    except json.JSONDecodeError:
        print("❌ Failed to decode Strava response.")
        return []
