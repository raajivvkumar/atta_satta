"""Canonical domain models for historical lottery results."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum


class RecordStatus(StrEnum):
    """Lifecycle state of a normalized historical record."""

    VALID = "valid"
    REVIEW = "review"
    INVALID = "invalid"


@dataclass(frozen=True, slots=True)
class LotteryDraw:
    """A normalized lottery draw independent of any extraction format."""

    game: str
    draw_date: date
    ticket_number: str
    draw_time: str | None = None
    timezone: str | None = None
    source_filename: str | None = None
    source_sha256: str | None = None
    source_page: int | None = None
    extraction_method: str | None = None
    extraction_confidence: float | None = None
    original_text: str | None = None
    status: RecordStatus = RecordStatus.REVIEW
    imported_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.game.strip():
            raise ValueError("game must not be empty")
        if not self.ticket_number.strip():
            raise ValueError("ticket_number must not be empty")
        if self.source_page is not None and self.source_page < 1:
            raise ValueError("source_page must be >= 1")
        if self.extraction_confidence is not None and not 0 <= self.extraction_confidence <= 100:
            raise ValueError("extraction_confidence must be between 0 and 100")
