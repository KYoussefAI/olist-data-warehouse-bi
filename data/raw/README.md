# Raw Olist CSV files

Place the source CSV files here before running the ETL pipeline.

Expected files:

```text
olist_customers_dataset.csv
olist_geolocation_dataset.csv
olist_order_items_dataset.csv
olist_order_payments_dataset.csv
olist_order_reviews_dataset.csv
olist_orders_dataset.csv
olist_products_dataset.csv
olist_sellers_dataset.csv
product_category_name_translation.csv
olist_marketing_qualified_leads_dataset.csv
olist_closed_deals_dataset.csv
```

The CSV files are intentionally not committed to Git. The repository `.gitignore` excludes `data/raw/*.csv`.

After adding the files, run:

```bash
python -m src.run_etl --step all
```
