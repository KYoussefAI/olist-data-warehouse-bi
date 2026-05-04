-- ============================================================
-- Load Warehouse Tables — Olist Data Warehouse & BI
-- Purpose:
-- Transform staging tables into warehouse dimensions and facts.
-- ============================================================

-- ============================================================
-- 1. Load Dimensions
-- ============================================================

INSERT INTO warehouse.dim_customer (
    customer_id,
    customer_unique_id,
    customer_zip_code_prefix,
    customer_city,
    customer_state
)
SELECT
    customer_id,
    customer_unique_id,
    customer_zip_code_prefix,
    LOWER(TRIM(customer_city)) AS customer_city,
    customer_state
FROM staging.customers;


INSERT INTO warehouse.dim_product (
    product_id,
    product_category_name,
    product_category_name_english,
    product_name_length,
    product_description_length,
    product_photos_qty,
    product_weight_g,
    product_length_cm,
    product_height_cm,
    product_width_cm
)
SELECT
    p.product_id,
    COALESCE(p.product_category_name, 'unknown') AS product_category_name,
    COALESCE(t.product_category_name_english, 'unknown') AS product_category_name_english,
    p.product_name_lenght AS product_name_length,
    p.product_description_lenght AS product_description_length,
    p.product_photos_qty,
    p.product_weight_g,
    p.product_length_cm,
    p.product_height_cm,
    p.product_width_cm
FROM staging.products p
LEFT JOIN staging.product_category_translation t
    ON p.product_category_name = t.product_category_name;


INSERT INTO warehouse.dim_seller (
    seller_id,
    seller_zip_code_prefix,
    seller_city,
    seller_state
)
SELECT
    seller_id,
    seller_zip_code_prefix,
    LOWER(TRIM(seller_city)) AS seller_city,
    seller_state
FROM staging.sellers;


INSERT INTO warehouse.dim_order_status (
    order_status
)
SELECT DISTINCT
    order_status
FROM staging.orders
WHERE order_status IS NOT NULL;


INSERT INTO warehouse.dim_payment_type (
    payment_type
)
SELECT DISTINCT
    payment_type
FROM staging.order_payments
WHERE payment_type IS NOT NULL;


INSERT INTO warehouse.dim_location (
    zip_code_prefix,
    city,
    state,
    latitude,
    longitude
)
SELECT
    geolocation_zip_code_prefix AS zip_code_prefix,
    MIN(LOWER(TRIM(geolocation_city))) AS city,
    MIN(geolocation_state) AS state,
    AVG(geolocation_lat) AS latitude,
    AVG(geolocation_lng) AS longitude
FROM staging.geolocation
GROUP BY geolocation_zip_code_prefix;


INSERT INTO warehouse.dim_date (
    date_key,
    full_date,
    day,
    month,
    month_name,
    quarter,
    year,
    day_of_week,
    day_name,
    is_weekend
)
SELECT DISTINCT
    TO_CHAR(date_value, 'YYYYMMDD')::INTEGER AS date_key,
    date_value AS full_date,
    EXTRACT(DAY FROM date_value)::INTEGER AS day,
    EXTRACT(MONTH FROM date_value)::INTEGER AS month,
    TO_CHAR(date_value, 'Month') AS month_name,
    EXTRACT(QUARTER FROM date_value)::INTEGER AS quarter,
    EXTRACT(YEAR FROM date_value)::INTEGER AS year,
    EXTRACT(ISODOW FROM date_value)::INTEGER AS day_of_week,
    TO_CHAR(date_value, 'Day') AS day_name,
    CASE
        WHEN EXTRACT(ISODOW FROM date_value) IN (6, 7) THEN TRUE
        ELSE FALSE
    END AS is_weekend
FROM (
    SELECT order_purchase_timestamp::DATE AS date_value
    FROM staging.orders
    WHERE order_purchase_timestamp IS NOT NULL

    UNION

    SELECT order_approved_at::DATE
    FROM staging.orders
    WHERE order_approved_at IS NOT NULL

    UNION

    SELECT order_delivered_carrier_date::DATE
    FROM staging.orders
    WHERE order_delivered_carrier_date IS NOT NULL

    UNION

    SELECT order_delivered_customer_date::DATE
    FROM staging.orders
    WHERE order_delivered_customer_date IS NOT NULL

    UNION

    SELECT order_estimated_delivery_date::DATE
    FROM staging.orders
    WHERE order_estimated_delivery_date IS NOT NULL

    UNION

    SELECT shipping_limit_date::DATE
    FROM staging.order_items
    WHERE shipping_limit_date IS NOT NULL

    UNION

    SELECT review_creation_date::DATE
    FROM staging.order_reviews
    WHERE review_creation_date IS NOT NULL

    UNION

    SELECT review_answer_timestamp::DATE
    FROM staging.order_reviews
    WHERE review_answer_timestamp IS NOT NULL
) all_dates
WHERE date_value IS NOT NULL;


-- ============================================================
-- 2. Load Facts
-- ============================================================

INSERT INTO warehouse.fact_order_items (
    order_id,
    order_item_id,
    customer_key,
    product_key,
    seller_key,
    purchase_date_key,
    order_status_key,
    customer_location_key,
    seller_location_key,
    price,
    freight_value,
    total_item_value,
    delivery_days,
    is_late_delivery
)
SELECT
    oi.order_id,
    oi.order_item_id,

    dc.customer_key,
    dp.product_key,
    ds.seller_key,
    dd.date_key,
    dos.order_status_key,

    dcl.location_key AS customer_location_key,
    dsl.location_key AS seller_location_key,

    oi.price,
    oi.freight_value,
    oi.price + oi.freight_value AS total_item_value,

    CASE
        WHEN o.order_delivered_customer_date IS NOT NULL
        THEN EXTRACT(EPOCH FROM (o.order_delivered_customer_date - o.order_purchase_timestamp)) / 86400
        ELSE NULL
    END AS delivery_days,

    CASE
        WHEN o.order_delivered_customer_date IS NOT NULL
             AND o.order_delivered_customer_date > o.order_estimated_delivery_date
        THEN TRUE
        WHEN o.order_delivered_customer_date IS NOT NULL
        THEN FALSE
        ELSE NULL
    END AS is_late_delivery

FROM staging.order_items oi
JOIN staging.orders o
    ON oi.order_id = o.order_id
JOIN staging.customers c
    ON o.customer_id = c.customer_id
JOIN warehouse.dim_customer dc
    ON c.customer_id = dc.customer_id
JOIN warehouse.dim_product dp
    ON oi.product_id = dp.product_id
JOIN warehouse.dim_seller ds
    ON oi.seller_id = ds.seller_id
JOIN warehouse.dim_date dd
    ON o.order_purchase_timestamp::DATE = dd.full_date
JOIN warehouse.dim_order_status dos
    ON o.order_status = dos.order_status
LEFT JOIN warehouse.dim_location dcl
    ON c.customer_zip_code_prefix = dcl.zip_code_prefix
LEFT JOIN warehouse.dim_location dsl
    ON ds.seller_zip_code_prefix = dsl.zip_code_prefix;


INSERT INTO warehouse.fact_payments (
    order_id,
    payment_sequential,
    payment_type_key,
    payment_installments,
    payment_value
)
SELECT
    op.order_id,
    op.payment_sequential,
    dpt.payment_type_key,
    op.payment_installments,
    op.payment_value
FROM staging.order_payments op
JOIN warehouse.dim_payment_type dpt
    ON op.payment_type = dpt.payment_type;


INSERT INTO warehouse.fact_reviews (
    review_id,
    order_id,
    review_date_key,
    review_score,
    has_review_comment,
    review_answer_delay_days
)
SELECT
    r.review_id,
    r.order_id,
    dd.date_key AS review_date_key,
    r.review_score,

    CASE
        WHEN r.review_comment_message IS NOT NULL
             AND TRIM(r.review_comment_message) <> ''
        THEN TRUE
        ELSE FALSE
    END AS has_review_comment,

    EXTRACT(EPOCH FROM (r.review_answer_timestamp - r.review_creation_date)) / 86400
        AS review_answer_delay_days

FROM staging.order_reviews r
JOIN warehouse.dim_date dd
    ON r.review_creation_date::DATE = dd.full_date;