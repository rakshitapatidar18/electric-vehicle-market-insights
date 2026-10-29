"""
Unit and validation tests for the Pandas analytical engine (src/analysis.py).
Tests KPI calculations, aggregation parity with SQLite database, and Tableau exports.
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
from src.analysis import EVMarketAnalytics


@pytest.fixture(scope="module")
def analytics_engine():
    """Provides an instance of the analytical engine."""
    return EVMarketAnalytics()


def test_analytics_initialization(analytics_engine):
    """Verify data loaded properly into memory."""
    assert analytics_engine.df is not None
    assert len(analytics_engine.df) == 299999
    assert 'price_usd' in analytics_engine.df.columns
    assert 'range_km' in analytics_engine.df.columns
    assert 'estimated_revenue_usd' in analytics_engine.df.columns


def test_kpi_parity_with_sqlite(analytics_engine):
    """Verify Pandas KPI calculations exactly match SQLite database query results."""
    pandas_kpis = analytics_engine.get_executive_kpis()

    conn = sqlite3.connect(str(config.DATABASE_PATH))
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            COUNT(vehicle_id) AS total_vehicles,
            ROUND(AVG(range_km), 1) AS avg_range,
            ROUND(AVG(battery_capacity_kwh), 1) AS avg_battery,
            ROUND(AVG(price_usd), 2) AS avg_price,
            SUM(annual_sales_units) AS total_sales
        FROM vehicles;
    """)
    sql_kpis = cursor.fetchone()
    conn.close()

    assert pandas_kpis['total_vehicles'] == sql_kpis[0]
    assert pandas_kpis['avg_driving_range_km'] == sql_kpis[1]
    assert pandas_kpis['avg_battery_capacity_kwh'] == sql_kpis[2]
    assert pandas_kpis['avg_price_usd'] == sql_kpis[3]
    assert pandas_kpis['total_annual_sales_units'] == sql_kpis[4]


def test_manufacturer_performance(analytics_engine):
    """Verify manufacturer rankings and market share sum."""
    df_mfg = analytics_engine.get_manufacturer_performance(top_n=None)
    assert len(df_mfg) == 200
    assert df_mfg['total_sales_units'].sum() == analytics_engine.df['annual_sales_units'].sum()
    # Total market share should sum to ~100%
    assert round(df_mfg['market_share_pct'].sum(), 1) == 100.0


def test_category_comparison(analytics_engine):
    """Verify all 15 vehicle categories are present and counts match."""
    df_cat = analytics_engine.get_category_comparison()
    assert len(df_cat) == 15
    assert df_cat['vehicle_count'].sum() == 299999
    assert (df_cat['avg_range_km'] > 0).all()


def test_battery_analysis(analytics_engine):
    """Verify 5 battery chemistries are compared."""
    df_bat = analytics_engine.get_battery_analysis()
    assert len(df_bat) == 5
    assert set(df_bat['battery_type']) == {'NMC', 'LFP', 'NCA', 'Sodium-Ion', 'Solid-State'}
    assert df_bat['total_models_deployed'].sum() == 299999


def test_tableau_exports_generation(analytics_engine):
    """Verify all Tableau export files exist and are populated."""
    exports = analytics_engine.export_tableau_data()
    for name, path in exports.items():
        assert path.exists(), f"Missing export file for {name}: {path}"
        assert path.stat().st_size > 0, f"Export file is empty: {path}"

    # Verify master export has enriched columns
    master_df = pd.read_csv(exports["master"], nrows=10)
    assert 'price_tier' in master_df.columns
    assert 'range_tier' in master_df.columns
    assert 'cost_per_km_range' in master_df.columns
    assert 'power_to_weight_ratio' in master_df.columns
