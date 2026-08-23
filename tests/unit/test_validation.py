from atta_satta.validation.results import ValidationStatus, validate_ticket_number


def test_valid_ticket_number() -> None:
    result = validate_ticket_number("123", minimum=0, maximum=999)

    assert result.status is ValidationStatus.VALID


def test_non_numeric_value_requires_review() -> None:
    result = validate_ticket_number("12O", minimum=0, maximum=999)

    assert result.status is ValidationStatus.REVIEW
    assert "non-numeric" in result.reason


def test_out_of_range_value_is_invalid() -> None:
    result = validate_ticket_number("1000", minimum=0, maximum=999)

    assert result.status is ValidationStatus.INVALID


def test_empty_value_requires_review() -> None:
    result = validate_ticket_number("   ", minimum=0, maximum=999)

    assert result.status is ValidationStatus.REVIEW
