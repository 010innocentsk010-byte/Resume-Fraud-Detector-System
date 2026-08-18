"""Candidate-facing notification emails for the public apply-link flow.

Plain smtplib — no provider SDK, works with any standard SMTP relay. If
SMTP_HOST isn't configured, sending is skipped (logged, not raised): a
missing mail setup must never break the apply request a candidate is
waiting on.

Content rule, same as everywhere else a candidate-facing response is built
(PublicApplyResponse carries no score fields either): never mention fraud,
risk, or any score. A candidate is told only that they matched or didn't —
never why, never a number.
"""
import smtplib
from email.message import EmailMessage

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def _build_message(to_email: str, candidate_name: str, posting_title: str, company: str | None, qualified: bool) -> EmailMessage:
    employer = company or "the hiring team"
    if qualified:
        subject = f"Update on your application for {posting_title}"
        body = (
            f"Hi {candidate_name},\n\n"
            f"Thanks for applying to {posting_title} at {employer}. Your background is a strong match "
            "for this role, and a member of the team will be in touch about next steps.\n\n"
            f"— {employer}"
        )
    else:
        subject = f"Update on your application for {posting_title}"
        body = (
            f"Hi {candidate_name},\n\n"
            f"Thank you for applying to {posting_title} at {employer}. After reviewing applications, "
            "we've decided to move forward with other candidates at this time. We encourage you to "
            "apply to future openings.\n\n"
            f"— {employer}"
        )

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM_ADDRESS}>"
    message["To"] = to_email
    message.set_content(body)
    return message


def send_qualification_email(
    to_email: str, candidate_name: str, posting_title: str, company: str | None, qualified: bool
) -> None:
    if not settings.SMTP_HOST:
        logger.warning(
            "SMTP_HOST not configured — skipping qualification email to %s for posting %r", to_email, posting_title
        )
        return

    message = _build_message(to_email, candidate_name, posting_title, company, qualified)

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as smtp:
            if settings.SMTP_USE_TLS:
                smtp.starttls()
            if settings.SMTP_USERNAME:
                smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            smtp.send_message(message)
    except Exception:
        logger.exception("Failed to send qualification email to %s for posting %r", to_email, posting_title)
