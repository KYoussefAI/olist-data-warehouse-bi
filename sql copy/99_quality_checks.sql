-- Diagnostic quality checks. These SELECTs should return zero rows for failed checks where noted.

-- Orphan checks in DWH facts
SELECT 'fact_order_items_missing_order_key' AS check_name, COUNT(*) AS failed_rows
FROM dwh.fact_order_items WHERE order_key IS NULL;

SELECT 'fact_payments_missing_order_key' AS check_name, COUNT(*) AS failed_rows
FROM dwh.fact_payments WHERE order_key IS NULL;

SELECT 'fact_reviews_missing_order_key' AS check_name, COUNT(*) AS failed_rows
FROM dwh.fact_reviews WHERE order_key IS NULL;

SELECT 'fact_order_items_missing_product_key' AS check_name, COUNT(*) AS failed_rows
FROM dwh.fact_order_items WHERE product_key IS NULL;

SELECT 'fact_order_items_missing_seller_key' AS check_name, COUNT(*) AS failed_rows
FROM dwh.fact_order_items WHERE seller_key IS NULL;

-- Business diagnostics
SELECT 'closed_deals_not_active_sellers' AS check_name, COUNT(*) AS rows_count
FROM dwh.fact_closed_deals WHERE is_active_seller = FALSE;

SELECT 'reviews_outside_1_5' AS check_name, COUNT(*) AS failed_rows
FROM dwh.fact_reviews WHERE review_score NOT BETWEEN 1 AND 5;
