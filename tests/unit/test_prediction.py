from datetime import date, timedelta

import pytest

from atta_satta.normalization.models import LotteryDraw
from atta_satta.prediction.ranking import random_ranking, rank_candidates


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
    assert ranked[0].contradicting_signals == ("not observed in the supplied history",)


def test_validated_confidence_uses_measured_score_bands() -> None:
    records = [LotteryDraw("Example", date(2026, 1, 1), "1")]
    ranked = rank_candidates(records, minimum=1, maximum=1, validated=True)
    assert ranked[0].confidence == "Very High"
    assert ranked[0].supporting_signals


def test_rank_candidates_rejects_invalid_arguments() -> None:
    with pytest.raises(ValueError, match="minimum"):
        rank_candidates([], minimum=2, maximum=1)
    with pytest.raises(ValueError, match="candidates"):
        rank_candidates([], minimum=1, maximum=2, candidates=0)


def test_random_ranking_is_reproducible_and_bounded() -> None:
    first = random_ranking(minimum=1, maximum=5, candidates=3, seed=7)
    second = random_ranking(minimum=1, maximum=5, candidates=3, seed=7)
    assert first == second
    assert len(first) == 3
    assert len(set(first)) == 3
    assert set(first).issubset({"1", "2", "3", "4", "5"})
