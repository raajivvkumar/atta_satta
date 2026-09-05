from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from atta_satta.extraction.pdf import extract_pdf_text
from atta_satta.ingestion.files import describe_source_file
from atta_satta.normalization.models import LotteryDraw
from atta_satta.ocr.image import configure_tesseract, ocr_image
from atta_satta.prediction.ranking import rank_candidates
from atta_satta.statistics.analysis import distribution_summary, frequency_table


def test_statistics_and_prediction_pipeline() -> None:
    history = [
        LotteryDraw("Example", date(2026, 1, 1), "1"),
        LotteryDraw("Example", date(2026, 1, 2), "2"),
        LotteryDraw("Example", date(2026, 1, 3), "1"),
        LotteryDraw("Example", date(2026, 1, 4), "3"),
    ]

    summary = distribution_summary(history)
    frequencies = frequency_table(history)
    ranking = rank_candidates(history, minimum=1, maximum=3, candidates=3)

    assert summary.total_records == 4
    assert summary.unique_numbers == 3
    assert frequencies[0].ticket_number == "1"
    assert ranking[0].ticket_number == "1"
    assert ranking[0].confidence == "Unvalidated"


def test_source_hash_is_reproducible(tmp_path: Path) -> None:
    source = tmp_path / "sample.pdf"
    source.write_bytes(b"lottery result")

    first = describe_source_file(source)
    second = describe_source_file(source)

    assert first.sha256 == second.sha256
    assert len(first.sha256) == 64


def test_pdf_extraction_rejects_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        list(extract_pdf_text(tmp_path / "missing.pdf"))


def test_ocr_rejects_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        ocr_image(tmp_path / "missing.png")


def test_ocr_reports_missing_tesseract_executable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pytesseract = pytest.importorskip("pytesseract")
    pil = pytest.importorskip("PIL")
    Image = pil.Image

    source = tmp_path / "sample.png"
    Image.new("RGB", (10, 10), color="white").save(source)

    def raise_missing_executable(*args, **kwargs):
        raise pytesseract.TesseractNotFoundError()

    monkeypatch.setattr(pytesseract, "image_to_string", raise_missing_executable)

    with pytest.raises(RuntimeError, match="Tesseract OCR is unavailable"):
        ocr_image(source)


def test_configure_tesseract_discovers_windows_installation(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    pytesseract = pytest.importorskip("pytesseract")
    executable = tmp_path / "Tesseract-OCR" / "tesseract.exe"
    executable.parent.mkdir()
    executable.write_bytes(b"")
    monkeypatch.setattr("atta_satta.ocr.image.os.name", "nt")
    monkeypatch.setenv("ProgramFiles", str(tmp_path))
    monkeypatch.setattr("atta_satta.ocr.image.shutil.which", lambda _: None)

    configure_tesseract(pytesseract)

    assert pytesseract.pytesseract.tesseract_cmd == str(
        tmp_path / "Tesseract-OCR" / "tesseract.exe"
    )
