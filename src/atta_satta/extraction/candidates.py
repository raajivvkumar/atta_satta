"""Conservative lottery ticket candidate extraction from source text."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TicketCandidate:
    """A detected ticket candidate retained for human validation."""

    value: str
    raw_value: str
    pattern: str
    confidence: str
    start: int
    end: int


# Explicit patterns are deliberately conservative. A numeric ticket is only
# recognized when it contains exactly seven digits; prefixed tickets contain
# one letter and exactly six digits, optionally separated by - or whitespace.
# Numeric tickets must not be embedded in an alphanumeric token such as
# ``XA1234567`` because that is not a standalone ticket representation.
_TICKET_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "letter_6_digits",
        re.compile(r"(?<![A-Za-z0-9])([A-Za-z])\s*-?\s*(\d{6})(?!\d)"),
    ),
    (
        "numeric_7_digits",
        re.compile(r"(?<![A-Za-z0-9])(\d{7})(?![A-Za-z0-9])"),
    ),
)


def _normalize_prefixed(letter: str, digits: str) -> str:
    return f"{letter.upper()}{digits}"


def extract_ticket_candidates(text: str) -> list[TicketCandidate]:
    """Extract common ticket-number patterns without silently selecting winners.

    Supported examples include ``A123456``, ``A-123456``, ``A 123456`` and
    seven-digit numeric tickets such as ``1234568``. Matches are deduplicated
    by normalized value while retaining the first source occurrence.
    """
    candidates: list[TicketCandidate] = []
    seen: set[str] = set()
    matches: list[tuple[int, TicketCandidate]] = []

    for pattern_name, pattern in _TICKET_PATTERNS:
        for match in pattern.finditer(text):
            raw = match.group(0)
            if pattern_name == "letter_6_digits":
                value = _normalize_prefixed(match.group(1), match.group(2))
                confidence = "high"
            else:
                value = match.group(1)
                confidence = "high"
            candidate = TicketCandidate(
                value=value,
                raw_value=raw,
                pattern=pattern_name,
                confidence=confidence,
                start=match.start(),
                end=match.end(),
            )
            if value not in seen:
                seen.add(value)
                matches.append((match.start(), candidate))

    matches.sort(key=lambda item: item[0])
    candidates.extend(candidate for _, candidate in matches)
    return candidates


def extract_numeric_candidates(text: str, *, minimum: int, maximum: int) -> list[str]:
    """Extract numeric tokens in a configured range for human review.

    This legacy/general-purpose extractor remains intentionally separate from
    structured ticket detection because dates, page numbers and other document
    numbers may also match.
    """
    if minimum > maximum:
        raise ValueError("minimum must not exceed maximum")
    candidates: list[str] = []
    seen: set[str] = set()
    for token in re.findall(r"(?<!\d)\d+(?!\d)", text):
        number = int(token)
        if minimum <= number <= maximum and token not in seen:
            seen.add(token)
            candidates.append(token)
    return candidates
