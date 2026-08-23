"""OCR for scanned lottery documents and images."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class OcrResult:
    """OCR output with provenance and confidence metadata."""

    source_path: Path
    text: str
    extraction_method: str = "tesseract"
    confidence: float | None = None


def ocr_image(source_path: Path) -> OcrResult:
    """Extract text from an image using Tesseract.

    OCR is intentionally optional. The function fails explicitly when the
    dependency or Tesseract executable is unavailable rather than silently
    producing an empty result.
    """
    if not source_path.is_file():
        raise FileNotFoundError(source_path)

    if source_path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".webp"}:
        raise ValueError(f"Unsupported image format: {source_path.suffix}")

    try:
        import pytesseract
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError(
            "Image OCR requires the 'ocr' optional dependencies. "
            "Install with: pip install -e '.[ocr]'"
        ) from exc

    with Image.open(source_path) as image:
        text = pytesseract.image_to_string(image)
        data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)

    confidences = [
        float(value)
        for value in data.get("conf", [])
        if str(value).strip() not in {"", "-1"}
    ]
    confidence = sum(confidences) / len(confidences) if confidences else None

    return OcrResult(
        source_path=source_path,
        text=text,
        confidence=confidence,
    )
