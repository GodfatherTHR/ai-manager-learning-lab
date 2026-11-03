# AI Manager Learning Lab

A local, agent-agnostic environment for a university **Principles of Management** assignment.

Every student receives the **same fictional company case** from the teacher. Each student writes their own Markdown management instructions, connects their own AI assistant as the **AI Manager**, runs a management session against the common data, and exports a professional PDF report plus a ZIP of their instruction files.

> **This build does not contain an AI model, does not call Gemini, and does not need an API key.** The student's chosen AI harness is the AI Manager. The lab provides the company data, student instructions, session logging, and academic exports. This is deliberate: students can use Command Code, Claude Code, Cursor, ChatGPT, or another approved tool, and the environment remains the same.

## What is included

- A read-only common company case in `teacher_materials/`.
- A student instruction workspace in `student_instructions/`.
- An agent protocol in `AGENTS.md` that any harness can follow.
- An optional, invoked-only skill library in `builtin_skills/` for advanced project management.
- A CLI bridge (`tools/lab.py`) for data queries, instruction discovery, session logging, and exports.
- An optional MCP server (`tools/mcp_server.py`) for MCP-capable harnesses.
- A Streamlit lab console (`app.py`) with:
  - Markdown instruction editor, upload, examples, rename, delete.
  - Read-only company data browser and safe quick filters.
  - Session workspace with transcript, turn logging, agent briefing, and finalisation.
  - Session history.
  - PDF session report and instruction ZIP export.
- A visible demo company case built around the supplied employee dataset.
- An environment doctor that checks data, packages, database, writability, and PDF fonts.

## Quick start (Windows)

Open a terminal in the project folder.

```powershell
py -m pip install -r requirements.txt
py -m streamlit run app.py
```

If `py` is not available, use `python` or `python3` instead.

On Windows, you can also double-click `setup.bat` once, then double-click `run.bat` to start the lab.

The app opens in your browser. No API key or `.env` file is required.

Run the environment check at any time:

```powershell
py tools/lab.py doctor
```

## The student workflow

1. **Write your management instructions.** Go to **Instructions** and create one or more `.md` files. Write your own management concepts, objectives, procedures, rules, and decision guidelines.
2. **Start a session.** Go to **AI Manager**, enter your name and student ID, choose your AI harness, and start a session.
3. **Connect your AI Manager.** Use **AI Manager → Agent setup**:
   - Copy the session-specific start prompt into your AI harness.
   - Or use the CLI/MCP tools directly.
   - If your harness cannot run commands, paste its response into **Log a turn**.
4. **Run a useful session.** Ask management questions, follow up, and require the AI Manager to cite your instruction files and the company data.
5. **Add a final summary.** Use **Finalize & export** to record the decisions, recommendations, and follow-up actions.
6. **Export two files.** Generate the **PDF session report** and the **instruction ZIP**. Submit exactly those two files.

## How the AI Manager knows what to do

The protocol is in [`AGENTS.md`](AGENTS.md). In short, the AI Manager must:

- Prioritise the student's Markdown instructions over generic advice.
- Use the teacher-provided company data for factual claims.
- Cite the file names and figures it used.
- Never invent company information.
- Keep the session context across follow-up questions.
- Log the student's exact query and its full response.
- Avoid exposing private chain-of-thought.

The Streamlit app does not send data to an AI provider. Your chosen harness may have its own data policy; use the tool approved by your course teacher.

## Optional built-in skills

The `builtin_skills/` folder contains 14 optional skills for students who want to go further as a top-level manager. They are **not** student instructions and are **not** read automatically. The AI Manager reads a skill body only when the student explicitly invokes it by name:

```text
Use the /gantt-planner skill to build a 90-day recovery schedule from tasks.csv.
Use the /okr-strategist skill to draft Q4 objectives and key results.
Use the /stakeholder-map skill for the inventory data cleanup.
```

The catalog includes:

- planning and scheduling: `gantt-planner`, `timeline-builder`
- goals and alignment: `okr-strategist`
- estimation: `project-sizing-guide`
- agile delivery: `sprint-plan-builder`, `story-map-builder`
- reporting: `work-recap-writer`
- meetings: `meeting-summarizer`
- task management: `task-flow`
- execution and learning: `workflow-orchestration`
- discovery: `project-discovery`
- stakeholder communication: `stakeholder-map`
- risk and control: `risk-register`
- performance review: `operating-review`

The full catalog, triggers, source notes, and copyable invocation examples are in **Help → Built-in project-management skills** in the app. Skills are adapted from [Kimi's 17 AI Project Management Skills](https://www.kimi.ai/resources/project-management-skills-for-agents) and the open-source projects it references, plus three management extensions. No external integrations are assumed; skills produce local Markdown analysis.

When a skill is used, it is logged separately in the turn's `skills` field and shown separately from instruction files in the PDF.

## Session logging and the PDF

A session is stored locally in `sessions/lab.db`. Each turn records:

- The student's exact query.
- The AI Manager's full response.
- The instruction files applied.
- The built-in skills invoked, if any.
- The company data files consulted.
- The evidence points cited.
- The management principles referenced.
- The timestamp.

The PDF report contains a cover page with the student name, student ID, course, company, session date, and agent/harness; a session summary; the full chronological transcript; separate traces for instruction files, built-in skills, and company data; evidence; and a submission declaration. The ZIP contains only active `.md` instruction files.

## Using a terminal-capable harness

From the project root, a harness can run:

```powershell
py tools/lab.py doctor
py tools/lab.py instructions-list
py tools/lab.py skills-list
py tools/lab.py skills-read gantt-planner
py tools/lab.py data-list
py tools/lab.py data-summary sales.csv
py tools/lab.py data-query sales.csv --filter "Quarter=2026-Q3" --group-by Channel --metric sum:Revenue --sort sum_Revenue:desc
py tools/lab.py session-context <session-id>
py tools/lab.py log-turn <session-id> --json sessions/turn.json
py tools/lab.py export-pdf <session-id>
py tools/lab.py export-zip <session-id>
```

The CLI is read-only on teacher data. It validates instruction and data references when a turn is logged, so a typo in a source file is caught immediately.

### Recommended turn JSON

Write `sessions/turn.json` with UTF-8 content:

```json
{
  "query": "The student's exact question",
  "response": "The AI Manager's full response",
  "instructions": ["planning.md", "decision_making.md"],
  "skills": ["gantt-planner"],
  "documents": ["sales.csv", "company_profile.md"],
  "evidence": [
    "Q3 2026 revenue was $6.60B, down 11.8% year on year.",
    "Retail Stores revenue fell 19.6% while E-commerce grew 3.3%."
  ],
  "principles": ["Controlling", "Decision making"]
}
```

Then:

```powershell
py tools/lab.py log-turn <session-id> --json sessions/turn.json
```

Use a JSON file instead of long command-line arguments. Windows command-line quoting is fragile.

## Using an MCP-capable harness

The project includes `.mcp.json` with an `ai-manager-lab` server. If your harness supports MCP, enable it. The server exposes company data, instructions, sessions, and exports as tools, and contains no AI model.

Check the server locally:

```powershell
py tools/mcp_server.py --check
```

If your harness does not use `py`, change the command in `.mcp.json` to `python` or your environment's Python executable.

## Usage without a terminal (chat-only harness)

1. Upload the company files and your instruction files to your AI tool.
2. Ask your questions.
3. Copy the exact query and the full response into **AI Manager → Log a turn**.
4. Select the instruction files and company files that were actually used, and add evidence and principles.
5. Export the PDF and ZIP.

The lab does not care which AI tool produced the response. It cares about the traceability of the session.

## Teacher workflow

1. Replace the contents of `teacher_materials/` with the class dataset. Keep the folder name.
2. Keep UTF-8 CSV tables with header rows and Markdown documents. The app discovers files automatically.
3. Put the company name in the first Markdown heading of `company_profile.md` (for example `# Meridian Consumer Group, Inc.`).
4. Refresh the integrity manifest:

   ```powershell
   py tools/lab.py teacher-manifest --write
   ```

5. Run the environment check and start the app:

   ```powershell
   py tools/lab.py doctor
   py -m streamlit run app.py
   ```

6. For a fresh class, remove `sessions/lab.db`, `sessions/ACTIVE_SESSION`, and generated files in `exports/`. Keep `teacher_materials/` and leave `student_instructions/` empty for the student distribution.

The detailed teacher notes are in [`teacher_materials/README.md`](teacher_materials/README.md).

## Demo company case

The supplied employee dataset is `Extended_Employee_Performance_and_Productivity_Data.csv`. It remains at the project root as the source for the demo generator, and the canonical copy for students is `teacher_materials/employees.csv` (100,000 anonymised records). The other demo files are a clearly labelled fictional case generated around it:

- **Meridian Consumer Group, Inc.** — an omnichannel consumer-products company.
- FY2025 revenue $30.09B; Q3 2026 revenue down 11.8% year on year.
- 89,990 active employees; $576.3M monthly active payroll.
- 50 of 72 sampled SKU–warehouse inventory lines below reorder point or safety stock.
- CSAT down from 80.4 to 71.5; complaints up.
- 30 management tasks, including 3 blocked and 1 past due.

The case is deliberately difficult and includes measurement problems, cross-functional dependencies, and cost pressure. It is a teaching dataset, not a real company.

Regenerate the demo CSVs:

```powershell
py scripts/generate_demo_data.py --force
```

## Project structure

```text
POM/
├── app.py                          Streamlit lab console
├── run.bat                         Windows launcher
├── setup.bat                       Windows dependency installer
├── AGENTS.md                       Protocol for any AI Manager harness
├── AI_MANAGER_START_PROMPT.md       Manual start prompt
├── CLAUDE.md                       Claude Code pointer to AGENTS.md
├── .cursor/rules/                  Cursor rule pointer
├── .mcp.json                       Optional MCP server configuration
├── requirements.txt
├── README.md
├── lab/                            Core services (data, instructions, sessions, PDF)
├── tools/
│   ├── lab.py                      CLI bridge
│   └── mcp_server.py               Optional MCP server
├── teacher_materials/              Common read-only company case
├── student_instructions/           Student workspace (empty in the student ZIP)
├── builtin_skills/                 Optional invoked-only management skills
├── sessions/                       SQLite history and active session pointer
├── exports/                        Generated PDF and ZIP files
└── scripts/
    └── generate_demo_data.py       Demo case generator
```

The student distribution ZIP is built with a genuinely empty `student_instructions/` folder. A working source copy may contain optional examples or test files; those are not included in the student ZIP.

## Command reference

```powershell
py tools/lab.py doctor
py tools/lab.py data-list
py tools/lab.py data-show company_profile.md
py tools/lab.py data-summary employees.csv
py tools/lab.py data-query expenses.csv --filter "Month>=2026-01" --group-by Category --metric sum:Budget --metric sum:Actual --metric sum:Variance --sort sum_Variance:desc
py tools/lab.py instructions-list
py tools/lab.py instructions-search "sales decline control"
py tools/lab.py instructions-read planning.md
py tools/lab.py skills-list
py tools/lab.py skills-read gantt-planner
py tools/lab.py session-new --student-name "A. Student" --student-id "2026-001" --agent "Command Code"
py tools/lab.py session-list
py tools/lab.py session-context latest
py tools/lab.py log-turn latest --json sessions/turn.json
py tools/lab.py session-update latest --summary-file summary.txt
py tools/lab.py session-finish latest
py tools/lab.py export-pdf latest
py tools/lab.py export-zip latest
py tools/lab.py teacher-manifest --write
```

## Troubleshooting

**`python` opens the Microsoft Store or is not found.** Use the Windows Python launcher: `py`. The app and CLI work with `py`.

**A package is missing.** Run `py -m pip install -r requirements.txt` again. The optional MCP server needs the `mcp` package; the rest of the lab works without it.

**No company data appears.** Confirm that `teacher_materials/` exists and contains readable `.md`/`.csv` files. Run `py tools/lab.py doctor`.

**A CSV is rejected.** Check that it is UTF-8, has a header row, and has consistent delimiters. Run `py tools/lab.py data-summary <file>` for the error.

**The PDF takes a moment.** ReportLab is rendering the full transcript. Large sessions produce larger PDFs.

**The ZIP is empty.** Active instruction files must end in `.md` and cannot start with `_`. `README.md` and `_examples/` are ignored by the app and are not included in the student distribution ZIP.

**The teacher-data warning appears.** The dataset was edited after the manifest was created. The teacher can refresh it with `py tools/lab.py teacher-manifest --write`.

**The AI harness cannot run commands.** Use the **Log a turn** tab. The session record is still complete if the query, response, sources, and evidence are entered.

**A skill name is rejected.** Use the exact name from **Help → Built-in project-management skills** or run `py tools/lab.py skills-list`. Skills are optional; leave the `skills` field empty when no skill was invoked.

**A session is stuck or the database is locked.** Close other app/CLI processes and retry. SQLite uses WAL mode for local concurrency.

**I want a fresh class.** Stop the app, remove `sessions/lab.db`, `sessions/ACTIVE_SESSION`, and the generated files in `exports/`, then restart. This deletes local session history; keep any submitted exports first.

## Privacy and academic integrity

- The lab is local-first. It does not send data to an AI provider.
- No API key is stored or required.
- Teacher data is read-only in the app. The manifest warns if files change after distribution.
- Student instructions are assessed work. Do not submit the optional examples unchanged.
- The PDF reproduces the student's queries verbatim and the AI responses as logged. Do not edit the log to change the substance of the session.
- The chosen AI harness's data policy is outside this lab. Use the tool approved by the course teacher.

## License and use

This is a teaching environment, not production software. The demo company and generated CSVs are fictional. Do not use the company data for real employment, financial, or operational decisions.
