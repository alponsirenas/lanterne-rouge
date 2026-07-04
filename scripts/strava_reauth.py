#!/usr/bin/env python3
"""One-time Strava re-authorization to add the profile:read_all scope.

Run it, open the printed URL, approve, paste the URL your browser lands on.
Writes the new tokens to tokens.json and prints what to update in GitHub Secrets.
"""

import json
import os
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

CLIENT_ID = os.getenv("STRAVA_CLIENT_ID")
CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")
if not (CLIENT_ID and CLIENT_SECRET):
    sys.exit("STRAVA_CLIENT_ID / STRAVA_CLIENT_SECRET not found in .env")

print(
    "\n1. Open this URL in your browser and click Authorize:\n\n"
    f"https://www.strava.com/oauth/authorize?client_id={CLIENT_ID}"
    "&response_type=code&redirect_uri=http://localhost&approval_prompt=force"
    "&scope=read,activity:read_all,profile:read_all\n\n"
    "2. Your browser will land on a page that fails to load (http://localhost/...).\n"
    "   That is expected. Copy the ENTIRE address from the address bar.\n"
)
pasted = input("3. Paste that address (or just the code) here: ").strip()

if "code=" in pasted:
    code = parse_qs(urlparse(pasted).query)["code"][0]
else:
    code = pasted

resp = requests.post(
    "https://www.strava.com/oauth/token",
    data={
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
    },
    timeout=15,
)
if resp.status_code != 200:
    sys.exit(f"\nExchange failed ({resp.status_code}): {resp.text}\n"
             "Codes are single-use and expire fast; run this script again for a fresh one.")

tokens = resp.json()
(ROOT / "tokens.json").write_text(json.dumps(
    {"access_token": tokens["access_token"], "refresh_token": tokens["refresh_token"]},
    indent=2,
))

print("\nDone. tokens.json updated, the morning loop will use it from now on.")
print("\nFor GitHub Secrets (Phase 2), set STRAVA_REFRESH_TOKEN to:\n")
print(f"  {tokens['refresh_token']}\n")
