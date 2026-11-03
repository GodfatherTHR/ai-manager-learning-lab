---
name: operating-review
title: Operating Review
category: Performance review
source: Lab management extension
triggers: Operating review, monthly review, quarterly review, scorecard, KPI, variance, action register, performance meeting
description: Prepare a focused monthly or quarterly operating review with a balanced scorecard, variance analysis, decisions, and actions.
---
# Operating Review

**Invocation rule:** Apply this skill only when the student explicitly invokes it or asks for an operating review, performance review meeting, management scorecard, or monthly/quarterly business review. Do not auto-apply it to every performance question.

## Purpose

Turn a large amount of management data into a short, decision-oriented review. The review should show performance against plan, explain the important variances, and leave with owned actions.

## Inputs

Gather:

- the period and the audience,
- the financial, customer, operational, and people targets,
- actual performance and prior-period comparisons,
- the action register from the previous review,
- the key risks and decisions required,
- the company policy thresholds.

Use `sales.csv`, `expenses.csv`, `inventory.csv`, `tasks.csv`, `customer_feedback.csv`, `employees.csv`, and `headcount_plan.csv` as relevant. Do not invent missing figures.

## Procedure

1. **Set the review question.** State what decisions the meeting must make.
2. **Build a balanced scorecard.** Include:
   - financial: revenue versus target, gross margin, operating expense versus budget;
   - customer: CSAT, NPS, complaints, response time;
   - operational: inventory risk, overstock, service, project delivery;
   - people: active headcount, overtime, attrition, training, performance calibration;
   - risk and compliance: top risks and control actions.
3. **Analyse variances.** Show actual, target, variance, trend, and the main driver. Use the correct sign convention.
4. **Review the previous actions.** Mark each as complete, on track, late, or blocked. Do not ignore unfinished actions.
5. **Focus the discussion.** Select the three to five issues that require a decision or a change of course. Put the rest in an appendix.
6. **Decide.** For each issue, state the decision, owner, date, expected effect, leading indicator, and escalation.
7. **Record the actions.** Use one action register with a single owner and a due date per action.
8. **Set the next review.** State the date, the data cut-off, and what must be reported.

## Output format

Provide:

- a one-page executive summary,
- a balanced scorecard table with actual, target, variance, trend, and source,
- the action register from the previous review,
- decisions and new actions,
- risks and escalations,
- the next review date.

## Quality checks

- The review is decision-oriented, not a data dump.
- Every figure has a source and period.
- Rates are not summed; samples are labelled.
- Actions have owners and dates.
- Unfinished actions are visible.
- The student's instructions and company policies take precedence.
