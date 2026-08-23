"""Application configuration for Atta Satta."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Settings:
    """Immutable application settings with safe project-relative defaults."""

    project_root: Path
    data_dir: Path
    raw_data_dir: Path
    extracted_data_dir: Path
    validated_data_dir: Path

    @classmethod
    def from_project_root(cls, project_root: Path | None = None) -> Settings:
        """Build settings from an explicit project root or the repository root."""
        root = (project_root or Path(__file__).resolve().parents[2]).resolve()
        data_dir = root / "data"
        return cls(
            project_root=root,
            data_dir=data_dir,
            raw_data_dir=data_dir / "raw",
            extracted_data_dir=data_dir / "extracted",
            validated_data_dir=data_dir / "validated",
        )

    def ensure_directories(self) -> None:
        """Create application data directories when they do not exist."""
        for directory in (
            self.data_dir,
            self.raw_data_dir,
            self.extracted_data_dir,
            self.validated_data_dir,
        ):
            directory.mkdir(parents=True, exist_ok=True)
