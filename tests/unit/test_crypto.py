from __future__ import annotations

import pytest
from cryptography.fernet import Fernet, InvalidToken

from app.core.crypto import decrypt_config, encrypt_config


def test_round_trip_preserves_data() -> None:
    data = {"host": "localhost", "port": 8080, "username": "admin", "password": "s3cr3t"}
    ciphertext = encrypt_config(data)
    assert decrypt_config(ciphertext) == data


def test_ciphertext_is_bytes() -> None:
    ciphertext = encrypt_config({"key": "value"})
    assert isinstance(ciphertext, bytes)


def test_wrong_key_raises_invalid_token() -> None:
    ciphertext = encrypt_config({"key": "value"})

    other_key = Fernet.generate_key()
    other_fernet = Fernet(other_key)

    with pytest.raises(InvalidToken):
        other_fernet.decrypt(ciphertext)
