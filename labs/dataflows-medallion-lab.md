# Renishaw Finance Lab: Medallion Architecture with Dataflows Gen2

## Session goals

* Build a **Bronze → Silver → Gold medallion architecture** entirely with low-code
  **Dataflows Gen2** and **Power Query in Fabric**.
* Use synthetic **Renishaw finance data** (GL actuals (General Ledgers), budget, cost centre master, FX
  rates) as the working example.
* Clean, standardise and currency-convert raw finance data in the **Silver** layer.
* Build a curated **Actual vs Budget variance** table in the **Gold** layer, ready for
  Power BI.
* Compare **Power Query in Fabric (Dataflows Gen2)** with **Power Query in Power BI
  Desktop**, and explain where each one hits its limits.

**Duration:** 45–60 minutes, delivered slowly with narration at each step.
**Format:** live demo — talk through every click, pause for questions between parts.

---

## Why this matters for Renishaw

* Renishaw's finance function consolidates actuals and budgets across five product
  divisions (Metrology Systems, Analytical Instruments, Neuro Solutions, Additive
  Manufacturing, Raman Spectroscopy) and Corporate Functions, sold across the UK,
  Europe, Americas and Asia Pacific in local currencies, with GBP as the group
  reporting currency.
* Today that kind of consolidation and currency conversion is likely done in Excel or
  bespoke scripts — hard to govern, hard to refresh, hard to hand over.
* **Dataflows Gen2** gives the finance team (not just IT) a low-code, visual,
  governed way to build this pipeline, with a single definition that refreshes on a
  schedule and lands trusted tables in OneLake for Power BI to consume.
* The **medallion architecture** (Bronze/Silver/Gold) gives a clear, auditable
  separation between "what source systems gave us", "what we've cleaned and
  standardised" and "what the business actually reports on".

> ### 🗣️ SAY THIS
>
> *"Today I want to show you how Renishaw's finance team could take raw GL exports
> from different systems, clean and standardise them without writing code, and land
> a trusted actual-vs-budget table that refreshes automatically and feeds straight
> into Power BI. We'll do this using a pattern called medallion architecture, and a
> Fabric tool called Dataflows Gen2, which is built on the same Power Query engine
> you already use in Power BI and Excel. By the end of this session you'll have seen
> every layer of that pipeline built live, and you'll understand exactly which parts
> of it your own team could take over and run themselves, without needing a
> developer."*

---

## Prerequisites

* Access to a Microsoft Fabric tenant with a trial capacity or an assigned Fabric
  capacity.
* Permission to create a **workspace** and Fabric items (**Lakehouse**, **Dataflow
  Gen2**) in that workspace.
* The four CSV files from this repo's `data/bronze/` folder, downloaded locally so
  you can upload them during the demo:
  * `cost_centre_master.csv`
  * `fx_rates.csv`
  * `gl_actuals.csv`
  * `gl_budget.csv`

### About the data

| File | Grain | Description |
| --- | --- | --- |
| `cost_centre_master.csv` | 1 row per cost centre. This is just a list of teams, where they are and who the manager is | Dimension: cost centre → division, region, country, manager |
| `fx_rates.csv` | 1 row per currency per month. Currency conversion rates. Foreign exchange rates | Reference: monthly FX rate to GBP |
| `gl_actuals.csv` | 1 row per GL transaction. The master record of every financial transaction of revenue coming in or going out | Fact: actual revenue/cost postings by cost centre, account and month, in **local currency** |
| `gl_budget.csv` | 1 row per budget line. What was planned for comparison. | Fact: monthly budget by cost centre and account, already in **GBP** |

**Explanation:** the actuals arrive in local currency (because that's how the local
ERP posts them) but the budget is set centrally in GBP. That mismatch is deliberate —
it gives us a real reason to demonstrate a **currency conversion merge** in the
Silver layer, which is exactly the kind of problem Renishaw's finance team faces when
consolidating a multi-country group.

The actuals file also has a few intentional data quality issues baked in (a blank
description, inconsistent casing/trailing whitespace on a couple of rows, and one
exact duplicate transaction) so there's something real to clean during the demo.

---

## Part A: Set Up the Workspace and Land the Bronze Layer

### Step 1: Create a Workspace and Lakehouse

* Open [Microsoft Fabric](https://app.fabric.microsoft.com).
* Select **Workspaces** → **New workspace**.
* Name it `Renishaw Finance Demo` (or similar, using your own name if this is a
  shared tenant, e.g. `Renishaw Finance Demo - <yourname>`).
* Assign it to your trial or Fabric capacity, then select **Apply**.
* Inside the workspace, select **New item** → search for and select **Lakehouse**.
* Name it `finance_lh` and select **Create**.

> ### 🗣️ SAY THIS
>
> *"A workspace in Fabric is a container for everything we build today — it's how
> Renishaw would separate, say, a Finance workspace from an Engineering or
> Manufacturing workspace, each with its own permissions and its own people who can
> see it. The Lakehouse is where our data will actually live, on top of OneLake,
> which is Fabric's single, open data lake — one copy of the data, usable by every
> Fabric engine, whether that's Power BI, Spark, or a Warehouse. That 'one copy'
> point matters: today, the same finance numbers often get copied into three or four
> different spreadsheets or systems, and they all quietly drift apart over time.
> Here, everything downstream reads from this same place."*

### Step 2: Land the Raw CSVs into the Lakehouse (Bronze)

* In `finance_lh`, select the **Files** node on the left.
* Select **Upload** → **Upload files**.
* Select all four CSVs (`cost_centre_master.csv`, `fx_rates.csv`, `gl_actuals.csv`,
  `gl_budget.csv`) and upload them into `Files/bronze/`.
* Confirm all four appear under **Files → bronze**.

**Explanation:** this is the **Bronze layer** — raw data landed exactly as it came
from source, with no transformation. We keep it because it's cheap, it's our audit
trail back to source, and it means we can always rebuild Silver and Gold from
scratch if a transformation rule changes.

> ### 🗣️ SAY THIS
>
> *"Notice I haven't changed a single value yet. This is Bronze — it's deliberately
> dumb. We land the file exactly as it arrived, warts and all, before we touch
> anything. If finance ever asks 'where did this number originally come from', or an
> auditor asks us to prove we haven't silently altered a source figure, we can always
> point back here and show the untouched original. It also means that if we ever
> discover a mistake in how we cleaned or calculated something downstream, we haven't
> lost anything — we can just rebuild Silver and Gold again from this same starting
> point."*

---

## Part B: Build the Silver Layer with Dataflows Gen2

The Silver layer takes the raw Bronze files and produces **clean, standardised,
currency-converted, enriched** tables — one row per GL transaction, in GBP, with the
division/region/manager already attached. This is the layer other teams should be
allowed to build on.

### Step 3: Create the Silver Dataflow

* Return to the workspace.
* Select **New item** → search for and select **Dataflow Gen2**.
* Name it `silver_finance_prep`.
* Fabric opens the **Power Query** editor — this is the same visual, ribbon-driven
  editor used in Power BI Desktop and Excel's Get & Transform.

> ### 🗣️ SAY THIS
>
> *"If you've ever used Get Data in Excel or Power BI, this screen will look
> immediately familiar — it's the same Power Query engine and the same ribbon,
> same menus, same idea of applying steps one at a time. The difference isn't the
> tool you're looking at right now, it's where it runs and what it's for — a
> Dataflow Gen2 runs independently in Fabric, not embedded inside one report, so it
> can be reused and refreshed on its own schedule. I'll come back to that comparison
> properly once we've built the whole pipeline, so you can see it in context."*

### Step 4: Bring in `gl_actuals` and Clean It

* Select **Get data** → **OneLake catalog** (or **Import from a Text/CSV file** if
  prompted, pointing at the Lakehouse Files path) → select `finance_lh` → browse to
  `Files/bronze/gl_actuals.csv` → select **Create**.
* In **Power Query**, rename the query (right-click it in the **Queries** pane) to
  `gl_actuals_clean`.
* Confirm the data types Power Query auto-detected on each column (look at the small
  type icons in the column headers):
  * `transaction_id` → Whole Number
  * `period` → Date
  * `amount_local` → Decimal Number
  * everything else → Text
* Clean up whitespace and casing issues on the text columns:
  * Select the `cost_centre_name` and `description` columns (hold **Ctrl** to
    multi-select).
  * On the **Transform** tab, select **Format** → **Trim**, then **Format** →
    **Clean**.
  * On the **Transform** tab, select **Format** → **Capitalize Each Word** on
    `description` only, to fix the all-caps row we saw earlier.
* Remove the exact duplicate transaction:
  * Select all columns (**Ctrl+A** on the column headers, or select the table
    selector in the top-left corner of the grid).
  * On the **Home** tab, select **Remove Rows** → **Remove Duplicates**.
* Handle the blank `description`:
  * Right-click the `description` column header → **Replace Values**.
  * Set **Value To Find** to blank (leave empty) and **Replace With** to
    `Uncategorised transaction`.

**Explanation:** we've just done classic Silver-layer work — trimming whitespace,
standardising text casing, removing an exact duplicate and filling a blank field with
a sensible default. None of this changed the meaning of the data; it made it
consistent enough to trust downstream.

> ### 🗣️ SAY THIS
>
> *"This is the boring-but-critical part of any finance consolidation — and it's
> exactly the kind of thing that normally lives in someone's personal Excel macro,
> or a rule that only one person on the team actually remembers. Here it's visual,
> it's documented step by step in the Applied Steps pane on the right, and anyone on
> the team can open this dataflow and see exactly what was done and why, without
> needing to ask the original author. That's a governance win as much as a technical
> one — if that person leaves the team, the logic doesn't leave with them."*

* Point at the **Applied Steps** pane on the right-hand side.

> ### 🗣️ SAY THIS
>
> *"Every single click I've made is recorded here as a step, in plain English, in
> order. This is what makes Power Query so auditable — nothing happens silently.
> You can click back through this list to see exactly what the data looked like
> before and after any single step, which is invaluable if a number ever looks wrong
> and you need to work out at which point it changed."*

### Step 5: Bring in the Reference Tables

* Select **Get data** again and repeat for the remaining three Bronze files, each as
  its own query:
  * `Files/bronze/cost_centre_master.csv` → rename query to `cost_centre_master`
  * `Files/bronze/fx_rates.csv` → rename query to `fx_rates`
  * `Files/bronze/gl_budget.csv` → keep for now — we'll use it in the **Gold**
    dataflow, not here (Silver only cleans the actuals). If it was brought in
    automatically, right-click it in the Queries pane and select **Delete** so
    Silver stays focused on actuals.
* On `fx_rates`, confirm `rate_month` is typed as **Date** and `rate_to_gbp` as
  **Decimal Number**.

**Explanation:** in this pipeline, `cost_centre_master` and `fx_rates` are
**dimension/reference queries** — small, mostly-static tables we merge onto the
transaction-level fact query. Keeping them as separate queries (rather than typing
the join logic by hand) means Power Query can show us exactly how the merge is
built, step by step.

### Step 6: Merge in the FX Rate and Convert to GBP

* Select the `gl_actuals_clean` query.
* On the **Home** tab, select **Merge queries** → **Merge queries as new** is *not*
  needed here — use plain **Merge queries** so it merges into the current query.
* In the **Merge** dialog:
  * Left table: `gl_actuals_clean`, select the `currency` column, then **Ctrl+click**
    the `period` column.
  * Right table: select `fx_rates`, select the `currency` column, then **Ctrl+click**
    the `rate_month` column.
  * **Join kind:** Left Outer (all rows from `gl_actuals_clean`, matching rows from
    `fx_rates`).
  * Select **OK**.
* A new column appears containing nested tables. Select the **expand** icon on that
  column header, untick everything except `rate_to_gbp`, untick **Use original
  column name as prefix**, then select **OK**.
* Add a calculated column for the converted amount:
  * On the **Add column** tab, select **Custom column**.
  * Name it `amount_gbp`.
  * Formula: `[amount_local] * [rate_to_gbp]`
  * Select **OK**.
* Set `amount_gbp`'s data type to **Decimal Number** (fixed decimal is fine too).

**Explanation:** this single merge step is doing the job of a manual FX conversion
spreadsheet — matching each transaction's currency and month to the right rate, then
multiplying it out — but it's now a repeatable, refreshable, auditable step instead
of a one-off exercise redone every month.

> ### 🗣️ SAY THIS
>
> *"This is the moment I want you to picture your month-end currency conversion
> process. Instead of VLOOKUPs across tabs, or a script someone maintains locally on
> their own laptop, this is one visual merge step that will re-run identically every
> time this dataflow refreshes. Whoever owns this dataflow can update the FX rates
> table next month, hit refresh, and every downstream number recalculates
> automatically — no one has to remember to redo this by hand, and no one can
> accidentally use last month's rate."*

### Step 7: Enrich Actuals with Cost Centre Attributes

* With `gl_actuals_clean` selected, select **Merge queries** again.
* Left table: `gl_actuals_clean`, select `cost_centre_id`.
* Right table: `cost_centre_master`, select `cost_centre_id`.
* **Join kind:** Left Outer. Select **OK**.
* Expand the new column, keeping `division`, `region`, `country` and
  `cost_centre_manager` (untick the prefix option again).
* Remove now-redundant columns you no longer need downstream: select
  `cost_centre_name` (the one still in local casing from the source) and
  `amount_local`/`currency`/`rate_to_gbp` if you want a slimmer table — for this lab,
  **keep them all** so we can show the audit trail from local currency to GBP.

### Step 8: Set the Output Destination

* On the **Home** tab, select **Add data destination** → **Lakehouse**.
* Choose `finance_lh`.
* Set the destination table name to `silver_gl_actuals`.
* Set **Update method** to **Replace** (a full refresh — appropriate for a lab; in
  production Renishaw might use **Append** with incremental logic for a large
  ledger).
* Repeat **Add data destination** for the `cost_centre_master` and `fx_rates` queries
  too (as `silver_cost_centre_master` and `silver_fx_rates`), so the whole Silver
  layer is captured in the Lakehouse, not just the fact table.
* Select **Save and run** (top-right, near **Publish**) and wait for the dataflow to
  complete — the status shows in the bottom-left and in the workspace item list.

**Explanation:** the destination step is what turns a Power Query transformation
into a **persisted, reusable table** other people and other tools can query — this is
what separates a Dataflow Gen2 from Power Query used only inside a single Power BI
report.

> ### 🗣️ SAY THIS
>
> *"Now this Silver table lives in the Lakehouse. It's not locked inside my dataflow
> or inside one Power BI report — a warehouse, a notebook, another dataflow, or a
> completely different Power BI report can all read `silver_gl_actuals` straight
> away, with no copy-pasting and no re-building the same cleaning logic somewhere
> else. That reuse is the biggest structural difference from Power Query in Power BI
> Desktop, which I'll show you properly once we've finished the Gold layer. Think of
> this as the moment the data stops being 'my query' and starts being 'the
> business's table'."*

---

## Part C: Build the Gold Layer — Actual vs Budget Variance

The Gold layer answers a business question directly: **how is each division tracking
against budget, by month, in GBP?** This is the table Power BI reports should point
at.

### Step 9: Create the Gold Dataflow

* Return to the workspace.
* Select **New item** → **Dataflow Gen2** → name it `gold_finance_variance`.

### Step 10: Bring in the Silver Tables and the Budget

* **Get data** → **Lakehouse** → `finance_lh` → select `silver_gl_actuals`.
* **Get data** → **Lakehouse** → `finance_lh` → select `silver_cost_centre_master`.
* **Get data** → OneLake/Lakehouse **Files** → `Files/bronze/gl_budget.csv` (the
  budget was never modified in Silver, so it's fine to read it straight from Bronze
  here — the value here is that it's already in GBP and doesn't need currency
  conversion).

### Step 11: Aggregate Actuals by Division, Region, Period and Account Category

* Select `silver_gl_actuals`.
* On the **Transform** tab, select **Group by**.
* Select **Advanced** to add multiple grouping columns: `division`, `region`,
  `period`, `account_category`.
* Add a new column named `actual_amount_gbp`, **Operation:** Sum, **Column:**
  `amount_gbp`.
* Select **OK**.
* Rename this query to `actuals_by_division_period`.

### Step 12: Aggregate Budget by Division, Region, Period and Account Category

* Select the `gl_budget` query.
* First merge it with `silver_cost_centre_master` (via `cost_centre_id`) to bring in
  `division` and `region`, expanding just those two columns — same technique as
  Step 7.
* On the **Transform** tab, select **Group by**, grouping on `division`, `region`,
  `period`, `account_category`, with a new **Sum** column named `budget_amount_gbp`
  on `budget_amount_gbp`.
* Rename this query to `budget_by_division_period`.

### Step 13: Merge Actuals and Budget into One Variance Table

* Select `actuals_by_division_period`.
* **Merge queries**, matching on `division`, `region`, `period` and
  `account_category` against `budget_by_division_period`.
* **Join kind:** Full Outer (so a division/period with budget but no actuals yet, or
  vice versa, still appears).
* Expand the merged column, keeping only `budget_amount_gbp`.
* Replace any resulting `null` values in `actual_amount_gbp` or `budget_amount_gbp`
  with `0` (select the column → right-click → **Replace Values**, find `null`
  replace with `0`).
* Add a **Custom column** named `variance_gbp`:
  `[actual_amount_gbp] - [budget_amount_gbp]`
* Add another **Custom column** named `variance_pct`:
  `if [budget_amount_gbp] = 0 then null else [variance_gbp] / [budget_amount_gbp]`
* Rename this query to `gold_actual_vs_budget`.

**Explanation:** this is now a business-ready, decision-grade table. A Renishaw FP&A
analyst — or an executive in Power BI — can filter this by division or region and
immediately see where spend or revenue is ahead or behind budget, in the group
reporting currency, without needing to know anything about FX rates, cost centre
codes or which ERP the number originally came from.

> ### 🗣️ SAY THIS
>
> *"This is the payoff. Three source files that started life in different systems,
> different currencies and different naming conventions have become one clean,
> governed table that answers a real finance question: 'are we on budget?' And it
> will refresh on whatever schedule Renishaw sets, without anyone re-doing this work
> by hand every month. If a new month of actuals lands in Bronze tomorrow, this
> entire Silver-to-Gold journey — cleaning, currency conversion, enrichment,
> aggregation, variance — replays automatically the next time it refreshes."*

### Step 14: Set the Gold Output Destination

* Select `gold_actual_vs_budget`.
* **Add data destination** → **Lakehouse** → `finance_lh`.
* Table name: `gold_actual_vs_budget`. **Update method:** Replace.
* Optionally also persist `actuals_by_division_period` and
  `budget_by_division_period` as Lakehouse tables if you want to show the
  intermediate aggregates too — not required for the demo.
* Select **Save and run**, and wait for it to finish.

### Step 15: Preview the Result

* Open `finance_lh` → **Tables** → select `gold_actual_vs_budget`.
* Sort or filter by `variance_pct` to show the biggest overspends/underspends by
  division.

> ### 🗣️ SAY THIS
>
> *"If we had time today, this is exactly the table I'd plug straight into a Power
> BI report — one visual for actual vs budget by division, one for the trend by
> month, maybe a matrix broken down by region. That's normally the next session.
> The point I want to leave you with here is that all of that reporting work becomes
> much easier and much more trustworthy once it's sitting on top of a single, clean,
> pre-aggregated Gold table like this one, rather than each report author having to
> re-derive variance logic themselves."*

---

## Part D: Power Query in Fabric vs. Power Query in Power BI Desktop

This is a natural point to step back from the click-through and have a conversation
about **why** Renishaw would use Dataflows Gen2 rather than just building this logic
as Power Query steps inside a Power BI Desktop report.

> ### 🗣️ SAY THIS
>
> *"Everything we just did — merges, group by, custom columns, replace values — you
> can do all of that inside Power BI Desktop's Power Query Editor too. So why bother
> with a separate Dataflow? It comes down to where the logic and the data end up
> living once you're done. In Power BI Desktop, all of that transformation logic is
> baked into one report file, on one person's machine. Here, it's a standalone
> item, sitting in the Fabric workspace, that anything else can plug into. Let me
> show you where the two genuinely diverge."*

| Aspect | Power Query in **Power BI Desktop** | Power Query in **Fabric (Dataflow Gen2)** |
| --- | --- | --- |
| **Where it runs** | On the report author's machine (or the Power BI service capacity at refresh time), and the transformed data is embedded inside that one `.pbix`/semantic model. | Runs as its own Fabric item on Fabric compute, independent of any single report. |
| **Reusability** | Query logic and output data are private to that one report unless copy-pasted into another. | Output lands as a table in a Lakehouse/Warehouse in OneLake — any number of Power BI reports, Warehouses, Notebooks or other Dataflows can consume it. |
| **Refresh & orchestration** | Refreshes as part of that report's own scheduled refresh; no native way to sequence it with other data loads. | Has its own refresh schedule, can be triggered by a **Fabric Data Pipeline**, and can be chained after/before other dataflows or notebooks. |
| **Staging & compute** | Limited primarily by the Desktop machine's memory (for local refreshes) or the capacity's per-report memory limit in the service. | Backed by Fabric's Dataflow staging (Lakehouse-backed), better suited to larger volumes and multiple large merges. |
| **Governance/lineage** | Lives inside a single `.pbix`; harder to see reused across an org without inspecting every report. | First-class Fabric item with its own workspace permissions, and appears in **OneLake data hub** / lineage view, so data teams can see what feeds what. |
| **Connectors** | Full Power Query connector library available. | Same Power Query engine and largely the same connector library, plus native **Lakehouse/Warehouse/OneLake** destinations that Desktop doesn't have. |
| **Best for** | Shaping data for one report, quick one-off analysis, prototyping. | Shared, governed, repeatable data preparation feeding multiple downstream consumers — exactly this Bronze→Silver→Gold pattern. |
| **Where Dataflows Gen2 hits its own limits** | — | Very large, high-frequency (e.g. near-real-time, sub-minute) loads are usually better served by a **Warehouse/Lakehouse notebook with Spark**, or a **Fabric Data Pipeline** with native copy activities, rather than Dataflow Gen2's Power Query engine. Extremely complex row-by-row procedural logic can also be easier to express and unit-test in a notebook than in the M language behind Power Query. |

**Explanation for the room:** the transformation *language* (Power Query / M) is
identical in both places — that's why everything we clicked through today will feel
instantly familiar to anyone who has built a Power BI report. What changes is the
**deployment model**: Dataflows Gen2 turn Power Query from a report-embedded
convenience into a governed, reusable, schedulable **data product** that lives
independently in OneLake. For Renishaw, that's the difference between "the finance
analyst's personal query" and "the group's trusted actual-vs-budget table".

> ### 🗣️ SAY THIS
>
> *"So the short version: same Power Query skills your team already has from Power
> BI and Excel, but Dataflows Gen2 turn that into something Renishaw's whole data
> estate can rely on — refreshed on schedule, sitting in one place in OneLake,
> governed like any other Fabric item. You don't need to throw away anything your
> team already knows to get there; you just need to move the transformation out of
> an individual report and into a shared, reusable layer. That's really the whole
> pitch behind medallion architecture on Fabric."*

---

## Advanced Extensions (Optional)

These three extensions are **optional add-ons**, not required to complete the core
Bronze/Silver/Gold story above. Use them if time allows, or as a "what else is
possible" close-out. Budget roughly 10–15 minutes total if you do all three. Each one
builds directly on queries you've already created, so nothing new needs to be
imported.

> ### 🗣️ SAY THIS
>
> *"Everything so far is what most teams need day to day. But since we've got a bit
> more time, let me show you three features that come up once your data preparation
> grows beyond a handful of source files — reusable logic so you're not repeating
> yourself, matching messy free-text when a clean ID isn't available, and making a
> single dataflow flexible enough to serve more than one scenario without
> duplicating it. None of these are required to get value from Dataflows Gen2 — think
> of them as 'what's possible once you're comfortable with the basics'."*

### Extension 1: Custom Functions — Turn Repeated Cleaning Steps into One Reusable Function

**Why it matters for Renishaw:** in Step 4, you cleaned `cost_centre_name` and
`description` using the same two operations (Trim, then Clean) applied twice, by
hand. A **custom function** lets you write that logic once and re-use it on any
column, in any query, in any dataflow — exactly what you'd want once Renishaw has
more than a couple of source systems each needing the same text clean-up.

* In `silver_finance_prep`, right-click in the blank space at the bottom of the
  **Queries** pane → **New query** → **Blank query**.
* Rename it to `fn_CleanText`.
* On the **Home** tab, select **Advanced Editor** and replace the contents with:

  ```
  (inputText as any) as text =>
      let
          textValue = Text.From(inputText),
          trimmed = Text.Trim(textValue),
          cleaned = Text.Clean(trimmed)
      in
          cleaned
  ```

* Select **Done**. Notice the query's icon changes to `fx` in the Queries pane — Power
  Query has recognised this as a **function**, not a table, so it won't try to load
  it anywhere by itself.
* Go to `gl_actuals_clean`. Select the `description` column.
* On the **Add column** tab, select **Invoke Custom Function**.
* **New column name:** `description_clean`. **Function query:** `fn_CleanText`.
* Under **inputText**, choose **Column** and select `description`.
* Select **OK** — a new `description_clean` column appears, already trimmed and
  cleaned.
* Repeat **Invoke Custom Function** for `cost_centre_name` (new column name
  `cost_centre_name_clean`).
* Remove the two original untreated columns and rename the `_clean` columns back to
  `description` and `cost_centre_name` (right-click → **Remove**, then right-click
  the `_clean` columns → **Rename**).

**Explanation:** you've replaced two manual, one-off formatting steps with a single
piece of logic that can now be invoked on *any* text column, in *any* query, in *any*
dataflow you build later — a new source system with the same messy-text problem
takes one click, not a rebuild.

> ### 🗣️ SAY THIS
>
> *"This is where Power Query stops being just 'a series of clicks' and starts
> behaving like a small code library. If Renishaw brings on a sixth division next
> year with its own slightly messy ERP export, this exact function is ready to
> reuse — no one has to remember or re-build the cleaning steps from scratch, and if
> we ever need to change the cleaning rule itself, we only have to change it in this
> one place and every query that uses it picks up the fix automatically."*

### Extension 2: Fuzzy Merge — Matching Text That Doesn't Match Exactly

**Why it matters for Renishaw:** Step 7 matched `gl_actuals_clean` to
`cost_centre_master` using `cost_centre_id` — a clean, exact key. In the real world,
not every system exports a clean ID; sometimes the only common field is a
free-text name, and those names rarely match character-for-character across
systems (extra spaces, "Sys" vs "Systems", different capitalisation — exactly the
kind of thing baked into a few rows of `gl_actuals.csv` in this lab).

* Still in `silver_finance_prep`, go to **Merge queries** as if repeating Step 7, but
  this time select `cost_centre_name` as the join column on both sides (instead of
  `cost_centre_id`).
* In the bottom-left of the **Merge** dialog, tick **Use fuzzy matching to perform
  the merge**.
* Expand **Fuzzy matching options**:
  * **Similarity threshold**: drag it down from `1.00` (exact match only) to around
    `0.80` and explain that this is a slider between "must match exactly" and
    "match almost anything".
  * **Ignore case** and **Match by combining text parts** are both enabled by
    default — point these out as the settings that let `"Metrology Systems - UK
    Manufacturing  "` (with trailing spaces) still match `"Metrology Systems - UK
    Manufacturing"`.
* Select **OK** and look at the row count in the preview compared to the exact-match
  version from Step 7 — with fuzzy matching, rows that previously failed to match
  due to whitespace/casing differences now join successfully.
* **You do not need to keep this query** — this is a "just to show it" moment. Select
  **Remove** on this new merge step from the Applied Steps pane afterwards so the
  main Silver query stays on the clean, exact `cost_centre_id` join used for the rest
  of the lab.

**Explanation:** fuzzy merge is not "on" by default because approximate matching
should be a deliberate choice, not an accident — you don't want two genuinely
different cost centres silently merged together. It's there for exactly the
situation where the only common field across two systems is imperfect free text.

> ### 🗣️ SAY THIS
>
> *"I want to be upfront that we don't use fuzzy matching in our main pipeline
> today — a clean ID join is always safer where one's available, because it can
> never accidentally join two different things together. But when the only thing
> two systems have in common is a name someone typed by hand, this is the tool that
> saves you from a painful manual reconciliation exercise in Excel, matching things
> up row by row. The similarity threshold is your safety valve — the closer to 1.00
> you keep it, the more conservative the matching, so you'd tune this carefully
> rather than leaving it wide open."*

### Extension 3: Dataflow Parameters — One Dataflow, Multiple Scenarios

**Why it matters for Renishaw:** right now, `gold_finance_variance` always
calculates variance across every division and every period in the source data. A
**parameter** lets you turn a fixed dataflow into a flexible one — for example, "only
show me this one division" or "only look from this cut-off date onwards" — by
changing a single value, with no changes to any transformation step. (A colleague's
session covers driving this from a **Data Pipeline** automatically; here we'll just
show the parameter working manually inside the dataflow itself.)

* In `gold_finance_variance`, on the **Home** tab, select **Manage parameters** →
  **New parameter**.
* Set:
  * **Name:** `TargetDivision`
  * **Type:** Text
  * **Required:** Yes
  * **Current Value:** `All`
* Select **OK**. Notice `TargetDivision` now appears in the Queries pane under its
  own **Parameters** group.
* Select the `gold_actual_vs_budget` query. On the **Home** tab, select **Reduce
  Rows** → **Filter Rows** (or right-click the `division` column header → **Text
  Filters** → **Custom Filter**), and instead of a fixed value, add a **Custom
  column** first:
  * **Add column** → **Custom column** → name it `keep_row`.
  * Formula: `if TargetDivision = "All" then true else [division] = TargetDivision`
* Filter the `keep_row` column to keep only `TRUE`, then remove the helper
  `keep_row` column.
* Select **Save and run** once with the parameter left as `All` — confirm every
  division still appears.
* Now go back to **Manage parameters**, change `TargetDivision`'s **Current Value**
  to `Metrology Systems`, and select **Save and run** again.
* Open `gold_actual_vs_budget` in the Lakehouse and confirm only Metrology Systems
  rows are now present. Change the parameter back to `All` afterwards so the
  dataflow is left in its default state.

**Explanation:** nothing about the transformation logic changed between those two
runs — only the parameter value did. That's the difference between a one-off report
and a genuinely reusable data product: the same dataflow can serve "give me
everything" and "give me just Metrology Systems" without being rebuilt or
duplicated.

> ### 🗣️ SAY THIS
>
> *"This is the building block that makes automation possible. Today I changed this
> value by hand, but the exact same parameter is what a scheduled pipeline would set
> automatically — say, running this once per division every month-end without
> anyone touching the dataflow itself, or letting a report page pass in whichever
> division the user has selected. That orchestration piece is what's being covered
> in the follow-up session, but the important thing to take away here is that
> parameters are what turn a single dataflow into something that can serve many
> different requests, rather than needing a separate copy built for each one."*

---

## Recap Table

| Layer | Item built | What it does | Renishaw value |
| --- | --- | --- | --- |
| Bronze | Files in `finance_lh` | Raw CSVs landed untouched | Audit trail back to source |
| Silver | `silver_finance_prep` dataflow → `silver_gl_actuals`, `silver_cost_centre_master`, `silver_fx_rates` | Cleans text, removes duplicates, converts currency to GBP, enriches with division/region | One trusted, reusable, GBP-standardised transaction table |
| Gold | `gold_finance_variance` dataflow → `gold_actual_vs_budget` | Aggregates actuals and budget by division/region/period, calculates variance | Decision-ready table for Power BI / FP&A reporting |
| Advanced (optional) | `fn_CleanText` custom function, fuzzy merge demo, `TargetDivision` parameter | Reusable cleaning logic, approximate text matching, flexible single-dataflow scenarios | Shows the pipeline scales beyond a one-off build |

---

## Troubleshooting

* **Lakehouse Files don't show the uploaded CSVs:** confirm you uploaded into the
  `Files` area (not `Tables`), and refresh the Explorer pane.
* **Merge produces no matches / all nulls after expand:** double-check the join
  columns are the *same data type* on both sides (e.g. `period` and `rate_month`
  must both be typed as Date, not Date as Text on one side).
* **`Add data destination` is greyed out or missing:** confirm you have permission to
  write to the selected Lakehouse, and that the query doesn't still contain an error
  (a red warning triangle in the Queries pane) — fix the error first.
* **Dataflow "Save and run" takes a long time:** normal for the first run of a new
  Dataflow Gen2 while Fabric provisions its Mashup/staging compute; subsequent runs
  are typically faster.
* **`variance_pct` shows an error instead of a number:** confirm the "replace nulls
  with 0" step ran *before* the custom column, and that both `actual_amount_gbp` and
  `budget_amount_gbp` are numeric (not text) types.
* **Numbers look off after currency conversion:** the FX rates in this lab are
  synthetic and randomised — that's expected and fine for a demo; just don't treat
  the actual figures as real Renishaw numbers in front of the customer.
