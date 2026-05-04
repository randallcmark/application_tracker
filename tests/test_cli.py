from pathlib import Path
import sqlite3
from zipfile import ZIP_DEFLATED, ZipFile

import pytest

from app.cli import main


def _write_valid_backup(path: Path) -> None:
    database_path = path.parent / "backup.db"
    connection = sqlite3.connect(database_path)
    try:
        connection.execute("create table example (id integer primary key)")
        connection.commit()
    finally:
        connection.close()

    with ZipFile(path, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr(
            "MANIFEST.txt",
            "\n".join(
                [
                    "Application Tracker backup",
                    "Created at: 2026-05-03T12:00:00+00:00",
                    "App version: 0.1.0",
                    "Database URL: sqlite:////app/data/app.db",
                    "Storage backend: local",
                    "Local storage path: /app/data/artefacts",
                    "",
                ]
            ),
        )
        archive.write(database_path, "database/app.db")
        archive.writestr("artefacts/README.txt", "No local artefact files were present at backup time.\n")


def test_cli_backup_validate_reports_success(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    backup_path = tmp_path / "backup.zip"
    _write_valid_backup(backup_path)

    exit_code = main(["backup", "validate", "--file", str(backup_path)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Backup validation passed." in captured.out
