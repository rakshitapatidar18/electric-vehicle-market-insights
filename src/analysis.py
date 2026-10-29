"""
EV Market Performance & Insights - Analytical Engine.
Provides modular, reusable Pandas analytics routines for vehicle specifications,
manufacturers, categories, battery chemistries, pricing, and sales performance.
Generates Tableau-ready CSV exports.
"""

import sys
import sqlite3
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd
import numpy as np

# Project root setup
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import config


class EVMarketAnalytics:
    """Reusable analytical engine for the EV Market Performance project."""

    def __init__(self, data_source: Optional[str] = None):
        """
        Initializes the analytical engine.
        Defaults to loading the master cleaned CSV or SQLite database view.
        """
        self.data_path = Path(data_source) if data_source else config.CLEANED_DATA_FILE
        self.db_path = config.DATABASE_PATH
        self.df: Optional[pd.DataFrame] = None
        self.load_data()

    def load_data(self) -> pd.DataFrame:
        """Loads data into memory. Prefers clean CSV; falls back to SQLite view."""
        if self.data_path.exists():
            print(f"EVMarketAnalytics: Loading dataset from CSV: {self.data_path}")
            self.df = pd.read_csv(self.data_path)
        elif self.db_path.exists():
            print(f"EVMarketAnalytics: Loading dataset from SQLite database: {self.db_path}")
            conn = sqlite3.connect(str(self.db_path))
            self.df = pd.read_sql_query("SELECT * FROM v_vehicles_complete;", conn)
            conn.close()
        else:
            raise FileNotFoundError(f"Neither cleaned CSV ({self.data_path}) nor SQLite DB ({self.db_path}) found!")

        # Ensure numeric columns are properly typed
        float_cols = ['battery_capacity_kwh', 'range_km', 'price_usd', 'customer_rating', 
                      'top_speed_kmph', 'acceleration_0_100_sec', 'charging_dc_fast_time_min',
                      'efficiency_wh_per_km', 'battery_cycle_life', 'battery_degradation_pct_5yr',
                      'resale_value_pct_3yr', 'co2_saved_tons_per_year']
        for col in float_cols:
            if col in self.df.columns:
                self.df[col] = pd.to_numeric(self.df[col], errors='coerce')

        if 'annual_sales_units' in self.df.columns:
            self.df['annual_sales_units'] = pd.to_numeric(self.df['annual_sales_units'], errors='coerce').fillna(0).astype(int)

        if 'estimated_revenue_usd' not in self.df.columns:
            self.df['estimated_revenue_usd'] = (self.df['annual_sales_units'] * self.df['price_usd']).round(2)

        print(f"EVMarketAnalytics: Ready with {len(self.df):,} records and {len(self.df.columns)} columns.")
        return self.df

    # --------------------------------------------------------------------------
    # 1. Executive KPIs
    # --------------------------------------------------------------------------
    def get_executive_kpis(self) -> Dict[str, Any]:
        """Calculates executive KPI metrics matching Query 1."""
        df = self.df
        total_revenue = float(df['estimated_revenue_usd'].sum())
        kpis = {
            "total_vehicles": int(len(df)),
            "total_manufacturers": int(df['manufacturer'].nunique()),
            "total_categories": int(df['category'].nunique()),
            "total_manufacturing_countries": int(df['manufacturing_country'].nunique()),
            "avg_driving_range_km": round(float(df['range_km'].mean()), 1),
            "max_driving_range_km": round(float(df['range_km'].max()), 1),
            "min_driving_range_km": round(float(df['range_km'].min()), 1),
            "avg_battery_capacity_kwh": round(float(df['battery_capacity_kwh'].mean()), 1),
            "avg_price_usd": round(float(df['price_usd'].mean()), 2),
            "min_price_usd": round(float(df['price_usd'].min()), 2),
            "max_price_usd": round(float(df['price_usd'].max()), 2),
            "total_annual_sales_units": int(df['annual_sales_units'].sum()),
            "total_revenue_billion_usd": round(total_revenue / 1e9, 2),
            "avg_customer_rating": round(float(df['customer_rating'].mean()), 2),
            "avg_efficiency_wh_per_km": round(float(df['efficiency_wh_per_km'].mean()), 1),
        }
        return kpis

    # --------------------------------------------------------------------------
    # 2. Manufacturer Performance & Market Share
    # --------------------------------------------------------------------------
    def get_manufacturer_performance(self, top_n: int = 10) -> pd.DataFrame:
        """Calculates manufacturer metrics, volume, revenue, and market share."""
        df = self.df
        total_global_sales = df['annual_sales_units'].sum()
        
        mfg_grp = df.groupby('manufacturer').agg(
            total_models_offered=('vehicle_id', 'count'),
            total_sales_units=('annual_sales_units', 'sum'),
            total_revenue_usd=('estimated_revenue_usd', 'sum'),
            avg_vehicle_price=('price_usd', 'mean'),
            avg_range_km=('range_km', 'mean'),
            avg_rating=('customer_rating', 'mean')
        ).reset_index()

        mfg_grp['revenue_million_usd'] = (mfg_grp['total_revenue_usd'] / 1e6).round(2)
        mfg_grp['market_share_pct'] = ((mfg_grp['total_sales_units'] / total_global_sales) * 100).round(2)
        mfg_grp['avg_vehicle_price'] = mfg_grp['avg_vehicle_price'].round(2)
        mfg_grp['avg_range_km'] = mfg_grp['avg_range_km'].round(1)
        mfg_grp['avg_rating'] = mfg_grp['avg_rating'].round(2)

        mfg_grp = mfg_grp.sort_values(by='total_sales_units', ascending=False)
        if top_n:
            return mfg_grp.head(top_n).copy()
        return mfg_grp

    # --------------------------------------------------------------------------
    # 3. Vehicle Category Comparison
    # --------------------------------------------------------------------------
    def get_category_comparison(self) -> pd.DataFrame:
        """Analyzes price, range, battery capacity, efficiency, and sales across categories."""
        df = self.df
        cat_grp = df.groupby('category').agg(
            vehicle_count=('vehicle_id', 'count'),
            avg_price_usd=('price_usd', 'mean'),
            min_price_usd=('price_usd', 'min'),
            max_price_usd=('price_usd', 'max'),
            avg_range_km=('range_km', 'mean'),
            avg_battery_kwh=('battery_capacity_kwh', 'mean'),
            avg_efficiency_wh_km=('efficiency_wh_per_km', 'mean'),
            avg_0_100_sec=('acceleration_0_100_sec', 'mean'),
            total_sales_units=('annual_sales_units', 'sum'),
            avg_customer_rating=('customer_rating', 'mean')
        ).reset_index()

        cat_grp['avg_price_usd'] = cat_grp['avg_price_usd'].round(2)
        cat_grp['min_price_usd'] = cat_grp['min_price_usd'].round(2)
        cat_grp['max_price_usd'] = cat_grp['max_price_usd'].round(2)
        cat_grp['avg_range_km'] = cat_grp['avg_range_km'].round(1)
        cat_grp['avg_battery_kwh'] = cat_grp['avg_battery_kwh'].round(1)
        cat_grp['avg_efficiency_wh_km'] = cat_grp['avg_efficiency_wh_km'].round(1)
        cat_grp['avg_0_100_sec'] = cat_grp['avg_0_100_sec'].round(2)
        cat_grp['avg_customer_rating'] = cat_grp['avg_customer_rating'].round(2)

        return cat_grp.sort_values(by='total_sales_units', ascending=False)

    # --------------------------------------------------------------------------
    # 4. Battery Technology Analysis
    # --------------------------------------------------------------------------
    def get_battery_analysis(self) -> pd.DataFrame:
        """Compares battery chemistries on capacity, degradation, cycle life, and cost."""
        df = self.df.copy()
        df['cost_per_km_range'] = df['price_usd'] / df['range_km']

        bat_grp = df.groupby('battery_type').agg(
            total_models_deployed=('vehicle_id', 'count'),
            avg_capacity_kwh=('battery_capacity_kwh', 'mean'),
            avg_range_km=('range_km', 'mean'),
            avg_cycle_life_cycles=('battery_cycle_life', 'mean'),
            avg_5yr_degradation_pct=('battery_degradation_pct_5yr', 'mean'),
            avg_fast_charge_min=('charging_dc_fast_time_min', 'mean'),
            avg_cost_per_km_range=('cost_per_km_range', 'mean'),
            total_sales_units=('annual_sales_units', 'sum')
        ).reset_index()

        bat_grp['avg_capacity_kwh'] = bat_grp['avg_capacity_kwh'].round(1)
        bat_grp['avg_range_km'] = bat_grp['avg_range_km'].round(1)
        bat_grp['avg_cycle_life_cycles'] = bat_grp['avg_cycle_life_cycles'].round(0)
        bat_grp['avg_5yr_degradation_pct'] = bat_grp['avg_5yr_degradation_pct'].round(2)
        bat_grp['avg_fast_charge_min'] = bat_grp['avg_fast_charge_min'].round(1)
        bat_grp['avg_cost_per_km_range'] = bat_grp['avg_cost_per_km_range'].round(2)

        return bat_grp.sort_values(by='total_models_deployed', ascending=False)

    # --------------------------------------------------------------------------
    # 5. Annual Sales Trends (2018 - 2026)
    # --------------------------------------------------------------------------
    def get_annual_sales_trends(self) -> pd.DataFrame:
        """Analyzes market evolution and technological progress over model years."""
        df = self.df
        year_grp = df.groupby('model_year').agg(
            models_introduced=('vehicle_id', 'count'),
            total_units_sold=('annual_sales_units', 'sum'),
            total_revenue_usd=('estimated_revenue_usd', 'sum'),
            avg_price_usd=('price_usd', 'mean'),
            avg_range_km=('range_km', 'mean'),
            avg_battery_kwh=('battery_capacity_kwh', 'mean'),
            avg_fast_charge_time_min=('charging_dc_fast_time_min', 'mean'),
            avg_customer_rating=('customer_rating', 'mean')
        ).reset_index()

        year_grp['revenue_billion_usd'] = (year_grp['total_revenue_usd'] / 1e9).round(2)
        year_grp['avg_price_usd'] = year_grp['avg_price_usd'].round(2)
        year_grp['avg_range_km'] = year_grp['avg_range_km'].round(1)
        year_grp['avg_battery_kwh'] = year_grp['avg_battery_kwh'].round(1)
        year_grp['avg_fast_charge_time_min'] = year_grp['avg_fast_charge_time_min'].round(1)
        year_grp['avg_customer_rating'] = year_grp['avg_customer_rating'].round(2)

        return year_grp.sort_values(by='model_year', ascending=True)

    # --------------------------------------------------------------------------
    # 6. Country & Regional Geographical Distribution
    # --------------------------------------------------------------------------
    def get_country_manufacturing(self) -> pd.DataFrame:
        """Analyzes manufacturing country hubs."""
        df = self.df
        country_grp = df.groupby('manufacturing_country').agg(
            active_manufacturers=('manufacturer', 'nunique'),
            vehicle_count=('vehicle_id', 'count'),
            total_sales_produced=('annual_sales_units', 'sum'),
            avg_price_usd=('price_usd', 'mean'),
            avg_range_km=('range_km', 'mean'),
            avg_customer_satisfaction=('customer_rating', 'mean')
        ).reset_index()

        country_grp['avg_price_usd'] = country_grp['avg_price_usd'].round(2)
        country_grp['avg_range_km'] = country_grp['avg_range_km'].round(1)
        country_grp['avg_customer_satisfaction'] = country_grp['avg_customer_satisfaction'].round(2)

        return country_grp.sort_values(by='total_sales_produced', ascending=False)

    def get_regional_market_demand(self) -> pd.DataFrame:
        """Analyzes target market region sales and demand."""
        df = self.df
        reg_grp = df.groupby('market_region').agg(
            models_available=('vehicle_id', 'count'),
            total_regional_sales=('annual_sales_units', 'sum'),
            avg_regional_price=('price_usd', 'mean'),
            avg_satisfaction_rating=('customer_rating', 'mean')
        ).reset_index()

        reg_grp['avg_regional_price'] = reg_grp['avg_regional_price'].round(2)
        reg_grp['avg_satisfaction_rating'] = reg_grp['avg_satisfaction_rating'].round(2)

        return reg_grp.sort_values(by='total_regional_sales', ascending=False)

    # --------------------------------------------------------------------------
    # 7. Price Segments & Value Metrics
    # --------------------------------------------------------------------------
    def get_price_segment_analysis(self) -> pd.DataFrame:
        """Segments vehicles into market tiers and evaluates segment performance."""
        df = self.df.copy()
        bins = [0, 25000, 60000, 100000, float('inf')]
        labels = ['Budget (<$25K)', 'Mid-Range ($25K-$60K)', 'Premium ($60K-$100K)', 'Luxury (>$100K)']
        df['price_segment'] = pd.cut(df['price_usd'], bins=bins, labels=labels, right=False)

        seg_grp = df.groupby('price_segment', observed=False).agg(
            vehicle_count=('vehicle_id', 'count'),
            total_sales_units=('annual_sales_units', 'sum'),
            avg_price_usd=('price_usd', 'mean'),
            avg_range_km=('range_km', 'mean'),
            avg_battery_kwh=('battery_capacity_kwh', 'mean'),
            avg_customer_rating=('customer_rating', 'mean')
        ).reset_index()

        seg_grp['avg_price_usd'] = seg_grp['avg_price_usd'].round(2)
        seg_grp['avg_range_km'] = seg_grp['avg_range_km'].round(1)
        seg_grp['avg_battery_kwh'] = seg_grp['avg_battery_kwh'].round(1)
        seg_grp['avg_customer_rating'] = seg_grp['avg_customer_rating'].round(2)
        return seg_grp

    # --------------------------------------------------------------------------
    # 8. Tableau Export Pipeline
    # --------------------------------------------------------------------------
    def export_tableau_data(self) -> Dict[str, Path]:
        """
        Creates fully prepared Tableau-ready CSV files in data/processed/:
        1. ev_tableau_export.csv (flat master dataset with enriched calculated fields)
        2. tableau_manufacturer_kpis.csv
        3. tableau_category_kpis.csv
        4. tableau_battery_kpis.csv
        5. tableau_yearly_trends.csv
        6. tableau_country_kpis.csv
        """
        config.PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
        df_export = self.df.copy()

        # Enriched calculated fields for Tableau BI
        price_bins = [0, 25000, 60000, 100000, float('inf')]
        price_labels = ['Budget (<$25K)', 'Mid-Range ($25K-$60K)', 'Premium ($60K-$100K)', 'Luxury (>$100K)']
        df_export['price_tier'] = pd.cut(df_export['price_usd'], bins=price_bins, labels=price_labels, right=False)

        range_bins = [0, 200, 400, 550, float('inf')]
        range_labels = ['Short Range (<200 km)', 'Standard Range (200-400 km)', 'Long Range (400-550 km)', 'Ultra-Long Range (>550 km)']
        df_export['range_tier'] = pd.cut(df_export['range_km'], bins=range_bins, labels=range_labels, right=False)

        df_export['cost_per_km_range'] = (df_export['price_usd'] / df_export['range_km']).round(2)
        df_export['power_to_weight_ratio'] = (df_export['motor_power_kw'] / df_export['weight_kg']).round(4)
        df_export['fast_charge_rate_km_per_min'] = (df_export['range_km'] / df_export['charging_dc_fast_time_min']).round(2)

        # Primary flat Tableau export
        master_path = config.TABLEAU_EXPORT_FILE
        df_export.to_csv(master_path, index=False)
        print(f"Tableau Export: Saved master file ({len(df_export):,} rows) to: {master_path}")

        # Summary tables for Tableau
        exports = {
            "master": master_path,
            "manufacturers": config.PROCESSED_DATA_DIR / "tableau_manufacturer_kpis.csv",
            "categories": config.PROCESSED_DATA_DIR / "tableau_category_kpis.csv",
            "batteries": config.PROCESSED_DATA_DIR / "tableau_battery_kpis.csv",
            "annual_trends": config.PROCESSED_DATA_DIR / "tableau_yearly_trends.csv",
            "countries": config.PROCESSED_DATA_DIR / "tableau_country_kpis.csv"
        }

        self.get_manufacturer_performance(top_n=50).to_csv(exports["manufacturers"], index=False)
        self.get_category_comparison().to_csv(exports["categories"], index=False)
        self.get_battery_analysis().to_csv(exports["batteries"], index=False)
        self.get_annual_sales_trends().to_csv(exports["annual_trends"], index=False)
        self.get_country_manufacturing().to_csv(exports["countries"], index=False)

        print("Tableau Export: Generated all Tableau aggregated KPI files.")
        return exports


def run_analysis_pipeline():
    """Main CLI entrypoint for running the analysis pipeline."""
    print("=" * 70)
    print("ELECTRIC VEHICLE MARKET PERFORMANCE & INSIGHTS: ANALYTICAL ENGINE")
    print("=" * 70)
    
    analytics = EVMarketAnalytics()
    kpis = analytics.get_executive_kpis()
    
    print("\n--- EXECUTIVE KPIS ---")
    for k, v in kpis.items():
        print(f"  {k:32}: {v}")

    print("\n--- TOP 5 MANUFACTURERS ---")
    print(analytics.get_manufacturer_performance(top_n=5).to_string(index=False))

    print("\n--- TOP VEHICLE CATEGORIES ---")
    print(analytics.get_category_comparison().head(5).to_string(index=False))

    print("\n--- BATTERY CHEMISTRY COMPARISON ---")
    print(analytics.get_battery_analysis().to_string(index=False))

    print("\n--- ANNUAL FLEET EVOLUTION ---")
    print(analytics.get_annual_sales_trends().to_string(index=False))

    print("\n--- GENERATING TABLEAU EXPORTS ---")
    exports = analytics.export_tableau_data()
    for name, path in exports.items():
        print(f"  [{name}] -> {path}")

    return analytics

if __name__ == "__main__":
    run_analysis_pipeline()
