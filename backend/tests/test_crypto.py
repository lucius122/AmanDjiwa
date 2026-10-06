import pytest
from cryptography.exceptions import InvalidTag

from app.services.crypto import decrypt, encrypt


def test_roundtrip_with_random_nonce() -> None:
    a, b = encrypt("aku capek banget"), encrypt("aku capek banget")
    assert a != b
    assert decrypt(a) == decrypt(b) == "aku capek banget"
    assert b"capek" not in a


def test_tampered_ciphertext_is_rejected() -> None:
    blob = bytearray(encrypt("rahasia"))
    blob[-1] ^= 1
    with pytest.raises(InvalidTag):
        decrypt(bytes(blob))
