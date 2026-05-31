from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_PATH = ROOT / "dashboard" / "app.py"


def test_dashboard_app_exists():
    assert APP_PATH.exists()


def test_dashboard_app_has_reusable_helpers():
    source = APP_PATH.read_text(encoding="utf-8")
    for helper in [
        "page_header",
        "metric_grid",
        "section_title",
        "standard_chart_layout",
    ]:
        assert f"def {helper}" in source


def test_dashboard_app_has_navigation_mapping_and_apply_button():
    source = APP_PATH.read_text(encoding="utf-8")
    assert "NAV_OPTIONS = {" in source
    for label in [
        "Executive · Ventes",
        "Commerce · Paiements",
        "Commerce · Satisfaction",
        "Operations · Logistique",
        "Growth · Marketing",
        "Data Quality · Contrôles",
    ]:
        assert label in source
    assert 'selectbox("Navigation"' in source
    assert "Afficher la page" not in source
    assert "st.rerun" not in source
    assert "active_page" not in source
    assert "pending_page_label" not in source


def test_sales_page_does_not_use_pie_chart():
    source = APP_PATH.read_text(encoding="utf-8")
    sales_start = source.index("def page_sales")
    payments_start = source.index("def page_payments")
    sales_source = source[sales_start:payments_start]
    assert "px.pie" not in sales_source
