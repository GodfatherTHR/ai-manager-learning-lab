"""Session and turn storage for the AI Manager Learning Lab."""

from __future__ import annotations

import json
import secrets
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from typing import Iterable

from lab import config, data_store, instructions, skills
from lab.errors import SessionError

MAX_QUERY_CHARS = 200_000
MAX_RESPONSE_CHARS = 400_000
MAX_SUMMARY_CHARS = 40_000
MAX_LIST_ITEMS = 100
MAX_LIST_ITEM_CHARS = 4_000

_INITIALIZED = False


@dataclass(frozen=True)
class Turn:
    id: int
    session_id: str
    turn_no: int
    created_at: str
    query: str
    response: str
    instructions: list[str] = field(default_factory=list)
    documents: list[str] = field(default_factory=list)
    skills: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)
    principles: list[str] = field(default_factory=list)


@dataclass
class Session:
    id: str
    title: str
    student_name: str
    student_id: str
    course: str
    company: str
    agent: str
    status: str
    summary: str
    created_at: str
    updated_at: str
    ended_at: str
    turns: list[Turn] = field(default_factory=list)

    @property
    def turn_count(self) -> int:
        return len(self.turns)


@dataclass(frozen=True)
class SessionSummary:
    id: str
    title: str
    student_name: str
    student_id: str
    course: str
    company: str
    agent: str
    status: str
    created_at: str
    updated_at: str
    ended_at: str
    turn_count: int


@contextmanager
def _connect():
    config.ensure_runtime_dirs()
    connection = sqlite3.connect(config.DB_PATH, timeout=30)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 5000")
    connection.execute("PRAGMA journal_mode = WAL")
    try:
        yield connection
    finally:
        connection.close()


def init_db() -> None:
    global _INITIALIZED
    with _connect() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                student_name TEXT NOT NULL DEFAULT '',
                student_id TEXT NOT NULL DEFAULT '',
                course TEXT NOT NULL DEFAULT 'Principles of Management',
                company TEXT NOT NULL DEFAULT '',
                agent TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'completed')),
                summary TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                ended_at TEXT NOT NULL DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS turns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                turn_no INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                query TEXT NOT NULL,
                response TEXT NOT NULL,
                instructions_json TEXT NOT NULL DEFAULT '[]',
                documents_json TEXT NOT NULL DEFAULT '[]',
                skills_json TEXT NOT NULL DEFAULT '[]',
                evidence_json TEXT NOT NULL DEFAULT '[]',
                principles_json TEXT NOT NULL DEFAULT '[]',
                FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
                UNIQUE (session_id, turn_no)
            );

            CREATE INDEX IF NOT EXISTS idx_turns_session
                ON turns(session_id, turn_no);
            CREATE INDEX IF NOT EXISTS idx_sessions_updated
                ON sessions(updated_at DESC);
            """
        )
        turn_columns = {
            row["name"] for row in connection.execute("PRAGMA table_info(turns)").fetchall()
        }
        if "skills_json" not in turn_columns:
            connection.execute(
                "ALTER TABLE turns ADD COLUMN skills_json TEXT NOT NULL DEFAULT '[]'"
            )
        connection.commit()
    _INITIALIZED = True


def _ensure_db() -> None:
    if not _INITIALIZED:
        init_db()


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def human_time(value: str) -> str:
    if not value:
        return "Not recorded"
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return value
    return f"{parsed.day} {parsed.strftime('%b %Y, %H:%M')}"


def human_date(value: str) -> str:
    if not value:
        now = datetime.now().astimezone()
        return f"{now.day} {now.strftime('%b %Y')}"
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return value
    return f"{parsed.day} {parsed.strftime('%b %Y')}"


def _default_title() -> str:
    return f"Management session — {human_date(now_iso())}"


def _clean_metadata(value: str | None, maximum: int = 200) -> str:
    text = (value or "").strip()
    text = text.replace("\x00", "")
    if len(text) > maximum:
        raise SessionError(f"A metadata field is too long (maximum {maximum} characters).")
    return text


def _normalize_string_list(values: Iterable[str] | None, label: str) -> list[str]:
    if values is None:
        return []
    if isinstance(values, str):
        values = [values]
    output = []
    seen = set()
    for value in values:
        text = str(value).replace("\x00", "").strip()
        if not text:
            continue
        if len(text) > MAX_LIST_ITEM_CHARS:
            text = text[: MAX_LIST_ITEM_CHARS - 1] + "…"
        if text not in seen:
            output.append(text)
            seen.add(text)
    if len(output) > MAX_LIST_ITEMS:
        raise SessionError(f"Too many {label} entries (maximum {MAX_LIST_ITEMS}).")
    return output


def _normalize_instruction_refs(values: Iterable[str] | None) -> list[str]:
    if isinstance(values, str):
        values = [values]
    output = []
    seen = set()
    for value in values or []:
        raw = str(value).strip()
        if not raw:
            continue
        path = instructions.resolve_instruction(raw)
        name = path.relative_to(config.STUDENT_DIR.resolve()).as_posix()
        if name not in seen:
            output.append(name)
            seen.add(name)
    return output


def _normalize_document_refs(values: Iterable[str] | None) -> list[str]:
    if isinstance(values, str):
        values = [values]
    output = []
    seen = set()
    for value in values or []:
        raw = str(value).strip()
        if not raw:
            continue
        name = data_store.normalize_company_reference(raw)
        if name not in seen:
            output.append(name)
            seen.add(name)
    return output


def _normalize_skill_refs(values: Iterable[str] | None) -> list[str]:
    if isinstance(values, str):
        values = [values]
    output = []
    seen = set()
    for value in values or []:
        raw = str(value).strip()
        if not raw:
            continue
        name = skills.normalize_skill_ref(raw)
        if name not in seen:
            output.append(name)
            seen.add(name)
    return output


def _session_id() -> str:
    timestamp = datetime.now().astimezone()
    base = timestamp.strftime("S-%Y%m%d-%H%M%S")
    for _ in range(20):
        candidate = f"{base}-{secrets.token_hex(2).upper()}"
        with _connect() as connection:
            exists = connection.execute("SELECT 1 FROM sessions WHERE id = ?", (candidate,)).fetchone()
        if not exists:
            return candidate
    raise SessionError("Could not allocate a unique session ID.")


def new_session(
    title: str | None = None,
    student_name: str | None = None,
    student_id: str | None = None,
    agent: str | None = None,
    company: str | None = None,
) -> Session:
    _ensure_db()
    session_id = _session_id()
    timestamp = now_iso()
    clean_title = _clean_metadata(title, 200) or _default_title()
    clean_company = _clean_metadata(company, 200) or data_store.company_name()
    with _connect() as connection:
        connection.execute(
            """
            INSERT INTO sessions
                (id, title, student_name, student_id, course, company, agent, status, summary, created_at, updated_at, ended_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'active', '', ?, ?, '')
            """,
            (
                session_id,
                clean_title,
                _clean_metadata(student_name, 120),
                _clean_metadata(student_id, 60),
                config.COURSE_NAME,
                clean_company,
                _clean_metadata(agent, 100),
                timestamp,
                timestamp,
            ),
        )
        connection.commit()
    set_active_session(session_id)
    return get_session(session_id)


def set_active_session(session_id: str | None) -> None:
    _ensure_db()
    if not session_id:
        clear_active_session()
        return
    resolved = resolve_session_id(session_id)
    config.ensure_runtime_dirs()
    temporary = config.ACTIVE_SESSION_FILE.with_suffix(".tmp")
    try:
        temporary.write_text(resolved + "\n", encoding="utf-8")
        temporary.replace(config.ACTIVE_SESSION_FILE)
    except OSError as exc:
        raise SessionError(f"Could not set the active session: {exc}") from exc


def get_active_session_id() -> str | None:
    try:
        value = config.ACTIVE_SESSION_FILE.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    return value or None


def clear_active_session() -> None:
    try:
        config.ACTIVE_SESSION_FILE.unlink(missing_ok=True)
    except OSError:
        pass


def resolve_session_id(reference: str | None = None) -> str:
    _ensure_db()
    raw = (reference or "").strip()
    if raw and raw.lower() not in {"latest", "current", "active"}:
        with _connect() as connection:
            row = connection.execute("SELECT id FROM sessions WHERE id = ?", (raw,)).fetchone()
            if row:
                return row["id"]
            prefix_rows = connection.execute(
                "SELECT id FROM sessions WHERE id LIKE ? ORDER BY updated_at DESC LIMIT 2",
                (raw + "%",),
            ).fetchall()
        if len(prefix_rows) == 1:
            return prefix_rows[0]["id"]
        if len(prefix_rows) > 1:
            raise SessionError(f"Session reference '{reference}' is ambiguous.")
        raise SessionError(f"Session not found: {reference}")

    active = get_active_session_id()
    if active:
        with _connect() as connection:
            row = connection.execute("SELECT id FROM sessions WHERE id = ?", (active,)).fetchone()
        if row:
            return row["id"]
        clear_active_session()

    with _connect() as connection:
        row = connection.execute(
            "SELECT id FROM sessions WHERE status = 'active' ORDER BY updated_at DESC LIMIT 1"
        ).fetchone()
        if not row:
            row = connection.execute("SELECT id FROM sessions ORDER BY updated_at DESC LIMIT 1").fetchone()
    if not row:
        raise SessionError("No session exists yet. Create one with the app or `session-new`.")
    return row["id"]


def _load_list(value: str) -> list[str]:
    try:
        parsed = json.loads(value or "[]")
    except (TypeError, json.JSONDecodeError):
        return []
    if not isinstance(parsed, list):
        return []
    return [str(item) for item in parsed]


def _row_to_turn(row: sqlite3.Row) -> Turn:
    return Turn(
        id=int(row["id"]),
        session_id=row["session_id"],
        turn_no=int(row["turn_no"]),
        created_at=row["created_at"],
        query=row["query"],
        response=row["response"],
        instructions=_load_list(row["instructions_json"]),
        documents=_load_list(row["documents_json"]),
        skills=_load_list(row["skills_json"]) if "skills_json" in row.keys() else [],
        evidence=_load_list(row["evidence_json"]),
        principles=_load_list(row["principles_json"]),
    )


def _row_to_session(row: sqlite3.Row, turns: list[Turn] | None = None) -> Session:
    return Session(
        id=row["id"],
        title=row["title"],
        student_name=row["student_name"],
        student_id=row["student_id"],
        course=row["course"],
        company=row["company"],
        agent=row["agent"],
        status=row["status"],
        summary=row["summary"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        ended_at=row["ended_at"],
        turns=turns or [],
    )


def _row_to_summary(row: sqlite3.Row) -> SessionSummary:
    return SessionSummary(
        id=row["id"],
        title=row["title"],
        student_name=row["student_name"],
        student_id=row["student_id"],
        course=row["course"],
        company=row["company"],
        agent=row["agent"],
        status=row["status"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        ended_at=row["ended_at"],
        turn_count=int(row["turn_count"]) if "turn_count" in row.keys() else 0,
    )


def list_sessions(limit: int = 200) -> list[SessionSummary]:
    _ensure_db()
    with _connect() as connection:
        rows = connection.execute(
            """
            SELECT s.*, (SELECT COUNT(*) FROM turns t WHERE t.session_id = s.id) AS turn_count
            FROM sessions s
            ORDER BY s.updated_at DESC
            LIMIT ?
            """,
            (max(1, limit),),
        ).fetchall()
    return [_row_to_summary(row) for row in rows]


def get_session(reference: str | None = None) -> Session:
    _ensure_db()
    session_id = resolve_session_id(reference)
    with _connect() as connection:
        row = connection.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
        if not row:
            raise SessionError(f"Session not found: {session_id}")
        turn_rows = connection.execute(
            "SELECT * FROM turns WHERE session_id = ? ORDER BY turn_no ASC",
            (session_id,),
        ).fetchall()
    return _row_to_session(row, [_row_to_turn(turn) for turn in turn_rows])


def log_turn(
    session_id: str | None,
    query: str,
    response: str,
    instruction_refs: Iterable[str] | None = None,
    document_refs: Iterable[str] | None = None,
    evidence: Iterable[str] | None = None,
    principles: Iterable[str] | None = None,
    skill_refs: Iterable[str] | None = None,
) -> Turn:
    _ensure_db()
    if not isinstance(query, str) or not query.strip():
        raise SessionError("The student query cannot be empty.")
    if not isinstance(response, str) or not response.strip():
        raise SessionError("The AI Manager response cannot be empty.")
    if len(query) > MAX_QUERY_CHARS:
        raise SessionError(f"The query is too long (maximum {MAX_QUERY_CHARS:,} characters).")
    if len(response) > MAX_RESPONSE_CHARS:
        raise SessionError(f"The response is too long (maximum {MAX_RESPONSE_CHARS:,} characters).")
    if "\x00" in query or "\x00" in response:
        raise SessionError("The query or response contains an invalid null character.")

    resolved_id = resolve_session_id(session_id)
    normalized_instructions = _normalize_instruction_refs(instruction_refs)
    normalized_documents = _normalize_document_refs(document_refs)
    normalized_skills = _normalize_skill_refs(skill_refs)
    normalized_evidence = _normalize_string_list(evidence, "evidence")
    normalized_principles = _normalize_string_list(principles, "principle")
    timestamp = now_iso()

    with _connect() as connection:
        connection.execute("BEGIN IMMEDIATE")
        try:
            session_row = connection.execute(
                "SELECT status FROM sessions WHERE id = ?", (resolved_id,)
            ).fetchone()
            if not session_row:
                raise SessionError(f"Session not found: {resolved_id}")
            if session_row["status"] == "completed":
                raise SessionError(
                    "This session is completed. Reopen it before logging another turn."
                )
            next_turn = connection.execute(
                "SELECT COALESCE(MAX(turn_no), 0) + 1 AS next_turn FROM turns WHERE session_id = ?",
                (resolved_id,),
            ).fetchone()["next_turn"]
            cursor = connection.execute(
                """
                INSERT INTO turns
                    (session_id, turn_no, created_at, query, response,
                     instructions_json, documents_json, skills_json, evidence_json, principles_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    resolved_id,
                    int(next_turn),
                    timestamp,
                    query,
                    response,
                    json.dumps(normalized_instructions, ensure_ascii=False),
                    json.dumps(normalized_documents, ensure_ascii=False),
                    json.dumps(normalized_skills, ensure_ascii=False),
                    json.dumps(normalized_evidence, ensure_ascii=False),
                    json.dumps(normalized_principles, ensure_ascii=False),
                ),
            )
            connection.execute(
                "UPDATE sessions SET updated_at = ? WHERE id = ?",
                (timestamp, resolved_id),
            )
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        row = connection.execute("SELECT * FROM turns WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return _row_to_turn(row)


def update_session(
    session_id: str | None,
    title: str | None = None,
    student_name: str | None = None,
    student_id: str | None = None,
    agent: str | None = None,
    company: str | None = None,
    summary: str | None = None,
    status: str | None = None,
) -> Session:
    _ensure_db()
    resolved_id = resolve_session_id(session_id)
    current = get_session(resolved_id)
    updates = {}
    if title is not None:
        updates["title"] = _clean_metadata(title, 200) or _default_title()
    if student_name is not None:
        updates["student_name"] = _clean_metadata(student_name, 120)
    if student_id is not None:
        updates["student_id"] = _clean_metadata(student_id, 60)
    if agent is not None:
        updates["agent"] = _clean_metadata(agent, 100)
    if company is not None:
        updates["company"] = _clean_metadata(company, 200) or data_store.company_name()
    if summary is not None:
        summary_text = (summary or "").replace("\x00", "")
        if len(summary_text) > MAX_SUMMARY_CHARS:
            raise SessionError(f"The session summary is too long (maximum {MAX_SUMMARY_CHARS:,} characters).")
        updates["summary"] = summary_text
    timestamp = now_iso()
    if status is not None:
        if status not in {"active", "completed"}:
            raise SessionError("Session status must be 'active' or 'completed'.")
        updates["status"] = status
        updates["ended_at"] = timestamp if status == "completed" else ""
    if not updates:
        return current
    updates["updated_at"] = timestamp
    assignments = ", ".join(f"{column} = ?" for column in updates)
    with _connect() as connection:
        connection.execute(
            f"UPDATE sessions SET {assignments} WHERE id = ?",
            (*updates.values(), resolved_id),
        )
        connection.commit()
    return get_session(resolved_id)


def finish_session(session_id: str | None = None, summary: str | None = None) -> Session:
    return update_session(session_id, summary=summary, status="completed")


def save_summary(session_id: str | None, summary: str) -> Session:
    return update_session(session_id, summary=summary)


def delete_session(session_id: str, confirm: bool = False) -> None:
    if not confirm:
        raise SessionError("Refusing to delete a session without explicit confirmation.")
    _ensure_db()
    resolved = resolve_session_id(session_id)
    with _connect() as connection:
        connection.execute("DELETE FROM sessions WHERE id = ?", (resolved,))
        connection.commit()
    if get_active_session_id() == resolved:
        clear_active_session()


def session_stats(session: Session) -> dict:
    instruction_refs = sorted({ref for turn in session.turns for ref in turn.instructions}, key=str.lower)
    skill_refs = sorted({ref for turn in session.turns for ref in turn.skills}, key=str.lower)
    document_refs = sorted({ref for turn in session.turns for ref in turn.documents}, key=str.lower)
    principles = []
    seen = set()
    for turn in session.turns:
        for principle in turn.principles:
            if principle not in seen:
                principles.append(principle)
                seen.add(principle)
    evidence_count = sum(len(turn.evidence) for turn in session.turns)
    return {
        "turns": len(session.turns),
        "instruction_refs": instruction_refs,
        "skill_refs": skill_refs,
        "document_refs": document_refs,
        "principles": principles,
        "evidence_count": evidence_count,
        "first_turn_at": session.turns[0].created_at if session.turns else session.created_at,
        "last_turn_at": session.turns[-1].created_at if session.turns else session.updated_at,
    }


def _fence(text: str) -> str:
    fence = "```"
    while fence in text:
        fence += "`"
    return fence


def format_session_markdown(session: Session, include_turns: bool = True) -> str:
    stats = session_stats(session)
    lines = [
        f"# {session.title}",
        "",
        f"- **Session ID:** {session.id}",
        f"- **Student:** {session.student_name or 'Not provided'}",
        f"- **Student ID:** {session.student_id or 'Not provided'}",
        f"- **Course:** {session.course}",
        f"- **Company:** {session.company}",
        f"- **Agent / harness:** {session.agent or 'Not recorded'}",
        f"- **Status:** {session.status}",
        f"- **Started:** {human_time(session.created_at)}",
        f"- **Last updated:** {human_time(session.updated_at)}",
        f"- **Turns:** {stats['turns']}",
    ]
    if session.summary.strip():
        lines.extend(["", "## Session summary", "", session.summary])
    if not include_turns:
        return "\n".join(lines)
    lines.extend(["", "## Conversation", ""])
    if not session.turns:
        lines.append("_No turns have been logged._")
        return "\n".join(lines)
    for turn in session.turns:
        fence = _fence(turn.query)
        lines.extend([
            f"### Turn {turn.turn_no} — {human_time(turn.created_at)}",
            "",
            "**Student query (verbatim):**",
            "",
            fence,
            turn.query,
            fence,
            "",
            "**AI Manager response:**",
            "",
            turn.response,
            "",
            "**Management instructions applied:** " + (", ".join(f"`{name}`" for name in turn.instructions) if turn.instructions else "None recorded"),
            "",
            "**Built-in skills applied:** " + (", ".join(f"`{name}`" for name in turn.skills) if turn.skills else "None recorded"),
            "",
            "**Company data consulted:** " + (", ".join(f"`{name}`" for name in turn.documents) if turn.documents else "None recorded"),
            "",
        ])
        if turn.evidence:
            lines.append("**Evidence cited:**")
            lines.extend(f"- {item}" for item in turn.evidence)
            lines.append("")
        if turn.principles:
            lines.append("**Management principles:** " + ", ".join(turn.principles))
            lines.append("")
        lines.append("---")
        lines.append("")
    return "\n".join(lines)


def session_context_markdown(session: Session) -> str:
    stats = session_stats(session)
    lines = [
        f"# AI Manager session context — {session.id}",
        "",
        "You are continuing an existing AI Manager Learning Lab session. Use the previous turns for continuity, "
        "keep prioritising the student's Markdown instructions, and cite company data for every factual claim.",
        "",
        f"- **Student:** {session.student_name or 'Not provided'}",
        f"- **Student ID:** {session.student_id or 'Not provided'}",
        f"- **Course:** {session.course}",
        f"- **Company:** {session.company}",
        f"- **Agent / harness:** {session.agent or 'Not recorded'}",
        f"- **Status:** {session.status}",
        f"- **Turns so far:** {stats['turns']}",
        "",
        "## Instructions available to the student",
        "",
        instructions.instructions_digest(),
        "",
        "## Conversation so far",
        "",
    ]
    if not session.turns:
        lines.append("_No turns have been logged yet._")
    else:
        for turn in session.turns:
            fence = _fence(turn.query)
            lines.extend([
                f"### Turn {turn.turn_no} — {human_time(turn.created_at)}",
                "",
                f"{fence}",
                turn.query,
                f"{fence}",
                "",
                turn.response,
                "",
                f"Instructions: {', '.join(turn.instructions) or 'None recorded'}",
                f"Skills: {', '.join(turn.skills) or 'None recorded'}",
                f"Data: {', '.join(turn.documents) or 'None recorded'}",
                "",
                "---",
                "",
            ])
    lines.extend([
        "## Next turn",
        "",
        "Answer the student's new query, then log the turn with the exact query and your full response "
        "using `py tools/lab.py log-turn` or the MCP `session_log_turn` tool.",
    ])
    return "\n".join(lines)


def session_to_dict(session: Session) -> dict:
    stats = session_stats(session)
    return {
        "id": session.id,
        "title": session.title,
        "student_name": session.student_name,
        "student_id": session.student_id,
        "course": session.course,
        "company": session.company,
        "agent": session.agent,
        "status": session.status,
        "summary": session.summary,
        "created_at": session.created_at,
        "updated_at": session.updated_at,
        "ended_at": session.ended_at,
        "turns": [
            {
                "turn_no": turn.turn_no,
                "created_at": turn.created_at,
                "query": turn.query,
                "response": turn.response,
                "instructions": turn.instructions,
                "skills": turn.skills,
                "documents": turn.documents,
                "evidence": turn.evidence,
                "principles": turn.principles,
            }
            for turn in session.turns
        ],
        "stats": stats,
    }
