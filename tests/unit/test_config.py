from pathlib import Path

from atta_satta.config import Settings


def test_settings_use_project_relative_data_directories(tmp_path: Path) -> None:
    settings = Settings.from_project_root(tmp_path)

    assert settings.project_root == tmp_path.resolve()
    assert settings.data_dir == tmp_path / "data"
    assert settings.raw_data_dir == tmp_path / "data" / "raw"
    assert settings.extracted_data_dir == tmp_path / "data" / "extracted"
    assert settings.validated_data_dir == tmp_path / "data" / "validated"


def test_settings_can_create_data_directories(tmp_path: Path) -> None:
    settings = Settings.from_project_root(tmp_path)

    settings.ensure_directories()

    assert settings.data_dir.is_dir()
    assert settings.raw_data_dir.is_dir()
    assert settings.extracted_data_dir.is_dir()
    assert settings.validated_data_dir.is_dir()
