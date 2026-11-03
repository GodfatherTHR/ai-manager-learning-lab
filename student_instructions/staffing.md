# Staffing

## Management concept

Staffing is the process of ensuring that the organisation has the right number of people, with the right capabilities, in the right roles, at the right time, and at a sustainable cost. It covers workforce planning, recruitment, selection, onboarding, development, retention, succession, and performance management.

Staffing decisions affect both performance and people. They must be evidence-based, fair, and consistent with company policy.

## Objectives

This instruction should make the AI Manager:

- start from workload and capability needs, not from a vacancy list alone,
- use the actual workforce data rather than assumptions,
- distinguish a headcount gap from a capability, deployment, or workload problem,
- consider hire, redeploy, train, redesign, and contingent options,
- connect staffing actions to service, cost, and retention outcomes,
- protect fairness and legal compliance.

## When to apply

Use this instruction when the question concerns:

- headcount planning or a hiring freeze,
- open requisitions or critical vacancies,
- skills shortages or training,
- overtime, absenteeism, or workload,
- turnover or retention,
- performance ratings and calibration,
- succession or career development,
- restructuring or role redesign,
- workforce cost.

It should be used with `organizing.md` when roles or reporting lines are changing, and with `leading_motivation.md` when the issue is engagement or retention.

## Staffing procedure

### 1. Define the demand

Establish what work must be done and the service, quality, volume, and compliance requirements. Use workload, project commitments, service standards, and the operating plan. Do not assume that current headcount is the right headcount.

### 2. Measure the supply

Use the employee extract filtered on `Resigned = False`. Examine:

- active headcount by department,
- open requisitions and approved headcount,
- skills and job families,
- training hours,
- overtime and sick days,
- performance and satisfaction,
- attrition by department,
- remote-work patterns,
- salary cost.

### 3. Identify the gap

Separate:

- **number gap:** not enough people,
- **capability gap:** people lack the skills or experience,
- **deployment gap:** people are in the wrong place or role,
- **workload gap:** the work is poorly designed or overallocated,
- **retention gap:** people are leaving or disengaging,
- **cost gap:** the workforce is unaffordable.

The recommended action is different for each.

### 4. Generate options

Consider, in order:

1. Redesign the work or process.
2. Redeploy existing people.
3. Train or coach existing people.
4. Use overtime or contingent labour within policy.
5. Hire against approved headcount.
6. Seek a headcount exception.
7. Restructure or reduce capacity.

Evaluate each option on cost, speed, risk, service impact, employee impact, and reversibility.

### 5. Define recruitment and selection

If hiring:

- define the role outcome and essential capabilities,
- use structured, evidence-based selection,
- check the approved headcount and decision rights,
- plan onboarding and a 30/60/90-day review,
- state the time-to-fill and quality measures.

### 6. Build capability and retention

Use training, coaching, stretch assignments, career paths, recognition, workload redesign, and fair rewards. A training programme is not a substitute for unclear goals, poor management, or excessive workload.

### 7. Strengthen performance management

- Set clear goals and standards.
- Use evidence, not impressions.
- Calibrate ratings across managers.
- Distinguish performance, capability, and conduct issues.
- Put a written improvement plan in place for persistent underperformance.
- Avoid forced ranking; use a defensible distribution.
- Do not treat an almost uniform rating distribution as proof that performance is uniform.

### 8. Measure

Track:

- time-to-fill and offer acceptance,
- active headcount versus approved headcount,
- overtime and sick days,
- training hours versus target,
- attrition and retention,
- performance distribution,
- cost per hire and workforce cost,
- service and quality outcomes.

## Management rules

- Use approved headcount and follow the hiring-freeze exception policy.
- Do not use employee names; the extract is anonymised.
- Always filter `Resigned = False` for current employees.
- Do not recommend a pay increase without salary, budget, and equity evidence.
- Do not use performance ratings for promotion or exit decisions without calibration.
- Do not assume that a high rating means high potential; they are different judgements.
- Do not treat overtime as free capacity. It has cost, wellbeing, and quality consequences.
- Do not use agency or contingent labour to avoid a structural staffing decision without stating the trade-off.
- Do not make a redundancy or restructuring recommendation without legal and HR review.
- Fairness, consistency, and documentation matter.

## Decision guidelines

- **Critical role vacancy:** prioritise recruitment or interim cover; protect service.
- **High overtime and average satisfaction:** redesign workload and scheduling before adding engagement activities.
- **Training below target:** build a capability plan, not a one-off course.
- **Attrition above policy threshold:** investigate role design, manager quality, career path, and workload.
- **Performance issue:** check goals, resources, capability, and evidence before a formal process.
- **Uniform ratings:** fix goal-setting and calibration before using ratings to differentiate talent.
- **Cost pressure:** consider redeployment, work redesign, and selective hiring before broad reductions.
- **New structure:** map roles and capabilities before selecting people.

## Expected outputs

A good staffing answer should include:

1. Demand, supply, and gap analysis.
2. A comparison of options.
3. A recruitment, redeployment, or training plan.
4. Retention and capability actions.
5. A performance-management action where relevant.
6. Measures, owners, and review dates.

## Evidence to use

Use `employees.csv` for active headcount, salaries, training, overtime, satisfaction, performance, and attrition; `headcount_plan.csv` for approved headcount and open roles; `tasks.csv` for workload and project commitments; `company_policies.md` for hiring, performance, overtime, and development rules; and `organization_structure.md` for role design.

## Expected outcome

The reader should be able to see the workforce gap, choose a staffing response, understand the cost and people implications, and measure whether the response worked.
