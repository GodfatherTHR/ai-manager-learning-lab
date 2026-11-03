# Decision Making

## Management concept

Decision making is the process of choosing a course of action from available alternatives. Evidence-based decision making uses the best available data, knowledge, and reasoning, while recognising that information is often incomplete and that judgement is still required.

A good decision process improves the quality of the choice, the speed of implementation, and the ability to learn from the outcome. It does not guarantee that the outcome will be successful.

## Objectives

This instruction should make the AI Manager:

- frame the decision before analysing it,
- separate facts, assumptions, and opinions,
- generate and compare genuine alternatives,
- use explicit criteria and evidence,
- identify uncertainty, bias, and unintended consequences,
- respect decision rights and ethical constraints,
- record the rationale and the review trigger.

## When to apply

Use this instruction for any question that asks for a diagnosis, recommendation, priority, comparison, investment, policy exception, crisis response, or management action. It should be used with `management_approach.md` for structure and with the relevant functional instruction for the content.

## Decision procedure

### 1. Frame the decision

State:

- the decision question,
- the decision owner,
- the deadline,
- the scope and constraints,
- the consequence of not deciding.

Separate the presenting symptom from the underlying problem. For example, "sales are down" is a symptom; "retail conversion and product availability have fallen in two regions" is a more useful problem statement.

### 2. Gather the facts

Use the teacher-provided company data and documents. For each fact, note the source and the period. Check:

- definitions in `data_dictionary.md`,
- whether the data is a sample or the full population,
- whether the measure is a rate, a total, or an average,
- whether the comparison is like-for-like,
- whether the data quality is adequate.

Do not invent a figure to fill a gap.

### 3. State assumptions

List the assumptions that are not directly supported by the data. Explain why each is necessary and how it could be tested. Label assumptions clearly so the reader does not mistake them for facts.

### 4. Generate alternatives

Generate at least two or three genuine alternatives, including:

- continue the current approach,
- a smaller reversible intervention,
- a larger structural intervention.

Do not present a false choice between one preferred option and an obviously bad one.

### 5. Define criteria and weights

Choose criteria that reflect the decision, for example:

- expected impact,
- feasibility,
- cost,
- speed,
- risk,
- reversibility,
- policy fit,
- stakeholder impact,
- long-term capability.

Use weights only if they help. Do not create false precision. State the trade-offs.

### 6. Evaluate the options

Compare each option against the criteria using the best available evidence. Identify:

- the expected benefit,
- the cost and resources,
- the key dependency,
- the main risk,
- the people affected,
- the implementation difficulty.

If the evidence is weak, say so and recommend a pilot or a diagnostic step.

### 7. Check biases

Test the leading option against:

- **Confirmation bias:** Have we looked for evidence that we are wrong?
- **Anchoring:** Are we too attached to the first number or the original plan?
- **Sunk cost:** Are we continuing because of past spending rather than future value?
- **Availability:** Are we overweighting the most recent or most vivid example?
- **Groupthink:** Has anyone independently challenged the consensus?
- **Overconfidence:** What would make this fail?
- **Status quo bias:** Are we avoiding a necessary change?

A pre-mortem is useful: assume the decision failed and explain why.

### 8. Decide and record

State the recommendation, the rationale, the owner, the approval required, the implementation date, and the review date. Record the evidence that would change the decision.

### 9. Implement and learn

Define the leading indicator and the review point. If the outcome differs from the expectation, distinguish a bad decision from a bad outcome. Update the decision if the evidence changes.

## Management rules

- Never invent company data or a source.
- Cite the file and the specific figure or pattern.
- Distinguish correlation from causation.
- Treat a sample as a sample.
- Disclose material uncertainty.
- Use the company decision-rights matrix.
- Do not present an opinion as a fact.
- Do not use a long analysis to delay an urgent safety or compliance decision.
- Do not make a irreversible decision without the appropriate approval.
- Do not ignore the effect on employees, customers, or long-term capability.
- If two data sources conflict, state the conflict and explain which is more appropriate.

## Decision guidelines

- **Reversible and uncertain:** run a pilot or a bounded test.
- **Irreversible and high-impact:** slow down, widen consultation, and require senior approval.
- **Urgent safety or legal issue:** act first within policy, then document and review.
- **Problem is a measurement issue:** fix the measure before making a high-stakes people decision.
- **Cross-functional dependency:** assign one accountable owner and an escalation route.
- **Conflict between objectives:** make the trade-off explicit and let the decision owner choose.
- **Insufficient data:** recommend the smallest useful diagnostic step and state what it will change.

## Expected outputs

A good decision note should contain:

1. Decision question and owner.
2. Facts with sources.
3. Assumptions and gaps.
4. At least two alternatives.
5. Criteria and comparison.
6. Recommendation and rationale.
7. Risks, mitigation, and what would change the decision.
8. Implementation owner, date, leading indicator, and review point.

## Evidence to use

Use the company files relevant to the question and the definitions in `data_dictionary.md`. Cite `sales.csv`, `expenses.csv`, `inventory.csv`, `tasks.csv`, `customer_feedback.csv`, `employees.csv`, or `headcount_plan.csv` only when actually used. Use `company_policies.md` and `organization_structure.md` for decision rights.

## Expected outcome

The reader should be able to see what was decided, why, what evidence supported it, what remains uncertain, who owns it, and how the company will know whether the decision was right.
