"""Time-aware model comparison for the MVP.

The comparison is intentionally conservative: models that cannot be validated
from the available data are reported as unavailable rather than assigned an
invented score.
"""

from __future__ import annotations

from dataclasses import dataclass

from atta_satta.normalization.models import LotteryDraw
from atta_satta.prediction.ranking import random_ranking, rank_candidates


@dataclass(frozen=True, slots=True)
class ModelResult:
    name: str
    status: str
    predictions: int
    top_k_hits: int
    top_k_hit_rate: float
    note: str


def compare_models(
    records: list[LotteryDraw],
    *,
    minimum: int,
    maximum: int,
    top_k: int = 10,
    minimum_history: int = 20,
) -> list[ModelResult]:
    """Compare random and historical baselines using walk-forward validation.

    Astronomy and ML models are only marked available once enough timestamped
    data and model-ready features exist. This prevents false precision in an MVP.
    """
    ordered = sorted(records, key=lambda item: (item.draw_date, item.draw_time or ""))
    historical_hits = 0
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
        )
        random_candidates = random_ranking(
            minimum=minimum,
            maximum=maximum,
            candidates=top_k,
            seed=index,
        )
        historical_hits += target in {item.ticket_number for item in ranked}
        random_hits += target in random_candidates
        predictions += 1

    historical_rate = historical_hits / predictions if predictions else 0.0
    random_rate = random_hits / predictions if predictions else 0.0
    astronomy_ready = sum(1 for record in ordered if record.draw_time) >= minimum_history
    ml_ready = len(ordered) >= max(100, minimum_history)

    return [
        ModelResult(
            "Random baseline",
            "validated" if predictions else "insufficient_data",
            predictions,
            random_hits,
            random_rate,
            "Reproducible random ranking baseline.",
        ),
        ModelResult(
            "Frequency/recency baseline",
            "validated" if predictions else "insufficient_data",
            predictions,
            historical_hits,
            historical_rate,
            "Historical features only; temporal walk-forward evaluation.",
        ),
        ModelResult(
            "Statistical model",
            "available_for_extension",
            0,
            0,
            0.0,
            (
                "Descriptive statistics are implemented; inferential model selection "
                "requires a configured lottery schema."
            ),
        ),
        ModelResult(
            "Historical-feature ML",
            "ready" if ml_ready else "insufficient_data",
            0,
            0,
            0.0,
            "Requires at least 100 chronologically ordered observations for the MVP ML experiment.",
        ),
        ModelResult(
            "Astronomy-feature model",
            "ready_for_experiment" if astronomy_ready else "insufficient_timestamp_data",
            0,
            0,
            0.0,
            (
                "Astronomy is experimental and must demonstrate out-of-sample "
                "improvement before contributing to ranking."
            ),
        ),
        ModelResult(
            "Combined model",
            "not_enabled_until_validated",
            0,
            0,
            0.0,
            (
                "Combined weights must be learned/validated; no unvalidated astronomy "
                "contribution is applied."
            ),
        ),
    ]
