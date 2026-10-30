# How to Present This Project

## Resume bullets (pick 3–4)
**ShopKart Sales Performance Analysis** | Python, SQL, Power BI | [GitHub link]
- Cleaned and analysed **10,900+ e-commerce orders** (2024–25), fixing duplicates, 3 date formats, text inconsistencies and invalid values using pandas.
- Wrote **15 SQL queries** (CTEs, window functions — LAG, RANK, NTILE) to answer business questions on growth, profitability, returns and customer concentration.
- Found that **Electronics drove 64% of revenue but only 5% of profit**, and that discounts above 20% caused a **₹14.4 lakh loss**; recommended a discount cap and shifting festive offers to high-margin categories.
- Identified that **COD orders are cancelled 4× more often** than prepaid and that **8+ day deliveries double the return rate**, with fixes to reduce ₹74 lakh in revenue leakage.
- Built a 2-page **interactive Power BI dashboard** with DAX measures (YoY growth, margin, return rate) for sales leadership.

## 60-second pitch ("Tell me about your project")
> "I analysed two years of order data for an Indian online retailer to find out why profit wasn't keeping pace with revenue.
> First I cleaned the raw data — it had duplicates, three date formats, prices stored as text and invalid ages.
> Then I used SQL and Python to answer six business questions.
> The main finding was that Electronics brought in 64% of revenue but only 5% of profit, because heavy discounts on phones and laptops
> were wiping out an already thin margin — orders with more than 20% discount actually lost ₹14 lakh.
> I also found that Cash-on-Delivery orders were cancelled about four times as often as prepaid ones, and slow deliveries doubled returns.
> I recommended capping Electronics discounts, moving festive offers to high-margin Fashion and Beauty, and nudging customers toward UPI.
> I presented everything in a Power BI dashboard."

Structure it as **Problem → Data/cleaning → Analysis → Key finding → Recommendation**. Always end with the business action.

## Likely interview questions & answers

**Q: Why did you count revenue only for delivered orders?**
Cancelled and returned orders don't bring money in. Counting them would overstate revenue by ~10%. I kept `net_sales` for all orders separately so I could also measure the lost revenue.

**Q: How did you handle missing values?**
It depended on the column. Region was missing for 107 rows, but region is fully decided by state, so I filled it from state.
Age and gender belong to the customer, so I filled them from the same customer's other orders. Rating and delivery days are blank for cancelled orders — that's correct, so I left them.
Only 27 ages were still unknown, and I labelled them "Unknown" rather than guessing.

**Q: Why not fill missing ages with the mean?**
Mean imputation adds fake values and shrinks variation. Since the same customer appears on several orders, their real age was available — a better source than an average.

**Q: What does `LAG` do in your month-over-month query?**
It returns the value from the previous row in the given order, so I could compare each month's revenue to the month before without a self-join.

**Q: Difference between `RANK`, `DENSE_RANK` and `ROW_NUMBER`?**
For ties: ROW_NUMBER gives 1,2,3; RANK gives 1,1,3; DENSE_RANK gives 1,1,2. I used RANK for top-3 cities per region.

**Q: `WHERE` vs `HAVING`?**
WHERE filters rows before grouping; HAVING filters groups after aggregation. I used HAVING to find products whose *total* profit is negative.

**Q: Is the discount finding causal? Maybe deep discounts were only on bad products.**
Good point — it's a correlation. The loss is concentrated in Electronics, where cost is ~88% of price, so any discount over ~12% is mathematically loss-making per unit. To prove that discounts don't bring enough *extra* sales to compensate, I'd recommend an A/B test: same product, different discount levels, compare volume and profit.

**Q: What would you do with more data?**
Add marketing spend (to measure return on discount), shipping and return-handling costs (true profit), and website sessions (conversion rate). I'd also do RFM segmentation and customer lifetime value.

**Q: Which chart would you show the CEO first?**
Revenue share vs profit share by category — it explains the whole "revenue up, profit flat" problem in one picture.

**Q: Is this real data?**
Be honest: "It's a synthetic dataset I generated to mimic a real Indian e-commerce company, including realistic data-quality problems, because company data is confidential. The cleaning, SQL and analysis steps are exactly what I'd do on real data."

## Make it your own (important!)
Recruiters see the same Kaggle projects again and again. To stand out:
1. Change a few parameters in `generate_data.py` (cities, products, seed) and rerun — your numbers will be unique.
2. Build the Power BI dashboard yourself and add screenshots.
3. Add one extra analysis of your own (e.g. RFM segmentation, weekday vs weekend sales, or a forecast for 2026 festive season).
4. Write a short LinkedIn post with your 3 main insights and one chart.
