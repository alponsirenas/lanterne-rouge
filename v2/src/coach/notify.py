# notify.py
# Sends the daily coaching recommendation by email (Gmail SMTP).
# Skips silently if EMAIL_ADDRESS is not set — safe to run locally without credentials.

import os
import smtplib
from email.mime.text import MIMEText

from dotenv import load_dotenv

load_dotenv()


def send_email(subject: str, body: str) -> None:
    """Send a plain-text email via Gmail SMTP SSL.

    Required env vars: EMAIL_ADDRESS, EMAIL_PASS, TO_EMAIL
    Uses a Gmail App Password — not your account password.
    See: https://support.google.com/accounts/answer/185833
    """
    sender = os.getenv("EMAIL_ADDRESS")
    password = os.getenv("EMAIL_PASS")
    recipient = os.getenv("TO_EMAIL")

    if not all([sender, password, recipient]):
        print("⚠️  Email not configured (EMAIL_ADDRESS / EMAIL_PASS / TO_EMAIL not set) — skipping.")
        return

    msg = MIMEText(body, "plain")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipient

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, password)
            server.send_message(msg)
        print(f"📧  Email sent to {recipient}")
    except smtplib.SMTPException as exc:
        print(f"❌  Failed to send email: {exc}")
