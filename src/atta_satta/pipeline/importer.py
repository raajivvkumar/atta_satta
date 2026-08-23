"""Conservative import orchestration for extracted lottery records."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path

from atta_satta.database.sqlite import LotteryRepository
from atta_satta.ingestion.files import describe_source_file
from atta_satta.normalization.models import LotteryDraw, RecordStatus
from atta_satta.normalization.text import normalize_ticket_number
from atta_satta.validation.results import ValidationStatus, validate_ticket_number


@dataclass(frozen=True, slots=True)
class ImportCandidate:
    """A parsed candidate before it is persisted."""

    game: str
    draw_date: date
    ticket_number: str
    source_path: Path
    source_page: int | None = None
    extraction_method: str = "unknown"
    extraction_confidence: float | None = None
    original_text: str | None = None


def prepare_candidate(
    candidate: ImportCandidate,
    *,
    minimum_ticket: int,
    maximum_ticket: int,
) -> LotteryDraw:
    """Normalize and validate a candidate while preserving questionable values."""
    source = describe_source_file(candidate.source_path)
    ticket = normalize_ticket_number(candidate.ticket_number)
    validation = validate_ticket_number(
        ticket,
        minimum=minimum_ticket,
        maximum=maximum_ticket,
    )

    status_map = {
        ValidationStatus.VALID: RecordStatus.VALID,
        ValidationStatus.REVIEW: RecordStatus.REVIEW,
        ValidationStatus.INVALID: RecordStatus.INVALID,
    }

    return LotteryDraw(
        game=candidate.game,
        draw_date=candidate.draw_date,
        ticket_number=ticket,
        source_filename=source.filename,
        source_sha256=source.sha256,
        source_page=candidate.source_page,
        extraction_method=candidate.extraction_method,
        extraction_confidence=candidate.extraction_confidence,
        original_text=candidate.original_text,
        status=status_map[validation.status],
        imported_at=datetime.now(UTC),
    )


def import_candidates(
    repository: LotteryRepository,
    candidates: list[ImportCandidate],
    *,
    minimum_ticket: int,
    maximum_ticket: int,
) -> int:
    """Prepare and persist candidates as one transaction.

    No candidate is silently discarded. Invalid and review-required records are
    persisted with their status so a later review workflow can correct them.
    """
    draws = [
        prepare_candidate(
            candidate,
            minimum_ticket=minimum_ticket,
            maximum_ticket=maximum_ticket,
        )
        for candidate in candidates
    ]
    return repository.add_draws(draws)
