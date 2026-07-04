#!/usr/bin/env python3
"""Persist a rotated Strava refresh token back to the GitHub Actions secret.

Run after run_morning.py in CI. Compares tokens.json against the
STRAVA_REFRESH_TOKEN the workflow started with; when Strava rotated it,
encrypts the new one with the repo's public key and PUTs the secret.
Never fails the morning run: missing GH_PAT or an API error just warns.
"""

import base64
import json
import os
import sys
from pathlib import Path

import requests

TOKENS_PATH = Path(__file__).resolve().parents[1] / "tokens.json"


def main():
    if not TOKENS_PATH.exists():
        print("No tokens.json, nothing to persist.")
        return
    new_refresh = json.loads(TOKENS_PATH.read_text()).get("refresh_token")
    old_refresh = os.getenv("STRAVA_REFRESH_TOKEN")
    if not new_refresh or new_refresh == old_refresh:
        print("Refresh token unchanged.")
        return

    pat = os.getenv("GH_PAT")
    if not pat:
        print("WARNING: Strava rotated the refresh token but GH_PAT is not set; "
              "update the STRAVA_REFRESH_TOKEN secret by hand or the next run will fail.")
        return

    from nacl import encoding, public  # deferred, only CI needs pynacl

    repo = os.getenv("GITHUB_REPOSITORY", "alponsirenas/lanterne-rouge")
    headers = {"Authorization": f"Bearer {pat}", "Accept": "application/vnd.github+json"}

    r = requests.get(f"https://api.github.com/repos/{repo}/actions/secrets/public-key",
                     headers=headers, timeout=15)
    r.raise_for_status()
    key = r.json()

    sealed = public.SealedBox(
        public.PublicKey(key["key"].encode(), encoding.Base64Encoder())
    ).encrypt(new_refresh.encode())
    r = requests.put(
        f"https://api.github.com/repos/{repo}/actions/secrets/STRAVA_REFRESH_TOKEN",
        headers=headers,
        json={"encrypted_value": base64.b64encode(sealed).decode(), "key_id": key["key_id"]},
        timeout=15,
    )
    r.raise_for_status()
    print("STRAVA_REFRESH_TOKEN secret updated with the rotated token.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # never block the morning run on this
        print(f"WARNING: could not persist rotated token: {exc}")
        sys.exit(0)
