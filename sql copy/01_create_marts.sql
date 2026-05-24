-- Dashboard marts. Run after DWH tables are populated.

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
    COALESCE(SUM(foi.total_item_value), 0) AS gross_revenue
FROM dwh.fact_orders fo
LEFT JOIN dwh.fact_order_items foi ON fo.order_key = foi.order_key
LEFT JOIN dwh.dim_date dd ON fo.purchase_date_key = dd.date_key
LEFT JOIN dwh.dim_order_status os ON fo.order_status_key = os.order_status_key
GROUP BY dd.year_number, dd.month_number, dd.month_name, os.order_status;

CREATE OR REPLACE VIEW marts.sales_by_category AS
SELECT
    dd.year_number,
    dd.month_number,
    pc.product_category_name_english AS category_name,
    COUNT(foi.order_item_key) AS item_count,
    COUNT(DISTINCT foi.order_id) AS order_count,
    SUM(foi.item_price) AS item_revenue,
    SUM(foi.freight_value) AS freight_revenue,
    SUM(foi.total_item_value) AS total_revenue
FROM dwh.fact_order_items foi
LEFT JOIN dwh.fact_orders fo ON foi.order_key = fo.order_key
LEFT JOIN dwh.dim_date dd ON fo.purchase_date_key = dd.date_key
LEFT JOIN dwh.dim_product p ON foi.product_key = p.product_key
LEFT JOIN dwh.dim_product_category pc ON p.product_category_key = pc.product_category_key
GROUP BY dd.year_number, dd.month_number, pc.product_category_name_english;

CREATE OR REPLACE VIEW marts.delivery_performance AS
SELECT
    dd.year_number,
    dd.month_number,
    dd.month_name,
    os.order_status,
    COUNT(*) FILTER (WHERE fo.is_delivered) AS delivered_orders,
    AVG(fo.days_to_customer) AS avg_days_purchase_to_delivery,
    AVG(fo.delivery_delay_days) AS avg_days_vs_estimate,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE fo.is_delivered AND fo.is_delivered_on_time = FALSE)
        / NULLIF(COUNT(*) FILTER (WHERE fo.is_delivered), 0),
        2
    ) AS late_delivery_rate_pct
FROM dwh.fact_orders fo
LEFT JOIN dwh.dim_date dd ON fo.purchase_date_key = dd.date_key
LEFT JOIN dwh.dim_order_status os ON fo.order_status_key = os.order_status_key
GROUP BY dd.year_number, dd.month_number, dd.month_name, os.order_status;

CREATE OR REPLACE VIEW marts.customer_satisfaction AS
SELECT
    dd.year_number,
    dd.month_number,
    dd.month_name,
    pc.product_category_name_english AS category_name,
    COUNT(fr.review_key) AS review_count,
    AVG(fr.review_score::NUMERIC) AS avg_review_score,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE fr.is_negative_review)
        / NULLIF(COUNT(*), 0),
        2
    ) AS negative_review_rate_pct
FROM dwh.fact_reviews fr
LEFT JOIN dwh.fact_orders fo ON fr.order_key = fo.order_key
LEFT JOIN dwh.fact_order_items foi ON fo.order_key = foi.order_key
LEFT JOIN dwh.dim_product p ON foi.product_key = p.product_key
LEFT JOIN dwh.dim_product_category pc ON p.product_category_key = pc.product_category_key
LEFT JOIN dwh.dim_date dd ON fr.review_creation_date_key = dd.date_key
GROUP BY dd.year_number, dd.month_number, dd.month_name, pc.product_category_name_english;

CREATE OR REPLACE VIEW marts.payment_analysis AS
SELECT
    dd.year_number,
    dd.month_number,
    dd.month_name,
    pt.payment_type,
    fp.payment_installments,
    COUNT(*) AS payment_count,
    SUM(fp.payment_value) AS total_payment_value,
    AVG(fp.payment_value) AS avg_payment_value
FROM dwh.fact_payments fp
LEFT JOIN dwh.fact_orders fo ON fp.order_key = fo.order_key
LEFT JOIN dwh.dim_date dd ON fo.purchase_date_key = dd.date_key
LEFT JOIN dwh.dim_payment_type pt ON fp.payment_type_key = pt.payment_type_key
GROUP BY dd.year_number, dd.month_number, dd.month_name, pt.payment_type, fp.payment_installments;

CREATE OR REPLACE VIEW marts.marketing_funnel AS
SELECT
    dd.year_number,
    dd.month_number,
    dd.month_name,
    mo.origin_name AS marketing_origin,
    COUNT(DISTINCT fml.mql_id) AS mql_count,
    COUNT(DISTINCT fcd.mql_id) AS won_deal_count,
    COUNT(DISTINCT fcd.mql_id) FILTER (WHERE fcd.is_active_seller) AS active_seller_deal_count,
    ROUND(100.0 * COUNT(DISTINCT fcd.mql_id) / NULLIF(COUNT(DISTINCT fml.mql_id), 0), 2) AS lead_to_deal_conversion_rate_pct,
    ROUND(100.0 * COUNT(DISTINCT fcd.mql_id) FILTER (WHERE fcd.is_active_seller) / NULLIF(COUNT(DISTINCT fcd.mql_id), 0), 2) AS active_seller_rate_pct,
    SUM(fcd.declared_monthly_revenue) AS declared_monthly_revenue_sum
FROM dwh.fact_marketing_leads fml
LEFT JOIN dwh.fact_closed_deals fcd ON fml.mql_id = fcd.mql_id
LEFT JOIN dwh.dim_date dd ON fml.first_contact_date_key = dd.date_key
LEFT JOIN dwh.dim_marketing_origin mo ON fml.marketing_origin_key = mo.marketing_origin_key
GROUP BY dd.year_number, dd.month_number, dd.month_name, mo.origin_name;
