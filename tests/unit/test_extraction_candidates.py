from atta_satta.extraction.candidates import (
    extract_numeric_candidates,
    extract_ticket_candidates,
)


def test_numeric_candidates_are_unique_and_range_limited() -> None:
    text = "Result 12 12 page 99 invalid 1000"
    assert extract_numeric_candidates(text, minimum=0, maximum=99) == ["12", "99"]


def test_numeric_candidates_ignore_dates_times_pages_and_embedded_ids() -> None:
    text = "Date 2026-08-23 time 10:30 Page 1 of 2 IDA12 result 47 88"

    assert extract_numeric_candidates(text, minimum=0, maximum=99) == ["47", "88"]


def test_numeric_candidates_can_require_fixed_width() -> None:
    text = "page 2 values 123 1234568 7654321"

    assert extract_numeric_candidates(
        text,
        minimum=0,
        maximum=9_999_999,
        fixed_width=7,
    ) == ["1234568", "7654321"]


def test_ticket_candidates_detect_prefixed_and_numeric_patterns() -> None:
    text = "A123456 B123456 C123457 A-123456 B-123456 C-123456 1234568 1234587 1234659"

    candidates = extract_ticket_candidates(text)

    assert [candidate.value for candidate in candidates] == [
        "A123456",
        "B123456",
        "C123457",
        "C123456",
        "1234568",
        "1234587",
        "1234659",
    ]
    assert candidates[0].pattern == "letter_6_digits"
    assert candidates[0].confidence == "high"
    assert candidates[3].raw_value == "C-123456"


def test_ticket_candidates_support_whitespace_and_case_normalization() -> None:
    candidates = extract_ticket_candidates("a 123456 C-123456")

    assert [candidate.value for candidate in candidates] == ["A123456", "C123456"]
    assert candidates[0].raw_value == "a 123456"


def test_ticket_candidates_do_not_match_embedded_numbers() -> None:
    candidates = extract_ticket_candidates("XA1234567 12345678 123456")

    assert candidates == []
