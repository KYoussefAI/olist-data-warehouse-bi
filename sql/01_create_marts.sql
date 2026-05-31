-- Dedicated analytical marts for the Streamlit dashboard.
-- This file can be executed with: python -m src.run_etl --step marts

CREATE SCHEMA IF NOT EXISTS marts;

CREATE OR REPLACE VIEW marts.sales_overview AS
SELECT
    dd.year_number,
    dd.month_number,
    dd.month_name,
    os.order_status,
    COUNT(DISTINCT fo.order_id) AS order_count,
    COUNT(foi.order_item_key) AS item_count,
    COALESCE(SUM(foi.item_price), 0) AS gross_item_value,
    COALESCE(SUM(foi.freight_value), 0) AS gross_freight_value,
    COALESCE(SUM(foi.item_price + foi.freight_value), 0) AS gross_revenue
FROM dwh.fact_orders fo
LEFT JOIN dwh.fact_order_items foi ON fo.order_key = foi.order_key
LEFT JOIN dwh.dim_date dd ON fo.purchase_date_key = dd.date_key
LEFT JOIN dwh.dim_order_status os ON fo.order_status_key = os.order_status_key
GROUP BY dd.year_number, dd.month_number, dd.month_name, os.order_status;

CREATE OR REPLACE VIEW marts.sales_by_category AS
SELECT
    COALESCE(NULLIF(dpc.product_category_name_english, ''), dpc.product_category_name, 'unknown') AS product_category,
    COUNT(foi.order_item_key) AS item_count,
    COUNT(DISTINCT foi.order_id) AS order_count,
    COALESCE(SUM(foi.item_price), 0) AS gross_item_value,
    COALESCE(SUM(foi.freight_value), 0) AS gross_freight_value,
    COALESCE(SUM(foi.item_price + foi.freight_value), 0) AS gross_revenue
FROM dwh.fact_order_items foi
LEFT JOIN dwh.dim_product dp ON foi.product_key = dp.product_key
LEFT JOIN dwh.dim_product_category dpc ON dp.product_category_key = dpc.product_category_key
GROUP BY COALESCE(NULLIF(dpc.product_category_name_english, ''), dpc.product_category_name, 'unknown');

CREATE OR REPLACE VIEW marts.payment_analysis AS
SELECT
    dd.year_number,
    dd.month_number,
    dd.month_name,
    pt.payment_type,
    fp.payment_installments,
    COUNT(*) AS payment_count,
    COALESCE(SUM(fp.payment_value), 0) AS total_payment_value,
    AVG(fp.payment_value) AS avg_payment_value
FROM dwh.fact_payments fp
LEFT JOIN dwh.fact_orders fo ON fp.order_key = fo.order_key
LEFT JOIN dwh.dim_date dd ON fo.purchase_date_key = dd.date_key
LEFT JOIN dwh.dim_payment_type pt ON fp.payment_type_key = pt.payment_type_key
GROUP BY dd.year_number, dd.month_number, dd.month_name, pt.payment_type, fp.payment_installments;

CREATE OR REPLACE VIEW marts.customer_satisfaction AS
SELECT
    dd.year_number,
    dd.month_number,
    dd.month_name,
    fr.review_score,
    COUNT(*) AS review_count,
    AVG(fr.review_score::NUMERIC) AS avg_review_score
FROM dwh.fact_reviews fr
LEFT JOIN dwh.dim_date dd ON fr.review_creation_date_key = dd.date_key
GROUP BY dd.year_number, dd.month_number, dd.month_name, fr.review_score;

CREATE OR REPLACE VIEW marts.delivery_performance AS
SELECT
    dd.year_number,
    dd.month_number,
    dd.month_name,
    os.order_status,
    COUNT(*) AS delivered_orders,
    AVG(EXTRACT(EPOCH FROM (fo.order_delivered_customer_ts - fo.order_purchase_ts)) / 86400.0) AS avg_days_purchase_to_delivery,
    AVG(EXTRACT(EPOCH FROM (fo.order_delivered_customer_ts - fo.order_estimated_delivery_ts)) / 86400.0) AS avg_days_vs_estimate,
    AVG(CASE WHEN fo.is_delivered_on_time THEN 1.0 ELSE 0.0 END) AS on_time_rate
FROM dwh.fact_orders fo
LEFT JOIN dwh.dim_date dd ON fo.purchase_date_key = dd.date_key
LEFT JOIN dwh.dim_order_status os ON fo.order_status_key = os.order_status_key
WHERE fo.order_delivered_customer_ts IS NOT NULL
GROUP BY dd.year_number, dd.month_number, dd.month_name, os.order_status;

CREATE OR REPLACE VIEW marts.marketing_funnel AS
SELECT
    dd.year_number,
    dd.month_number,
    dd.month_name,
    mo.origin_name AS marketing_origin,
    COUNT(DISTINCT fml.mql_id) AS mql_count,
    COUNT(DISTINCT fcd.mql_id) AS won_deal_count,
    COALESCE(SUM(fcd.declared_monthly_revenue), 0) AS declared_monthly_revenue_sum,
    CASE
        WHEN COUNT(DISTINCT fml.mql_id) = 0 THEN 0
        ELSE COUNT(DISTINCT fcd.mql_id)::NUMERIC / COUNT(DISTINCT fml.mql_id)
    END AS conversion_rate
FROM dwh.fact_marketing_leads fml
LEFT JOIN dwh.fact_closed_deals fcd ON fml.mql_id = fcd.mql_id
LEFT JOIN dwh.dim_date dd ON fml.first_contact_date_key = dd.date_key
LEFT JOIN dwh.dim_marketing_origin mo ON fml.marketing_origin_key = mo.marketing_origin_key
GROUP BY dd.year_number, dd.month_number, dd.month_name, mo.origin_name;
