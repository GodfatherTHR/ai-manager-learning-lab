---
name: timeline-builder
title: Timeline Builder
category: Planning and scheduling
source: Adapted from Kimi's timeline-builder skill
triggers: Timeline, milestones, project history, release log, chronological sequence, chronology
description: Organize events, milestones, and decisions into a clear chronological timeline with planned versus actual dates.
---
# Timeline Builder

**Invocation rule:** Apply this skill only when the student explicitly asks for a timeline, chronology, milestone history, release log, or chronological visualization. Do not auto-apply it to every planning question.

## Purpose

Create a readable chronological view of a project, change programme, or management case. The timeline helps the student see sequence, delay, dependencies, and decision points.

## Inputs

Gather:

- the period covered,
- events, milestones, decisions, and delivery dates,
- planned dates versus actual dates,
- owners or decision forums,
- the source of each date.

Use `tasks.csv`, the management committee minutes, session decisions, and company documents. If a date is unknown, mark it as unknown rather than inventing one.

## Procedure

1. **Define the timeline scope.** State the start, end, audience, and purpose.
2. **Collect dated events.** Separate facts from planned dates and estimates.
3. **Group the events.** Use phases such as diagnosis, design, approval, implementation, and review.
4. **Identify milestones and decisions.** Distinguish a task, a milestone, and a decision.
5. **Show planned versus actual.** Highlight delays, accelerations, and missed gates.
6. **Add context.** For each major item, state why it matters and what depends on it.
7. **Summarize the pattern.** Identify the main sequence, bottlenecks, and upcoming deadlines.

## Output format

Provide:

- a chronological table with date, event, type, owner or forum, status, and source,
- a short phase summary,
- the next three milestones,
- delays or risks,
- assumptions where dates are incomplete.

If a visual is requested, a Markdown or Mermaid timeline is sufficient. An optional self-contained HTML timeline can be written to `exports/` if the harness supports files.

## Quality checks

- Every date is sourced or labelled as planned/assumed.
- Planned and actual dates are not mixed without a label.
- The timeline does not invent events or decisions.
- The sequence is consistent with dependencies.
- The summary distinguishes what happened from what is planned.
- The student's instructions and company evidence remain authoritative.
