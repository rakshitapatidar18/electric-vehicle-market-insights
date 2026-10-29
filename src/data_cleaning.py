"""
Data Cleaning and Validation Pipeline for EV Market Datasets.
Cleans raw train and test files, handles missing values using category/chemistry
aware median imputation, removes duplicates, and outputs clean CSVs.
Preserves original raw data untouched.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

# Project Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
TRAIN_RAW_FILE = RAW_DIR / "ev_market_train.csv"
TEST_RAW_FILE = RAW_DIR / "ev_market_test.csv"

CLEANED_UNIFIED_FILE = PROCESSED_DIR / "electric_vehicles_cleaned.csv"
CLEANED_TRAIN_FILE = PROCESSED_DIR / "ev_market_train_cleaned.csv"
CLEANED_TEST_FILE = PROCESSED_DIR / "ev_market_test_cleaned.csv"


def clean_dataframe(df: pd.DataFrame, dataset_name: str) -> pd.DataFrame:
    """
    Cleans a single EV dataframe:
    - Removes exact duplicate records
    - Verifies data types and string trimming
    - Imputes missing values intelligently based on domain logic:
        * battery_cycle_life: median by battery_type
        * customer_rating: median by category
        * annual_sales_units: median by category
        * resale_value_pct_3yr: median by category
        * infotainment_screen_inch: median by category
    """
    print(f"\n--- Cleaning {dataset_name} ---")
    initial_count = len(df)
    
    # 1. Deduplication
    df_cleaned = df.drop_duplicates(subset=['vehicle_id']).copy()
    duplicates_removed = initial_count - len(df_cleaned)
    print(f"Removed {duplicates_removed} duplicate row(s). Remaining: {len(df_cleaned):,}")

    # 2. String trimming and standardizing
    str_cols = df_cleaned.select_dtypes(include=['object', 'string']).columns
    for col in str_cols:
        df_cleaned[col] = df_cleaned[col].astype(str).str.strip()

    # 3. Domain-aware missing value imputation
    # Battery cycle life depends heavily on battery chemistry (e.g. LFP vs NMC)
    if 'battery_cycle_life' in df_cleaned.columns and df_cleaned['battery_cycle_life'].isnull().any():
        nulls = df_cleaned['battery_cycle_life'].isnull().sum()
        df_cleaned['battery_cycle_life'] = df_cleaned.groupby('battery_type')['battery_cycle_life'].transform(
            lambda x: x.fillna(x.median())
        )
        # Fallback to overall median if any group was entirely NaN
        df_cleaned['battery_cycle_life'] = df_cleaned['battery_cycle_life'].fillna(df_cleaned['battery_cycle_life'].median()).round(1)
        print(f"Imputed {nulls:,} missing battery_cycle_life values by battery_type median.")

    # Category-based imputations
    for col in ['customer_rating', 'annual_sales_units', 'resale_value_pct_3yr', 'infotainment_screen_inch']:
        if col in df_cleaned.columns and df_cleaned[col].isnull().any():
            nulls = df_cleaned[col].isnull().sum()
            df_cleaned[col] = df_cleaned.groupby('category')[col].transform(
                lambda x: x.fillna(x.median())
            )
            df_cleaned[col] = df_cleaned[col].fillna(df_cleaned[col].median())
            if col == 'annual_sales_units':
                df_cleaned[col] = df_cleaned[col].round().astype(int)
            elif col == 'customer_rating':
                df_cleaned[col] = df_cleaned[col].round(2)
            else:
                df_cleaned[col] = df_cleaned[col].round(2)
            print(f"Imputed {nulls:,} missing {col} values by vehicle category median.")

    # 4. Final verification
    remaining_nulls = df_cleaned.isnull().sum().sum()
    print(f"Final null count in {dataset_name}: {remaining_nulls}")
    assert remaining_nulls == 0, f"Unexpected null values remaining in {dataset_name}!"
    
    return df_cleaned


def process_datasets():
    """
    Main execution pipeline:
    - Reads raw files safely
    - Cleans train and test data
    - Adds split_source column ('train' / 'test')
    - Saves clean train, clean test, and unified clean datasets
    """
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    print(f"Loading raw train data from: {TRAIN_RAW_FILE}")
    train_df = pd.read_csv(TRAIN_RAW_FILE)
    train_clean = clean_dataframe(train_df, "Train Set")
    train_clean['split_source'] = 'train'
    
    print(f"\nLoading raw test data from: {TEST_RAW_FILE}")
    test_df = pd.read_csv(TEST_RAW_FILE)
    test_clean = clean_dataframe(test_df, "Test Set")
    test_clean['split_source'] = 'test'
    
    # Check for ID overlap between train and test
    overlap_ids = set(train_clean['vehicle_id']).intersection(set(test_clean['vehicle_id']))
    if overlap_ids:
        print(f"Warning: Found {len(overlap_ids)} overlapping vehicle IDs between train and test!")
    else:
        print("\nVerified: Zero overlapping vehicle IDs between train and test.")
        
    # Combine into unified analytics master dataset
    unified_df = pd.concat([train_clean, test_clean], ignore_index=True)
    print(f"\nUnified Dataset Created: {len(unified_df):,} total vehicle records.")

    # Save outputs
    print(f"Saving cleaned train dataset to: {CLEANED_TRAIN_FILE}")
    train_clean.to_csv(CLEANED_TRAIN_FILE, index=False)
    
    print(f"Saving cleaned test dataset to: {CLEANED_TEST_FILE}")
    test_clean.to_csv(CLEANED_TEST_FILE, index=False)
    
    print(f"Saving unified cleaned dataset to: {CLEANED_UNIFIED_FILE}")
    unified_df.to_csv(CLEANED_UNIFIED_FILE, index=False)
    
    print("\nData cleaning and export completed successfully!")
    return unified_df, train_clean, test_clean


if __name__ == "__main__":
    process_datasets()
