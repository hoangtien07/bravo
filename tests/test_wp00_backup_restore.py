from pathlib import Path

import pytest

from scripts.wp00_backup_restore import BackupError, _metadata, _volume


def test_project_volume_names_are_isolated():
    assert _volume("bravo-wp00", "uploads") == "bravo-wp00_uploads"
    assert _volume("bravo-wp00-restore", "uploads") != _volume("bravo-wp00", "uploads")


def test_metadata_requires_all_three_artifacts(tmp_path: Path):
    (tmp_path / "db_20260731_000000.dump").write_bytes(b"db")
    with pytest.raises(BackupError, match="incomplete"):
        _metadata(tmp_path, "20260731_000000", "bravo-wp00")
