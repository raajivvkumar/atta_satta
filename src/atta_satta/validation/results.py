"""Validation models for extracted lottery results."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum


class ValidationStatus(StrEnum):
    """Review status for an extracted result."""

    VALID = "valid"
    REVIEW = "review"
    INVALID = "invalid"


@dataclass(frozen=True, slots=True)
class ValidationResult:
    """Result of validating a candidate lottery number."""

    value: str
    status: ValidationStatus
    reason: str


_STRUCTURED_TICKET = re.compile(r"^[A-Z]\d{6}$")


def validate_ticket_number(value: str, *, minimum: int, maximum: int) -> ValidationResult:
    """Validate numeric or structured ticket values without OCR guessing.

    Supported structured tickets use one letter followed by six digits, for
    example ``A123456``. The configured numeric range is applied to the digit
    portion so prefixed and seven-digit tickets can share the same validator.
    """
    normalized = value.strip().upper()
    if not normalized:
        return ValidationResult(normalized, ValidationStatus.REVIEW, "empty value")

    if _STRUCTURED_TICKET.fullmatch(normalized):
        number = int(normalized[1:])
        if not minimum <= number <= maximum:
            return ValidationResult(
                normalized,
                ValidationStatus.INVALID,
                f"numeric portion outside configured range {minimum}..{maximum}",
            )
        return ValidationResult(
            normalized,
            ValidationStatus.VALID,
            "structured ticket format with numeric portion in range",
        )

    if not normalized.isdigit():
        return ValidationResult(normalized, ValidationStatus.REVIEW, "non-numeric or malformed ticket")

    number = int(normalized)
    if not minimum <= number <= maximum:
        return ValidationResult(
            normalized,
            ValidationStatus.INVALID,
            f"value outside allowed range {minimum}..{maximum}",
        )

    return ValidationResult(normalized, ValidationStatus.VALID, "within configured range")
