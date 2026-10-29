# Data Profiling & Quality Assessment Report
**Project:** Electric Vehicle Market Performance & Insights  
**Author:** AI & Data Science Student  
**Evaluation Role:** Senior Data Analyst & BI Developer  
**Status:** Completed & Ready for Review

---

## 1. Executive Summary
This report presents an in-depth data profiling, structural verification, and quality audit of the electric vehicle (EV) dataset provided for the **Electric Vehicle Market Performance & Insights** project.

Two raw CSV files were supplied:
1. `data/raw/ev_market_train.csv` (200,000 records, 44.33 MB)
2. `data/raw/ev_market_test.csv` (100,000 records, 23.24 MB)

Our automated profiling confirms that the datasets represent a comprehensive, rich, and high-fidelity global electric vehicle market database encompassing **37 core vehicle attributes**. The dataset covers 200 automotive manufacturers, 15 vehicle categories, 5 advanced battery chemistries, and spans model years **2018 through 2026** across 7 global market regions.

---

## 2. File Verification & Structural Schema

| Property | `ev_market_train.csv` | `ev_market_test.csv` | Unified Master (`electric_vehicles_cleaned.csv`) |
|:---|:---|:---|:---|
| **Row Count** | 200,000 | 100,000 | 299,999 (1 duplicate dropped) |
| **Column Count** | 37 | 37 | 38 (includes `split_source`) |
| **File Size** | 44.33 MB | 23.24 MB | ~67.5 MB |
| **ID Column** | `vehicle_id` (`EV######`) | `vehicle_id` (`EV######`) | `vehicle_id` (Unique Primary Key) |
| **Duplicate Rows** | 1 (Row 83209 & 199999) | 0 | 0 (Deduplicated) |
| **Model Year Span** | 2018 – 2026 | 2018 – 2026 | 2018 – 2026 |
| **Manufacturers** | 200 distinct | 200 distinct | 200 distinct |

### Schema Parity
Both files share an **exact, 100% column parity**. The 37 columns include all critical business, technical, and consumer fields required by this analytics solution:
- **Identification & Manufacturer:** `vehicle_id`, `model_name`, `manufacturer`, `model_year`, `manufacturing_country`, `market_region`
- **Classification:** `category`, `recommended_use_case`
- **Powertrain & Performance:** `motor_power_kw`, `torque_nm`, `num_motors`, `drivetrain`, `top_speed_kmph`, `acceleration_0_100_sec`
- **Battery & Charging:** `battery_capacity_kwh`, `battery_type`, `battery_cycle_life`, `battery_degradation_pct_5yr`, `range_km`, `efficiency_wh_per_km`, `max_dc_charging_kw`, `charging_dc_fast_time_min`, `charging_ac_time_hr`, `num_charging_ports`
- **Physical Specifications:** `num_seats`, `weight_kg`, `cargo_capacity_liters`
- **Economics & Market Performance:** `price_usd`, `insurance_cost_usd_yearly`, `warranty_years`, `resale_value_pct_3yr`, `annual_sales_units`
- **Consumer & Safety Metrics:** `safety_rating_stars`, `autonomous_level`, `infotainment_screen_inch`, `co2_saved_tons_per_year`, `customer_rating`

---

## 3. ID Overlap & Train/Test Relationship Evaluation

### Does the Test File Represent "Future" Data?
**Finding:** **No.**
- In temporal forecasting datasets, a test set consists of future years (e.g., train: 2018–2023, test: 2024–2026).
- However, in this dataset, **both files span the exact same timeline (2018 to 2026)** with identical distributions across years, categories, and countries.
- This confirms the dataset was partitioned via random cross-validation sampling rather than a temporal cutoff.

### Overlapping Vehicle IDs Check
**Finding:** **Zero Overlap (0.0%).**
- `set(train['vehicle_id']) ∩ set(test['vehicle_id']) = ∅`
- There are **199,999 unique IDs** in `train` and **100,000 unique IDs** in `test`.
- Because there is zero vehicle ID collision, combining the records produces **299,999 distinct real-world vehicle profiles**.

### Why We Do Not Train a Machine Learning Model
This project is strictly scoped as a **Business Intelligence and Data Analytics solution**. Business decision-makers in automotive strategy do not need black-box predictions; they need:
1. Descriptive analytics on market share, top manufacturers, and pricing trends.
2. Diagnostic analytics comparing battery technologies (LFP vs NMC vs Solid-State vs Sodium-Ion).
3. Prescriptive insights to identify whitespace opportunities in vehicle categories and charging performance.

To honor complete data lineage, each record in our processed dataset carries a `split_source` attribute (`train` or `test`), preserving complete auditability.

---

## 4. Data Quality, Null Values & Anomalies

### Missing Value Audit
Out of 37 columns, **32 columns have 0 missing values (100% complete)**. Missing values were isolated to only 5 optional attributes with very low missingness (< 3.1%):

| Column | Train Null Count (%) | Test Null Count (%) | Imputation Strategy |
|:---|:---:|:---:|:---|
| `battery_cycle_life` | 3,786 (1.89%) | 2,028 (2.03%) | Median by `battery_type` chemistry |
| `customer_rating` | 3,977 (1.99%) | 1,931 (1.93%) | Median by `category` vehicle class |
| `annual_sales_units` | 2,028 (1.01%) | 989 (0.99%) | Median by `category` vehicle class |
| `resale_value_pct_3yr` | 6,103 (3.05%) | 3,057 (3.06%) | Median by `category` vehicle class |
| `infotainment_screen_inch` | 3,102 (1.55%) | 1,506 (1.51%) | Median by `category` vehicle class |

### Duplicates Audit
- **Train Set:** Exactly 1 duplicate record was identified (Row index 83,209 and Row 199,999, `vehicle_id` `EV229214`, AmpereMotors Bolt-400). This duplicate was safely removed.
- **Test Set:** 0 duplicate rows found.

### Boundary & Anomaly Audit
All numerical values were checked against domain thresholds:
- No negative numbers in price, range, battery capacity, acceleration, or sales.
- Ranges correspond to realistic vehicle dynamics:
  - Minimum range: 55 km (Micro City Cars / Two-Wheelers)
  - Maximum range: 660 km (Long-range Executive Sedans / Grand Tourers)
  - Minimum price: $900.21 (Two-wheelers)
  - Maximum price: $409,995.49 (Electric Buses & Specialized Heavy Vehicles)
  - Customer ratings: bounded within `1.52` to `5.00` stars.

---

## 5. Cleaned Dataset Deliverables

The raw CSV files remain **100% unmodified and preserved** in `data/raw/`.

The data pipeline has generated three clean outputs in `data/processed/`:
1. `electric_vehicles_cleaned.csv`: Master unified dataset (299,999 records, 0 nulls, 38 columns).
2. `ev_market_train_cleaned.csv`: Cleaned training subset (199,999 records, 0 nulls).
3. `ev_market_test_cleaned.csv`: Cleaned test subset (100,000 records, 0 nulls).

---

## 6. Suitability Verdict for BI & SQL Analytics
**Verdict: Highly Suitable (A+ Quality).**
The dataset possesses excellent statistical distribution, diverse categorical variety, zero schema discrepancies, and realistic automotive metrics. It is ready for:
- SQLite relational database modeling and analytical SQL queries.
- Modular Pandas aggregation routines.
- Interactive Plotly visualizations and Flask web application.
- Tableau Public dashboards and multi-scene Tableau Story.
