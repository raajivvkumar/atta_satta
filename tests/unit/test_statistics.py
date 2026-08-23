from datetime import date, timedelta

from atta_satta.normalization.models import LotteryDraw
from atta_satta.statistics.analysis import autocorrelation, distribution_summary, frequency_table


def _records() -> list[LotteryDraw]:
    start = date(2026, 1, 1)
    return [
        LotteryDraw("Example", start + timedelta(days=i), value)
        for i, value in enumerate(["1", "2", "1", "3"])
    ]


def test_frequency_table_counts_and_gaps() -> None:
    table = frequency_table(_records())
    assert table[0].ticket_number == "1"
    assert table[0].count == 2
    assert table[0].gap == 1


def test_distribution_summary() -> None:
    summary = distribution_summary(_records())
    assert summary.total_records == 4
    assert summary.unique_numbers == 3
    assert summary.min_number == 1
    assert summary.max_number == 3


def test_autocorrelation_returns_value() -> None:
    result = autocorrelation(_records())
    assert result is not None
    assert -1 <= result <= 1
