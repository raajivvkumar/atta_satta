"""Explainable candidate ranking and walk-forward evaluation primitives."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from math import exp
import random

from atta_satta.normalization.models import LotteryDraw


@dataclass(frozen=True, slots=True)
class CandidateScore:
    rank: int
    ticket_number: str
    score: float
    confidence: str
    statistical_score: float
    historical_score: float
    astronomy_score: float
    model_score: float
    supporting_signals: tuple[str, ...]
    contradicting_signals: tuple[str, ...]
    explanation: str


def _confidence(score: float, validated: bool) -> str:
    if not validated:
        return "Unvalidated"
    if score >= 80:
        return "Very High"
    if score >= 65:
        return "High"
    if score >= 50:
        return "Moderate"
    if score >= 35:
        return "Low"
    return "Very Low"


def rank_candidates(
    history: list[LotteryDraw],
    *,
    minimum: int,
    maximum: int,
    candidates: int = 10,
    validated: bool = False,
) -> list[CandidateScore]:
    """Rank a ticket range using historical frequency and recency only.

    This is intentionally a transparent baseline. It does not claim that a
    frequent historical number is more likely to occur in an independent draw.
    """
    if minimum > maximum:
        raise ValueError("minimum must not exceed maximum")
    if candidates < 1:
        raise ValueError("candidates must be positive")

    ordered = sorted(history, key=lambda item: (item.draw_date, item.draw_time or ""))
    counts: dict[str, int] = {}
    last_seen: dict[str, int] = {}
    for index, record in enumerate(ordered):
        counts[record.ticket_number] = counts.get(record.ticket_number, 0) + 1
        last_seen[record.ticket_number] = index

    total = len(ordered)
    max_count = max(counts.values(), default=1)
    scored: list[tuple[str, float, float, float, tuple[str, ...], tuple[str, ...], str]] = []
    for number in range(minimum, maximum + 1):
        ticket = str(number)
        count = counts.get(ticket, 0)
        frequency_score = 100.0 * count / max_count
        if total and ticket in last_seen:
            gap = total - 1 - last_seen[ticket]
            recency_score = 100.0 * exp(-gap / max(1.0, total / 4))
        else:
            gap = total
            recency_score = 0.0

        historical = 0.6 * frequency_score + 0.4 * recency_score
        statistical = frequency_score
        astronomy = 0.0
        model = historical
        score = 0.7 * historical + 0.3 * statistical
        supporting: list[str] = []
        contradicting: list[str] = []
        if count:
            supporting.append(f"observed {count} time(s) historically")
        else:
            contradicting.append("not observed in the supplied history")
        if ticket in last_seen and gap <= max(1, total // 10):
            supporting.append("recently observed relative to this history")
        elif count:
            contradicting.append(f"current gap is {gap} draws")
        explanation = "; ".join(supporting or contradicting)
        scored.append((ticket, score, statistical, historical, tuple(supporting), tuple(contradicting), explanation))

    scored.sort(key=lambda item: (-item[1], int(item[0])))
    return [
        CandidateScore(
            rank=index,
            ticket_number=item[0],
            score=round(item[1], 2),
            confidence=_confidence(item[1], validated),
            statistical_score=round(item[2], 2),
            historical_score=round(item[3], 2),
            astronomy_score=0.0,
            model_score=round(item[3], 2),
            supporting_signals=item[4],
            contradicting_signals=item[5],
            explanation=item[6],
        )
        for index, item in enumerate(scored[:candidates], start=1)
    ]


def random_ranking(
    *, minimum: int, maximum: int, candidates: int, seed: int = 42
) -> list[str]:
    """Return a reproducible random candidate sample for baseline comparison."""
    values = [str(number) for number in range(minimum, maximum + 1)]
    rng = random.Random(seed)
    rng.shuffle(values)
    return values[: min(candidates, len(values))]
