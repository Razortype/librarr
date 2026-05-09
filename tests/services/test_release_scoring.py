from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.services.release_scoring import score_release

_NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)

# ---------------------------------------------------------------------------
# Format detection
# ---------------------------------------------------------------------------


def test_epub_format_detected() -> None:
    detected, _ = score_release("Great Book EPUB", 0, 1_000_000, None, now=_NOW)
    assert detected == "epub"


def test_azw3_format_detected() -> None:
    detected, _ = score_release("Great Book AZW3", 0, 1_000_000, None, now=_NOW)
    assert detected == "azw3"


def test_pdf_format_detected() -> None:
    detected, _ = score_release("Great Book.pdf", 0, 1_000_000, None, now=_NOW)
    assert detected == "pdf"


def test_mobi_format_detected() -> None:
    detected, _ = score_release("Great Book.mobi", 0, 1_000_000, None, now=_NOW)
    assert detected == "mobi"


def test_unknown_format_when_no_match() -> None:
    detected, _ = score_release("Great Book", 0, 1_000_000, None, now=_NOW)
    assert detected == "unknown"


def test_format_detection_is_case_insensitive() -> None:
    d1, _ = score_release("Book EPUB", 0, 0, None, now=_NOW)
    d2, _ = score_release("Book epub", 0, 0, None, now=_NOW)
    d3, _ = score_release("Book Epub", 0, 0, None, now=_NOW)
    assert d1 == d2 == d3 == "epub"


# ---------------------------------------------------------------------------
# Format score component
# ---------------------------------------------------------------------------


def test_epub_scores_100() -> None:
    # epub=100, seeders=0, size<100MB, no date → 100+0-0-0=100
    _, s = score_release("epub", 0, 1_000_000, None, now=_NOW)
    assert s == 100


def test_azw3_scores_70() -> None:
    _, s = score_release("azw3", 0, 1_000_000, None, now=_NOW)
    assert s == 70


def test_pdf_scores_60() -> None:
    _, s = score_release("pdf", 0, 1_000_000, None, now=_NOW)
    assert s == 60


def test_mobi_scores_40() -> None:
    _, s = score_release("mobi", 0, 1_000_000, None, now=_NOW)
    assert s == 40


def test_unknown_format_scores_0() -> None:
    _, s = score_release("no format", 0, 1_000_000, None, now=_NOW)
    assert s == 0


# ---------------------------------------------------------------------------
# Seeder score component
# ---------------------------------------------------------------------------


def test_seeder_score_below_cap() -> None:
    # 10 seeders → min(10,50)*2 = 20; with epub format_score=100 → 120
    _, s = score_release("epub", 10, 1_000_000, None, now=_NOW)
    assert s == 120


def test_seeder_cap_at_50() -> None:
    # min(50,50)*2 = 100; epub 100 → 200
    _, s = score_release("epub", 50, 1_000_000, None, now=_NOW)
    assert s == 200


def test_seeder_above_cap_clamped_to_50() -> None:
    # min(51,50)*2 = 100 — same as exactly 50
    _, s1 = score_release("epub", 50, 1_000_000, None, now=_NOW)
    _, s2 = score_release("epub", 51, 1_000_000, None, now=_NOW)
    assert s1 == s2


def test_zero_seeders() -> None:
    _, s = score_release("epub", 0, 1_000_000, None, now=_NOW)
    assert s == 100  # only format_score


# ---------------------------------------------------------------------------
# Size penalty component
# ---------------------------------------------------------------------------


def test_exactly_100mb_no_penalty() -> None:
    _, s = score_release("epub", 0, 100 * 1024 * 1024, None, now=_NOW)
    assert s == 100


def test_200mb_penalty_50() -> None:
    # (200-100)*0.5 = 50; epub 100 - 50 = 50
    _, s = score_release("epub", 0, 200 * 1024 * 1024, None, now=_NOW)
    assert s == 50


def test_300mb_penalty_100() -> None:
    # (300-100)*0.5 = 100; epub 100 - 100 = 0
    _, s = score_release("epub", 0, 300 * 1024 * 1024, None, now=_NOW)
    assert s == 0


def test_below_100mb_no_penalty() -> None:
    _, s1 = score_release("epub", 0, 50 * 1024 * 1024, None, now=_NOW)
    _, s2 = score_release("epub", 0, 1_000_000, None, now=_NOW)
    assert s1 == s2 == 100


# ---------------------------------------------------------------------------
# Age penalty component
# ---------------------------------------------------------------------------


def test_364_days_no_penalty() -> None:
    pd = _NOW - timedelta(days=364)
    _, s = score_release("epub", 0, 1_000_000, pd, now=_NOW)
    assert s == 100


def test_exactly_365_days_no_penalty() -> None:
    # boundary: >365 triggers penalty, so exactly 365 does NOT
    pd = _NOW - timedelta(days=365)
    _, s = score_release("epub", 0, 1_000_000, pd, now=_NOW)
    assert s == 100


def test_366_days_penalty_10() -> None:
    pd = _NOW - timedelta(days=366)
    _, s = score_release("epub", 0, 1_000_000, pd, now=_NOW)
    assert s == 90


def test_no_publish_date_no_penalty() -> None:
    _, s = score_release("epub", 0, 1_000_000, None, now=_NOW)
    assert s == 100


def test_naive_publish_date_treated_as_utc() -> None:
    pd_naive = datetime(2024, 12, 1)  # naive
    pd_aware = datetime(2024, 12, 1, tzinfo=timezone.utc)
    _, s_naive = score_release("epub", 0, 1_000_000, pd_naive, now=_NOW)
    _, s_aware = score_release("epub", 0, 1_000_000, pd_aware, now=_NOW)
    assert s_naive == s_aware
