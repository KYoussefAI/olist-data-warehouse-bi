-- ============================================================
-- Reporting Views — Olist Data Warehouse & BI
-- Purpose:
-- Create analytical SQL views for Power BI reporting.
-- ============================================================

DROP SCHEMA IF EXISTS reporting CASCADE;

CREATE SCHEMA reporting;

-- ============================================================
-- 1. Sales Overview
-- One row per order item enriched with dimensions.
-- ============================================================

CREATE VIEW reporting.vw_sales_overview AS
SELECT
    foi.order_id,
    foi.order_item_id,

    dd.full_date AS purchase_date,
    dd.year AS purchase_year,
    dd.month AS purchase_month,
    TRIM(dd.month_name) AS purchase_month_name,
    dd.quarter AS purchase_quarter,

    dc.customer_id,
    dc.customer_unique_id,
    dc.customer_city,
    dc.customer_state,

    dp.product_id,
    dp.product_category_name,
    dp.product_category_name_english,

    ds.seller_id,
    ds.seller_city,
    ds.seller_state,

    dos.order_status,

    cl.city AS customer_location_city,
    cl.state AS customer_location_state,
    cl.latitude AS customer_latitude,
    cl.longitude AS customer_longitude,

    sl.city AS seller_location_city,
    sl.state AS seller_location_state,
    sl.latitude AS seller_latitude,
    sl.longitude AS seller_longitude,

    foi.price,
    foi.freight_value,
    foi.total_item_value,
    foi.delivery_days,
    foi.is_late_delivery

FROM warehouse.fact_order_items foi
LEFT JOIN warehouse.dim_date dd
    ON foi.purchase_date_key = dd.date_key
LEFT JOIN warehouse.dim_customer dc
    ON foi.customer_key = dc.customer_key
LEFT JOIN warehouse.dim_product dp
    ON foi.product_key = dp.product_key
LEFT JOIN warehouse.dim_seller ds
    ON foi.seller_key = ds.seller_key
LEFT JOIN warehouse.dim_order_status dos
    ON foi.order_status_key = dos.order_status_key
LEFT JOIN warehouse.dim_location cl
    ON foi.customer_location_key = cl.location_key
LEFT JOIN warehouse.dim_location sl
    ON foi.seller_location_key = sl.location_key;


-- ============================================================
-- 2. Revenue by Month
-- Used for monthly sales trend visuals.
-- ============================================================

CREATE VIEW reporting.vw_revenue_by_month AS
SELECT
    dd.year,
    dd.month,
    TRIM(dd.month_name) AS month_name,
    dd.quarter,

    COUNT(DISTINCT foi.order_id) AS total_orders,
    COUNT(*) AS total_items,
    ROUND(SUM(foi.price), 2) AS total_revenue,
    ROUND(SUM(foi.freight_value), 2) AS total_freight,
    ROUND(SUM(foi.total_item_value), 2) AS total_item_value,
    ROUND(AVG(foi.price), 2) AS average_item_price

FROM warehouse.fact_order_items foi
JOIN warehouse.dim_date dd
    ON foi.purchase_date_key = dd.date_key
GROUP BY
    dd.year,
    dd.month,
    dd.month_name,
    dd.quarter;


-- ============================================================
-- 3. Revenue by Product Category
-- Used for top category and category performance visuals.
-- ============================================================

CREATE VIEW reporting.vw_revenue_by_category AS
SELECT
    dp.product_category_name_english AS product_category,

    COUNT(DISTINCT foi.order_id) AS total_orders,
    COUNT(*) AS total_items,
    ROUND(SUM(foi.price), 2) AS total_revenue,
    ROUND(SUM(foi.freight_value), 2) AS total_freight,
    ROUND(SUM(foi.total_item_value), 2) AS total_item_value,
    ROUND(AVG(foi.price), 2) AS average_item_price,
    ROUND(AVG(foi.freight_value), 2) AS average_freight_value

FROM warehouse.fact_order_items foi
JOIN warehouse.dim_product dp
    ON foi.product_key = dp.product_key
GROUP BY
    dp.product_category_name_english;


-- ============================================================
-- 4. Customer Geography Summary
-- Used for maps and customer location analysis.
-- ============================================================

CREATE VIEW reporting.vw_customer_geography AS
SELECT
    dc.customer_state,
    dc.customer_city,

    COUNT(DISTINCT dc.customer_id) AS total_customers,
    COUNT(DISTINCT foi.order_id) AS total_orders,
    COUNT(*) AS total_items,
    ROUND(SUM(foi.price), 2) AS total_revenue,
    ROUND(SUM(foi.freight_value), 2) AS total_freight,
    ROUND(AVG(foi.delivery_days), 2) AS average_delivery_days,
    ROUND(
        AVG(
            CASE
                WHEN foi.is_late_delivery = TRUE THEN 1
                WHEN foi.is_late_delivery = FALSE THEN 0
                ELSE NULL
            END
        ) * 100,
        2
    ) AS late_delivery_rate_percent

FROM warehouse.fact_order_items foi
JOIN warehouse.dim_customer dc
    ON foi.customer_key = dc.customer_key
GROUP BY
    dc.customer_state,
    dc.customer_city;


-- ============================================================
-- 5. Seller Performance
-- Used for seller ranking and delay analysis.
-- ============================================================

CREATE VIEW reporting.vw_seller_performance AS
SELECT
    ds.seller_id,
    ds.seller_city,
    ds.seller_state,

    COUNT(DISTINCT foi.order_id) AS total_orders,
    COUNT(*) AS total_items,
    ROUND(SUM(foi.price), 2) AS total_revenue,
    ROUND(SUM(foi.freight_value), 2) AS total_freight,
    ROUND(AVG(foi.delivery_days), 2) AS average_delivery_days,
    COUNT(*) FILTER (WHERE foi.is_late_delivery = TRUE) AS late_items,
    ROUND(
        COUNT(*) FILTER (WHERE foi.is_late_delivery = TRUE)::NUMERIC
        / NULLIF(COUNT(*) FILTER (WHERE foi.is_late_delivery IS NOT NULL), 0)
        * 100,
        2
    ) AS late_delivery_rate_percent

FROM warehouse.fact_order_items foi
JOIN warehouse.dim_seller ds
    ON foi.seller_key = ds.seller_key
GROUP BY
    ds.seller_id,
    ds.seller_city,
    ds.seller_state;


-- ============================================================
-- 6. Delivery Performance
-- Used for logistics dashboard visuals.
-- ============================================================

CREATE VIEW reporting.vw_delivery_performance AS
SELECT
    dos.order_status,

    COUNT(*) AS total_items,
    COUNT(foi.delivery_days) AS items_with_delivery_date,
    COUNT(*) - COUNT(foi.delivery_days) AS items_without_delivery_date,
    ROUND(AVG(foi.delivery_days), 2) AS average_delivery_days,

    COUNT(*) FILTER (WHERE foi.is_late_delivery = TRUE) AS late_items,
    COUNT(*) FILTER (WHERE foi.is_late_delivery = FALSE) AS on_time_items,

    ROUND(
        COUNT(*) FILTER (WHERE foi.is_late_delivery = TRUE)::NUMERIC
        / NULLIF(COUNT(*) FILTER (WHERE foi.is_late_delivery IS NOT NULL), 0)
        * 100,
        2
    ) AS late_delivery_rate_percent

FROM warehouse.fact_order_items foi
JOIN warehouse.dim_order_status dos
    ON foi.order_status_key = dos.order_status_key
GROUP BY
    dos.order_status;


-- ============================================================
-- 7. Payment Summary
-- Used for payment method analysis.
-- ============================================================

CREATE VIEW reporting.vw_payment_summary AS
SELECT
    dpt.payment_type,

    COUNT(*) AS total_payments,
    ROUND(SUM(fp.payment_value), 2) AS total_payment_value,
    ROUND(AVG(fp.payment_value), 2) AS average_payment_value,
    ROUND(AVG(fp.payment_installments), 2) AS average_installments

FROM warehouse.fact_payments fp
JOIN warehouse.dim_payment_type dpt
    ON fp.payment_type_key = dpt.payment_type_key
GROUP BY
    dpt.payment_type;


-- ============================================================
-- 8. Review Summary
-- Used for customer satisfaction KPIs.
-- ============================================================

CREATE VIEW reporting.vw_review_summary AS
SELECT
    fr.review_score,

    COUNT(*) AS total_reviews,
    COUNT(*) FILTER (WHERE fr.review_score <= 2) AS low_review_count,
    ROUND(AVG(fr.review_answer_delay_days), 2) AS average_review_answer_delay_days,
    ROUND(
        AVG(
            CASE
                WHEN fr.has_review_comment = TRUE THEN 1
                ELSE 0
            END
        ) * 100,
        2
    ) AS review_comment_rate_percent

FROM warehouse.fact_reviews fr
GROUP BY
    fr.review_score;


-- ============================================================
-- 9. Review by Product Category
-- Used to compare satisfaction by category.
-- ============================================================

CREATE VIEW reporting.vw_review_by_category AS
SELECT
    dp.product_category_name_english AS product_category,

    COUNT(fr.review_key) AS total_reviews,
    ROUND(AVG(fr.review_score), 2) AS average_review_score,
    COUNT(*) FILTER (WHERE fr.review_score <= 2) AS low_review_count,
    ROUND(
        COUNT(*) FILTER (WHERE fr.review_score <= 2)::NUMERIC
        / NULLIF(COUNT(fr.review_key), 0)
        * 100,
        2
    ) AS low_review_rate_percent

FROM warehouse.fact_reviews fr
JOIN warehouse.fact_order_items foi
    ON fr.order_id = foi.order_id
JOIN warehouse.dim_product dp
    ON foi.product_key = dp.product_key
GROUP BY
    dp.product_category_name_english;


-- ============================================================
-- 10. Executive KPI Snapshot
-- Single-row overview for dashboard KPI cards.
-- ============================================================

CREATE VIEW reporting.vw_executive_kpi_snapshot AS
SELECT
    sales.total_orders,
    sales.total_items,
    sales.total_revenue,
    sales.total_freight,
    sales.total_item_value,
    sales.average_item_price,

    delivery.average_delivery_days,
    delivery.late_delivery_rate_percent,

    reviews.total_reviews,
    reviews.average_review_score,
    reviews.low_review_count,

    payments.total_payments,
    payments.total_payment_value,
    payments.average_payment_value

FROM (
    SELECT
        COUNT(DISTINCT order_id) AS total_orders,
        COUNT(*) AS total_items,
        ROUND(SUM(price), 2) AS total_revenue,
        ROUND(SUM(freight_value), 2) AS total_freight,
        ROUND(SUM(total_item_value), 2) AS total_item_value,
        ROUND(AVG(price), 2) AS average_item_price
    FROM warehouse.fact_order_items
) sales
CROSS JOIN (
    SELECT
        ROUND(AVG(delivery_days), 2) AS average_delivery_days,
        ROUND(
            AVG(
                CASE
                    WHEN is_late_delivery = TRUE THEN 1
                    WHEN is_late_delivery = FALSE THEN 0
                    ELSE NULL
                END
            ) * 100,
            2
        ) AS late_delivery_rate_percent
    FROM warehouse.fact_order_items
) delivery
CROSS JOIN (
    SELECT
        COUNT(*) AS total_reviews,
        ROUND(AVG(review_score), 2) AS average_review_score,
        COUNT(*) FILTER (WHERE review_score <= 2) AS low_review_count
    FROM warehouse.fact_reviews
) reviews
CROSS JOIN (
    SELECT
        COUNT(*) AS total_payments,
        ROUND(SUM(payment_value), 2) AS total_payment_value,
        ROUND(AVG(payment_value), 2) AS average_payment_value
    FROM warehouse.fact_payments
) payments;