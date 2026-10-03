"""Conservative import orchestration for extracted lottery records."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path

from atta_satta.database.sqlite import LotteryRepository
from atta_satta.extraction.candidates import (
    extract_numeric_candidates,
    extract_ticket_candidates,
)
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


def _range_width(minimum_ticket: int, maximum_ticket: int) -> int | None:
    """Use an exact numeric width for large ranges to avoid short metadata values."""
    if minimum_ticket < 0 or maximum_ticket < 0:
        return None
    if maximum_ticket < 10_000:
        return None
    return len(str(maximum_ticket))


def extract_import_candidates(
    text: str,
    *,
    game: str,
    draw_date: date,
    source_path: Path,
    source_page: int | None = None,
    extraction_method: str = "unknown",
    extraction_confidence: float | None = None,
    minimum_ticket: int | None = None,
    maximum_ticket: int | None = None,
) -> list[ImportCandidate]:
    """Convert detected ticket patterns into import-ready candidates.

    Structured ticket detection remains the first signal. When a configured
    numeric range is supplied, standalone numeric values in that range are also
    detected. This is required for games whose actual results are values such
    as 0..99 instead of seven-digit ticket identifiers.

    Detection is deliberately separate from validation. Every detected ticket
    is retained with its raw source text so callers can review it before commit.
    """
    candidates: list[ImportCandidate] = []
    seen: set[str] = set()

    for detected in extract_ticket_candidates(text):
        seen.add(detected.value)
        candidates.append(
            ImportCandidate(
                game=game,
                draw_date=draw_date,
                ticket_number=detected.value,
                source_path=source_path,
                source_page=source_page,
                extraction_method=extraction_method,
                extraction_confidence=extraction_confidence,
                original_text=detected.raw_value,
            )
        )

    if minimum_ticket is not None and maximum_ticket is not None:
        numeric_values = extract_numeric_candidates(
            text,
            minimum=minimum_ticket,
            maximum=maximum_ticket,
            fixed_width=_range_width(minimum_ticket, maximum_ticket),
        )
        for value in numeric_values:
            if value in seen:
                continue
            seen.add(value)
            candidates.append(
                ImportCandidate(
                    game=game,
                    draw_date=draw_date,
                    ticket_number=value,
                    source_path=source_path,
                    source_page=source_page,
                    extraction_method=extraction_method,
                    extraction_confidence=extraction_confidence,
                    original_text=value,
                )
            )

    return candidates


def import_extracted_text(
    repository: LotteryRepository,
    text: str,
    *,
    game: str,
    draw_date: date,
    source_path: Path,
    minimum_ticket: int,
    maximum_ticket: int,
    source_page: int | None = None,
    extraction_method: str = "unknown",
    extraction_confidence: float | None = None,
) -> int:
    """Extract ticket patterns from text, validate them, and persist them."""
    candidates = extract_import_candidates(
        text,
        game=game,
        draw_date=draw_date,
        source_path=source_path,
        source_page=source_page,
        extraction_method=extraction_method,
        extraction_confidence=extraction_confidence,
        minimum_ticket=minimum_ticket,
        maximum_ticket=maximum_ticket,
    )
    return import_candidates(
        repository,
        candidates,
        minimum_ticket=minimum_ticket,
        maximum_ticket=maximum_ticket,
    )
