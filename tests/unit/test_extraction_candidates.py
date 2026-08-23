from atta_satta.extraction.candidates import (
    extract_numeric_candidates,
    extract_ticket_candidates,
)


def test_numeric_candidates_are_unique_and_range_limited() -> None:
    text = "Result 12 12 page 99 invalid 1000"
    assert extract_numeric_candidates(text, minimum=0, maximum=99) == ["12", "99"]


def test_ticket_candidates_detect_prefixed_and_numeric_patterns() -> None:
    text = "A123456 B123456 C123457 A-123456 B-123456 C-123456 1234568 1234587 1234659"

    candidates = extract_ticket_candidates(text)

    assert [candidate.value for candidate in candidates] == [
        "A123456",
        "B123456",
        "C123457",
        "A123456",
        "B123456",
        "C123456",
        "1234568",
        "1234587",
        "1234659",
    ]
    assert candidates[0].pattern == "letter_6_digits"
    assert candidates[0].confidence == "high"
    assert candidates[3].raw_value == "A-123456"


def test_ticket_candidates_support_whitespace_and_case_normalization() -> None:
    candidates = extract_ticket_candidates("a 123456 C-123456")

    assert [candidate.value for candidate in candidates] == ["A123456", "C123456"]
    assert candidates[0].raw_value == "a 123456"


def test_ticket_candidates_do_not_match_embedded_numbers() -> None:
    candidates = extract_ticket_candidates("XA1234567 12345678 123456")

    assert candidates == []
