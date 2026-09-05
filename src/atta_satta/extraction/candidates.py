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


@dataclass(frozen=True, slots=True)
class RankedTicketCandidate:
    """A ticket associated with a result rank in the source text."""

    rank: int
    ticket: TicketCandidate


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


_ORDINAL_WORDS = {
    "first": 1,
    "second": 2,
    "third": 3,
    "fourth": 4,
    "fifth": 5,
    "sixth": 6,
    "seventh": 7,
    "eighth": 8,
    "ninth": 9,
    "tenth": 10,
}
_RANK_PATTERN = re.compile(
    r"(?ix)"
    r"(?:\b(?:rank|position|prize|place)\s*[:#-]?\s*(\d{1,2})\b"
    r"|\b(\d{1,2})(?:st|nd|rd|th)\b"
    r"|\b(first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth)"
    r"|\b(\d{1,2})\s*(?:st|nd|rd|th)?\s*(?:prize|place|rank)\b)"
)


def _line_rank(line: str) -> int | None:
    match = _RANK_PATTERN.search(line)
    if not match:
        return None
    if match.group(1) or match.group(2) or match.group(4):
        return int(match.group(1) or match.group(2) or match.group(4))
    return _ORDINAL_WORDS[match.group(3).lower()]


def extract_ranked_ticket_candidates(text: str) -> list[RankedTicketCandidate]:
    """Extract one ticket per result line, excluding prize amounts.

    Explicit labels such as ``1st``, ``Rank 2`` and ``First Prize`` are used
    when present. For unlabeled result lists, candidates retain source order.
    """
    ranked: list[RankedTicketCandidate] = []
    seen: set[str] = set()
    next_rank = 1
    pending_rank: int | None = None

    for line in text.splitlines():
        line_rank = _line_rank(line)
        tickets = extract_ticket_candidates(line)
        if not tickets:
            if line_rank is not None:
                pending_rank = line_rank
            continue
        rank = line_rank if line_rank is not None else pending_rank
        if rank is None:
            rank = next_rank
        pending_rank = None
        next_rank = max(next_rank, rank + 1)
        ticket = tickets[0]
        if ticket.value in seen:
            continue
        seen.add(ticket.value)
        ranked.append(RankedTicketCandidate(rank=rank, ticket=ticket))

    if ranked:
        return sorted(ranked, key=lambda item: (item.rank, item.ticket.start))

    return [
        RankedTicketCandidate(rank=index, ticket=ticket)
        for index, ticket in enumerate(extract_ticket_candidates(text), start=1)
    ]


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
