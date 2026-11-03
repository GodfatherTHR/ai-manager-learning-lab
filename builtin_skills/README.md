# Built-in Skills

These are **optional, invoked-only** skills for students who want to go beyond the core management instructions. They are adapted for this lab from the project-management skill examples in Kimi's article [17 AI Project Management Skills for Better Project Execution](https://www.kimi.ai/resources/project-management-skills-for-agents) and the open-source projects it references, plus three management extensions.

## Important behaviour

- Skills are **not** student instruction files. They are not discovered by `student_instructions/` and they are not included in the student submission ZIP.
- The AI Manager must **not read or apply a skill automatically**. It reads a skill only when the student explicitly invokes it, for example:
  - `Use the /gantt-planner skill to schedule the inventory recovery plan.`
  - `Run the okr-strategist skill for Q4.`
  - `Apply the stakeholder-map skill to the inventory data cleanup.`
- A skill is a **method**, not a policy override. The student's instructions, the company data, and the company policies still take precedence.
- If a skill asks for data that the lab does not contain, the AI Manager must say what is missing instead of inventing it.
- No external integrations are assumed. Skills produce local Markdown analysis. They do not connect to Notion, GitHub, TickTick, Lark/Feishu, Obsidian, or an external calendar.

## Available skills

| Skill | Category | Use |
| --- | --- | --- |
| `gantt-planner` | Planning and scheduling | Dependency-aware schedule, critical path, float, milestones |
| `timeline-builder` | Planning and scheduling | Chronological milestones and planned-versus-actual history |
| `okr-strategist` | Goals and alignment | Objectives, key results, baselines, targets, alignment, review |
| `project-sizing-guide` | Estimation | Three-point estimates, PERT-style ranges, T-shirt sizing |
| `sprint-plan-builder` | Agile delivery | Capacity-based short-cycle plan, scope, dependencies, definition of done |
| `story-map-builder` | Agile delivery | Outcome-to-deliverable mapping, MoSCoW priority, release slices |
| `work-recap-writer` | Reporting | Weekly or monthly management recap from session evidence |
| `meeting-summarizer` | Meetings and follow-up | Decisions, actions, owners, dates, open questions |
| `task-flow` | Task management | Task lifecycle, prioritization, blockers, next actions |
| `workflow-orchestration` | Execution and learning | Plan, execute, verify, capture lessons, decision log |
| `project-discovery` | Discovery and briefs | Problem, users, assumptions, experiments, MVP, launch |
| `stakeholder-map` | Stakeholder and communication | Interest, influence, attitude, engagement and communication plan |
| `risk-register` | Risk and control | Cause, event, impact, likelihood, mitigation, contingency, trigger |
| `operating-review` | Performance review | Balanced scorecard, variance, decisions, action register |

## File format

Each skill is a Markdown file with simple frontmatter:

```markdown
---
name: skill-name
title: Human-readable title
category: Category
source: Source or adaptation note
triggers: Keywords, phrases, and situations
description: One-line purpose
---
# Skill title

Instructions for the AI Manager...
```

The application reads this metadata for the Help catalog, CLI, and MCP discovery. The skill body is read only when the skill is invoked.

## Adding a skill

Create a new `.md` file in this folder with the frontmatter above. Use a lowercase hyphenated `name`. Run:

```powershell
py tools/lab.py skills-list
py tools/lab.py doctor
```

The skill appears in the Help catalog and in `skills-list`. It remains optional until a student invokes it.

## Logging and the PDF

When a skill is used, log it in the turn's `skills` field:

```json
{
  "query": "Use the /gantt-planner skill for the inventory recovery plan.",
  "response": "...",
  "instructions": ["planning.md"],
  "skills": ["gantt-planner"],
  "documents": ["tasks.csv", "inventory.csv"],
  "evidence": ["..."],
  "principles": ["Planning", "Controlling"]
}
```

The PDF report shows instruction files, built-in skills, and company data separately so the teacher can see exactly what shaped the answer.
