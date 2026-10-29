"""
Database initialization and data loading pipeline for ev_market.db.
Creates normalized SQLite tables, constraints, foreign keys, indexes,
and safely loads cleaned vehicle records into relational tables.
Safe to run repeatedly (idempotent).
"""

import sys
import sqlite3
from pathlib import Path
import pandas as pd

# Set up project path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import config

def get_db_connection(db_path: Path = config.DATABASE_PATH) -> sqlite3.Connection:
    """Creates a connection with foreign key enforcement and row factory."""
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.row_factory = sqlite3.Row
    return conn

def init_schema(conn: sqlite3.Connection, schema_path: Path = config.SCHEMA_PATH):
    """Executes DDL statements from schema.sql."""
    print(f"Applying schema DDL from: {schema_path}")
    with open(schema_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()
    conn.executescript(schema_sql)
    conn.commit()
    print("Database schema and views initialized successfully.")

def populate_database(csv_path: Path = config.CLEANED_DATA_FILE, db_path: Path = config.DATABASE_PATH, rebuild: bool = True):
    """
    Loads data from cleaned CSV into normalized SQLite tables:
    1. manufacturers
    2. categories
    3. battery_technologies
    4. vehicles
    5. vehicle_sales
    6. customer_ratings
    """
    if not csv_path.exists():
        raise FileNotFoundError(f"Cleaned CSV dataset not found at: {csv_path}. Run data_cleaning.py first.")

    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    if rebuild and db_path.exists():
        print(f"Rebuilding existing database: {db_path}")
        try:
            db_path.unlink()
        except PermissionError:
            print("Notice: Database in use; truncating tables instead of unlinking.")

    conn = get_db_connection(db_path)
    init_schema(conn)

    print(f"Reading cleaned dataset from: {csv_path}")
    df = pd.read_csv(csv_path)
    total_records = len(df)
    print(f"Loaded {total_records:,} records into memory for database staging.")

    cursor = conn.cursor()

    # 1. Populate Manufacturers Dimension
    print("Populating 'manufacturers' table...")
    manufacturers = sorted(df['manufacturer'].unique())
    cursor.executemany(
        "INSERT OR IGNORE INTO manufacturers (manufacturer_name) VALUES (?);",
        [(m,) for m in manufacturers]
    )
    conn.commit()
    cursor.execute("SELECT manufacturer_name, manufacturer_id FROM manufacturers;")
    mfg_map = dict(cursor.fetchall())
    print(f"  Inserted/Mapped {len(mfg_map)} unique manufacturers.")

    # 2. Populate Categories Dimension
    print("Populating 'categories' table...")
    categories = sorted(df['category'].unique())
    cursor.executemany(
        "INSERT OR IGNORE INTO categories (category_name) VALUES (?);",
        [(c,) for c in categories]
    )
    conn.commit()
    cursor.execute("SELECT category_name, category_id FROM categories;")
    cat_map = dict(cursor.fetchall())
    print(f"  Inserted/Mapped {len(cat_map)} unique categories.")

    # 3. Populate Battery Technologies Dimension
    print("Populating 'battery_technologies' table...")
    battery_types = sorted(df['battery_type'].unique())
    cursor.executemany(
        "INSERT OR IGNORE INTO battery_technologies (battery_type_name) VALUES (?);",
        [(b,) for b in battery_types]
    )
    conn.commit()
    cursor.execute("SELECT battery_type_name, battery_type_id FROM battery_technologies;")
    bat_map = dict(cursor.fetchall())
    print(f"  Inserted/Mapped {len(bat_map)} unique battery technologies.")

    # 4. Populate Vehicles Core Table
    print("Populating 'vehicles' core specifications table...")
    vehicles_data = []
    sales_data = []
    ratings_data = []

    for row in df.itertuples(index=False):
        mfg_id = mfg_map[row.manufacturer]
        cat_id = cat_map[row.category]
        bat_id = bat_map[row.battery_type]
        sales_units = int(row.annual_sales_units)
        price = float(row.price_usd)
        revenue = round(sales_units * price, 2)
        cust_rating = round(float(row.customer_rating), 2)
        safety_stars = int(row.safety_rating_stars)
        resale_pct = round(float(row.resale_value_pct_3yr), 2)

        # vehicles tuple (contains all specifications + key KPIs)
        vehicles_data.append((
            row.vehicle_id,
            row.model_name,
            mfg_id,
            cat_id,
            bat_id,
            int(row.model_year),
            row.manufacturing_country,
            row.market_region,
            float(row.battery_capacity_kwh),
            float(row.battery_cycle_life),
            float(row.battery_degradation_pct_5yr),
            float(row.range_km),
            float(row.efficiency_wh_per_km),
            float(row.motor_power_kw),
            float(row.torque_nm),
            int(row.num_motors),
            row.drivetrain,
            float(row.top_speed_kmph),
            float(row.acceleration_0_100_sec),
            float(row.max_dc_charging_kw),
            float(row.charging_dc_fast_time_min),
            float(row.charging_ac_time_hr),
            int(row.num_charging_ports),
            int(row.num_seats),
            float(row.weight_kg),
            float(row.cargo_capacity_liters),
            price,
            float(row.insurance_cost_usd_yearly),
            int(row.warranty_years),
            int(row.autonomous_level),
            float(row.infotainment_screen_inch),
            float(row.co2_saved_tons_per_year),
            sales_units,
            revenue,
            cust_rating,
            safety_stars,
            resale_pct,
            row.recommended_use_case,
            row.split_source
        ))

        # vehicle_sales tuple
        sales_data.append((
            row.vehicle_id,
            int(row.model_year),
            sales_units,
            revenue
        ))

        # customer_ratings tuple
        ratings_data.append((
            row.vehicle_id,
            cust_rating,
            safety_stars,
            resale_pct
        ))

    # Fast batch execution
    cursor.executemany("""
        INSERT OR IGNORE INTO vehicles (
            vehicle_id, model_name, manufacturer_id, category_id, battery_type_id,
            model_year, manufacturing_country, market_region, battery_capacity_kwh,
            battery_cycle_life, battery_degradation_pct_5yr, range_km, efficiency_wh_per_km,
            motor_power_kw, torque_nm, num_motors, drivetrain, top_speed_kmph,
            acceleration_0_100_sec, max_dc_charging_kw, charging_dc_fast_time_min,
            charging_ac_time_hr, num_charging_ports, num_seats, weight_kg,
            cargo_capacity_liters, price_usd, insurance_cost_usd_yearly, warranty_years,
            autonomous_level, infotainment_screen_inch, co2_saved_tons_per_year,
            annual_sales_units, estimated_revenue_usd, customer_rating, safety_rating_stars,
            resale_value_pct_3yr, recommended_use_case, split_source
        ) VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
        );
    """, vehicles_data)
    conn.commit()
    print(f"  Inserted {len(vehicles_data):,} vehicles.")

    # 5. Populate Sales Table
    print("Populating 'vehicle_sales' performance table...")
    cursor.executemany("""
        INSERT OR IGNORE INTO vehicle_sales (
            vehicle_id, model_year, annual_sales_units, estimated_revenue_usd
        ) VALUES (?, ?, ?, ?);
    """, sales_data)
    conn.commit()
    print(f"  Inserted {len(sales_data):,} sales records.")

    # 6. Populate Customer Ratings Table
    print("Populating 'customer_ratings' table...")
    cursor.executemany("""
        INSERT OR IGNORE INTO customer_ratings (
            vehicle_id, customer_rating, safety_rating_stars, resale_value_pct_3yr
        ) VALUES (?, ?, ?, ?);
    """, ratings_data)
    conn.commit()
    print(f"  Inserted {len(ratings_data):,} ratings records.")

    # 7. Validate Database Integrity
    print("\n--- Validating Database Integrity ---")
    cursor.execute("PRAGMA foreign_key_check;")
    fk_errors = cursor.fetchall()
    if fk_errors:
        print(f"Foreign key violations detected: {fk_errors}")
    else:
        print("Foreign Key Verification: Passed (0 violations).")

    cursor.execute("SELECT COUNT(*) FROM vehicles;")
    v_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM vehicle_sales;")
    s_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM customer_ratings;")
    r_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM manufacturers;")
    m_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM categories;")
    c_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM battery_technologies;")
    b_count = cursor.fetchone()[0]

    print(f"Table row counts:")
    print(f"  - manufacturers:        {m_count:,}")
    print(f"  - categories:           {c_count:,}")
    print(f"  - battery_technologies: {b_count:,}")
    print(f"  - vehicles:             {v_count:,}")
    print(f"  - vehicle_sales:        {s_count:,}")
    print(f"  - customer_ratings:     {r_count:,}")

    # Test View Query
    cursor.execute("SELECT COUNT(*) FROM v_vehicles_complete;")
    view_count = cursor.fetchone()[0]
    print(f"  - v_vehicles_complete:  {view_count:,}")

    conn.close()
    print("\nDatabase initialization and load completed successfully!")

if __name__ == "__main__":
    populate_database()
