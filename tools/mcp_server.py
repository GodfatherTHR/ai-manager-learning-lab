"""Optional MCP server exposing the AI Manager Learning Lab environment.

This server contains no AI model. It only exposes read-only company data,
student instructions, session logging, and academic exports as MCP tools.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mcp.server.fastmcp import FastMCP

from lab import config, data_store, instructions, pdf_export, sessions, skills, zip_export

mcp = FastMCP(
    "AI Manager Learning Lab",
    instructions=(
        "You are the AI Manager for a university Principles of Management exercise. "
        "Read the student's Markdown instructions first, then query the teacher-provided company data. "
        "Never modify teacher_materials. Never invent company figures. Log every turn with the exact student query "
        "and your full response using session_log_turn. Cite instruction and data files. "
        "The environment does not call an AI model; you are the AI Manager."
    ),
)


def _json(data) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False)


def _error(exc: Exception) -> str:
    return _json({"error": str(exc)})


@mcp.tool()
def lab_guide() -> str:
    """Return the AI Manager protocol, folder map, and session workflow."""
    return _json({
        "app": config.APP_TITLE,
        "course": config.COURSE_NAME,
        "company": data_store.company_name(),
        "teacher_materials": config.display_path(config.TEACHER_DIR),
        "student_instructions": config.display_path(config.STUDENT_DIR),
        "builtin_skills": config.display_path(config.SKILLS_DIR),
        "sessions": config.display_path(config.SESSIONS_DIR),
        "exports": config.display_path(config.EXPORTS_DIR),
        "rules": [
            "Read the student's instruction files before answering.",
            "Prioritise the student's own management instructions over generic advice.",
            "Use teacher-provided data for factual claims and cite the file names.",
            "Do not invent company facts, figures, or employee names.",
            "Do not modify teacher_materials.",
            "Built-in skills are optional and invoked-only. Read a skill only when the student explicitly names it.",
            "Keep the student's query verbatim and log the full response.",
            "Do not expose private chain-of-thought; give concise analysis and recommendations.",
        ],
        "workflow": [
            "Call instructions_list and read relevant instruction files.",
            "If the student explicitly invokes a built-in skill, call skills_read and apply it. Otherwise do not read skill bodies.",
            "Call company_files and data_summary / data_query for evidence.",
            "Answer with findings, instructions applied, recommendations, and sources.",
            "Call session_log_turn with the exact query, full response, and source file lists.",
            "When the student is ready, call session_finish, export_session_pdf, and export_instructions_zip.",
        ],
    })


@mcp.tool()
def company_files() -> str:
    """List the teacher-provided company documents and CSV tables."""
    try:
        return _json({
            "company": data_store.company_name(),
            "files": [
                {"name": item.name, "kind": item.kind, "size": item.size, "modified": item.modified}
                for item in data_store.list_company_files()
            ],
        })
    except Exception as exc:
        return _error(exc)


@mcp.tool()
def data_read_document(file: str) -> str:
    """Read a company Markdown, text, or JSON document in full."""
    try:
        return data_store.read_document(file)
    except Exception as exc:
        return _error(exc)


@mcp.tool()
def data_summary(file: str) -> str:
    """Summarize a company CSV table or document with column types and sample values."""
    try:
        path = data_store.resolve_company_file(file)
        if path.suffix.lower() == ".csv":
            return data_store.describe_table(file)
        text = data_store.read_document(file)
        headings = [line.strip() for line in text.splitlines() if line.strip().startswith("#")]
        return "\n".join([
            f"# {file}",
            f"Characters: {len(text):,}",
            f"Words: {len(text.split()):,}",
            "Headings:",
            *[f"- {heading}" for heading in headings[:20]],
            "",
            "Preview:",
            "\n".join(text.splitlines()[:30]),
        ])
    except Exception as exc:
        return _error(exc)


@mcp.tool()
def data_query(
    file: str,
    filters: list[str] | None = None,
    group_by: str | None = None,
    metrics: list[str] | None = None,
    sort_by: str | None = None,
    limit: int = 100,
) -> str:
    """Query a company CSV with safe filters, grouping, and aggregations (no code execution)."""
    try:
        result = data_store.query_table(
            file,
            filters=filters or [],
            group_by=group_by,
            metrics=metrics or [],
            sort_by=sort_by,
            limit=limit,
        )
        return data_store.format_query_result(result, "json")
    except Exception as exc:
        return _error(exc)


@mcp.tool()
def instructions_list() -> str:
    """List the student's active Markdown management instruction files."""
    try:
        return _json([
            {
                "name": item.name,
                "words": item.words,
                "modified": item.modified,
                "heading": item.heading,
            }
            for item in instructions.list_instructions()
        ])
    except Exception as exc:
        return _error(exc)


@mcp.tool()
def instructions_read(file: str) -> str:
    """Read one active student instruction file in full."""
    try:
        return instructions.read_instruction(file)
    except Exception as exc:
        return _error(exc)


@mcp.tool()
def instructions_search(query: str, limit: int = 8) -> str:
    """Find candidate instruction files using transparent keyword scoring.

    This is a retrieval aid, not the final selection. Read the candidate files and
    decide which management instructions genuinely apply.
    """
    try:
        matches = instructions.search_instructions(query, limit=limit)
        return _json([
            {
                "name": item.name,
                "score": item.score,
                "matched_terms": list(item.matched_terms),
                "heading": item.heading,
            }
            for item in matches
        ])
    except Exception as exc:
        return _error(exc)


@mcp.tool()
def skills_list() -> str:
    """List optional built-in skills and their metadata. This does not read the skill bodies."""
    try:
        return _json(skills.catalog())
    except Exception as exc:
        return _error(exc)


@mcp.tool()
def skills_read(name: str) -> str:
    """Read one built-in skill in full.

    Call this only after the student explicitly invokes the skill. Do not read
    skills automatically just because a question matches a trigger.
    """
    try:
        return skills.read_skill(name)
    except Exception as exc:
        return _error(exc)


@mcp.tool()
def skills_search(query: str, limit: int = 10) -> str:
    """Search built-in skill metadata. Results are candidates, not an instruction to apply a skill."""
    try:
        matches = skills.search_skills(query, limit=limit)
        return _json([
            {
                "name": item.name,
                "title": item.title,
                "category": item.category,
                "description": item.description,
                "score": item.score,
                "matched_terms": list(item.matched_terms),
            }
            for item in matches
        ])
    except Exception as exc:
        return _error(exc)


@mcp.tool()
def session_start(
    title: str | None = None,
    student_name: str = "",
    student_id: str = "",
    agent: str = "",
) -> str:
    """Start a new session. Prefer starting from the Streamlit app so student details are captured."""
    try:
        session = sessions.new_session(
            title=title,
            student_name=student_name,
            student_id=student_id,
            agent=agent,
        )
        return _json({
            "session_id": session.id,
            "title": session.title,
            "student_name": session.student_name,
            "status": session.status,
            "created_at": session.created_at,
        })
    except Exception as exc:
        return _error(exc)


@mcp.tool()
def session_current() -> str:
    """Show the active session and its turn count."""
    try:
        session = sessions.get_session("latest")
        return _json({
            "session_id": session.id,
            "title": session.title,
            "student_name": session.student_name,
            "student_id": session.student_id,
            "company": session.company,
            "agent": session.agent,
            "status": session.status,
            "turns": session.turn_count,
            "updated_at": session.updated_at,
        })
    except Exception as exc:
        return _error(exc)


@mcp.tool()
def session_context(session_id: str = "latest") -> str:
    """Return the full session context plus the company data index for continuation."""
    try:
        session = sessions.get_session(session_id)
        return sessions.session_context_markdown(session) + "\n\n## Company data index\n\n" + data_store.data_digest()
    except Exception as exc:
        return _error(exc)


@mcp.tool()
def session_log_turn(
    session_id: str,
    query: str,
    response: str,
    instruction_files: list[str] | None = None,
    document_files: list[str] | None = None,
    skill_files: list[str] | None = None,
    evidence: list[str] | None = None,
    principles: list[str] | None = None,
) -> str:
    """Log one turn with the exact student query, full response, and cited sources.

    Include skill_files only when the student explicitly invoked those skills.
    """
    try:
        turn = sessions.log_turn(
            session_id,
            query,
            response,
            instruction_refs=instruction_files or [],
            document_refs=document_files or [],
            evidence=evidence or [],
            principles=principles or [],
            skill_refs=skill_files or [],
        )
        warnings = []
        if not turn.instructions:
            warnings.append("No student instruction files were cited for this turn.")
        if not turn.documents:
            warnings.append("No company data files were cited for this turn.")
        return _json({
            "session_id": turn.session_id,
            "turn": turn.turn_no,
            "logged_at": turn.created_at,
            "instructions": turn.instructions,
            "skills": turn.skills,
            "documents": turn.documents,
            "warnings": warnings,
        })
    except Exception as exc:
        return _error(exc)


@mcp.tool()
def session_update(
    session_id: str = "latest",
    title: str | None = None,
    student_name: str | None = None,
    student_id: str | None = None,
    agent: str | None = None,
    summary: str | None = None,
) -> str:
    """Update session metadata or save the final session summary."""
    try:
        session = sessions.update_session(
            session_id,
            title=title,
            student_name=student_name,
            student_id=student_id,
            agent=agent,
            summary=summary,
        )
        return _json({
            "session_id": session.id,
            "title": session.title,
            "student_name": session.student_name,
            "status": session.status,
            "summary_saved": bool(session.summary.strip()),
        })
    except Exception as exc:
        return _error(exc)


@mcp.tool()
def session_finish(session_id: str = "latest", summary: str | None = None) -> str:
    """Mark the session complete and optionally save the final summary."""
    try:
        session = sessions.finish_session(session_id, summary=summary)
        return _json({
            "session_id": session.id,
            "status": session.status,
            "ended_at": session.ended_at,
            "turns": session.turn_count,
        })
    except Exception as exc:
        return _error(exc)


@mcp.tool()
def export_session_pdf(session_id: str = "latest") -> str:
    """Generate the academic PDF session report and return its path."""
    try:
        path = pdf_export.export_session_pdf(session_id)
        return _json({"pdf": str(path), "size_bytes": path.stat().st_size})
    except Exception as exc:
        return _error(exc)


@mcp.tool()
def export_instructions_zip(session_id: str = "latest") -> str:
    """Zip the student's active Markdown instruction files and return the path."""
    try:
        session = sessions.get_session(session_id)
        path = zip_export.write_instructions_zip(session=session)
        return _json({
            "zip": str(path),
            "instruction_files": instructions.instruction_names(),
        })
    except Exception as exc:
        return _error(exc)


@mcp.tool()
def session_list(limit: int = 50) -> str:
    """List recent sessions."""
    try:
        return _json([
            {
                "session_id": item.id,
                "title": item.title,
                "student_name": item.student_name,
                "turns": item.turn_count,
                "status": item.status,
                "updated_at": item.updated_at,
            }
            for item in sessions.list_sessions(limit=limit)
        ])
    except Exception as exc:
        return _error(exc)


if __name__ == "__main__":
    if "--check" in sys.argv:
        tool_names = sorted(getattr(mcp._tool_manager, "_tools", {}).keys())
        print(f"MCP server ready with {len(tool_names)} tools: {', '.join(tool_names)}")
    else:
        mcp.run(transport="stdio")
