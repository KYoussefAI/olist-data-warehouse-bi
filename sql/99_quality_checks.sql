-- Manual quality checks for the Olist Data Warehouse.
-- Run in psql or any SQL client after the ELT load.

SELECT 'raw_orders_loaded' AS check_name, COUNT(*)::TEXT AS value, (COUNT(*) > 0) AS passed
FROM raw.olist_orders
UNION ALL
SELECT 'dwh_fact_orders_loaded', COUNT(*)::TEXT, (COUNT(*) > 0)
FROM dwh.fact_orders
UNION ALL
SELECT 'fact_order_items_missing_order_key', COUNT(*)::TEXT, (COUNT(*) = 0)
FROM dwh.fact_order_items WHERE order_key IS NULL
UNION ALL
SELECT 'fact_order_items_missing_product_key', COUNT(*)::TEXT, (COUNT(*) = 0)
FROM dwh.fact_order_items WHERE product_key IS NULL
UNION ALL
SELECT 'fact_order_items_missing_seller_key', COUNT(*)::TEXT, (COUNT(*) = 0)
FROM dwh.fact_order_items WHERE seller_key IS NULL
UNION ALL
SELECT 'fact_payments_missing_order_key', COUNT(*)::TEXT, (COUNT(*) = 0)
FROM dwh.fact_payments WHERE order_key IS NULL
UNION ALL
SELECT 'fact_reviews_missing_order_key', COUNT(*)::TEXT, (COUNT(*) = 0)
FROM dwh.fact_reviews WHERE order_key IS NULL
UNION ALL
SELECT 'reviews_outside_1_5', COUNT(*)::TEXT, (COUNT(*) = 0)
FROM dwh.fact_reviews WHERE review_score NOT BETWEEN 1 AND 5
UNION ALL
SELECT 'marts_sales_overview_loaded', COUNT(*)::TEXT, (COUNT(*) > 0)
FROM marts.sales_overview
UNION ALL
SELECT 'marts_payment_analysis_loaded', COUNT(*)::TEXT, (COUNT(*) > 0)
FROM marts.payment_analysis
UNION ALL
SELECT 'marts_customer_satisfaction_loaded', COUNT(*)::TEXT, (COUNT(*) > 0)
FROM marts.customer_satisfaction;
