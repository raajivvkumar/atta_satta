from datetime import date

from atta_satta.database.sqlite import LotteryRepository
from atta_satta.normalization.models import LotteryDraw, RecordStatus


def test_repository_creates_database_and_persists_draw(tmp_path) -> None:
    repository = LotteryRepository(tmp_path / "atta_satta.sqlite3")
    draw = LotteryDraw(
        game="Example",
        draw_date=date(2026, 8, 23),
        ticket_number="12345",
        status=RecordStatus.VALID,
        source_filename="results.pdf",
        source_page=1,
    )

    assert repository.count() == 0
    assert repository.add_draw(draw) == 1
    assert repository.count() == 1


def test_repository_bulk_insert(tmp_path) -> None:
    repository = LotteryRepository(tmp_path / "atta_satta.sqlite3")
    draws = [
        LotteryDraw("Example", date(2026, 8, 23), "12345"),
        LotteryDraw("Example", date(2026, 8, 24), "67890"),
    ]

    assert repository.add_draws(draws) == 2
    assert repository.count() == 2
