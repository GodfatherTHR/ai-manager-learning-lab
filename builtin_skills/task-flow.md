---
name: task-flow
title: Task Flow
category: Task management
source: Adapted from the open-source task-flow, tasknotes, and ticktick-cli skills
triggers: Task list, task board, checklist, blockers, priorities, next actions, work in progress, task lifecycle
description: Turn a messy set of tasks into a prioritized flow with owners, status, dependencies, blockers, and next actions.
---
# Task Flow

**Invocation rule:** Apply this skill only when the student explicitly invokes it or asks for a task board, task breakdown, prioritization, blocker review, or next-action list. Do not auto-apply it to every planning question.

## Purpose

Make work visible and actionable. The skill moves tasks from a vague list into a clear flow: captured, clarified, prioritized, assigned, in progress, blocked, done, and reviewed.

## Inputs

Gather:

- the task list or backlog,
- the outcome each task serves,
- owner roles,
- due dates and dependencies,
- current status and blockers,
- priority criteria.

Use `tasks.csv` where relevant. Do not invent tasks, owners, or deadlines. If a task has no owner, mark it as unassigned.

## Procedure

1. **Capture.** List every task in one place. Remove duplicates.
2. **Clarify.** For each task, state the outcome, definition of done, owner, and due date.
3. **Prioritize.** Use a simple rule such as impact × urgency, or Must/Should/Could. Explain the rule.
4. **Limit work in progress.** Identify tasks that are started but not progressing. Recommend a WIP limit or a focus list.
5. **Expose dependencies.** Mark tasks waiting on a decision, data, supplier, or another team.
6. **Review blockers.** For each blocked task, state the blocker, the owner of the blocker, the escalation route, and the next check.
7. **Define next actions.** Give each active task a concrete next action.
8. **Review the flow.** Identify overload, idle work, and tasks that should be stopped.

## Output format

Provide:

- a task table with task, outcome, owner, priority, status, due date, dependency, blocker, and next action,
- a short focus list,
- blocked items and escalation,
- tasks to stop or defer,
- a review cadence.

## Quality checks

- Every active task has a next action.
- Blocked tasks have an escalation owner.
- Priorities are explained.
- WIP is not hidden.
- No external tool integration is assumed; local Markdown is sufficient.
- The student's instructions and company evidence take precedence.
