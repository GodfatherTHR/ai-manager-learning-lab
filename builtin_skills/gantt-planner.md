---
name: gantt-planner
title: Gantt Planner
category: Planning and scheduling
source: Adapted from Kimi's gantt-planner skill
triggers: Gantt chart, critical path, task dependencies, project schedule, milestones, float, timeline
description: Build a dependency-aware project schedule, calculate float, and identify the critical path and milestones.
---
# Gantt Planner

**Invocation rule:** Apply this skill only when the student explicitly asks for it by name or clearly requests a Gantt chart, critical-path analysis, or dependency-based schedule. Do not auto-apply it to every planning question.

## Purpose

Turn a list of project tasks into a practical schedule. The skill identifies task order, dependencies, duration, float, milestones, and the critical path so the student can see where delay would affect the final date.

## Inputs

Collect or infer from the company case:

- the project objective and required finish date,
- tasks with owners and estimated durations,
- dependencies between tasks,
- milestones and approval gates,
- resource constraints and known blackout dates,
- assumptions where duration or effort is uncertain.

Use `tasks.csv` for existing project commitments. If durations or dependencies are missing, state the assumption or ask for them; do not invent precise dates.

## Procedure

1. **Clarify the scope.** State the project outcome, start date, finish date, and what is excluded.
2. **List the tasks.** Give each task an ID, name, owner role, duration, and dependencies. Include milestones as zero-duration items.
3. **Check the logic.** Remove circular dependencies. Distinguish mandatory dependencies from preferred sequencing.
4. **Calculate the schedule.** Determine earliest start/finish and latest start/finish for each task. Calculate float.
5. **Identify the critical path.** The critical path is the longest dependency chain; tasks on it have zero or minimum float. Explain what happens if a critical task slips.
6. **Check resources and constraints.** Identify tasks that require the same scarce role or approval. Flag unrealistic parallel work.
7. **Add milestones and review gates.** Show decision points, approvals, and go/no-go checks.
8. **Present the schedule.** Use a table with ID, task, owner, duration, start, finish, dependencies, float, and critical-path flag.
9. **State assumptions and risks.** List the assumptions that determine the dates and the top schedule risks.

## Output format

Provide:

- a one-paragraph schedule summary,
- the task table,
- the critical path in order,
- milestones and review gates,
- top schedule risks and mitigations,
- assumptions.

If the student asks for a visual and the harness can write files, optionally produce a self-contained HTML Gantt in `exports/`. Otherwise, a clear Markdown table is sufficient.

## Quality checks

- The critical path is complete and consistent with the dependency table.
- Durations and dates are not presented as facts when they are estimates.
- Resource conflicts are visible.
- The schedule respects approval gates and company decision rights.
- The student's instructions and the company data take precedence over this skill.
- The output does not invent tasks, owners, or dates that are not supported.
