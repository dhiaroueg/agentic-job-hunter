"""Persist daily reports and send email only when SMTP credentials are configured."""
from email.message import EmailMessage
import smtplib
from pathlib import Path

from app.config import settings


def save_report(report: str, report_date: str) -> Path:
    folder = Path(settings.REPORT_DIR)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"job_report_{report_date}.md"
    path.write_text(report, encoding="utf-8")
    return path


def send_report(report: str, report_date: str) -> bool:
    if not (settings.EMAIL_SENDER and settings.EMAIL_PASSWORD and settings.EMAIL_RECEIVER):
        return False
    message = EmailMessage()
    message["Subject"] = f"Votre rapport quotidien de stages – {report_date}"
    message["From"] = settings.EMAIL_SENDER
    message["To"] = settings.EMAIL_RECEIVER
    message.set_content(report)
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=30) as smtp:
        if settings.SMTP_USE_TLS:
            smtp.starttls()
        smtp.login(settings.EMAIL_SENDER, settings.EMAIL_PASSWORD)
        smtp.send_message(message)
    return True
