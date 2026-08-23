"""Validation models for extracted lottery results."""

from __future__ import annotations

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


def validate_ticket_number(value: str, *, minimum: int, maximum: int) -> ValidationResult:
    """Validate a numeric ticket value without correcting OCR silently."""
    normalized = value.strip()
    if not normalized:
        return ValidationResult(normalized, ValidationStatus.REVIEW, "empty value")

    if not normalized.isdigit():
        return ValidationResult(normalized, ValidationStatus.REVIEW, "non-numeric value")

    number = int(normalized)
    if not minimum <= number <= maximum:
        return ValidationResult(
            normalized,
            ValidationStatus.INVALID,
            f"value outside allowed range {minimum}..{maximum}",
        )

    return ValidationResult(normalized, ValidationStatus.VALID, "within configured range")
