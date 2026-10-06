import asyncio
import smtplib
from email.message import EmailMessage

import yaml

from app.settings import CONFIG_DIR, settings

_COPY = yaml.safe_load((CONFIG_DIR / "emails.yaml").read_text("utf-8"))


def _send(msg: EmailMessage) -> None:
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
        if settings.smtp_user:  # produksi; dev (Mailpit) tanpa auth
            smtp.starttls()
            smtp.login(settings.smtp_user, settings.smtp_password)
        smtp.send_message(msg)


async def send_guardian_request(to: str, link: str, days: int) -> None:
    tpl = _COPY["guardian_request"]
    msg = EmailMessage()
    msg["Subject"] = tpl["subject"]
    msg["From"] = settings.smtp_from
    msg["To"] = to
    msg.set_content(tpl["body"].format(link=link, days=days, contact=_COPY["contact"]))
    await asyncio.to_thread(_send, msg)
