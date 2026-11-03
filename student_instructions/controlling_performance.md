# Controlling and Performance Evaluation

## Management concept

Controlling is the process of setting standards, measuring actual performance, comparing actual performance with the standard, and taking corrective action. Performance evaluation is the structured assessment of individual, team, and organisational performance against goals.

Control is not only a financial function. It applies to operations, customers, inventory, projects, people, quality, compliance, and risk. The purpose of control is to help the organisation achieve its goals and learn, not to punish people.

## Objectives

This instruction should make the AI Manager:

- define the standard or target before measuring performance,
- use consistent, traceable data,
- analyse variances by segment and trend,
- distinguish a performance problem from a measurement problem,
- recommend corrective action with an owner, date, and control,
- connect individual performance evaluation to organisational goals,
- avoid gaming and unintended consequences.

## When to apply

Use this instruction when the question concerns:

- a performance review or monthly operating review,
- budget or expense variance,
- sales or revenue performance,
- customer service or quality,
- inventory control,
- project delivery,
- individual or team performance evaluation,
- KPI or scorecard design,
- a control failure or governance issue.

It should be used with `planning.md` when the standard comes from a plan and with `decision_making.md` when a corrective action requires a choice.

## Control procedure

### 1. Define the standard

State the measure, the target, the period, the owner, and the data source. A standard should be:

- specific,
- measurable,
- achievable,
- relevant,
- time-bound,
- owned,
- consistent with company policy.

Use both outcome measures (lagging) and leading indicators. Examples of leading indicators include response time, stockout risk, pipeline coverage, training completion, and open critical roles.

### 2. Measure actual performance

Use actual company data. Check:

- the definition of the measure,
- the period and the as-of date,
- whether the data is complete,
- whether the measure is a sum, average, rate, or ratio,
- whether the comparison is like-for-like,
- whether the sample is representative.

Do not sum rates or percentages. Do not compare a monthly figure with an annual target without adjusting.

### 3. Analyse the variance

Calculate:

- absolute variance,
- percentage variance,
- trend over time,
- contribution by segment (region, channel, product line, category, department, project),
- target versus prior period.

Positive expense variance means overspend. Revenue below target is unfavourable. State the sign convention clearly.

### 4. Diagnose the cause

Consider:

- demand or volume,
- price, discount, or mix,
- process or productivity,
- capability or staffing,
- supply or inventory,
- quality or service,
- project dependency,
- data or measurement,
- external factors not in the data.

Do not stop at the first plausible cause. Check at least two.

### 5. Take corrective action

For each material variance, define:

- the action,
- the accountable owner,
- the deadline,
- the expected effect,
- the leading indicator,
- the escalation route.

Avoid corrective actions that simply shift the problem to another period or another team.

### 6. Review and close the loop

Set the review cadence. Confirm whether the action worked. If it did not, diagnose why and adjust. Update the standard if it is no longer valid. Record the lesson.

## Performance evaluation

### 1. Align goals

Individual and team goals should connect to the company plan. Use a small number of meaningful goals. Distinguish outcome goals from behavioural expectations.

### 2. Use evidence

Use documented results, observable behaviour, customer feedback, and agreed standards. Do not rely on a single impression or a recent incident.

### 3. Calibrate

Calibrate ratings across managers to improve consistency and fairness. A defensible distribution is not the same as a forced ranking. An almost uniform distribution across a large population can indicate that goals and ratings are not differentiating performance.

### 4. Give feedback

Feedback should be specific, timely, behavioural, and forward-looking. Separate the person from the behaviour. Agree the next action.

### 5. Manage underperformance

Check whether the issue is clarity, capability, resources, or conduct. Use a documented improvement plan with measurable expectations, support, review dates, and consequences. Follow HR policy.

### 6. Recognise and develop

Recognise specific contributions. Identify development actions for high performers and critical-role successors. Do not assume that a high performance rating automatically means high potential.

## Management rules

- Do not measure without a standard.
- Do not compare unlike periods or definitions.
- Do not sum rates or percentages.
- Do not treat a sample as the full population.
- Do not blame individuals for system problems.
- Do not use a single measure to judge a complex outcome.
- Do not let a dashboard become a substitute for diagnosis.
- Do not set targets that reward gaming or unsafe behaviour.
- Do not use performance ratings for high-stakes decisions without calibration and evidence.
- Do not hide an unfavourable variance; explain it and act.

## Decision guidelines

- **Variance above the policy threshold:** require a written corrective action.
- **Variance repeats:** investigate the root cause and the standard.
- **Project blocked beyond the escalation window:** escalate to the accountable executive.
- **KPI conflict:** make the trade-off explicit and choose a primary measure.
- **Data quality problem:** fix the measure before using it for a people decision.
- **Service failure:** link the corrective action to the customer promise and the process owner.
- **Performance issue:** check goals, capability, resources, and evidence before formal action.

## Expected outputs

A control answer should include:

1. The standard, actual, and variance.
2. A segmented and trend analysis.
3. The likely causes and the evidence.
4. A corrective action table with owner, timing, measure, and escalation.
5. A review cadence.
6. For people questions, a fair performance-evaluation approach.

## Evidence to use

Use `sales.csv` for revenue, target, margin, discount, and returns; `expenses.csv` for budget and actual; `inventory.csv` for stock status and weeks of supply; `tasks.csv` for project status and overdue work; `customer_feedback.csv` for CSAT, NPS, complaints, and response time; `employees.csv` for performance and workforce measures; `headcount_plan.csv` for staffing and training targets; and `company_policies.md` for thresholds and decision rights.

## Expected outcome

The reader should know what standard was set, how actual performance compared, why the gap occurred, what corrective action is required, who owns it, and when it will be reviewed.
