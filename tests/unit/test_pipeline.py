from datetime import date

from atta_satta.database.sqlite import LotteryRepository
from atta_satta.pipeline.importer import ImportCandidate, import_candidates, prepare_candidate
from atta_satta.normalization.models import RecordStatus


def test_prepare_candidate_preserves_source_and_validation(tmp_path) -> None:
    source = tmp_path / "results.pdf"
    source.write_bytes(b"source")

    draw = prepare_candidate(
        ImportCandidate(
            game="Example",
            draw_date=date(2026, 8, 23),
            ticket_number="123",
            source_path=source,
            source_page=2,
            extraction_method="pdf_text",
            extraction_confidence=99.0,
            original_text="123",
        ),
        minimum_ticket=0,
        maximum_ticket=999,
    )

    assert draw.ticket_number == "123"
    assert draw.status is RecordStatus.VALID
    assert draw.source_filename == "results.pdf"
    assert draw.source_page == 2
    assert draw.source_sha256 is not None


def test_invalid_candidates_are_stored_for_review(tmp_path) -> None:
    source = tmp_path / "results.pdf"
    source.write_bytes(b"source")
    repository = LotteryRepository(tmp_path / "db.sqlite3")

    count = import_candidates(
        repository,
        [
            ImportCandidate(
                game="Example",
                draw_date=date(2026, 8, 23),
                ticket_number="OCR-ERROR",
                source_path=source,
            )
        ],
        minimum_ticket=0,
        maximum_ticket=999,
    )

    assert count == 1
    assert repository.count() == 1
