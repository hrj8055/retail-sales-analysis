"""
clean_data.py
-------------
Cleans the raw ShopKart sales file and adds the calculated columns
needed for analysis.

Run:  python scripts/clean_data.py
Input:  data/raw/shopkart_sales_raw.csv
Output: data/processed/shopkart_sales_clean.csv
        data/processed/cleaning_log.txt
"""

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "shopkart_sales_raw.csv"
OUT = ROOT / "data" / "processed" / "shopkart_sales_clean.csv"
LOG = ROOT / "data" / "processed" / "cleaning_log.txt"

log = []


def note(msg):
    print(msg)
    log.append(msg)


df = pd.read_csv(RAW, dtype=str)
note(f"Raw rows: {len(df):,}")

# 1. Remove exact duplicate rows ----------------------------------------
before = len(df)
df = df.drop_duplicates()
note(f"[1] Removed {before - len(df):,} exact duplicate rows")

# 2. Standardise dates (3 formats in source) ----------------------------
d1 = pd.to_datetime(df["order_date"], format="%Y-%m-%d", errors="coerce")
d2 = pd.to_datetime(df["order_date"], format="%d/%m/%Y", errors="coerce")
d3 = pd.to_datetime(df["order_date"], format="%d-%b-%Y", errors="coerce")
df["order_date"] = d1.fillna(d2).fillna(d3)
note(f"[2] Parsed dates; unparseable left: {df['order_date'].isna().sum()}")

# 3. Clean text columns -------------------------------------------------
df["city"] = df["city"].str.strip().str.title().replace({"Bengaluru": "Bangalore"})
pay_map = {"upi": "UPI", "cod": "Cash on Delivery", "cash on delivery": "Cash on Delivery",
           "cc": "Credit Card", "credit card": "Credit Card", "debit card": "Debit Card",
           "net banking": "Net Banking", "wallet": "Wallet"}
df["payment_method"] = df["payment_method"].str.strip().str.lower().map(pay_map)
note(f"[3] Standardised city names -> {df['city'].nunique()} cities; "
     f"payment methods -> {sorted(df['payment_method'].unique())}")

# 4. Fix numeric columns ------------------------------------------------
df["unit_price"] = df["unit_price"].str.replace("₹", "", regex=False).str.replace(",", "", regex=False)
num_cols = ["unit_price", "unit_cost", "discount_pct", "quantity",
            "customer_age", "delivery_days", "customer_rating"]
df[num_cols] = df[num_cols].apply(pd.to_numeric, errors="coerce")
note("[4] Removed currency symbols/commas and converted numeric columns")

# 5. Fill missing region from state (region is fully determined by state)
state_region = df.dropna(subset=["region"]).groupby("state")["region"].agg(lambda s: s.mode()[0])
missing_region = df["region"].isna().sum()
df["region"] = df["region"].fillna(df["state"].map(state_region))
note(f"[5] Filled {missing_region} missing regions using state -> region lookup")

# 6. Invalid values -----------------------------------------------------
bad_qty = (df["quantity"] <= 0).sum()
df = df[df["quantity"] > 0]
note(f"[6a] Dropped {bad_qty} rows with quantity <= 0 (data-entry errors)")

bad_age = (~df["customer_age"].between(18, 80) & df["customer_age"].notna()).sum()
df.loc[~df["customer_age"].between(18, 80), "customer_age"] = np.nan
# a customer's age should be the same on every order, so recover it from their other orders
df["customer_age"] = df["customer_age"].fillna(
    df.groupby("customer_id")["customer_age"].transform("median"))
df["gender"] = df["gender"].fillna(
    df.groupby("customer_id")["gender"].transform(lambda s: s.mode()[0] if s.notna().any() else np.nan))
df["gender"] = df["gender"].fillna("Unknown")
note(f"[6b] Set {bad_age} impossible ages to null, then filled age/gender from the "
     f"same customer's other orders; ages still missing: {df['customer_age'].isna().sum()}")

# 7. Feature engineering ------------------------------------------------
df["gross_sales"] = df["unit_price"] * df["quantity"]
df["discount_amount"] = (df["gross_sales"] * df["discount_pct"]).round(2)
df["net_sales"] = df["gross_sales"] - df["discount_amount"]
df["total_cost"] = df["unit_cost"] * df["quantity"]
df["profit"] = df["net_sales"] - df["total_cost"]
# cancelled/returned orders do not generate revenue
realised = df["order_status"] == "Delivered"
df["revenue"] = np.where(realised, df["net_sales"], 0)
df["realised_profit"] = np.where(realised, df["profit"], 0)

df["year"] = df["order_date"].dt.year
df["month"] = df["order_date"].dt.month
df["year_month"] = df["order_date"].dt.to_period("M").astype(str)
df["day_of_week"] = df["order_date"].dt.day_name()
df["age_group"] = pd.cut(df["customer_age"], [17, 24, 34, 44, 54, 80],
                         labels=["18-24", "25-34", "35-44", "45-54", "55+"]
                         ).cat.add_categories("Unknown").fillna("Unknown").astype(str)
df["discount_band"] = pd.cut(df["discount_pct"], [-0.01, 0, 0.10, 0.20, 0.30, 1],
                             labels=["No discount", "1-10%", "11-20%", "21-30%", ">30%"]).astype(str)
note("[7] Added gross_sales, discount_amount, net_sales, total_cost, profit, revenue, "
     "realised_profit, date parts, age_group, discount_band")

df = df.sort_values("order_date").reset_index(drop=True)
df["order_date"] = df["order_date"].dt.strftime("%Y-%m-%d")
OUT.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(OUT, index=False)
note(f"Clean rows: {len(df):,}  ->  {OUT.relative_to(ROOT)}")
LOG.write_text("\n".join(log), encoding="utf-8")
