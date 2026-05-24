from __future__ import annotations

import logging

from sqlalchemy.engine import Engine

from .db import execute_many

logger = logging.getLogger(__name__)

STAGING_TABLES = [
    "staging.stg_reviews",
    "staging.stg_payments",
    "staging.stg_order_items",
    "staging.stg_orders",
    "staging.stg_products",
    "staging.stg_product_categories",
    "staging.stg_geolocation",
    "staging.stg_sellers",
    "staging.stg_customers",
    "staging.stg_closed_deals",
    "staging.stg_marketing_leads",
]

TRUNCATE_STAGING_SQL = [
    f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE" for table in STAGING_TABLES
]

STAGING_SQL = [
    """
    INSERT INTO staging.stg_customers (
        customer_id, customer_unique_id, zip_prefix, city_name, state_code
    )
    SELECT
        customer_id,
        customer_unique_id,
        LPAD(TRIM(customer_zip_code_prefix), 5, '0') AS zip_prefix,
        LOWER(TRIM(customer_city)) AS city_name,
        UPPER(TRIM(customer_state)) AS state_code
    FROM raw.olist_customers
    """,
    """
    INSERT INTO staging.stg_sellers (
        seller_id, zip_prefix, city_name, state_code
    )
    SELECT
        seller_id,
        LPAD(TRIM(seller_zip_code_prefix), 5, '0') AS zip_prefix,
        LOWER(TRIM(seller_city)) AS city_name,
        UPPER(TRIM(seller_state)) AS state_code
    FROM raw.olist_sellers
    """,
    """
    INSERT INTO staging.stg_geolocation (
        zip_prefix, latitude, longitude, city_name, state_code
    )
    WITH cleaned AS (
        SELECT
            LPAD(TRIM(geolocation_zip_code_prefix), 5, '0') AS zip_prefix,
            geolocation_lat AS latitude,
            geolocation_lng AS longitude,
            LOWER(TRIM(geolocation_city)) AS city_name,
            UPPER(TRIM(geolocation_state)) AS state_code
        FROM raw.olist_geolocation
        WHERE geolocation_zip_code_prefix IS NOT NULL
    ),
    geo_avg AS (
        SELECT
            zip_prefix,
            AVG(latitude) AS latitude,
            AVG(longitude) AS longitude
        FROM cleaned
        GROUP BY zip_prefix
    ),
    city_rank AS (
        SELECT
            zip_prefix,
            city_name,
            state_code,
            ROW_NUMBER() OVER (
                PARTITION BY zip_prefix
                ORDER BY COUNT(*) DESC, city_name, state_code
            ) AS rn
        FROM cleaned
        GROUP BY zip_prefix, city_name, state_code
    )
    SELECT
        a.zip_prefix,
        a.latitude,
        a.longitude,
        r.city_name,
        r.state_code
    FROM geo_avg a
    LEFT JOIN city_rank r
        ON a.zip_prefix = r.zip_prefix
       AND r.rn = 1
    """,
    """
    INSERT INTO staging.stg_product_categories (
        product_category_name, product_category_name_english
    )
    WITH source_categories AS (
        SELECT DISTINCT COALESCE(NULLIF(TRIM(product_category_name), ''), 'unknown') AS product_category_name
        FROM raw.olist_products
        UNION
        SELECT DISTINCT COALESCE(NULLIF(TRIM(product_category_name), ''), 'unknown') AS product_category_name
        FROM raw.product_category_name_translation
    )
    SELECT
        sc.product_category_name,
        COALESCE(t.product_category_name_english, sc.product_category_name) AS product_category_name_english
    FROM source_categories sc
    LEFT JOIN raw.product_category_name_translation t
        ON sc.product_category_name = t.product_category_name
    """,
    """
    INSERT INTO staging.stg_products (
        product_id,
        product_category_name,
        product_name_length,
        product_description_length,
        product_photos_qty,
        product_weight_g,
        product_length_cm,
        product_height_cm,
        product_width_cm
    )
    SELECT
        product_id,
        COALESCE(NULLIF(TRIM(product_category_name), ''), 'unknown') AS product_category_name,
        product_name_lenght AS product_name_length,
        product_description_lenght AS product_description_length,
        product_photos_qty,
        product_weight_g,
        product_length_cm,
        product_height_cm,
        product_width_cm
    FROM raw.olist_products
    """,
    """
    INSERT INTO staging.stg_orders (
        order_id,
        customer_id,
        order_status,
        order_purchase_ts,
        order_approved_ts,
        order_delivered_carrier_ts,
        order_delivered_customer_ts,
        order_estimated_delivery_ts
    )
    SELECT
        order_id,
        customer_id,
        LOWER(TRIM(order_status)) AS order_status,
        order_purchase_timestamp,
        order_approved_at,
        order_delivered_carrier_date,
        order_delivered_customer_date,
        order_estimated_delivery_date
    FROM raw.olist_orders
    """,
    """
    INSERT INTO staging.stg_order_items (
        order_id,
        order_item_id,
        product_id,
        seller_id,
        shipping_limit_ts,
        price,
        freight_value
    )
    SELECT
        order_id,
        order_item_id,
        product_id,
        seller_id,
        shipping_limit_date,
        price,
        freight_value
    FROM raw.olist_order_items
    """,
    """
    INSERT INTO staging.stg_payments (
        order_id,
        payment_sequential,
        payment_type,
        payment_installments,
        payment_value
    )
    SELECT
        order_id,
        payment_sequential,
        LOWER(TRIM(payment_type)) AS payment_type,
        payment_installments,
        payment_value
    FROM raw.olist_order_payments
    """,
    """
    INSERT INTO staging.stg_reviews (
        review_id,
        order_id,
        review_score,
        review_comment_title,
        review_comment_message,
        review_creation_ts,
        review_answer_ts
    )
    SELECT
        review_id,
        order_id,
        review_score,
        review_comment_title,
        review_comment_message,
        review_creation_date,
        review_answer_timestamp
    FROM raw.olist_order_reviews
    """,
    """
    INSERT INTO staging.stg_marketing_leads (
        mql_id,
        first_contact_date,
        landing_page_id,
        origin
    )
    SELECT
        mql_id,
        first_contact_date,
        COALESCE(NULLIF(TRIM(landing_page_id), ''), 'unknown') AS landing_page_id,
        COALESCE(NULLIF(LOWER(TRIM(origin)), ''), 'unknown') AS origin
    FROM raw.olist_marketing_qualified_leads
    """,
    """
    INSERT INTO staging.stg_closed_deals (
        mql_id,
        seller_id,
        sdr_id,
        sr_id,
        won_ts,
        business_segment,
        lead_type,
        lead_behaviour_profile,
        has_company,
        has_gtin,
        average_stock,
        business_type,
        declared_product_catalog_size,
        declared_monthly_revenue
    )
    SELECT
        mql_id,
        NULLIF(TRIM(seller_id), '') AS seller_id,
        NULLIF(TRIM(sdr_id), '') AS sdr_id,
        NULLIF(TRIM(sr_id), '') AS sr_id,
        won_date,
        COALESCE(NULLIF(LOWER(TRIM(business_segment)), ''), 'unknown') AS business_segment,
        COALESCE(NULLIF(LOWER(TRIM(lead_type)), ''), 'unknown') AS lead_type,
        COALESCE(NULLIF(LOWER(TRIM(lead_behaviour_profile)), ''), 'unknown') AS lead_behaviour_profile,
        CASE
            WHEN LOWER(TRIM(has_company)) IN ('true', '1', 'yes', 'y', 'sim') THEN TRUE
            WHEN LOWER(TRIM(has_company)) IN ('false', '0', 'no', 'n', 'nao', 'não') THEN FALSE
            ELSE NULL
        END AS has_company,
        CASE
            WHEN LOWER(TRIM(has_gtin)) IN ('true', '1', 'yes', 'y', 'sim') THEN TRUE
            WHEN LOWER(TRIM(has_gtin)) IN ('false', '0', 'no', 'n', 'nao', 'não') THEN FALSE
            ELSE NULL
        END AS has_gtin,
        NULLIF(LOWER(TRIM(average_stock)), '') AS average_stock,
        COALESCE(NULLIF(LOWER(TRIM(business_type)), ''), 'unknown') AS business_type,
        declared_product_catalog_size,
        declared_monthly_revenue
    FROM raw.olist_closed_deals
    """,
]


def build_staging(engine: Engine) -> None:
    logger.info("Building staging layer")
    execute_many(engine, TRUNCATE_STAGING_SQL + STAGING_SQL)
