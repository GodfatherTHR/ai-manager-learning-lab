"""Filesystem and application configuration."""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _env_path(name: str, default: Path) -> Path:
    value = os.environ.get(name, "").strip()
    if not value:
        return default.resolve()
    path = Path(value)
    if not path.is_absolute():
        path = ROOT / path
    return path.resolve()


TEACHER_DIR = _env_path("LAB_TEACHER_DIR", ROOT / "teacher_materials")
STUDENT_DIR = _env_path("LAB_STUDENT_DIR", ROOT / "student_instructions")
SKILLS_DIR = _env_path("LAB_SKILLS_DIR", ROOT / "builtin_skills")
SESSIONS_DIR = _env_path("LAB_SESSIONS_DIR", ROOT / "sessions")
EXPORTS_DIR = _env_path("LAB_EXPORTS_DIR", ROOT / "exports")
DB_PATH = SESSIONS_DIR / "lab.db"
ACTIVE_SESSION_FILE = SESSIONS_DIR / "ACTIVE_SESSION"
MANIFEST_PATH = TEACHER_DIR / ".dataset_manifest.json"

COURSE_NAME = "Principles of Management"
APP_TITLE = "AI Manager Learning Lab"
COMPANY_FALLBACK = "Teacher-Provided Company"
SUPPORTED_DATA_SUFFIXES = {".csv", ".md", ".txt", ".json"}
SUPPORTED_TABLE_SUFFIXES = {".csv"}
SUPPORTED_DOC_SUFFIXES = {".md", ".txt", ".json"}


def ensure_runtime_dirs() -> None:
    for path in (STUDENT_DIR, SESSIONS_DIR, EXPORTS_DIR):
        path.mkdir(parents=True, exist_ok=True)


def display_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(ROOT).as_posix()
    except ValueError:
        return str(resolved)
