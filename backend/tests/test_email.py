from email.message import EmailMessage
from typing import Any

import httpx
import pytest

from app.services import email
from app.settings import settings


def test_brevo_used_when_key_set_and_errors_become_oserror(monkeypatch: pytest.MonkeyPatch) -> None:
    sent: list[dict[str, Any]] = []

    def fake_post(
        url: str, *, headers: dict[str, str], json: dict[str, Any], timeout: int
    ) -> httpx.Response:
        sent.append({"headers": headers, "json": json})
        status = 401 if json["subject"] == "gagal" else 201
        return httpx.Response(status, request=httpx.Request("POST", url))

    monkeypatch.setattr(settings, "brevo_api_key", "kunci-tes")
    monkeypatch.setattr(settings, "smtp_from", "AmanDjiwa <tim@contoh.id>")
    monkeypatch.setattr(email.httpx, "post", fake_post)
    msg = EmailMessage()
    msg["To"], msg["Subject"] = "wali@contoh.id", "Izin"
    msg.set_content("Halo")
    email._send(msg)
    assert sent[0]["headers"] == {"api-key": "kunci-tes"}
    assert sent[0]["json"]["sender"] == {"name": "AmanDjiwa", "email": "tim@contoh.id"}
    assert sent[0]["json"]["to"] == [{"email": "wali@contoh.id"}]

    msg.replace_header("Subject", "gagal")
    with pytest.raises(OSError):
        email._send(msg)
