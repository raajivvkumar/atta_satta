"""Input-file discovery and provenance metadata."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

SUPPORTED_EXTENSIONS = {
    ".pdf",
    ".png",
    ".jpg",
    ".jpeg",
    ".tif",
    ".tiff",
    ".webp",
}


@dataclass(frozen=True, slots=True)
class SourceFile:
    """Immutable metadata describing an imported source file."""

    path: Path
    filename: str
    sha256: str
    size_bytes: int
    imported_at: datetime


def fingerprint_file(path: Path) -> str:
    """Return a SHA-256 fingerprint without loading the entire file in memory."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def describe_source_file(path: Path) -> SourceFile:
    """Create provenance metadata for a supported source file."""
    if not path.is_file():
        raise FileNotFoundError(path)
    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported source format: {path.suffix}")

    stat = path.stat()
    return SourceFile(
        path=path,
        filename=path.name,
        sha256=fingerprint_file(path),
        size_bytes=stat.st_size,
        imported_at=datetime.now(UTC),
    )


def discover_source_files(directory: Path) -> list[SourceFile]:
    """Discover supported source files recursively and preserve duplicates by hash."""
    if not directory.is_dir():
        raise NotADirectoryError(directory)

    return [
        describe_source_file(path)
        for path in sorted(directory.rglob("*"))
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
    ]
