# Power BI Dashboard – Step-by-Step Build Guide

Build a 2-page interactive dashboard from `data/processed/shopkart_sales_clean.csv`.
(Excel users: the same visuals work with PivotTables + PivotCharts + Slicers — see the end of this guide.)

Time needed: ~2–3 hours.

---

## 1. Load the data
1. **Home → Get Data → Text/CSV** → select `shopkart_sales_clean.csv` → **Transform Data**.
2. In Power Query, check data types:
   - `order_date` → Date
   - `unit_price, unit_cost, discount_pct, gross_sales, net_sales, profit, revenue, realised_profit` → Decimal number
   - `quantity, year, month, delivery_days, customer_rating` → Whole number
3. Rename the query to **Sales** → **Close & Apply**.

## 2. Create a Date table (good practice – interviewers notice this)
**Modeling → New Table**
```DAX
Date =
ADDCOLUMNS (
    CALENDAR ( DATE ( 2024, 1, 1 ), DATE ( 2025, 12, 31 ) ),
    "Year", YEAR ( [Date] ),
    "Month No", MONTH ( [Date] ),
    "Month", FORMAT ( [Date], "MMM" ),
    "Year-Month", FORMAT ( [Date], "YYYY-MM" ),
    "Quarter", "Q" & QUARTER ( [Date] )
)
```
- Mark it as a date table (**Table tools → Mark as date table**).
- Sort `Month` by `Month No`.
- **Model view:** drag `Date[Date]` → `Sales[order_date]` (one-to-many).

## 3. DAX measures
Create a blank table called **_Measures** to keep them together.
```DAX
Total Revenue      = SUM ( Sales[revenue] )
Total Profit       = SUM ( Sales[realised_profit] )
Profit Margin %    = DIVIDE ( [Total Profit], [Total Revenue] )
Total Orders       = DISTINCTCOUNT ( Sales[order_id] )
Total Customers    = DISTINCTCOUNT ( Sales[customer_id] )
Delivered Orders   = CALCULATE ( [Total Orders], Sales[order_status] = "Delivered" )
Avg Order Value    = DIVIDE ( [Total Revenue], [Delivered Orders] )

Return Rate %      = DIVIDE ( CALCULATE ( [Total Orders], Sales[order_status] = "Returned" ),  [Total Orders] )
Cancel Rate %      = DIVIDE ( CALCULATE ( [Total Orders], Sales[order_status] = "Cancelled" ), [Total Orders] )
Lost Revenue       = CALCULATE ( SUM ( Sales[net_sales] ), Sales[order_status] <> "Delivered" )
Avg Rating         = CALCULATE ( AVERAGE ( Sales[customer_rating] ), Sales[order_status] = "Delivered" )

Revenue LY         = CALCULATE ( [Total Revenue], SAMEPERIODLASTYEAR ( 'Date'[Date] ) )
Revenue YoY %      = DIVIDE ( [Total Revenue] - [Revenue LY], [Revenue LY] )
Profit LY          = CALCULATE ( [Total Profit], SAMEPERIODLASTYEAR ( 'Date'[Date] ) )
Profit YoY %       = DIVIDE ( [Total Profit] - [Profit LY], [Profit LY] )
```
Format the `%` measures as Percentage and the money measures as Currency (₹).

## 4. Page 1 – "Executive Overview"
| Position | Visual | Fields |
|---|---|---|
| Top row | 5 **Card** visuals | Total Revenue, Total Profit, Profit Margin %, Total Orders, Avg Order Value |
| Middle left (wide) | **Line chart** | X: `Date[Year-Month]`, Y: Total Revenue (add Profit as a 2nd line only if both share the same axis) |
| Middle right | **Clustered bar** | Y: `category`, X: Total Revenue & Total Profit |
| Bottom left | **Column chart** | X: `discount_band` (sort in order), Y: Profit Margin % — use conditional formatting: red if < 0 |
| Bottom right | **Filled map** or **bar** | `state` / `city` by Total Revenue |
| Top / side | **Slicers** | `Date[Year]`, `region`, `category`, `payment_method` |

Title: *"ShopKart Sales Overview 2024–2025"*. Add a text box with the 3 key takeaways.

## 5. Page 2 – "Operations & Customers"
| Visual | Fields |
|---|---|
| Cards | Return Rate %, Cancel Rate %, Lost Revenue, Avg Rating |
| **Bar** | `category` by Return Rate % |
| **Bar** | `payment_method` by Cancel Rate % |
| **Column** | `delivery_days` (grouped 1-3 / 4-5 / 6-7 / 8+) by Return Rate % and Avg Rating (two separate visuals) |
| **Matrix** | Rows `age_group`, Columns `gender`, Values Total Revenue (conditional formatting → background color scale) |
| **Table** | Top 10 products by Total Profit (Top N filter) |

To group delivery days: right-click `delivery_days` → **New group** → Bin size 2, or create a calculated column:
```DAX
Delivery Bucket =
SWITCH ( TRUE (),
    ISBLANK ( Sales[delivery_days] ), "Cancelled",
    Sales[delivery_days] <= 3, "1-3 days",
    Sales[delivery_days] <= 5, "4-5 days",
    Sales[delivery_days] <= 7, "6-7 days",
    "8+ days" )
```

## 6. Design tips
- Use 2–3 colours only: one main colour, one highlight colour for bad news (losses, high returns), grey for the rest.
- Same font, aligned visuals, consistent number formats (₹ lakh: Display units → Lakhs isn't built-in, so use Millions or a custom format).
- Every chart title should state the insight, e.g. *"Discounts above 20% lose money"* — not just *"Margin by discount"*.
- Add a **Reset filters** bookmark button and tooltips.

## 7. Publish & showcase
- **File → Publish → Publish to web** (free Power BI account) and put the link in your README / resume, **or**
- Export screenshots to `images/` and a PDF to `dashboard/`.

---

## Excel version (if you don't have Power BI)
1. Open the clean CSV → **Insert → Table**.
2. Create PivotTables on a new sheet for: revenue by Year-Month, revenue & profit by category, margin by discount band,
   cancel rate by payment method (use *Show values as → % of row total* on `order_status`).
3. Add **PivotCharts** for each, and **Slicers** (region, year, category) connected to all pivots (*Report Connections*).
4. KPI cards: cells with `=GETPIVOTDATA(...)` or `=SUMIFS(...)`, formatted large.
5. Arrange on a single "Dashboard" sheet, hide gridlines (View → uncheck Gridlines).
