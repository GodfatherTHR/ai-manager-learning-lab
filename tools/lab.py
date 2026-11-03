#!/usr/bin/env python
"""Command-line bridge for the AI Manager Learning Lab.

This tool contains no AI model. It gives any agent harness safe, read-only access
to company data, student instructions, and session logging.
"""

from __future__ import annotations

import argparse
import json
import sys
import textwrap
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lab import config, data_store, health, instructions, pdf_export, sessions, skills, zip_export
from lab.errors import LabError

for stream in (sys.stdout, sys.stderr):
    try:
        stream.reconfigure(encoding="utf-8")
    except Exception:
        pass


def _print_json(data) -> None:
    print(json.dumps(data, indent=2, ensure_ascii=False))


def _print_table(headers: list[str], rows: list[list], max_width: int = 46) -> None:
    def cell(value) -> str:
        text = str(value).replace("\r", " ").replace("\n", " ").strip()
        if len(text) > max_width:
            text = text[: max_width - 1] + "…"
        return text

    rendered = [[cell(value) for value in row] for row in rows]
    widths = [len(header) for header in headers]
    for row in rendered:
        for index, value in enumerate(row):
            widths[index] = max(widths[index], len(value))
    print("  ".join(header.ljust(widths[index]) for index, header in enumerate(headers)))
    print("  ".join("-" * width for width in widths))
    for row in rendered:
        print("  ".join(value.ljust(widths[index]) for index, value in enumerate(row)))


def _read_text(value: str | None, file_path: str | None, label: str) -> str:
    if value is not None and file_path is not None:
        raise LabError(f"Provide either {label} text or a {label} file, not both.")
    if file_path is not None:
        if file_path == "-":
            return sys.stdin.read()
        path = Path(file_path)
        try:
            return path.read_text(encoding="utf-8")
        except OSError as exc:
            raise LabError(f"Could not read {label} file {file_path}: {exc}") from exc
    if value is None:
        raise LabError(f"Missing {label}. Provide the text or use a file.")
    return value


def _split_items(values: list[str] | None, comma_value: str | None = None) -> list[str]:
    output = []
    for value in values or []:
        output.extend(part.strip() for part in str(value).split(",") if part.strip())
    if comma_value:
        output.extend(part.strip() for part in comma_value.split(",") if part.strip())
    return output


def _lines_from_text(value: str | None, file_path: str | None = None) -> list[str]:
    lines = []
    if value:
        lines.extend(value.splitlines())
    if file_path:
        try:
            lines.extend(Path(file_path).read_text(encoding="utf-8").splitlines())
        except OSError as exc:
            raise LabError(f"Could not read {file_path}: {exc}") from exc
    return [line.strip() for line in lines if line.strip()]


def cmd_doctor(_args) -> int:
    checks = health.run_checks()
    print(health.format_checks(checks))
    return 1 if health.has_failures(checks) else 0


def cmd_data_list(args) -> None:
    files = data_store.list_company_files()
    if args.json:
        _print_json({"company": data_store.company_name(), "files": [asdict(item) for item in files]})
        return
    print(f"Company: {data_store.company_name()}")
    print(f"Folder: {config.display_path(config.TEACHER_DIR)}")
    print()
    if not files:
        print("No teacher-provided company files were found.")
        return
    rows = []
    for item in files:
        if item.kind == "table":
            try:
                frame = data_store.load_table(item.name)
                rows.append([item.name, "table", f"{len(frame):,}", f"{len(frame.columns):,}", f"{item.size / 1024:.0f} KB"])
            except LabError as exc:
                rows.append([item.name, "table", "ERROR", "-", str(exc)])
        else:
            rows.append([item.name, "document", "-", "-", f"{item.size / 1024:.0f} KB"])
    _print_table(["File", "Kind", "Rows", "Columns", "Size"], rows)


def cmd_data_show(args) -> None:
    path = data_store.resolve_company_file(args.file)
    if path.suffix.lower() == ".csv":
        print(data_store.describe_table(args.file))
    else:
        print(data_store.read_document(args.file))


def cmd_data_summary(args) -> None:
    path = data_store.resolve_company_file(args.file)
    if path.suffix.lower() == ".csv":
        print(data_store.describe_table(args.file))
        return
    text = data_store.read_document(args.file)
    headings = [line.strip() for line in text.splitlines() if line.strip().startswith("#")]
    preview_lines = text.splitlines()[:30]
    print(f"# {args.file}")
    print()
    print(f"- Characters: {len(text):,}")
    print(f"- Words: {len(text.split()):,}")
    if headings:
        print("- Headings:")
        for heading in headings[:20]:
            print(f"  {heading}")
    print()
    print("## Preview")
    print()
    print("\n".join(preview_lines))


def cmd_data_query(args) -> None:
    result = data_store.query_table(
        args.file,
        filters=args.filter or [],
        group_by=args.group_by,
        metrics=args.metric or [],
        sort_by=args.sort,
        limit=args.limit,
    )
    print(data_store.format_query_result(result, args.format))


def cmd_instructions_list(args) -> None:
    files = instructions.list_instructions()
    if args.json:
        _print_json([asdict(item) for item in files])
        return
    if not files:
        print("No active instruction files yet.")
        return
    _print_table(
        ["File", "Words", "Modified", "First heading"],
        [[item.name, f"{item.words:,}", item.modified, item.heading or "-"] for item in files],
    )


def cmd_instructions_read(args) -> None:
    print(instructions.read_instruction(args.file))


def cmd_instructions_search(args) -> None:
    matches = instructions.search_instructions(args.query, limit=args.limit)
    if args.json:
        _print_json([asdict(item) for item in matches])
        return
    if not matches:
        print("No instruction files matched the query terms.")
        return
    _print_table(
        ["File", "Score", "Matched terms", "First heading"],
        [[item.name, f"{item.score:.2f}", ", ".join(item.matched_terms), item.heading or "-"] for item in matches],
    )
    print("\nThis is a retrieval aid, not the final selection. Read the candidate files and decide which instructions apply.")


def cmd_instructions_write(args) -> None:
    content = _read_text(args.content, args.content_file, "content") if (args.content is not None or args.content_file) else ""
    exists = False
    try:
        instructions.resolve_instruction(args.file)
        exists = True
    except LabError:
        exists = False
    if exists and not args.force:
        raise LabError(f"{args.file} already exists. Use --force to overwrite it.")
    item = instructions.update_instruction(args.file, content) if exists else instructions.create_instruction(args.file, content)
    print(f"Saved {item.name} ({item.words:,} words).")


def cmd_skills_list(args) -> None:
    catalog = skills.catalog()
    if args.json:
        _print_json(catalog)
        return
    if not catalog:
        print("No built-in skills are installed.")
        return
    _print_table(
        ["Skill", "Category", "Title", "What it does"],
        [[item["name"], item["category"], item["title"], item["description"]] for item in catalog],
    )
    print("\nSkills are optional and invoked-only. An AI Manager should read one only when the student names it.")


def cmd_skills_read(args) -> None:
    print(skills.read_skill(args.name))


def cmd_skills_search(args) -> None:
    matches = skills.search_skills(args.query, limit=args.limit)
    if args.json:
        _print_json([asdict(item) for item in matches])
        return
    if not matches:
        print("No built-in skills matched the query terms.")
        return
    _print_table(
        ["Skill", "Category", "Score", "Matched terms", "Description"],
        [[item.name, item.category, f"{item.score:.2f}", ", ".join(item.matched_terms), item.description] for item in matches],
    )
    print("\nThis is metadata search only. Read and apply a skill only when the student explicitly invokes it.")


def cmd_session_new(args) -> None:
    session = sessions.new_session(
        title=args.title,
        student_name=args.student_name,
        student_id=args.student_id,
        agent=args.agent,
    )
    print(f"Created session {session.id}")
    print(f"Title: {session.title}")
    print(f"Student: {session.student_name or 'Not provided'}")
    print(f"Agent / harness: {session.agent or 'Not recorded'}")
    print()
    print("The session is now active. Log each turn with:")
    print(f'  py tools/lab.py log-turn {session.id} --json turn.json')
    print("Or start from the app's AI Manager > Agent setup tab.")


def cmd_session_list(args) -> None:
    items = sessions.list_sessions(args.limit)
    if args.json:
        _print_json([asdict(item) for item in items])
        return
    if not items:
        print("No sessions yet.")
        return
    _print_table(
        ["Session ID", "Title", "Student", "Turns", "Status", "Updated"],
        [
            [item.id, item.title, item.student_name or "-", item.turn_count, item.status, sessions.human_time(item.updated_at)]
            for item in items
        ],
    )


def cmd_session_use(args) -> None:
    session_id = sessions.resolve_session_id(args.session)
    sessions.set_active_session(session_id)
    session = sessions.get_session(session_id)
    print(f"Active session: {session.id} - {session.title}")


def cmd_session_show(args) -> None:
    session = sessions.get_session(args.session)
    if args.json:
        _print_json(sessions.session_to_dict(session))
    else:
        print(sessions.format_session_markdown(session))


def cmd_session_context(args) -> None:
    session = sessions.get_session(args.session)
    print(sessions.session_context_markdown(session))
    print()
    print("## Company data index")
    print()
    print(data_store.data_digest())
    if args.full:
        print()
        print("## Current company documents and tables")
        print(data_store.data_digest(max_columns=100))


def cmd_session_update(args) -> None:
    summary = args.summary
    if args.summary_file:
        summary = Path(args.summary_file).read_text(encoding="utf-8")
    session = sessions.update_session(
        args.session,
        title=args.title,
        student_name=args.student_name,
        student_id=args.student_id,
        agent=args.agent,
        company=args.company,
        summary=summary,
        status=args.status,
    )
    print(f"Updated session {session.id} - {session.title}")
    print(f"Status: {session.status}")


def cmd_session_finish(args) -> None:
    summary = args.summary
    if args.summary_file:
        summary = Path(args.summary_file).read_text(encoding="utf-8")
    session = sessions.finish_session(args.session, summary=summary)
    print(f"Completed session {session.id} - {session.title}")
    print(f"Turns: {session.turn_count}")
    print("Next: export the PDF and the instruction ZIP.")


def cmd_session_delete(args) -> None:
    sessions.delete_session(args.session, confirm=args.yes)
    print(f"Deleted session {args.session}.")


def _json_list(value, label: str) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        if label in {"evidence"}:
            return [line.strip() for line in value.splitlines() if line.strip()]
        return [part.strip() for part in value.replace("\n", ",").split(",") if part.strip()]
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    raise LabError(f"'{label}' must be a string or a list of strings.")


def _load_turn_json(path: str) -> dict:
    try:
        text = sys.stdin.read() if path == "-" else Path(path).read_text(encoding="utf-8")
        payload = json.loads(text)
    except OSError as exc:
        raise LabError(f"Could not read turn JSON: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise LabError(f"Turn JSON is invalid: {exc}") from exc
    if not isinstance(payload, dict):
        raise LabError("Turn JSON must be an object.")
    return payload


def cmd_log_turn(args) -> None:
    if args.json:
        payload = _load_turn_json(args.json)
        query = payload.get("query")
        response = payload.get("response")
        if query is None or response is None:
            raise LabError("Turn JSON must contain both 'query' and 'response'.")
        instruction_refs = _json_list(payload.get("instructions") or payload.get("instruction_refs"), "instructions")
        document_refs = _json_list(payload.get("documents") or payload.get("document_refs"), "documents")
        skill_refs = _json_list(payload.get("skills") or payload.get("skill_files"), "skills")
        evidence = _json_list(payload.get("evidence"), "evidence")
        principles = _json_list(payload.get("principles"), "principles")
    else:
        query = _read_text(args.query, args.query_file, "query")
        response = _read_text(args.response, args.response_file, "response")
        instruction_refs = _split_items(args.instruction, args.instructions)
        document_refs = _split_items(args.document, args.documents)
        skill_refs = _split_items(args.skill, args.skills)
        evidence = _lines_from_text(args.evidence, args.evidence_file)
        principles = _split_items(args.principle, args.principles)

    turn = sessions.log_turn(
        args.session,
        query,
        response,
        instruction_refs=instruction_refs,
        document_refs=document_refs,
        evidence=evidence,
        principles=principles,
        skill_refs=skill_refs,
    )
    session = sessions.get_session(turn.session_id)
    print(f"Logged turn {turn.turn_no} in session {session.id} - {session.title}")
    print(f"Instructions: {', '.join(turn.instructions) if turn.instructions else 'None recorded'}")
    print(f"Skills: {', '.join(turn.skills) if turn.skills else 'None recorded'}")
    print(f"Company data: {', '.join(turn.documents) if turn.documents else 'None recorded'}")
    print(f"Evidence points: {len(turn.evidence)}")
    if not turn.instructions:
        print("WARNING: this turn did not cite any student instruction files.", file=sys.stderr)
    if not turn.documents:
        print("WARNING: this turn did not cite any company data files.", file=sys.stderr)
    print()
    print("Continue the session, or export with:")
    print(f"  py tools/lab.py export-pdf {session.id}")
    print(f"  py tools/lab.py export-zip {session.id}")


def cmd_export_pdf(args) -> None:
    path = pdf_export.export_session_pdf(args.session, Path(args.out) if args.out else None)
    print(f"PDF report written to: {path}")
    print(f"Size: {path.stat().st_size / 1024:.1f} KB")


def cmd_export_zip(args) -> None:
    session = sessions.get_session(args.session) if args.session else None
    if args.student_name:
        student_name = args.student_name
    else:
        student_name = session.student_name if session else ""
    out_path = Path(args.out) if args.out else None
    if out_path is None:
        out_path = config.EXPORTS_DIR / zip_export.default_zip_name(student_name)
    path = zip_export.write_instructions_zip(session=session, out_path=out_path)
    print(f"Instruction ZIP written to: {path}")
    print(f"Files included: {len(instructions.list_instructions())}")


def cmd_teacher_manifest(args) -> None:
    if args.write:
        path = data_store.write_manifest()
        print(f"Wrote dataset manifest: {path}")
    else:
        result = data_store.check_manifest()
        print(result["summary"])
        for key in ("changed", "missing", "added"):
            for name in result.get(key, []):
                print(f"- {key}: {name}")


def cmd_mcp(_args) -> None:
    import runpy
    sys.argv = ["mcp_server.py"]
    runpy.run_path(str(ROOT / "tools" / "mcp_server.py"), run_name="__main__")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lab",
        description="AI Manager Learning Lab environment bridge. No AI model is built in.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent(
            """\
            Examples:
              py tools/lab.py doctor
              py tools/lab.py data-list
              py tools/lab.py data-summary sales.csv
              py tools/lab.py data-query sales.csv --filter "Quarter=2026-Q3" --group-by Channel --metric sum:Revenue --sort Revenue:desc
              py tools/lab.py instructions-list
              py tools/lab.py skills-list
              py tools/lab.py skills-read gantt-planner
              py tools/lab.py session-new --student-name "A. Student" --student-id "2026-001" --agent "Command Code"
              py tools/lab.py log-turn latest --json turn.json
              py tools/lab.py export-pdf latest
              py tools/lab.py export-zip latest
            """
        ),
    )
    parser.add_argument("--version", action="version", version="AI Manager Learning Lab 1.0")
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor = subparsers.add_parser("doctor", help="Check the environment.")
    doctor.set_defaults(func=cmd_doctor)

    data_list = subparsers.add_parser("data-list", help="List teacher-provided company files.")
    data_list.add_argument("--json", action="store_true")
    data_list.set_defaults(func=cmd_data_list)

    data_show = subparsers.add_parser("data-show", help="Show a company document or table summary.")
    data_show.add_argument("file")
    data_show.set_defaults(func=cmd_data_show)

    data_summary = subparsers.add_parser("data-summary", help="Summarize a company file.")
    data_summary.add_argument("file")
    data_summary.set_defaults(func=cmd_data_summary)

    data_query = subparsers.add_parser("data-query", help="Query a company CSV safely.")
    data_query.add_argument("file")
    data_query.add_argument("--filter", action="append", default=[], help="COLUMN=VALUE, COLUMN>VALUE, COLUMN~TEXT; repeatable.")
    data_query.add_argument("--group-by", help="Comma-separated column(s).")
    data_query.add_argument("--metric", action="append", default=[], help="AGG:COLUMN, e.g. sum:Revenue; repeatable.")
    data_query.add_argument("--sort", help="COLUMN:asc|desc. Aggregated output columns may be named sum_Revenue.")
    data_query.add_argument("--limit", type=int, default=data_store.DEFAULT_QUERY_LIMIT)
    data_query.add_argument("--format", choices=["table", "csv", "json"], default="table")
    data_query.set_defaults(func=cmd_data_query)

    instructions_list = subparsers.add_parser("instructions-list", help="List active student instructions.")
    instructions_list.add_argument("--json", action="store_true")
    instructions_list.set_defaults(func=cmd_instructions_list)

    instructions_read = subparsers.add_parser("instructions-read", help="Print a student instruction file.")
    instructions_read.add_argument("file")
    instructions_read.set_defaults(func=cmd_instructions_read)

    instructions_search = subparsers.add_parser("instructions-search", help="Transparent keyword retrieval over student instructions.")
    instructions_search.add_argument("query")
    instructions_search.add_argument("--limit", type=int, default=8)
    instructions_search.add_argument("--json", action="store_true")
    instructions_search.set_defaults(func=cmd_instructions_search)

    instructions_write = subparsers.add_parser("instructions-write", help="Create or overwrite a student instruction file.")
    instructions_write.add_argument("file")
    instructions_write.add_argument("--content")
    instructions_write.add_argument("--content-file")
    instructions_write.add_argument("--force", action="store_true")
    instructions_write.set_defaults(func=cmd_instructions_write)

    skills_list = subparsers.add_parser("skills-list", help="List optional built-in skills (metadata only).")
    skills_list.add_argument("--json", action="store_true")
    skills_list.set_defaults(func=cmd_skills_list)

    skills_read = subparsers.add_parser("skills-read", help="Read one built-in skill after the student invokes it.")
    skills_read.add_argument("name")
    skills_read.set_defaults(func=cmd_skills_read)

    skills_search = subparsers.add_parser("skills-search", help="Search built-in skill metadata (do not auto-apply).")
    skills_search.add_argument("query")
    skills_search.add_argument("--limit", type=int, default=10)
    skills_search.add_argument("--json", action="store_true")
    skills_search.set_defaults(func=cmd_skills_search)

    session_new = subparsers.add_parser("session-new", help="Start a new session.")
    session_new.add_argument("--title")
    session_new.add_argument("--student-name")
    session_new.add_argument("--student-id")
    session_new.add_argument("--agent", help="Agent or harness name, e.g. Command Code, Claude Code, ChatGPT.")
    session_new.set_defaults(func=cmd_session_new)

    session_list = subparsers.add_parser("session-list", help="List sessions.")
    session_list.add_argument("--limit", type=int, default=50)
    session_list.add_argument("--json", action="store_true")
    session_list.set_defaults(func=cmd_session_list)

    session_use = subparsers.add_parser("session-use", help="Set the active session.")
    session_use.add_argument("session")
    session_use.set_defaults(func=cmd_session_use)

    session_show = subparsers.add_parser("session-show", help="Show a session transcript.")
    session_show.add_argument("session", nargs="?", default="latest")
    session_show.add_argument("--json", action="store_true")
    session_show.set_defaults(func=cmd_session_show)

    session_context = subparsers.add_parser("session-context", help="Print a context pack for continuing the session.")
    session_context.add_argument("session", nargs="?", default="latest")
    session_context.add_argument("--full", action="store_true")
    session_context.set_defaults(func=cmd_session_context)

    session_update = subparsers.add_parser("session-update", help="Update session metadata or summary.")
    session_update.add_argument("session", nargs="?", default="latest")
    session_update.add_argument("--title")
    session_update.add_argument("--student-name")
    session_update.add_argument("--student-id")
    session_update.add_argument("--agent")
    session_update.add_argument("--company")
    session_update.add_argument("--summary")
    session_update.add_argument("--summary-file")
    session_update.add_argument("--status", choices=["active", "completed"])
    session_update.set_defaults(func=cmd_session_update)

    session_finish = subparsers.add_parser("session-finish", help="Mark a session completed.")
    session_finish.add_argument("session", nargs="?", default="latest")
    session_finish.add_argument("--summary")
    session_finish.add_argument("--summary-file")
    session_finish.set_defaults(func=cmd_session_finish)

    session_delete = subparsers.add_parser("session-delete", help="Delete a session (requires --yes).")
    session_delete.add_argument("session")
    session_delete.add_argument("--yes", action="store_true")
    session_delete.set_defaults(func=cmd_session_delete)

    log_turn = subparsers.add_parser(
        "log-turn",
        help="Log one exact query and response with its sources.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent(
            """\
            Recommended JSON shape:
              {
                "query": "The student's exact question",
                "response": "The AI Manager's full response",
                "instructions": ["planning.md", "decision_making.md"],
                "skills": ["gantt-planner"],
                "documents": ["sales.csv", "company_profile.md"],
                "evidence": ["Q3 2026 revenue was ..."],
                "principles": ["Controlling", "Decision making"]
              }
            """
        ),
    )
    log_turn.add_argument("session", nargs="?", default="latest")
    log_turn.add_argument("--json", help="Path to a turn JSON file, or '-' for stdin.")
    log_turn.add_argument("--query")
    log_turn.add_argument("--query-file")
    log_turn.add_argument("--response")
    log_turn.add_argument("--response-file")
    log_turn.add_argument("--instruction", action="append", default=[])
    log_turn.add_argument("--instructions", help="Comma-separated instruction file names.")
    log_turn.add_argument("--document", action="append", default=[])
    log_turn.add_argument("--documents", help="Comma-separated company data file names.")
    log_turn.add_argument("--skill", action="append", default=[])
    log_turn.add_argument("--skills", help="Comma-separated built-in skill names that the student invoked.")
    log_turn.add_argument("--evidence", help="Evidence text; use --evidence-file for multiple lines.")
    log_turn.add_argument("--evidence-file")
    log_turn.add_argument("--principle", action="append", default=[])
    log_turn.add_argument("--principles", help="Comma-separated management principles.")
    log_turn.set_defaults(func=cmd_log_turn)

    export_pdf = subparsers.add_parser("export-pdf", help="Generate the academic session PDF.")
    export_pdf.add_argument("session", nargs="?", default="latest")
    export_pdf.add_argument("--out")
    export_pdf.set_defaults(func=cmd_export_pdf)

    export_zip = subparsers.add_parser("export-zip", help="Zip the active student instruction files.")
    export_zip.add_argument("session", nargs="?", default=None)
    export_zip.add_argument("--student-name")
    export_zip.add_argument("--out")
    export_zip.set_defaults(func=cmd_export_zip)

    manifest = subparsers.add_parser("teacher-manifest", help="Check or write the teacher dataset manifest.")
    manifest.add_argument("--write", action="store_true")
    manifest.set_defaults(func=cmd_teacher_manifest)

    mcp = subparsers.add_parser("mcp", help="Run the optional MCP server over stdio.")
    mcp.set_defaults(func=cmd_mcp)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args) or 0
    except LabError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("Cancelled.", file=sys.stderr)
        return 130
    except Exception as exc:
        if __import__("os").environ.get("LAB_DEBUG"):
            raise
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
