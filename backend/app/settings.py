import base64
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = Path(__file__).resolve().parent / "config"  # YAML: teks UI, leksikon, hotline


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT / ".env", extra="ignore")

    database_url: str
    message_enc_key: str  # base64 dari 32 byte acak
    jwt_secret: str
    frontend_origin: str = "http://localhost:5173"
    # Demo hackathon (§6.9): izinkan `cli seed-demo` & tandai dasbor kota "data contoh".
    demo_mode: bool = False
    # Tugas terjadwal (jobs/) di proses API. Matikan kalau ada proses lain yang menjalankannya.
    run_jobs: bool = True
    # Admin kota PERTAMA dibuat otomatis saat start kalau belum ada admin kota sama sekali
    # (hosting tanpa akses terminal, mis. Railway). Login pertama tetap wajib pasang authenticator
    # + ganti password. Hapus variabelnya setelah admin berhasil masuk.
    bootstrap_admin_email: str = ""
    bootstrap_admin_password: str = ""
    bootstrap_admin_name: str = "Admin Kota"
    # Kode authenticator (TOTP) saat login staf. Keputusan 2026-10-06: DIMATIKAN DULU (staf masuk
    # cukup email + password). STAFF_TOTP=true menyalakannya lagi, termasuk pasang authenticator
    # di login pertama. Wajib dinyalakan sebelum dipakai dengan data remaja sungguhan.
    staff_totp: bool = False

    redis_url: str = "redis://127.0.0.1:6379/0"

    # LLM opsional untuk balasan level hijau (§6.4). Kosong = LLM mati, pakai bank respons saja.
    nvidia_api_key: str = ""

    # Telegram (§3: aiogram 3, mode webhook). Kosong = bot nonaktif, endpoint webhook 503.
    telegram_bot_token: str = ""
    telegram_webhook_secret: str = ""
    telegram_bot_username: str = (
        "AmanDjiwa_bot"  # handle dari BotFather (cek: cli telegram-webhook)
    )

    smtp_host: str = "127.0.0.1"
    smtp_port: int = 1025
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "AmanDjiwa <no-reply@amandjiwa.local>"
    # Railway (paket Hobby/Trial) memblokir SMTP keluar. Diisi → email dikirim lewat API HTTPS
    # Brevo; pengirimnya SMTP_FROM, dan alamat itu harus terverifikasi di Brevo. Kosong = SMTP.
    brevo_api_key: str = ""

    @field_validator("database_url")
    @classmethod
    def _asyncpg_scheme(cls, v: str) -> str:
        """Railway memberi postgres:// atau postgresql://; SQLAlchemy async butuh +asyncpg."""
        for prefix in ("postgres://", "postgresql://"):
            if v.startswith(prefix):
                return "postgresql+asyncpg://" + v.removeprefix(prefix)
        return v

    @field_validator("message_enc_key")
    @classmethod
    def _key_is_32_bytes(cls, v: str) -> str:
        if len(base64.b64decode(v)) != 32:
            raise ValueError("MESSAGE_ENC_KEY harus base64 dari tepat 32 byte")
        return v

    @field_validator("jwt_secret")
    @classmethod
    def _jwt_secret_strong(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("JWT_SECRET minimal 32 karakter")
        return v


settings = Settings()  # type: ignore[call-arg]  # nilai wajib datang dari env
