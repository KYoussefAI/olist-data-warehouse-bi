-- ============================================================
-- Staging Quality Checks — Olist Data Warehouse & BI
-- Purpose:
-- Validate row counts, uniqueness, nulls, duplicates, and
-- relationships before building warehouse dimensions and facts.
-- ============================================================

-- 1. Row counts
SELECT 'customers' AS table_name, COUNT(*) AS row_count FROM staging.customers
UNION ALL
SELECT 'geolocation', COUNT(*) FROM staging.geolocation
UNION ALL
SELECT 'order_items', COUNT(*) FROM staging.order_items
UNION ALL
SELECT 'order_payments', COUNT(*) FROM staging.order_payments
UNION ALL
SELECT 'order_reviews', COUNT(*) FROM staging.order_reviews
UNION ALL
SELECT 'orders', COUNT(*) FROM staging.orders
UNION ALL
SELECT 'products', COUNT(*) FROM staging.products
UNION ALL
SELECT 'sellers', COUNT(*) FROM staging.sellers
UNION ALL
SELECT 'product_category_translation', COUNT(*) FROM staging.product_category_translation;


-- 2. Primary key uniqueness checks

SELECT
    'orders.order_id' AS check_name,
    COUNT(*) AS total_rows,
    COUNT(DISTINCT order_id) AS distinct_values,
    COUNT(*) - COUNT(DISTINCT order_id) AS duplicate_count
FROM staging.orders;

SELECT
    'customers.customer_id' AS check_name,
    COUNT(*) AS total_rows,
    COUNT(DISTINCT customer_id) AS distinct_values,
    COUNT(*) - COUNT(DISTINCT customer_id) AS duplicate_count
FROM staging.customers;

SELECT
    'products.product_id' AS check_name,
    COUNT(*) AS total_rows,
    COUNT(DISTINCT product_id) AS distinct_values,
    COUNT(*) - COUNT(DISTINCT product_id) AS duplicate_count
FROM staging.products;

SELECT
    'sellers.seller_id' AS check_name,
    COUNT(*) AS total_rows,
    COUNT(DISTINCT seller_id) AS distinct_values,
    COUNT(*) - COUNT(DISTINCT seller_id) AS duplicate_count
FROM staging.sellers;


-- 3. Known geolocation duplicate check

SELECT
    'geolocation full duplicate rows' AS check_name,
    COUNT(*) AS duplicate_rows
FROM (
    SELECT
        geolocation_zip_code_prefix,
        geolocation_lat,
        geolocation_lng,
        geolocation_city,
        geolocation_state,
        COUNT(*) AS row_count
    FROM staging.geolocation
    GROUP BY
        geolocation_zip_code_prefix,
        geolocation_lat,
        geolocation_lng,
        geolocation_city,
        geolocation_state
    HAVING COUNT(*) > 1
) duplicated_rows;


-- 4. Foreign key relationship checks

SELECT
    'order_items without matching orders' AS check_name,
    COUNT(*) AS invalid_rows
FROM staging.order_items oi
LEFT JOIN staging.orders o
    ON oi.order_id = o.order_id
WHERE o.order_id IS NULL;

SELECT
    'orders without matching customers' AS check_name,
    COUNT(*) AS invalid_rows
FROM staging.orders o
LEFT JOIN staging.customers c
    ON o.customer_id = c.customer_id
WHERE c.customer_id IS NULL;

SELECT
    'order_items without matching products' AS check_name,
    COUNT(*) AS invalid_rows
FROM staging.order_items oi
LEFT JOIN staging.products p
    ON oi.product_id = p.product_id
WHERE p.product_id IS NULL;

SELECT
    'order_items without matching sellers' AS check_name,
    COUNT(*) AS invalid_rows
FROM staging.order_items oi
LEFT JOIN staging.sellers s
    ON oi.seller_id = s.seller_id
WHERE s.seller_id IS NULL;

SELECT
    'payments without matching orders' AS check_name,
    COUNT(*) AS invalid_rows
FROM staging.order_payments op
LEFT JOIN staging.orders o
    ON op.order_id = o.order_id
WHERE o.order_id IS NULL;

SELECT
    'reviews without matching orders' AS check_name,
    COUNT(*) AS invalid_rows
FROM staging.order_reviews r
LEFT JOIN staging.orders o
    ON r.order_id = o.order_id
WHERE o.order_id IS NULL;


-- 5. Null checks on important columns

SELECT
    'orders null delivery dates' AS check_name,
    COUNT(*) AS null_rows
FROM staging.orders
WHERE order_delivered_customer_date IS NULL;

SELECT
    'products null category' AS check_name,
    COUNT(*) AS null_rows
FROM staging.products
WHERE product_category_name IS NULL;

SELECT
    'reviews null comment message' AS check_name,
    COUNT(*) AS null_rows
FROM staging.order_reviews
WHERE review_comment_message IS NULL;


-- 6. Order status distribution

SELECT
    order_status,
    COUNT(*) AS row_count
FROM staging.orders
GROUP BY order_status
ORDER BY row_count DESC;


-- 7. Review score distribution

SELECT
    review_score,
    COUNT(*) AS row_count
FROM staging.order_reviews
GROUP BY review_score
ORDER BY review_score;


-- 8. Payment type distribution

SELECT
    payment_type,
    COUNT(*) AS row_count
FROM staging.order_payments
GROUP BY payment_type
ORDER BY row_count DESC;