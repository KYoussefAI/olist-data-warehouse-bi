from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"

DATABASE_URL = "postgresql+psycopg2://youssef:youssef@localhost:5432/olist_dw"


TABLE_MAPPINGS = [
    {
        "file_name": "olist_customers_dataset.csv",
        "table_name": "customers",
    },
    {
        "file_name": "olist_geolocation_dataset.csv",
        "table_name": "geolocation",
    },
    {
        "file_name": "olist_order_items_dataset.csv",
        "table_name": "order_items",
    },
    {
        "file_name": "olist_order_payments_dataset.csv",
        "table_name": "order_payments",
    },
    {
        "file_name": "olist_order_reviews_dataset.csv",
        "table_name": "order_reviews",
    },
    {
        "file_name": "olist_orders_dataset.csv",
        "table_name": "orders",
    },
    {
        "file_name": "olist_products_dataset.csv",
        "table_name": "products",
    },
    {
        "file_name": "olist_sellers_dataset.csv",
        "table_name": "sellers",
    },
    {
        "file_name": "product_category_name_translation.csv",
        "table_name": "product_category_translation",
    },
]


def load_csv_to_staging(engine, file_name: str, table_name: str) -> None:
    file_path = RAW_DATA_DIR / file_name

    if not file_path.exists():
        raise FileNotFoundError(f"Missing file: {file_path}")

    print(f"Loading {file_name} into staging.{table_name}...")

    df = pd.read_csv(file_path)

    df.to_sql(
        name=table_name,
        con=engine,
        schema="staging",
        if_exists="append",
        index=False,
        chunksize=10000,
        method="multi",
    )

    print(f"Loaded {len(df)} rows into staging.{table_name}")


def main() -> None:
    engine = create_engine(DATABASE_URL)

    print("========== LOADING RAW CSV FILES TO POSTGRESQL STAGING ==========")

    for mapping in TABLE_MAPPINGS:
        load_csv_to_staging(
            engine=engine,
            file_name=mapping["file_name"],
            table_name=mapping["table_name"],
        )

    print("========== STAGING LOAD COMPLETE ==========")


if __name__ == "__main__":
    main()