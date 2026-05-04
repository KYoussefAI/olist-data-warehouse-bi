-- ============================================================
-- Warehouse Tables — Olist Data Warehouse & BI
-- Purpose:
-- Create dimensional warehouse tables for BI reporting.
-- ============================================================

DROP SCHEMA IF EXISTS warehouse CASCADE;

CREATE SCHEMA warehouse;

-- ============================================================
-- Dimension Tables
-- ============================================================

CREATE TABLE warehouse.dim_customer (
    customer_key SERIAL PRIMARY KEY,
    customer_id TEXT NOT NULL UNIQUE,
    customer_unique_id TEXT,
    customer_zip_code_prefix INTEGER,
    customer_city TEXT,
    customer_state TEXT
);

CREATE TABLE warehouse.dim_product (
    product_key SERIAL PRIMARY KEY,
    product_id TEXT NOT NULL UNIQUE,
    product_category_name TEXT,
    product_category_name_english TEXT,
    product_name_length INTEGER,
    product_description_length INTEGER,
    product_photos_qty INTEGER,
    product_weight_g NUMERIC,
    product_length_cm NUMERIC,
    product_height_cm NUMERIC,
    product_width_cm NUMERIC
);

CREATE TABLE warehouse.dim_seller (
    seller_key SERIAL PRIMARY KEY,
    seller_id TEXT NOT NULL UNIQUE,
    seller_zip_code_prefix INTEGER,
    seller_city TEXT,
    seller_state TEXT
);

CREATE TABLE warehouse.dim_date (
    date_key INTEGER PRIMARY KEY,
    full_date DATE NOT NULL UNIQUE,
    day INTEGER,
    month INTEGER,
    month_name TEXT,
    quarter INTEGER,
    year INTEGER,
    day_of_week INTEGER,
    day_name TEXT,
    is_weekend BOOLEAN
);

CREATE TABLE warehouse.dim_location (
    location_key SERIAL PRIMARY KEY,
    zip_code_prefix INTEGER NOT NULL UNIQUE,
    city TEXT,
    state TEXT,
    latitude NUMERIC,
    longitude NUMERIC
);

CREATE TABLE warehouse.dim_order_status (
    order_status_key SERIAL PRIMARY KEY,
    order_status TEXT NOT NULL UNIQUE
);

CREATE TABLE warehouse.dim_payment_type (
    payment_type_key SERIAL PRIMARY KEY,
    payment_type TEXT NOT NULL UNIQUE
);

-- ============================================================
-- Fact Tables
-- ============================================================

CREATE TABLE warehouse.fact_order_items (
    order_item_key SERIAL PRIMARY KEY,

    order_id TEXT NOT NULL,
    order_item_id INTEGER NOT NULL,

    customer_key INTEGER REFERENCES warehouse.dim_customer(customer_key),
    product_key INTEGER REFERENCES warehouse.dim_product(product_key),
    seller_key INTEGER REFERENCES warehouse.dim_seller(seller_key),
    purchase_date_key INTEGER REFERENCES warehouse.dim_date(date_key),
    order_status_key INTEGER REFERENCES warehouse.dim_order_status(order_status_key),
    customer_location_key INTEGER REFERENCES warehouse.dim_location(location_key),
    seller_location_key INTEGER REFERENCES warehouse.dim_location(location_key),

    price NUMERIC,
    freight_value NUMERIC,
    total_item_value NUMERIC,
    delivery_days NUMERIC,
    is_late_delivery BOOLEAN,

    UNIQUE (order_id, order_item_id)
);

CREATE TABLE warehouse.fact_payments (
    payment_key SERIAL PRIMARY KEY,

    order_id TEXT NOT NULL,
    payment_sequential INTEGER,
    payment_type_key INTEGER REFERENCES warehouse.dim_payment_type(payment_type_key),
    payment_installments INTEGER,
    payment_value NUMERIC,

    UNIQUE (order_id, payment_sequential)
);

CREATE TABLE warehouse.fact_reviews (
    review_key SERIAL PRIMARY KEY,

    review_id TEXT NOT NULL,
    order_id TEXT NOT NULL,
    review_date_key INTEGER REFERENCES warehouse.dim_date(date_key),
    review_score INTEGER,
    has_review_comment BOOLEAN,
    review_answer_delay_days NUMERIC,

    UNIQUE (review_id, order_id)
);

-- ============================================================
-- Indexes for BI Query Performance
-- ============================================================

CREATE INDEX idx_fact_order_items_order_id
ON warehouse.fact_order_items(order_id);

CREATE INDEX idx_fact_order_items_customer_key
ON warehouse.fact_order_items(customer_key);

CREATE INDEX idx_fact_order_items_product_key
ON warehouse.fact_order_items(product_key);

CREATE INDEX idx_fact_order_items_seller_key
ON warehouse.fact_order_items(seller_key);

CREATE INDEX idx_fact_order_items_purchase_date_key
ON warehouse.fact_order_items(purchase_date_key);

CREATE INDEX idx_fact_payments_order_id
ON warehouse.fact_payments(order_id);

CREATE INDEX idx_fact_reviews_order_id
ON warehouse.fact_reviews(order_id);