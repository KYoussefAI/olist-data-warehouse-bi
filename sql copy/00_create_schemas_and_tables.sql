-- Olist PostgreSQL DDL - final project version
-- Layers: raw -> staging -> dwh -> marts

BEGIN;

CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS dwh;
CREATE SCHEMA IF NOT EXISTS marts;

-- ---------------------------------------------------------------------------
-- RAW LANDING TABLES: mirror source CSV files
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS raw.olist_customers (
    customer_id TEXT PRIMARY KEY,
    customer_unique_id TEXT,
    customer_zip_code_prefix TEXT,
    customer_city TEXT,
    customer_state TEXT
);

CREATE TABLE IF NOT EXISTS raw.olist_geolocation (
    geolocation_zip_code_prefix TEXT,
    geolocation_lat NUMERIC(10, 7),
    geolocation_lng NUMERIC(10, 7),
    geolocation_city TEXT,
    geolocation_state TEXT
);

CREATE TABLE IF NOT EXISTS raw.olist_marketing_qualified_leads (
    mql_id TEXT PRIMARY KEY,
    first_contact_date DATE,
    landing_page_id TEXT,
    origin TEXT
);

CREATE TABLE IF NOT EXISTS raw.olist_closed_deals (
    mql_id TEXT PRIMARY KEY,
    seller_id TEXT,
    sdr_id TEXT,
    sr_id TEXT,
    won_date TIMESTAMP,
    business_segment TEXT,
    lead_type TEXT,
    lead_behaviour_profile TEXT,
    has_company TEXT,
    has_gtin TEXT,
    average_stock TEXT,
    business_type TEXT,
    declared_product_catalog_size NUMERIC(14, 2),
    declared_monthly_revenue NUMERIC(14, 2),
    CHECK (declared_product_catalog_size IS NULL OR declared_product_catalog_size >= 0),
    CHECK (declared_monthly_revenue IS NULL OR declared_monthly_revenue >= 0)
);

CREATE TABLE IF NOT EXISTS raw.olist_orders (
    order_id TEXT PRIMARY KEY,
    customer_id TEXT,
    order_status TEXT,
    order_purchase_timestamp TIMESTAMP,
    order_approved_at TIMESTAMP,
    order_delivered_carrier_date TIMESTAMP,
    order_delivered_customer_date TIMESTAMP,
    order_estimated_delivery_date TIMESTAMP
);

CREATE TABLE IF NOT EXISTS raw.olist_order_items (
    order_id TEXT,
    order_item_id INTEGER,
    product_id TEXT,
    seller_id TEXT,
    shipping_limit_date TIMESTAMP,
    price NUMERIC(12, 2),
    freight_value NUMERIC(12, 2),
    PRIMARY KEY (order_id, order_item_id),
    CHECK (order_item_id > 0),
    CHECK (price >= 0),
    CHECK (freight_value >= 0)
);

CREATE TABLE IF NOT EXISTS raw.olist_order_payments (
    order_id TEXT,
    payment_sequential INTEGER,
    payment_type TEXT,
    payment_installments INTEGER,
    payment_value NUMERIC(12, 2),
    PRIMARY KEY (order_id, payment_sequential),
    CHECK (payment_sequential > 0),
    CHECK (payment_installments >= 0),
    CHECK (payment_value >= 0)
);

CREATE TABLE IF NOT EXISTS raw.olist_order_reviews (
    review_id TEXT,
    order_id TEXT,
    review_score INTEGER,
    review_comment_title TEXT,
    review_comment_message TEXT,
    review_creation_date TIMESTAMP,
    review_answer_timestamp TIMESTAMP,
    CHECK (review_score BETWEEN 1 AND 5)
);

CREATE TABLE IF NOT EXISTS raw.olist_products (
    product_id TEXT PRIMARY KEY,
    product_category_name TEXT,
    product_name_lenght INTEGER,
    product_description_lenght INTEGER,
    product_photos_qty INTEGER,
    product_weight_g NUMERIC(12, 2),
    product_length_cm NUMERIC(12, 2),
    product_height_cm NUMERIC(12, 2),
    product_width_cm NUMERIC(12, 2),
    CHECK (product_name_lenght IS NULL OR product_name_lenght >= 0),
    CHECK (product_description_lenght IS NULL OR product_description_lenght >= 0),
    CHECK (product_photos_qty IS NULL OR product_photos_qty >= 0),
    CHECK (product_weight_g IS NULL OR product_weight_g >= 0),
    CHECK (product_length_cm IS NULL OR product_length_cm >= 0),
    CHECK (product_height_cm IS NULL OR product_height_cm >= 0),
    CHECK (product_width_cm IS NULL OR product_width_cm >= 0)
);

CREATE TABLE IF NOT EXISTS raw.olist_sellers (
    seller_id TEXT PRIMARY KEY,
    seller_zip_code_prefix TEXT,
    seller_city TEXT,
    seller_state TEXT
);

CREATE TABLE IF NOT EXISTS raw.product_category_name_translation (
    product_category_name TEXT PRIMARY KEY,
    product_category_name_english TEXT
);

CREATE INDEX IF NOT EXISTS idx_raw_geolocation_zip_prefix
    ON raw.olist_geolocation (geolocation_zip_code_prefix);

-- ---------------------------------------------------------------------------
-- STAGING TABLES: cleaned and standardized structures
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS staging.stg_customers (
    customer_id TEXT PRIMARY KEY,
    customer_unique_id TEXT NOT NULL,
    zip_prefix TEXT,
    city_name TEXT,
    state_code TEXT
);

CREATE TABLE IF NOT EXISTS staging.stg_sellers (
    seller_id TEXT PRIMARY KEY,
    zip_prefix TEXT,
    city_name TEXT,
    state_code TEXT
);

CREATE TABLE IF NOT EXISTS staging.stg_geolocation (
    zip_prefix TEXT PRIMARY KEY,
    latitude NUMERIC(10, 7),
    longitude NUMERIC(10, 7),
    city_name TEXT,
    state_code TEXT
);

CREATE TABLE IF NOT EXISTS staging.stg_product_categories (
    product_category_name TEXT PRIMARY KEY,
    product_category_name_english TEXT
);

CREATE TABLE IF NOT EXISTS staging.stg_products (
    product_id TEXT PRIMARY KEY,
    product_category_name TEXT,
    product_name_length INTEGER,
    product_description_length INTEGER,
    product_photos_qty INTEGER,
    product_weight_g NUMERIC(12, 2),
    product_length_cm NUMERIC(12, 2),
    product_height_cm NUMERIC(12, 2),
    product_width_cm NUMERIC(12, 2),
    CHECK (product_name_length IS NULL OR product_name_length >= 0),
    CHECK (product_description_length IS NULL OR product_description_length >= 0),
    CHECK (product_photos_qty IS NULL OR product_photos_qty >= 0),
    CHECK (product_weight_g IS NULL OR product_weight_g >= 0),
    CHECK (product_length_cm IS NULL OR product_length_cm >= 0),
    CHECK (product_height_cm IS NULL OR product_height_cm >= 0),
    CHECK (product_width_cm IS NULL OR product_width_cm >= 0)
);

CREATE TABLE IF NOT EXISTS staging.stg_orders (
    order_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    order_status TEXT,
    order_purchase_ts TIMESTAMP,
    order_approved_ts TIMESTAMP,
    order_delivered_carrier_ts TIMESTAMP,
    order_delivered_customer_ts TIMESTAMP,
    order_estimated_delivery_ts TIMESTAMP
);

CREATE TABLE IF NOT EXISTS staging.stg_order_items (
    order_id TEXT,
    order_item_id INTEGER,
    product_id TEXT,
    seller_id TEXT,
    shipping_limit_ts TIMESTAMP,
    price NUMERIC(12, 2),
    freight_value NUMERIC(12, 2),
    PRIMARY KEY (order_id, order_item_id),
    CHECK (order_item_id > 0),
    CHECK (price >= 0),
    CHECK (freight_value >= 0)
);

CREATE TABLE IF NOT EXISTS staging.stg_payments (
    order_id TEXT,
    payment_sequential INTEGER,
    payment_type TEXT,
    payment_installments INTEGER,
    payment_value NUMERIC(12, 2),
    PRIMARY KEY (order_id, payment_sequential),
    CHECK (payment_sequential > 0),
    CHECK (payment_installments >= 0),
    CHECK (payment_value >= 0)
);

CREATE TABLE IF NOT EXISTS staging.stg_reviews (
    review_id TEXT,
    order_id TEXT,
    review_score INTEGER,
    review_comment_title TEXT,
    review_comment_message TEXT,
    review_creation_ts TIMESTAMP,
    review_answer_ts TIMESTAMP,
    CHECK (review_score BETWEEN 1 AND 5)
);

CREATE TABLE IF NOT EXISTS staging.stg_marketing_leads (
    mql_id TEXT PRIMARY KEY,
    first_contact_date DATE,
    landing_page_id TEXT,
    origin TEXT
);

CREATE TABLE IF NOT EXISTS staging.stg_closed_deals (
    mql_id TEXT PRIMARY KEY,
    seller_id TEXT,
    sdr_id TEXT,
    sr_id TEXT,
    won_ts TIMESTAMP,
    business_segment TEXT,
    lead_type TEXT,
    lead_behaviour_profile TEXT,
    has_company BOOLEAN,
    has_gtin BOOLEAN,
    average_stock TEXT,
    business_type TEXT,
    declared_product_catalog_size NUMERIC(14, 2),
    declared_monthly_revenue NUMERIC(14, 2),
    CHECK (declared_product_catalog_size IS NULL OR declared_product_catalog_size >= 0),
    CHECK (declared_monthly_revenue IS NULL OR declared_monthly_revenue >= 0)
);

-- ---------------------------------------------------------------------------
-- DWH DIMENSIONS
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS dwh.dim_date (
    date_key INTEGER PRIMARY KEY,
    full_date DATE NOT NULL UNIQUE,
    day_of_month SMALLINT NOT NULL,
    day_of_week SMALLINT NOT NULL,
    day_name TEXT NOT NULL,
    week_of_year SMALLINT NOT NULL,
    month_number SMALLINT NOT NULL,
    month_name TEXT NOT NULL,
    quarter_number SMALLINT NOT NULL,
    year_number INTEGER NOT NULL,
    is_weekend BOOLEAN NOT NULL
);

CREATE TABLE IF NOT EXISTS dwh.dim_state (
    state_key BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    state_code TEXT NOT NULL UNIQUE,
    state_name TEXT
);

CREATE TABLE IF NOT EXISTS dwh.dim_city (
    city_key BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    city_name TEXT NOT NULL,
    state_key BIGINT NOT NULL REFERENCES dwh.dim_state (state_key),
    UNIQUE (city_name, state_key)
);

CREATE TABLE IF NOT EXISTS dwh.dim_zip_prefix (
    zip_prefix_key BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    zip_prefix TEXT NOT NULL UNIQUE,
    city_key BIGINT REFERENCES dwh.dim_city (city_key),
    state_key BIGINT REFERENCES dwh.dim_state (state_key),
    latitude NUMERIC(10, 7),
    longitude NUMERIC(10, 7)
);

CREATE TABLE IF NOT EXISTS dwh.dim_customer (
    customer_key BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_id TEXT NOT NULL UNIQUE,
    customer_unique_id TEXT NOT NULL,
    zip_prefix_key BIGINT REFERENCES dwh.dim_zip_prefix (zip_prefix_key),
    city_key BIGINT REFERENCES dwh.dim_city (city_key),
    state_key BIGINT REFERENCES dwh.dim_state (state_key)
);

CREATE TABLE IF NOT EXISTS dwh.dim_seller (
    seller_key BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    seller_id TEXT NOT NULL UNIQUE,
    zip_prefix_key BIGINT REFERENCES dwh.dim_zip_prefix (zip_prefix_key),
    city_key BIGINT REFERENCES dwh.dim_city (city_key),
    state_key BIGINT REFERENCES dwh.dim_state (state_key)
);

CREATE TABLE IF NOT EXISTS dwh.dim_product_category (
    product_category_key BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    product_category_name TEXT NOT NULL UNIQUE,
    product_category_name_english TEXT
);

CREATE TABLE IF NOT EXISTS dwh.dim_product (
    product_key BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    product_id TEXT NOT NULL UNIQUE,
    product_category_key BIGINT REFERENCES dwh.dim_product_category (product_category_key),
    product_name_length INTEGER,
    product_description_length INTEGER,
    product_photos_qty INTEGER,
    product_weight_g NUMERIC(12, 2),
    product_length_cm NUMERIC(12, 2),
    product_height_cm NUMERIC(12, 2),
    product_width_cm NUMERIC(12, 2)
);

CREATE TABLE IF NOT EXISTS dwh.dim_order_status (
    order_status_key BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    order_status TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS dwh.dim_payment_type (
    payment_type_key BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    payment_type TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS dwh.dim_marketing_origin (
    marketing_origin_key BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    origin_name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS dwh.dim_landing_page (
    landing_page_key BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    landing_page_id TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS dwh.dim_business_segment (
    business_segment_key BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    business_segment TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS dwh.dim_lead_type (
    lead_type_key BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    lead_type TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS dwh.dim_lead_profile (
    lead_profile_key BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    lead_behaviour_profile TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS dwh.dim_sales_rep (
    sales_rep_key BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    sales_rep_id TEXT NOT NULL,
    sales_role TEXT NOT NULL,
    UNIQUE (sales_rep_id, sales_role)
);

-- ---------------------------------------------------------------------------
-- DWH FACTS
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS dwh.fact_marketing_leads (
    marketing_lead_key BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    mql_id TEXT NOT NULL UNIQUE,
    first_contact_date_key INTEGER REFERENCES dwh.dim_date (date_key),
    landing_page_key BIGINT REFERENCES dwh.dim_landing_page (landing_page_key),
    marketing_origin_key BIGINT REFERENCES dwh.dim_marketing_origin (marketing_origin_key),
    lead_count INTEGER NOT NULL DEFAULT 1,
    CHECK (lead_count > 0)
);

CREATE TABLE IF NOT EXISTS dwh.fact_closed_deals (
    closed_deal_key BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    mql_id TEXT NOT NULL UNIQUE,
    seller_key BIGINT REFERENCES dwh.dim_seller (seller_key),
    won_date_key INTEGER REFERENCES dwh.dim_date (date_key),
    sdr_sales_rep_key BIGINT REFERENCES dwh.dim_sales_rep (sales_rep_key),
    sr_sales_rep_key BIGINT REFERENCES dwh.dim_sales_rep (sales_rep_key),
    business_segment_key BIGINT REFERENCES dwh.dim_business_segment (business_segment_key),
    lead_type_key BIGINT REFERENCES dwh.dim_lead_type (lead_type_key),
    lead_profile_key BIGINT REFERENCES dwh.dim_lead_profile (lead_profile_key),
    has_company BOOLEAN,
    has_gtin BOOLEAN,
    average_stock TEXT,
    business_type TEXT,
    declared_product_catalog_size NUMERIC(14, 2),
    declared_monthly_revenue NUMERIC(14, 2),
    is_active_seller BOOLEAN NOT NULL DEFAULT FALSE,
    deal_count INTEGER NOT NULL DEFAULT 1,
    CHECK (declared_product_catalog_size IS NULL OR declared_product_catalog_size >= 0),
    CHECK (declared_monthly_revenue IS NULL OR declared_monthly_revenue >= 0),
    CHECK (deal_count > 0)
);

CREATE TABLE IF NOT EXISTS dwh.fact_orders (
    order_key BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    order_id TEXT NOT NULL UNIQUE,
    customer_key BIGINT REFERENCES dwh.dim_customer (customer_key),
    order_status_key BIGINT REFERENCES dwh.dim_order_status (order_status_key),
    purchase_date_key INTEGER REFERENCES dwh.dim_date (date_key),
    approved_date_key INTEGER REFERENCES dwh.dim_date (date_key),
    delivered_carrier_date_key INTEGER REFERENCES dwh.dim_date (date_key),
    delivered_customer_date_key INTEGER REFERENCES dwh.dim_date (date_key),
    estimated_delivery_date_key INTEGER REFERENCES dwh.dim_date (date_key),
    order_purchase_ts TIMESTAMP,
    order_approved_ts TIMESTAMP,
    order_delivered_carrier_ts TIMESTAMP,
    order_delivered_customer_ts TIMESTAMP,
    order_estimated_delivery_ts TIMESTAMP,
    approval_delay_hours NUMERIC(12, 2),
    days_to_carrier NUMERIC(12, 2),
    days_to_customer NUMERIC(12, 2),
    estimated_delivery_days NUMERIC(12, 2),
    delivery_delay_days NUMERIC(12, 2),
    is_delivered_on_time BOOLEAN,
    is_delivered BOOLEAN NOT NULL DEFAULT FALSE,
    order_count INTEGER NOT NULL DEFAULT 1,
    CHECK (order_count > 0)
);

CREATE TABLE IF NOT EXISTS dwh.fact_order_items (
    order_item_key BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    order_id TEXT NOT NULL,
    order_item_id INTEGER NOT NULL,
    order_key BIGINT REFERENCES dwh.fact_orders (order_key),
    product_key BIGINT REFERENCES dwh.dim_product (product_key),
    seller_key BIGINT REFERENCES dwh.dim_seller (seller_key),
    shipping_limit_date_key INTEGER REFERENCES dwh.dim_date (date_key),
    shipping_limit_ts TIMESTAMP,
    item_price NUMERIC(12, 2),
    freight_value NUMERIC(12, 2),
    total_item_value NUMERIC(12, 2),
    item_count INTEGER NOT NULL DEFAULT 1,
    UNIQUE (order_id, order_item_id),
    CHECK (item_price IS NULL OR item_price >= 0),
    CHECK (freight_value IS NULL OR freight_value >= 0),
    CHECK (total_item_value IS NULL OR total_item_value >= 0),
    CHECK (item_count > 0)
);

CREATE TABLE IF NOT EXISTS dwh.fact_payments (
    payment_key BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    order_id TEXT NOT NULL,
    payment_sequential INTEGER NOT NULL,
    order_key BIGINT REFERENCES dwh.fact_orders (order_key),
    payment_type_key BIGINT REFERENCES dwh.dim_payment_type (payment_type_key),
    payment_installments INTEGER,
    payment_value NUMERIC(12, 2),
    payment_count INTEGER NOT NULL DEFAULT 1,
    UNIQUE (order_id, payment_sequential),
    CHECK (payment_sequential > 0),
    CHECK (payment_installments IS NULL OR payment_installments >= 0),
    CHECK (payment_value IS NULL OR payment_value >= 0),
    CHECK (payment_count > 0)
);

CREATE TABLE IF NOT EXISTS dwh.fact_reviews (
    review_key BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    review_id TEXT NOT NULL,
    order_id TEXT NOT NULL,
    order_key BIGINT REFERENCES dwh.fact_orders (order_key),
    review_creation_date_key INTEGER REFERENCES dwh.dim_date (date_key),
    review_answer_date_key INTEGER REFERENCES dwh.dim_date (date_key),
    review_score INTEGER,
    review_comment_title TEXT,
    review_comment_message TEXT,
    review_creation_ts TIMESTAMP,
    review_answer_ts TIMESTAMP,
    review_response_time_hours NUMERIC(12, 2),
    has_review_title BOOLEAN NOT NULL DEFAULT FALSE,
    has_review_message BOOLEAN NOT NULL DEFAULT FALSE,
    is_positive_review BOOLEAN NOT NULL DEFAULT FALSE,
    is_neutral_review BOOLEAN NOT NULL DEFAULT FALSE,
    is_negative_review BOOLEAN NOT NULL DEFAULT FALSE,
    review_count INTEGER NOT NULL DEFAULT 1,
    CHECK (review_score BETWEEN 1 AND 5),
    CHECK (review_count > 0)
);

CREATE INDEX IF NOT EXISTS idx_fact_orders_customer_key ON dwh.fact_orders (customer_key);
CREATE INDEX IF NOT EXISTS idx_fact_orders_purchase_date_key ON dwh.fact_orders (purchase_date_key);
CREATE INDEX IF NOT EXISTS idx_fact_order_items_order_key ON dwh.fact_order_items (order_key);
CREATE INDEX IF NOT EXISTS idx_fact_order_items_product_key ON dwh.fact_order_items (product_key);
CREATE INDEX IF NOT EXISTS idx_fact_order_items_seller_key ON dwh.fact_order_items (seller_key);
CREATE INDEX IF NOT EXISTS idx_fact_payments_order_key ON dwh.fact_payments (order_key);
CREATE INDEX IF NOT EXISTS idx_fact_reviews_order_key ON dwh.fact_reviews (order_key);
CREATE INDEX IF NOT EXISTS idx_fact_closed_deals_seller_key ON dwh.fact_closed_deals (seller_key);

COMMIT;
