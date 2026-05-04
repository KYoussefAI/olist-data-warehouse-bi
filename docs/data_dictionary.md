# Data Dictionary — Olist Data Warehouse & BI

## 1. Purpose

This document describes the role of each raw Olist dataset file, its main business meaning, key columns, and how it will be used in the Data Warehouse.

The objective is to move from raw CSV understanding to dimensional modeling.

---

## 2. Source Tables Overview

| Source File | Business Meaning | Main Key | Target Role |
|---|---|---|---|
| olist_customers_dataset.csv | Customer information and location | customer_id | Dimension source |
| olist_orders_dataset.csv | Order lifecycle and timestamps | order_id | Fact and date source |
| olist_order_items_dataset.csv | Products sold inside each order | order_id + order_item_id | Main fact source |
| olist_order_payments_dataset.csv | Payment transactions linked to orders | order_id + payment_sequential | Payment fact source |
| olist_order_reviews_dataset.csv | Customer satisfaction reviews | review_id | Review fact source |
| olist_products_dataset.csv | Product attributes and categories | product_id | Dimension source |
| olist_sellers_dataset.csv | Seller information and location | seller_id | Dimension source |
| olist_geolocation_dataset.csv | Zip code geographic coordinates | geolocation_zip_code_prefix | Location dimension source |
| product_category_name_translation.csv | Portuguese to English category mapping | product_category_name | Reference table |

---

## 3. Table Details

### 3.1 Customers

Source file:

```text
olist_customers_dataset.csv
```

Business role:

```text
Identifies the customer linked to each order and provides customer city/state information.
```

Important columns:

| Column | Meaning |
|---|---|
| customer_id | Order-level customer identifier |
| customer_unique_id | Unique anonymized customer identifier |
| customer_zip_code_prefix | Customer zip code prefix |
| customer_city | Customer city |
| customer_state | Customer state |

Target use:

```text
dim_customer
dim_location
```

Data quality notes:

```text
No null values were detected in the customer source table.
customer_id is unique at order-customer level, while customer_unique_id can appear across multiple orders.
```

---

### 3.2 Orders

Source file:

```text
olist_orders_dataset.csv
```

Business role:

```text
Stores order status and key timestamps for purchase, approval, shipping, delivery, and estimated delivery.
```

Important columns:

| Column | Meaning |
|---|---|
| order_id | Unique order identifier |
| customer_id | Links order to customer |
| order_status | Current/final order status |
| order_purchase_timestamp | Purchase date and time |
| order_approved_at | Approval timestamp |
| order_delivered_carrier_date | Carrier delivery timestamp |
| order_delivered_customer_date | Customer delivery timestamp |
| order_estimated_delivery_date | Estimated delivery date |

Target use:

```text
fact_order_items
dim_date
dim_order_status
logistics KPIs
```

Data quality notes:

```text
Delivery timestamp columns contain null values.
These nulls must be handled carefully when calculating delivery duration and late delivery rate.
Orders without delivered_customer_date should not be used directly in average delivery duration calculations.
```

---

### 3.3 Order Items

Source file:

```text
olist_order_items_dataset.csv
```

Business role:

```text
Stores each product item sold inside an order.
```

Important columns:

| Column | Meaning |
|---|---|
| order_id | Links item to order |
| order_item_id | Item number inside the order |
| product_id | Product sold |
| seller_id | Seller of the item |
| shipping_limit_date | Seller shipping deadline |
| price | Item price |
| freight_value | Freight cost |

Target use:

```text
fact_order_items
```

Grain:

```text
One row = one product item sold inside one order
```

Data quality notes:

```text
No null values were detected in the order items source table.
This table is the central source for sales revenue, freight value, product analysis, and seller analysis.
```

---

### 3.4 Payments

Source file:

```text
olist_order_payments_dataset.csv
```

Business role:

```text
Stores payment methods, installments, and payment amounts for each order.
```

Important columns:

| Column | Meaning |
|---|---|
| order_id | Links payment to order |
| payment_sequential | Payment sequence number |
| payment_type | Payment method |
| payment_installments | Number of installments |
| payment_value | Payment amount |

Target use:

```text
fact_payments
dim_payment_type
```

Grain:

```text
One row = one payment sequence linked to an order
```

Data quality notes:

```text
Some orders may have multiple payment rows.
For this reason, payments should not be blindly joined to order_items without aggregation or careful grain management.
```

---

### 3.5 Reviews

Source file:

```text
olist_order_reviews_dataset.csv
```

Business role:

```text
Stores customer review scores and optional review comments.
```

Important columns:

| Column | Meaning |
|---|---|
| review_id | Review identifier |
| order_id | Links review to order |
| review_score | Score from 1 to 5 |
| review_comment_title | Optional review title |
| review_comment_message | Optional review message |
| review_creation_date | Review creation date |
| review_answer_timestamp | Review answer timestamp |

Target use:

```text
fact_reviews
customer satisfaction KPIs
```

Data quality notes:

```text
review_comment_title and review_comment_message contain many null values.
The first version of the BI dashboard will focus on review_score as the main satisfaction metric.
Text analytics on review comments can be added later as an improvement.
```

---

### 3.6 Products

Source file:

```text
olist_products_dataset.csv
```

Business role:

```text
Stores product attributes, category, size, weight, and photo quantity.
```

Important columns:

| Column | Meaning |
|---|---|
| product_id | Unique product identifier |
| product_category_name | Product category in Portuguese |
| product_name_lenght | Product name length |
| product_description_lenght | Product description length |
| product_photos_qty | Number of product photos |
| product_weight_g | Product weight in grams |
| product_length_cm | Product length |
| product_height_cm | Product height |
| product_width_cm | Product width |

Target use:

```text
dim_product
```

Data quality notes:

```text
Some product category values are missing.
Missing categories will be handled as unknown or uncategorized in dim_product.
The English category name will be added using product_category_name_translation.csv.
```

---

### 3.7 Sellers

Source file:

```text
olist_sellers_dataset.csv
```

Business role:

```text
Stores seller location information.
```

Important columns:

| Column | Meaning |
|---|---|
| seller_id | Unique seller identifier |
| seller_zip_code_prefix | Seller zip code prefix |
| seller_city | Seller city |
| seller_state | Seller state |

Target use:

```text
dim_seller
dim_location
```

Data quality notes:

```text
No null values were detected in the seller source table.
Seller location can be analyzed by city, state, and optionally zip code prefix.
```

---

### 3.8 Geolocation

Source file:

```text
olist_geolocation_dataset.csv
```

Business role:

```text
Stores geographic coordinates by zip code prefix.
```

Important columns:

| Column | Meaning |
|---|---|
| geolocation_zip_code_prefix | Zip code prefix |
| geolocation_lat | Latitude |
| geolocation_lng | Longitude |
| geolocation_city | City |
| geolocation_state | State |

Target use:

```text
dim_location
```

Data quality notes:

```text
This file contains many duplicate rows.
It should be deduplicated or aggregated by zip code prefix before being used as a location dimension.
A practical first approach is to group by zip code prefix, city, and state, then calculate average latitude and longitude.
```

---

### 3.9 Product Category Translation

Source file:

```text
product_category_name_translation.csv
```

Business role:

```text
Maps Portuguese product category names to English category names.
```

Important columns:

| Column | Meaning |
|---|---|
| product_category_name | Portuguese category name |
| product_category_name_english | English category name |

Target use:

```text
Reference table for dim_product
```

Data quality notes:

```text
This file is small and will be used as a lookup table during product dimension creation.
```

---

## 4. Main Relationships

```text
orders.customer_id
→ customers.customer_id

order_items.order_id
→ orders.order_id

order_items.product_id
→ products.product_id

order_items.seller_id
→ sellers.seller_id

payments.order_id
→ orders.order_id

reviews.order_id
→ orders.order_id

products.product_category_name
→ product_category_name_translation.product_category_name

customers.customer_zip_code_prefix
→ geolocation.geolocation_zip_code_prefix

sellers.seller_zip_code_prefix
→ geolocation.geolocation_zip_code_prefix
```

---

## 5. Modeling Direction

The first warehouse version will use the following target tables.

### Dimensions

```text
dim_customer
dim_product
dim_seller
dim_date
dim_location
dim_order_status
dim_payment_type
```

### Facts

```text
fact_order_items
fact_payments
fact_reviews
```

---

## 6. Important Data Quality Decisions

| Issue | Decision |
|---|---|
| Geolocation duplicates | Deduplicate or aggregate by zip code prefix |
| Missing review comments | Keep review_score as main satisfaction metric |
| Missing product category | Replace with unknown or uncategorized |
| Missing delivery dates | Exclude from delivery duration calculation or mark as not delivered |
| Multiple payments per order | Keep payment fact at payment sequence grain |
| Multiple items per order | Keep sales fact at item-level grain |
| Product categories in Portuguese | Join translation table to expose English category names |

---

## 7. First Version Scope

Version 1 of the Data Warehouse will focus on:

```text
Sales analysis
Product/category analysis
Customer location analysis
Seller performance
Delivery delay analysis
Payment method analysis
Review score analysis
```

Out of scope for version 1:

```text
Natural language processing on review comments
Advanced customer segmentation
Machine learning prediction
Real-time streaming
Airflow orchestration
Dockerized deployment
```

These topics can be added after the minimal working BI pipeline is complete.

---

## 8. Reusable Pattern to Memorize

For every future Data Warehouse project, repeat this pattern:

```text
Raw source inventory
→ Data dictionary
→ Relationship mapping
→ Grain definition
→ Dimension/fact design
→ Staging tables
→ Warehouse tables
→ Validation queries
→ Dashboard
```

