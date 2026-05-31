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

## Screenshots

### Vue globale des ventes

![Vue globale des ventes](../docs/images/dashboard/dashboard_sales_overview.png)

### Analyse des paiements

![Analyse des paiements](../docs/images/dashboard/dashboard_payment_analysis.png)

### Satisfaction client

![Satisfaction client](../docs/images/dashboard/dashboard_customer_satisfaction.png)

### Performance logistique

![Performance logistique](../docs/images/dashboard/dashboard_delivery_performance.png)

### Tunnel marketing

![Tunnel marketing](../docs/images/dashboard/dashboard_marketing_funnel.png)

### Contrôles qualité

![Contrôles qualité](../docs/images/dashboard/dashboard_quality_checks.png)
