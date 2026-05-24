from __future__ import annotations

import logging
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.engine import Engine

from .config import settings

logger = logging.getLogger(__name__)

RAW_TABLES = {
    "olist_customers_dataset.csv": (
        "raw.olist_customers",
        [
            "customer_id",
            "customer_unique_id",
            "customer_zip_code_prefix",
            "customer_city",
            "customer_state",
        ],
    ),
    "olist_geolocation_dataset.csv": (
        "raw.olist_geolocation",
        [
            "geolocation_zip_code_prefix",
            "geolocation_lat",
            "geolocation_lng",
            "geolocation_city",
            "geolocation_state",
        ],
    ),
    "olist_marketing_qualified_leads_dataset.csv": (
        "raw.olist_marketing_qualified_leads",
        ["mql_id", "first_contact_date", "landing_page_id", "origin"],
    ),
    "olist_closed_deals_dataset.csv": (
        "raw.olist_closed_deals",
        [
            "mql_id",
            "seller_id",
            "sdr_id",
            "sr_id",
            "won_date",
            "business_segment",
            "lead_type",
            "lead_behaviour_profile",
            "has_company",
            "has_gtin",
            "average_stock",
            "business_type",
            "declared_product_catalog_size",
            "declared_monthly_revenue",
        ],
    ),
    "olist_orders_dataset.csv": (
        "raw.olist_orders",
        [
            "order_id",
            "customer_id",
            "order_status",
            "order_purchase_timestamp",
            "order_approved_at",
            "order_delivered_carrier_date",
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
        ],
    ),
    "olist_order_items_dataset.csv": (
        "raw.olist_order_items",
        [
            "order_id",
            "order_item_id",
            "product_id",
            "seller_id",
            "shipping_limit_date",
            "price",
            "freight_value",
        ],
    ),
    "olist_order_payments_dataset.csv": (
        "raw.olist_order_payments",
        [
            "order_id",
            "payment_sequential",
            "payment_type",
            "payment_installments",
            "payment_value",
        ],
    ),
    "olist_order_reviews_dataset.csv": (
        "raw.olist_order_reviews",
        [
            "review_id",
            "order_id",
            "review_score",
            "review_comment_title",
            "review_comment_message",
            "review_creation_date",
            "review_answer_timestamp",
        ],
    ),
    "olist_products_dataset.csv": (
        "raw.olist_products",
        [
            "product_id",
            "product_category_name",
            "product_name_lenght",
            "product_description_lenght",
            "product_photos_qty",
            "product_weight_g",
            "product_length_cm",
            "product_height_cm",
            "product_width_cm",
        ],
    ),
    "olist_sellers_dataset.csv": (
        "raw.olist_sellers",
        ["seller_id", "seller_zip_code_prefix", "seller_city", "seller_state"],
    ),
    "product_category_name_translation.csv": (
        "raw.product_category_name_translation",
        ["product_category_name", "product_category_name_english"],
    ),
}

RAW_TRUNCATE_ORDER = [table for table, _ in RAW_TABLES.values()]


def truncate_raw(engine: Engine) -> None:
    logger.info("Truncating raw tables")
    with engine.begin() as conn:
        for table in RAW_TRUNCATE_ORDER:
            conn.execute(text(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE"))


def copy_csv_to_table(engine: Engine, csv_path: Path, table_name: str, columns: list[str]) -> None:
    if not csv_path.exists():
        raise FileNotFoundError(f"Missing raw CSV: {csv_path}")

    column_list = ", ".join(columns)
    copy_sql = f"""
        COPY {table_name} ({column_list})
        FROM STDIN
        WITH (FORMAT CSV, HEADER TRUE, NULL '', ENCODING 'UTF8')
    """

    logger.info("Loading %s into %s", csv_path.name, table_name)
    raw_conn = engine.raw_connection()
    try:
        with raw_conn.cursor() as cur, csv_path.open("r", encoding="utf-8") as f:
            cur.copy_expert(copy_sql, f)
        raw_conn.commit()
    except Exception:
        raw_conn.rollback()
        raise
    finally:
        raw_conn.close()


def load_all_raw(engine: Engine, raw_data_dir: Path | None = None) -> None:
    raw_data_dir = raw_data_dir or settings.raw_data_dir
    truncate_raw(engine)
    for filename, (table_name, columns) in RAW_TABLES.items():
        copy_csv_to_table(engine, raw_data_dir / filename, table_name, columns)
