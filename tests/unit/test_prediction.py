from datetime import date, timedelta

from atta_satta.normalization.models import LotteryDraw
from atta_satta.prediction.ranking import rank_candidates


def test_ranking_is_deterministic() -> None:
    records = [
        LotteryDraw("Example", date(2026, 1, 1) + timedelta(days=i), value)
        for i, value in enumerate(["1", "2", "1", "3"])
    ]
    first = rank_candidates(records, minimum=1, maximum=3, candidates=3)
    second = rank_candidates(records, minimum=1, maximum=3, candidates=3)
    assert first == second
    assert first[0].ticket_number == "1"


def test_unvalidated_rankings_are_not_high_confidence() -> None:
    ranked = rank_candidates([], minimum=1, maximum=3, candidates=3)
    assert all(item.confidence == "Unvalidated" for item in ranked)
