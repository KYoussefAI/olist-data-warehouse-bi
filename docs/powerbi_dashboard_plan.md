# Power BI Dashboard Plan — Olist Data Warehouse & BI

## 1. Purpose

This document defines the Power BI dashboard structure for the Olist Data Warehouse & BI project.

The objective is to transform the PostgreSQL reporting views into a clear Business Intelligence dashboard that helps analyze sales, customers, products, sellers, logistics, payments, and customer satisfaction.

The dashboard must connect to the PostgreSQL `reporting` schema, not directly to raw CSV files.

---

## 2. Current Data Architecture

```text
Olist CSV files
→ PostgreSQL staging tables
→ PostgreSQL warehouse dimensions and facts
→ PostgreSQL reporting views
→ Power BI dashboard
```

Power BI will mainly use the following reporting views:

```text
reporting.vw_executive_kpi_snapshot
reporting.vw_sales_overview
reporting.vw_revenue_by_month
reporting.vw_revenue_by_category
reporting.vw_customer_geography
reporting.vw_seller_performance
reporting.vw_delivery_performance
reporting.vw_payment_summary
reporting.vw_review_summary
reporting.vw_review_by_category
```

---

## 3. Dashboard Pages

The first version of the Power BI dashboard will contain five pages:

```text
1. Executive Overview
2. Sales & Product Performance
3. Customer Geography
4. Logistics & Seller Performance
5. Payments & Reviews
```

This structure keeps the dashboard professional and easy to understand.

---

## 4. Page 1 — Executive Overview

### Purpose

Give a quick business summary of the marketplace performance.

### Main View

```text
reporting.vw_executive_kpi_snapshot
```

### KPI Cards

| KPI | Source Column |
|---|---|
| Total Orders | total_orders |
| Total Items | total_items |
| Total Revenue | total_revenue |
| Total Freight | total_freight |
| Total Item Value | total_item_value |
| Average Item Price | average_item_price |
| Average Delivery Days | average_delivery_days |
| Late Delivery Rate | late_delivery_rate_percent |
| Total Reviews | total_reviews |
| Average Review Score | average_review_score |
| Total Payments | total_payments |
| Total Payment Value | total_payment_value |

### Recommended Visuals

| Visual | Data Source |
|---|---|
| KPI cards | vw_executive_kpi_snapshot |
| Revenue by month line chart | vw_revenue_by_month |
| Top categories bar chart | vw_revenue_by_category |
| Payment method donut chart | vw_payment_summary |
| Review score distribution bar chart | vw_review_summary |

### Business Questions Answered

- What is the total revenue?
- How many orders and items were sold?
- How good is the delivery performance?
- What is the average customer satisfaction?
- Which categories drive the most revenue?

---

## 5. Page 2 — Sales & Product Performance

### Purpose

Analyze revenue, order volume, item sales, and product category performance.

### Main Views

```text
reporting.vw_sales_overview
reporting.vw_revenue_by_month
reporting.vw_revenue_by_category
```

### Recommended Visuals

| Visual | Description |
|---|---|
| Line chart | Revenue by year and month |
| Clustered bar chart | Revenue by product category |
| Table | Top categories with revenue, items, orders, average freight |
| KPI cards | Total revenue, total orders, total items, average item price |
| Slicer | Year |
| Slicer | Product category |

### Important Fields

From `vw_revenue_by_month`:

```text
year
month
month_name
total_orders
total_items
total_revenue
total_freight
average_item_price
```

From `vw_revenue_by_category`:

```text
product_category
total_orders
total_items
total_revenue
total_freight
average_item_price
average_freight_value
```

### Business Questions Answered

- Which months generated the most revenue?
- Which categories generate the most revenue?
- Which categories sell the most items?
- Which categories have high freight costs?

---

## 6. Page 3 — Customer Geography

### Purpose

Analyze customers, orders, revenue, and delivery performance by location.

### Main View

```text
reporting.vw_customer_geography
```

### Recommended Visuals

| Visual | Description |
|---|---|
| Filled map or map visual | Revenue or orders by customer state |
| Bar chart | Top customer states by revenue |
| Table | City-level customer performance |
| KPI cards | Total customers, total orders, total revenue |
| Slicer | Customer state |
| Slicer | Customer city |

### Important Fields

```text
customer_state
customer_city
total_customers
total_orders
total_items
total_revenue
total_freight
average_delivery_days
late_delivery_rate_percent
```

### Business Questions Answered

- Where are customers located?
- Which states generate the most revenue?
- Which cities have the most orders?
- Which locations have higher delivery delays?

---

## 7. Page 4 — Logistics & Seller Performance

### Purpose

Understand delivery performance and seller contribution.

### Main Views

```text
reporting.vw_delivery_performance
reporting.vw_seller_performance
```

### Recommended Visuals

| Visual | Description |
|---|---|
| KPI cards | Average delivery days, late delivery rate, late items |
| Bar chart | Late delivery rate by order status |
| Table | Seller ranking by revenue |
| Bar chart | Top sellers by total revenue |
| Scatter plot | Seller revenue vs late delivery rate |
| Slicer | Seller state |
| Slicer | Order status |

### Important Fields

From `vw_delivery_performance`:

```text
order_status
total_items
items_with_delivery_date
items_without_delivery_date
average_delivery_days
late_items
on_time_items
late_delivery_rate_percent
```

From `vw_seller_performance`:

```text
seller_id
seller_city
seller_state
total_orders
total_items
total_revenue
total_freight
average_delivery_days
late_items
late_delivery_rate_percent
```

### Business Questions Answered

- What is the average delivery duration?
- What percentage of deliveries are late?
- Which sellers generate the most revenue?
- Which sellers are linked to frequent delays?

---

## 8. Page 5 — Payments & Reviews

### Purpose

Analyze payment behavior and customer satisfaction.

### Main Views

```text
reporting.vw_payment_summary
reporting.vw_review_summary
reporting.vw_review_by_category
```

### Recommended Visuals

| Visual | Description |
|---|---|
| Donut chart | Payment method distribution |
| Bar chart | Payment value by payment type |
| KPI cards | Total payments, total payment value, average payment value |
| Bar chart | Review score distribution |
| Table | Average review score by category |
| Bar chart | Low review rate by category |

### Important Fields

From `vw_payment_summary`:

```text
payment_type
total_payments
total_payment_value
average_payment_value
average_installments
```

From `vw_review_summary`:

```text
review_score
total_reviews
low_review_count
average_review_answer_delay_days
review_comment_rate_percent
```

From `vw_review_by_category`:

```text
product_category
total_reviews
average_review_score
low_review_count
low_review_rate_percent
```

### Business Questions Answered

- Which payment methods are most used?
- Which payment methods generate the most payment value?
- What is the average review score?
- Which categories have the lowest satisfaction?

---

## 9. Recommended Dashboard Layout

### Top Area

Use KPI cards for the most important metrics.

Example:

```text
Total Revenue | Total Orders | Average Delivery Days | Late Delivery Rate | Average Review Score
```

### Middle Area

Use trend and comparison visuals.

Example:

```text
Revenue by Month
Revenue by Category
Orders by State
```

### Bottom Area

Use detail tables.

Example:

```text
Top Sellers
Category Performance
Payment Summary
Review by Category
```

---

## 10. Power BI Connection Plan

### Connection Type

Use PostgreSQL database connection.

### Database

```text
olist_dw
```

### Host

```text
localhost
```

### Port

```text
5432
```

### User

```text
youssef
```

### Schema to use

```text
reporting
```

### Recommended Tables/Views to Import

```text
vw_executive_kpi_snapshot
vw_revenue_by_month
vw_revenue_by_category
vw_customer_geography
vw_seller_performance
vw_delivery_performance
vw_payment_summary
vw_review_summary
vw_review_by_category
vw_sales_overview
```

For the first dashboard version, start with:

```text
vw_executive_kpi_snapshot
vw_revenue_by_month
vw_revenue_by_category
vw_customer_geography
vw_seller_performance
vw_delivery_performance
vw_payment_summary
vw_review_summary
vw_review_by_category
```

Use `vw_sales_overview` only if you need item-level detailed analysis.

---

## 11. Reference KPIs to Validate in Power BI

Power BI values should match the SQL validation values:

| KPI | Expected Value |
|---|---:|
| Total Orders | 98,666 |
| Total Items | 112,650 |
| Total Revenue | 13,591,643.70 |
| Total Freight | 2,251,909.54 |
| Total Item Value | 15,843,553.24 |
| Average Item Price | 120.65 |
| Average Delivery Days | 12.47 |
| Late Delivery Rate | 7.91% |
| Total Reviews | 99,224 |
| Average Review Score | 4.09 |
| Low Review Count | 14,575 |
| Total Payments | 103,886 |
| Total Payment Value | 16,008,872.12 |
| Average Payment Value | 154.10 |

If Power BI displays different values, the problem is likely caused by aggregation settings, duplicate relationships, or filtering.

---

## 12. Dashboard Design Rules

Use simple and professional design:

- Keep one main topic per page.
- Use clear KPI cards.
- Do not overload the dashboard with too many visuals.
- Use slicers for year, state, category, seller state, and payment type.
- Use consistent number formatting.
- Use revenue formatting with two decimals.
- Use percentages for late delivery rate and low review rate.
- Use tables for detailed ranking.
- Use charts for trends and comparisons.

---

## 13. Minimum Viable Dashboard Version

The first version should include:

```text
Page 1 — Executive Overview
Page 2 — Sales & Product Performance
Page 3 — Logistics & Seller Performance
```

Then add:

```text
Page 4 — Customer Geography
Page 5 — Payments & Reviews
```

This avoids spending too much time on visual design before validating the dashboard logic.

---

## 14. Reusable Pattern to Memorize

For any BI project, repeat this process:

```text
Business questions
→ KPIs
→ Data warehouse model
→ Reporting views
→ Dashboard pages
→ KPI validation
→ Final storytelling
```

The dashboard should not be a random collection of charts.

It should answer business questions clearly.
