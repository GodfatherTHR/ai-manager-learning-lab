"""ZIP export of the student's active Markdown instruction files."""

from __future__ import annotations

import io
import re
import zipfile
from datetime import datetime
from pathlib import Path

from lab import config, instructions, sessions
from lab.errors import ExportError


def _slug(value: str) -> str:
    text = re.sub(r"[^A-Za-z0-9._-]+", "_", (value or "").strip()).strip("._-")
    return text or "student"


def default_zip_name(student_name: str = "") -> str:
    date = datetime.now().astimezone().strftime("%Y%m%d")
    return f"{_slug(student_name)}_management_instructions_{date}.zip"


def render_instructions_zip() -> bytes:
    files = instructions.list_instructions()
    if not files:
        raise ExportError("There are no active instruction files to export. Create at least one .md file first.")
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for item in files:
            try:
                content = instructions.read_instruction(item.name)
            except Exception as exc:
                raise ExportError(f"Could not read {item.name} for the ZIP: {exc}") from exc
            archive.writestr(item.name, content.encode("utf-8"))
    return buffer.getvalue()


def write_instructions_zip(session: sessions.Session | None = None, out_path: Path | None = None) -> Path:
    data = render_instructions_zip()
    student_name = session.student_name if session else ""
    destination = out_path.resolve() if out_path else (config.EXPORTS_DIR / default_zip_name(student_name))
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(destination.name + ".tmp")
    try:
        temporary.write_bytes(data)
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)
    return destination
