"""
Runner and validator for analytical SQL queries in database/sql_queries.sql.
Executes each query, verifies execution, and prints sample outputs.
"""

import sys
import sqlite3
from pathlib import Path
import time
import re
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import config

def execute_analytical_queries():
    conn = sqlite3.connect(str(config.DATABASE_PATH))
    conn.row_factory = sqlite3.Row
    
    with open(config.SQL_QUERIES_PATH, "r", encoding="utf-8") as f:
        sql_content = f.read()

    # Split on semicolon to separate queries
    raw_statements = sql_content.split(";")
    
    queries = []
    for stmt in raw_statements:
        clean_stmt = stmt.strip()
        if not clean_stmt:
            continue
            
        # Extract title from comments if available
        title_match = re.search(r'-- QUERY \d+:[^\n]+', clean_stmt)
        if title_match:
            title = title_match.group(0).replace('-- ', '')
        else:
            title = "Analytical Query"
            
        # Strip all leading comment lines to get clean executable SQL
        lines = clean_stmt.splitlines()
        sql_lines = [l for l in lines if not l.strip().startswith("--")]
        exec_sql = "\n".join(sql_lines).strip()
        
        if exec_sql:
            queries.append((title, exec_sql))

    print(f"\nExtracted {len(queries)} executable analytical queries.\n")
    
    results = {}
    for i, (title, sql_text) in enumerate(queries, 1):
        t0 = time.time()
        cursor = conn.cursor()
        cursor.execute(sql_text)
        rows = cursor.fetchall()
        elapsed = time.time() - t0
        
        if cursor.description:
            cols = [col[0] for col in cursor.description]
            df_res = pd.DataFrame([dict(r) for r in rows], columns=cols)
        else:
            df_res = pd.DataFrame()
            
        results[title] = df_res
        
        print(f"[{i}/{len(queries)}] {title} (Runtime: {elapsed*1000:.1f}ms, Rows: {len(df_res)})")
        print(df_res.head(3).to_string(index=False))
        print("-" * 80)

    conn.close()
    return results

if __name__ == "__main__":
    execute_analytical_queries()
