"""Generate the clearly-labelled demo company dataset for AI Manager Learning Lab.

The employee file is the teacher-provided dataset. Every other file is synthetic
demo material generated deterministically so the case is coherent and repeatable.
"""

from __future__ import annotations

import argparse
import itertools
import shutil
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "Extended_Employee_Performance_and_Productivity_Data.csv"
DEFAULT_OUT = ROOT / "teacher_materials"

SEED = 20260930
COMPANY = "Meridian Consumer Group, Inc."

MONTHS = pd.period_range("2025-01", "2026-09", freq="M")
SEASON = {
    1: 0.94, 2: 0.91, 3: 0.97, 4: 0.96, 5: 1.00, 6: 1.02,
    7: 1.00, 8: 1.03, 9: 0.99, 10: 1.05, 11: 1.16, 12: 1.23,
}
BASE_MONTHLY_REVENUE = 2_400_000_000
PERFORMANCE_2026 = {1: 0.980, 2: 0.960, 3: 0.950, 4: 0.920, 5: 0.900,
                    6: 0.880, 7: 0.860, 8: 0.840, 9: 0.820}

REGIONS = ["North", "South", "East", "West"]
CHANNELS = ["Retail Stores", "E-commerce", "Wholesale"]
PRODUCT_LINES = ["Home Essentials", "Seasonal Living", "Consumer Electronics"]

REGION_WEIGHTS = {
    2025: {"North": 0.30, "South": 0.25, "East": 0.25, "West": 0.20},
    2026: {"North": 0.29, "South": 0.26, "East": 0.24, "West": 0.21},
}
CHANNEL_WEIGHTS = {
    2025: {"Retail Stores": 0.56, "E-commerce": 0.29, "Wholesale": 0.15},
    2026: {"Retail Stores": 0.51, "E-commerce": 0.34, "Wholesale": 0.15},
}
PRODUCT_WEIGHTS = {
    2025: {"Home Essentials": 0.44, "Seasonal Living": 0.34, "Consumer Electronics": 0.22},
    2026: {"Home Essentials": 0.47, "Seasonal Living": 0.33, "Consumer Electronics": 0.20},
}

AVG_UNIT_PRICE = {
    "Home Essentials": 48.0,
    "Seasonal Living": 72.0,
    "Consumer Electronics": 165.0,
}
BASE_MARGIN = {
    "Home Essentials": 42.0,
    "Seasonal Living": 38.0,
    "Consumer Electronics": 28.0,
}
BASE_RETURN_RATE = {
    "Home Essentials": 0.022,
    "Seasonal Living": 0.040,
    "Consumer Electronics": 0.070,
}
BASE_DISCOUNT = {
    "Home Essentials": 0.07,
    "Seasonal Living": 0.11,
    "Consumer Electronics": 0.09,
}

PRODUCTS = [
    {"sku": "HOM-001", "name": "Harbor Ceramic Dinner Set", "line": "Home Essentials", "demand": 420, "cost": 18.0, "price": 44.0, "lead": 21},
    {"sku": "HOM-002", "name": "Harbor Storage Bins (4-pack)", "line": "Home Essentials", "demand": 610, "cost": 9.0, "price": 26.0, "lead": 18},
    {"sku": "HOM-003", "name": "Harbor Cotton Towel Set", "line": "Home Essentials", "demand": 760, "cost": 7.5, "price": 22.0, "lead": 14},
    {"sku": "HOM-004", "name": "Harbor Kitchen Scale", "line": "Home Essentials", "demand": 330, "cost": 11.0, "price": 29.0, "lead": 24},
    {"sku": "HOM-005", "name": "Harbor LED Desk Lamp", "line": "Home Essentials", "demand": 290, "cost": 13.0, "price": 34.0, "lead": 30},
    {"sku": "HOM-006", "name": "Harbor Air Purifier Mini", "line": "Home Essentials", "demand": 180, "cost": 41.0, "price": 89.0, "lead": 35},
    {"sku": "SEA-001", "name": "Terra Patio Chair", "line": "Seasonal Living", "demand": 310, "cost": 32.0, "price": 79.0, "lead": 28},
    {"sku": "SEA-002", "name": "Terra Outdoor Planter", "line": "Seasonal Living", "demand": 540, "cost": 8.0, "price": 24.0, "lead": 20},
    {"sku": "SEA-003", "name": "Terra Holiday Light Set", "line": "Seasonal Living", "demand": 880, "cost": 5.5, "price": 19.0, "lead": 16},
    {"sku": "SEA-004", "name": "Terra Picnic Blanket", "line": "Seasonal Living", "demand": 350, "cost": 12.0, "price": 36.0, "lead": 22},
    {"sku": "SEA-005", "name": "Terra Garden Tool Kit", "line": "Seasonal Living", "demand": 260, "cost": 17.0, "price": 49.0, "lead": 26},
    {"sku": "SEA-006", "name": "Terra Cooler 24L", "line": "Seasonal Living", "demand": 220, "cost": 28.0, "price": 69.0, "lead": 31},
    {"sku": "ELE-001", "name": "Lumen Wireless Earbuds", "line": "Consumer Electronics", "demand": 690, "cost": 29.0, "price": 79.0, "lead": 32},
    {"sku": "ELE-002", "name": "Lumen Smart Plug", "line": "Consumer Electronics", "demand": 820, "cost": 7.0, "price": 22.0, "lead": 20},
    {"sku": "ELE-003", "name": "Lumen Bluetooth Speaker", "line": "Consumer Electronics", "demand": 410, "cost": 34.0, "price": 89.0, "lead": 29},
    {"sku": "ELE-004", "name": "Lumen Fitness Band", "line": "Consumer Electronics", "demand": 520, "cost": 26.0, "price": 69.0, "lead": 34},
    {"sku": "ELE-005", "name": "Lumen 4K Streaming Stick", "line": "Consumer Electronics", "demand": 730, "cost": 21.0, "price": 54.0, "lead": 25},
    {"sku": "ELE-006", "name": "Lumen Power Bank 20K", "line": "Consumer Electronics", "demand": 640, "cost": 16.0, "price": 45.0, "lead": 23},
]

WAREHOUSE_FACTOR = {"North DC": 1.15, "South DC": 1.00, "East DC": 1.10, "West DC": 0.85}

TASKS = [
    ("T-001", "Q4 e-commerce recovery plan", "Marketing", "VP Marketing", "Critical", "In Progress", "2026-09-01", "2026-10-15", 35, 250000, 90000, "High", "Conversion rate down 18% year on year; channel plan required."),
    ("T-002", "Electronics replenishment programme", "Operations", "Director, Supply Chain", "Critical", "In Progress", "2026-08-15", "2026-10-10", 55, 1200000, 800000, "High", "North and East DCs below reorder point on several SKUs."),
    ("T-003", "Seasonal inventory clearance", "Operations", "VP Operations", "High", "Not Started", "2026-10-01", "2026-12-15", 0, 300000, 0, "Medium", "West and South DCs carry excess seasonal stock."),
    ("T-004", "Customer response time reduction", "Customer Support", "VP Customer Support", "High", "Blocked", "2026-07-01", "2026-09-30", 40, 180000, 120000, "High", "Due 30 September; CRM integration dependency unresolved."),
    ("T-005", "Sales pipeline review", "Sales", "VP Sales", "High", "In Progress", "2026-08-01", "2026-10-31", 60, 75000, 40000, "Medium", "Wholesale renewal risk and retail conversion weakness."),
    ("T-006", "Performance rating calibration", "HR", "CHRO", "High", "In Progress", "2026-09-01", "2026-11-30", 20, 50000, 10000, "Medium", "Rating distribution is almost uniform; manager calibration needed."),
    ("T-007", "Delegation and approval limits refresh", "HR", "COO", "Medium", "Not Started", "2026-10-15", "2026-12-31", 0, 25000, 0, "Low", "Clarify decision rights across functions and regions."),
    ("T-008", "ERP procurement module rollout", "IT", "CIO", "Medium", "Blocked", "2026-05-01", "2026-11-30", 30, 600000, 220000, "High", "Vendor dependency and master-data ownership issues."),
    ("T-009", "Warehouse labour scheduling pilot", "Operations", "Director, Fulfilment", "High", "In Progress", "2026-07-15", "2026-11-15", 45, 140000, 70000, "Medium", "Overtime remains above target in two DCs."),
    ("T-010", "Marketing spend effectiveness review", "Marketing", "VP Marketing", "High", "Not Started", "2026-10-05", "2026-11-20", 0, 40000, 0, "Medium", "Marketing ratio has risen while revenue has fallen."),
    ("T-011", "Wholesale contract renewal", "Sales", "VP Sales", "High", "In Progress", "2026-08-01", "2026-10-31", 65, 30000, 18000, "Medium", "Two contracts representing 6% of revenue are under review."),
    ("T-012", "Team lead coaching programme", "HR", "CHRO", "Medium", "In Progress", "2026-06-01", "2026-12-15", 50, 110000, 55000, "Low", "First-line leader capability and feedback quality."),
    ("T-013", "Monthly operating review redesign", "Finance", "CFO", "Medium", "Not Started", "2026-10-15", "2026-12-01", 0, 15000, 0, "Low", "Move from reporting to action tracking."),
    ("T-014", "Supplier lead-time renegotiation", "Operations", "Director, Procurement", "High", "In Progress", "2026-07-01", "2026-10-20", 40, 20000, 8000, "Medium", "Electronics lead times remain volatile."),
    ("T-015", "Returns reduction initiative", "Customer Support", "VP Customer Support", "Medium", "In Progress", "2026-06-15", "2026-12-31", 35, 90000, 35000, "Medium", "Electronics return rate is above plan."),
    ("T-016", "Store labour productivity pilot", "Operations", "VP Operations", "Medium", "In Progress", "2026-08-01", "2027-01-31", 25, 160000, 40000, "Medium", "Test scheduling model in 12 stores."),
    ("T-017", "Digital shelf content refresh", "Marketing", "Director, Digital", "Medium", "Complete", "2026-04-01", "2026-08-31", 100, 80000, 78000, "Low", "Completed; conversion uplift not yet isolated."),
    ("T-018", "Remote work policy review", "HR", "CHRO", "Low", "Not Started", "2026-11-01", "2027-01-31", 0, 10000, 0, "Low", "Review hybrid expectations by role."),
    ("T-019", "Customer retention campaign", "Marketing", "VP Marketing", "High", "In Progress", "2026-08-15", "2026-11-30", 30, 200000, 60000, "High", "Target repeat buyers with declining satisfaction."),
    ("T-020", "Inventory data cleanup", "IT", "CIO", "Medium", "Blocked", "2026-06-01", "2026-09-15", 20, 120000, 45000, "High", "Past due; master-data ownership unclear."),
    ("T-021", "Budget variance dashboard", "Finance", "CFO", "Medium", "In Progress", "2026-07-01", "2026-10-31", 70, 45000, 30000, "Low", "Automate category-level variance reporting."),
    ("T-022", "Cross-functional S&OP cadence", "Operations", "COO", "High", "Not Started", "2026-10-01", "2026-12-15", 0, 35000, 0, "Medium", "Single demand and supply review each month."),
    ("T-023", "Safety stock policy update", "Operations", "Director, Supply Chain", "High", "Not Started", "2026-10-01", "2026-11-30", 0, 20000, 0, "Medium", "Policy has not kept pace with lead-time volatility."),
    ("T-024", "Electronics supplier diversification", "Operations", "Director, Procurement", "High", "In Progress", "2026-09-01", "2027-02-28", 15, 50000, 5000, "Medium", "Reduce single-supplier concentration."),
    ("T-025", "Complaint root-cause analysis", "Customer Support", "Director, Service Quality", "High", "In Progress", "2026-08-01", "2026-10-15", 55, 30000, 14000, "Medium", "Late delivery and unavailable items dominate complaints."),
    ("T-026", "Q4 seasonal staffing plan", "HR", "CHRO", "High", "In Progress", "2026-09-15", "2026-10-31", 50, 60000, 20000, "Medium", "Customer support and warehouse roles are priority."),
    ("T-027", "Pricing and discount guardrails", "Finance", "CFO", "High", "Not Started", "2026-10-15", "2026-12-01", 0, 25000, 0, "Medium", "Discount depth has increased faster than volume."),
    ("T-028", "Warehouse cycle count audit", "Operations", "Director, Fulfilment", "Medium", "Complete", "2026-07-01", "2026-08-31", 100, 18000, 17000, "Low", "Completed; two SKU count variances remain open."),
    ("T-029", "Executive scorecard refresh", "Finance", "CFO", "Medium", "In Progress", "2026-09-01", "2026-11-15", 40, 20000, 8000, "Low", "Align measures with the recovery plan."),
    ("T-030", "Customer refund process redesign", "Customer Support", "VP Customer Support", "Medium", "In Progress", "2026-07-15", "2026-11-30", 60, 70000, 42000, "Medium", "Refund delays are a recurring complaint theme."),
]

COMPLAINTS = [
    "Late delivery", "Product unavailable", "Refund delay",
    "Damaged item", "Support response time", "Incorrect product information",
]


def generate_sales(rng: np.random.Generator) -> pd.DataFrame:
    totals_2025 = {}
    targets_2025 = {}
    totals_2026 = {}
    targets_2026 = {}

    for period in MONTHS:
        if period.year == 2025:
            growth = 1 + 0.004 * (period.month - 1)
            noise = rng.normal(0, 0.011)
            total = BASE_MONTHLY_REVENUE * SEASON[period.month] * growth * (1 + noise)
            totals_2025[period.month] = total
            targets_2025[period.month] = total / 1.005

    for period in MONTHS:
        if period.year == 2026:
            target = totals_2025[period.month] * 1.05
            actual = target * PERFORMANCE_2026[period.month] * rng.normal(1, 0.004)
            targets_2026[period.month] = target
            totals_2026[period.month] = actual

    rows = []
    for period in MONTHS:
        if period.year == 2025:
            total = totals_2025[period.month]
            target = targets_2025[period.month]
        else:
            total = totals_2026[period.month]
            target = targets_2026[period.month]

        combos = list(itertools.product(REGIONS, CHANNELS, PRODUCT_LINES))
        weights = []
        for region, channel, product in combos:
            weight = (
                REGION_WEIGHTS[period.year][region]
                * CHANNEL_WEIGHTS[period.year][channel]
                * PRODUCT_WEIGHTS[period.year][product]
            )
            weights.append(weight * rng.lognormal(0, 0.05))
        weight_sum = sum(weights)

        for (region, channel, product), weight in zip(combos, weights):
            revenue = total * weight / weight_sum
            target_revenue = target * weight / weight_sum
            unit_price = AVG_UNIT_PRICE[product] * rng.normal(1, 0.01)
            units = max(0, int(round(revenue / unit_price)))
            return_rate = BASE_RETURN_RATE[product]
            discount = BASE_DISCOUNT[product] + (0.022 if period.year == 2026 else 0.0) + rng.normal(0, 0.006)
            margin = BASE_MARGIN[product] - discount * 35 + rng.normal(0, 0.8)
            if period.year == 2026:
                margin -= 1.2
            rows.append({
                "Month": f"{period.year}-{period.month:02d}",
                "Year": period.year,
                "Quarter": f"{period.year}-Q{period.quarter}",
                "Region": region,
                "Channel": channel,
                "Product_Line": product,
                "Revenue": round(revenue, 2),
                "Target_Revenue": round(target_revenue, 2),
                "Units_Sold": units,
                "Returns": max(0, int(round(units * return_rate * rng.uniform(0.85, 1.2)))),
                "Discount_Rate": round(float(np.clip(discount, 0.02, 0.30)), 4),
                "Gross_Margin_Pct": round(float(np.clip(margin, 12.0, 55.0)), 2),
            })

    return pd.DataFrame(rows)


def generate_expenses(rng: np.random.Generator, sales: pd.DataFrame, employees: pd.DataFrame) -> pd.DataFrame:
    active = employees.loc[~employees["Resigned"].astype(bool)]
    active_payroll = float(active["Monthly_Salary"].sum())
    active_headcount = int(len(active))

    monthly_revenue = sales.groupby("Month")["Revenue"].sum().to_dict()
    monthly_target = sales.groupby("Month")["Target_Revenue"].sum().to_dict()

    utility_season = {1: 1.15, 2: 1.12, 3: 1.05, 4: 0.95, 5: 0.90, 6: 0.95,
                      7: 1.00, 8: 1.00, 9: 0.98, 10: 0.95, 11: 1.02, 12: 1.10}

    rows = []
    for month in monthly_revenue:
        year = int(month[:4])
        month_num = int(month[5:7])
        revenue = monthly_revenue[month]
        target = monthly_target[month]
        seasonal = utility_season[month_num]

        if year == 2025:
            actual = {
                "Payroll": active_payroll * rng.normal(1, 0.001),
                "Rent & Facilities": 62_000_000 * rng.normal(1, 0.002),
                "Marketing": revenue * 0.036 * rng.normal(1, 0.02),
                "Logistics": revenue * 0.022 * rng.normal(1, 0.03),
                "Technology": (32_000_000 + revenue * 0.002) * rng.normal(1, 0.01),
                "Customer Support": (16_000_000 + revenue * 0.0015) * rng.normal(1, 0.01),
                "Utilities": 10_000_000 * seasonal * rng.normal(1, 0.02),
                "Supplies": (12_000_000 + revenue * 0.001) * rng.normal(1, 0.02),
                "Professional Services": 8_000_000 * rng.normal(1, 0.02),
                "Other": 9_000_000 * rng.normal(1, 0.02),
            }
            budget = {key: value * 1.005 for key, value in actual.items()}
        else:
            actual = {
                "Payroll": active_payroll * 1.03 * rng.normal(1, 0.001),
                "Rent & Facilities": 64_000_000 * rng.normal(1, 0.002),
                "Marketing": revenue * 0.044 * rng.normal(1, 0.02),
                "Logistics": revenue * 0.028 * rng.normal(1, 0.03),
                "Technology": (38_000_000 + revenue * 0.0025) * rng.normal(1, 0.01),
                "Customer Support": (20_000_000 + revenue * 0.002) * rng.normal(1, 0.01),
                "Utilities": 11_000_000 * seasonal * rng.normal(1, 0.02),
                "Supplies": (13_000_000 + revenue * 0.001) * rng.normal(1, 0.02),
                "Professional Services": (14_500_000 if month in {"2026-05", "2026-06"} else 8_500_000) * rng.normal(1, 0.02),
                "Other": 9_000_000 * rng.normal(1, 0.02),
            }
            budget = {
                "Payroll": active_payroll * 1.03 * 1.005,
                "Rent & Facilities": 62_000_000 * 1.03,
                "Marketing": target * 0.038,
                "Logistics": target * 0.023,
                "Technology": 34_000_000 + target * 0.002,
                "Customer Support": 17_000_000 + target * 0.0015,
                "Utilities": 10_500_000 * seasonal,
                "Supplies": 13_000_000 + target * 0.001,
                "Professional Services": 8_500_000,
                "Other": 9_000_000,
            }

        departments = {
            "Payroll": "HR",
            "Rent & Facilities": "Operations",
            "Marketing": "Marketing",
            "Logistics": "Operations",
            "Technology": "IT",
            "Customer Support": "Customer Support",
            "Utilities": "Operations",
            "Supplies": "Operations",
            "Professional Services": "Legal",
            "Other": "Finance",
        }
        notes = {
            "Payroll": f"Active headcount {active_headcount:,}; 3% merit cycle effective January 2026." if year == 2026 else f"Base payroll for {active_headcount:,} active employees.",
            "Rent & Facilities": "Lease escalation and facility maintenance.",
            "Marketing": "Brand campaign, retention activity and markdown support." if year == 2026 else "Planned brand and demand-generation spend.",
            "Logistics": "Expedited freight and split shipments to protect electronics orders." if year == 2026 else "Base freight and distribution cost.",
            "Technology": "Cloud, cybersecurity and ERP licence renewal." if year == 2026 else "Core platforms and infrastructure.",
            "Customer Support": "Additional seasonal agents and CRM support." if year == 2026 else "Service operations and contact-centre support.",
            "Utilities": "Seasonal energy costs.",
            "Supplies": "Warehouse consumables and packaging.",
            "Professional Services": "One-time ERP and compliance review." if month in {"2026-05", "2026-06"} else "External audit and legal advisory.",
            "Other": "Insurance, travel and miscellaneous.",
        }

        for category in actual:
            act = max(0.0, actual[category])
            bud = max(0.0, budget[category])
            rows.append({
                "Month": month,
                "Category": category,
                "Department": departments[category],
                "Budget": round(bud, 2),
                "Actual": round(act, 2),
                "Variance": round(act - bud, 2),
                "Variance_Pct": round((act - bud) / bud * 100, 2) if bud else 0.0,
                "Notes": notes[category],
            })

    return pd.DataFrame(rows)


def generate_inventory(rng: np.random.Generator) -> pd.DataFrame:
    rows = []
    last_dates = pd.date_range("2026-09-15", "2026-09-30", freq="D")
    for product in PRODUCTS:
        for warehouse, factor in WAREHOUSE_FACTOR.items():
            weekly = int(round(product["demand"] * factor * rng.uniform(0.82, 1.18)))
            lead = max(10, product["lead"] + int(rng.integers(-3, 6)))
            safety = int(round(weekly * lead / 7 * 0.5))
            reorder = int(round(weekly * lead / 7 + safety))

            if product["line"] == "Consumer Electronics" and warehouse in {"North DC", "East DC"}:
                on_hand = int(round(weekly * rng.uniform(0.8, 2.2)))
                on_order = int(round(weekly * rng.uniform(1.0, 2.8)))
            elif product["line"] == "Seasonal Living" and warehouse in {"South DC", "West DC"}:
                on_hand = int(round(weekly * rng.uniform(7.0, 12.0)))
                on_order = int(round(weekly * rng.uniform(0.0, 0.8)))
            elif product["line"] == "Home Essentials":
                on_hand = int(round(weekly * rng.uniform(2.4, 5.8)))
                on_order = int(round(weekly * rng.uniform(0.0, 1.2)))
            else:
                on_hand = int(round(weekly * rng.uniform(1.4, 6.0)))
                on_order = int(round(weekly * rng.uniform(0.0, 1.5)))

            if on_hand < safety:
                status = "Below Safety Stock"
            elif on_hand + on_order < reorder:
                status = "Below Reorder Point"
            elif on_hand > weekly * 9:
                status = "Overstock"
            else:
                status = "Healthy"

            rows.append({
                "SKU": product["sku"],
                "Product_Name": product["name"],
                "Product_Line": product["line"],
                "Warehouse": warehouse,
                "Units_On_Hand": on_hand,
                "Units_On_Order": on_order,
                "Avg_Weekly_Demand": weekly,
                "Safety_Stock": safety,
                "Reorder_Point": reorder,
                "Lead_Time_Days": lead,
                "Weeks_Of_Supply": round(on_hand / weekly, 2) if weekly else 0.0,
                "Unit_Cost": round(product["cost"], 2),
                "Unit_Price": round(product["price"], 2),
                "Last_Stocktake": pd.Timestamp(rng.choice(last_dates)).strftime("%Y-%m-%d"),
                "Stock_Status": status,
            })
    return pd.DataFrame(rows)


def generate_customer_feedback(rng: np.random.Generator) -> pd.DataFrame:
    rows = []
    for period in MONTHS:
        for region in REGIONS:
            region_adjust = {"North": -1.5, "South": 1.0, "East": -0.5, "West": 0.5}[region]
            if period.year == 2025:
                csat = 80.5 + region_adjust + rng.normal(0, 0.8)
                nps = 31 + rng.normal(0, 2.5)
                complaints = int(round(rng.uniform(520, 760) * (1.15 if region == "North" else 1.0)))
                response = rng.uniform(5.2, 7.0)
            else:
                progress = 3.0 - 0.18 * period.month
                csat = 73.5 + region_adjust - progress + rng.normal(0, 0.7)
                nps = 18 - 0.7 * period.month + rng.normal(0, 2.0)
                complaints = int(round(rng.uniform(1_050, 1_450) * (1.15 if region == "North" else 1.0)))
                response = rng.uniform(9.0, 13.5)
            responses = int(round(rng.uniform(950, 1_550)))
            theme_weights = {
                "Late delivery": 0.29 if period.year == 2026 else 0.19,
                "Product unavailable": 0.24 if period.year == 2026 else 0.14,
                "Refund delay": 0.16 if period.year == 2026 else 0.11,
                "Damaged item": 0.13,
                "Support response time": 0.12 if period.year == 2026 else 0.07,
                "Incorrect product information": 0.06,
            }
            themes = list(theme_weights)
            weights = list(theme_weights.values())
            rows.append({
                "Month": f"{period.year}-{period.month:02d}",
                "Region": region,
                "Survey_Responses": responses,
                "CSAT": round(float(np.clip(csat, 55, 90)), 1),
                "NPS": round(float(np.clip(nps, -10, 50)), 1),
                "Complaints": complaints,
                "Avg_Response_Hours": round(float(np.clip(response, 3, 18)), 1),
                "Top_Complaint": rng.choice(themes, p=np.array(weights) / sum(weights)),
            })
    return pd.DataFrame(rows)


def generate_headcount_plan(employees: pd.DataFrame) -> pd.DataFrame:
    open_roles = {
        "IT": 120, "Finance": 40, "Operations": 250, "Sales": 180, "Legal": 20,
        "Customer Support": 300, "HR": 50, "Marketing": 60, "Engineering": 140,
    }
    notes = {
        "IT": "Priority roles: data engineering and cybersecurity.",
        "Finance": "Limited hiring; focus on analytical capability.",
        "Operations": "Largest hiring need; warehouse and supply-chain roles.",
        "Sales": "Selective hiring; wholesale account coverage.",
        "Legal": "Low volume; contract support.",
        "Customer Support": "Critical customer-facing roles; hiring freeze exception.",
        "HR": "Recruiting and employee relations capability.",
        "Marketing": "Digital and retention roles only.",
        "Engineering": "Product and platform roles; annual plan approved.",
    }
    rows = []
    for department, group in employees.groupby("Department"):
        active = group.loc[~group["Resigned"].astype(bool)]
        active_count = int(len(active))
        open_count = open_roles.get(department, 0)
        rows.append({
            "Department": department,
            "Approved_Headcount": active_count + open_count,
            "Active_Headcount": active_count,
            "Open_Requisitions": open_count,
            "Attrition_Rate_Pct": round(float(group["Resigned"].mean() * 100), 2),
            "Avg_Training_Hours": round(float(active["Training_Hours"].mean()), 1),
            "Training_Target_Hours": 60,
            "Monthly_Salary_Budget": round(float(active["Monthly_Salary"].sum()), 2),
            "Notes": notes.get(department, ""),
        })
    return pd.DataFrame(rows).sort_values("Department").reset_index(drop=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate demo company CSVs for the AI Manager Learning Lab.")
    parser.add_argument("--source-csv", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--force", action="store_true", help="Overwrite existing generated files.")
    args = parser.parse_args()

    source = args.source_csv.resolve()
    out = args.out.resolve()
    if not source.exists():
        raise SystemExit(f"Source employee CSV not found: {source}")
    if args.force:
        out.mkdir(parents=True, exist_ok=True)
    else:
        out.mkdir(parents=True, exist_ok=True)

    target_employees = out / "employees.csv"
    if not target_employees.exists() or args.force:
        shutil.copy2(source, target_employees)
        print(f"Wrote {target_employees}")

    employees = pd.read_csv(target_employees, low_memory=False)
    rng = np.random.default_rng(SEED)

    sales = generate_sales(rng)
    expenses = generate_expenses(rng, sales, employees)

    generated = {
        "sales.csv": sales,
        "expenses.csv": expenses,
        "inventory.csv": generate_inventory(np.random.default_rng(SEED + 2)),
        "tasks.csv": pd.DataFrame(TASKS, columns=[
            "Task_ID", "Task_Name", "Department", "Owner_Role", "Priority", "Status",
            "Start_Date", "Due_Date", "Percent_Complete", "Budget", "Spent", "Risk_Level", "Notes",
        ]),
        "customer_feedback.csv": generate_customer_feedback(np.random.default_rng(SEED + 3)),
        "headcount_plan.csv": generate_headcount_plan(employees),
    }

    for name, frame in generated.items():
        path = out / name
        if path.exists() and not args.force:
            print(f"Skipped existing {path} (use --force to overwrite)")
            continue
        frame.to_csv(path, index=False, encoding="utf-8")
        print(f"Wrote {path} ({len(frame):,} rows)")

    sales = generated["sales.csv"]
    expenses = generated["expenses.csv"]
    revenue_2025 = sales.loc[sales["Year"] == 2025, "Revenue"].sum()
    revenue_2026_ytd = sales.loc[sales["Year"] == 2026, "Revenue"].sum()
    q3_2025 = sales.loc[sales["Quarter"] == "2025-Q3", "Revenue"].sum()
    q3_2026 = sales.loc[sales["Quarter"] == "2026-Q3", "Revenue"].sum()
    opex_2025 = expenses.loc[expenses["Month"].str.startswith("2025"), "Actual"].sum()
    opex_2026_ytd = expenses.loc[expenses["Month"].str.startswith("2026"), "Actual"].sum()
    active = employees.loc[~employees["Resigned"].astype(bool)]
    inventory = generated["inventory.csv"]
    tasks = generated["tasks.csv"]
    feedback = generated["customer_feedback.csv"]

    print("\nCASE SUMMARY")
    print(f"Company: {COMPANY}")
    print(f"Active headcount: {len(active):,}")
    print(f"Resignation rate: {employees['Resigned'].mean() * 100:.2f}%")
    print(f"Active monthly payroll: ${active['Monthly_Salary'].sum():,.0f}")
    print(f"FY2025 revenue: ${revenue_2025:,.0f}")
    print(f"2026 YTD revenue: ${revenue_2026_ytd:,.0f}")
    print(f"Q3 2025 revenue: ${q3_2025:,.0f}")
    print(f"Q3 2026 revenue: ${q3_2026:,.0f}")
    print(f"Q3 YoY change: {(q3_2026 / q3_2025 - 1) * 100:.2f}%")
    print(f"2025 operating expenses: ${opex_2025:,.0f}")
    print(f"2026 YTD operating expenses: ${opex_2026_ytd:,.0f}")
    print("Inventory status counts:")
    print(inventory["Stock_Status"].value_counts().to_string())
    print("Task status counts:")
    print(tasks["Status"].value_counts().to_string())
    print(f"Overdue tasks: {((pd.to_datetime(tasks['Due_Date']) < pd.Timestamp('2026-09-30')) & (tasks['Status'] != 'Complete')).sum()}")
    print(f"2025 CSAT: {feedback.loc[feedback['Month'].str.startswith('2025'), 'CSAT'].mean():.1f}")
    print(f"2026 YTD CSAT: {feedback.loc[feedback['Month'].str.startswith('2026'), 'CSAT'].mean():.1f}")


if __name__ == "__main__":
    main()
