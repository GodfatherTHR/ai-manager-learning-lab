# Company Data Dictionary

**As of 30 September 2026 · All amounts in USD · Dates use ISO format (YYYY-MM-DD)**

The teacher-provided files in this folder are the authoritative source for the case. Read the relevant columns before making a claim. Do not invent values, employees, suppliers, stores, or customers.

## 1. `employees.csv`

An anonymised workforce extract supplied by the course teacher.

| Column | Type | Meaning |
| --- | --- | --- |
| `Employee_ID` | integer | Unique employee identifier; no names are included |
| `Department` | text | One of Sales, Marketing, Operations, Customer Support, Finance, HR, IT, Legal, Engineering |
| `Gender` | text | Self-reported gender category |
| `Age` | integer | Age in years |
| `Job_Title` | text | Broad job family: Specialist, Manager, Technician, Analyst, Engineer, Consultant, Developer |
| `Hire_Date` | datetime | Hire date and time |
| `Years_At_Company` | integer | Completed years of service in the extract |
| `Education_Level` | text | Highest education level reported |
| `Performance_Score` | integer 1–5 | Most recent performance rating; 1 = does not meet expectations, 5 = exceptional |
| `Monthly_Salary` | decimal | Monthly salary in USD |
| `Work_Hours_Per_Week` | integer | Contracted or recorded weekly hours |
| `Projects_Handled` | integer | Number of projects handled in the review period |
| `Overtime_Hours` | integer | Overtime hours in the review period |
| `Sick_Days` | integer | Sick days in the review period |
| `Remote_Work_Frequency` | integer 0–100 | Percentage of work performed remotely |
| `Team_Size` | integer | Size of the employee's team |
| `Training_Hours` | integer | Training hours in the review period |
| `Promotions` | integer | Number of promotions in the review period |
| `Employee_Satisfaction_Score` | decimal 1–5 | Satisfaction score; higher is better |
| `Resigned` | boolean | True if the employee has separated; False if active |

**Rules for analysis**

- Use `Resigned = False` when analysing current employees.
- The file contains 100,000 records, including 10,010 separated employees. A simple `COUNT(*)` is not active headcount.
- `Monthly_Salary` is monthly, not annual.
- Department averages in this teaching extract are very similar. Do not claim that one department is substantially better or worse without checking the actual values and acknowledging the limits of the data.
- The extract is anonymised and synthetic. Do not infer real people, real performance, or causal relationships.

## 2. `sales.csv`

Monthly revenue and target data by region, channel, and product line. It is not SKU-level sales.

| Column | Type | Meaning |
| --- | --- | --- |
| `Month` | text | Month in `YYYY-MM` format |
| `Year` | integer | Calendar year |
| `Quarter` | text | Quarter label, e.g. `2026-Q3` |
| `Region` | text | North, South, East, West |
| `Channel` | text | Retail Stores, E-commerce, Wholesale |
| `Product_Line` | text | Home Essentials, Seasonal Living, Consumer Electronics |
| `Revenue` | decimal | Net revenue in USD for the row |
| `Target_Revenue` | decimal | Revenue target in USD for the row |
| `Units_Sold` | integer | Units sold in the row |
| `Returns` | integer | Units returned in the row |
| `Discount_Rate` | decimal | Average discount as a fraction (e.g. 0.12 = 12%) |
| `Gross_Margin_Pct` | decimal | Gross margin percentage for the row |

**Rules for analysis**

- Sum `Revenue` and `Target_Revenue` to compare actual versus target.
- Do not sum `Discount_Rate` or `Gross_Margin_Pct`; use a revenue-weighted average or analyse by segment.
- `Revenue` is net of returns and discounts.
- The period covered is January 2025 to September 2026.

## 3. `expenses.csv`

Monthly operating expenses by category and department, with budget and actual.

| Column | Type | Meaning |
| --- | --- | --- |
| `Month` | text | Month in `YYYY-MM` format |
| `Category` | text | Payroll, Rent & Facilities, Marketing, Logistics, Technology, Customer Support, Utilities, Supplies, Professional Services, Other |
| `Department` | text | Primary budget owner |
| `Budget` | decimal | Budget for the month and category |
| `Actual` | decimal | Actual spend for the month and category |
| `Variance` | decimal | Actual minus Budget; positive means overspend |
| `Variance_Pct` | decimal | Variance divided by Budget, as a percentage |
| `Notes` | text | Short explanation of the category or a specific variance |

**Rules for analysis**

- Use `Actual` and `Budget` for variance analysis; `Variance` is already computed.
- Payroll is based on the active employee extract: 89,990 active employees, monthly salary bill of $576.3 million before the 2026 merit cycle.
- Do not treat the notes as the only explanation. Query the values before concluding.

## 4. `inventory.csv`

A sample of 18 SKUs across four distribution centres, giving 72 SKU–warehouse lines. It is not the full inventory ledger.

| Column | Type | Meaning |
| --- | --- | --- |
| `SKU` | text | Stock-keeping unit code |
| `Product_Name` | text | Product name |
| `Product_Line` | text | Home Essentials, Seasonal Living, Consumer Electronics |
| `Warehouse` | text | North DC, South DC, East DC, West DC |
| `Units_On_Hand` | integer | Units physically available |
| `Units_On_Order` | integer | Units ordered but not yet received |
| `Avg_Weekly_Demand` | integer | Average weekly demand used for planning |
| `Safety_Stock` | integer | Buffer stock for demand and lead-time variability |
| `Reorder_Point` | integer | Inventory level that triggers replenishment |
| `Lead_Time_Days` | integer | Supplier lead time in days |
| `Weeks_Of_Supply` | decimal | Units on hand divided by average weekly demand |
| `Unit_Cost` | decimal | Unit cost in USD |
| `Unit_Price` | decimal | Unit selling price in USD |
| `Last_Stocktake` | date | Date of the last physical count |
| `Stock_Status` | text | `Below Safety Stock`, `Below Reorder Point`, `Healthy`, or `Overstock` |

**Rules for analysis**

- `Below Safety Stock` and `Below Reorder Point` are both availability risks. Count them separately and together.
- `Overstock` means more than 9 weeks of supply in this extract.
- The 72 lines are a sample. Do not claim that 50 of 72 lines represents every SKU in the company. Say "in the provided sample".
- Inventory value at cost can be estimated as `Units_On_Hand × Unit_Cost`, but it is sample value, not total company inventory.

## 5. `tasks.csv`

The current management and operational task register.

| Column | Type | Meaning |
| --- | --- | --- |
| `Task_ID` | text | Task identifier |
| `Task_Name` | text | Task description |
| `Department` | text | Lead function |
| `Owner_Role` | text | Accountable role; no employee names |
| `Priority` | text | Critical, High, Medium, Low |
| `Status` | text | Not Started, In Progress, Blocked, Complete |
| `Start_Date` | date | Start date |
| `Due_Date` | date | Due date |
| `Percent_Complete` | integer 0–100 | Reported completion percentage |
| `Budget` | decimal | Approved budget in USD |
| `Spent` | decimal | Spent to date in USD |
| `Risk_Level` | text | High, Medium, Low |
| `Notes` | text | Short context |

**Rules for analysis**

- The case date is 30 September 2026. A task with a due date before that and a status other than Complete is past due.
- Blocked tasks are not the same as late tasks; a task can be blocked and not yet due.
- Do not infer that a task is complete because `Percent_Complete` is high. Use `Status`.

## 6. `customer_feedback.csv`

Monthly customer experience data by region.

| Column | Type | Meaning |
| --- | --- | --- |
| `Month` | text | Month in `YYYY-MM` format |
| `Region` | text | North, South, East, West |
| `Survey_Responses` | integer | Number of survey responses |
| `CSAT` | decimal 0–100 | Customer satisfaction score; higher is better |
| `NPS` | decimal -100 to +100 | Net Promoter Score; higher is better |
| `Complaints` | integer | Number of complaints recorded |
| `Avg_Response_Hours` | decimal | Average first-response time in hours |
| `Top_Complaint` | text | Most common complaint theme for the month and region |

**Rules for analysis**

- Do not sum CSAT or NPS. Use weighted or unweighted averages and state the method.
- `Complaints` can be summed across regions and months.
- The complaint themes are categories, not the full text of customer comments.

## 7. `headcount_plan.csv`

Approved headcount, open roles, attrition, training, and salary plan by department.

| Column | Type | Meaning |
| --- | --- | --- |
| `Department` | text | Function |
| `Approved_Headcount` | integer | Active headcount plus approved open requisitions |
| `Active_Headcount` | integer | Current active employees from the employee extract |
| `Open_Requisitions` | integer | Approved but unfilled roles |
| `Attrition_Rate_Pct` | decimal | Separation flag rate for the department, as a percentage |
| `Avg_Training_Hours` | decimal | Average training hours for active employees |
| `Training_Target_Hours` | integer | Annual training target per employee |
| `Monthly_Salary_Budget` | decimal | Monthly salary budget for active employees |
| `Notes` | text | Hiring priorities and constraints |

**Rules for analysis**

- `Active_Headcount` should reconcile to the employee extract when filtered on `Resigned = False`.
- `Monthly_Salary_Budget` is monthly, not annual.
- Open requisitions are approved roles, not vacancies that have been filled.

## 8. General conventions

- All money is in US dollars.
- Percentages are stored as decimals in `Discount_Rate` and as percentage points in `Gross_Margin_Pct` and `Variance_Pct`.
- Dates are ISO `YYYY-MM-DD`; months are `YYYY-MM`.
- The employee file is a teacher-provided anonymised extract; the other files are a labelled demo case.
- The data is for a university management exercise. It is not operational, financial, or HR advice.
- Use `data-query` or the app's data browser to check values. Do not rely on this dictionary for figures; it explains meaning, not current performance.

## 9. Example queries

```powershell
py tools/lab.py data-query sales.csv --filter "Quarter=2026-Q3" --group-by Channel --metric sum:Revenue --sort Revenue:desc
py tools/lab.py data-query sales.csv --filter "Year=2026" --group-by Product_Line --metric sum:Revenue --metric sum:Target_Revenue
py tools/lab.py data-query expenses.csv --filter "Month>=2026-01" --group-by Category --metric sum:Budget --metric sum:Actual --metric sum:Variance --sort sum_Variance:desc
py tools/lab.py data-query inventory.csv --group-by Stock_Status --metric count:SKU
py tools/lab.py data-query employees.csv --filter "Resigned=False" --group-by Department --metric mean:Performance_Score --metric mean:Employee_Satisfaction_Score
py tools/lab.py data-query tasks.csv --filter "Status=Blocked"
```
