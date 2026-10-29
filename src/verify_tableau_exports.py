"""
Verification script for all Tableau CSV export files in data/processed/.
Checks file existence, sizes, headers, and exact record counts.
"""

import sys
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

TABLEAU_FILES = {
    "Master Tableau Export": PROCESSED_DIR / "ev_tableau_export.csv",
    "Manufacturer KPIs": PROCESSED_DIR / "tableau_manufacturer_kpis.csv",
    "Category KPIs": PROCESSED_DIR / "tableau_category_kpis.csv",
    "Battery KPIs": PROCESSED_DIR / "tableau_battery_kpis.csv",
    "Yearly Trends": PROCESSED_DIR / "tableau_yearly_trends.csv",
    "Country KPIs": PROCESSED_DIR / "tableau_country_kpis.csv",
}

def verify_files():
    print("=" * 80)
    print("VERIFYING TABLEAU EXPORT CSV FILES IN data/processed/")
    print("=" * 80)
    
    report = []
    for label, path in TABLEAU_FILES.items():
        if not path.exists():
            print(f"[MISSING] {label} at {path}")
            report.append((label, str(path), False, 0, 0, []))
            continue
            
        size_mb = path.stat().st_size / (1024 * 1024)
        df = pd.read_csv(path)
        row_count = len(df)
        col_count = len(df.columns)
        headers = df.columns.tolist()
        
        print(f"\n[OK] {label}")
        print(f"   Absolute Path: {path}")
        print(f"   File Size:     {size_mb:.2f} MB ({path.stat().st_size:,} bytes)")
        print(f"   Record Count:  {row_count:,} rows")
        print(f"   Columns ({col_count}): {headers[:8]}...")
        report.append((label, str(path), True, row_count, col_count, headers))
        
    return report

if __name__ == "__main__":
    verify_files()
