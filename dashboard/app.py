from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Iterable

import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.engine.url import make_url
from sqlalchemy.exc import SQLAlchemyError

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://olist:olist@localhost:5432/olist_dw",
)

st.set_page_config(
    page_title="Olist Data Warehouse BI",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .block-container {padding-top: 1.4rem; padding-bottom: 2rem;}
    [data-testid="stMetricValue"] {font-size: 1.75rem;}
    div[data-testid="stDataFrame"] {border: 1px solid #e5e7eb; border-radius: 10px;}
    .small-caption {font-size: 0.86rem; color: #64748b;}
    </style>
    """,
    unsafe_allow_html=True,
)


@dataclass(frozen=True)
class DashboardFilters:
    years: list[int]


@st.cache_resource(show_spinner=False)
def get_engine() -> Engine:
    return create_engine(DATABASE_URL, pool_pre_ping=True, future=True)


@st.cache_data(ttl=300, show_spinner=False)
def run_query(sql: str, params: dict | None = None) -> pd.DataFrame:
    engine = get_engine()
    with engine.connect() as conn:
        return pd.read_sql_query(text(sql), conn, params=params or {})


def safe_query(sql: str, params: dict | None = None) -> pd.DataFrame:
    try:
        return run_query(sql, params)
    except SQLAlchemyError as exc:
        st.error("Impossible de lire les données PostgreSQL. Vérifiez que Docker/PostgreSQL est lancé et que le pipeline ELT a été exécuté.")
        with st.expander("Détail technique"):
            st.code(str(exc))
        return pd.DataFrame()


def format_brl(value: float | int | None) -> str:
    if value is None or pd.isna(value):
        return "R$ 0"
    return f"R$ {value:,.0f}".replace(",", " ")


def format_pct(value: float | int | None) -> str:
    if value is None or pd.isna(value):
        return "0.0 %"
    return f"{value * 100:.1f} %"


def as_period(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or not {"year_number", "month_number"}.issubset(df.columns):
        return df
    out = df.copy()
    out["period"] = pd.to_datetime(
        out["year_number"].astype(int).astype(str) + "-" + out["month_number"].astype(int).astype(str) + "-01"
    )
    return out.sort_values("period")


def year_filter_clause(alias: str = "") -> str:
    column = f"{alias}.year_number" if alias else "year_number"
    return f"WHERE {column} = ANY(:years)" if st.session_state.get("selected_years") else ""


def params() -> dict:
    years = st.session_state.get("selected_years") or []
    return {"years": years}


def load_available_years() -> list[int]:
    df = safe_query(
        """
        SELECT DISTINCT year_number
        FROM marts.sales_overview
        WHERE year_number IS NOT NULL
        ORDER BY year_number
        """
    )
    if df.empty:
        return []
    return [int(x) for x in df["year_number"].dropna().tolist()]


def kpi_row(items: Iterable[tuple[str, str, str | None]]) -> None:
    items = list(items)
    cols = st.columns(len(items))
    for col, (label, value, help_text) in zip(cols, items):
        col.metric(label=label, value=value, help=help_text)


def show_empty_state(subject: str) -> None:
    st.warning(
        f"Aucune donnee disponible pour {subject}. Verifiez que l'ETL et la creation des vues marts ont bien ete executes."
    )


def database_target() -> str:
    try:
        url = make_url(DATABASE_URL)
        host = url.host or "localhost"
        database = url.database or "unknown"
        return f"{host} / {database}"
    except Exception:
        return "configuration DATABASE_URL non lisible"


def sidebar() -> str:
    st.sidebar.title("Olist BI")
    st.sidebar.caption("Dashboard Streamlit connecté aux vues marts PostgreSQL.")
    st.sidebar.info(f"Base active: `{database_target()}`")

    years = load_available_years()
    if years:
        selected = st.sidebar.multiselect(
            "Années",
            options=years,
            default=years,
            help="Filtre global appliqué aux pages temporelles.",
        )
    else:
        selected = []
    st.session_state["selected_years"] = selected

    page = st.sidebar.radio(
        "Page",
        [
            "Vue globale des ventes",
            "Analyse des paiements",
            "Satisfaction client",
            "Performance logistique",
            "Tunnel marketing",
            "Contrôles qualité",
        ],
    )
    st.sidebar.markdown("---")
    st.sidebar.markdown("<span class='small-caption'>Run: `streamlit run dashboard/app.py`</span>", unsafe_allow_html=True)
    return page


def page_sales() -> None:
    st.title("Vue globale des ventes")
    st.caption("Chiffre d'affaires, volumes de commandes et catégories produits les plus contributrices.")

    df = safe_query(
        f"""
        SELECT
            year_number,
            month_number,
            month_name,
            order_status,
            order_count,
            item_count,
            gross_revenue
        FROM marts.sales_overview
        {year_filter_clause()}
        ORDER BY year_number, month_number, order_status
        """,
        params(),
    )
    df = as_period(df)
    if df.empty:
        show_empty_state("la vue globale des ventes")
        return

    total_revenue = float(df["gross_revenue"].fillna(0).sum())
    total_orders = int(df["order_count"].fillna(0).sum())
    total_items = int(df["item_count"].fillna(0).sum())
    avg_order_value = total_revenue / total_orders if total_orders else 0

    kpi_row(
        [
            ("Revenu brut", format_brl(total_revenue), None),
            ("Commandes", f"{total_orders:,}".replace(",", " "), None),
            ("Articles vendus", f"{total_items:,}".replace(",", " "), None),
            ("Panier moyen", format_brl(avg_order_value), None),
        ]
    )

    monthly = df.groupby("period", as_index=False).agg(
        gross_revenue=("gross_revenue", "sum"),
        order_count=("order_count", "sum"),
        item_count=("item_count", "sum"),
    )
    status = df.groupby("order_status", as_index=False).agg(order_count=("order_count", "sum"))

    left, right = st.columns([2, 1])
    with left:
        fig = px.line(monthly, x="period", y="gross_revenue", markers=True, title="Revenu mensuel")
        fig.update_layout(xaxis_title="Mois", yaxis_title="Revenu brut")
        st.plotly_chart(fig, use_container_width=True)
    with right:
        fig = px.pie(status, values="order_count", names="order_status", title="Commandes par statut")
        st.plotly_chart(fig, use_container_width=True)

    cat = safe_query(
        """
        SELECT product_category, item_count, order_count, gross_revenue
        FROM marts.sales_by_category
        ORDER BY gross_revenue DESC
        LIMIT 15
        """
    )
    if not cat.empty:
        fig = px.bar(
            cat.sort_values("gross_revenue"),
            x="gross_revenue",
            y="product_category",
            orientation="h",
            title="Top 15 catégories par revenu brut",
        )
        fig.update_layout(xaxis_title="Revenu brut", yaxis_title="Catégorie")
        st.plotly_chart(fig, use_container_width=True)
    else:
        show_empty_state("les categories produits")

    with st.expander("Voir les données agrégées"):
        st.dataframe(monthly, use_container_width=True)


def page_payments() -> None:
    st.title("Analyse des paiements")
    st.caption("Modes de paiement, valeur totale et distribution des versements.")

    df = safe_query(
        f"""
        SELECT
            year_number,
            month_number,
            month_name,
            payment_type,
            payment_installments,
            payment_count,
            total_payment_value
        FROM marts.payment_analysis
        {year_filter_clause()}
        ORDER BY year_number, month_number, payment_type, payment_installments
        """,
        params(),
    )
    df = as_period(df)
    if df.empty:
        show_empty_state("l'analyse des paiements")
        return

    total_value = float(df["total_payment_value"].fillna(0).sum())
    total_count = int(df["payment_count"].fillna(0).sum())
    avg_payment = total_value / total_count if total_count else 0
    installments_avg = float((df["payment_installments"].fillna(0) * df["payment_count"].fillna(0)).sum() / total_count) if total_count else 0

    kpi_row(
        [
            ("Valeur totale payee", format_brl(total_value), None),
            ("Paiements", f"{total_count:,}".replace(",", " "), None),
            ("Versements moyens", f"{installments_avg:.2f}", None),
        ]
    )

    by_type = df.groupby("payment_type", as_index=False).agg(
        total_payment_value=("total_payment_value", "sum"),
        payment_count=("payment_count", "sum"),
    ).sort_values("total_payment_value", ascending=False)

    left, right = st.columns(2)
    with left:
        fig = px.bar(by_type, x="payment_type", y="total_payment_value", title="Valeur par mode de paiement")
        fig.update_layout(xaxis_title="Mode", yaxis_title="Valeur totale")
        st.plotly_chart(fig, use_container_width=True)
    with right:
        fig = px.pie(by_type, values="payment_count", names="payment_type", title="Nombre de paiements par mode")
        st.plotly_chart(fig, use_container_width=True)

    installments = df.groupby("payment_installments", as_index=False).agg(payment_count=("payment_count", "sum"))
    fig = px.bar(installments, x="payment_installments", y="payment_count", title="Distribution des versements")
    fig.update_layout(xaxis_title="Nombre de versements", yaxis_title="Nombre de paiements")
    st.plotly_chart(fig, use_container_width=True)


def page_satisfaction() -> None:
    st.title("Satisfaction client")
    st.caption("Scores d'avis, évolution mensuelle et part d'avis négatifs.")

    df = safe_query(
        f"""
        SELECT
            year_number,
            month_number,
            month_name,
            review_score,
            review_count
        FROM marts.customer_satisfaction
        {year_filter_clause()}
        ORDER BY year_number, month_number, review_score
        """,
        params(),
    )
    df = as_period(df)
    if df.empty:
        show_empty_state("la satisfaction client")
        return

    total_reviews = int(df["review_count"].fillna(0).sum())
    weighted_score = (df["review_score"] * df["review_count"]).sum() / total_reviews if total_reviews else 0
    negative = int(df.loc[df["review_score"].isin([1, 2]), "review_count"].fillna(0).sum())
    positive = int(df.loc[df["review_score"].isin([4, 5]), "review_count"].fillna(0).sum())

    kpi_row(
        [
            ("Avis", f"{total_reviews:,}".replace(",", " "), None),
            ("Score moyen", f"{weighted_score:.2f} / 5", None),
            ("Avis negatifs", format_pct(negative / total_reviews if total_reviews else 0), None),
            ("Avis positifs", format_pct(positive / total_reviews if total_reviews else 0), None),
        ]
    )

    monthly = df.groupby("period", as_index=False).apply(
        lambda x: pd.Series({
            "avg_score": (x["review_score"] * x["review_count"]).sum() / x["review_count"].sum(),
            "review_count": x["review_count"].sum(),
        })
    ).reset_index(drop=True)

    distribution = df.groupby("review_score", as_index=False).agg(review_count=("review_count", "sum"))

    left, right = st.columns([2, 1])
    with left:
        fig = px.line(monthly, x="period", y="avg_score", markers=True, title="Score moyen mensuel")
        fig.update_layout(xaxis_title="Mois", yaxis_title="Score moyen")
        st.plotly_chart(fig, use_container_width=True)
    with right:
        fig = px.bar(distribution, x="review_score", y="review_count", title="Distribution des scores")
        fig.update_layout(xaxis_title="Score", yaxis_title="Nombre d'avis")
        st.plotly_chart(fig, use_container_width=True)


def page_delivery() -> None:
    st.title("Performance logistique")
    st.caption("Délai de livraison et écart moyen avec la date estimée.")

    df = safe_query(
        f"""
        SELECT
            year_number,
            month_number,
            month_name,
            order_status,
            delivered_orders,
            avg_days_purchase_to_delivery,
            avg_days_vs_estimate,
            on_time_rate
        FROM marts.delivery_performance
        {year_filter_clause()}
        ORDER BY year_number, month_number, order_status
        """,
        params(),
    )
    df = as_period(df)
    if df.empty:
        show_empty_state("la performance logistique")
        return

    total_delivered = int(df["delivered_orders"].fillna(0).sum())
    avg_delivery = float((df["avg_days_purchase_to_delivery"].fillna(0) * df["delivered_orders"].fillna(0)).sum() / total_delivered) if total_delivered else 0
    avg_vs_estimate = float((df["avg_days_vs_estimate"].fillna(0) * df["delivered_orders"].fillna(0)).sum() / total_delivered) if total_delivered else 0
    on_time_rate = float((df["on_time_rate"].fillna(0) * df["delivered_orders"].fillna(0)).sum() / total_delivered) if total_delivered and "on_time_rate" in df else 0

    kpi_row(
        [
            ("Commandes livrees", f"{total_delivered:,}".replace(",", " "), None),
            ("Delai moyen", f"{avg_delivery:.1f} jours", None),
            ("Ecart vs estimation", f"{avg_vs_estimate:.1f} jours", None),
            ("Livrees a temps", format_pct(on_time_rate), None),
        ]
    )

    monthly = df.groupby("period", as_index=False).apply(
        lambda x: pd.Series({
            "avg_days_purchase_to_delivery": (x["avg_days_purchase_to_delivery"].fillna(0) * x["delivered_orders"].fillna(0)).sum() / x["delivered_orders"].fillna(0).sum(),
            "avg_days_vs_estimate": (x["avg_days_vs_estimate"].fillna(0) * x["delivered_orders"].fillna(0)).sum() / x["delivered_orders"].fillna(0).sum(),
        })
    ).reset_index(drop=True)

    fig = px.line(
        monthly,
        x="period",
        y=["avg_days_purchase_to_delivery", "avg_days_vs_estimate"],
        markers=True,
        title="Évolution des délais logistiques",
    )
    fig.update_layout(xaxis_title="Mois", yaxis_title="Jours", legend_title="Indicateur")
    st.plotly_chart(fig, use_container_width=True)


def page_marketing() -> None:
    st.title("Tunnel marketing")
    st.caption("Leads qualifiés, deals conclus et taux de conversion par canal.")

    df = safe_query(
        f"""
        SELECT
            year_number,
            month_number,
            month_name,
            marketing_origin,
            mql_count,
            won_deal_count,
            declared_monthly_revenue_sum,
            conversion_rate
        FROM marts.marketing_funnel
        {year_filter_clause()}
        ORDER BY year_number, month_number, marketing_origin
        """,
        params(),
    )
    df = as_period(df)
    if df.empty:
        show_empty_state("le tunnel marketing")
        return

    total_leads = int(df["mql_count"].fillna(0).sum())
    total_deals = int(df["won_deal_count"].fillna(0).sum())
    revenue = float(df["declared_monthly_revenue_sum"].fillna(0).sum())
    conversion = total_deals / total_leads if total_leads else 0

    kpi_row(
        [
            ("MQL", f"{total_leads:,}".replace(",", " "), None),
            ("Deals gagnes", f"{total_deals:,}".replace(",", " "), None),
            ("Conversion", format_pct(conversion), None),
            ("Revenu declare", format_brl(revenue), None),
        ]
    )

    by_origin = df.groupby("marketing_origin", as_index=False).agg(
        mql_count=("mql_count", "sum"),
        won_deal_count=("won_deal_count", "sum"),
        declared_monthly_revenue_sum=("declared_monthly_revenue_sum", "sum"),
    )
    by_origin["conversion_rate"] = by_origin["won_deal_count"] / by_origin["mql_count"].replace(0, pd.NA)
    by_origin = by_origin.sort_values("mql_count", ascending=False).head(15)

    left, right = st.columns(2)
    with left:
        fig = px.bar(by_origin, x="marketing_origin", y=["mql_count", "won_deal_count"], barmode="group", title="MQL vs deals par origine")
        fig.update_layout(xaxis_title="Origine", yaxis_title="Volume")
        st.plotly_chart(fig, use_container_width=True)
    with right:
        fig = px.bar(by_origin, x="marketing_origin", y="conversion_rate", title="Taux de conversion par origine")
        fig.update_layout(xaxis_title="Origine", yaxis_title="Conversion")
        st.plotly_chart(fig, use_container_width=True)

    with st.expander("Table marketing par origine"):
        st.dataframe(by_origin, use_container_width=True)


def page_quality() -> None:
    st.title("Contrôles qualité")
    st.caption("Diagnostics rapides sur les tables principales et les vues marts.")

    checks = safe_query(
        """
        SELECT 'raw_orders_loaded' AS check_name, COUNT(*)::TEXT AS value, (COUNT(*) > 0) AS passed
        FROM raw.olist_orders
        UNION ALL
        SELECT 'dwh_fact_orders_loaded', COUNT(*)::TEXT, (COUNT(*) > 0)
        FROM dwh.fact_orders
        UNION ALL
        SELECT 'fact_order_items_missing_order_key', COUNT(*)::TEXT, (COUNT(*) = 0)
        FROM dwh.fact_order_items WHERE order_key IS NULL
        UNION ALL
        SELECT 'fact_order_items_missing_product_key', COUNT(*)::TEXT, (COUNT(*) = 0)
        FROM dwh.fact_order_items WHERE product_key IS NULL
        UNION ALL
        SELECT 'fact_order_items_missing_seller_key', COUNT(*)::TEXT, (COUNT(*) = 0)
        FROM dwh.fact_order_items WHERE seller_key IS NULL
        UNION ALL
        SELECT 'fact_payments_missing_order_key', COUNT(*)::TEXT, (COUNT(*) = 0)
        FROM dwh.fact_payments WHERE order_key IS NULL
        UNION ALL
        SELECT 'reviews_outside_1_5', COUNT(*)::TEXT, (COUNT(*) = 0)
        FROM dwh.fact_reviews WHERE review_score NOT BETWEEN 1 AND 5
        UNION ALL
        SELECT 'marts_sales_overview_loaded', COUNT(*)::TEXT, (COUNT(*) > 0)
        FROM marts.sales_overview
        UNION ALL
        SELECT 'marts_sales_by_category_loaded', COUNT(*)::TEXT, (COUNT(*) > 0)
        FROM marts.sales_by_category
        """
    )
    if checks.empty:
        show_empty_state("les controles qualite")
        return

    passed = int(checks["passed"].sum())
    total = len(checks)
    c1, c2, c3 = st.columns(3)
    c1.metric("Contrôles", total)
    c2.metric("Réussis", passed)
    c3.metric("Échecs", total - passed)

    checks["status"] = checks["passed"].map({True: "PASS", False: "FAIL"})
    st.dataframe(checks[["status", "check_name", "value"]], use_container_width=True)


def main() -> None:
    page = sidebar()
    if page == "Vue globale des ventes":
        page_sales()
    elif page == "Analyse des paiements":
        page_payments()
    elif page == "Satisfaction client":
        page_satisfaction()
    elif page == "Performance logistique":
        page_delivery()
    elif page == "Tunnel marketing":
        page_marketing()
    elif page == "Contrôles qualité":
        page_quality()


if __name__ == "__main__":
    main()
