from pathlib import Path

import pytest

from atta_satta.ingestion.files import describe_source_file, fingerprint_file


def test_fingerprint_is_deterministic(tmp_path: Path) -> None:
    source = tmp_path / "results.txt"
    source.write_text("lottery results", encoding="utf-8")

    assert fingerprint_file(source) == fingerprint_file(source)


def test_describe_source_file_preserves_provenance(tmp_path: Path) -> None:
    source = tmp_path / "results.pdf"
    source.write_bytes(b"test pdf bytes")

    metadata = describe_source_file(source)

    assert metadata.filename == "results.pdf"
    assert metadata.size_bytes == len(b"test pdf bytes")
    assert len(metadata.sha256) == 64
    assert metadata.imported_at.tzinfo is not None


def test_unsupported_source_is_rejected(tmp_path: Path) -> None:
    source = tmp_path / "results.txt"
    source.write_text("unsupported", encoding="utf-8")

    with pytest.raises(ValueError, match="Unsupported source format"):
        describe_source_file(source)
