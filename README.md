# Fabric Dataflows Gen2 Lab: Finance Medallion Architecture for Renishaw

A self-contained, presenter-ready demo lab showing how **Microsoft Fabric Dataflows Gen2**
implement a **Bronze → Silver → Gold medallion architecture** using synthetic finance
data modelled on Renishaw plc (precision engineering, metrology and analytical
instruments).

*   **Audience:** Renishaw finance / data & analytics stakeholders
*   **Duration:** 45–60 minutes, delivered slowly with explanation at each step
*   **Format:** Low-code, Power Query-based (Dataflows Gen2) — no notebooks or Spark required
*   **Style:** Modelled on the [fabric-training-cmi](https://github.com/ineslantero/fabric-training-cmi) lab format

## Contents

```
├── README.md                     <- you are here
├── generate_data.py               <- script used to synthesize the source CSVs (for reference)
├── labs/
│   └── dataflows-medallion-lab.md <- the full, prescriptive lab guide + presenter notes
├── data/
│   └── bronze/
│       ├── cost_centre_master.csv <- dimension: cost centre -> division/region/manager
│       ├── fx_rates.csv           <- reference: monthly FX rate to GBP by currency
│       ├── gl_actuals.csv         <- fact: monthly actual GL transactions (local currency)
│       └── gl_budget.csv          <- fact: monthly budget by cost centre (GBP)
└── images/                        <- optional space for screenshots you capture while presenting
```

## What this lab covers

1. **Bronze layer** — Landing the four raw Renishaw finance CSVs into a Fabric Lakehouse
   untouched, exactly as extracted from source systems.
2. **Silver layer** — Using **Dataflows Gen2** and the Power Query editor to clean,
   standardise, currency-convert (merge with `fx_rates`), and enrich the actuals with
   cost centre dimension attributes.
3. **Gold layer** — Building a curated, business-ready **Actual vs Budget variance**
   table aggregated by division, region and period — ready for Power BI reporting.
4. **Power Query in Fabric vs. Power Query in Power BI Desktop** — a comparison section
   explaining where the engines diverge (compute location, refresh/orchestration,
   staging, connectors, scale limits) so Renishaw understands why Dataflows Gen2 is the
   right tool for shared, governed data preparation versus report-level shaping.
5. **Advanced Extensions (optional)** — three short, optional add-ons for once the
   core story is told: **custom functions** (reusable cleaning logic), **fuzzy merge**
   (matching messy free-text keys), and **dataflow parameters** (one dataflow, multiple
   scenarios, driven manually — orchestration via a Data Pipeline is left to a
   follow-up session).

## How to run it

Open [`labs/dataflows-medallion-lab.md`](labs/dataflows-medallion-lab.md) and follow it
top to bottom. Each step tells you exactly what to click, and each step has a **🗣️
Talk track** callout with suggested narration for the live demo.

## Prerequisites

*   A Microsoft Fabric tenant/trial with capacity assigned, and permission to create a
    workspace and Fabric items (Lakehouse, Dataflow Gen2).
*   The four CSV files in `data/bronze/` (already generated — no need to re-run
    `generate_data.py` unless you want fresh/re-randomised numbers).

## Notes on the data

The data is **entirely synthetic** and was generated with `generate_data.py`
(seeded, reproducible). It reflects the *shape* of Renishaw's business — five
product divisions (Metrology Systems, Analytical Instruments, Neuro Solutions,
Additive Manufacturing, Raman Spectroscopy) plus Corporate Functions, sold across
UK/Europe/Americas/Asia Pacific in local currencies with GBP group reporting — but
contains no real financial figures, and should be treated as illustrative only.
