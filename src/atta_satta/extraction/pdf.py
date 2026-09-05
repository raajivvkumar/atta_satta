"""PDF text extraction with provenance metadata and scanned-page OCR fallback."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from atta_satta.ocr.image import configure_tesseract


@dataclass(frozen=True, slots=True)
class ExtractedPage:
    """Text extracted from one PDF page."""

    source_path: Path
    page_number: int
    text: str
    extraction_method: str = "pdf_text"
    extraction_confidence: float | None = None


def _ocr_pdf_page(page, pymupdf_module) -> tuple[str, float | None]:
    """Render a PDF page and OCR it when the OCR dependencies are available."""
    try:
        import pytesseract
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError(
            "Scanned PDF OCR requires the 'ocr' optional dependencies. "
            "Install with: pip install -e '.[ocr]'"
        ) from exc

    configure_tesseract(pytesseract)
    pixmap = page.get_pixmap(matrix=pymupdf_module.Matrix(2, 2), alpha=False)
    image = Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)
    try:
        text = pytesseract.image_to_string(image)
        data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
    except pytesseract.TesseractNotFoundError as exc:
        raise RuntimeError(
            "Tesseract OCR is unavailable for this scanned PDF. Install the Tesseract "
            "executable and add its directory to PATH, then restart the application."
        ) from exc
    confidences = [
        float(value)
        for value in data.get("conf", [])
        if str(value).strip() not in {"", "-1"}
    ]
    confidence = sum(confidences) / len(confidences) if confidences else None
    return text, confidence


def extract_pdf_text(source_path: Path) -> list[ExtractedPage]:
    """Extract every PDF page, using OCR for pages with no embedded text.

    Text-based pages retain the ``pdf_text`` provenance. Pages that contain no
    usable embedded text are rendered and passed through Tesseract, preserving
    ``pdf_ocr`` provenance and OCR confidence. This makes scanned lottery PDFs
    part of the same reviewable ingestion pipeline instead of silently producing
    zero candidates.
    """
    if not source_path.is_file():
        raise FileNotFoundError(source_path)

    if source_path.suffix.lower() != ".pdf":
        raise ValueError(f"Expected a PDF file, received: {source_path.name}")

    try:
        import pymupdf
    except ImportError as exc:
        raise RuntimeError(
            "PDF extraction requires the 'documents' optional dependencies. "
            "Install with: pip install -e '.[documents]'"
        ) from exc

    pages: list[ExtractedPage] = []
    with pymupdf.open(source_path) as document:
        for index, page in enumerate(document):
            text = page.get_text("text")
            if text.strip():
                pages.append(
                    ExtractedPage(
                        source_path=source_path,
                        page_number=index + 1,
                        text=text,
                    )
                )
                continue

            ocr_text, confidence = _ocr_pdf_page(page, pymupdf)
            pages.append(
                ExtractedPage(
                    source_path=source_path,
                    page_number=index + 1,
                    text=ocr_text,
                    extraction_method="pdf_ocr",
                    extraction_confidence=confidence,
                )
            )

    return pages
