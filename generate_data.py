"""
Generates synthetic finance data reflective of Renishaw plc for the
Fabric Dataflows Gen2 medallion architecture lab.

Renishaw is a UK-headquartered precision engineering and metrology group with
divisions spanning Metrology Systems, Analytical Instruments, Neuro Solutions,
Additive Manufacturing and Raman Spectroscopy, selling globally (UK, Europe,
Americas, Asia Pacific) and reporting in GBP.

Output (data/bronze/):
    cost_centre_master.csv - dimension: cost centre -> division/region/manager
    fx_rates.csv            - reference: monthly FX rate to GBP by currency
    gl_actuals.csv          - fact: monthly actual GL transactions (local currency)
    gl_budget.csv           - fact: monthly budget by cost centre (GBP)
"""
import csv
import random
from datetime import date

random.seed(42)

OUT_DIR = "data/bronze"

DIVISIONS = [
    "Metrology Systems",
    "Analytical Instruments",
    "Neuro Solutions",
    "Additive Manufacturing",
    "Raman Spectroscopy",
    "Corporate Functions",
]

REGIONS = {
    "UK": {"country": "United Kingdom", "currency": "GBP"},
    "Europe": {"country": "Germany", "currency": "EUR"},
    "Americas": {"country": "United States", "currency": "USD"},
    "Asia Pacific": {"country": "Japan", "currency": "JPY"},
}

MANAGERS = [
    "A. Whitfield", "S. Okoro", "L. Bergman", "J. Patel", "M. Costa",
    "R. Nakamura", "E. Fischer", "T. Griffiths", "K. Yamamoto", "D. Alonso",
]

# Cost centre master: sensible cross-section, not a full cartesian product
COST_CENTRES = [
    ("CC1001", "Metrology Systems - UK Manufacturing", "Metrology Systems", "UK"),
    ("CC1002", "Metrology Systems - Europe Sales", "Metrology Systems", "Europe"),
    ("CC1003", "Metrology Systems - Americas Sales", "Metrology Systems", "Americas"),
    ("CC1004", "Analytical Instruments - UK R&D", "Analytical Instruments", "UK"),
    ("CC1005", "Analytical Instruments - APAC Sales", "Analytical Instruments", "Asia Pacific"),
    ("CC2001", "Neuro Solutions - UK R&D", "Neuro Solutions", "UK"),
    ("CC2002", "Neuro Solutions - Americas Sales", "Neuro Solutions", "Americas"),
    ("CC3001", "Additive Manufacturing - UK Production", "Additive Manufacturing", "UK"),
    ("CC3002", "Additive Manufacturing - Europe Sales", "Additive Manufacturing", "Europe"),
    ("CC4001", "Raman Spectroscopy - UK R&D", "Raman Spectroscopy", "UK"),
    ("CC4002", "Raman Spectroscopy - APAC Sales", "Raman Spectroscopy", "Asia Pacific"),
    ("CC9001", "Corporate Functions - UK Head Office", "Corporate Functions", "UK"),
]

ACCOUNT_CATEGORIES = [
    ("4000", "Product Revenue", "Revenue"),
    ("4100", "Service & Calibration Revenue", "Revenue"),
    ("5000", "Material Costs", "Cost of Sales"),
    ("5100", "Direct Labour", "Cost of Sales"),
    ("6000", "Research & Development", "Operating Expense"),
    ("6100", "Selling & Distribution", "Operating Expense"),
    ("6200", "Administrative Expense", "Operating Expense"),
    ("7000", "Capital Expenditure", "Capital Expenditure"),
]

MONTHS = [date(2026, m, 1) for m in range(1, 7)]  # Jan-Jun 2026 (H2 FY26)

# Approximate, illustrative FX rates to GBP by month (synthetic, for lab use only)
FX_BASE = {"GBP": 1.00, "EUR": 0.855, "USD": 0.79, "JPY": 0.0052}


def month_str(d):
    return d.strftime("%Y-%m-01")


def write_cost_centre_master():
    path = f"{OUT_DIR}/cost_centre_master.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["cost_centre_id", "cost_centre_name", "division", "region", "country", "cost_centre_manager"])
        for i, (cc_id, cc_name, division, region) in enumerate(COST_CENTRES):
            country = REGIONS[region]["country"]
            manager = MANAGERS[i % len(MANAGERS)]
            w.writerow([cc_id, cc_name, division, region, country, manager])
    print(f"Wrote {path}")


def write_fx_rates():
    path = f"{OUT_DIR}/fx_rates.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["currency", "rate_month", "rate_to_gbp"])
        for currency, base_rate in FX_BASE.items():
            for idx, m in enumerate(MONTHS):
                # small monthly drift so the FX join/merge step is meaningful
                drift = 1 + (random.uniform(-0.02, 0.02))
                rate = round(base_rate * (drift ** (idx + 1)), 6) if currency != "GBP" else 1.0
                w.writerow([currency, month_str(m), rate])
    print(f"Wrote {path}")


def write_gl_actuals():
    path = f"{OUT_DIR}/gl_actuals.csv"
    rows = []
    txn_id = 500001
    for cc_id, cc_name, division, region in COST_CENTRES:
        currency = REGIONS[region]["currency"]
        is_revenue_cc = "Sales" in cc_name
        is_rd_cc = "R&D" in cc_name
        is_production_cc = "Manufacturing" in cc_name or "Production" in cc_name
        is_corporate_cc = division == "Corporate Functions"

        for m in MONTHS:
            seasonal = 1 + 0.06 * ((m.month % 6) - 2.5) / 2.5  # mild seasonality

            if is_revenue_cc:
                categories = [
                    ("4000", "Product Revenue", "Revenue", random.uniform(180000, 420000)),
                    ("4100", "Service & Calibration Revenue", "Revenue", random.uniform(20000, 60000)),
                    ("6100", "Selling & Distribution", "Operating Expense", random.uniform(15000, 45000)),
                ]
            elif is_rd_cc:
                categories = [
                    ("6000", "Research & Development", "Operating Expense", random.uniform(90000, 220000)),
                    ("5100", "Direct Labour", "Cost of Sales", random.uniform(40000, 90000)),
                ]
            elif is_production_cc:
                categories = [
                    ("5000", "Material Costs", "Cost of Sales", random.uniform(120000, 260000)),
                    ("5100", "Direct Labour", "Cost of Sales", random.uniform(70000, 150000)),
                    ("7000", "Capital Expenditure", "Capital Expenditure", random.uniform(0, 60000)),
                ]
            elif is_corporate_cc:
                categories = [
                    ("6200", "Administrative Expense", "Operating Expense", random.uniform(150000, 260000)),
                ]
            else:
                categories = [
                    ("6200", "Administrative Expense", "Operating Expense", random.uniform(30000, 70000)),
                ]

            for account_code, account_name, account_category, base_amount in categories:
                amount_local = round(base_amount * seasonal, 2)
                # sprinkle a few data-quality issues for the "clean in Power Query" story
                description = f"{account_name} - {m.strftime('%b %Y')}"
                if txn_id % 47 == 0:
                    description = description.upper() + "   "  # inconsistent casing/whitespace
                if txn_id % 61 == 0:
                    cc_name_out = cc_name + "  "  # trailing whitespace on dimension text
                else:
                    cc_name_out = cc_name

                rows.append([
                    txn_id, month_str(m), cc_id, cc_name_out, account_code, account_name,
                    account_category, description, currency, amount_local,
                ])
                txn_id += 1

    # inject a handful of nulls/blank descriptions and a duplicate row to demonstrate cleansing
    rows[5][7] = ""  # blank description
    rows.append(rows[10][:])  # exact duplicate transaction

    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "transaction_id", "period", "cost_centre_id", "cost_centre_name", "account_code",
            "account_name", "account_category", "description", "currency", "amount_local",
        ])
        w.writerows(rows)
    print(f"Wrote {path} ({len(rows)} rows)")


def write_gl_budget():
    path = f"{OUT_DIR}/gl_budget.csv"
    rows = []
    for cc_id, cc_name, division, region in COST_CENTRES:
        is_revenue_cc = "Sales" in cc_name
        is_rd_cc = "R&D" in cc_name
        is_production_cc = "Manufacturing" in cc_name or "Production" in cc_name
        is_corporate_cc = division == "Corporate Functions"

        for m in MONTHS:
            if is_revenue_cc:
                budget_lines = [("4000", "Product Revenue", "Revenue", 300000),
                                 ("4100", "Service & Calibration Revenue", "Revenue", 38000),
                                 ("6100", "Selling & Distribution", "Operating Expense", 30000)]
            elif is_rd_cc:
                budget_lines = [("6000", "Research & Development", "Operating Expense", 150000),
                                ("5100", "Direct Labour", "Cost of Sales", 65000)]
            elif is_production_cc:
                budget_lines = [("5000", "Material Costs", "Cost of Sales", 190000),
                                 ("5100", "Direct Labour", "Cost of Sales", 110000),
                                 ("7000", "Capital Expenditure", "Capital Expenditure", 25000)]
            elif is_corporate_cc:
                budget_lines = [("6200", "Administrative Expense", "Operating Expense", 200000)]
            else:
                budget_lines = [("6200", "Administrative Expense", "Operating Expense", 45000)]

            for account_code, account_name, account_category, budget_gbp in budget_lines:
                rows.append([cc_id, month_str(m), account_code, account_name, account_category, budget_gbp])

    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["cost_centre_id", "period", "account_code", "account_name", "account_category", "budget_amount_gbp"])
        w.writerows(rows)
    print(f"Wrote {path} ({len(rows)} rows)")


if __name__ == "__main__":
    import os
    os.makedirs(OUT_DIR, exist_ok=True)
    write_cost_centre_master()
    write_fx_rates()
    write_gl_actuals()
    write_gl_budget()
