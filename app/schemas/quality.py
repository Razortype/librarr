from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class QualityObject(BaseModel):
    format: Literal["epub", "mobi", "azw3", "pdf", "m4b", "mp3"]
    language: str  # ISO 639-1
    source_quality: str | None = None  # e.g. 'retail', 'web', 'cdrom'
