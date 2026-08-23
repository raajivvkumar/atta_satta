from atta_satta.validation.results import ValidationStatus, validate_ticket_number


def test_valid_ticket_number() -> None:
    result = validate_ticket_number("123", minimum=0, maximum=999)

    assert result.status is ValidationStatus.VALID


def test_structured_ticket_number_is_valid() -> None:
    result = validate_ticket_number("A123456", minimum=0, maximum=999999)

    assert result.status is ValidationStatus.VALID
    assert result.value == "A123456"


def test_structured_ticket_numeric_portion_is_range_checked() -> None:
    result = validate_ticket_number("B123456", minimum=0, maximum=99999)

    assert result.status is ValidationStatus.INVALID


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
