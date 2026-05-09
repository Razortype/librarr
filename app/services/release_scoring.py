from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Literal

_FORMAT_RE = re.compile(r"\b(epub|pdf|mobi|azw3)\b", re.IGNORECASE)
_FORMAT_SCORES: dict[str, int] = {"epub": 100, "azw3": 70, "pdf": 60, "mobi": 40}
_SIZE_PENALTY_THRESHOLD_MB = 100
_AGE_THRESHOLD_DAYS = 365

DetectedFormat = Literal["epub", "pdf", "mobi", "azw3", "unknown"]


def score_release(
    title: str,
    seeders: int,
    size_bytes: int,
    publish_date: datetime | None,
    now: datetime | None = None,
) -> tuple[DetectedFormat, int]:
    """Return (detected_format, score) for a release candidate.

    Pure function — no I/O. Pass `now` in tests to avoid time-dependent results.
    """
    if now is None:
        now = datetime.now(timezone.utc)

    m = _FORMAT_RE.search(title)
    detected: DetectedFormat = m.group(1).lower() if m else "unknown"  # type: ignore[assignment]
    format_score = _FORMAT_SCORES.get(detected, 0)

    seeder_score = min(seeders, 50) * 2

    size_mb = size_bytes / (1024 * 1024)
    size_penalty = (size_mb - _SIZE_PENALTY_THRESHOLD_MB) * 0.5 if size_mb > _SIZE_PENALTY_THRESHOLD_MB else 0.0

    age_penalty = 0
    if publish_date is not None:
        pd = publish_date if publish_date.tzinfo else publish_date.replace(tzinfo=timezone.utc)
        n = now if now.tzinfo else now.replace(tzinfo=timezone.utc)
        if (n - pd).days > _AGE_THRESHOLD_DAYS:
            age_penalty = 10

    return detected, round(format_score + seeder_score - size_penalty - age_penalty)
