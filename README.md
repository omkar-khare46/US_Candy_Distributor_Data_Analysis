# 🍬 US Candy Distributor — Data Warehouse & BI Analytics

An end-to-end data engineering and analytics project: raw CSV exports from a US candy distributor are cleaned, modeled into a star-schema data warehouse, and surfaced in an interactive Power BI dashboard.

Built as a portfolio project to demonstrate the full pipeline — **ETL (Python) → Data Warehouse (MySQL) → BI Dashboard (Power BI)** — rather than analysis on a single flat file.

---

## 📌 Project Overview

The dataset covers order-level sales for a candy distributor across 15 products, 5 factories, and customers in the US and Canada, alongside sales targets by division and a US ZIP-code geographic reference table.

**Goals:**
- Build a reproducible ETL pipeline that turns messy source CSVs into a clean, validated warehouse
- Design a proper star schema (fact + dimension tables) rather than working off flat files
- Load the cleaned, modeled data into a production-style MySQL warehouse
- Surface the data in an interactive BI dashboard, including a geospatial logistics-efficiency analysis using the Haversine formula

---

## 🏗️ Architecture

```
                     ┌─────────────────┐
   Raw CSVs  ──────► │   extract.py    │  Read + profile 5 source tables
 (data/raw/)         └────────┬────────┘
                               │
                     ┌─────────▼────────┐
                     │  transform.py    │  Clean dtypes, dedupe, validate
                     │                  │  keys, trim US Zips to Sales-only
                     └────────┬─────────┘
                               │
                    (data/processed/*.parquet)
                               │
                     ┌──────────▼─────────┐
                     │   load_mysql.py     │  Create schema, load in
                     │                     │  FK-safe order
                     └──────────┬──────────┘
                                │
                     ┌───────────▼────────────┐
                     │  Star Schema Warehouse  │
                     │       (MySQL)           │
                     │  fact_sales +           │
                     │  dim_products,          │
                     │  dim_factories,         │
                     │  dim_targets,           │
                     │  dim_geography          │
                     └───────────┬────────────┘
                                 │
                     ┌───────────▼────────────┐
                     │   Power BI Dashboard    │
                     │  (Sales / Product /     │
                     │   Logistics pages)      │
                     └────────────────────────┘
```

### Star Schema

- **`fact_sales`** — one row per order line, FKs to `product_id` and `division` (enforced)
- **`dim_products`** — product catalog, FKs to `dim_factories` and `dim_targets`
- **`dim_factories`** — the 5 production facilities and their coordinates
- **`dim_targets`** — sales target per division
- **`dim_geography`** — US ZIP-code reference data (lat/lng, city, state, timezone), trimmed to only the ZIP codes present in Sales

> **Note:** `postal_code` in `fact_sales` has **no enforced foreign key** to `dim_geography` — the geography reference table is US-only, but Sales legitimately includes Canadian orders (23 rows). This is a documented modeling decision, not a data quality gap.

---

## 📂 Repository Structure

```
US_Candy_Distributor/
│
├── data/
│   ├── raw/                     # original source CSVs
│   └── processed/                # cleaned parquet checkpoints
│
├── sql/
│   ├── schema_mysql.sql              # star schema DDL
│   └── validation_queries_mysql.sql   # post-load checks
│
├── src/
│   ├── extract.py                  # Stage 1: read + profile raw CSVs
│   ├── transform.py                 # Stage 2: clean, validate, dedupe
│   └── load_mysql.py                 # Stage 3: load into MySQL
│
├── notebooks/
│   └── exploratory_data_analysis.ipynb  # EDA, Haversine logistics analysis,
│                                          # factory reallocation optimization
│
├── dashboard/
│   └── candy_distributor.pbix         # Power BI dashboard file
│
├── docs/
│   └── screenshots/                    # dashboard page screenshots
│
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 📊 Dashboard

Built in Power BI, connected directly to the MySQL warehouse.

### Page 1 — Sales Analysis
KPI cards (Revenue, Customers, Profit, Profit Margin %), revenue by ship mode, revenue/profit trend over time, revenue by division, revenue by region, and top 10 cities by profit.

![Sales Analysis](docs/screenshots/sales_analysis.png)

### Page 2 — Product Analysis
Revenue by product and by factory, division/product slicers, revenue-by-division breakdown, and revenue-vs-target gauges per division.

![Product Analysis](docs/screenshots/product_analysis.png)

### Page 3 — Logistics Efficiency *(in progress)*
Haversine-distance-based route efficiency: profit-per-mile by route, most/least efficient shipping lanes, and the factory reallocation savings opportunity identified in the EDA notebook.

---

## ✅ Data Validation

The loaded warehouse was validated against the raw source data to confirm the ETL pipeline introduced no loss, duplication, or corruption:

- **Row counts** match exactly across all 5 tables (5 factories, 3 targets, 15 products, 631 geography rows, 10,194 sales rows)
- **No duplicate primary keys** in `fact_sales` or `dim_products`
- **No orphaned foreign keys** — every `product_id`, `division`, and `factory_name` reference resolves correctly
- **Aggregate totals** (`SUM(sales)`, `SUM(gross_profit)`, `SUM(cost)`, `SUM(units)`) match the raw CSV exactly
- **Gross Profit consistency check** — `Gross Profit = Sales - Cost` holds for all 10,194 rows, with zero discrepancies

Validation queries are in `sql/validation_queries_mysql.sql`.

---

## 🔍 Key Findings

- **Chocolate** drives 93% of total revenue and runs at ~488% of its sales target — worth re-validating whether the target itself is outdated.
- The **"Other" division's** profit margin (37.7%) trails Chocolate and Sugar (57–67%) by a wide margin — flagged for follow-up.
- A **Haversine-distance analysis** of customer-to-factory shipping routes identified both highly efficient short-haul lanes (Phoenix-area, served by "Lot's O' Nuts") and inefficient long-haul routes with collapsed margins (Northeast routes served by "The Other Factory").
- Comparing actual vs. volume-weighted nearest-factory assignment surfaces a **potential 19–54% logistics-cost saving** on several products, most significantly on the high-volume Wonka Bar chocolate line.

---

## 🛠️ Tech Stack

- **Python** (pandas, SQLAlchemy) — ETL pipeline
- **MySQL** — data warehouse
- **Power BI** — dashboard and DAX/Power Query Haversine calculations
- **Jupyter Notebook** — exploratory data analysis

---

## 🚧 Future Work

- Complete the Logistics Efficiency dashboard page (Haversine distance, route mapping)
- Automate the pipeline end-to-end with a single orchestration script (`main.py`)
- Add unit tests for the transform logic
- Investigate and document the "Other" division margin gap

---

## 👤 Author

**Omkar Khare**
Assistant Professor (Mathematics) transitioning into Data Analytics
