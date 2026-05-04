# Business Questions — Olist Data Warehouse & BI

## 1. Project Context

This project simulates a Business Intelligence request for an e-commerce marketplace.

The objective is to transform raw operational Olist CSV files into a clean analytical Data Warehouse that can be used to answer business questions through SQL and Power BI dashboards.

---

## 2. Main Business Goal

Help the business team understand the performance of the Olist marketplace across sales, customers, sellers, products, logistics, payments, and customer satisfaction.

---

## 3. Business Domains and Questions

### 3.1 Sales Analysis

Questions:

- What is the total revenue?
- How many orders were placed?
- What is the average order value?
- Which months generated the highest revenue?
- Which product categories generate the most revenue?

Expected KPIs:

- Total revenue
- Number of orders
- Average order value
- Revenue by month
- Revenue by product category

---

### 3.2 Product Analysis

Questions:

- Which product categories sell the most?
- Which categories generate the highest revenue?
- Which products are associated with high freight cost?

Expected KPIs:

- Revenue by category
- Number of items sold by category
- Average freight value by category

---

### 3.3 Customer Analysis

Questions:

- Where are customers located?
- Which states and cities generate the most orders?
- Which regions generate the most revenue?

Expected KPIs:

- Number of customers
- Orders by customer state
- Revenue by customer state
- Top customer cities

---

### 3.4 Seller Analysis

Questions:

- Which sellers generate the most revenue?
- Which sellers have the highest number of orders?
- Which sellers are associated with frequent delivery delays?

Expected KPIs:

- Number of sellers
- Revenue by seller
- Orders by seller
- Delay rate by seller

---

### 3.5 Logistics Analysis

Questions:

- What is the average delivery time?
- Which orders were delivered late?
- Which states have the highest delay rate?
- Does freight cost vary by region or product category?

Expected KPIs:

- Average delivery duration
- Late delivery rate
- Average freight value
- Delay rate by state

---

### 3.6 Customer Satisfaction Analysis

Questions:

- What is the average review score?
- Does review score decrease when delivery is late?
- Which categories receive the best and worst reviews?

Expected KPIs:

- Average review score
- Review score by category
- Review score by delivery status
- Low review count

---

### 3.7 Payment Analysis

Questions:

- Which payment methods are most used?
- Does payment in installments influence order value?
- What is the average payment value by payment type?

Expected KPIs:

- Payment method distribution
- Average payment value
- Average number of installments
- Revenue by payment type

---

## 4. Initial KPI List

| KPI | Description |
|---|---|
| Total Revenue | Sum of item price values |
| Total Freight | Sum of freight values |
| Number of Orders | Count of unique orders |
| Number of Customers | Count of unique customers |
| Number of Sellers | Count of unique sellers |
| Average Order Value | Revenue divided by number of orders |
| Average Delivery Time | Difference between purchase date and delivered date |
| Late Delivery Rate | Percentage of orders delivered after estimated date |
| Average Review Score | Average customer review score |
| Revenue by Category | Revenue grouped by product category |
| Revenue by Month | Revenue grouped by year and month |
| Payment Type Distribution | Number of payments by payment type |

---

## 5. Data Warehouse Decision

The dashboard must not query raw CSV files directly.

The dashboard will query analytical tables from PostgreSQL Data Warehouse tables.

Target structure:

```text
Raw CSV files
→ Staging tables
→ Dimension tables
→ Fact tables
→ Power BI dashboard