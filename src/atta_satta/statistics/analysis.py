"""Descriptive and inferential statistics for lottery histories."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from math import sqrt
from statistics import mean

from atta_satta.normalization.models import LotteryDraw


@dataclass(frozen=True, slots=True)
class NumberStatistic:
    ticket_number: str
    count: int
    frequency: float
    gap: int


@dataclass(frozen=True, slots=True)
class DistributionSummary:
    total_records: int
    unique_numbers: int
    min_number: int | None
    max_number: int | None
    mean_number: float | None
    std_number: float | None


def frequency_table(records: list[LotteryDraw]) -> list[NumberStatistic]:
    """Return frequency and current gap for each observed ticket number."""
    if not records:
        return []
    ordered = sorted(records, key=lambda item: (item.draw_date, item.draw_time or ""))
    counts = Counter(record.ticket_number for record in ordered)
    last_seen: dict[str, int] = {}
    for index, record in enumerate(ordered):
        last_seen[record.ticket_number] = index
    total = len(ordered)
    return sorted(
        (
            NumberStatistic(
                ticket_number=number,
                count=count,
                frequency=count / total,
                gap=total - 1 - last_seen[number],
            )
            for number, count in counts.items()
        ),
        key=lambda item: (-item.count, item.gap, item.ticket_number),
    )


def distribution_summary(records: list[LotteryDraw]) -> DistributionSummary:
    numbers = [int(record.ticket_number) for record in records if record.ticket_number.isdigit()]
    if not numbers:
        return DistributionSummary(len(records), 0, None, None, None, None)
    average = mean(numbers)
    variance = mean((value - average) ** 2 for value in numbers)
    return DistributionSummary(
        total_records=len(records),
        unique_numbers=len(set(numbers)),
        min_number=min(numbers),
        max_number=max(numbers),
        mean_number=average,
        std_number=sqrt(variance),
    )


def autocorrelation(records: list[LotteryDraw], lag: int = 1) -> float | None:
    """Pearson autocorrelation for numeric ticket values at a given lag."""
    values = [int(record.ticket_number) for record in records if record.ticket_number.isdigit()]
    if lag < 1 or len(values) <= lag:
        return None
    x = values[:-lag]
    y = values[lag:]
    mx, my = mean(x), mean(y)
    numerator = sum((a - mx) * (b - my) for a, b in zip(x, y, strict=True))
    denominator = sqrt(sum((a - mx) ** 2 for a in x) * sum((b - my) ** 2 for b in y))
    return numerator / denominator if denominator else None
