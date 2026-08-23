from datetime import date

from atta_satta.database.queries import LotteryReader
from atta_satta.database.sqlite import LotteryRepository
from atta_satta.normalization.models import RecordStatus
from atta_satta.pipeline.importer import (
    ImportCandidate,
    extract_import_candidates,
    import_candidates,
    import_extracted_text,
    prepare_candidate,
)


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


def test_extract_import_candidates_maps_detected_tickets(tmp_path) -> None:
    source = tmp_path / "results.pdf"
    source.write_bytes(b"source")

    candidates = extract_import_candidates(
        "A123456 B-123457 1234568",
        game="Example",
        draw_date=date(2026, 8, 23),
        source_path=source,
        source_page=3,
        extraction_method="pdf_text",
    )

    assert [candidate.ticket_number for candidate in candidates] == [
        "A123456",
        "B123457",
        "1234568",
    ]
    assert all(candidate.source_page == 3 for candidate in candidates)


def test_import_extracted_text_persists_detected_tickets(tmp_path) -> None:
    source = tmp_path / "results.pdf"
    source.write_bytes(b"source")
    database = tmp_path / "db.sqlite3"
    repository = LotteryRepository(database)

    count = import_extracted_text(
        repository,
        "A123456 A-123456 1234568",
        game="Example",
        draw_date=date(2026, 8, 23),
        source_path=source,
        source_page=1,
        extraction_method="pdf_text",
        minimum_ticket=0,
        maximum_ticket=9999999,
    )

    assert count == 2
    records = LotteryReader(database).records()
    assert [record.ticket_number for record in records] == ["A123456", "1234568"]
    assert all(record.status is RecordStatus.VALID for record in records)
