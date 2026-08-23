from datetime import date

import pytest

from atta_satta.normalization.models import LotteryDraw, RecordStatus
from atta_satta.normalization.text import normalize_text, normalize_ticket_number


def test_normalize_text_collapses_whitespace() -> None:
    assert normalize_text("  12\n  34\t") == "12 34"


def test_ticket_normalization_does_not_guess_ocr() -> None:
    assert normalize_ticket_number("12O") == "12O"


def test_lottery_draw_preserves_provenance() -> None:
    draw = LotteryDraw(
        game="Example Lottery",
        draw_date=date(2026, 8, 23),
        ticket_number="12345",
        source_filename="results.pdf",
        source_sha256="a" * 64,
        source_page=2,
        extraction_method="pdf_text",
        extraction_confidence=98.5,
        status=RecordStatus.VALID,
    )

    assert draw.game == "Example Lottery"
    assert draw.source_page == 2
    assert draw.status is RecordStatus.VALID


def test_lottery_draw_rejects_invalid_page() -> None:
    with pytest.raises(ValueError, match="source_page"):
        LotteryDraw(
            game="Example Lottery",
            draw_date=date(2026, 8, 23),
            ticket_number="12345",
            source_page=0,
        )


def test_lottery_draw_rejects_invalid_confidence() -> None:
    with pytest.raises(ValueError, match="extraction_confidence"):
        LotteryDraw(
            game="Example Lottery",
            draw_date=date(2026, 8, 23),
            ticket_number="12345",
            extraction_confidence=101,
        )
