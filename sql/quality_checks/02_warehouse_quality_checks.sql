-- ============================================================
-- Warehouse Quality Checks — Olist Data Warehouse & BI
-- Purpose:
-- Validate warehouse dimensions, facts, relationships, and KPIs.
-- ============================================================

-- 1. Warehouse table counts
SELECT 'dim_customer' AS table_name, COUNT(*) AS row_count FROM warehouse.dim_customer
UNION ALL
SELECT 'dim_product', COUNT(*) FROM warehouse.dim_product
UNION ALL
SELECT 'dim_seller', COUNT(*) FROM warehouse.dim_seller
UNION ALL
SELECT 'dim_date', COUNT(*) FROM warehouse.dim_date
UNION ALL
SELECT 'dim_location', COUNT(*) FROM warehouse.dim_location
UNION ALL
SELECT 'dim_order_status', COUNT(*) FROM warehouse.dim_order_status
UNION ALL
SELECT 'dim_payment_type', COUNT(*) FROM warehouse.dim_payment_type
UNION ALL
SELECT 'fact_order_items', COUNT(*) FROM warehouse.fact_order_items
UNION ALL
SELECT 'fact_payments', COUNT(*) FROM warehouse.fact_payments
UNION ALL
SELECT 'fact_reviews', COUNT(*) FROM warehouse.fact_reviews;


-- 2. Null foreign key checks in fact_order_items
SELECT
    'fact_order_items null customer_key' AS check_name,
    COUNT(*) AS null_rows
FROM warehouse.fact_order_items
WHERE customer_key IS NULL;

SELECT
    'fact_order_items null product_key' AS check_name,
    COUNT(*) AS null_rows
FROM warehouse.fact_order_items
WHERE product_key IS NULL;

SELECT
    'fact_order_items null seller_key' AS check_name,
    COUNT(*) AS null_rows
FROM warehouse.fact_order_items
WHERE seller_key IS NULL;

SELECT
    'fact_order_items null purchase_date_key' AS check_name,
    COUNT(*) AS null_rows
FROM warehouse.fact_order_items
WHERE purchase_date_key IS NULL;

SELECT
    'fact_order_items null order_status_key' AS check_name,
    COUNT(*) AS null_rows
FROM warehouse.fact_order_items
WHERE order_status_key IS NULL;

SELECT
    'fact_order_items null customer_location_key' AS check_name,
    COUNT(*) AS null_rows
FROM warehouse.fact_order_items
WHERE customer_location_key IS NULL;

SELECT
    'fact_order_items null seller_location_key' AS check_name,
    COUNT(*) AS null_rows
FROM warehouse.fact_order_items
WHERE seller_location_key IS NULL;


-- 3. Null foreign key checks in fact_payments and fact_reviews
SELECT
    'fact_payments null payment_type_key' AS check_name,
    COUNT(*) AS null_rows
FROM warehouse.fact_payments
WHERE payment_type_key IS NULL;

SELECT
    'fact_reviews null review_date_key' AS check_name,
    COUNT(*) AS null_rows
FROM warehouse.fact_reviews
WHERE review_date_key IS NULL;


-- 4. Duplicate checks in fact tables
SELECT
    'fact_order_items duplicate natural grain' AS check_name,
    COUNT(*) - COUNT(DISTINCT order_id || '-' || order_item_id) AS duplicate_count
FROM warehouse.fact_order_items;

SELECT
    'fact_payments duplicate natural grain' AS check_name,
    COUNT(*) - COUNT(DISTINCT order_id || '-' || payment_sequential) AS duplicate_count
FROM warehouse.fact_payments;

SELECT
    'fact_reviews duplicate natural grain' AS check_name,
    COUNT(*) - COUNT(DISTINCT review_id || '-' || order_id) AS duplicate_count
FROM warehouse.fact_reviews;


-- 5. Main KPI reference values
SELECT
    COUNT(DISTINCT order_id) AS total_orders,
    COUNT(*) AS total_items,
    ROUND(SUM(price), 2) AS total_revenue,
    ROUND(SUM(freight_value), 2) AS total_freight,
    ROUND(SUM(total_item_value), 2) AS total_item_value,
    ROUND(AVG(price), 2) AS average_item_price
FROM warehouse.fact_order_items;


-- 6. Delivery KPI reference values
SELECT
    COUNT(*) AS total_items,
    COUNT(delivery_days) AS items_with_delivery_date,
    COUNT(*) - COUNT(delivery_days) AS items_without_delivery_date,
    ROUND(AVG(delivery_days), 2) AS average_delivery_days,
    ROUND(AVG(CASE WHEN is_late_delivery = TRUE THEN 1 ELSE 0 END) * 100, 2) AS late_delivery_rate_percent
FROM warehouse.fact_order_items;


-- 7. Review KPI reference values
SELECT
    COUNT(*) AS total_reviews,
    ROUND(AVG(review_score), 2) AS average_review_score,
    COUNT(*) FILTER (WHERE review_score <= 2) AS low_review_count,
    ROUND(AVG(CASE WHEN has_review_comment = TRUE THEN 1 ELSE 0 END) * 100, 2) AS review_comment_rate_percent,
    ROUND(AVG(review_answer_delay_days), 2) AS average_review_answer_delay_days
FROM warehouse.fact_reviews;


-- 8. Payment KPI reference values
SELECT
    COUNT(*) AS total_payments,
    ROUND(SUM(payment_value), 2) AS total_payment_value,
    ROUND(AVG(payment_value), 2) AS average_payment_value,
    ROUND(AVG(payment_installments), 2) AS average_installments
FROM warehouse.fact_payments;


-- 9. Revenue by product category
SELECT
    dp.product_category_name_english,
    COUNT(DISTINCT foi.order_id) AS orders,
    COUNT(*) AS items,
    ROUND(SUM(foi.price), 2) AS revenue
FROM warehouse.fact_order_items foi
JOIN warehouse.dim_product dp
    ON foi.product_key = dp.product_key
GROUP BY dp.product_category_name_english
ORDER BY revenue DESC
LIMIT 10;


-- 10. Revenue by month
SELECT
    dd.year,
    dd.month,
    TRIM(dd.month_name) AS month_name,
    COUNT(DISTINCT foi.order_id) AS orders,
    ROUND(SUM(foi.price), 2) AS revenue
FROM warehouse.fact_order_items foi
JOIN warehouse.dim_date dd
    ON foi.purchase_date_key = dd.date_key
GROUP BY dd.year, dd.month, dd.month_name
ORDER BY dd.year, dd.month;


-- 11. Review score distribution
SELECT
    review_score,
    COUNT(*) AS review_count
FROM warehouse.fact_reviews
GROUP BY review_score
ORDER BY review_score;


-- 12. Payment type distribution
SELECT
    dpt.payment_type,
    COUNT(*) AS payment_count,
    ROUND(SUM(fp.payment_value), 2) AS total_payment_value
FROM warehouse.fact_payments fp
JOIN warehouse.dim_payment_type dpt
    ON fp.payment_type_key = dpt.payment_type_key
GROUP BY dpt.payment_type
ORDER BY payment_count DESC;


-- 13. Late delivery by order status
SELECT
    dos.order_status,
    COUNT(*) AS items,
    COUNT(*) FILTER (WHERE foi.is_late_delivery = TRUE) AS late_items,
    ROUND(
        COUNT(*) FILTER (WHERE foi.is_late_delivery = TRUE)::NUMERIC
        / NULLIF(COUNT(*) FILTER (WHERE foi.is_late_delivery IS NOT NULL), 0)
        * 100,
        2
    ) AS late_rate_percent
FROM warehouse.fact_order_items foi
JOIN warehouse.dim_order_status dos
    ON foi.order_status_key = dos.order_status_key
GROUP BY dos.order_status
ORDER BY items DESC;