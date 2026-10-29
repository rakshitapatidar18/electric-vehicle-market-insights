"""
Unit tests for data cleaning and validation.
"""

import sys
from pathlib import Path
import pytest
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import config

def test_raw_files_exist():
    """Verify raw CSV files exist and are not empty."""
    train_file = config.RAW_DATA_DIR / "ev_market_train.csv"
    test_file = config.RAW_DATA_DIR / "ev_market_test.csv"
    assert train_file.exists(), "Raw train file missing"
    assert test_file.exists(), "Raw test file missing"
    assert train_file.stat().st_size > 0
    assert test_file.stat().st_size > 0

def test_cleaned_files_exist():
    """Verify cleaned files are generated."""
    assert config.CLEANED_DATA_FILE.exists(), "Unified cleaned CSV missing"
    assert (config.PROCESSED_DATA_DIR / "ev_market_train_cleaned.csv").exists()
    assert (config.PROCESSED_DATA_DIR / "ev_market_test_cleaned.csv").exists()

def test_cleaned_dataset_quality():
    """Verify cleaned unified dataset has no nulls, correct rows, and unique IDs."""
    df = pd.read_csv(config.CLEANED_DATA_FILE)
    
    # Check total rows (199,999 train + 100,000 test)
    assert len(df) == 299999, f"Expected 299,999 rows, found {len(df)}"
    
    # Check no missing values
    assert df.isnull().sum().sum() == 0, "Cleaned dataset contains unexpected null values"
    
    # Check uniqueness of vehicle_id
    assert df['vehicle_id'].nunique() == 299999, "Duplicate vehicle IDs exist in cleaned data"
    
    # Check split source values
    assert set(df['split_source'].unique()) == {'train', 'test'}
    assert (df['split_source'] == 'train').sum() == 199999
    assert (df['split_source'] == 'test').sum() == 100000

def test_numeric_ranges():
    """Verify core metrics fall within realistic domain boundaries."""
    df = pd.read_csv(config.CLEANED_DATA_FILE)
    assert df['model_year'].min() >= 2018
    assert df['model_year'].max() <= 2026
    assert (df['price_usd'] > 0).all()
    assert (df['range_km'] > 0).all()
    assert (df['battery_capacity_kwh'] > 0).all()
    assert (df['annual_sales_units'] >= 0).all()
    assert (df['customer_rating'] >= 1.0).all() and (df['customer_rating'] <= 5.0).all()
