"""Atur Supabase Auth untuk login remaja lewat Management API (bukan klik manual di dashboard):
template email kode OTP (bahasa Indonesia), panjang & masa berlaku kode, Site URL + Redirect URL,
dan — kalau datanya ada di .env — SMTP sendiri serta login Google.

    cd backend && uv run python -m app.cli supabase-auth [--site-url https://domainmu]

Personal access token (supabase.com/dashboard/account/tokens) dibaca dari env
SUPABASE_ACCESS_TOKEN atau ditanyakan lewat prompt. JANGAN disimpan di .env: token itu
berlaku untuk semua proyek di akun Supabase. Cabut setelah dipakai.
"""

import getpass
import os
from typing import Any
from urllib.parse import urlparse

import httpx
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.settings import ROOT

API = "https://api.supabase.com/v1"
TEMPLATE = ROOT / "supabase" / "templates" / "kode-masuk.html"
SUBJECT = "Kode masuk AmanDjiwa"
OTP_LENGTH = 6  # halaman /masuk meminta 6 digit
OTP_EXP_S = 600  # 10 menit (teks template)
WRITE_ONLY = {"smtp_pass", "external_google_secret"}  # bisa tidak dikembalikan oleh GET


class AuthSetup(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT / ".env", extra="ignore")

    supabase_url: str
    frontend_origin: str = "http://localhost:5173"
    google_client_id: str = ""
    google_client_secret: str = ""
    auth_smtp_host: str = ""
    auth_smtp_port: int = 587
    auth_smtp_user: str = ""
    auth_smtp_pass: str = ""
    auth_smtp_sender: str = ""  # alamat pengirim, mis. no-reply@domainmu atau akun Gmail


def build_payload(
    current: dict[str, Any], s: AuthSetup, template: str, site_url: str
) -> tuple[dict[str, Any], list[str]]:
    """(isi PATCH, kunci yang tidak dikenal API). Redirect URL lama tetap dipertahankan."""
    site = site_url.rstrip("/")
    allow = [u for u in (current.get("uri_allow_list") or "").split(",") if u]
    if f"{site}/mulai" not in allow:
        allow.append(f"{site}/mulai")
    want: dict[str, Any] = {
        "site_url": site,
        "uri_allow_list": ",".join(allow),
        "mailer_subjects_magic_link": SUBJECT,
        "mailer_templates_magic_link_content": template,
        "mailer_subjects_confirmation": SUBJECT,  # pengguna baru menerima template ini
        "mailer_templates_confirmation_content": template,
        "mailer_otp_length": OTP_LENGTH,
        "mailer_otp_exp": OTP_EXP_S,
    }
    if bool(s.google_client_id) != bool(s.google_client_secret):
        raise ValueError("Isi GOOGLE_CLIENT_ID dan GOOGLE_CLIENT_SECRET keduanya (atau kosongkan).")
    if s.google_client_id:
        want |= {
            "external_google_enabled": True,
            "external_google_client_id": s.google_client_id,
            "external_google_secret": s.google_client_secret,
        }
    smtp = [s.auth_smtp_host, s.auth_smtp_user, s.auth_smtp_pass, s.auth_smtp_sender]
    if any(smtp) and not all(smtp):
        raise ValueError("SMTP butuh AUTH_SMTP_HOST, _USER, _PASS, dan _SENDER sekaligus.")
    if all(smtp):
        want |= {
            "smtp_host": s.auth_smtp_host,
            "smtp_port": str(s.auth_smtp_port),
            "smtp_user": s.auth_smtp_user,
            "smtp_pass": s.auth_smtp_pass,
            "smtp_admin_email": s.auth_smtp_sender,
            "smtp_sender_name": "AmanDjiwa",
        }
    known = set(current) | WRITE_ONLY
    return {k: v for k, v in want.items() if k in known}, [k for k in want if k not in known]


def run(site_url: str | None) -> None:
    s = AuthSetup()  # type: ignore[call-arg]  # supabase_url wajib dari .env
    ref = (urlparse(s.supabase_url).hostname or "").split(".")[0]
    token = os.environ.get("SUPABASE_ACCESS_TOKEN") or getpass.getpass(
        "Supabase personal access token (tidak disimpan): "
    )
    url = f"{API}/projects/{ref}/config/auth"
    with httpx.Client(headers={"Authorization": f"Bearer {token}"}, timeout=30) as http:
        current = http.get(url)
        if current.status_code in (401, 403):
            raise SystemExit("Token ditolak Supabase (cek token & akses ke proyek ini).")
        current.raise_for_status()
        body, unknown = build_payload(
            current.json(), s, TEMPLATE.read_text("utf-8"), site_url or s.frontend_origin
        )
        http.patch(url, json=body).raise_for_status()
        after = http.get(url).json()
    print(f"Proyek {ref} diperbarui:")
    print(f"  Site URL        : {after.get('site_url')}")
    print(f"  Redirect URL    : {after.get('uri_allow_list')}")
    otp = f"{after.get('mailer_otp_length')} digit, {after.get('mailer_otp_exp')} detik"
    print(f"  Kode OTP        : {otp}")
    tpl = after.get("mailer_templates_magic_link_content") or ""
    print(f"  Template kode   : {'OK' if '{{ .Token }}' in tpl else 'BELUM'}")
    print(f"  SMTP sendiri    : {after.get('smtp_host') or 'belum (masih SMTP bawaan Supabase)'}")
    print(f"  Login Google    : {'aktif' if after.get('external_google_enabled') else 'belum'}")
    if unknown:
        print(f"  PERINGATAN: kunci tidak dikenal API, dilewati: {', '.join(unknown)}")
