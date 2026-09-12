-- validation_queries_mysql.sql
-- Post-load checks for the Candy Distributor warehouse (MySQL version).
-- Same logic as sql/validation_queries.sql (SQLite) — the SQL here is
-- ANSI-standard enough that nothing needed to change except this header
-- and confirming compatibility with MySQL 8's default ONLY_FULL_GROUP_BY
-- mode (query 8 only selects grouped/aggregated columns, so it's fine).
--
-- Run with: mysql -u root -p candy_warehouse < sql\validation_queries_mysql.sql
-- (or paste individual queries into Workbench)

USE candy_warehouse;

-- ============================================================
-- 1. ROW COUNTS — confirm nothing was dropped or duplicated
-- ============================================================
-- Expect: 5, 3, 15, 631, 10194
SELECT 'dim_factories' AS table_name, COUNT(*) AS row_count FROM dim_factories
UNION ALL
SELECT 'dim_targets', COUNT(*) FROM dim_targets
UNION ALL
SELECT 'dim_products', COUNT(*) FROM dim_products
UNION ALL
SELECT 'dim_geography', COUNT(*) FROM dim_geography
UNION ALL
SELECT 'fact_sales', COUNT(*) FROM fact_sales;


-- ============================================================
-- 2. DUPLICATE PRIMARY KEYS — should all return 0 rows
-- ============================================================
SELECT row_id, COUNT(*) AS n
FROM fact_sales
GROUP BY row_id
HAVING COUNT(*) > 1;

SELECT product_id, COUNT(*) AS n
FROM dim_products
GROUP BY product_id
HAVING COUNT(*) > 1;


-- ============================================================
-- 3. ORPHANED FOREIGN KEYS — should all return 0 rows
--    (product_id and division ARE enforced via FK, so these should
--    always be empty; this is a belt-and-suspenders check)
-- ============================================================
SELECT s.product_id
FROM fact_sales s
LEFT JOIN dim_products p ON s.product_id = p.product_id
WHERE p.product_id IS NULL;

SELECT s.division
FROM fact_sales s
LEFT JOIN dim_targets t ON s.division = t.division
WHERE t.division IS NULL;

SELECT p.factory_name
FROM dim_products p
LEFT JOIN dim_factories f ON p.factory_name = f.factory_name
WHERE f.factory_name IS NULL;


-- ============================================================
-- 4. POSTAL CODE COVERAGE — postal_code has no enforced FK
--    (dim_geography is US-only; Sales includes Canada), so this
--    is informational, not a failure. Expect 23 unmatched
--    DISTINCT zips / 200 unmatched fact_sales rows.
-- ============================================================
SELECT COUNT(*) AS unmatched_postal_code_rows
FROM fact_sales s
LEFT JOIN dim_geography g ON s.postal_code = g.zip
WHERE g.zip IS NULL;


-- ============================================================
-- 5. NULL CHECKS on columns that should never be null
-- ============================================================
SELECT COUNT(*) AS null_order_id FROM fact_sales WHERE order_id IS NULL;
SELECT COUNT(*) AS null_product_id FROM fact_sales WHERE product_id IS NULL;
SELECT COUNT(*) AS null_sales_amount FROM fact_sales WHERE sales IS NULL;


-- ============================================================
-- 6. GROSS PROFIT CONSISTENCY — flags rows where the loaded
--    Gross Profit doesn't equal Sales - Cost.
-- ============================================================
SELECT row_id, sales, cost, gross_profit, (sales - cost) AS expected_gp
FROM fact_sales
WHERE ABS(gross_profit - (sales - cost)) > 0.01;


-- ============================================================
-- 7. AGGREGATE SANITY CHECK — compare against raw CSV totals
--    via pandas: df['Sales'].sum() etc. Should match exactly.
-- ============================================================
SELECT
    COUNT(*)              AS total_rows,
    SUM(sales)            AS total_sales,
    SUM(gross_profit)     AS total_gross_profit,
    SUM(cost)             AS total_cost,
    SUM(units)            AS total_units
FROM fact_sales;


-- ============================================================
-- 8. SPOT-CHECK BUSINESS QUERY — sales by division vs. target
-- ============================================================
SELECT
    t.division,
    t.target,
    SUM(s.sales) AS actual_sales,
    ROUND(100.0 * SUM(s.sales) / t.target, 1) AS pct_of_target
FROM fact_sales s
JOIN dim_targets t ON s.division = t.division
GROUP BY t.division, t.target
ORDER BY pct_of_target DESC;
