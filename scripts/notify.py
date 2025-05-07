import smtplib
from email.mime.text import MIMEText
import os
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

def send_sms_via_email(body, to_number_email):
    subject = "Lanterne Rouge: Training Plan"
    send_email(subject, body, to_number_email)

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
    return message.sid

def send_sms(body, to_number, use_twilio=False):
    if use_twilio:
        return send_sms_via_twilio(body, to_number)
    else:
        return send_sms_via_email(body, to_number)
