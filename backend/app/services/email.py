import asyncio
import smtplib
from email.message import EmailMessage
from email.utils import parseaddr

import httpx
import yaml

from app.settings import CONFIG_DIR, settings

_COPY = yaml.safe_load((CONFIG_DIR / "emails.yaml").read_text("utf-8"))
EMAILS = _COPY  # dipakai juga oleh auth remaja & jobs


def _send(msg: EmailMessage) -> None:
    """Gagal kirim → OSError (pemanggil sudah menangkapnya), baik lewat SMTP maupun Brevo."""
    if settings.brevo_api_key:  # Railway memblokir SMTP keluar; API HTTPS tidak
        name, sender = parseaddr(settings.smtp_from)
        try:
            httpx.post(
                "https://api.brevo.com/v3/smtp/email",
                headers={"api-key": settings.brevo_api_key},
                json={
                    "sender": {"name": name or "AmanDjiwa", "email": sender},
                    "to": [{"email": str(msg["To"])}],
                    "subject": str(msg["Subject"]),
                    "textContent": msg.get_content(),
                },
                timeout=10,
            ).raise_for_status()
        except httpx.HTTPError as e:
            raise OSError(type(e).__name__) from None  # tanpa isi respons (bisa memuat alamat)
        return
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


async def send_plain(to: str, subject: str, body: str) -> None:
    """Email teks biasa untuk staf (peringatan kasus merah, laporan mingguan)."""
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.smtp_from
    msg["To"] = to
    msg.set_content(body)
    await asyncio.to_thread(_send, msg)
