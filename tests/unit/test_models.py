from datetime import date, timedelta

from atta_satta.models.comparison import compare_models
from atta_satta.normalization.models import LotteryDraw


def test_model_comparison_reports_baselines() -> None:
    records = [
        LotteryDraw("Example", date(2026, 1, 1) + timedelta(days=i), str((i % 3) + 1))
        for i in range(25)
    ]
    results = compare_models(records, minimum=1, maximum=3, top_k=1, minimum_history=20)
    names = {result.name for result in results}
    assert "Random baseline" in names
    assert "Frequency/recency baseline" in names
    assert len(results) == 6
