"""Enkripsi at-rest AES-256-GCM (CLAUDE.md §7). Format: versi(1) | nonce(12) | ciphertext+tag."""

import base64
import hashlib
import hmac
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.settings import settings

_VERSION = b"\x01"  # naikkan saat rotasi kunci; dekripsi lalu pilih kunci menurut byte ini
_KEY = base64.b64decode(settings.message_enc_key)
_aes = AESGCM(_KEY)
# Kunci terpisah untuk hash pencarian email (turunan, supaya tidak memakai kunci AES langsung).
_EMAIL_KEY = hmac.new(_KEY, b"amandjiwa-email-lookup-v1", hashlib.sha256).digest()


def encrypt(text: str) -> bytes:
    nonce = os.urandom(12)
    return _VERSION + nonce + _aes.encrypt(nonce, text.encode(), None)


def decrypt(blob: bytes) -> str:
    if blob[:1] != _VERSION:
        raise ValueError("versi enkripsi tidak dikenal")
    return _aes.decrypt(blob[1:13], blob[13:], None).decode()


def email_lookup_hash(email: str) -> str:
    """Hash email remaja untuk mencari akun saat login, tanpa menyimpan email polos (§7).

    HMAC berkunci: tanpa MESSAGE_ENC_KEY, daftar hash tidak bisa dicocokkan dengan daftar email.
    Ganti kunci = semua remaja perlu reset password (hash lama tidak cocok lagi).
    """
    return hmac.new(_EMAIL_KEY, email.strip().lower().encode(), hashlib.sha256).hexdigest()
