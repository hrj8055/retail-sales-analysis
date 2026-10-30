/* =====================================================================
   ShopKart Sales Analysis - Business Questions in SQL
   Table: orders  (one row per order line, created by load_to_sqlite.py)
   Key columns:
     revenue          = net sales of DELIVERED orders only
     realised_profit  = profit of DELIVERED orders only
     net_sales        = sales after discount (all statuses)
   Dialect: SQLite (works in MySQL/PostgreSQL with small date-function changes)
   ===================================================================== */

-- Q1. Overall KPIs: orders, customers, revenue, profit, margin, AOV
SELECT
    COUNT(DISTINCT order_id)                                   AS total_orders,
    COUNT(DISTINCT customer_id)                                AS total_customers,
    ROUND(SUM(revenue) / 1e5, 2)                               AS revenue_lakh,
    ROUND(SUM(realised_profit) / 1e5, 2)                       AS profit_lakh,
    ROUND(100.0 * SUM(realised_profit) / SUM(revenue), 2)      AS profit_margin_pct,
    ROUND(SUM(revenue) / SUM(order_status = 'Delivered'), 0)   AS avg_order_value
FROM orders;

-- Q2. Year-over-year growth in revenue and profit
WITH yearly AS (
    SELECT year,
           SUM(revenue)         AS revenue,
           SUM(realised_profit) AS profit
    FROM orders
    GROUP BY year
)
SELECT year,
       ROUND(revenue / 1e5, 2) AS revenue_lakh,
       ROUND(profit / 1e5, 2)  AS profit_lakh,
       ROUND(100.0 * (revenue - LAG(revenue) OVER (ORDER BY year))
             / LAG(revenue) OVER (ORDER BY year), 1) AS revenue_growth_pct
FROM yearly;

-- Q3. Monthly revenue trend with month-over-month growth (window function)
WITH monthly AS (
    SELECT year_month, SUM(revenue) AS revenue
    FROM orders
    GROUP BY year_month
)
SELECT year_month,
       ROUND(revenue / 1e5, 2) AS revenue_lakh,
       ROUND(100.0 * (revenue - LAG(revenue) OVER (ORDER BY year_month))
             / LAG(revenue) OVER (ORDER BY year_month), 1) AS mom_growth_pct
FROM monthly
ORDER BY year_month;

-- Q4. Category performance: revenue share vs profit share
SELECT category,
       ROUND(SUM(revenue) / 1e5, 2)                                         AS revenue_lakh,
       ROUND(100.0 * SUM(revenue) / (SELECT SUM(revenue) FROM orders), 1)   AS revenue_share_pct,
       ROUND(SUM(realised_profit) / 1e5, 2)                                 AS profit_lakh,
       ROUND(100.0 * SUM(realised_profit)
             / (SELECT SUM(realised_profit) FROM orders), 1)                AS profit_share_pct,
       ROUND(100.0 * SUM(realised_profit) / SUM(revenue), 1)               AS margin_pct
FROM orders
GROUP BY category
ORDER BY revenue_lakh DESC;

-- Q5. Top 10 products by profit
SELECT product_name, category,
       SUM(quantity)                          AS units_sold,
       ROUND(SUM(revenue) / 1e5, 2)           AS revenue_lakh,
       ROUND(SUM(realised_profit) / 1e5, 2)   AS profit_lakh
FROM orders
GROUP BY product_name, category
ORDER BY profit_lakh DESC
LIMIT 10;

-- Q6. Products that LOSE money overall
SELECT product_name, category,
       ROUND(SUM(revenue) / 1e5, 2)          AS revenue_lakh,
       ROUND(SUM(realised_profit) / 1e5, 2)  AS profit_lakh
FROM orders
GROUP BY product_name, category
HAVING SUM(realised_profit) < 0
ORDER BY profit_lakh;

-- Q7. Impact of discount level on profitability
SELECT discount_band,
       COUNT(*)                                               AS orders,
       ROUND(SUM(revenue) / 1e5, 2)                           AS revenue_lakh,
       ROUND(SUM(realised_profit) / 1e5, 2)                   AS profit_lakh,
       ROUND(100.0 * SUM(realised_profit) / SUM(revenue), 1)  AS margin_pct
FROM orders
GROUP BY discount_band
ORDER BY CASE discount_band
            WHEN 'No discount' THEN 1 WHEN '1-10%' THEN 2 WHEN '11-20%' THEN 3
            WHEN '21-30%' THEN 4 ELSE 5 END;

-- Q8. Regional revenue, 2024 vs 2025 (conditional aggregation)
SELECT region,
       ROUND(SUM(CASE WHEN year = 2024 THEN revenue END) / 1e5, 2) AS rev_2024_lakh,
       ROUND(SUM(CASE WHEN year = 2025 THEN revenue END) / 1e5, 2) AS rev_2025_lakh,
       ROUND(100.0 * (SUM(CASE WHEN year = 2025 THEN revenue END)
                    - SUM(CASE WHEN year = 2024 THEN revenue END))
                    / SUM(CASE WHEN year = 2024 THEN revenue END), 1) AS growth_pct
FROM orders
GROUP BY region
ORDER BY growth_pct DESC;

-- Q9. Top 3 cities in each region by revenue (RANK window function)
WITH city_rev AS (
    SELECT region, city, SUM(revenue) AS revenue,
           RANK() OVER (PARTITION BY region ORDER BY SUM(revenue) DESC) AS rnk
    FROM orders
    GROUP BY region, city
)
SELECT region, city, ROUND(revenue / 1e5, 2) AS revenue_lakh, rnk
FROM city_rev
WHERE rnk <= 3
ORDER BY region, rnk;

-- Q10. Return and cancellation rate by category
SELECT category,
       COUNT(*)                                                         AS orders,
       ROUND(100.0 * SUM(order_status = 'Returned')  / COUNT(*), 1)     AS return_rate_pct,
       ROUND(100.0 * SUM(order_status = 'Cancelled') / COUNT(*), 1)     AS cancel_rate_pct
FROM orders
GROUP BY category
ORDER BY return_rate_pct DESC;

-- Q11. Cancellation rate by payment method (is COD a problem?)
SELECT payment_method,
       COUNT(*)                                                      AS orders,
       ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM orders), 1)   AS share_pct,
       ROUND(100.0 * SUM(order_status = 'Cancelled') / COUNT(*), 1)  AS cancel_rate_pct
FROM orders
GROUP BY payment_method
ORDER BY cancel_rate_pct DESC;

-- Q12. Delivery speed vs customer rating and returns
SELECT CASE WHEN delivery_days <= 3 THEN '1-3 days'
            WHEN delivery_days <= 5 THEN '4-5 days'
            WHEN delivery_days <= 7 THEN '6-7 days'
            ELSE '8+ days' END                                        AS delivery_bucket,
       COUNT(*)                                                       AS orders,
       ROUND(AVG(CASE WHEN order_status = 'Delivered'
                      THEN customer_rating END), 2)                   AS avg_rating,
       ROUND(100.0 * SUM(order_status = 'Returned') / COUNT(*), 1)   AS return_rate_pct
FROM orders
WHERE delivery_days IS NOT NULL
GROUP BY delivery_bucket
ORDER BY delivery_bucket;

-- Q13. Customer concentration: what share of revenue comes from the top 20% of customers?
WITH cust AS (
    SELECT customer_id, SUM(revenue) AS revenue
    FROM orders
    GROUP BY customer_id
    HAVING SUM(revenue) > 0
),
ranked AS (
    SELECT revenue, NTILE(5) OVER (ORDER BY revenue DESC) AS quintile
    FROM cust
)
SELECT quintile,
       COUNT(*)                                                    AS customers,
       ROUND(SUM(revenue) / 1e5, 2)                                AS revenue_lakh,
       ROUND(100.0 * SUM(revenue) / (SELECT SUM(revenue) FROM cust), 1) AS revenue_share_pct
FROM ranked
GROUP BY quintile
ORDER BY quintile;

-- Q14. New vs repeat customers per year (first purchase via subquery)
WITH first_order AS (
    SELECT customer_id, MIN(order_date) AS first_date
    FROM orders
    GROUP BY customer_id
)
SELECT o.year,
       COUNT(DISTINCT CASE WHEN o.order_date = f.first_date THEN o.customer_id END) AS new_customers,
       COUNT(DISTINCT CASE WHEN o.order_date > f.first_date THEN o.customer_id END) AS returning_customers
FROM orders o
JOIN first_order f ON o.customer_id = f.customer_id
GROUP BY o.year;

-- Q15. Revenue by age group and gender
SELECT age_group, gender,
       COUNT(DISTINCT customer_id)        AS customers,
       ROUND(SUM(revenue) / 1e5, 2)       AS revenue_lakh
FROM orders
WHERE gender <> 'Unknown' AND age_group <> 'Unknown'
GROUP BY age_group, gender
ORDER BY age_group, gender;
