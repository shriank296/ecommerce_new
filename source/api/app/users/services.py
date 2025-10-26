import asyncio
import json
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from azure.servicebus import ServiceBusClient

from app.settings import get_app_settings

app_settings = get_app_settings()

logger = logging.getLogger(__name__)


def send_email(to_email: str, subject: str, body: str, html: str | None = None):
    """
    Simple SMTP email sender.
    """
    msg = MIMEMultipart("alternative")
    msg["From"] = app_settings.SMTP_FROM
    msg["To"] = to_email
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain"))
    if html:
        msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP(app_settings.SMTP_HOST, app_settings.SMTP_PORT) as server:
            server.starttls()
            server.login(app_settings.SMTP_USER, app_settings.SMTP_PASSWORD)
            server.send_message(msg)
            logger.info("Sent email to %s", to_email)
    except Exception as e:
        logger.exception("Failed to send email to %s: %s", to_email, e)


def handle_user_created_event(event: dict):
    """
    Process a single UserCreated event and send an email.
    """
    email = event.get("email")
    if not email:
        logger.warning("No email in event, skipping: %s", event)
        return

    subject = "Welcome to our platform!"
    body = (
        f"Hi {email},\n\nYour account has been successfully created.\n\nThanks,\nTeam"
    )
    html = f"<p>Hi <b>{email}</b>,</p><p>Your account has been successfully created.</p><p>Thanks,<br>Team</p>"

    send_email(to_email=email, subject=subject, body=body, html=html)


async def consume_user_created_events():
    sb_client = ServiceBusClient.from_connection_string(app_settings.SB_NAMESPACE)
    with sb_client:
        receiver = sb_client.get_subscription_receiver(
            topic_name=app_settings.SB_ECOMMERCE_USER_CREATED_TOPIC,
            subscription_name=app_settings.SB_SUBSCRIPTION,
        )
        with receiver:
            while True:
                messages = receiver.receive_messages(max_wait_time=5)
                for msg in messages:
                    try:
                        data = json.loads(b"".join([b for b in msg.body]))
                        handle_user_created_event(data)
                        receiver.complete_message(msg)
                    except Exception as e:
                        logger.exception("Error: %s", e)
                        receiver.abandon_message(msg)
                await asyncio.sleep(1)
