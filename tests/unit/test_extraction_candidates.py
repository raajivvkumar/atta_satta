from atta_satta.extraction.candidates import (
    extract_numeric_candidates,
    extract_ranked_ticket_candidates,
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


def test_ranked_candidates_use_result_labels_and_ignore_amounts() -> None:
    text = """
    1st Prize: A123456 Amount: 50000
    Second Prize - B123457 Rs. 25000
    Rank 3: 1234568 10000
    """

    candidates = extract_ranked_ticket_candidates(text)

    assert [(item.rank, item.ticket.value) for item in candidates] == [
        (1, "A123456"),
        (2, "B123457"),
        (3, "1234568"),
    ]


def test_ranked_candidates_fall_back_to_source_order() -> None:
    candidates = extract_ranked_ticket_candidates("A123456\nB123457\n1234568")

    assert [(item.rank, item.ticket.value) for item in candidates] == [
        (1, "A123456"),
        (2, "B123457"),
        (3, "1234568"),
    ]


def test_ranked_candidates_allow_rank_and_ticket_on_adjacent_lines() -> None:
    candidates = extract_ranked_ticket_candidates(
        "1st Prize\nA123456\n2nd Prize\nB123457"
    )

    assert [(item.rank, item.ticket.value) for item in candidates] == [
        (1, "A123456"),
        (2, "B123457"),
    ]
