---
name: sprint-plan-builder
title: Sprint Plan Builder
category: Agile delivery
source: Adapted from Kimi's sprint-plan-builder and sprint-planning skills
triggers: Sprint, iteration, capacity, backlog, velocity, workload balancing, agile planning, two-week plan
description: Build a capacity-based sprint or delivery-cycle plan with scope, owners, dependencies, and a clear definition of done.
---
# Sprint Plan Builder

**Invocation rule:** Apply this skill only when the student explicitly invokes it or asks for a sprint plan, iteration plan, capacity-based scope, or workload-balanced delivery cycle. Do not auto-apply it to every project.

## Purpose

Create a realistic short-cycle plan. The skill helps a manager choose what can be delivered with available capacity, expose dependencies, balance workload, and commit to a sprint goal.

## Inputs

Gather:

- the delivery or improvement goal,
- the candidate backlog or tasks,
- team capacity in person-days or hours,
- available roles and skills,
- historical velocity if available,
- dependencies and approval gates,
- definition of done.

Use `tasks.csv` and `headcount_plan.csv` when relevant. If velocity is unavailable, state the assumption and treat the plan as provisional.

## Procedure

1. **Set the sprint goal.** One outcome, not a list of activities.
2. **Calculate capacity.** Subtract leave, meetings, support duties, and non-project work. Do not assume 100% availability.
3. **Select scope.** Choose items by value, risk, and dependency. Avoid filling capacity to the maximum; leave a buffer for unplanned work.
4. **Break down items.** Convert each selected item into tasks with an owner and an estimate.
5. **Check dependencies.** Identify external decisions, approvals, data, or supplier inputs.
6. **Balance workload.** Check individual and team load; flag overallocation.
7. **Define done.** State the acceptance criteria, review, and hand-off.
8. **Identify risks and blockers.** Include a mitigation and escalation route.
9. **Set the review.** State the daily or weekly check-in, the demo or review, and the retrospective.

## Output format

Provide:

- the sprint goal,
- a capacity table,
- a sprint backlog with item, owner, estimate, dependency, and acceptance criteria,
- workload and dependency risks,
- definition of done,
- review and retrospective dates,
- assumptions.

## Quality checks

- Capacity is realistic and explicit.
- The plan includes non-project work and support duties.
- Dependencies are visible.
- The sprint goal is an outcome, not a task list.
- The plan does not assume unlimited overtime.
- The student's instructions and company constraints take precedence.
- No external tracker integration is assumed; use local Markdown unless the environment provides a tool.
