from datetime import date, timedelta

from atta_satta.evaluation.backtest import walk_forward_backtest
from atta_satta.normalization.models import LotteryDraw


def test_walk_forward_uses_only_prior_records() -> None:
    records = [
        LotteryDraw("Example", date(2026, 1, 1) + timedelta(days=i), value)
        for i, value in enumerate(["1", "2", "1", "2", "1", "2"])
    ]
    result = walk_forward_backtest(
        records,
        minimum=1,
        maximum=2,
        top_k=1,
        minimum_history=2,
    )
    assert result.predictions == 4
    assert 0 <= result.hit_rate <= 1
    assert 0 <= result.random_hit_rate <= 1
