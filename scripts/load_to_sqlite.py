"""
load_to_sqlite.py
-----------------
Loads the cleaned CSV into a SQLite database (no server needed) and runs
every query in sql/business_queries.sql, printing the results.

Run:  python scripts/load_to_sqlite.py
Output: data/processed/shopkart.db

Tip: open shopkart.db in DB Browser for SQLite or DBeaver to run the
queries yourself. The same SQL works in MySQL/PostgreSQL with minor
changes (strftime -> DATE_FORMAT / TO_CHAR).
"""

import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / "data" / "processed" / "shopkart_sales_clean.csv"
DB = ROOT / "data" / "processed" / "shopkart.db"
SQL = ROOT / "sql" / "business_queries.sql"

pd.set_option("display.width", 160)
pd.set_option("display.max_columns", 20)

df = pd.read_csv(CSV)
con = sqlite3.connect(DB)
df.to_sql("orders", con, if_exists="replace", index=False)
print(f"Loaded {len(df):,} rows into table 'orders' ({DB.name})\n")

# split the file on the '-- Q' markers so each query is printed with its title
blocks = SQL.read_text(encoding="utf-8").split("-- Q")[1:]
for block in blocks:
    title = "Q" + block.splitlines()[0].strip()
    query = "\n".join(l for l in block.splitlines()[1:] if not l.strip().startswith("--"))
    print("=" * 90)
    print(title)
    print("-" * 90)
    print(pd.read_sql_query(query, con).to_string(index=False))
    print()
con.close()
