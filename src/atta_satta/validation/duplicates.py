"""Duplicate detection for normalized historical records."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable

from atta_satta.normalization.models import LotteryDraw


def duplicate_groups(records: Iterable[LotteryDraw]) -> list[list[LotteryDraw]]:
    """Group exact logical duplicates without deleting or mutating records.

    A duplicate key uses the game, draw date, draw time and ticket number. Source
    provenance is intentionally excluded so the same result appearing in several
    source documents can be identified for review.
    """
    groups: dict[tuple[str, object, str | None, str], list[LotteryDraw]] = defaultdict(list)
    for record in records:
        key = (record.game, record.draw_date, record.draw_time, record.ticket_number)
        groups[key].append(record)

    return [group for group in groups.values() if len(group) > 1]
