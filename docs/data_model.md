# Data Model — Olist Data Warehouse & BI

## 1. Purpose

This document defines the dimensional model of the Olist Data Warehouse.

The objective is to transform raw operational CSV files into analytical tables optimized for SQL analysis and Power BI reporting.

The dashboard must not query raw CSV files directly. It will query fact and dimension tables stored in PostgreSQL.

---

## 2. Modeling Approach

This project uses dimensional modeling.

Dimensional modeling separates data into:

- **Fact tables**: measurable business events.
- **Dimension tables**: descriptive analysis axes.

General flow:

```text
Raw CSV files
→ Staging tables
→ Dimension tables
→ Fact tables
→ SQL validation
→ Power BI dashboard
```

---

## 3. Central Grain Decision

The main business process is e-commerce sales.

The central grain is:

```text
One row = one product item sold inside one order
```

This grain is represented by:

```text
fact_order_items
```

This means that if one order contains three products, the fact table will contain three rows for that order.

This grain allows analysis by:

- order
- customer
- product
- product category
- seller
- purchase date
- customer location
- seller location
- order status
- item price
- freight value

---

## 4. Target Tables

### 4.1 Dimension Tables

| Dimension | Grain | Main Source |
|---|---|---|
| dim_customer | One row per customer_id | olist_customers_dataset.csv |
| dim_product | One row per product_id | olist_products_dataset.csv |
| dim_seller | One row per seller_id | olist_sellers_dataset.csv |
| dim_date | One row per calendar date | Generated from order dates |
| dim_location | One row per zip code prefix | olist_geolocation_dataset.csv |
| dim_order_status | One row per order status | olist_orders_dataset.csv |
| dim_payment_type | One row per payment type | olist_order_payments_dataset.csv |

### 4.2 Fact Tables

| Fact Table | Grain | Main Source |
|---|---|---|
| fact_order_items | One row per order item | olist_order_items_dataset.csv |
| fact_payments | One row per payment sequence | olist_order_payments_dataset.csv |
| fact_reviews | One row per review | olist_order_reviews_dataset.csv |

---

## 5. Logical Star Schema

```text
                          dim_date
                             |
                             |
dim_customer  ----   fact_order_items   ---- dim_product
                             |
                             |
                         dim_seller
                             |
                             |
                    dim_order_status
                             |
                             |
                        dim_location


fact_payments  ---- dim_payment_type
fact_reviews   ---- dim_date
```

Important note:

```text
fact_payments and fact_reviews are linked to orders through order_id.
In the first version, order_id can be kept as a degenerate dimension for traceability.
```

---

## 6. Dimension Definitions

## 6.1 dim_customer

### Purpose

Stores customer-level descriptive information.

### Source

```text
olist_customers_dataset.csv
```

### Grain

```text
One row = one customer_id
```

### Columns

| Column | Type | Description |
|---|---|---|
| customer_key | surrogate key | Technical warehouse key |
| customer_id | natural key | Source customer identifier |
| customer_unique_id | text | Unique anonymized customer identifier |
| customer_zip_code_prefix | integer | Customer zip code prefix |
| customer_city | text | Customer city |
| customer_state | text | Customer state |

### Business Questions Supported

- Which states generate the most orders?
- Which cities generate the most revenue?
- How many customers does the marketplace have?

---

## 6.2 dim_product

### Purpose

Stores product attributes and category information.

### Sources

```text
olist_products_dataset.csv
product_category_name_translation.csv
```

### Grain

```text
One row = one product_id
```

### Columns

| Column | Type | Description |
|---|---|---|
| product_key | surrogate key | Technical warehouse key |
| product_id | natural key | Source product identifier |
| product_category_name | text | Original category name in Portuguese |
| product_category_name_english | text | Translated category name in English |
| product_name_length | integer | Product name length |
| product_description_length | integer | Product description length |
| product_photos_qty | integer | Number of product photos |
| product_weight_g | numeric | Product weight in grams |
| product_length_cm | numeric | Product length |
| product_height_cm | numeric | Product height |
| product_width_cm | numeric | Product width |

### Business Questions Supported

- Which categories generate the highest revenue?
- Which product categories sell the most?
- Which categories have high freight costs?
- Which categories receive better or worse reviews?

### Data Quality Decision

Missing product categories will be replaced with:

```text
unknown
```

---

## 6.3 dim_seller

### Purpose

Stores seller-level descriptive information.

### Source

```text
olist_sellers_dataset.csv
```

### Grain

```text
One row = one seller_id
```

### Columns

| Column | Type | Description |
|---|---|---|
| seller_key | surrogate key | Technical warehouse key |
| seller_id | natural key | Source seller identifier |
| seller_zip_code_prefix | integer | Seller zip code prefix |
| seller_city | text | Seller city |
| seller_state | text | Seller state |

### Business Questions Supported

- Which sellers generate the most revenue?
- Which sellers have the highest number of orders?
- Which sellers are linked to frequent delivery delays?

---

## 6.4 dim_date

### Purpose

Stores calendar attributes for time-based analysis.

### Source

Generated from date columns in:

```text
olist_orders_dataset.csv
olist_order_reviews_dataset.csv
olist_order_items_dataset.csv
```

### Grain

```text
One row = one calendar date
```

### Columns

| Column | Type | Description |
|---|---|---|
| date_key | integer | Date key in YYYYMMDD format |
| full_date | date | Calendar date |
| day | integer | Day of month |
| month | integer | Month number |
| month_name | text | Month name |
| quarter | integer | Quarter number |
| year | integer | Year |
| day_of_week | integer | Day of week number |
| day_name | text | Day name |
| is_weekend | boolean | Weekend flag |

### Business Questions Supported

- Which months generate the most revenue?
- How do sales evolve over time?
- What is the average delivery time by month?

---

## 6.5 dim_location

### Purpose

Stores geographic information for location-based analysis.

### Source

```text
olist_geolocation_dataset.csv
```

### Grain

Version 1 grain:

```text
One row = one zip code prefix
```

### Columns

| Column | Type | Description |
|---|---|---|
| location_key | surrogate key | Technical warehouse key |
| zip_code_prefix | integer | Zip code prefix |
| city | text | City |
| state | text | State |
| latitude | numeric | Average latitude |
| longitude | numeric | Average longitude |

### Business Questions Supported

- Which states have the highest order volume?
- Which cities generate the most revenue?
- Where are delivery delays concentrated?

### Data Quality Decision

The geolocation file contains many duplicate rows. The first warehouse version will aggregate geolocation by zip code prefix using average latitude and longitude.

---

## 6.6 dim_order_status

### Purpose

Stores the list of possible order statuses.

### Source

```text
olist_orders_dataset.csv
```

### Grain

```text
One row = one order_status
```

### Columns

| Column | Type | Description |
|---|---|---|
| order_status_key | surrogate key | Technical warehouse key |
| order_status | text | Order status value |

### Example Values

```text
delivered
shipped
canceled
invoiced
processing
unavailable
created
approved
```

### Business Questions Supported

- How many orders were delivered?
- How many orders were canceled?
- What is the revenue by order status?

---

## 6.7 dim_payment_type

### Purpose

Stores payment method categories.

### Source

```text
olist_order_payments_dataset.csv
```

### Grain

```text
One row = one payment_type
```

### Columns

| Column | Type | Description |
|---|---|---|
| payment_type_key | surrogate key | Technical warehouse key |
| payment_type | text | Payment method |

### Example Values

```text
credit_card
boleto
voucher
debit_card
not_defined
```

### Business Questions Supported

- Which payment method is most used?
- Does payment method influence average order value?
- Which payment method generates the most revenue?

---

## 7. Fact Table Definitions

## 7.1 fact_order_items

### Purpose

Main sales fact table.

### Grain

```text
One row = one product item sold inside one order
```

### Main Sources

```text
olist_order_items_dataset.csv
olist_orders_dataset.csv
olist_customers_dataset.csv
olist_products_dataset.csv
olist_sellers_dataset.csv
```

### Columns

| Column | Type | Description |
|---|---|---|
| order_item_key | surrogate key | Technical fact key |
| order_id | degenerate dimension | Source order identifier |
| order_item_id | integer | Item sequence inside the order |
| customer_key | foreign key | Links to dim_customer |
| product_key | foreign key | Links to dim_product |
| seller_key | foreign key | Links to dim_seller |
| purchase_date_key | foreign key | Links to dim_date |
| order_status_key | foreign key | Links to dim_order_status |
| customer_location_key | foreign key | Links to dim_location |
| seller_location_key | foreign key | Links to dim_location |
| price | numeric | Item price |
| freight_value | numeric | Freight cost |
| total_item_value | numeric | price + freight_value |
| delivery_days | numeric | Days between purchase and customer delivery |
| is_late_delivery | boolean | True if delivered after estimated date |

### Measures

| Measure | Formula |
|---|---|
| Revenue | SUM(price) |
| Freight | SUM(freight_value) |
| Total Item Value | SUM(price + freight_value) |
| Number of Items | COUNT(*) |
| Number of Orders | COUNT(DISTINCT order_id) |
| Average Freight | AVG(freight_value) |
| Average Delivery Days | AVG(delivery_days) |
| Late Delivery Rate | AVG(is_late_delivery as numeric) |

---

## 7.2 fact_payments

### Purpose

Payment analysis fact table.

### Grain

```text
One row = one payment sequence for one order
```

### Source

```text
olist_order_payments_dataset.csv
```

### Columns

| Column | Type | Description |
|---|---|---|
| payment_key | surrogate key | Technical fact key |
| order_id | degenerate dimension | Source order identifier |
| payment_type_key | foreign key | Links to dim_payment_type |
| payment_sequential | integer | Payment sequence |
| payment_installments | integer | Number of installments |
| payment_value | numeric | Payment amount |

### Measures

| Measure | Formula |
|---|---|
| Total Payment Value | SUM(payment_value) |
| Average Payment Value | AVG(payment_value) |
| Average Installments | AVG(payment_installments) |
| Number of Payments | COUNT(*) |

---

## 7.3 fact_reviews

### Purpose

Customer satisfaction fact table.

### Grain

```text
One row = one review
```

### Source

```text
olist_order_reviews_dataset.csv
```

### Columns

| Column | Type | Description |
|---|---|---|
| review_key | surrogate key | Technical fact key |
| review_id | natural key | Source review identifier |
| order_id | degenerate dimension | Source order identifier |
| review_date_key | foreign key | Links to dim_date |
| review_score | integer | Review score from 1 to 5 |
| has_review_comment | boolean | True if review_comment_message is available |
| review_answer_delay_days | numeric | Days between review creation and answer timestamp |

### Measures

| Measure | Formula |
|---|---|
| Average Review Score | AVG(review_score) |
| Number of Reviews | COUNT(*) |
| Low Review Count | COUNT where review_score <= 2 |
| Review Comment Rate | AVG(has_review_comment as numeric) |
| Average Review Answer Delay | AVG(review_answer_delay_days) |

---

## 8. Key Relationships

```text
fact_order_items.customer_key
→ dim_customer.customer_key

fact_order_items.product_key
→ dim_product.product_key

fact_order_items.seller_key
→ dim_seller.seller_key

fact_order_items.purchase_date_key
→ dim_date.date_key

fact_order_items.order_status_key
→ dim_order_status.order_status_key

fact_order_items.customer_location_key
→ dim_location.location_key

fact_order_items.seller_location_key
→ dim_location.location_key

fact_payments.payment_type_key
→ dim_payment_type.payment_type_key

fact_reviews.review_date_key
→ dim_date.date_key
```

Traceability relationships using source IDs:

```text
fact_order_items.order_id
→ staging_orders.order_id

fact_payments.order_id
→ staging_orders.order_id

fact_reviews.order_id
→ staging_orders.order_id
```

---

## 9. KPI Mapping

| KPI | Source Fact | Dimensions Used |
|---|---|---|
| Total Revenue | fact_order_items | dim_date, dim_product, dim_seller, dim_customer |
| Number of Orders | fact_order_items | dim_date, dim_customer, dim_order_status |
| Average Order Value | fact_order_items | dim_date, dim_customer |
| Revenue by Category | fact_order_items | dim_product |
| Revenue by Month | fact_order_items | dim_date |
| Average Freight | fact_order_items | dim_product, dim_location |
| Average Delivery Days | fact_order_items | dim_date, dim_location |
| Late Delivery Rate | fact_order_items | dim_seller, dim_location, dim_date |
| Payment Method Distribution | fact_payments | dim_payment_type |
| Average Installments | fact_payments | dim_payment_type |
| Average Review Score | fact_reviews | dim_date |
| Low Review Count | fact_reviews | dim_date |

---

## 10. Important Design Decisions

| Topic | Decision |
|---|---|
| Main sales grain | One row per order item |
| Payment grain | One row per payment sequence |
| Review grain | One row per review |
| Location grain | One row per zip code prefix |
| Missing product category | Replace with unknown |
| Geolocation duplicates | Aggregate by zip code prefix |
| Missing delivery dates | Keep delivery metrics null or mark as not delivered |
| Raw order_id in facts | Keep as degenerate dimension for traceability |
| Dashboard source | PostgreSQL warehouse tables, not raw CSV files |

---

## 11. Reusable Pattern to Memorize

For future BI and Data Warehouse projects, repeat this sequence:

```text
Business questions
→ KPIs
→ Source inventory
→ Data dictionary
→ Grain decision
→ Dimensions
→ Facts
→ Relationships
→ SQL validation
→ Dashboard
```

The most important modeling question is always:

```text
What does one row in the fact table represent?
```

For this project, the answer is:

```text
One row = one product item sold inside one order
```
