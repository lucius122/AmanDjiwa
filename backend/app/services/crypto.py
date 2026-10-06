"""Enkripsi at-rest AES-256-GCM (CLAUDE.md §7). Format: versi(1) | nonce(12) | ciphertext+tag."""

import base64
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.settings import settings

_VERSION = b"\x01"  # naikkan saat rotasi kunci; dekripsi lalu pilih kunci menurut byte ini
_aes = AESGCM(base64.b64decode(settings.message_enc_key))


def encrypt(text: str) -> bytes:
    nonce = os.urandom(12)
    return _VERSION + nonce + _aes.encrypt(nonce, text.encode(), None)


def decrypt(blob: bytes) -> str:
    if blob[:1] != _VERSION:
        raise ValueError("versi enkripsi tidak dikenal")
    return _aes.decrypt(blob[1:13], blob[13:], None).decode()
