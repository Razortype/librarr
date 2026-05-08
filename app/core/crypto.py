from __future__ import annotations

import json
from typing import Any

from cryptography.fernet import Fernet

from app.core.config import settings

_fernet = Fernet(settings.librarr_secret_key.encode())


def encrypt_config(data: dict[str, Any]) -> bytes:
    plaintext = json.dumps(data).encode()
    return _fernet.encrypt(plaintext)


def decrypt_config(ciphertext: bytes) -> dict[str, Any]:
    plaintext = _fernet.decrypt(ciphertext)
    return json.loads(plaintext.decode())
