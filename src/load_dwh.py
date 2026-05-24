from __future__ import annotations

import logging

from sqlalchemy.engine import Engine

from .db import execute_many

logger = logging.getLogger(__name__)

TRUNCATE_DWH_SQL = [
    """
    TRUNCATE TABLE
        dwh.fact_reviews,
        dwh.fact_payments,
        dwh.fact_order_items,
        dwh.fact_orders,
        dwh.fact_closed_deals,
        dwh.fact_marketing_leads,
        dwh.dim_sales_rep,
        dwh.dim_lead_profile,
        dwh.dim_lead_type,
        dwh.dim_business_segment,
        dwh.dim_landing_page,
        dwh.dim_marketing_origin,
        dwh.dim_payment_type,
        dwh.dim_order_status,
        dwh.dim_product,
        dwh.dim_product_category,
        dwh.dim_seller,
        dwh.dim_customer,
        dwh.dim_zip_prefix,
        dwh.dim_city,
        dwh.dim_state,
        dwh.dim_date
    RESTART IDENTITY CASCADE
    """
]

DWH_SQL = [
    # Date dimension
    """
    INSERT INTO dwh.dim_date (
        date_key, full_date, day_of_month, day_of_week, day_name,
        week_of_year, month_number, month_name, quarter_number, year_number, is_weekend
    )
    WITH all_dates AS (
        SELECT first_contact_date::date AS dt FROM staging.stg_marketing_leads
        UNION SELECT won_ts::date FROM staging.stg_closed_deals
        UNION SELECT order_purchase_ts::date FROM staging.stg_orders
        UNION SELECT order_approved_ts::date FROM staging.stg_orders
        UNION SELECT order_delivered_carrier_ts::date FROM staging.stg_orders
        UNION SELECT order_delivered_customer_ts::date FROM staging.stg_orders
        UNION SELECT order_estimated_delivery_ts::date FROM staging.stg_orders
        UNION SELECT shipping_limit_ts::date FROM staging.stg_order_items
        UNION SELECT review_creation_ts::date FROM staging.stg_reviews
        UNION SELECT review_answer_ts::date FROM staging.stg_reviews
    ), bounds AS (
        SELECT MIN(dt) AS min_dt, MAX(dt) AS max_dt
        FROM all_dates
        WHERE dt IS NOT NULL
    )
    SELECT
        TO_CHAR(d::date, 'YYYYMMDD')::integer AS date_key,
        d::date AS full_date,
        EXTRACT(DAY FROM d)::smallint AS day_of_month,
        EXTRACT(ISODOW FROM d)::smallint AS day_of_week,
        TRIM(TO_CHAR(d, 'Day')) AS day_name,
        EXTRACT(WEEK FROM d)::smallint AS week_of_year,
        EXTRACT(MONTH FROM d)::smallint AS month_number,
        TRIM(TO_CHAR(d, 'Month')) AS month_name,
        EXTRACT(QUARTER FROM d)::smallint AS quarter_number,
        EXTRACT(YEAR FROM d)::integer AS year_number,
        EXTRACT(ISODOW FROM d) IN (6, 7) AS is_weekend
    FROM bounds b,
         GENERATE_SERIES(b.min_dt, b.max_dt, interval '1 day') AS d
    """,
    # State dimension
    """
    INSERT INTO dwh.dim_state (state_code, state_name)
    WITH states AS (
        SELECT state_code FROM staging.stg_geolocation
        UNION SELECT state_code FROM staging.stg_customers
        UNION SELECT state_code FROM staging.stg_sellers
    )
    SELECT DISTINCT
        state_code,
        CASE state_code
            WHEN 'AC' THEN 'Acre'
            WHEN 'AL' THEN 'Alagoas'
            WHEN 'AP' THEN 'Amapá'
            WHEN 'AM' THEN 'Amazonas'
            WHEN 'BA' THEN 'Bahia'
            WHEN 'CE' THEN 'Ceará'
            WHEN 'DF' THEN 'Distrito Federal'
            WHEN 'ES' THEN 'Espírito Santo'
            WHEN 'GO' THEN 'Goiás'
            WHEN 'MA' THEN 'Maranhão'
            WHEN 'MT' THEN 'Mato Grosso'
            WHEN 'MS' THEN 'Mato Grosso do Sul'
            WHEN 'MG' THEN 'Minas Gerais'
            WHEN 'PA' THEN 'Pará'
            WHEN 'PB' THEN 'Paraíba'
            WHEN 'PR' THEN 'Paraná'
            WHEN 'PE' THEN 'Pernambuco'
            WHEN 'PI' THEN 'Piauí'
            WHEN 'RJ' THEN 'Rio de Janeiro'
            WHEN 'RN' THEN 'Rio Grande do Norte'
            WHEN 'RS' THEN 'Rio Grande do Sul'
            WHEN 'RO' THEN 'Rondônia'
            WHEN 'RR' THEN 'Roraima'
            WHEN 'SC' THEN 'Santa Catarina'
            WHEN 'SP' THEN 'São Paulo'
            WHEN 'SE' THEN 'Sergipe'
            WHEN 'TO' THEN 'Tocantins'
            ELSE NULL
        END AS state_name
    FROM states
    WHERE state_code IS NOT NULL AND state_code <> ''
    """,
    # City dimension
    """
    INSERT INTO dwh.dim_city (city_name, state_key)
    WITH cities AS (
        SELECT city_name, state_code FROM staging.stg_geolocation
        UNION SELECT city_name, state_code FROM staging.stg_customers
        UNION SELECT city_name, state_code FROM staging.stg_sellers
    )
    SELECT DISTINCT
        c.city_name,
        s.state_key
    FROM cities c
    JOIN dwh.dim_state s ON c.state_code = s.state_code
    WHERE c.city_name IS NOT NULL AND c.city_name <> ''
    """,
    # ZIP prefix dimension
    """
    INSERT INTO dwh.dim_zip_prefix (zip_prefix, city_key, state_key, latitude, longitude)
    WITH all_zips AS (
        SELECT zip_prefix, city_name, state_code, latitude, longitude, 1 AS priority
        FROM staging.stg_geolocation
        UNION ALL
        SELECT zip_prefix, city_name, state_code, NULL::numeric AS latitude, NULL::numeric AS longitude, 2 AS priority
        FROM staging.stg_customers
        UNION ALL
        SELECT zip_prefix, city_name, state_code, NULL::numeric AS latitude, NULL::numeric AS longitude, 3 AS priority
        FROM staging.stg_sellers
    ), ranked AS (
        SELECT
            zip_prefix,
            city_name,
            state_code,
            latitude,
            longitude,
            ROW_NUMBER() OVER (
                PARTITION BY zip_prefix
                ORDER BY priority, city_name NULLS LAST, state_code NULLS LAST
            ) AS rn
        FROM all_zips
        WHERE zip_prefix IS NOT NULL AND zip_prefix <> ''
    )
    SELECT
        r.zip_prefix,
        c.city_key,
        s.state_key,
        r.latitude,
        r.longitude
    FROM ranked r
    LEFT JOIN dwh.dim_state s ON r.state_code = s.state_code
    LEFT JOIN dwh.dim_city c ON r.city_name = c.city_name AND c.state_key = s.state_key
    WHERE r.rn = 1
    """,
    # Customer dimension
    """
    INSERT INTO dwh.dim_customer (customer_id, customer_unique_id, zip_prefix_key, city_key, state_key)
    SELECT
        c.customer_id,
        c.customer_unique_id,
        z.zip_prefix_key,
        city.city_key,
        state.state_key
    FROM staging.stg_customers c
    LEFT JOIN dwh.dim_zip_prefix z ON c.zip_prefix = z.zip_prefix
    LEFT JOIN dwh.dim_state state ON c.state_code = state.state_code
    LEFT JOIN dwh.dim_city city ON c.city_name = city.city_name AND city.state_key = state.state_key
    """,
    # Seller dimension
    """
    INSERT INTO dwh.dim_seller (seller_id, zip_prefix_key, city_key, state_key)
    SELECT
        s.seller_id,
        z.zip_prefix_key,
        city.city_key,
        state.state_key
    FROM staging.stg_sellers s
    LEFT JOIN dwh.dim_zip_prefix z ON s.zip_prefix = z.zip_prefix
    LEFT JOIN dwh.dim_state state ON s.state_code = state.state_code
    LEFT JOIN dwh.dim_city city ON s.city_name = city.city_name AND city.state_key = state.state_key
    """,
    # Product dimensions
    """
    INSERT INTO dwh.dim_product_category (product_category_name, product_category_name_english)
    SELECT product_category_name, product_category_name_english
    FROM staging.stg_product_categories
    """,
    """
    INSERT INTO dwh.dim_product (
        product_id, product_category_key, product_name_length, product_description_length,
        product_photos_qty, product_weight_g, product_length_cm, product_height_cm, product_width_cm
    )
    SELECT
        p.product_id,
        pc.product_category_key,
        p.product_name_length,
        p.product_description_length,
        p.product_photos_qty,
        p.product_weight_g,
        p.product_length_cm,
        p.product_height_cm,
        p.product_width_cm
    FROM staging.stg_products p
    LEFT JOIN dwh.dim_product_category pc ON p.product_category_name = pc.product_category_name
    """,
    # Small dimensions
    """
    INSERT INTO dwh.dim_order_status (order_status)
    SELECT DISTINCT COALESCE(NULLIF(order_status, ''), 'unknown')
    FROM staging.stg_orders
    """,
    """
    INSERT INTO dwh.dim_payment_type (payment_type)
    SELECT DISTINCT COALESCE(NULLIF(payment_type, ''), 'unknown')
    FROM staging.stg_payments
    """,
    """
    INSERT INTO dwh.dim_marketing_origin (origin_name)
    SELECT DISTINCT COALESCE(NULLIF(origin, ''), 'unknown')
    FROM staging.stg_marketing_leads
    """,
    """
    INSERT INTO dwh.dim_landing_page (landing_page_id)
    SELECT DISTINCT COALESCE(NULLIF(landing_page_id, ''), 'unknown')
    FROM staging.stg_marketing_leads
    """,
    """
    INSERT INTO dwh.dim_business_segment (business_segment)
    SELECT DISTINCT COALESCE(NULLIF(business_segment, ''), 'unknown')
    FROM staging.stg_closed_deals
    """,
    """
    INSERT INTO dwh.dim_lead_type (lead_type)
    SELECT DISTINCT COALESCE(NULLIF(lead_type, ''), 'unknown')
    FROM staging.stg_closed_deals
    """,
    """
    INSERT INTO dwh.dim_lead_profile (lead_behaviour_profile)
    SELECT DISTINCT COALESCE(NULLIF(lead_behaviour_profile, ''), 'unknown')
    FROM staging.stg_closed_deals
    """,
    """
    INSERT INTO dwh.dim_sales_rep (sales_rep_id, sales_role)
    SELECT DISTINCT sdr_id, 'SDR'
    FROM staging.stg_closed_deals
    WHERE sdr_id IS NOT NULL AND sdr_id <> ''
    UNION
    SELECT DISTINCT sr_id, 'SR'
    FROM staging.stg_closed_deals
    WHERE sr_id IS NOT NULL AND sr_id <> ''
    """,
    # Facts
    """
    INSERT INTO dwh.fact_marketing_leads (
        mql_id, first_contact_date_key, landing_page_key, marketing_origin_key, lead_count
    )
    SELECT
        ml.mql_id,
        TO_CHAR(ml.first_contact_date, 'YYYYMMDD')::integer AS first_contact_date_key,
        lp.landing_page_key,
        mo.marketing_origin_key,
        1 AS lead_count
    FROM staging.stg_marketing_leads ml
    LEFT JOIN dwh.dim_landing_page lp ON ml.landing_page_id = lp.landing_page_id
    LEFT JOIN dwh.dim_marketing_origin mo ON ml.origin = mo.origin_name
    """,
    """
    INSERT INTO dwh.fact_closed_deals (
        mql_id, seller_key, won_date_key, sdr_sales_rep_key, sr_sales_rep_key,
        business_segment_key, lead_type_key, lead_profile_key,
        has_company, has_gtin, average_stock, business_type,
        declared_product_catalog_size, declared_monthly_revenue,
        is_active_seller, deal_count
    )
    SELECT
        cd.mql_id,
        ds.seller_key,
        TO_CHAR(cd.won_ts::date, 'YYYYMMDD')::integer AS won_date_key,
        sdr.sales_rep_key AS sdr_sales_rep_key,
        sr.sales_rep_key AS sr_sales_rep_key,
        bs.business_segment_key,
        lt.lead_type_key,
        lp.lead_profile_key,
        cd.has_company,
        cd.has_gtin,
        cd.average_stock,
        cd.business_type,
        cd.declared_product_catalog_size,
        cd.declared_monthly_revenue,
        ds.seller_key IS NOT NULL AS is_active_seller,
        1 AS deal_count
    FROM staging.stg_closed_deals cd
    LEFT JOIN dwh.dim_seller ds ON cd.seller_id = ds.seller_id
    LEFT JOIN dwh.dim_sales_rep sdr ON cd.sdr_id = sdr.sales_rep_id AND sdr.sales_role = 'SDR'
    LEFT JOIN dwh.dim_sales_rep sr ON cd.sr_id = sr.sales_rep_id AND sr.sales_role = 'SR'
    LEFT JOIN dwh.dim_business_segment bs ON cd.business_segment = bs.business_segment
    LEFT JOIN dwh.dim_lead_type lt ON cd.lead_type = lt.lead_type
    LEFT JOIN dwh.dim_lead_profile lp ON cd.lead_behaviour_profile = lp.lead_behaviour_profile
    """,
    """
    INSERT INTO dwh.fact_orders (
        order_id, customer_key, order_status_key,
        purchase_date_key, approved_date_key, delivered_carrier_date_key,
        delivered_customer_date_key, estimated_delivery_date_key,
        order_purchase_ts, order_approved_ts, order_delivered_carrier_ts,
        order_delivered_customer_ts, order_estimated_delivery_ts,
        approval_delay_hours, days_to_carrier, days_to_customer,
        estimated_delivery_days, delivery_delay_days,
        is_delivered_on_time, is_delivered, order_count
    )
    SELECT
        o.order_id,
        dc.customer_key,
        os.order_status_key,
        TO_CHAR(o.order_purchase_ts::date, 'YYYYMMDD')::integer AS purchase_date_key,
        TO_CHAR(o.order_approved_ts::date, 'YYYYMMDD')::integer AS approved_date_key,
        TO_CHAR(o.order_delivered_carrier_ts::date, 'YYYYMMDD')::integer AS delivered_carrier_date_key,
        TO_CHAR(o.order_delivered_customer_ts::date, 'YYYYMMDD')::integer AS delivered_customer_date_key,
        TO_CHAR(o.order_estimated_delivery_ts::date, 'YYYYMMDD')::integer AS estimated_delivery_date_key,
        o.order_purchase_ts,
        o.order_approved_ts,
        o.order_delivered_carrier_ts,
        o.order_delivered_customer_ts,
        o.order_estimated_delivery_ts,
        ROUND((EXTRACT(EPOCH FROM (o.order_approved_ts - o.order_purchase_ts)) / 3600.0)::numeric, 2) AS approval_delay_hours,
        ROUND((EXTRACT(EPOCH FROM (o.order_delivered_carrier_ts - o.order_purchase_ts)) / 86400.0)::numeric, 2) AS days_to_carrier,
        ROUND((EXTRACT(EPOCH FROM (o.order_delivered_customer_ts - o.order_purchase_ts)) / 86400.0)::numeric, 2) AS days_to_customer,
        ROUND((EXTRACT(EPOCH FROM (o.order_estimated_delivery_ts - o.order_purchase_ts)) / 86400.0)::numeric, 2) AS estimated_delivery_days,
        ROUND((EXTRACT(EPOCH FROM (o.order_delivered_customer_ts - o.order_estimated_delivery_ts)) / 86400.0)::numeric, 2) AS delivery_delay_days,
        CASE
            WHEN o.order_delivered_customer_ts IS NULL OR o.order_estimated_delivery_ts IS NULL THEN NULL
            ELSE o.order_delivered_customer_ts <= o.order_estimated_delivery_ts
        END AS is_delivered_on_time,
        o.order_delivered_customer_ts IS NOT NULL AS is_delivered,
        1 AS order_count
    FROM staging.stg_orders o
    LEFT JOIN dwh.dim_customer dc ON o.customer_id = dc.customer_id
    LEFT JOIN dwh.dim_order_status os ON COALESCE(o.order_status, 'unknown') = os.order_status
    """,
    """
    INSERT INTO dwh.fact_order_items (
        order_id, order_item_id, order_key, product_key, seller_key,
        shipping_limit_date_key, shipping_limit_ts,
        item_price, freight_value, total_item_value, item_count
    )
    SELECT
        oi.order_id,
        oi.order_item_id,
        fo.order_key,
        dp.product_key,
        ds.seller_key,
        TO_CHAR(oi.shipping_limit_ts::date, 'YYYYMMDD')::integer AS shipping_limit_date_key,
        oi.shipping_limit_ts,
        oi.price,
        oi.freight_value,
        COALESCE(oi.price, 0) + COALESCE(oi.freight_value, 0) AS total_item_value,
        1 AS item_count
    FROM staging.stg_order_items oi
    LEFT JOIN dwh.fact_orders fo ON oi.order_id = fo.order_id
    LEFT JOIN dwh.dim_product dp ON oi.product_id = dp.product_id
    LEFT JOIN dwh.dim_seller ds ON oi.seller_id = ds.seller_id
    """,
    """
    INSERT INTO dwh.fact_payments (
        order_id, payment_sequential, order_key, payment_type_key,
        payment_installments, payment_value, payment_count
    )
    SELECT
        p.order_id,
        p.payment_sequential,
        fo.order_key,
        pt.payment_type_key,
        p.payment_installments,
        p.payment_value,
        1 AS payment_count
    FROM staging.stg_payments p
    LEFT JOIN dwh.fact_orders fo ON p.order_id = fo.order_id
    LEFT JOIN dwh.dim_payment_type pt ON COALESCE(p.payment_type, 'unknown') = pt.payment_type
    """,
    """
    INSERT INTO dwh.fact_reviews (
        review_id, order_id, order_key,
        review_creation_date_key, review_answer_date_key,
        review_score, review_comment_title, review_comment_message,
        review_creation_ts, review_answer_ts, review_response_time_hours,
        has_review_title, has_review_message,
        is_positive_review, is_neutral_review, is_negative_review, review_count
    )
    SELECT
        r.review_id,
        r.order_id,
        fo.order_key,
        TO_CHAR(r.review_creation_ts::date, 'YYYYMMDD')::integer AS review_creation_date_key,
        TO_CHAR(r.review_answer_ts::date, 'YYYYMMDD')::integer AS review_answer_date_key,
        r.review_score,
        r.review_comment_title,
        r.review_comment_message,
        r.review_creation_ts,
        r.review_answer_ts,
        ROUND((EXTRACT(EPOCH FROM (r.review_answer_ts - r.review_creation_ts)) / 3600.0)::numeric, 2) AS review_response_time_hours,
        NULLIF(TRIM(COALESCE(r.review_comment_title, '')), '') IS NOT NULL AS has_review_title,
        NULLIF(TRIM(COALESCE(r.review_comment_message, '')), '') IS NOT NULL AS has_review_message,
        r.review_score >= 4 AS is_positive_review,
        r.review_score = 3 AS is_neutral_review,
        r.review_score <= 2 AS is_negative_review,
        1 AS review_count
    FROM staging.stg_reviews r
    LEFT JOIN dwh.fact_orders fo ON r.order_id = fo.order_id
    """,
]


def load_dwh(engine: Engine) -> None:
    logger.info("Loading DWH dimensions and facts")
    execute_many(engine, TRUNCATE_DWH_SQL + DWH_SQL)
