"""
generate_data.py
----------------
Generates a realistic (synthetic) raw sales dataset for an Indian online
retailer, "ShopKart", covering Jan 2024 - Dec 2025.

The raw file deliberately contains real-world data-quality problems
(duplicates, mixed date formats, inconsistent text, currency symbols in
numbers, missing values, impossible values) so that the cleaning step
is a genuine part of the project.

Run:  python scripts/generate_data.py
Output: data/raw/shopkart_sales_raw.csv
"""

import random
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
rng = np.random.default_rng(SEED)
random.seed(SEED)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "raw" / "shopkart_sales_raw.csv"

# ---------------------------------------------------------------- products
# (product_name, category, sub_category, list_price, cost_ratio)
PRODUCTS = [
    ("Redmi Note 13", "Electronics", "Mobiles", 17999, 0.88),
    ("Samsung Galaxy M34", "Electronics", "Mobiles", 15999, 0.87),
    ("iPhone 15", "Electronics", "Mobiles", 69900, 0.90),
    ("HP Pavilion 15", "Electronics", "Laptops", 62999, 0.89),
    ("Lenovo IdeaPad Slim 3", "Electronics", "Laptops", 45990, 0.88),
    ("boAt Rockerz 450", "Electronics", "Audio", 1499, 0.70),
    ("Sony WH-1000XM5", "Electronics", "Audio", 29990, 0.85),
    ("Noise ColorFit Pro", "Electronics", "Wearables", 2999, 0.72),
    ("Men's Cotton T-Shirt", "Fashion", "Topwear", 599, 0.45),
    ("Women's Kurta Set", "Fashion", "Ethnic Wear", 1499, 0.50),
    ("Silk Saree", "Fashion", "Ethnic Wear", 3999, 0.55),
    ("Slim Fit Jeans", "Fashion", "Bottomwear", 1299, 0.48),
    ("Running Shoes", "Fashion", "Footwear", 2499, 0.52),
    ("Casual Sneakers", "Fashion", "Footwear", 1899, 0.50),
    ("Non-Stick Cookware Set", "Home & Kitchen", "Cookware", 2499, 0.65),
    ("Mixer Grinder 750W", "Home & Kitchen", "Appliances", 3499, 0.72),
    ("Cotton Bedsheet Set", "Home & Kitchen", "Furnishing", 999, 0.55),
    ("LED Table Lamp", "Home & Kitchen", "Decor", 799, 0.58),
    ("Air Fryer 4L", "Home & Kitchen", "Appliances", 5999, 0.74),
    ("Ergonomic Office Chair", "Furniture", "Chairs", 8999, 0.70),
    ("Study Table", "Furniture", "Tables", 5499, 0.68),
    ("Wooden Bookshelf", "Furniture", "Storage", 6999, 0.66),
    ("3-Seater Sofa", "Furniture", "Living Room", 24999, 0.72),
    ("Vitamin C Face Serum", "Beauty", "Skincare", 599, 0.40),
    ("Sunscreen SPF 50", "Beauty", "Skincare", 449, 0.42),
    ("Eau de Parfum 100ml", "Beauty", "Fragrance", 1999, 0.45),
    ("Onion Hair Oil", "Beauty", "Haircare", 349, 0.38),
    ("Yoga Mat", "Sports", "Fitness", 799, 0.55),
    ("Adjustable Dumbbells", "Sports", "Fitness", 3999, 0.65),
    ("English Willow Cricket Bat", "Sports", "Cricket", 4499, 0.62),
    ("Badminton Racket Pair", "Sports", "Racket Sports", 1299, 0.58),
]
CAT_WEIGHT = {"Electronics": 0.22, "Fashion": 0.30, "Home & Kitchen": 0.17,
              "Furniture": 0.07, "Beauty": 0.14, "Sports": 0.10}
RETURN_RATE = {"Electronics": 0.05, "Fashion": 0.13, "Home & Kitchen": 0.05,
               "Furniture": 0.10, "Beauty": 0.03, "Sports": 0.04}

prod_df = pd.DataFrame(PRODUCTS, columns=["product_name", "category", "sub_category",
                                          "list_price", "cost_ratio"])
prod_df["product_id"] = [f"P{1001 + i}" for i in range(len(prod_df))]
# probability of each product = category weight split across its products,
# cheaper products sell more often within a category
prod_df["w"] = prod_df.apply(lambda r: CAT_WEIGHT[r.category] / (r.list_price ** 0.35), axis=1)
prod_df["w"] = prod_df.groupby("category")["w"].transform(lambda s: s / s.sum())
prod_df["w"] = prod_df["w"] * prod_df["category"].map(CAT_WEIGHT)
prod_df["w"] /= prod_df["w"].sum()

# ---------------------------------------------------------------- geography
CITIES = [  # city, state, region, weight
    ("Mumbai", "Maharashtra", "West", 0.14), ("Pune", "Maharashtra", "West", 0.06),
    ("Ahmedabad", "Gujarat", "West", 0.05), ("Delhi", "Delhi", "North", 0.15),
    ("Jaipur", "Rajasthan", "North", 0.04), ("Lucknow", "Uttar Pradesh", "North", 0.05),
    ("Chandigarh", "Chandigarh", "North", 0.03), ("Bangalore", "Karnataka", "South", 0.13),
    ("Chennai", "Tamil Nadu", "South", 0.08), ("Hyderabad", "Telangana", "South", 0.09),
    ("Kochi", "Kerala", "South", 0.03), ("Kolkata", "West Bengal", "East", 0.08),
    ("Bhubaneswar", "Odisha", "East", 0.03), ("Patna", "Bihar", "East", 0.02),
    ("Guwahati", "Assam", "East", 0.02),
]
city_df = pd.DataFrame(CITIES, columns=["city", "state", "region", "w"])
city_df["w"] /= city_df["w"].sum()

# ---------------------------------------------------------------- customers
N_CUST = 3200
cust = pd.DataFrame({
    "customer_id": [f"C{10001 + i}" for i in range(N_CUST)],
    "gender": rng.choice(["Male", "Female"], N_CUST, p=[0.54, 0.46]),
    "age": np.clip(rng.normal(31, 8, N_CUST).round(), 18, 65).astype(int),
    "home_city": rng.choice(city_df.index, N_CUST, p=city_df["w"]),
})
# Pareto-like loyalty: a small group of customers buys very often
cust["activity"] = rng.pareto(1.6, N_CUST) + 1
cust["activity"] /= cust["activity"].sum()

# ---------------------------------------------------------------- order dates
months = pd.period_range("2024-01", "2025-12", freq="M")
SEASON = {1: 0.80, 2: 0.82, 3: 0.95, 4: 0.92, 5: 0.95, 6: 0.90,
          7: 0.98, 8: 1.05, 9: 1.10, 10: 1.75, 11: 1.55, 12: 1.15}  # Diwali in Oct/Nov
BASE_ORDERS = 330
rows = []
order_no = 500001
for i, m in enumerate(months):
    n_orders = int(BASE_ORDERS * (1.018 ** i) * SEASON[m.month] * rng.uniform(0.95, 1.05))
    days = rng.integers(1, m.days_in_month + 1, n_orders)
    for d in days:
        date = pd.Timestamp(year=m.year, month=m.month, day=int(d))
        c = cust.iloc[rng.choice(N_CUST, p=cust["activity"])]
        # 85% of the time a customer orders to their home city
        ci = c.home_city if rng.random() < 0.85 else rng.choice(city_df.index, p=city_df["w"])
        city = city_df.loc[ci]
        # South region grows faster in 2025 (new warehouse in Bangalore)
        if m.year == 2025 and city.region != "South" and rng.random() < 0.10:
            city = city_df[city_df.region == "South"].sample(1, random_state=int(rng.integers(1e9))).iloc[0]
        p = prod_df.iloc[rng.choice(len(prod_df), p=prod_df["w"])]

        qty = 1 if p.list_price > 5000 else int(rng.choice([1, 1, 1, 2, 2, 3]))
        festive = m.month in (10, 11)
        # discount policy: mostly modest; some deep-discount campaigns
        if rng.random() < (0.16 if festive else 0.06):
            disc = float(rng.choice([0.30, 0.35, 0.40, 0.45, 0.50]))
        else:
            disc = float(rng.choice([0, 0, 0.05, 0.10, 0.10, 0.15, 0.20]))
        unit_price = round(p.list_price * rng.uniform(0.97, 1.03))
        unit_cost = round(p.list_price * p.cost_ratio)

        payment = rng.choice(["UPI", "Credit Card", "Debit Card", "Cash on Delivery",
                              "Net Banking", "Wallet"],
                             p=[0.42, 0.18, 0.12, 0.18, 0.05, 0.05])
        delivery_days = int(np.clip(rng.normal(4.5 if city.region != "East" else 6.5, 1.8), 1, 14))

        # order status
        cancel_p = 0.11 if payment == "Cash on Delivery" else 0.025
        ret_p = RETURN_RATE[p.category] * (1.8 if delivery_days >= 8 else 1.0)
        r = rng.random()
        status = "Cancelled" if r < cancel_p else ("Returned" if r < cancel_p + ret_p else "Delivered")

        rating = None
        if status == "Delivered":
            base = 4.4 - 0.18 * max(0, delivery_days - 5)
            rating = int(np.clip(round(rng.normal(base, 0.8)), 1, 5))
        elif status == "Returned":
            rating = int(rng.choice([1, 1, 2, 2, 3]))

        rows.append({
            "order_id": f"ORD{order_no}",
            "order_date": date,
            "customer_id": c.customer_id,
            "gender": c.gender,
            "customer_age": c.age,
            "city": city.city,
            "state": city.state,
            "region": city.region,
            "product_id": p.product_id,
            "product_name": p.product_name,
            "category": p.category,
            "sub_category": p.sub_category,
            "quantity": qty,
            "unit_price": unit_price,
            "unit_cost": unit_cost,
            "discount_pct": disc,
            "payment_method": payment,
            "order_status": status,
            "delivery_days": delivery_days if status != "Cancelled" else None,
            "customer_rating": rating,
        })
        order_no += 1

df = pd.DataFrame(rows).sort_values(["order_date", "order_id"]).reset_index(drop=True)

# ---------------------------------------------------------------- make it messy
n = len(df)
df = df.astype({"unit_price": object, "customer_age": object, "quantity": object})

# 1) mixed date formats
fmt_choice = rng.choice(3, n, p=[0.70, 0.20, 0.10])
df["order_date"] = [
    d.strftime("%Y-%m-%d") if f == 0 else d.strftime("%d/%m/%Y") if f == 1 else d.strftime("%d-%b-%Y")
    for d, f in zip(df["order_date"], fmt_choice)
]
# 2) inconsistent city text
idx = rng.choice(n, int(n * 0.06), replace=False)
df.loc[idx, "city"] = [rng.choice([c.upper(), c.lower(), f" {c} ", f"{c} "]) for c in df.loc[idx, "city"]]
blr = df.index[df["city"] == "Bangalore"]
df.loc[rng.choice(blr, int(len(blr) * 0.25), replace=False), "city"] = "Bengaluru"
# 3) currency symbols / commas in price
idx = rng.choice(n, int(n * 0.08), replace=False)
df.loc[idx, "unit_price"] = [f"₹{int(v):,}" for v in df.loc[idx, "unit_price"]]
# 4) inconsistent payment labels
pay_map = {"UPI": ["upi", "UPI "], "Cash on Delivery": ["COD", "cod"], "Credit Card": ["credit card", "CC"]}
for k, variants in pay_map.items():
    k_idx = df.index[df["payment_method"] == k]
    pick = rng.choice(k_idx, int(len(k_idx) * 0.07), replace=False)
    df.loc[pick, "payment_method"] = rng.choice(variants, len(pick))
# 5) missing values
df.loc[rng.choice(n, int(n * 0.03), replace=False), "customer_age"] = None
df.loc[rng.choice(n, int(n * 0.02), replace=False), "gender"] = None
df.loc[rng.choice(n, int(n * 0.01), replace=False), "region"] = None
# 6) impossible values (data-entry errors)
df.loc[rng.choice(n, 12, replace=False), "customer_age"] = rng.choice([0, 150, 999, -5], 12)
df.loc[rng.choice(n, 15, replace=False), "quantity"] = rng.choice([0, -1, -2], 15)
# 7) duplicate rows (system double-logging)
dups = df.sample(int(n * 0.015), random_state=SEED)
df = pd.concat([df, dups]).sample(frac=1, random_state=SEED).reset_index(drop=True)

OUT.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(OUT, index=False)
print(f"Wrote {len(df):,} rows -> {OUT.relative_to(ROOT)}")
