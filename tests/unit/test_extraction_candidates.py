from atta_satta.extraction.candidates import extract_numeric_candidates


def test_numeric_candidates_are_unique_and_range_limited() -> None:
    text = "Result 12 12 page 99 invalid 1000"
    assert extract_numeric_candidates(text, minimum=0, maximum=99) == ["12", "99"]
