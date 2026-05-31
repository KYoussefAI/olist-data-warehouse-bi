from __future__ import annotations

import os
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

PAGE_CONFIG = {
    "Executive · Ventes": {
        "title": "Vue globale des ventes",
        "subtitle": "Suivi executive des revenus, commandes, statuts et categories prioritaires.",
        "handler": "page_sales",
    },
    "Commerce · Paiements": {
        "title": "Analyse des paiements",
        "subtitle": "Lecture business des montants, modes de paiement et comportements de versement.",
        "handler": "page_payments",
    },
    "Commerce · Satisfaction": {
        "title": "Satisfaction client",
        "subtitle": "Synthese des avis clients pour suivre la perception et les signaux de friction.",
        "handler": "page_satisfaction",
    },
    "Operations · Logistique": {
        "title": "Performance logistique",
        "subtitle": "Pilotage des delais de livraison, des ecarts a la promesse et du taux a temps.",
        "handler": "page_delivery",
    },
    "Growth · Marketing": {
        "title": "Tunnel marketing",
        "subtitle": "Vue funnel des leads qualifies, deals signes et revenus declares par origine.",
        "handler": "page_marketing",
    },
    "Data Quality · Contrôles": {
        "title": "Contrôles qualité",
        "subtitle": "Verification des chargements critiques et des controles de coherence marts/DWH.",
        "handler": "page_quality",
    },
}

NAV_OPTIONS = {
    "Executive · Ventes": "sales",
    "Commerce · Paiements": "payments",
    "Commerce · Satisfaction": "satisfaction",
    "Operations · Logistique": "delivery",
    "Growth · Marketing": "marketing",
    "Data Quality · Contrôles": "quality",
}

PLOTLY_TEMPLATE = "plotly_white"
CHART_HEIGHT = 340
ACCENT = "#0F766E"
ACCENT_LIGHT = "#CCFBF1"
TEXT_MUTED = "#64748B"
BORDER = "#E2E8F0"
SURFACE = "#FFFFFF"
SURFACE_ALT = "#F8FAFC"

st.set_page_config(
    page_title="Olist BI Dashboard",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    f"""
    <style>
    .stApp {{
        background: linear-gradient(180deg, #F8FAFC 0%, #EEF4F7 100%);
    }}
    .block-container {{
        padding-top: 1.2rem;
        padding-bottom: 2rem;
        max-width: 1380px;
    }}
    [data-testid="stSidebar"] {{
        background: #F8FAFC;
        border-right: 1px solid {BORDER};
    }}
    .sidebar-card {{
        background: {SURFACE};
        border: 1px solid {BORDER};
        border-radius: 14px;
        padding: 0.9rem 1rem;
        margin: 0.25rem 0 1rem 0;
    }}
    .page-header {{
        background: {SURFACE};
        border: 1px solid {BORDER};
        border-radius: 18px;
        padding: 1.25rem 1.35rem;
        margin-bottom: 1.1rem;
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
    }}
    .page-header-top {{
        display: flex;
        justify-content: space-between;
        gap: 1rem;
        align-items: flex-start;
    }}
    .page-title {{
        margin: 0;
        font-size: 1.8rem;
        font-weight: 700;
        color: #0F172A;
    }}
    .page-subtitle {{
        margin: 0.45rem 0 0 0;
        color: {TEXT_MUTED};
        font-size: 0.97rem;
        line-height: 1.5;
    }}
    .db-badge {{
        display: inline-flex;
        align-items: center;
        white-space: nowrap;
        background: {SURFACE_ALT};
        border: 1px solid {BORDER};
        border-radius: 999px;
        padding: 0.35rem 0.75rem;
        color: #0F172A;
        font-size: 0.82rem;
        font-weight: 600;
    }}
    .section-title {{
        margin: 1.15rem 0 0.35rem 0;
        font-size: 1.02rem;
        font-weight: 700;
        color: #0F172A;
    }}
    .section-description {{
        margin: 0 0 0.8rem 0;
        color: {TEXT_MUTED};
        font-size: 0.9rem;
    }}
    .metric-card {{
        background: {SURFACE};
        border: 1px solid {BORDER};
        border-radius: 16px;
        padding: 1rem 1.05rem;
        min-height: 122px;
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
    }}
    .metric-label {{
        color: {TEXT_MUTED};
        font-size: 0.84rem;
        font-weight: 600;
        margin-bottom: 0.55rem;
        text-transform: uppercase;
        letter-spacing: 0.03em;
    }}
    .metric-value {{
        color: #0F172A;
        font-size: 1.7rem;
        font-weight: 700;
        line-height: 1.15;
    }}
    .metric-help {{
        margin-top: 0.6rem;
        color: {TEXT_MUTED};
        font-size: 0.82rem;
    }}
    .panel-card {{
        background: {SURFACE};
        border: 1px solid {BORDER};
        border-radius: 18px;
        padding: 0.9rem 1rem 0.35rem 1rem;
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
    }}
    .small-caption {{
        color: {TEXT_MUTED};
        font-size: 0.82rem;
    }}
    .quality-table {{
        width: 100%;
        border-collapse: collapse;
        font-size: 0.92rem;
    }}
    .quality-table th {{
        text-align: left;
        color: {TEXT_MUTED};
        font-weight: 600;
        padding: 0.75rem 0.65rem;
        border-bottom: 1px solid {BORDER};
    }}
    .quality-table td {{
        padding: 0.8rem 0.65rem;
        border-bottom: 1px solid #F1F5F9;
        color: #0F172A;
    }}
    .status-badge {{
        display: inline-block;
        border-radius: 999px;
        padding: 0.18rem 0.58rem;
        font-size: 0.78rem;
        font-weight: 700;
    }}
    .status-pass {{
        background: #DCFCE7;
        color: #166534;
    }}
    .status-fail {{
        background: #FEE2E2;
        color: #991B1B;
    }}
    div[data-testid="stExpander"] {{
        border: 1px solid {BORDER};
        border-radius: 16px;
        background: {SURFACE};
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


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
        st.error(
            "Impossible de lire les donnees PostgreSQL. Verifiez que PostgreSQL est accessible et que les vues marts ont ete chargees."
        )
        with st.expander("Detail technique"):
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


def format_count(value: float | int | None) -> str:
    if value is None or pd.isna(value):
        return "0"
    return f"{int(value):,}".replace(",", " ")


def database_target() -> str:
    try:
        url = make_url(DATABASE_URL)
        host = url.host or "localhost"
        database = url.database or "unknown"
        return f"{host} / {database}"
    except Exception:
        return "configuration DATABASE_URL non lisible"


def as_period(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or not {"year_number", "month_number"}.issubset(df.columns):
        return df
    out = df.copy()
    out["period"] = pd.to_datetime(
        out["year_number"].astype(int).astype(str)
        + "-"
        + out["month_number"].astype(int).astype(str)
        + "-01"
    )
    return out.sort_values("period")


def year_filter_clause(alias: str = "") -> str:
    column = f"{alias}.year_number" if alias else "year_number"
    return f"WHERE (:use_year_filter = FALSE OR {column} = ANY(:years))"


def params() -> dict:
    selected_years = st.session_state.get("selected_years") or []
    return {
        "years": selected_years,
        "use_year_filter": bool(selected_years),
    }


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


def page_header(title: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <div class="page-header">
            <div class="page-header-top">
                <div>
                    <h1 class="page-title">{title}</h1>
                    <p class="page-subtitle">{subtitle}</p>
                </div>
                <div class="db-badge">Base active: {database_target()}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def metric_card(label: str, value: str, help_text: str | None = None) -> None:
    help_block = f'<div class="metric-help">{help_text}</div>' if help_text else ""
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            {help_block}
        </div>
        """,
        unsafe_allow_html=True,
    )


def metric_grid(metrics: Iterable[tuple[str, str, str | None]]) -> None:
    metrics = list(metrics)
    cols = st.columns(len(metrics))
    for col, (label, value, help_text) in zip(cols, metrics):
        with col:
            metric_card(label, value, help_text)


def section_title(title: str, description: str | None = None) -> None:
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)
    if description:
        st.markdown(
            f'<div class="section-description">{description}</div>',
            unsafe_allow_html=True,
        )


def standard_chart_layout(fig, height: int = CHART_HEIGHT):
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=50, b=20),
        font=dict(color="#0F172A"),
        title=dict(font=dict(size=16)),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            title_text="",
        ),
        xaxis=dict(showgrid=True, gridcolor="#E2E8F0", zeroline=False),
        yaxis=dict(showgrid=True, gridcolor="#E2E8F0", zeroline=False),
    )
    return fig


def chart_panel(fig) -> None:
    with st.container():
        st.markdown('<div class="panel-card">', unsafe_allow_html=True)
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)


def show_empty_state(subject: str) -> None:
    st.warning(
        f"Aucune donnee disponible pour {subject}. Verifiez que l'ETL et la creation des vues marts ont bien ete executes."
    )


def render_quality_table(checks: pd.DataFrame) -> None:
    rows: list[str] = []
    for row in checks.itertuples(index=False):
        badge_class = "status-pass" if row.passed else "status-fail"
        badge_text = "PASS" if row.passed else "FAIL"
        rows.append(
            f"""
            <tr>
                <td><span class="status-badge {badge_class}">{badge_text}</span></td>
                <td>{row.check_name}</td>
                <td>{row.value}</td>
            </tr>
            """
        )

    st.markdown(
        """
        <div class="panel-card">
            <table class="quality-table">
                <thead>
                    <tr>
                        <th>Statut</th>
                        <th>Controle</th>
                        <th>Valeur</th>
                    </tr>
                </thead>
                <tbody>
        """
        + "".join(rows)
        + """
                </tbody>
            </table>
        </div>
        """,
        unsafe_allow_html=True,
    )


def sidebar() -> str:
    st.sidebar.markdown("## Olist BI Dashboard")
    st.sidebar.markdown(
        '<div class="small-caption">Data Warehouse Analytics</div>',
        unsafe_allow_html=True,
    )
    st.sidebar.markdown(
        f"""
        <div class="sidebar-card">
            <div class="metric-label">Base active</div>
            <div style="font-weight:700;color:#0F172A;">{database_target()}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.sidebar.markdown("### Filtres globaux")
    years = load_available_years()
    selected_years = st.sidebar.multiselect(
        "Annees",
        options=years,
        default=years,
        help="Filtre global applique aux pages temporelles.",
    )
    st.session_state["selected_years"] = selected_years

    st.sidebar.markdown("### Navigation")
    selected_label = st.sidebar.selectbox("Navigation", list(NAV_OPTIONS.keys()))
    st.sidebar.caption(f"Page active : {selected_label}")
    st.sidebar.markdown("---")
    st.sidebar.markdown(
        '<div class="small-caption">Run: streamlit run dashboard/app.py</div>',
        unsafe_allow_html=True,
    )
    return NAV_OPTIONS[selected_label]


def page_sales() -> None:
    config = PAGE_CONFIG["Executive · Ventes"]
    page_header(config["title"], config["subtitle"])

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

    section_title("Indicateurs cles")
    metric_grid(
        [
            ("Revenu brut", format_brl(total_revenue), "Somme du revenu brut observe dans marts.sales_overview."),
            ("Commandes", format_count(total_orders), "Volume total de commandes sur la selection active."),
            ("Articles vendus", format_count(total_items), "Nombre d'articles vendus dans les commandes filtrees."),
            ("Panier moyen", format_brl(avg_order_value), "Revenu brut moyen par commande."),
        ]
    )

    monthly = df.groupby("period", as_index=False).agg(
        gross_revenue=("gross_revenue", "sum"),
        order_count=("order_count", "sum"),
        item_count=("item_count", "sum"),
    )
    status = df.groupby("order_status", as_index=False).agg(order_count=("order_count", "sum"))
    status["share"] = status["order_count"] / status["order_count"].sum()
    status = status.sort_values("order_count", ascending=True)

    section_title("Evolution temporelle", "Lecture mensuelle des revenus generes.")
    left, right = st.columns([1.7, 1])
    with left:
        revenue_fig = px.line(
            monthly,
            x="period",
            y="gross_revenue",
            markers=True,
            title="Revenu mensuel",
            color_discrete_sequence=[ACCENT],
        )
        revenue_fig.update_traces(line_width=3)
        revenue_fig.update_layout(xaxis_title="Mois", yaxis_title="Revenu brut")
        chart_panel(standard_chart_layout(revenue_fig))
    with right:
        section_title("Repartition", "Distribution des commandes par statut.")
        status_fig = px.bar(
            status,
            x="order_count",
            y="order_status",
            orientation="h",
            title="Commandes par statut",
            text="order_count",
            color_discrete_sequence=[ACCENT],
            hover_data={"share": ":.1%"},
        )
        status_fig.update_layout(xaxis_title="Commandes", yaxis_title="Statut")
        chart_panel(standard_chart_layout(status_fig))

    section_title("Top categories", "Top 15 categories produit par revenu brut.")
    cat = safe_query(
        """
        SELECT product_category, item_count, order_count, gross_revenue
        FROM marts.sales_by_category
        ORDER BY gross_revenue DESC
        LIMIT 15
        """
    )
    if cat.empty:
        show_empty_state("les categories produits")
    else:
        cat_fig = px.bar(
            cat.sort_values("gross_revenue", ascending=True),
            x="gross_revenue",
            y="product_category",
            orientation="h",
            text="gross_revenue",
            title="Top categories par revenu brut",
            color_discrete_sequence=[ACCENT],
        )
        cat_fig.update_layout(xaxis_title="Revenu brut", yaxis_title="Categorie")
        chart_panel(standard_chart_layout(cat_fig, height=400))

    section_title("Details")
    with st.expander("Voir les donnees agregees"):
        st.dataframe(monthly, use_container_width=True, hide_index=True)


def page_payments() -> None:
    config = PAGE_CONFIG["Commerce · Paiements"]
    page_header(config["title"], config["subtitle"])

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
    installments_avg = (
        float(
            (df["payment_installments"].fillna(0) * df["payment_count"].fillna(0)).sum()
            / total_count
        )
        if total_count
        else 0
    )

    section_title("Indicateurs cles")
    metric_grid(
        [
            ("Valeur totale payee", format_brl(total_value), None),
            ("Nombre de paiements", format_count(total_count), None),
            ("Paiement moyen", format_brl(avg_payment), None),
            ("Versements moyens", f"{installments_avg:.2f}", None),
        ]
    )

    by_type = df.groupby("payment_type", as_index=False).agg(
        total_payment_value=("total_payment_value", "sum"),
        payment_count=("payment_count", "sum"),
    ).sort_values("total_payment_value", ascending=False)

    section_title("Repartition", "Lecture comparee des montants et volumes par mode de paiement.")
    left, right = st.columns(2)
    with left:
        value_fig = px.bar(
            by_type,
            x="payment_type",
            y="total_payment_value",
            title="Valeur par mode de paiement",
            color_discrete_sequence=[ACCENT],
        )
        value_fig.update_layout(xaxis_title="Mode", yaxis_title="Valeur totale")
        chart_panel(standard_chart_layout(value_fig))
    with right:
        count_fig = px.bar(
            by_type,
            x="payment_type",
            y="payment_count",
            title="Nombre de paiements par mode",
            color_discrete_sequence=["#0F172A"],
        )
        count_fig.update_layout(xaxis_title="Mode", yaxis_title="Nombre de paiements")
        chart_panel(standard_chart_layout(count_fig))

    section_title("Evolution temporelle", "Distribution des versements sur le perimetre selectionne.")
    installments = df.groupby("payment_installments", as_index=False).agg(
        payment_count=("payment_count", "sum")
    )
    installments_fig = px.bar(
        installments,
        x="payment_installments",
        y="payment_count",
        title="Distribution des versements",
        color_discrete_sequence=[ACCENT],
    )
    installments_fig.update_layout(
        xaxis_title="Nombre de versements",
        yaxis_title="Nombre de paiements",
    )
    chart_panel(standard_chart_layout(installments_fig))


def page_satisfaction() -> None:
    config = PAGE_CONFIG["Commerce · Satisfaction"]
    page_header(config["title"], config["subtitle"])

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
    weighted_score = (
        (df["review_score"] * df["review_count"]).sum() / total_reviews if total_reviews else 0
    )
    negative = int(df.loc[df["review_score"].isin([1, 2]), "review_count"].fillna(0).sum())
    positive = int(df.loc[df["review_score"].isin([4, 5]), "review_count"].fillna(0).sum())

    section_title("Indicateurs cles")
    metric_grid(
        [
            ("Nombre d'avis", format_count(total_reviews), None),
            ("Score moyen", f"{weighted_score:.2f} / 5", None),
            ("Avis positifs", format_pct(positive / total_reviews if total_reviews else 0), None),
            ("Avis negatifs", format_pct(negative / total_reviews if total_reviews else 0), None),
        ]
    )
    st.caption("Les scores 4-5 sont consideres comme positifs, 1-2 comme negatifs.")

    monthly = (
        df.groupby("period", as_index=False)
        .apply(
            lambda group: pd.Series(
                {
                    "avg_score": (
                        (group["review_score"] * group["review_count"]).sum()
                        / group["review_count"].sum()
                    ),
                    "review_count": group["review_count"].sum(),
                }
            )
        )
        .reset_index(drop=True)
    )
    distribution = df.groupby("review_score", as_index=False).agg(
        review_count=("review_count", "sum")
    )

    section_title("Evolution temporelle", "Evolution mensuelle du score moyen.")
    left, right = st.columns([1.4, 1])
    with left:
        monthly_fig = px.line(
            monthly,
            x="period",
            y="avg_score",
            markers=True,
            title="Score moyen mensuel",
            color_discrete_sequence=[ACCENT],
        )
        monthly_fig.update_layout(xaxis_title="Mois", yaxis_title="Score moyen")
        monthly_fig.update_yaxes(range=[0, 5])
        chart_panel(standard_chart_layout(monthly_fig))
    with right:
        section_title("Repartition", "Distribution des avis par score.")
        distribution_fig = px.bar(
            distribution,
            x="review_score",
            y="review_count",
            title="Distribution des scores",
            color_discrete_sequence=["#0F172A"],
        )
        distribution_fig.update_layout(xaxis_title="Score", yaxis_title="Nombre d'avis")
        chart_panel(standard_chart_layout(distribution_fig))


def page_delivery() -> None:
    config = PAGE_CONFIG["Operations · Logistique"]
    page_header(config["title"], config["subtitle"])

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
    avg_delivery = (
        float(
            (df["avg_days_purchase_to_delivery"].fillna(0) * df["delivered_orders"].fillna(0)).sum()
            / total_delivered
        )
        if total_delivered
        else 0
    )
    avg_vs_estimate = (
        float(
            (df["avg_days_vs_estimate"].fillna(0) * df["delivered_orders"].fillna(0)).sum()
            / total_delivered
        )
        if total_delivered
        else 0
    )
    on_time_rate = (
        float((df["on_time_rate"].fillna(0) * df["delivered_orders"].fillna(0)).sum() / total_delivered)
        if total_delivered
        else 0
    )

    section_title("Indicateurs cles")
    metric_grid(
        [
            ("Commandes livrees", format_count(total_delivered), None),
            ("Delai moyen", f"{avg_delivery:.1f} jours", None),
            ("Ecart vs estimation", f"{avg_vs_estimate:.1f} jours", None),
            ("Taux a temps", format_pct(on_time_rate), None),
        ]
    )

    monthly = (
        df.groupby("period", as_index=False)
        .apply(
            lambda group: pd.Series(
                {
                    "avg_days_purchase_to_delivery": (
                        (group["avg_days_purchase_to_delivery"].fillna(0) * group["delivered_orders"]).sum()
                        / group["delivered_orders"].sum()
                    ),
                    "on_time_rate": (
                        (group["on_time_rate"].fillna(0) * group["delivered_orders"]).sum()
                        / group["delivered_orders"].sum()
                    ),
                }
            )
        )
        .reset_index(drop=True)
    )
    by_status = df.groupby("order_status", as_index=False).agg(
        on_time_rate=(
            "on_time_rate",
            lambda series: (
                (
                    series.fillna(0)
                    * df.loc[series.index, "delivered_orders"].fillna(0)
                ).sum()
                / df.loc[series.index, "delivered_orders"].fillna(0).sum()
            )
            if df.loc[series.index, "delivered_orders"].fillna(0).sum()
            else 0
        )
    )
    by_status = by_status.sort_values("on_time_rate", ascending=True)

    section_title("Evolution temporelle", "Suivi mensuel des delais et du respect de la promesse client.")
    left, right = st.columns(2)
    with left:
        delay_fig = px.line(
            monthly,
            x="period",
            y="avg_days_purchase_to_delivery",
            markers=True,
            title="Delai moyen de livraison",
            color_discrete_sequence=[ACCENT],
        )
        delay_fig.update_layout(xaxis_title="Mois", yaxis_title="Jours")
        chart_panel(standard_chart_layout(delay_fig))
    with right:
        on_time_fig = px.bar(
            by_status,
            x="on_time_rate",
            y="order_status",
            orientation="h",
            title="Taux a temps par statut",
            text="on_time_rate",
            color_discrete_sequence=["#0F172A"],
        )
        on_time_fig.update_traces(texttemplate="%{text:.0%}")
        on_time_fig.update_layout(xaxis_title="Taux a temps", yaxis_title="Statut")
        chart_panel(standard_chart_layout(on_time_fig))


def page_marketing() -> None:
    config = PAGE_CONFIG["Growth · Marketing"]
    page_header(config["title"], config["subtitle"])

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

    section_title("Indicateurs cles")
    metric_grid(
        [
            ("MQL", format_count(total_leads), None),
            ("Deals gagnes", format_count(total_deals), None),
            ("Conversion", format_pct(conversion), None),
            ("Revenu declare", format_brl(revenue), None),
        ]
    )

    by_origin = df.groupby("marketing_origin", as_index=False).agg(
        mql_count=("mql_count", "sum"),
        won_deal_count=("won_deal_count", "sum"),
        declared_monthly_revenue_sum=("declared_monthly_revenue_sum", "sum"),
    )
    by_origin["conversion_rate"] = (
        by_origin["won_deal_count"] / by_origin["mql_count"].replace(0, pd.NA)
    )
    by_origin = by_origin.sort_values("mql_count", ascending=False).head(15)

    section_title("Repartition", "Comparaison du haut et du bas de funnel par origine marketing.")
    left, right = st.columns(2)
    with left:
        volume_fig = px.bar(
            by_origin,
            x="marketing_origin",
            y=["mql_count", "won_deal_count"],
            barmode="group",
            title="MQL vs deals par origine",
            color_discrete_sequence=[ACCENT, "#0F172A"],
        )
        volume_fig.update_layout(xaxis_title="Origine", yaxis_title="Volume")
        chart_panel(standard_chart_layout(volume_fig))
    with right:
        conversion_fig = px.bar(
            by_origin.sort_values("conversion_rate", ascending=False),
            x="marketing_origin",
            y="conversion_rate",
            title="Taux de conversion par origine",
            color_discrete_sequence=[ACCENT],
            text="conversion_rate",
        )
        conversion_fig.update_traces(texttemplate="%{text:.0%}")
        conversion_fig.update_layout(xaxis_title="Origine", yaxis_title="Conversion")
        chart_panel(standard_chart_layout(conversion_fig))

    section_title("Details")
    with st.expander("Voir les principales origines marketing"):
        display_df = by_origin.copy()
        display_df["conversion_rate"] = display_df["conversion_rate"].map(format_pct)
        display_df["declared_monthly_revenue_sum"] = display_df["declared_monthly_revenue_sum"].map(format_brl)
        st.dataframe(display_df, use_container_width=True, hide_index=True)


def page_quality() -> None:
    config = PAGE_CONFIG["Data Quality · Contrôles"]
    page_header(config["title"], config["subtitle"])

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

    section_title("Indicateurs cles")
    metric_grid(
        [
            ("Total checks", format_count(total), None),
            ("Passed", format_count(passed), None),
            ("Failed", format_count(total - passed), None),
        ]
    )

    section_title(
        "Details",
        "Ces controles valident la disponibilite des couches raw, DWH et marts ainsi que la coherence des cles critiques.",
    )
    render_quality_table(checks)


def main() -> None:
    page = sidebar()
    if page == "sales":
        page_sales()
    elif page == "payments":
        page_payments()
    elif page == "satisfaction":
        page_satisfaction()
    elif page == "delivery":
        page_delivery()
    elif page == "marketing":
        page_marketing()
    elif page == "quality":
        page_quality()


if __name__ == "__main__":
    main()
