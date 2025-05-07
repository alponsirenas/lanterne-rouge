# Standard library imports
import os
import sys
import base64
import json
import binascii

# Third-party library imports
import requests
from nacl import encoding, public
from dotenv import load_dotenv

load_dotenv()

# Inputs
repo_owner = os.getenv("REPO_OWNER")  # e.g., "alponsirenas"
repo_name = os.getenv("REPO_NAME")    # e.g., "lanterne-rouge"
secret_name = "STRAVA_REFRESH_TOKEN"
new_secret_value = os.getenv("STRAVA_REFRESH_TOKEN")  # new value to write
github_token = os.getenv("GH_PAT")

# Check for required GitHub token
if not github_token:
    print("❌ GH_PAT not found in environment. Ensure it is set as a secret and exposed to the script.")
    sys.exit(1)

# Step 1: Get the repository public key
headers = {
    "Authorization": f"token {github_token}",
    "Accept": "application/vnd.github+json",
    "User-Agent": "update-github-secret-script"
}
url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/actions/secrets/public-key"
resp = requests.get(url, headers=headers)
resp.raise_for_status()
key_data = resp.json()

# GitHub public key is Base64‑encoded and expects libsodium sealed‑box encryption
public_key = public.PublicKey(key_data["key"].encode("utf-8"), encoding.Base64Encoder())
sealed_box = public.SealedBox(public_key)
encrypted = sealed_box.encrypt(new_secret_value.encode("utf-8"))
encrypted_base64 = base64.b64encode(encrypted).decode("utf-8")

# Step 3: Put the secret back into GitHub
put_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/actions/secrets/{secret_name}"
payload = {
    "encrypted_value": encrypted_base64,
    "key_id": key_data["key_id"]
}
put_resp = requests.put(put_url, headers=headers, data=json.dumps(payload))
put_resp.raise_for_status()

print(f"✅ Successfully updated a secret in {repo_owner}/{repo_name}")
