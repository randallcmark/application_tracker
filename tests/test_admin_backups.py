from io import BytesIO
import sqlite3
import tempfile
from zipfile import ZIP_DEFLATED, ZipFile

from app.services.admin_backups import validate_backup_zip_bytes


def test_validate_backup_zip_accepts_application_tracker_backup_shape() -> None:
    with tempfile.NamedTemporaryFile(suffix=".db") as database_file:
        connection = sqlite3.connect(database_file.name)
        try:
            connection.execute("create table example (id integer primary key)")
            connection.commit()
        finally:
            connection.close()

        buffer = BytesIO()
        with ZipFile(buffer, "w", compression=ZIP_DEFLATED) as archive:
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
            archive.write(database_file.name, "database/app.db")
            archive.writestr("artefacts/README.txt", "No local artefact files were present at backup time.\n")
        result = validate_backup_zip_bytes(buffer.getvalue(), archive_name="backup.zip")

        assert result.is_valid is True
        assert result.archive_name == "backup.zip"
        assert result.manifest_present is True
        assert result.database_entry == "database/app.db"
        assert result.backup_version == "0.1.0"
        assert result.errors == []


def test_validate_backup_zip_rejects_path_traversal_members() -> None:
    buffer = BytesIO()
    with ZipFile(buffer, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr("MANIFEST.txt", "Application Tracker backup\n")
        archive.writestr("../escape.txt", "nope")
        archive.writestr("database/README.txt", "No database\n")
        archive.writestr("artefacts/README.txt", "No artefacts\n")

    result = validate_backup_zip_bytes(buffer.getvalue(), archive_name="bad.zip")

    assert result.is_valid is False
    assert any("escapes the backup root" in item for item in result.errors)


def test_validate_backup_zip_rejects_invalid_zip_payload() -> None:
    result = validate_backup_zip_bytes(b"not a zip archive", archive_name="bad.zip")

    assert result.is_valid is False
    assert result.errors == ["Archive is not a valid ZIP file."]
