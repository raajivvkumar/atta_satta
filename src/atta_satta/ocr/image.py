"""OCR for scanned lottery documents and images."""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class OcrResult:
    """OCR output with provenance and confidence metadata."""

    source_path: Path
    text: str
    extraction_method: str = "tesseract"
    confidence: float | None = None


def configure_tesseract(pytesseract_module) -> None:
    """Configure Tesseract from PATH, an environment override, or Windows defaults."""
    if shutil.which("tesseract"):
        return

    candidates = []
    configured_path = os.environ.get("TESSERACT_CMD")
    if configured_path:
        candidates.append(Path(configured_path))
    if os.name == "nt":
        candidates.extend(
            [
                Path(os.environ.get("ProgramFiles", r"C:\Program Files"))
                / "Tesseract-OCR"
                / "tesseract.exe",
                Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"))
                / "Tesseract-OCR"
                / "tesseract.exe",
            ]
        )

    for candidate in candidates:
        if candidate.is_file():
            pytesseract_module.pytesseract.tesseract_cmd = str(candidate)
            return


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

    configure_tesseract(pytesseract)
    try:
        with Image.open(source_path) as image:
            text = pytesseract.image_to_string(image)
            data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
    except pytesseract.TesseractNotFoundError as exc:
        raise RuntimeError(
            "Tesseract OCR is unavailable. Install the Tesseract executable and add "
            "its directory to PATH, then restart the application."
        ) from exc

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
