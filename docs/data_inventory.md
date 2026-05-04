# Raw Data Inventory — Olist Dataset

## Purpose

This document summarizes the structure and quality profile of the raw Olist CSV files before loading them into staging tables.

## Source Files Summary

| File | Rows | Columns | Duplicate Rows |
|---|---:|---:|---:|
| olist_customers_dataset.csv | 99441 | 5 | 0 |
| olist_geolocation_dataset.csv | 1000163 | 5 | 261831 |
| olist_order_items_dataset.csv | 112650 | 7 | 0 |
| olist_order_payments_dataset.csv | 103886 | 5 | 0 |
| olist_order_reviews_dataset.csv | 99224 | 7 | 0 |
| olist_orders_dataset.csv | 99441 | 8 | 0 |
| olist_products_dataset.csv | 32951 | 9 | 0 |
| olist_sellers_dataset.csv | 3095 | 4 | 0 |
| product_category_name_translation.csv | 71 | 2 | 0 |

---

## olist_customers_dataset.csv

- Rows: `99441`
- Columns: `5`
- Duplicate rows: `0`

| Column | Type | Null Count | Null % | Unique Values |
|---|---|---:|---:|---:|
| customer_id | str | 0 | 0.0 | 99441 |
| customer_unique_id | str | 0 | 0.0 | 96096 |
| customer_zip_code_prefix | int64 | 0 | 0.0 | 14994 |
| customer_city | str | 0 | 0.0 | 4119 |
| customer_state | str | 0 | 0.0 | 27 |

---

## olist_geolocation_dataset.csv

- Rows: `1000163`
- Columns: `5`
- Duplicate rows: `261831`

| Column | Type | Null Count | Null % | Unique Values |
|---|---|---:|---:|---:|
| geolocation_zip_code_prefix | int64 | 0 | 0.0 | 19015 |
| geolocation_lat | float64 | 0 | 0.0 | 717360 |
| geolocation_lng | float64 | 0 | 0.0 | 717613 |
| geolocation_city | str | 0 | 0.0 | 8011 |
| geolocation_state | str | 0 | 0.0 | 27 |

---

## olist_order_items_dataset.csv

- Rows: `112650`
- Columns: `7`
- Duplicate rows: `0`

| Column | Type | Null Count | Null % | Unique Values |
|---|---|---:|---:|---:|
| order_id | str | 0 | 0.0 | 98666 |
| order_item_id | int64 | 0 | 0.0 | 21 |
| product_id | str | 0 | 0.0 | 32951 |
| seller_id | str | 0 | 0.0 | 3095 |
| shipping_limit_date | str | 0 | 0.0 | 93318 |
| price | float64 | 0 | 0.0 | 5968 |
| freight_value | float64 | 0 | 0.0 | 6999 |

---

## olist_order_payments_dataset.csv

- Rows: `103886`
- Columns: `5`
- Duplicate rows: `0`

| Column | Type | Null Count | Null % | Unique Values |
|---|---|---:|---:|---:|
| order_id | str | 0 | 0.0 | 99440 |
| payment_sequential | int64 | 0 | 0.0 | 29 |
| payment_type | str | 0 | 0.0 | 5 |
| payment_installments | int64 | 0 | 0.0 | 24 |
| payment_value | float64 | 0 | 0.0 | 29077 |

---

## olist_order_reviews_dataset.csv

- Rows: `99224`
- Columns: `7`
- Duplicate rows: `0`

| Column | Type | Null Count | Null % | Unique Values |
|---|---|---:|---:|---:|
| review_id | str | 0 | 0.0 | 98410 |
| order_id | str | 0 | 0.0 | 98673 |
| review_score | int64 | 0 | 0.0 | 5 |
| review_comment_title | str | 87656 | 88.34 | 4527 |
| review_comment_message | str | 58247 | 58.7 | 36159 |
| review_creation_date | str | 0 | 0.0 | 636 |
| review_answer_timestamp | str | 0 | 0.0 | 98248 |

---

## olist_orders_dataset.csv

- Rows: `99441`
- Columns: `8`
- Duplicate rows: `0`

| Column | Type | Null Count | Null % | Unique Values |
|---|---|---:|---:|---:|
| order_id | str | 0 | 0.0 | 99441 |
| customer_id | str | 0 | 0.0 | 99441 |
| order_status | str | 0 | 0.0 | 8 |
| order_purchase_timestamp | str | 0 | 0.0 | 98875 |
| order_approved_at | str | 160 | 0.16 | 90733 |
| order_delivered_carrier_date | str | 1783 | 1.79 | 81018 |
| order_delivered_customer_date | str | 2965 | 2.98 | 95664 |
| order_estimated_delivery_date | str | 0 | 0.0 | 459 |

---

## olist_products_dataset.csv

- Rows: `32951`
- Columns: `9`
- Duplicate rows: `0`

| Column | Type | Null Count | Null % | Unique Values |
|---|---|---:|---:|---:|
| product_id | str | 0 | 0.0 | 32951 |
| product_category_name | str | 610 | 1.85 | 73 |
| product_name_lenght | float64 | 610 | 1.85 | 66 |
| product_description_lenght | float64 | 610 | 1.85 | 2960 |
| product_photos_qty | float64 | 610 | 1.85 | 19 |
| product_weight_g | float64 | 2 | 0.01 | 2204 |
| product_length_cm | float64 | 2 | 0.01 | 99 |
| product_height_cm | float64 | 2 | 0.01 | 102 |
| product_width_cm | float64 | 2 | 0.01 | 95 |

---

## olist_sellers_dataset.csv

- Rows: `3095`
- Columns: `4`
- Duplicate rows: `0`

| Column | Type | Null Count | Null % | Unique Values |
|---|---|---:|---:|---:|
| seller_id | str | 0 | 0.0 | 3095 |
| seller_zip_code_prefix | int64 | 0 | 0.0 | 2246 |
| seller_city | str | 0 | 0.0 | 611 |
| seller_state | str | 0 | 0.0 | 23 |

---

## product_category_name_translation.csv

- Rows: `71`
- Columns: `2`
- Duplicate rows: `0`

| Column | Type | Null Count | Null % | Unique Values |
|---|---|---:|---:|---:|
| product_category_name | str | 0 | 0.0 | 71 |
| product_category_name_english | str | 0 | 0.0 | 71 |

---

