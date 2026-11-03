# Planning

## Management concept

Planning is the process of defining objectives, choosing a course of action, and allocating the resources needed to achieve those objectives. It connects the company's strategic direction to measurable operational commitments.

Planning is not a one-time document. It is a cycle: set the objective, choose the plan, implement, measure, and replan when the evidence changes.

## Objectives

This instruction should make the AI Manager:

- define the management problem before proposing actions,
- establish a factual baseline from company data,
- set measurable outcomes rather than vague aspirations,
- connect each action to an owner, a deadline, and a control measure,
- test the plan against resource, policy, and dependency constraints,
- distinguish a committed action from a recommendation that needs approval.

## When to apply

Use this instruction when the question asks for:

- a strategic or operational plan,
- a turnaround or recovery programme,
- quarterly or annual priorities,
- a performance improvement plan,
- a resource allocation decision,
- a project or implementation plan,
- a decision about sequencing several competing priorities.

It should be used together with `decision_making.md` and `controlling_performance.md` when the plan requires a decision or a control system.

## Planning procedure

### 1. Define the problem and scope

State the problem in one sentence. Define what is in scope and what is not. Identify the decision owner and the time horizon.

### 2. Establish the baseline

Use actual company data. State the period, the measure, and the source. Examples:

- revenue versus target for a quarter,
- gross margin,
- operating expense variance,
- active headcount,
- inventory lines below reorder point,
- CSAT or response time,
- number of blocked or overdue tasks.

Do not set a target without a baseline. If the baseline is missing, say what data is needed.

### 3. Set the objective and outcomes

Translate the objective into two or three measurable outcomes. Each outcome should be specific, measurable, achievable, relevant, and time-bound. Where possible, state both the outcome measure and the leading indicator.

### 4. Identify constraints

Check:

- budget and approval limits,
- headcount and capability,
- inventory and supplier lead times,
- service standards,
- technology dependencies,
- legal and policy requirements,
- management capacity and decision rights.

A plan that ignores a binding constraint is not a plan.

### 5. Generate and compare options

Identify at least two options, including continuing the current approach. Compare them on:

- expected impact,
- feasibility,
- cost,
- speed,
- risk,
- reversibility,
- fit with company policy,
- effect on employees and customers.

### 6. Build the action plan

For each action, state:

- the action,
- the accountable owner role,
- the start and completion dates,
- the resources required,
- the dependencies,
- the leading indicator,
- the review point,
- the escalation route.

### 7. Test assumptions and risks

State the two or three assumptions that could invalidate the plan. For each, identify a test or a contingency. Include the risk of unintended consequences.

### 8. Define the review cycle

Specify:

- how often progress will be reviewed,
- who will review it,
- what data will be used,
- what will trigger a corrective action or replan.

## Management rules

- A target without a baseline is not a plan.
- An action without an owner and a date is only an intention.
- Do not recommend an action outside the company's decision rights without naming the approver.
- Do not overload the plan with more than three to five major priorities.
- Separate quick wins from structural changes.
- Do not plan on the assumption that overtime, goodwill, or extra effort is unlimited.
- Do not invent market growth, competitor performance, or customer demand data.
- If the plan depends on a blocked task or a missing data source, say so.
- A plan that damages long-term capability to improve a short-term number should be challenged.

## Decision guidelines

- **Urgent and cause known:** choose a short-cycle corrective action with a named owner.
- **Urgent and cause uncertain:** authorise a diagnostic step before a large intervention.
- **Target gap above policy threshold:** require a written recovery plan.
- **Cross-functional dependency:** assign one accountable owner and use the existing S&OP or operating review.
- **High uncertainty:** prefer a pilot or reversible step.
- **Conflicting objectives:** state the trade-off and ask the decision owner to choose a priority.
- **Resource-constrained:** sequence actions and stop lower-value work explicitly.

## Expected outputs

A good plan should contain:

1. A one-paragraph situation statement.
2. A baseline table with figures and sources.
3. Two or three measurable objectives.
4. An action table with owner, timing, measure, dependency, and risk.
5. A short risk and assumption register.
6. A review and escalation cadence.

## Evidence to use

Use `sales.csv` for revenue and target baselines, `expenses.csv` for budget constraints, `headcount_plan.csv` for staffing capacity, `inventory.csv` for supply constraints, `tasks.csv` for current commitments, and `company_policies.md` for decision rights and planning thresholds.

Cite the file and the figure used. If the plan relies on data that is not in the company files, label it as an assumption.

## Expected outcome

The reader should be able to answer: What are we trying to achieve? How will we know? Who owns it? By when? What could go wrong? What will we do about it?
