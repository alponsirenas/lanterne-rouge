import os
import re
import smtplib
from email.mime.text import MIMEText

from dotenv import load_dotenv

# Optional: Twilio fallback
try:
    from twilio.rest import Client
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False

load_dotenv()


def send_email(subject, body, to_email):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = os.getenv("EMAIL_ADDRESS")
    msg['To'] = to_email

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(os.getenv("EMAIL_ADDRESS"), os.getenv("EMAIL_PASS"))
        server.send_message(msg)
        print("Email sent successfully")


def send_sms_via_email(body: str, to_number: str) -> None:
    """
    Send an SMS by emailing the carrier gateway.

    Args:
        body: Message text.
        to_number: Either the full gateway address
                   (e.g. '1234567890@vtext.com') **or**
                   a raw phone number with optional symbols
                   (+, spaces, dashes).

    Environment:
        SMS_GATEWAY_DOMAIN – used when only digits are provided.
                             Defaults to 'txt.att.net'.

    """
    # Build gateway email address
    if "@" in to_number:
        to_number_email = to_number  # already a full address
    else:
        digits = re.sub(r"\D", "", to_number)
        if len(digits) < 10:
            raise ValueError(f"Invalid phone number: '{to_number}'")
        domain = os.getenv("SMS_GATEWAY_DOMAIN", "txt.att.net")
        to_number_email = f"{digits}@{domain}"

    # Empty subject to avoid extra header text on phones
    subject = ""
    send_email(subject, body, to_number_email)
    print("SMS sent successfully")


def send_sms_via_twilio(body, to_number):
    if not TWILIO_AVAILABLE:
        print("Twilio not installed. SMS not sent.")
        return
    client = Client(os.getenv("TWILIO_SID"), os.getenv("TWILIO_AUTH"))
    message = client.messages.create(
        body=body,
        from_=os.getenv("TWILIO_PHONE"),
        to=to_number
    )
    print("SMS sent successfully")
    return message.sid


def send_sms(body, to_number, use_twilio=False):
    if use_twilio:
        return send_sms_via_twilio(body, to_number)
    else:
        return send_sms_via_email(body, to_number)
