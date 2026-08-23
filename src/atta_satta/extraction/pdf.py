"""PDF text extraction with provenance metadata."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ExtractedPage:
    """Text extracted from one PDF page."""

    source_path: Path
    page_number: int
    text: str
    extraction_method: str = "pdf_text"


def extract_pdf_text(source_path: Path) -> Iterator[ExtractedPage]:
    """Yield text from each PDF page.

    PyMuPDF is imported lazily so the core package remains importable when the
    optional document dependencies are not installed.
    """
    if not source_path.is_file():
        raise FileNotFoundError(source_path)

    if source_path.suffix.lower() != ".pdf":
        raise ValueError(f"Expected a PDF file, received: {source_path.name}")

    try:
        import fitz
    except ImportError as exc:
        raise RuntimeError(
            "PDF extraction requires the 'documents' optional dependencies. "
            "Install with: pip install -e '.[documents]'"
        ) from exc

    with fitz.open(source_path) as document:
        for index, page in enumerate(document):
            yield ExtractedPage(
                source_path=source_path,
                page_number=index + 1,
                text=page.get_text("text"),
            )
