
# E-Commerce Delivery SLA, Customer Satisfaction & Retention Analysis

## 1. Problem Statement & Business Objective
**Problem Statement:** Olist has a low repeat-purchase rate and a significant share of 1–2 star reviews. This project analyzes delivered orders (Jan 2017 to Aug 2018) to measure how late delivery affects review scores and repeat purchases, identify which sellers, states, and categories contribute most to late deliveries, and recommend where Olist should intervene first.

**Objective:** Build an end-to-end relational analytics pipeline (**MySQL + Python + Power BI**) to:
1. Quantify the exact impact of late deliveries (`delivered_customer_date > estimated_delivery_date`) on customer review ratings (1–5 stars) and repeat buyer conversion (`customer_unique_id`).
2. Decompose delivery delays into **merchant dispatch delay** vs. **carrier transit delay** to isolate operational accountability.
3. Identify the top-contributing **sellers, customer/seller states, and product categories** driving late deliveries using Pareto analysis, and deliver quantified intervention priorities.

---

## 2. Core KPI Framework

| Role | KPI | Exact Formula | What It Measures |
| :--- | :--- | :--- | :--- |
| **Primary** | **% Late Deliveries** | $\frac{\text{Orders Delivered After Estimated Date}}{\text{Total Delivered Orders}} \times 100$ | Core operational SLA failure rate |
| **Supporting** | **Avg Review Score** | $\text{Mean}(\text{review\_score})$ (1–5 scale) | Overall post-delivery customer satisfaction |
| **Supporting** | **% Negative Reviews** | $\frac{\text{Reviews with Score 1 or 2}}{\text{Total Reviews}} \times 100$ | Severe customer dissatisfaction rate |
| **Supporting** | **Avg Delay (Days)** | $\text{Delivered Date} - \text{Estimated Date}$ *(late orders only)* | Severity of SLA breaches in days |
| **Supporting** | **Repeat Purchase Rate (%)** | $\frac{\text{Unique Buyers (customer\_unique\_id) with } \ge 2 \text{ Orders}}{\text{Total Unique Buyers}} \times 100$ | True buyer retention across order history |

---

## 3. Data Scope, Cleaning Rules & Limitations
* **Dataset:** Brazilian E-Commerce Public Dataset by Olist (~99,441 total orders across 9 relational tables)[cite: 1].
* **Analysis Scope:** Filtered to **delivered orders** placed between **January 2017 and August 2018** with valid delivery timestamps (`order_delivered_customer_date IS NOT NULL`).
* **Key Data Engineering Decisions:**
  * **Buyer Identity Resolution:** Used `customer_unique_id` rather than order-level `customer_id` to prevent false 0% repeat-rate calculations[cite: 1].
  * **Fan-Out Prevention:** Aggregated multi-item (`order_items`) and multi-review (`order_reviews`) tables to the `order_id` grain before joining to `fact_orders`[cite: 1].
  * **Geolocation Deduplication:** Collapsed >1M duplicate zip-code rows into 1 coordinate centroid per `zip_code_prefix`[cite: 1].
* **Limitations:** Public dataset does not expose internal carrier SLA contracts, product return/refund logs, or customer support tickets.

---

## 4. Technical Architecture & Workflow
* **Database Layer (`MySQL 8.0+`):**
  * `olist_bronze`: Raw ingestion of all 9 CSVs via Python (`Pandas` + `SQLAlchemy`) with row/null audit logging (`olist_audit.etl_run_log`)[cite: 1].
  * `olist_silver`: Cleaned Star Schema (`fact_orders`, `fact_order_items`, `dim_customers`, `dim_sellers`, `dim_products`, `dim_geolocation`) with automated anomaly checks (`olist_audit.dq_anomalies`)[cite: 1].
  * `olist_gold`: Analytical SQL views computing order-level delivery metrics, seller scorecards, category/state delay breakdowns, and buyer repeat cohorts.
* **Analysis Layer (`Python — Pandas, SciPy, Matplotlib/Seaborn`):**
  * Exploratory data analysis, Pareto concentration (80/20 seller & route contribution), and non-parametric statistical testing (Mann-Whitney U / Chi-Square) proving rating and repeat-rate drops on late orders.
* **Visualization Layer (`Power BI Desktop`):**
  * Interactive dashboard connected directly to `olist_gold` featuring KPI cards, monthly late-delivery trendlines, state-level delay heatmaps, and seller/category intervention drill-downs.

```text
olist-delivery-retention-analysis/
├── data/raw/                   # Raw Kaggle Olist CSVs (gitignored)[cite: 1]
├── etl/
│   ├── 01_ingest_bronze.py     # Raw CSV ingestion + audit logging[cite: 1]
│   ├── 02_dq_checks.sql        # Automated data quality checks[cite: 1]
│   └── 03_build_silver.sql     # Star Schema DDL/DML[cite: 1]
├── sql/
│   ├── 01_gold_analytics_views.sql  # Delivery, review & repeat-buyer SQL views
│   └── 02_diagnostic_queries.sql    # Pareto & root-cause insight queries
├── notebooks/
│   └── 01_eda_and_hypothesis_testing.ipynb  # Charts + statistical tests
├── powerbi/                    # .pbix dashboard + exported screenshots[cite: 1]
└── README.md