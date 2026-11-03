---
name: project-sizing-guide
title: Project Sizing Guide
category: Estimation
source: Adapted from Kimi's project-sizing-guide skill
triggers: Estimate, three-point estimate, PERT, T-shirt sizing, effort, workload, confidence interval, project sizing
description: Estimate project effort with three-point ranges, PERT-style expected values, confidence bands, and explicit assumptions.
---
# Project Sizing Guide

**Invocation rule:** Apply this skill only when the student explicitly invokes it or asks for an effort estimate, project sizing, three-point estimate, PERT, T-shirt sizing, or a confidence range. Do not auto-apply it to every plan.

## Purpose

Provide a defensible effort range instead of a false-precision single number. The skill is useful for management projects, process changes, system implementations, and cross-functional initiatives.

## Inputs

Gather:

- the project scope and deliverables,
- the work breakdown or task list,
- the team capacity and skills,
- historical effort or velocity data if available,
- dependencies and approvals,
- known uncertainty and constraints.

If historical data is missing, state that the estimate is judgement-based. Do not invent productivity or velocity data.

## Procedure

1. **Define the scope.** State what is included and excluded. A estimate without a boundary is not useful.
2. **Decompose the work.** Break the project into deliverables and tasks small enough to estimate.
3. **Estimate three points.** For each task, provide:
   - optimistic,
   - most likely,
   - pessimistic.
4. **Calculate the expected value.** Use the PERT approximation: `(optimistic + 4 × most likely + pessimistic) / 6`.
5. **Estimate uncertainty.** Show the range and, where useful, a rough standard deviation: `(pessimistic − optimistic) / 6`. Do not imply statistical precision that the inputs do not support.
6. **Add T-shirt sizing.** Label tasks or deliverables as S, M, L, or XL for quick comparison.
7. **Check capacity.** Compare the estimate with available people, skills, and competing commitments.
8. **Identify assumptions and risks.** State what would make the estimate move materially.
9. **Recommend a planning range.** Give a most-likely range and a contingency rather than a single date.

## Output format

Provide:

- a task table with optimistic, most likely, pessimistic, expected, and T-shirt size,
- the total expected effort and range,
- capacity and dependency notes,
- assumptions,
- top estimation risks,
- a recommended planning range.

## Quality checks

- The estimate is not presented as a guarantee.
- The scope is explicit.
- The units are clear: person-days, weeks, or another unit.
- Capacity is not assumed to be unlimited.
- Historical data, if used, is cited.
- The output does not invent team velocity or market data.
- The student's instructions and company constraints take precedence.
