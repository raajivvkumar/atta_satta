"""Conservative normalization helpers for extracted lottery text."""

from __future__ import annotations

import re

_WHITESPACE = re.compile(r"\s+")


def normalize_text(value: str) -> str:
    """Normalize whitespace without altering potentially meaningful characters."""
    return _WHITESPACE.sub(" ", value).strip()


def normalize_ticket_number(value: str) -> str:
    """Normalize a ticket value without guessing OCR substitutions.

    OCR corrections such as O->0 are deliberately excluded. Such corrections
    require validation context and should remain reviewable rather than being
    silently introduced into historical data.
    """
    normalized = normalize_text(value)
    return normalized
