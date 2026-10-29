"""
Data inspection and profiling script for EV Market Train and Test datasets.
Examines schemas, column names, missing values, duplicates, data types,
and potential overlaps between train and test sets.
"""

import sys
from pathlib import Path
import json
import pandas as pd
import numpy as np

# Set project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
TRAIN_FILE = RAW_DIR / "ev_market_train.csv"
TEST_FILE = RAW_DIR / "ev_market_test.csv"

def inspect_dataset(file_path: Path, name: str):
    print(f"\n{'='*30} INSPECTING {name} {'='*30}")
    print(f"File: {file_path}")
    print(f"Size: {file_path.stat().st_size / (1024*1024):.2f} MB")
    
    # Read first 5 rows to see structure
    sample_df = pd.read_csv(file_path, nrows=5)
    print("\nColumns:", sample_df.columns.tolist())
    print("\nSample row 0:")
    for col, val in sample_df.iloc[0].items():
        print(f"  {col}: {val} (type: {type(val).__name__})")
        
    # Read full dataset
    df = pd.read_csv(file_path)
    print(f"\nTotal rows: {len(df):,}")
    print(f"Total columns: {len(df.columns)}")
    
    # Check data types and nulls
    profile = []
    for col in df.columns:
        null_count = df[col].isnull().sum()
        null_pct = (null_count / len(df)) * 100
        nunique = df[col].nunique(dropna=False)
        dtype = str(df[col].dtype)
        sample_vals = df[col].dropna().unique()[:3].tolist()
        profile.append({
            "column": col,
            "dtype": dtype,
            "null_count": int(null_count),
            "null_pct": round(float(null_pct), 2),
            "n_unique": int(nunique),
            "sample_values": sample_vals
        })
    
    # Check duplicates
    full_duplicates = df.duplicated().sum()
    print(f"Full duplicate rows: {full_duplicates}")
    
    # Check potential ID columns
    id_cols = [c for c in df.columns if 'id' in c.lower()]
    for id_col in id_cols:
        id_dups = df[id_col].duplicated().sum()
        print(f"Column '{id_col}' unique values: {df[id_col].nunique():,}, duplicates: {id_dups}")
        
    # Numerical summaries
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    print("\nNumerical columns summary:")
    print(df[num_cols].describe().T[['count', 'mean', 'std', 'min', '50%', 'max']])
    
    # Categorical summaries
    cat_cols = df.select_dtypes(include=['object']).columns.tolist()
    print("\nCategorical columns summary:")
    for c in cat_cols:
        val_counts = df[c].value_counts().head(5).to_dict()
        print(f"  {c} (top 5): {val_counts}")
        
    return df, profile

def compare_datasets(train_df, test_df):
    print(f"\n{'='*30} COMPARISON & OVERLAP CHECK {'='*30}")
    print("Train columns == Test columns?", list(train_df.columns) == list(test_df.columns))
    
    id_cols = [c for c in train_df.columns if 'id' in c.lower()]
    for id_col in id_cols:
        train_ids = set(train_df[id_col].dropna())
        test_ids = set(test_df[id_col].dropna())
        overlap = train_ids.intersection(test_ids)
        print(f"ID Column '{id_col}':")
        print(f"  Train unique IDs: {len(train_ids):,}")
        print(f"  Test unique IDs: {len(test_ids):,}")
        print(f"  Overlapping IDs: {len(overlap):,}")
        if overlap:
            sample_overlap = list(overlap)[:5]
            print(f"  Sample overlapping IDs: {sample_overlap}")
            
    # Check if distributions are similar (e.g. model years, categories)
    print("\nModel Year range:")
    if 'Model_Year' in train_df.columns or 'model_year' in train_df.columns:
        my_col = 'Model_Year' if 'Model_Year' in train_df.columns else 'model_year'
        print(f"  Train: {train_df[my_col].min()} to {train_df[my_col].max()}")
        print(f"  Test:  {test_df[my_col].min()} to {test_df[my_col].max()}")

if __name__ == "__main__":
    train_df, train_prof = inspect_dataset(TRAIN_FILE, "TRAIN SET")
    test_df, test_prof = inspect_dataset(TEST_FILE, "TEST SET")
    compare_datasets(train_df, test_df)
