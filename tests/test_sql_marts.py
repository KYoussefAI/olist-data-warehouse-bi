from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SQL = (ROOT / "sql" / "01_create_marts.sql").read_text(encoding="utf-8").lower()


def test_marts_views_are_defined():
    expected_views = [
        "marts.sales_overview",
        "marts.sales_by_category",
        "marts.payment_analysis",
        "marts.customer_satisfaction",
        "marts.delivery_performance",
        "marts.marketing_funnel",
    ]
    for view in expected_views:
        assert view in SQL


def test_sql_uses_create_or_replace_view():
    assert "create or replace view" in SQL
