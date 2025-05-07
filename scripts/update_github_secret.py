
# Standard library imports
import os
import sys
import base64
import json
import binascii

# Third-party library imports
import requests
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization, hashes
from dotenv import load_dotenv

load_dotenv()

# Inputs
repo_owner = os.getenv("REPO_OWNER")  # e.g., "alponsirenas"
repo_name = os.getenv("REPO_NAME")    # e.g., "lanterne-rouge"
secret_name = "STRAVA_REFRESH_TOKEN"
new_secret_value = os.getenv("STRAVA_REFRESH_TOKEN")  # new value to write
github_token = os.getenv("GH_PAT")

# Step 1: Get the repository public key
headers = {
    "Authorization": f"token {github_token}",
    "Accept": "application/vnd.github+json"
}
url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/actions/secrets/public-key"
resp = requests.get(url, headers=headers)
resp.raise_for_status()
key_data = resp.json()

# Step 2: Encrypt the secret using the public key
public_key = serialization.load_pem_public_key(
    base64.b64decode(key_data["key"].encode("utf-8"))
)
encrypted_value = public_key.encrypt(
    new_secret_value.encode("utf-8"),
    padding.PKCS1v15()
)
encrypted_base64 = base64.b64encode(encrypted_value).decode("utf-8")

# Step 3: Put the secret back into GitHub
put_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/actions/secrets/{secret_name}"
payload = {
    "encrypted_value": encrypted_base64,
    "key_id": key_data["key_id"]
}
put_resp = requests.put(put_url, headers=headers, data=json.dumps(payload))
put_resp.raise_for_status()

print(f"✅ Successfully updated {secret_name} in {repo_owner}/{repo_name}")
