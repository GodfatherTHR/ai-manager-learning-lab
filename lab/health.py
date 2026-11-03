"""Environment health checks shared by the CLI and the Streamlit app."""

from __future__ import annotations

import importlib.util
import tempfile
from dataclasses import dataclass

from lab import config, data_store, instructions, sessions, skills


@dataclass(frozen=True)
class Check:
    name: str
    status: str
    detail: str


def _package_check(module: str, label: str, required: bool = True) -> Check:
    found = importlib.util.find_spec(module) is not None
    if found:
        return Check(label, "ok", f"Python package '{module}' is available.")
    return Check(label, "fail" if required else "warn", f"Python package '{module}' is not installed.")


def run_checks() -> list[Check]:
    checks: list[Check] = []
    version = ".".join(str(part) for part in __import__("sys").version_info[:3])
    if __import__("sys").version_info >= (3, 10):
        checks.append(Check("Python version", "ok", f"Python {version}."))
    else:
        checks.append(Check("Python version", "fail", f"Python {version}; Python 3.10 or newer is required."))

    for module, label in [
        ("streamlit", "Streamlit"),
        ("pandas", "Pandas"),
        ("reportlab", "ReportLab"),
        ("markdown", "Markdown"),
    ]:
        checks.append(_package_check(module, label, required=True))
    checks.append(_package_check("mcp", "MCP (optional)", required=False))

    if config.TEACHER_DIR.exists():
        checks.append(Check("Teacher materials", "ok", f"Found {config.display_path(config.TEACHER_DIR)}."))
    else:
        checks.append(Check("Teacher materials", "fail", f"Missing folder: {config.display_path(config.TEACHER_DIR)}."))

    company_files = data_store.list_company_files()
    tables = [item for item in company_files if item.kind == "table"]
    documents = [item for item in company_files if item.kind == "document"]
    if tables:
        checks.append(Check("Company tables", "ok", f"{len(tables)} CSV table(s) discovered."))
    else:
        checks.append(Check("Company tables", "fail", "No CSV tables were discovered in teacher_materials."))
    if documents:
        checks.append(Check("Company documents", "ok", f"{len(documents)} document(s) discovered."))
    else:
        checks.append(Check("Company documents", "warn", "No Markdown/txt/json company documents were discovered."))

    for item in tables:
        try:
            frame = data_store.load_table(item.name)
            checks.append(Check(f"CSV: {item.name}", "ok", f"{len(frame):,} rows, {len(frame.columns):,} columns."))
        except Exception as exc:
            checks.append(Check(f"CSV: {item.name}", "fail", str(exc)))

    manifest = data_store.check_manifest()
    manifest_status = "ok" if manifest["status"] in {"verified", "untracked"} else "warn"
    checks.append(Check("Dataset manifest", manifest_status, manifest["summary"]))
    for name in manifest.get("changed", []):
        checks.append(Check(f"Changed: {name}", "warn", "File differs from the recorded teacher manifest."))
    for name in manifest.get("missing", []):
        checks.append(Check(f"Missing: {name}", "warn", "File recorded in the manifest is missing."))
    for name in manifest.get("added", []):
        checks.append(Check(f"Added: {name}", "warn", "File is not recorded in the teacher manifest."))

    try:
        active = instructions.list_instructions()
        if active:
            checks.append(Check("Student instructions", "ok", f"{len(active)} active instruction file(s)."))
        else:
            checks.append(Check("Student instructions", "warn", "No active instruction files yet; students can create them in the app."))
        for item in active:
            try:
                instructions.read_instruction(item.name)
            except Exception as exc:
                checks.append(Check(f"Instruction: {item.name}", "fail", str(exc)))
    except Exception as exc:
        checks.append(Check("Student instructions", "fail", str(exc)))

    try:
        catalog = skills.catalog()
        skill_errors = skills.validate_all()
        if catalog:
            checks.append(Check("Built-in skills", "ok", f"{len(catalog)} optional skill(s) discovered."))
        else:
            checks.append(Check("Built-in skills", "warn", "No built-in skills were discovered in builtin_skills."))
        for error in skill_errors:
            checks.append(Check("Skill validation", "fail", error))
    except Exception as exc:
        checks.append(Check("Built-in skills", "fail", str(exc)))

    try:
        sessions.init_db()
        checks.append(Check("Session database", "ok", f"SQLite database is ready at {config.display_path(config.DB_PATH)}."))
        sessions.list_sessions(1)
    except Exception as exc:
        checks.append(Check("Session database", "fail", str(exc)))

    try:
        config.EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=config.EXPORTS_DIR, prefix=".write-test-", delete=True) as handle:
            handle.write(b"ok")
        checks.append(Check("Export folder", "ok", f"{config.display_path(config.EXPORTS_DIR)} is writable."))
    except Exception as exc:
        checks.append(Check("Export folder", "fail", str(exc)))

    try:
        from lab import pdf_export
        family = pdf_export.font_family()
        checks.append(Check("PDF fonts", "ok", f"Using font family '{family}' for PDF reports."))
    except Exception as exc:
        checks.append(Check("PDF fonts", "fail", f"Could not initialize PDF fonts: {exc}"))

    return checks


def format_checks(checks: list[Check]) -> str:
    labels = {"ok": "OK", "warn": "WARN", "fail": "FAIL"}
    lines = ["AI Manager Learning Lab — environment check", ""]
    for check in checks:
        lines.append(f"[{labels.get(check.status, check.status.upper()):4}] {check.name}: {check.detail}")
    failures = sum(1 for check in checks if check.status == "fail")
    warnings = sum(1 for check in checks if check.status == "warn")
    lines.append("")
    lines.append(f"{len(checks)} checks, {failures} failure(s), {warnings} warning(s).")
    return "\n".join(lines)


def has_failures(checks: list[Check]) -> bool:
    return any(check.status == "fail" for check in checks)
