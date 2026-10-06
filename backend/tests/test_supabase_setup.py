"""Isi konfigurasi Supabase Auth yang dikirim lewat Management API (tanpa jaringan)."""

import pytest

from app.supabase_setup import TEMPLATE, AuthSetup, build_payload

CURRENT = {
    "site_url": "http://localhost:3000",
    "uri_allow_list": "https://lama.example/cb",
    "mailer_subjects_magic_link": "",
    "mailer_templates_magic_link_content": "",
    "mailer_subjects_confirmation": "",
    "mailer_templates_confirmation_content": "",
    "mailer_otp_length": 8,
    "mailer_otp_exp": 3600,
    "external_google_enabled": False,
    "external_google_client_id": None,
    "smtp_host": None,
    "smtp_port": None,
    "smtp_user": None,
    "smtp_admin_email": None,
    "smtp_sender_name": None,
}


def _setup(**kw: object) -> AuthSetup:
    # _env_file=None: tes tidak membaca .env asli (yang nanti berisi kredensial Google/SMTP).
    return AuthSetup(_env_file=None, supabase_url="https://abc.supabase.co", **kw)  # type: ignore[arg-type,call-arg]


def test_template_has_otp_token() -> None:
    assert "{{ .Token }}" in TEMPLATE.read_text("utf-8")


def test_basic_payload_keeps_old_redirects_and_sets_otp() -> None:
    body, unknown = build_payload(
        CURRENT, _setup(), "<p>{{ .Token }}</p>", "http://localhost:5173/"
    )
    assert body["site_url"] == "http://localhost:5173"
    assert body["uri_allow_list"] == "https://lama.example/cb,http://localhost:5173/mulai"
    assert body["mailer_otp_length"] == 6 and body["mailer_otp_exp"] == 600
    assert body["mailer_templates_confirmation_content"] == "<p>{{ .Token }}</p>"
    assert "external_google_enabled" not in body and "smtp_host" not in body
    assert unknown == []


def test_google_and_smtp_only_when_complete() -> None:
    full = _setup(
        google_client_id="id",
        google_client_secret="rahasia",
        auth_smtp_host="smtp-relay.brevo.com",
        auth_smtp_user="u",
        auth_smtp_pass="p",
        auth_smtp_sender="no-reply@contoh.id",
    )
    body, _ = build_payload(CURRENT, full, "x", "http://localhost:5173")
    assert body["external_google_enabled"] is True and body["external_google_secret"] == "rahasia"
    assert body["smtp_port"] == "587" and body["smtp_pass"] == "p"  # kunci tulis-saja tetap dikirim
    with pytest.raises(ValueError):
        build_payload(CURRENT, _setup(google_client_id="id"), "x", "http://localhost:5173")
    with pytest.raises(ValueError):
        build_payload(CURRENT, _setup(auth_smtp_host="h"), "x", "http://localhost:5173")


def test_unknown_keys_are_reported_not_sent() -> None:
    body, unknown = build_payload({"site_url": ""}, _setup(), "x", "http://localhost:5173")
    assert set(body) == {"site_url"} and "mailer_otp_length" in unknown
