# Streamlit dashboard

This dashboard connects directly to the PostgreSQL Data Warehouse and reads the analytical marts created by the ELT pipeline.

## Run locally

From the repository root:

```bash
pip install -r requirements.txt
python -m src.run_etl --step all
streamlit run dashboard/app.py
```

## Required database objects

The dashboard expects these objects to exist:

```text
marts.sales_overview
marts.sales_by_category
marts.payment_analysis
marts.customer_satisfaction
marts.delivery_performance
marts.marketing_funnel
```

If a view is missing, run:

```bash
python -m src.run_etl --step marts
```

## Environment

The app reads the same `DATABASE_URL` used by the ETL:

```text
DATABASE_URL=postgresql+psycopg2://olist:olist@localhost:5432/olist_dw
```
