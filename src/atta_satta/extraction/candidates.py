"""Conservative candidate extraction from OCR/PDF text."""

from __future__ import annotations

import re


def extract_numeric_candidates(text: str, *, minimum: int, maximum: int) -> list[str]:
    """Extract numeric tokens in a configured range for human review.

    This function does not decide which token is the lottery result. Dates,
    page numbers and other document numbers may also match and therefore must
    remain reviewable before import.
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
