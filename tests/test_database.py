"""
Automated unit and integration tests for SQLite Database and SQL queries.
Tests schema, constraints, data integrity, and analytical query execution.
"""

import sys
import sqlite3
from pathlib import Path
import pytest
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import config

@pytest.fixture(scope="module")
def db_conn():
    """Provides a managed database connection for testing."""
    assert config.DATABASE_PATH.exists(), f"Database file not found: {config.DATABASE_PATH}"
    conn = sqlite3.connect(str(config.DATABASE_PATH))
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()

def test_database_tables_exist(db_conn):
    """Verify all tables and views exist in sqlite_master."""
    cursor = db_conn.cursor()
    cursor.execute("SELECT name, type FROM sqlite_master WHERE type IN ('table', 'view');")
    entities = {row['name']: row['type'] for row in cursor.fetchall()}
    
    expected_tables = ['manufacturers', 'categories', 'battery_technologies', 'vehicles', 'vehicle_sales', 'customer_ratings']
    for table in expected_tables:
        assert table in entities, f"Missing table: {table}"
        assert entities[table] == 'table'
        
    assert 'v_vehicles_complete' in entities, "Missing view: v_vehicles_complete"
    assert entities['v_vehicles_complete'] == 'view'

def test_database_record_counts(db_conn):
    """Verify expected row counts in all normalized tables."""
    cursor = db_conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM manufacturers;")
    assert cursor.fetchone()[0] == 200, "Manufacturers count mismatch"

    cursor.execute("SELECT COUNT(*) FROM categories;")
    assert cursor.fetchone()[0] == 15, "Categories count mismatch"

    cursor.execute("SELECT COUNT(*) FROM battery_technologies;")
    assert cursor.fetchone()[0] == 5, "Battery technologies count mismatch"

    cursor.execute("SELECT COUNT(*) FROM vehicles;")
    assert cursor.fetchone()[0] == 299999, "Vehicles count mismatch"

    cursor.execute("SELECT COUNT(*) FROM vehicle_sales;")
    assert cursor.fetchone()[0] == 299999, "Vehicle sales count mismatch"

    cursor.execute("SELECT COUNT(*) FROM customer_ratings;")
    assert cursor.fetchone()[0] == 299999, "Customer ratings count mismatch"

    cursor.execute("SELECT COUNT(*) FROM v_vehicles_complete;")
    assert cursor.fetchone()[0] == 299999, "View record count mismatch"

def test_foreign_key_integrity(db_conn):
    """Verify that foreign key constraints are 100% satisfied."""
    cursor = db_conn.cursor()
    cursor.execute("PRAGMA foreign_key_check;")
    violations = cursor.fetchall()
    assert len(violations) == 0, f"Foreign key check failed: {violations}"

def test_primary_key_duplicate_rejection(db_conn):
    """Verify that inserting duplicate vehicle_id raises IntegrityError."""
    cursor = db_conn.cursor()
    cursor.execute("SELECT * FROM vehicles LIMIT 1;")
    sample_row = dict(cursor.fetchone())
    
    cols = list(sample_row.keys())
    placeholders = ", ".join(["?"] * len(cols))
    sql = f"INSERT INTO vehicles ({', '.join(cols)}) VALUES ({placeholders});"
    
    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute(sql, list(sample_row.values()))

def test_check_constraint_enforcement(db_conn):
    """Verify that invalid values (e.g. negative price) trigger CHECK constraint failure."""
    cursor = db_conn.cursor()
    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute("""
            INSERT INTO vehicles (
                vehicle_id, model_name, manufacturer_id, category_id, battery_type_id,
                model_year, manufacturing_country, market_region, battery_capacity_kwh,
                range_km, price_usd, annual_sales_units, estimated_revenue_usd,
                customer_rating, safety_rating_stars, split_source
            ) VALUES (
                'INVALID_TEST_999', 'TestModel', 1, 1, 1,
                2024, 'USA', 'North America', 50.0,
                300.0, -9999.0, 100, 0, 4.0, 5, 'train'
            );
        """)

def test_analytical_queries_execution(db_conn):
    """Verify analytical queries in sql_queries.sql run successfully and return non-empty datasets."""
    with open(config.SQL_QUERIES_PATH, "r", encoding="utf-8") as f:
        statements = f.read().split(";")

    cursor = db_conn.cursor()
    executed = 0
    for stmt in statements:
        lines = [l for l in stmt.strip().splitlines() if not l.strip().startswith("--")]
        sql = "\n".join(lines).strip()
        if not sql:
            continue
        cursor.execute(sql)
        rows = cursor.fetchall()
        assert len(rows) > 0, f"Query returned empty result: {sql[:60]}..."
        executed += 1

    assert executed == 10, f"Expected 10 analytical queries, executed {executed}"
