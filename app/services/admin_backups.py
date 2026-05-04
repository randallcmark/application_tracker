from dataclasses import dataclass, field
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError, version
from io import BytesIO
from pathlib import Path, PurePosixPath
import sqlite3
import tempfile
from zipfile import ZIP_DEFLATED, BadZipFile, ZipFile

from sqlalchemy.engine import make_url

from app.core.config import settings


def app_version() -> str:
    try:
        return version("application-tracker")
    except PackageNotFoundError:
        return "unknown"


@dataclass(slots=True)
class BackupValidationResult:
    archive_name: str | None = None
    manifest_present: bool = False
    created_at: str | None = None
    backup_version: str | None = None
    database_url: str | None = None
    storage_backend: str | None = None
    local_storage_path: str | None = None
    database_entry: str | None = None
    artefact_entries: int = 0
    member_count: int = 0
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not self.errors


def sqlite_database_path() -> Path | None:
    url = make_url(settings.database_url)
    if url.get_backend_name() != "sqlite" or not url.database or url.database == ":memory:":
        return None
    return Path(url.database).resolve()


def write_sqlite_backup(archive: ZipFile) -> None:
    database_path = sqlite_database_path()
    if database_path is None or not database_path.exists():
        archive.writestr("database/README.txt", "SQLite database file was not available for backup.\n")
        return

    with tempfile.NamedTemporaryFile(suffix=".db") as backup_file:
        source = sqlite3.connect(database_path)
        destination = sqlite3.connect(backup_file.name)
        try:
            source.backup(destination)
        finally:
            destination.close()
            source.close()
        archive.write(backup_file.name, "database/app.db")


def write_local_artefacts_backup(archive: ZipFile) -> None:
    if settings.storage_backend != "local":
        archive.writestr(
            "artefacts/README.txt",
            f"Artefact backup is not supported for storage backend: {settings.storage_backend}.\n",
        )
        return

    storage_root = Path(settings.local_storage_path)
    if not storage_root.exists():
        archive.writestr("artefacts/README.txt", "No local artefact storage directory exists yet.\n")
        return

    written_files = 0
    for path in sorted(storage_root.rglob("*")):
        if not path.is_file():
            continue
        archive.write(path, Path("artefacts") / path.relative_to(storage_root))
        written_files += 1

    if written_files == 0:
        archive.writestr("artefacts/README.txt", "No local artefact files were present at backup time.\n")


def build_backup_zip() -> bytes:
    buffer = BytesIO()
    timestamp = datetime.now(UTC).replace(microsecond=0).isoformat()
    with ZipFile(buffer, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr(
            "MANIFEST.txt",
            "\n".join(
                [
                    "Application Tracker backup",
                    f"Created at: {timestamp}",
                    f"App version: {app_version()}",
                    f"Database URL: {settings.database_url}",
                    f"Storage backend: {settings.storage_backend}",
                    f"Local storage path: {settings.local_storage_path}",
                    "",
                ]
            ),
        )
        write_sqlite_backup(archive)
        write_local_artefacts_backup(archive)
    buffer.seek(0)
    return buffer.getvalue()


def _validate_member_name(name: str) -> str | None:
    path = PurePosixPath(name)
    if path.is_absolute():
        return f"Archive member uses an absolute path: {name}"
    if ".." in path.parts:
        return f"Archive member escapes the backup root: {name}"
    return None


def _read_manifest(result: BackupValidationResult, archive: ZipFile) -> None:
    try:
        manifest_text = archive.read("MANIFEST.txt").decode("utf-8")
    except KeyError:
        result.errors.append("Archive is missing MANIFEST.txt.")
        return
    except UnicodeDecodeError:
        result.errors.append("MANIFEST.txt is not valid UTF-8.")
        return

    result.manifest_present = True
    for line in manifest_text.splitlines():
        if line.startswith("Created at: "):
            result.created_at = line.removeprefix("Created at: ").strip() or None
        elif line.startswith("App version: "):
            result.backup_version = line.removeprefix("App version: ").strip() or None
        elif line.startswith("Database URL: "):
            result.database_url = line.removeprefix("Database URL: ").strip() or None
        elif line.startswith("Storage backend: "):
            result.storage_backend = line.removeprefix("Storage backend: ").strip() or None
        elif line.startswith("Local storage path: "):
            result.local_storage_path = line.removeprefix("Local storage path: ").strip() or None

    if result.created_at is None:
        result.warnings.append("Backup manifest does not record a creation timestamp.")
    if result.backup_version is None:
        result.warnings.append("Backup manifest does not record the app version.")


def _validate_sqlite_member(result: BackupValidationResult, archive: ZipFile, member_name: str) -> None:
    try:
        sqlite_bytes = archive.read(member_name)
    except KeyError:
        result.errors.append("Backup database payload could not be read.")
        return

    with tempfile.NamedTemporaryFile(suffix=".db") as candidate:
        candidate.write(sqlite_bytes)
        candidate.flush()
        try:
            connection = sqlite3.connect(candidate.name)
            try:
                connection.execute("PRAGMA schema_version;").fetchone()
            finally:
                connection.close()
        except sqlite3.DatabaseError as exc:
            result.errors.append(f"Backup database file is not a readable SQLite database: {exc}")


def validate_backup_zip_bytes(data: bytes, *, archive_name: str | None = None) -> BackupValidationResult:
    result = BackupValidationResult(archive_name=archive_name)

    try:
        with ZipFile(BytesIO(data)) as archive:
            members = archive.infolist()
            result.member_count = len(members)
            if not members:
                result.errors.append("Archive is empty.")
                return result

            for member in members:
                member_error = _validate_member_name(member.filename)
                if member_error:
                    result.errors.append(member_error)

            _read_manifest(result, archive)

            names = {member.filename for member in members}
            if "database/app.db" in names:
                result.database_entry = "database/app.db"
                _validate_sqlite_member(result, archive, "database/app.db")
            elif "database/README.txt" in names:
                result.database_entry = "database/README.txt"
                result.warnings.append("Backup does not contain a SQLite database file; check the database backend before restore.")
            else:
                result.errors.append("Archive is missing both database/app.db and database/README.txt.")

            result.artefact_entries = sum(
                1 for name in names if name.startswith("artefacts/") and name != "artefacts/README.txt"
            )
            if result.artefact_entries == 0 and "artefacts/README.txt" not in names:
                result.warnings.append("Archive contains no artefact files or artefact README.")
    except BadZipFile:
        result.errors.append("Archive is not a valid ZIP file.")

    return result
