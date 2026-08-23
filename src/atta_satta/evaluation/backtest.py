"""Leakage-safe walk-forward backtesting."""

from __future__ import annotations

from dataclasses import dataclass

from atta_satta.normalization.models import LotteryDraw
from atta_satta.prediction.ranking import random_ranking, rank_candidates


@dataclass(frozen=True, slots=True)
class BacktestResult:
    strategy: str
    predictions: int
    hits: int
    top_k: int
    hit_rate: float
    random_hit_rate: float
    lift_vs_random: float


def walk_forward_backtest(
    records: list[LotteryDraw],
    *,
    minimum: int,
    maximum: int,
    top_k: int = 10,
    minimum_history: int = 20,
) -> BacktestResult:
    """Evaluate the historical baseline without using the target draw itself."""
    ordered = sorted(records, key=lambda item: (item.draw_date, item.draw_time or ""))
    hits = 0
    random_hits = 0
    predictions = 0
    for index in range(minimum_history, len(ordered)):
        history = ordered[:index]
        target = ordered[index].ticket_number
        ranked = rank_candidates(
            history,
            minimum=minimum,
            maximum=maximum,
            candidates=top_k,
            validated=False,
        )
        random_candidates = random_ranking(
            minimum=minimum,
            maximum=maximum,
            candidates=top_k,
            seed=index,
        )
        hits += target in {item.ticket_number for item in ranked}
        random_hits += target in random_candidates
        predictions += 1

    hit_rate = hits / predictions if predictions else 0.0
    random_rate = random_hits / predictions if predictions else 0.0
    return BacktestResult(
        strategy="historical_frequency_recency",
        predictions=predictions,
        hits=hits,
        top_k=top_k,
        hit_rate=hit_rate,
        random_hit_rate=random_rate,
        lift_vs_random=(hit_rate / random_rate if random_rate else float("inf")),
    )
