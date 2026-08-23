from datetime import date

from atta_satta.normalization.models import LotteryDraw
from atta_satta.validation.duplicates import duplicate_groups


def test_duplicate_groups_identify_same_logical_result() -> None:
    records = [
        LotteryDraw("Example", date(2026, 8, 23), "123"),
        LotteryDraw("Example", date(2026, 8, 23), "123", source_filename="copy.pdf"),
        LotteryDraw("Example", date(2026, 8, 23), "456"),
    ]

    groups = duplicate_groups(records)

    assert len(groups) == 1
    assert len(groups[0]) == 2


def test_duplicate_detection_does_not_delete_records() -> None:
    records = [
        LotteryDraw("Example", date(2026, 8, 23), "123"),
        LotteryDraw("Example", date(2026, 8, 23), "123"),
    ]

    duplicate_groups(records)

    assert len(records) == 2
