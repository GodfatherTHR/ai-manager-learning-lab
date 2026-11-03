from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from lab import config, data_store, health, instructions, sessions, skills, zip_export
from lab.errors import LabError

st.set_page_config(
    page_title=config.APP_TITLE,
    layout="wide",
    initial_sidebar_state="expanded",
)

CSS = """
<style>
:root {
    --lab-navy: #1F3A5F;
    --lab-accent: #2E6F95;
    --lab-border: #DCE4EE;
    --lab-muted: #687685;
    --lab-bg: #FBFCFE;
}
.stApp { background: var(--lab-bg); }
.block-container { max-width: 1180px; padding-top: 1.5rem; padding-bottom: 3rem; }
h1, h2, h3 { color: var(--lab-navy); }
.lab-hero {
    background: linear-gradient(135deg, #1F3A5F 0%, #2E6F95 100%);
    border-radius: 16px;
    padding: 26px 30px 24px 30px;
    color: white;
    margin-bottom: 18px;
}
.lab-hero h1 { color: white; margin: 4px 0 6px 0; font-size: 2.0rem; letter-spacing: -0.02em; }
.lab-hero p { color: #DCE8F2; margin: 0; font-size: 0.98rem; max-width: 850px; }
.lab-kicker {
    color: #BFD4E8;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.13em;
    text-transform: uppercase;
}
.lab-card {
    border: 1px solid var(--lab-border);
    border-radius: 12px;
    padding: 16px 18px;
    background: white;
}
.lab-note {
    border-left: 3px solid var(--lab-accent);
    background: #F4F8FC;
    padding: 10px 14px;
    border-radius: 4px;
    color: #34495E;
    font-size: 0.9rem;
}
.lab-pill {
    display: inline-block;
    border: 1px solid var(--lab-border);
    border-radius: 999px;
    padding: 2px 9px;
    margin: 2px 4px 2px 0;
    font-size: 0.76rem;
    color: #34495E;
    background: white;
}
div[data-testid="stChatMessage"] {
    border: 1px solid var(--lab-border);
    border-radius: 12px;
    background: white;
    padding: 4px 10px;
    margin-bottom: 8px;
}
div[data-testid="stMetric"] {
    background: white;
    border: 1px solid var(--lab-border);
    border-radius: 12px;
    padding: 10px 14px;
}
.stButton > button { border-radius: 8px; }
.stDownloadButton > button { border-radius: 8px; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

try:
    config.ensure_runtime_dirs()
    sessions.init_db()
except Exception as exc:
    st.error(f"The lab could not initialize its local storage: {exc}")
    st.stop()


def flash(kind: str, message: str) -> None:
    st.session_state["_flash"] = (kind, message)


def show_flash() -> None:
    item = st.session_state.pop("_flash", None)
    if not item:
        return
    kind, message = item
    getattr(st, kind, st.info)(message)


def hero(kicker: str, title: str, subtitle: str) -> None:
    st.markdown(
        f'<div class="lab-hero"><div class="lab-kicker">{kicker}</div>'
        f"<h1>{title}</h1><p>{subtitle}</p></div>",
        unsafe_allow_html=True,
    )


def active_session() -> sessions.Session | None:
    session_id = sessions.get_active_session_id()
    if not session_id:
        return None
    try:
        return sessions.get_session(session_id)
    except LabError:
        sessions.clear_active_session()
        return None


def instruction_fingerprint() -> str:
    return "|".join(f"{item.name}:{item.size}:{item.modified}" for item in instructions.list_instructions()) or "empty"


def format_size(size: int) -> str:
    if size > 1024 * 1024:
        return f"{size / 1024 / 1024:.1f} MB"
    if size > 1024:
        return f"{size / 1024:.1f} KB"
    return f"{size} bytes"


def split_csv(value: str | None) -> list[str]:
    return [part.strip() for part in (value or "").split(",") if part.strip()]


def split_lines(value: str | None) -> list[str]:
    return [line.strip() for line in (value or "").splitlines() if line.strip()]


def payload_list(value, split_commas: bool = True) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        if split_commas:
            return [part.strip() for part in value.replace("\n", ",").split(",") if part.strip()]
        return [line.strip() for line in value.splitlines() if line.strip()]
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    raise LabError("A list field in the JSON is not a string or list.")


def sidebar() -> str:
    with st.sidebar:
        st.markdown("## AI Manager")
        st.markdown("**Learning Lab**")
        st.caption("Principles of Management")
        st.divider()
        if "pending_nav" in st.session_state:
            st.session_state["nav"] = st.session_state.pop("pending_nav")
        page = st.radio(
            "Workspace",
            ["Instructions", "Company Data", "AI Manager", "Session History", "Help"],
            key="nav",
            label_visibility="collapsed",
        )
        st.divider()
        try:
            instruction_count = len(instructions.list_instructions())
        except Exception:
            instruction_count = 0
        try:
            company_count = len(data_store.list_company_files())
        except Exception:
            company_count = 0
        try:
            skill_count = len(skills.list_skills())
        except Exception:
            skill_count = 0
        column_a, column_b, column_c = st.columns(3)
        column_a.metric("Instructions", instruction_count)
        column_b.metric("Company files", company_count)
        column_c.metric("Skills", skill_count)
        session = active_session()
        if session:
            st.caption(f"Active session: {session.title}")
            st.caption(f"`{session.id}` · {session.turn_count} turn(s)")
        else:
            st.caption("No active session.")
        if st.button("Start new session", width="stretch"):
            st.session_state["pending_nav"] = "AI Manager"
            st.session_state["show_new_session"] = True
            st.rerun()
        st.divider()
        st.caption("No built-in AI. Use your own agent harness. No API key required.")
    return page


def page_instructions() -> None:
    hero(
        "Student workspace",
        "Management Instructions",
        "Write the management knowledge, procedures, and decision rules your AI Manager must apply. "
        "Every active .md file is discovered automatically; files starting with '_' or named README.md are ignored.",
    )
    files = instructions.list_instructions()
    if st.session_state.pop("reset_instruction_selector", False):
        st.session_state.pop("instruction_selector", None)
    if "pending_instruction" in st.session_state:
        st.session_state["instruction_selector"] = st.session_state.pop("pending_instruction")

    left, right = st.columns([0.36, 0.64], gap="large")

    with left:
        st.subheader("Your instruction files")
        if files:
            names = [item.name for item in files]
            if st.session_state.get("instruction_selector") not in names:
                st.session_state.pop("instruction_selector", None)
            selected = st.selectbox(
                "Instruction file",
                names,
                key="instruction_selector",
                format_func=lambda name: next(
                    (f"{item.name} · {item.words} words" for item in files if item.name == name), name
                ),
            )
            chosen = next(item for item in files if item.name == selected)
            st.caption(f"{chosen.words:,} words · updated {chosen.modified.replace('T', ' ')}")
        else:
            selected = None
            st.info("No active instruction files yet. Create your first file below.")

        with st.expander("New instruction file", expanded=not files):
            with st.form("new_instruction_form"):
                new_name = st.text_input("File name", placeholder="planning.md")
                new_content = st.text_area(
                    "Starting content (optional)",
                    height=160,
                    placeholder="Write your management concept, objectives, procedures, rules, and expected outcomes.",
                )
                if st.form_submit_button("Create file", type="primary"):
                    try:
                        item = instructions.create_instruction(new_name, new_content)
                        flash("success", f"Created {item.name}.")
                        st.session_state["pending_instruction"] = item.name
                        st.rerun()
                    except LabError as exc:
                        st.error(str(exc))

        with st.expander("Upload Markdown files"):
            with st.form("upload_instruction_form"):
                uploads = st.file_uploader(
                    "Choose .md files",
                    type=["md"],
                    accept_multiple_files=True,
                )
                if st.form_submit_button("Upload files"):
                    if not uploads:
                        st.warning("Choose at least one .md file.")
                    else:
                        saved = []
                        errors = []
                        for upload in uploads:
                            try:
                                item = instructions.upload_instruction(upload.name, upload.getvalue())
                                saved.append(item.name)
                            except LabError as exc:
                                errors.append(f"{upload.name}: {exc}")
                        if saved:
                            messages = ["Uploaded: " + ", ".join(saved)]
                            if errors:
                                messages.append("Not uploaded: " + " · ".join(errors))
                            flash("success" if saved and not errors else "warning", " | ".join(messages))
                            st.session_state["pending_instruction"] = saved[0]
                            st.rerun()
                        if errors and not saved:
                            flash("warning", "No files were uploaded: " + " · ".join(errors))
                            st.rerun()

        examples = instructions.list_examples()
        if examples:
            with st.expander("Optional examples for beginners"):
                st.caption("Examples are inactive until you copy one into your own instruction files.")
                example_names = [item.name for item in examples]
                example_selected = st.selectbox(
                    "Example",
                    example_names,
                    key="example_selector",
                    format_func=lambda name: next(
                        (f"{item.name} — {item.heading or 'example'}" for item in examples if item.name == name), name
                    ),
                )
                destination = st.text_input(
                    "Copy as",
                    value=Path(example_selected).name,
                    key="example_destination",
                )
                if st.button("Copy example into my instructions", key="copy_example_button"):
                    try:
                        item = instructions.copy_example(example_selected, destination)
                        flash("success", f"Created {item.name} from the example.")
                        st.session_state["pending_instruction"] = item.name
                        st.rerun()
                    except LabError as exc:
                        st.error(str(exc))

        st.caption("Supported: .md only. Maximum file size: 1 MB. Files starting with '_' are reserved for examples.")

    with right:
        if not selected:
            st.subheader("Create your first instruction file")
            st.markdown(
                "Start with a management concept you want the AI Manager to apply, for example planning, "
                "organizing, leadership, motivation, delegation, control, or performance evaluation."
            )
            st.markdown(
                '<div class="lab-note">You do not need a template. Write in your own words. '
                "The AI Manager is instructed to prioritise your files over generic management advice.</div>",
                unsafe_allow_html=True,
            )
            return
        try:
            current_content = instructions.read_instruction(selected)
        except LabError as exc:
            st.error(str(exc))
            return
        content = st.text_area(
            "Markdown content",
            value=current_content,
            height=480,
            key=f"editor_{selected}",
        )
        words = instructions.word_count(content)
        action_a, action_b, action_c = st.columns([0.3, 0.3, 0.4])
        if action_a.button("Save changes", type="primary", width="stretch"):
            try:
                item = instructions.update_instruction(selected, content)
                flash("success", f"Saved {item.name} ({item.words:,} words).")
                st.rerun()
            except LabError as exc:
                st.error(str(exc))
        action_b.download_button(
            "Download .md",
            data=content,
            file_name=Path(selected).name,
            mime="text/markdown",
            width="stretch",
        )
        action_c.caption(f"{words:,} words · current editor content")

        with st.expander("Preview rendered Markdown"):
            st.markdown(content)

        with st.expander("Rename this file"):
            renamed = st.text_input("New file name", key=f"rename_instruction_value_{selected}")
            if st.button("Rename", key=f"rename_instruction_button_{selected}"):
                try:
                    item = instructions.rename_instruction(selected, renamed)
                    flash("success", f"Renamed to {item.name}.")
                    st.session_state["pending_instruction"] = item.name
                    st.rerun()
                except LabError as exc:
                    st.error(str(exc))

        with st.expander("Delete this file"):
            confirm = st.checkbox(
                "I understand this permanently deletes the file.",
                key=f"delete_instruction_confirm_{selected}",
            )
            if st.button("Delete file", disabled=not confirm, key=f"delete_instruction_button_{selected}"):
                try:
                    instructions.delete_instruction(selected)
                    flash("success", f"Deleted {selected}.")
                    st.session_state["reset_instruction_selector"] = True
                    st.rerun()
                except LabError as exc:
                    st.error(str(exc))


def page_company_data() -> None:
    hero(
        "Read-only company case",
        "Company Data",
        "The teacher-provided company dataset is read-only in this lab. The AI Manager must cite these files; "
        "students must not modify or replace them during a session.",
    )
    files = data_store.list_company_files()
    if not files:
        st.error(
            f"No company data was found in {config.display_path(config.TEACHER_DIR)}. "
            "Ask the teacher to provide the folder contents, then refresh this page."
        )
        return
    manifest = data_store.check_manifest()
    if manifest["status"] == "verified":
        st.success(manifest["summary"])
    elif manifest["status"] == "changed":
        st.warning(manifest["summary"] + " Check the details if you did not intentionally replace the dataset.")
        with st.expander("Manifest details"):
            st.json(manifest)
    elif manifest["status"] == "untracked":
        st.info(manifest["summary"] + " The teacher can create one with `py tools/lab.py teacher-manifest --write`.")
    else:
        st.warning(manifest["summary"])

    st.caption(
        f"Company: {data_store.company_name()} · Folder: {config.display_path(config.TEACHER_DIR)} · "
        f"Files are discovered automatically."
    )
    names = [item.name for item in files]
    if st.session_state.get("company_file_selector") not in names:
        st.session_state.pop("company_file_selector", None)
    selected = st.selectbox(
        "Company file",
        names,
        format_func=lambda name: f"{name} ({next(item.kind for item in files if item.name == name)})",
        key="company_file_selector",
    )
    item = next(file for file in files if file.name == selected)

    if item.kind == "table":
        try:
            frame = data_store.load_table(selected)
        except LabError as exc:
            st.error(str(exc))
            return
        metric_a, metric_b, metric_c, metric_d = st.columns(4)
        metric_a.metric("Rows", f"{len(frame):,}")
        metric_b.metric("Columns", f"{len(frame.columns):,}")
        metric_c.metric("Missing cells", f"{int(frame.isna().sum().sum()):,}")
        metric_d.metric("File size", format_size(item.size))
        tabs = st.tabs(["Preview", "Structure", "Quick filter"])
        with tabs[0]:
            st.caption(f"Showing the first {min(250, len(frame)):,} of {len(frame):,} rows.")
            st.dataframe(frame.head(250), width="stretch", hide_index=True)
        with tabs[1]:
            profile = data_store.table_profile(frame)
            st.markdown("**Columns**")
            st.dataframe(
                pd.DataFrame([
                    {
                        "Column": column["name"],
                        "Type": column["dtype"],
                        "Non-null": column["non_null"],
                        "Missing": column["missing"],
                        "Unique": column["unique"],
                        "Sample": "; ".join(str(value) for value in column["sample"]),
                    }
                    for column in profile["column_details"]
                ]),
                width="stretch",
                hide_index=True,
            )
            if profile["numeric_summary"]:
                st.markdown("**Numeric summary**")
                st.dataframe(
                    pd.DataFrame(profile["numeric_summary"]).rename(columns={
                        "column": "Column", "count": "Count", "mean": "Mean", "std": "Std",
                        "min": "Min", "median": "Median", "max": "Max",
                    }),
                    width="stretch",
                    hide_index=True,
                )
        with tabs[2]:
            filter_column = st.selectbox("Column", frame.columns, key=f"filter_column_{selected}")
            operator = st.selectbox("Operator", ["contains", "equals", ">", "<", ">=", "<="], key=f"filter_operator_{selected}")
            filter_value = st.text_input("Value", key=f"filter_value_{selected}")
            if filter_value:
                series = frame[filter_column]
                try:
                    if operator == "contains":
                        filtered = frame[series.astype(str).str.contains(filter_value, case=False, na=False)]
                    elif operator == "equals":
                        filtered = frame[series.astype(str).str.lower() == filter_value.lower()]
                    else:
                        numeric = pd.to_numeric(series, errors="coerce")
                        target = float(filter_value)
                        if operator == ">":
                            filtered = frame[numeric > target]
                        elif operator == "<":
                            filtered = frame[numeric < target]
                        elif operator == ">=":
                            filtered = frame[numeric >= target]
                        else:
                            filtered = frame[numeric <= target]
                    st.caption(f"{len(filtered):,} matching rows. Showing the first {min(250, len(filtered)):,}.")
                    st.dataframe(filtered.head(250), width="stretch", hide_index=True)
                except ValueError:
                    st.error("This operator needs a numeric value for the selected column.")
    else:
        try:
            content = data_store.read_document(selected)
        except LabError as exc:
            st.error(str(exc))
            return
        metric_a, metric_b, metric_c = st.columns(3)
        metric_a.metric("Characters", f"{len(content):,}")
        metric_b.metric("Words", f"{len(content.split()):,}")
        metric_c.metric("File size", format_size(item.size))
        if selected.lower().endswith(".json"):
            try:
                st.json(json.loads(content))
            except json.JSONDecodeError:
                st.code(content, language="text")
        else:
            st.markdown(content)


def session_header(session: sessions.Session) -> None:
    st.subheader(session.title)
    st.caption(
        f"`{session.id}` · {session.student_name or 'Student name not set'} · "
        f"{session.agent or 'Agent not recorded'} · {session.status}"
    )
    stats = sessions.session_stats(session)
    metric_a, metric_b, metric_c, metric_d, metric_e = st.columns(5)
    metric_a.metric("Turns", stats["turns"])
    metric_b.metric("Instruction files used", len(stats["instruction_refs"]))
    metric_c.metric("Skills used", len(stats["skill_refs"]))
    metric_d.metric("Data sources", len(stats["document_refs"]))
    metric_e.metric("Evidence points", stats["evidence_count"])


def render_transcript(session: sessions.Session) -> None:
    if not session.turns:
        st.info("No turns have been logged yet. Use the Log a turn tab or connect your AI Manager.")
        return
    for turn in session.turns:
        with st.chat_message("user"):
            st.markdown("**Student query (verbatim from the session log)**")
            st.markdown(turn.query)
        with st.chat_message("assistant"):
            st.markdown(turn.response)
            st.caption(f"Turn {turn.turn_no} · logged {sessions.human_time(turn.created_at)}")
        with st.expander(f"Turn {turn.turn_no} — sources, evidence and principles"):
            if turn.instructions:
                st.markdown("**Instruction files applied**")
                for name in turn.instructions:
                    st.markdown(f"- `{name}`")
            else:
                st.caption("No student instruction files were recorded for this turn.")
            if turn.skills:
                st.markdown("**Built-in skills applied**")
                for name in turn.skills:
                    st.markdown(f"- `{name}`")
            else:
                st.caption("No built-in skills were recorded for this turn.")
            if turn.documents:
                st.markdown("**Company data consulted**")
                for name in turn.documents:
                    st.markdown(f"- `{name}`")
            else:
                st.caption("No company data files were recorded for this turn.")
            if turn.evidence:
                st.markdown("**Evidence cited**")
                for evidence in turn.evidence:
                    st.markdown(f"- {evidence}")
            if turn.principles:
                st.caption("Management principles: " + ", ".join(turn.principles))


def start_session_form(prominent: bool = False) -> None:
    show = st.session_state.pop("show_new_session", False)
    if prominent:
        container = st.container(border=True)
        container.subheader("Start a new management session")
        target = container
    else:
        target = st.expander("Start another session", expanded=show)
    with target:
        with st.form("start_session_form"):
            student_name = st.text_input("Student name", placeholder="Your full name")
            student_id = st.text_input("Student ID", placeholder="Your course ID")
            agent = st.text_input("AI Manager / harness", placeholder="e.g. Command Code, Claude Code, ChatGPT, Cursor")
            title = st.text_input("Session title (optional)", placeholder="Q3 sales decline review")
            if st.form_submit_button("Start session", type="primary"):
                try:
                    session = sessions.new_session(
                        title=title,
                        student_name=student_name,
                        student_id=student_id,
                        agent=agent,
                    )
                    flash("success", f"Started session {session.id}.")
                    st.rerun()
                except LabError as exc:
                    st.error(str(exc))


def resume_session_form() -> None:
    try:
        items = sessions.list_sessions()
    except LabError as exc:
        st.error(str(exc))
        return
    if not items:
        return
    with st.expander("Resume an existing session"):
        options = [item.id for item in items]
        selected = st.selectbox(
            "Session",
            options,
            key="resume_session_selector",
            format_func=lambda session_id: next(
                (f"{item.title} — {item.id} ({item.turn_count} turns)" for item in items if item.id == session_id),
                session_id,
            ),
        )
        if st.button("Open selected session", key="resume_session_button"):
            try:
                sessions.set_active_session(selected)
                flash("success", "Session opened.")
                st.rerun()
            except LabError as exc:
                st.error(str(exc))


def log_turn_tab(session: sessions.Session) -> None:
    st.markdown(
        "The query and response are stored **exactly as provided**. The PDF report reproduces both from this log."
    )
    if session.status == "completed":
        st.warning(
            "This session is completed and frozen. Reopen it in the Finalize & export tab before logging another turn."
        )
        return
    active_instructions = instructions.instruction_names()
    company_files = data_store.company_file_names()
    skill_options = skills.skill_names()
    with st.form("log_turn_form", clear_on_submit=True):
        query = st.text_area("Student query (verbatim)", height=120)
        response = st.text_area("AI Manager response (full response)", height=280)
        instruction_refs = st.multiselect(
            "Instruction files applied",
            active_instructions,
            help="Select every student-written instruction file the response actually used.",
        )
        skill_refs = st.multiselect(
            "Built-in skills applied (optional)",
            skill_options,
            help="Select only a built-in skill that the student explicitly invoked by name. Leave empty otherwise.",
        )
        document_refs = st.multiselect(
            "Company data consulted",
            company_files,
            help="Select the teacher-provided files used as evidence.",
        )
        evidence = st.text_area("Evidence cited (one item per line)", height=100)
        principles = st.text_input("Management principles applied (comma-separated)")
        submitted = st.form_submit_button("Save turn", type="primary")
        if submitted:
            try:
                turn = sessions.log_turn(
                    session.id,
                    query,
                    response,
                    instruction_refs=instruction_refs,
                    document_refs=document_refs,
                    evidence=split_lines(evidence),
                    principles=split_csv(principles),
                    skill_refs=skill_refs,
                )
                warning = ""
                if not turn.instructions:
                    warning += " No instruction files were cited."
                if not turn.documents:
                    warning += " No company data files were cited."
                flash("success", f"Turn {turn.turn_no} logged." + warning)
                st.rerun()
            except LabError as exc:
                st.error(str(exc))

    with st.expander("Paste a turn JSON (for agent harnesses)"):
        st.caption("Paste the JSON your agent produced. Required keys: query and response.")
        payload_text = st.text_area("Turn JSON", height=230, key="turn_json_payload")
        if st.button("Log JSON turn", key="log_turn_json_button"):
            try:
                payload = json.loads(payload_text)
                if not isinstance(payload, dict):
                    raise LabError("The JSON must be an object.")
                turn = sessions.log_turn(
                    session.id,
                    payload.get("query", ""),
                    payload.get("response", ""),
                    instruction_refs=payload_list(payload.get("instructions") or payload.get("instruction_refs")),
                    document_refs=payload_list(payload.get("documents") or payload.get("document_refs")),
                    evidence=payload_list(payload.get("evidence"), split_commas=False),
                    principles=payload_list(payload.get("principles")),
                    skill_refs=payload_list(payload.get("skills") or payload.get("skill_files")),
                )
                flash("success", f"Turn {turn.turn_no} logged from JSON.")
                st.rerun()
            except json.JSONDecodeError as exc:
                st.error(f"Invalid JSON: {exc}")
            except LabError as exc:
                st.error(str(exc))
            except Exception as exc:
                st.error(f"Could not log this JSON turn: {exc}")


def agent_briefing(session: sessions.Session) -> str:
    return f"""# AI Manager session briefing

You are the **AI Manager** for a university Principles of Management exercise.
The student has written the management instructions; the teacher provided the company data.
This lab does not call an AI model. You are the AI Manager.

## Session
- Session ID: `{session.id}`
- Student: {session.student_name or 'Not provided'}
- Student ID: {session.student_id or 'Not provided'}
- Company: {session.company}
- Course: {session.course}
- Agent / harness: {session.agent or 'Not recorded'}

## Required behaviour
1. Read the student's instruction files before answering and prioritise them over generic advice.
2. Query the teacher-provided company data for factual claims. Never invent figures, employees, or events.
3. Do not modify `teacher_materials/`.
4. Answer with: situation, evidence from company data, instructions applied, analysis, recommendations, risks, and sources.
5. Do not expose private chain-of-thought. Give concise explanations and traceable evidence.
6. Log every turn with the student's exact query and your full response.
7. Keep the conversation context across turns.
8. Built-in skills are optional and invoked-only. Do not read or apply a skill unless the student explicitly names it.

## Student instruction files
{instructions.instructions_digest()}

## Optional built-in skills
{skills.skills_digest()}

## Company data index
{data_store.data_digest()}

## Working commands
```powershell
py tools/lab.py instructions-list
py tools/lab.py instructions-search "sales decline"
py tools/lab.py skills-list
py tools/lab.py skills-read gantt-planner
py tools/lab.py data-list
py tools/lab.py data-summary sales.csv
py tools/lab.py data-query sales.csv --filter "Quarter=2026-Q3" --group-by Channel --metric sum:Revenue --sort Revenue:desc
py tools/lab.py session-context {session.id}
```

## Log this turn
Write a temporary `turn.json` and run:

```powershell
py tools/lab.py log-turn {session.id} --json turn.json
```

```json
{{
  "query": "<the student's exact query>",
  "response": "<your full response>",
  "instructions": ["planning.md", "decision_making.md"],
  "skills": ["gantt-planner"],
  "documents": ["sales.csv", "company_profile.md"],
  "evidence": ["Q3 2026 revenue was $6.60B, down 11.8% year on year."],
  "principles": ["Controlling", "Decision making"]
}}
```

Use the **Log a turn** tab if you cannot run commands. The PDF report is exported from the session log.
"""


def agent_setup_tab(session: sessions.Session) -> None:
    st.markdown("### Connect your AI Manager")
    st.markdown(
        "Use any AI harness that can read files or run terminal commands: Command Code, Claude Code, Cursor, "
        "ChatGPT with uploaded files, or another approved tool. The lab provides the environment; your agent is the AI Manager."
    )
    start_prompt = f"""You are my AI Manager for the AI Manager Learning Lab.

Work in: {config.ROOT}
Read AGENTS.md first and follow it exactly.
My session ID is: {session.id}
My name is: {session.student_name or "<add your name>"}
My student ID is: {session.student_id or "<add your ID>"}

Use the student instruction files in student_instructions/ and the teacher-provided company data in teacher_materials/.
Do not modify teacher_materials/. Do not invent company facts. Cite the files and figures you use.
Built-in skills are optional: if I explicitly name a skill (for example "/gantt-planner"), read only that skill and apply it; otherwise do not read the skill bodies.
Log every turn with my exact query and your full response using:
py tools/lab.py log-turn {session.id} --json turn.json

Start by reading the instructions and data index, then answer my next question.
"""
    st.markdown("**1. Copy this start prompt into your harness**")
    st.code(start_prompt, language="text")
    briefing = agent_briefing(session)
    st.download_button(
        "Download full session briefing",
        data=briefing.encode("utf-8"),
        file_name=f"agent_briefing_{session.id}.md",
        mime="text/markdown",
    )

    st.markdown("**2. Or use the terminal directly**")
    st.code(
        f"""py tools/lab.py instructions-list
py tools/lab.py skills-list
py tools/lab.py data-list
py tools/lab.py session-context {session.id}
py tools/lab.py log-turn {session.id} --json turn.json""",
        language="powershell",
    )

    with st.expander("Full session briefing"):
        st.code(briefing, language="markdown")

    st.markdown("**3. Optional MCP connection**")
    st.markdown(
        "This project includes `.mcp.json`. If your harness supports MCP, enable the `ai-manager-lab` server. "
        "It exposes data, instruction, skill, session, and export tools. The MCP server also contains no AI model."
    )
    st.code(
        f"""py tools/lab.py session-context {session.id}
py tools/lab.py skills-list
py tools/mcp_server.py --check""",
        language="powershell",
    )
    st.info(
        "If your harness cannot run commands, use the Log a turn tab. Paste the exact query and the full AI response; "
        "the PDF is generated from that log."
    )


def export_controls(session: sessions.Session, key_prefix: str) -> None:
    try:
        from lab import pdf_export
    except Exception as exc:
        st.error(f"PDF export is unavailable: {exc}")
        pdf_export = None

    pdf_key = f"pdf::{session.id}::{session.updated_at}"
    zip_key = f"zip::{instruction_fingerprint()}"
    col_a, col_b = st.columns(2)
    if col_a.button("Generate PDF report", type="primary", key=f"pdf_button_{key_prefix}", width="stretch"):
        if pdf_export is None:
            st.error("PDF export is unavailable.")
        else:
            try:
                with st.spinner("Building the session report..."):
                    data = pdf_export.render_session_pdf(session)
                    path = pdf_export.write_session_pdf(session, data)
                st.session_state[pdf_key] = (data, str(path))
                st.success(f"PDF generated: {path.name}")
            except Exception as exc:
                st.error(f"Could not generate the PDF: {exc}")
    if col_b.button("Prepare instruction ZIP", key=f"zip_button_{key_prefix}", width="stretch"):
        try:
            path = zip_export.write_instructions_zip(session=session)
            st.session_state[zip_key] = (path.read_bytes(), str(path))
            st.success(f"ZIP prepared: {path.name}")
        except Exception as exc:
            st.error(f"Could not prepare the ZIP: {exc}")

    if pdf_key in st.session_state:
        data, path = st.session_state[pdf_key]
        st.download_button(
            "Download session PDF",
            data=data,
            file_name=Path(path).name,
            mime="application/pdf",
            key=f"pdf_download_{key_prefix}",
        )
        st.caption(f"Saved in {config.display_path(Path(path))}")
    if zip_key in st.session_state:
        data, path = st.session_state[zip_key]
        st.download_button(
            "Download instruction ZIP",
            data=data,
            file_name=Path(path).name,
            mime="application/zip",
            key=f"zip_download_{key_prefix}",
        )
        st.caption(f"Saved in {config.display_path(Path(path))}")


def finalize_tab(session: sessions.Session) -> None:
    st.markdown("### Session details")
    with st.form("session_metadata_form"):
        col_a, col_b = st.columns(2)
        student_name = col_a.text_input("Student name", value=session.student_name)
        student_id = col_b.text_input("Student ID", value=session.student_id)
        agent = st.text_input("AI Manager / harness", value=session.agent)
        title = st.text_input("Session title", value=session.title)
        if st.form_submit_button("Save session details"):
            try:
                sessions.update_session(
                    session.id,
                    title=title,
                    student_name=student_name,
                    student_id=student_id,
                    agent=agent,
                )
                flash("success", "Session details saved.")
                st.rerun()
            except LabError as exc:
                st.error(str(exc))

    if not session.student_name or not session.student_id:
        st.warning("Add the student name and ID before exporting the PDF for submission.")

    st.markdown("### Final session summary")
    with st.form("session_summary_form"):
        summary = st.text_area(
            "Summary of the session, decisions, and outcomes",
            value=session.summary,
            height=180,
            placeholder=(
                "Summarise the management problem, the instructions you applied, the main recommendations, "
                "and any decisions or follow-up actions."
            ),
        )
        if st.form_submit_button("Save summary"):
            try:
                sessions.save_summary(session.id, summary)
                flash("success", "Session summary saved.")
                st.rerun()
            except LabError as exc:
                st.error(str(exc))
    if not session.summary.strip():
        st.info("The PDF can be generated without a summary, but a final summary makes the submission easier to evaluate.")

    st.markdown("### Session status")
    if session.status == "active":
        col_a, col_b = st.columns([0.35, 0.65])
        if col_a.button("Mark session complete", type="primary", width="stretch"):
            try:
                sessions.finish_session(session.id)
                flash("success", "Session marked complete.")
                st.rerun()
            except LabError as exc:
                st.error(str(exc))
        col_b.caption("Complete the session when you are ready to export the final PDF.")
    else:
        st.success(f"Session completed {sessions.human_time(session.ended_at)}.")
        if st.button("Reopen session"):
            try:
                sessions.update_session(session.id, status="active")
                flash("success", "Session reopened.")
                st.rerun()
            except LabError as exc:
                st.error(str(exc))

    st.divider()
    st.markdown("### Export the two submission files")
    st.markdown(
        "Submit exactly two things: the **PDF session report** and the **ZIP of your Markdown instructions**. "
        "Do not submit code, the database, or the teacher dataset."
    )
    st.caption("Save the session details and summary above before generating the final PDF.")
    export_controls(session, f"finalize_{session.id}")
    st.markdown(
        '<div class="lab-note">The PDF contains the cover fields, session summary, full transcript, sources, evidence, '
        "and principles. The ZIP contains only your active .md instruction files.</div>",
        unsafe_allow_html=True,
    )


def page_ai_manager() -> None:
    hero(
        "Agent-agnostic workspace",
        "AI Manager",
        "Your own AI assistant is the AI Manager. The lab supplies the common company case, your instruction files, "
        "turn logging, and academic exports. No API key and no built-in model.",
    )
    session = active_session()
    if not data_store.list_company_files():
        st.warning(
            f"No company data was found in {config.display_path(config.TEACHER_DIR)}. "
            "Ask the teacher to provide the dataset before the session."
        )
    if not instructions.list_instructions():
        st.warning(
            "No active instruction files yet. Create at least one in the Instructions page so the AI Manager "
            "can apply your own management framework."
        )
    if session is None:
        start_session_form(prominent=True)
        resume_session_form()
        return

    session_header(session)
    with st.expander("Switch session", expanded=False):
        try:
            items = sessions.list_sessions()
        except LabError as exc:
            st.error(str(exc))
            items = []
        if items:
            options = [item.id for item in items]
            selected = st.selectbox(
                "Session",
                options,
                index=options.index(session.id) if session.id in options else 0,
                key="switch_session_selector",
                format_func=lambda session_id: next(
                    (f"{item.title} — {item.id}" for item in items if item.id == session_id), session_id
                ),
            )
            if st.button("Open selected session", key="switch_session_button"):
                try:
                    sessions.set_active_session(selected)
                    flash("success", "Session opened.")
                    st.rerun()
                except LabError as exc:
                    st.error(str(exc))
    if st.session_state.get("show_new_session"):
        start_session_form(prominent=False)

    tabs = st.tabs(["Transcript", "Log a turn", "Agent setup", "Finalize & export"])
    with tabs[0]:
        render_transcript(session)
    with tabs[1]:
        log_turn_tab(session)
    with tabs[2]:
        agent_setup_tab(session)
    with tabs[3]:
        finalize_tab(session)


def page_session_history() -> None:
    hero(
        "Academic record",
        "Session History",
        "Every session is stored locally. Open a session to view its transcript, sources, and exports.",
    )
    try:
        items = sessions.list_sessions()
    except LabError as exc:
        st.error(str(exc))
        return
    if not items:
        st.info("No sessions yet. Start one from the AI Manager page.")
        return
    st.dataframe(
        pd.DataFrame([
            {
                "Session ID": item.id,
                "Title": item.title,
                "Student": item.student_name or "-",
                "Student ID": item.student_id or "-",
                "Turns": item.turn_count,
                "Status": item.status,
                "Updated": sessions.human_time(item.updated_at),
            }
            for item in items
        ]),
        width="stretch",
        hide_index=True,
    )
    options = [item.id for item in items]
    selected = st.selectbox(
        "Open session",
        options,
        key="history_session_selector",
        format_func=lambda session_id: next(
            (f"{item.title} — {item.id} ({item.turn_count} turns)" for item in items if item.id == session_id),
            session_id,
        ),
    )
    try:
        session = sessions.get_session(selected)
    except LabError as exc:
        st.error(str(exc))
        return
    st.divider()
    session_header(session)
    col_a, col_b = st.columns([0.35, 0.65])
    if col_a.button("Set as active session", width="stretch"):
        try:
            sessions.set_active_session(session.id)
            flash("success", "Session set as active.")
            st.session_state["pending_nav"] = "AI Manager"
            st.rerun()
        except LabError as exc:
            st.error(str(exc))
    if session.summary.strip():
        with st.expander("Session summary", expanded=True):
            st.markdown(session.summary)
    tabs = st.tabs(["Transcript", "Sources", "Export"])
    with tabs[0]:
        render_transcript(session)
    with tabs[1]:
        stats = sessions.session_stats(session)
        st.markdown("**Instruction files applied across the session**")
        if stats["instruction_refs"]:
            for name in stats["instruction_refs"]:
                st.markdown(f"- `{name}`")
        else:
            st.caption("None recorded.")
        st.markdown("**Built-in skills applied across the session**")
        if stats["skill_refs"]:
            for name in stats["skill_refs"]:
                st.markdown(f"- `{name}`")
        else:
            st.caption("None recorded.")
        st.markdown("**Company data consulted across the session**")
        if stats["document_refs"]:
            for name in stats["document_refs"]:
                st.markdown(f"- `{name}`")
        else:
            st.caption("None recorded.")
        st.markdown("**Management principles referenced**")
        st.write(", ".join(stats["principles"]) if stats["principles"] else "None recorded.")
    with tabs[2]:
        export_controls(session, f"history_{session.id}")


def page_help() -> None:
    hero(
        "Start here",
        "How the lab works",
        "Same company for every student. Your own management instructions. Your own AI Manager. Two submission files.",
    )
    left, right = st.columns([0.55, 0.45], gap="large")
    with left:
        st.subheader("Quick start")
        st.markdown(
            "1. **Write your instructions.** Go to *Instructions* and create Markdown files with the management "
            "concepts, procedures, and decision rules you want your AI Manager to apply.\n"
            "2. **Start a session.** Go to *AI Manager*, enter your name and student ID, and start a session.\n"
            "3. **Connect your AI Manager.** Use the *Agent setup* tab to copy the briefing into Command Code, "
            "Claude Code, ChatGPT, Cursor, or another approved harness. If your harness cannot run commands, paste "
            "the queries and responses into *Log a turn*.\n"
            "4. **Run a useful session.** Ask management questions, follow up, inspect the company data, and require "
            "your AI Manager to cite your instructions and the company files.\n"
            "5. **Finalise and export.** Add a session summary, then generate the PDF report and the ZIP of your "
            "instruction files from *Finalize & export*.\n"
            "6. **Submit exactly two files.** The PDF and the ZIP. No code, database, or company dataset."
        )
        st.caption(
            "Advanced option: invoke a built-in project-management skill by name (for example `/gantt-planner`). "
            "The skill catalog is below; skills are optional and invoked-only."
        )
        st.subheader("The agent contract")
        st.markdown(
            "- The company data in `teacher_materials/` is common to the whole class and read-only.\n"
            "- The student instructions in `student_instructions/` are the student's own management knowledge.\n"
            "- The AI Manager must prioritise those instructions and cite the company data it uses.\n"
            "- Built-in skills in `builtin_skills/` are optional; the AI Manager reads one only when the student names it.\n"
            "- The lab does not call an AI model and does not store an API key. Your selected harness does the reasoning.\n"
            "- Queries and responses are logged verbatim for the PDF."
        )
        st.subheader("Environment check")
        if st.button("Run environment check"):
            checks = health.run_checks()
            st.dataframe(
                pd.DataFrame([
                    {"Status": check.status.upper(), "Check": check.name, "Detail": check.detail}
                    for check in checks
                ]),
                width="stretch",
                hide_index=True,
            )
            if health.has_failures(checks):
                st.error("One or more required checks failed. Fix those before the session.")
            else:
                st.success("No blocking environment problems were found.")

    with right:
        st.subheader("Copy-paste start prompt")
        st.caption("Use this if you are not using the session-specific prompt on the AI Manager page.")
        st.code(
            f"""You are my AI Manager for the AI Manager Learning Lab.
Work in: {config.ROOT}
Read AGENTS.md first and follow it exactly.
Use my instruction files in student_instructions/ and the teacher-provided
data in teacher_materials/. Do not modify teacher_materials/. Do not invent
company facts. Cite the files and figures you use. Log every turn with my
exact query and your full response using the lab CLI.

Built-in skills are optional. If I name one (for example /gantt-planner),
read only that skill and apply it; otherwise do not read the skill bodies.

Start by listing my instructions and the company data, then answer my query.""",
            language="text",
        )
        st.subheader("Files and folders")
        st.markdown(
            f"- `{config.display_path(config.TEACHER_DIR)}` — teacher data, read-only\n"
            f"- `{config.display_path(config.STUDENT_DIR)}` — your `.md` instructions\n"
            f"- `{config.display_path(config.SKILLS_DIR)}` — optional built-in skills\n"
            f"- `{config.display_path(config.SESSIONS_DIR)}` — local SQLite session history\n"
            f"- `{config.display_path(config.EXPORTS_DIR)}` — generated PDF and ZIP files\n"
            "- `AGENTS.md` — the protocol any AI harness should follow\n"
            "- `.mcp.json` — optional MCP connection"
        )
        st.subheader("Troubleshooting")
        st.markdown(
            "- **No PDF/ZIP:** generate them from *Finalize & export*; both are saved in `exports/`.\n"
            "- **No instruction files in ZIP:** active files must end in `.md` and cannot start with `_`.\n"
            "- **Changed teacher data warning:** the dataset was edited after the teacher manifest was created. "
            "The teacher can refresh it with `py tools/lab.py teacher-manifest --write`.\n"
            "- **Agent cannot run commands:** use the *Log a turn* tab and paste the exact query and response.\n"
            "- **Skill not found:** use the exact skill name from the catalog below; run `py tools/lab.py skills-list`.\n"
            "- **AI tool unavailable:** the environment still works; no API key or cloud service is required by the lab."
        )
        st.subheader("Privacy")
        st.markdown(
            "The lab stores sessions locally in SQLite and exports local files. It never sends data to an AI provider "
            "itself. Your chosen AI harness may have its own data policy; use the tool approved by your course teacher."
        )

    st.divider()
    st.subheader("Built-in project-management skills (optional)")
    st.markdown(
        "Advanced students can invoke a built-in skill by name. Skills are **methods, not mandatory instructions**: "
        "the AI Manager will not read or apply one unless you name it in your query. Your own instruction files and "
        "the company data still take priority."
    )
    st.markdown(
        f"Adapted from [Kimi's 17 AI Project Management Skills]({skills.SKILLS_SOURCE_URL}) and the open-source "
        "projects it references, plus three management extensions. No external integrations are assumed: skills "
        "produce local Markdown analysis and do not connect to Notion, GitHub, TickTick, Lark/Feishu, Obsidian, or calendars."
    )
    catalog = skills.catalog()
    if not catalog:
        st.info("No built-in skills are installed. The core lab still works normally.")
    else:
        st.markdown("**How to invoke a skill**")
        st.code(
            """Use the /gantt-planner skill to build a 90-day recovery schedule from tasks.csv.
Use the /okr-strategist skill to draft Q4 objectives and key results.
Use the /meeting-summarizer skill on the management committee minutes.
Use the /stakeholder-map skill for the inventory data cleanup.""",
            language="text",
        )
        st.dataframe(
            pd.DataFrame([
                {
                    "Skill": f"/{item['name']}",
                    "Category": item["category"],
                    "What it does": item["description"],
                }
                for item in catalog
            ]),
            width="stretch",
            hide_index=True,
        )
        st.caption(
            "Listing a skill does not activate it. The AI Manager reads the skill body only when you explicitly "
            "name the skill in your query."
        )
        grouped: dict[str, list[dict[str, str]]] = {}
        for item in catalog:
            grouped.setdefault(item["category"], []).append(item)
        for category in sorted(grouped):
            with st.expander(f"{category} — {len(grouped[category])} skill(s)"):
                for item in grouped[category]:
                    st.markdown(f"**`/{item['name']}` — {item['title']}**")
                    st.markdown(item["description"])
                    st.caption(f"Use when: {item['triggers']}")
                    st.caption(f"Source: {item['source']}")
                    st.code(f"Use the /{item['name']} skill: <your task>", language="text")
                    st.divider()
        selected_skill = st.selectbox(
            "Preview a skill's full instructions",
            [item["name"] for item in catalog],
            key="help_skill_preview",
            format_func=lambda name: next(
                (f"{item['title']} (`/{item['name']}`)" for item in catalog if item["name"] == name),
                name,
            ),
        )
        with st.expander("Read the selected skill"):
            st.markdown(skills.read_skill_body(selected_skill))
        st.markdown(
            "- Skills are optional and are **not** part of your instruction ZIP.\n"
            "- The PDF records the skills you actually used, separately from your instruction files.\n"
            "- If you want a skill method to apply permanently, adapt it into your own instruction file.\n"
            "- Skills never override the company policies or your own management instructions."
        )


page = sidebar()
show_flash()
if page == "Instructions":
    page_instructions()
elif page == "Company Data":
    page_company_data()
elif page == "AI Manager":
    page_ai_manager()
elif page == "Session History":
    page_session_history()
else:
    page_help()
