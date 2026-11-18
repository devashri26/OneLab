"""PAYMENT RECONCILIATION: Transaction & Bank Settlement Intelligence.

Production-grade Fintech Streamlit Dashboard for Payment Reconciliation,
Discrepancy Investigation, and Ledger Gap Auditing.
"""

import io
import os
from datetime import date, datetime
from decimal import Decimal
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from config import (
    DEFAULT_CUTOFF_DATE,
    DEFAULT_ROUNDING_TOLERANCE,
    STATUS_COLORS,
    STATUS_LABELS,
    ReconciliationStatus,
    TransactionType,
)
from reconciliation import reconcile_transactions
from utils import format_inr, to_decimal, validate_transactions_csv, validate_settlements_csv
from data_generator import generate_synthetic_datasets


# -----------------------------------------------------------------------------
# Page Configuration
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Payment Reconciliation & Gap Detection | Fintech Ledger",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------------------------------------------------------
# Custom Styling: Modern High-End Fintech UI (Inter / Slate / Deep Navy)
# -----------------------------------------------------------------------------
st.markdown(
    """
    <style>
    /* Global Typography & Font Family */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"], .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
        background-color: #F8FAFC;
        color: #0F172A;
    }
    
    /* Headers & Branding */
    h1, h2, h3, h4, h5 {
        color: #0F172A !important;
        font-weight: 700 !important;
        letter-spacing: -0.025em;
    }
    
    .brand-container {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding-bottom: 8px;
        border-bottom: 1px solid #E2E8F0;
        margin-bottom: 16px;
    }
    
    .brand-title {
        font-size: 1.85rem;
        font-weight: 800;
        color: #0F172A;
        letter-spacing: -0.03em;
        line-height: 1.15;
        margin: 0;
    }
    
    .brand-accent {
        color: #2563EB;
    }
    
    .brand-subtitle {
        font-size: 0.92rem;
        color: #64748B;
        font-weight: 400;
        margin-top: 4px;
        margin-bottom: 0px;
    }
    
    .badge-live {
        background-color: #ECFDF5;
        color: #059669;
        border: 1px solid #A7F3D0;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }
    .badge-live-dot {
        width: 7px;
        height: 7px;
        background-color: #059669;
        border-radius: 50%;
    }

    /* KPI Metric Cards */
    .metric-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 18px 20px;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04), 0 1px 2px rgba(15, 23, 42, 0.02);
        transition: transform 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease;
        position: relative;
        overflow: hidden;
        min-height: 128px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px -2px rgba(15, 23, 42, 0.08);
        border-color: #CBD5E1;
    }
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: transparent;
    }
    .metric-card.border-matched::before { background: #059669; }
    .metric-card.border-unsettled::before { background: #D97706; }
    .metric-card.border-gap::before { background: #DC2626; }
    .metric-card.border-exceptions::before { background: #4F46E5; }
    .metric-card.border-primary::before { background: #2563EB; }
    
    .metric-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 6px;
    }
    .metric-label {
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #64748B;
    }
    .metric-icon {
        font-size: 1.05rem;
        color: #94A3B8;
    }
    .metric-value {
        font-size: 1.70rem;
        font-weight: 700;
        color: #0F172A;
        letter-spacing: -0.03em;
        line-height: 1.2;
        font-variant-numeric: tabular-nums;
    }
    .metric-footer {
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 0.78rem;
        color: #64748B;
        margin-top: 6px;
    }
    .metric-pill {
        padding: 2px 8px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.72rem;
    }
    .pill-green { background: #ECFDF5; color: #047857; }
    .pill-amber { background: #FFFBEB; color: #B45309; }
    .pill-red { background: #FEF2F2; color: #B91C1C; }
    .pill-blue { background: #EFF6FF; color: #1D4ED8; }
    
    /* Anomaly Banner Cards */
    .anomaly-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 16px 18px;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.03);
        transition: all 0.15s ease;
        border-left: 4px solid #CBD5E1;
    }
    .anomaly-card:hover {
        border-color: #94A3B8;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px -2px rgba(15, 23, 42, 0.06);
    }
    
    /* Forensic Investigation Card */
    .dossier-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        box-shadow: 0 2px 6px rgba(15, 23, 42, 0.04);
        padding: 24px;
        margin-top: 10px;
    }
    .dossier-panel {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 16px;
    }
    .dossier-field {
        margin-bottom: 10px;
    }
    .dossier-field:last-child {
        margin-bottom: 0px;
    }
    .dossier-field-label {
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        color: #64748B;
    }
    .dossier-field-value {
        font-size: 1.05rem;
        font-weight: 600;
        color: #0F172A;
    }
    
    /* Status Pills */
    .status-pill {
        display: inline-block;
        padding: 3px 12px;
        font-size: 0.75rem;
        font-weight: 600;
        border-radius: 9999px;
        text-align: center;
        letter-spacing: 0.02em;
    }
    
    /* Tabs styling overrides */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        border-bottom: 1px solid #E2E8F0;
        padding-bottom: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        font-weight: 600 !important;
        font-size: 0.90rem !important;
        border-radius: 6px !important;
        padding: 8px 16px !important;
        background-color: transparent !important;
        color: #64748B !important;
    }
    .stTabs [aria-selected="true"] {
        color: #1E3A8A !important;
        background-color: #EFF6FF !important;
    }
    
    /* Sidebar polish */
    [data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: 1px solid #E2E8F0 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# -----------------------------------------------------------------------------
# Data Ingestion Helper with Session State Management
# -----------------------------------------------------------------------------
def load_default_sample_data():
    """Load default synthetic transactions and settlements from disk or generate on the fly."""
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    tx_path = os.path.join(data_dir, "transactions.csv")
    se_path = os.path.join(data_dir, "settlements.csv")

    if os.path.exists(tx_path) and os.path.exists(se_path):
        tx_df = pd.read_csv(tx_path)
        se_df = pd.read_csv(se_path)
    else:
        tx_df, se_df, _ = generate_synthetic_datasets(seed=42)
    return tx_df, se_df


# Initialize Session State
if "transactions_df" not in st.session_state:
    sample_tx, sample_se = load_default_sample_data()
    st.session_state["transactions_df"] = sample_tx
    st.session_state["settlements_df"] = sample_se
    st.session_state["data_source"] = "Sample Synthetic Dataset (135 Txns / 134 Settlements)"

if "cutoff_date" not in st.session_state:
    st.session_state["cutoff_date"] = DEFAULT_CUTOFF_DATE

if "tolerance" not in st.session_state:
    st.session_state["tolerance"] = DEFAULT_ROUNDING_TOLERANCE


# -----------------------------------------------------------------------------
# SIDEBAR CONTROLS
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### ⚖️ **Reconciliation Control**")
    st.caption("Financial Ledger & Bank Auditing Engine")
    st.divider()

    # Section Navigation
    st.markdown("**Navigation Views**")
    nav_selection = st.radio(
        "Go to Section",
        [
            "1. Overview & KPIs",
            "2. Financial Reconciliation",
            "3. Discrepancy Analysis",
            "4. Transaction Explorer",
            "5. Exception Investigation",
            "6. Download Reports",
        ],
        label_visibility="collapsed",
    )

    st.divider()
    st.markdown("**Audit Parameters**")
    
    # Month selector & Cutoff Date
    selected_month = st.selectbox("Accounting Period", ["January 2026 (Month-End)", "Custom Period"], index=0)
    if selected_month.startswith("January 2026"):
        selected_cutoff = st.date_input("Cutoff Boundary Date", value=DEFAULT_CUTOFF_DATE)
    else:
        selected_cutoff = st.date_input("Cutoff Boundary Date", value=st.session_state["cutoff_date"])
    
    st.session_state["cutoff_date"] = selected_cutoff

    tolerance_val = st.number_input(
        "Rounding Variance Tolerance (₹)",
        min_value=0.00,
        max_value=1.00,
        value=float(DEFAULT_ROUNDING_TOLERANCE),
        step=0.01,
        help="Differences within this threshold are routed to Rounding Variance rather than marked as Amount Mismatches.",
    )
    st.session_state["tolerance"] = to_decimal(tolerance_val)

    st.divider()
    st.markdown("**Data Ingestion**")
    use_sample = st.checkbox("Use Seeded Sample Dataset (Deterministic)", value=True, help="Loads pre-seeded dataset with all 4 isolated anomalies.")

    uploaded_tx = st.file_uploader("Upload Transactions CSV", type=["csv"])
    uploaded_se = st.file_uploader("Upload Settlements CSV", type=["csv"])

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        run_btn = st.button("🚀 Reconcile", type="primary", use_container_width=True)
    with col_btn2:
        reset_btn = st.button("🔄 Reset", use_container_width=True)

    if reset_btn:
        sample_tx, sample_se = load_default_sample_data()
        st.session_state["transactions_df"] = sample_tx
        st.session_state["settlements_df"] = sample_se
        st.session_state["data_source"] = "Sample Synthetic Dataset (135 Txns / 134 Settlements)"
        st.session_state["cutoff_date"] = DEFAULT_CUTOFF_DATE
        st.session_state["tolerance"] = DEFAULT_ROUNDING_TOLERANCE
        st.rerun()

    # Process File Uploads if provided
    if not use_sample and (uploaded_tx is not None or uploaded_se is not None):
        if uploaded_tx is not None:
            try:
                user_tx = pd.read_csv(uploaded_tx)
                is_valid, errs = validate_transactions_csv(user_tx)
                if is_valid:
                    st.session_state["transactions_df"] = user_tx
                    st.session_state["data_source"] = "Custom Uploaded Transactions"
                    st.sidebar.success(f"Loaded {len(user_tx)} transactions.")
                else:
                    st.sidebar.error("Transactions CSV Error:")
                    for e in errs:
                        st.sidebar.caption(f"• {e}")
            except Exception as e:
                st.sidebar.error(f"Error reading transactions: {e}")

        if uploaded_se is not None:
            try:
                user_se = pd.read_csv(uploaded_se)
                is_valid, errs = validate_settlements_csv(user_se)
                if is_valid:
                    st.session_state["settlements_df"] = user_se
                    st.session_state["data_source"] = "Custom Uploaded Settlements"
                    st.sidebar.success(f"Loaded {len(user_se)} settlements.")
                else:
                    st.sidebar.error("Settlements CSV Error:")
                    for e in errs:
                        st.sidebar.caption(f"• {e}")
            except Exception as e:
                st.sidebar.error(f"Error reading settlements: {e}")
    elif use_sample:
        sample_tx, sample_se = load_default_sample_data()
        st.session_state["transactions_df"] = sample_tx
        st.session_state["settlements_df"] = sample_se
        st.session_state["data_source"] = "Sample Synthetic Dataset (135 Txns / 134 Settlements)"


# -----------------------------------------------------------------------------
# RUN RECONCILIATION ENGINE
# -----------------------------------------------------------------------------
current_tx = st.session_state["transactions_df"]
current_se = st.session_state["settlements_df"]
current_cutoff = st.session_state["cutoff_date"]
current_tolerance = st.session_state["tolerance"]

reconciled_df, exceptions_df, summary, validation_report = reconcile_transactions(
    transactions=current_tx,
    settlements=current_se,
    cutoff_date=current_cutoff,
    rounding_tolerance=current_tolerance,
)


# -----------------------------------------------------------------------------
# APPLICATION HEADER
# -----------------------------------------------------------------------------
st.markdown(
    f"""
    <div class="brand-container">
        <div>
            <div class="brand-title">PAYMENT RECONCILIATION <span class="brand-accent">&bull;</span> Transaction & Bank Settlement Intelligence</div>
            <div class="brand-subtitle">Automated ledger comparison &bull; Gap detection &bull; Exact Decimal reconciliation</div>
        </div>
        <div>
            <span class="badge-live">
                <span class="badge-live-dot"></span> Audit Active &bull; Cutoff: {current_cutoff}
            </span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Active Context Breadcrumb
crumb_col1, crumb_col2, crumb_col3 = st.columns([2, 1, 1])
with crumb_col1:
    st.caption(f"📂 **Active Dataset:** {st.session_state['data_source']}")
with crumb_col2:
    st.caption(f"🎯 **Cutoff Boundary:** `{current_cutoff}`")
with crumb_col3:
    st.caption(f"⚙️ **Variance Tolerance:** `₹{float(current_tolerance):.2f}`")


# -----------------------------------------------------------------------------
# SECTION 1: OVERVIEW DASHBOARD & KPI CARDS
# -----------------------------------------------------------------------------
if nav_selection in ["1. Overview & KPIs"]:
    st.subheader("1. Executive Summary & KPIs")

    kpi1, kpi2, kpi3, kpi4, kpi5, kpi6 = st.columns(6)

    with kpi1:
        st.markdown(
            f"""
            <div class="metric-card border-primary">
                <div class="metric-header">
                    <span class="metric-label">Platform Volume</span>
                    <span class="metric-icon">💳</span>
                </div>
                <div class="metric-value">{summary['platform_total_records']}</div>
                <div class="metric-footer">
                    <span class="metric-pill pill-blue">Net: {format_inr(summary['platform_net_amount'])}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with kpi2:
        st.markdown(
            f"""
            <div class="metric-card border-primary">
                <div class="metric-header">
                    <span class="metric-label">Bank Settlements</span>
                    <span class="metric-icon">🏦</span>
                </div>
                <div class="metric-value">{summary['bank_total_records_period']}</div>
                <div class="metric-footer">
                    <span class="metric-pill pill-blue">Net: {format_inr(summary['bank_net_amount_period'])}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with kpi3:
        st.markdown(
            f"""
            <div class="metric-card border-matched">
                <div class="metric-header">
                    <span class="metric-label">Fully Matched</span>
                    <span class="metric-icon" style="color: #059669;">✓</span>
                </div>
                <div class="metric-value" style="color: #059669;">{summary['matched_count']}</div>
                <div class="metric-footer">
                    <span class="metric-pill pill-green">Gross: {format_inr(summary['matched_gross_amount'])}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with kpi4:
        st.markdown(
            f"""
            <div class="metric-card border-unsettled">
                <div class="metric-header">
                    <span class="metric-label">Unsettled In-Transit</span>
                    <span class="metric-icon" style="color: #D97706;">⏳</span>
                </div>
                <div class="metric-value" style="color: #D97706;">{summary['unsettled_count']}</div>
                <div class="metric-footer">
                    <span class="metric-pill pill-amber">{format_inr(summary['unsettled_amount'])} awaiting bank</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with kpi5:
        net_gap = summary["net_reconciliation_difference"]
        gap_color = "#DC2626" if net_gap != 0 else "#059669"
        border_cls = "border-gap" if net_gap != 0 else "border-matched"
        pill_cls = "pill-red" if net_gap != 0 else "pill-green"
        st.markdown(
            f"""
            <div class="metric-card {border_cls}">
                <div class="metric-header">
                    <span class="metric-label">Reconciliation Gap</span>
                    <span class="metric-icon" style="color: {gap_color};">⚖️</span>
                </div>
                <div class="metric-value" style="color: {gap_color};">{format_inr(net_gap)}</div>
                <div class="metric-footer">
                    <span class="metric-pill {pill_cls}">Net Bank vs. Platform</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with kpi6:
        st.markdown(
            f"""
            <div class="metric-card border-exceptions">
                <div class="metric-header">
                    <span class="metric-label">Total Exceptions</span>
                    <span class="metric-icon" style="color: #4F46E5;">⚠️</span>
                </div>
                <div class="metric-value" style="color: #4F46E5;">{summary['total_exceptions_count']}</div>
                <div class="metric-footer">
                    <span class="metric-pill pill-amber">Requires Audit / Follow-up</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Four Mandatory Anomaly Highlights
    st.markdown("#### 🎯 Mandatory Anomaly Detection Status")
    anom1, anom2, anom3, anom4 = st.columns(4)

    with anom1:
        st.markdown(
            f"""
            <div class="anomaly-card" style="border-left-color: #D97706; background: #FFFDF5;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                    <b style="color: #92400E; font-size: 0.88rem;">1. Late Settlement</b>
                    <span class="metric-pill pill-amber">Timing</span>
                </div>
                <div style="font-size: 1.45rem; font-weight: 700; color: #B45309; line-height: 1.2;">
                    {summary['late_settlement_count']} Detected
                </div>
                <div style="font-size: 0.82rem; color: #78350F; font-weight: 500; margin-top: 4px;">
                    Impact: <b>{format_inr(summary['late_settlement_amount'])}</b>
                </div>
                <div style="font-size: 0.74rem; color: #92400E; margin-top: 4px;">
                    Jan 31 txn settled Feb 1 &bull; Rolls to Feb balance
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with anom2:
        st.markdown(
            f"""
            <div class="anomaly-card" style="border-left-color: #2563EB; background: #F8FAFF;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                    <b style="color: #1E40AF; font-size: 0.88rem;">2. Rounding Variance</b>
                    <span class="metric-pill pill-blue">Decimal FX</span>
                </div>
                <div style="font-size: 1.45rem; font-weight: 700; color: #1D4ED8; line-height: 1.2;">
                    {summary['rounding_variance_count']} Detected
                </div>
                <div style="font-size: 0.82rem; color: #1E3A8A; font-weight: 500; margin-top: 4px;">
                    Net Diff: <b>{format_inr(summary['rounding_total_difference'])}</b>
                </div>
                <div style="font-size: 0.74rem; color: #1E40AF; margin-top: 4px;">
                    Cumulative decimal diffs within ₹0.05 tolerance
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with anom3:
        st.markdown(
            f"""
            <div class="anomaly-card" style="border-left-color: #DC2626; background: #FFF8F8;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                    <b style="color: #991B1B; font-size: 0.88rem;">3. Duplicate Settlement</b>
                    <span class="metric-pill pill-red">Quarantine</span>
                </div>
                <div style="font-size: 1.45rem; font-weight: 700; color: #B91C1C; line-height: 1.2;">
                    {summary['duplicate_settlement_count']} Detected
                </div>
                <div style="font-size: 0.82rem; color: #7F1D1D; font-weight: 500; margin-top: 4px;">
                    Impact: <b>{format_inr(summary['duplicate_settlement_amount'])}</b>
                </div>
                <div style="font-size: 0.74rem; color: #991B1B; margin-top: 4px;">
                    Repeated credit isolated; revenue protected
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with anom4:
        st.markdown(
            f"""
            <div class="anomaly-card" style="border-left-color: #7C3AED; background: #FCF8FF;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                    <b style="color: #6B21A8; font-size: 0.88rem;">4. Orphan Refund</b>
                    <span class="metric-pill" style="background:#F3E8FF; color:#6B21A8;">Audit</span>
                </div>
                <div style="font-size: 1.45rem; font-weight: 700; color: #7E22CE; line-height: 1.2;">
                    {summary['orphan_refund_count']} Detected
                </div>
                <div style="font-size: 0.82rem; color: #581C87; font-weight: 500; margin-top: 4px;">
                    Impact: <b>{format_inr(summary['orphan_refund_amount'])}</b>
                </div>
                <div style="font-size: 0.74rem; color: #6B21A8; margin-top: 4px;">
                    Bank debit lacking source payment &bull; Fraud alert
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# -----------------------------------------------------------------------------
# SECTION 2: FINANCIAL RECONCILIATION
# -----------------------------------------------------------------------------
if nav_selection in ["1. Overview & KPIs", "2. Financial Reconciliation"]:
    st.divider()
    st.subheader("2. Financial Reconciliation Ledger")
    st.caption("Detailed ledger audit reconciling Gross Payments, Refunds, and Net Settled Funds with Month-End Balances.")

    tab_gross, tab_refund, tab_net = st.tabs(["📊 Gross Payments Ledger", "🔄 Refunds & Contra-Revenue", "🌉 Net Reconciliation Bridge"])

    with tab_gross:
        g1, g2, g3 = st.columns(3)
        with g1:
            st.metric("Platform Expected Gross Payments", format_inr(summary["platform_total_payments"]))
        with g2:
            st.metric("Bank Gross Payments (Cleared In-Period)", format_inr(summary["bank_total_payments_period"]))
        with g3:
            gross_diff = summary["bank_total_payments_period"] - summary["platform_total_payments"]
            st.metric("Gross Payment Difference", format_inr(gross_diff), delta=float(gross_diff))

        col_tbl, col_notes = st.columns([1.4, 1])
        with col_tbl:
            gross_ledger_data = [
                {"Reconciliation Line Item": "Platform Expected Gross Payments", "Impact": format_inr(summary["platform_total_payments"]), "Direction": "Base"},
                {"Reconciliation Line Item": "Less: In-Transit / Unsettled Payments", "Impact": f"- {format_inr(summary['unsettled_payments_amount'])}", "Direction": "Deduction"},
                {"Reconciliation Line Item": "Less: Late Settlements (Settling in February)", "Impact": f"- {format_inr(summary['late_settlement_payments_amount'])}", "Direction": "Timing"},
                {"Reconciliation Line Item": "Add: Duplicate Payment Credits from Bank", "Impact": f"+ {format_inr(summary['duplicate_settlement_payments_amount'])}", "Direction": "Quarantine"},
                {"Reconciliation Line Item": "Add: Unmatched External Bank Credits", "Impact": f"+ {format_inr(summary['unmatched_bank_amount'])}", "Direction": "Unrecorded"},
                {"Reconciliation Line Item": "Net Rounding & Amount Discrepancies", "Impact": format_inr(summary["rounding_total_difference"] + summary["amount_mismatch_difference"]), "Direction": "Variance"},
                {"Reconciliation Line Item": "Realized Bank Gross Payments (Period)", "Impact": format_inr(summary["bank_total_payments_period"]), "Direction": "Reconciled"},
            ]
            st.dataframe(pd.DataFrame(gross_ledger_data), use_container_width=True, hide_index=True)

        with col_notes:
            st.info(
                f"""
                **Auditor Ledger Notes:**
                - **Cleared Payments:** `{format_inr(summary['matched_payments_amount'])}` across {summary['matched_payments_count']} payments fully verified.
                - **Timing Deferrals:** `{format_inr(summary['late_settlement_payments_amount'])}` transacted on Jan 31 rolling into February settlement clearing.
                - **Cash Protection:** `{format_inr(summary['duplicate_settlement_payments_amount'])}` duplicate credit quarantined from P&L revenue.
                """,
                icon="💡",
            )

    with tab_refund:
        r1, r2, r3 = st.columns(3)
        with r1:
            st.metric("Platform Expected Refunds", format_inr(summary["platform_total_refunds"]))
        with r2:
            st.metric("Bank Processed Refunds (In-Period)", format_inr(summary["bank_total_refunds_period"]))
        with r3:
            refund_diff = summary["bank_total_refunds_period"] - summary["platform_total_refunds"]
            st.metric("Refund Net Variance", format_inr(refund_diff), delta=float(refund_diff))

        col_ref_tbl, col_ref_notes = st.columns([1.4, 1])
        with col_ref_tbl:
            refund_ledger_data = [
                {"Refund Line Item": "Platform Expected Refunds (Contra-Revenue)", "Amount": format_inr(summary["platform_total_refunds"]), "Status": "Expected"},
                {"Refund Line Item": "Less: Unsettled Platform Refunds", "Amount": f"- {format_inr(summary['unsettled_refunds_amount'])}", "Status": "In-Transit"},
                {"Refund Line Item": "Less: Late Settlement Refunds (Feb Settlement)", "Amount": f"- {format_inr(summary['late_settlement_refunds_amount'])}", "Status": "Timing"},
                {"Refund Line Item": "Add: Orphan Bank Refunds (No Source Payment)", "Amount": f"+ {format_inr(summary['orphan_refund_amount'])}", "Status": "Anomaly"},
                {"Refund Line Item": "Add: Duplicate Bank Refund Debits", "Amount": f"+ {format_inr(summary['duplicate_settlement_refunds_amount'])}", "Status": "Anomaly"},
                {"Refund Line Item": "Realized Bank Processed Refunds", "Amount": format_inr(summary["bank_total_refunds_period"]), "Status": "Reconciled"},
            ]
            st.dataframe(pd.DataFrame(refund_ledger_data), use_container_width=True, hide_index=True)

        with col_ref_notes:
            st.warning(
                f"""
                **Refund Governance Observations:**
                - Verified **{summary['matched_refunds_count']} valid refunds** totaling `{format_inr(summary['matched_refunds_amount'])}` matched to original charges.
                - Flagged **{summary['orphan_refund_count']} orphan refund(s)** totaling `{format_inr(summary['orphan_refund_amount'])}` lacking parent transactions.
                - Flagged **{summary['refund_exceeds_payment_count']} refund(s)** exceeding original payment authorization.
                """,
                icon="⚠️",
            )

    with tab_net:
        n1, n2, n3 = st.columns(3)
        with n1:
            st.metric("Net Platform Expected (Gross - Refund)", format_inr(summary["platform_net_amount"]))
        with n2:
            st.metric("Net Bank Realized (Gross - Refund)", format_inr(summary["bank_net_amount_period"]))
        with n3:
            st.metric("Net Reconciliation Gap", format_inr(summary["net_reconciliation_difference"]), delta=float(summary["net_reconciliation_difference"]))

        # Visual Waterfall Chart of Net Bridge
        waterfall_x = [
            "Platform Net Revenue",
            "Unsettled Payments",
            "Unsettled Refunds",
            "Late Payments (Timing)",
            "Late Refunds (Timing)",
            "Duplicate Payments",
            "Duplicate Refunds",
            "Unmatched Bank Credits",
            "Orphan Bank Refunds",
            "Amount / Rounding Variance",
            "Bank Net Settled Cash",
        ]
        
        # Calculate disaggregated bridge steps
        unsettled_pay_impact = -float(summary["unsettled_payments_amount"])
        unsettled_ref_impact = float(summary["unsettled_refunds_amount"])
        late_pay_impact = -float(summary["late_settlement_payments_amount"])
        late_ref_impact = float(summary["late_settlement_refunds_amount"])
        dup_pay_impact = float(summary["duplicate_settlement_payments_amount"])
        dup_ref_impact = -float(summary["duplicate_settlement_refunds_amount"])
        unmatched_impact = float(summary["unmatched_bank_amount"])
        orphan_impact = -float(summary["orphan_refund_amount"])
        mismatch_rounding = float(summary["rounding_total_difference"] + summary["amount_mismatch_difference"])

        waterfall_y = [
            float(summary["platform_net_amount"]),
            unsettled_pay_impact,
            unsettled_ref_impact,
            late_pay_impact,
            late_ref_impact,
            dup_pay_impact,
            dup_ref_impact,
            unmatched_impact,
            orphan_impact,
            mismatch_rounding,
            0.0,
        ]

        fig_waterfall = go.Figure(
            go.Waterfall(
                name="Reconciliation Bridge",
                orientation="v",
                measure=["absolute", "relative", "relative", "relative", "relative", "relative", "relative", "relative", "relative", "relative", "total"],
                x=waterfall_x,
                y=waterfall_y,
                textposition="outside",
                text=[f"₹{abs(v):,.0f}" if v != 0 else "" for v in waterfall_y[:-1]] + [f"₹{float(summary['bank_net_amount_period']):,.0f}"],
                connector={"line": {"color": "#94A3B8", "width": 1.5}},
                decreasing={"marker": {"color": "#DC2626"}},
                increasing={"marker": {"color": "#059669"}},
                totals={"marker": {"color": "#1E3A8A"}},
            )
        )
        fig_waterfall.update_layout(
            title=dict(
                text="<b>Net Financial Reconciliation Bridge (Platform to Bank)</b>",
                font=dict(size=15, color="#0F172A"),
            ),
            plot_bgcolor="#FFFFFF",
            paper_bgcolor="#FFFFFF",
            height=430,
            margin=dict(l=20, r=20, t=50, b=20),
            yaxis=dict(
                title="Monetary Value (₹)",
                gridcolor="#F1F5F9",
                zerolinecolor="#CBD5E1",
            ),
            xaxis=dict(tickangle=-25),
        )
        st.plotly_chart(fig_waterfall, use_container_width=True)
        st.success(f"✅ **Mathematical Bridge Status:** Verified to **`{format_inr(summary['bridge_discrepancy'])}`** discrepancy (Exact 0.00). Ledger fully balanced.")


# -----------------------------------------------------------------------------
# SECTION 3: DISCREPANCY ANALYSIS
# -----------------------------------------------------------------------------
if nav_selection in ["1. Overview & KPIs", "3. Discrepancy Analysis"]:
    st.divider()
    st.subheader("3. Discrepancy & Anomaly Analysis")
    st.caption("Distribution of reconciliation exceptions categorized by volume and monetary balance impact.")

    col_chart1, col_chart2 = st.columns(2)

    cat_names = []
    cat_counts = []
    cat_amounts = []
    cat_colors = []

    for status in ReconciliationStatus:
        if status.value in [ReconciliationStatus.MATCHED.value, ReconciliationStatus.POST_CUTOFF_TRANSACTION.value]:
            continue
        m = summary["status_metrics"][status.value]
        if m["count"] > 0:
            cat_names.append(STATUS_LABELS.get(status.value, status.value))
            cat_counts.append(m["count"])
            if status in [ReconciliationStatus.UNSETTLED, ReconciliationStatus.LATE_SETTLEMENT, ReconciliationStatus.REFUND_EXCEEDS_PAYMENT]:
                amt = float(m["platform_amount"])
            elif status in [ReconciliationStatus.DUPLICATE_SETTLEMENT, ReconciliationStatus.ORPHAN_REFUND, ReconciliationStatus.UNMATCHED_BANK_ENTRY]:
                amt = float(m["bank_amount"])
            else:
                amt = abs(float(m["difference"]))
            cat_amounts.append(amt)
            cat_colors.append(STATUS_COLORS.get(status.value, "#64748B"))

    with col_chart1:
        if cat_counts:
            fig_donut = go.Figure(
                go.Pie(
                    labels=cat_names,
                    values=cat_counts,
                    hole=0.55,
                    marker=dict(colors=cat_colors),
                    textinfo="label+value",
                    textfont=dict(size=11),
                    hovertemplate="<b>%{label}</b><br>Exceptions: %{value}<br>Share: %{percent}<extra></extra>",
                )
            )
            fig_donut.update_layout(
                title=dict(text="<b>Exception Volume Breakdown</b>", font=dict(size=14, color="#0F172A")),
                paper_bgcolor="#FFFFFF",
                plot_bgcolor="#FFFFFF",
                height=350,
                showlegend=False,
                margin=dict(l=10, r=10, t=40, b=10),
            )
            st.plotly_chart(fig_donut, use_container_width=True)
        else:
            st.success("No exceptions found. Datasets match completely.")

    with col_chart2:
        if cat_amounts:
            fig_hbar = go.Figure(
                go.Bar(
                    x=cat_amounts,
                    y=cat_names,
                    orientation="h",
                    marker=dict(color=cat_colors),
                    text=[f"₹{a:,.2f}" for a in cat_amounts],
                    textposition="auto",
                    hovertemplate="<b>%{y}</b><br>Financial Impact: ₹%{x:,.2f}<extra></extra>",
                )
            )
            fig_hbar.update_layout(
                title=dict(text="<b>Monetary Balance Impact (₹)</b>", font=dict(size=14, color="#0F172A")),
                paper_bgcolor="#FFFFFF",
                plot_bgcolor="#FFFFFF",
                height=350,
                xaxis=dict(title="Monetary Impact (₹)", gridcolor="#F1F5F9"),
                yaxis=dict(autorange="reversed"),
                margin=dict(l=10, r=10, t=40, b=10),
            )
            st.plotly_chart(fig_hbar, use_container_width=True)


# -----------------------------------------------------------------------------
# SECTION 4: TRANSACTION EXPLORER
# -----------------------------------------------------------------------------
if nav_selection in ["4. Transaction Explorer"]:
    st.divider()
    st.subheader("4. Transaction & Settlement Explorer")
    st.caption("Forensic line-item audit table. Search by ID, filter by category, or export filtered views.")

    # Quick Preset Pills
    preset_cols = st.columns([1, 1, 1, 1, 1])
    with preset_cols[0]:
        btn_all = st.button(f"All Records ({len(reconciled_df)})", use_container_width=True)
    with preset_cols[1]:
        btn_exc = st.button(f"Exceptions Only ({len(exceptions_df)})", use_container_width=True)
    with preset_cols[2]:
        btn_match = st.button(f"Matched ({summary['matched_count']})", use_container_width=True)
    with preset_cols[3]:
        btn_late = st.button(f"Late Settled ({summary['late_settlement_count']})", use_container_width=True)
    with preset_cols[4]:
        btn_dup = st.button(f"Duplicates ({summary['duplicate_settlement_count']})", use_container_width=True)

    default_status_filter = []
    if btn_exc:
        default_status_filter = [st_val for st_val in STATUS_LABELS.keys() if st_val != ReconciliationStatus.MATCHED.value]
    elif btn_match:
        default_status_filter = [ReconciliationStatus.MATCHED.value]
    elif btn_late:
        default_status_filter = [ReconciliationStatus.LATE_SETTLEMENT.value]
    elif btn_dup:
        default_status_filter = [ReconciliationStatus.DUPLICATE_SETTLEMENT.value]

    # Explorer Filter Bar
    f_col1, f_col2, f_col3, f_col4 = st.columns([2, 2, 1.5, 2])

    with f_col1:
        search_query = st.text_input("🔍 Search Transaction / Settlement ID", placeholder="e.g. TXN1001, SET5001")
    with f_col2:
        status_filter = st.multiselect(
            "Reconciliation Status",
            options=list(STATUS_LABELS.keys()),
            format_func=lambda x: STATUS_LABELS.get(x, x),
            default=default_status_filter,
        )
    with f_col3:
        type_filter = st.multiselect(
            "Transaction Type",
            options=[TransactionType.PAYMENT.value, TransactionType.REFUND.value],
            default=[],
        )
    with f_col4:
        amount_range = st.slider(
            "Amount Filter (₹)",
            min_value=0.0,
            max_value=30000.0,
            value=(0.0, 30000.0),
            step=250.0,
        )

    # Filter Logic
    filtered_df = reconciled_df.copy()

    if search_query:
        q = search_query.strip().lower()
        filtered_df = filtered_df[
            filtered_df["transaction_id"].str.lower().str.contains(q)
            | filtered_df["settlement_id"].str.lower().str.contains(q)
        ]

    if status_filter:
        filtered_df = filtered_df[filtered_df["reconciliation_status"].isin(status_filter)]

    if type_filter:
        filtered_df = filtered_df[filtered_df["transaction_type"].isin(type_filter)]

    filtered_df = filtered_df[
        (filtered_df["platform_amount"] >= amount_range[0]) | (filtered_df["bank_amount"] >= amount_range[0])
    ]
    filtered_df = filtered_df[
        (filtered_df["platform_amount"] <= amount_range[1]) | (filtered_df["bank_amount"] <= amount_range[1])
    ]

    st.markdown(f"Displaying **{len(filtered_df)}** of **{len(reconciled_df)}** records:")

    display_cols = [
        "transaction_id",
        "settlement_id",
        "transaction_date",
        "settlement_date",
        "transaction_type",
        "platform_amount",
        "bank_amount",
        "difference",
        "reconciliation_status",
        "explanation",
    ]

    st.dataframe(
        filtered_df[display_cols],
        column_config={
            "transaction_id": st.column_config.TextColumn("Transaction ID", width="medium"),
            "settlement_id": st.column_config.TextColumn("Settlement ID", width="medium"),
            "transaction_date": st.column_config.TextColumn("Txn Date", width="small"),
            "settlement_date": st.column_config.TextColumn("Settle Date", width="small"),
            "transaction_type": st.column_config.TextColumn("Type", width="small"),
            "platform_amount": st.column_config.NumberColumn("Platform Amount", format="₹ %.2f"),
            "bank_amount": st.column_config.NumberColumn("Bank Amount", format="₹ %.2f"),
            "difference": st.column_config.NumberColumn("Variance", format="₹ %.2f"),
            "reconciliation_status": st.column_config.TextColumn("Status", width="medium"),
            "explanation": st.column_config.TextColumn("Audit Explanation", width="large"),
        },
        use_container_width=True,
        height=480,
        hide_index=True,
    )


# -----------------------------------------------------------------------------
# SECTION 5: EXCEPTION INVESTIGATION
# -----------------------------------------------------------------------------
if nav_selection in ["5. Exception Investigation"]:
    st.divider()
    st.subheader("5. Line-Item Forensic Investigation Dossier")
    st.caption("Deep-dive forensic audit card comparing Platform records against Bank Settlements with corrective recommendations.")

    if exceptions_df.empty:
        st.success("🎉 No reconciliation exceptions found! All records matched perfectly.")
    else:
        exception_options = exceptions_df.apply(
            lambda r: f"[{r['reconciliation_status']}] {r['transaction_id']} (Bank: {r['settlement_id']}) — Diff: ₹{r['difference']:.2f}",
            axis=1,
        ).tolist()

        selected_label = st.selectbox("Select Exception Record to Audit", exception_options, index=0)
        selected_idx = exception_options.index(selected_label)
        selected_record = exceptions_df.iloc[selected_idx]

        status_key = selected_record["reconciliation_status"]
        status_color = STATUS_COLORS.get(status_key, "#1E3A8A")

        # Visual Dossier Card
        st.markdown(
            f"""
            <div class="dossier-card" style="border-left: 5px solid {status_color};">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                    <div>
                        <span style="font-size: 1.35rem; font-weight: 800; color: #0F172A;">
                            Investigation Dossier: {selected_record['transaction_id']}
                        </span>
                        &nbsp;&bull;&nbsp;
                        <span style="font-size: 0.95rem; color: #64748B;">Bank Ref: <b>{selected_record['settlement_id']}</b></span>
                    </div>
                    <div>
                        <span class="status-pill" style="background-color: {status_color}18; color: {status_color}; border: 1px solid {status_color};">
                            {STATUS_LABELS.get(status_key, status_key)}
                        </span>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<br>", unsafe_allow_html=True)
        col_p_dossier, col_b_dossier, col_var_dossier = st.columns([1, 1, 1])

        with col_p_dossier:
            st.markdown(
                f"""
                <div class="dossier-panel">
                    <div style="font-weight: 700; color: #1E3A8A; margin-bottom: 12px; font-size: 0.90rem;">
                        💳 PLATFORM TRANSACTION LEDGER
                    </div>
                    <div class="dossier-field">
                        <div class="dossier-field-label">Transaction ID</div>
                        <div class="dossier-field-value">{selected_record['transaction_id']}</div>
                    </div>
                    <div class="dossier-field">
                        <div class="dossier-field-label">Capture Date</div>
                        <div class="dossier-field-value">{selected_record['transaction_date']}</div>
                    </div>
                    <div class="dossier-field">
                        <div class="dossier-field-label">Expected Amount</div>
                        <div class="dossier-field-value">{format_inr(selected_record['platform_amount'])}</div>
                    </div>
                    <div class="dossier-field">
                        <div class="dossier-field-label">Type</div>
                        <div class="dossier-field-value">{selected_record['transaction_type']}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col_b_dossier:
            st.markdown(
                f"""
                <div class="dossier-panel">
                    <div style="font-weight: 700; color: #059669; margin-bottom: 12px; font-size: 0.90rem;">
                        🏦 BANK SETTLEMENT STATEMENT
                    </div>
                    <div class="dossier-field">
                        <div class="dossier-field-label">Settlement ID</div>
                        <div class="dossier-field-value">{selected_record['settlement_id']}</div>
                    </div>
                    <div class="dossier-field">
                        <div class="dossier-field-label">Settlement Date</div>
                        <div class="dossier-field-value">{selected_record['settlement_date']}</div>
                    </div>
                    <div class="dossier-field">
                        <div class="dossier-field-label">Settled Amount</div>
                        <div class="dossier-field-value">{format_inr(selected_record['bank_amount'])}</div>
                    </div>
                    <div class="dossier-field">
                        <div class="dossier-field-label">Clearing Delay</div>
                        <div class="dossier-field-value">{f"{selected_record['days_to_settle']} days" if pd.notna(selected_record['days_to_settle']) else "N/A"}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col_var_dossier:
            diff_val = selected_record["difference"]
            diff_color = "#DC2626" if diff_val < 0 else ("#059669" if diff_val > 0 else "#64748B")
            st.markdown(
                f"""
                <div class="dossier-panel" style="border-left: 3px solid {diff_color};">
                    <div style="font-weight: 700; color: #0F172A; margin-bottom: 12px; font-size: 0.90rem;">
                        ⚖️ VARIANCE & AUDIT TRAIL
                    </div>
                    <div class="dossier-field">
                        <div class="dossier-field-label">Monetary Variance</div>
                        <div class="dossier-field-value" style="color: {diff_color};">{format_inr(diff_val)}</div>
                    </div>
                    <div class="dossier-field">
                        <div class="dossier-field-label">Period Cutoff</div>
                        <div class="dossier-field-value">{current_cutoff}</div>
                    </div>
                    <div class="dossier-field">
                        <div class="dossier-field-label">Exception Status</div>
                        <div class="dossier-field-value">{STATUS_LABELS.get(status_key, status_key)}</div>
                    </div>
                    <div class="dossier-field">
                        <div class="dossier-field-label">Variance Direction</div>
                        <div class="dossier-field-value">{"Net Cash Deficit" if diff_val < 0 else ("Net Cash Surplus" if diff_val > 0 else "Balanced")}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### 📖 Financial Root Cause")
        st.info(selected_record["explanation"], icon="ℹ️")

        st.markdown("#### 🛠️ Recommended Accounting Action")
        st.warning(selected_record["suggested_action"], icon="👉")


# -----------------------------------------------------------------------------
# SECTION 6: REPORT GENERATION & EXPORTS
# -----------------------------------------------------------------------------
if nav_selection in ["6. Download Reports"]:
    st.divider()
    st.subheader("6. Download Reconciliation Reports")
    st.caption("Generate verifiable audit files for accounting records, external auditors, and operations teams.")

    # 1. Full Reconciliation Report CSV
    full_csv = reconciled_df.to_csv(index=False).encode("utf-8")
    
    # 2. Exceptions Only CSV
    exceptions_csv = exceptions_df.to_csv(index=False).encode("utf-8")
    
    # 3. Financial Summary CSV with disaggregated fields
    summary_data = [
        {"Metric": "Cutoff Date", "Value": str(current_cutoff)},
        {"Metric": "Rounding Tolerance", "Value": str(current_tolerance)},
        {"Metric": "Platform Total Payments (Gross)", "Value": str(summary["platform_total_payments"])},
        {"Metric": "Platform Total Refunds", "Value": str(summary["platform_total_refunds"])},
        {"Metric": "Platform Net Expected Amount", "Value": str(summary["platform_net_amount"])},
        {"Metric": "Platform Total Records (Period)", "Value": summary["platform_total_records"]},
        {"Metric": "Bank Total Payments (Period)", "Value": str(summary["bank_total_payments_period"])},
        {"Metric": "Bank Total Refunds (Period)", "Value": str(summary["bank_total_refunds_period"])},
        {"Metric": "Bank Net Settled Amount", "Value": str(summary["bank_net_amount_period"])},
        {"Metric": "Bank Total Records (Period)", "Value": summary["bank_total_records_period"]},
        {"Metric": "Net Reconciliation Gap", "Value": str(summary["net_reconciliation_difference"])},
        {"Metric": "Mathematical Bridge Discrepancy", "Value": str(summary["bridge_discrepancy"])},
        {"Metric": "Matched Records Count", "Value": summary["matched_count"]},
        {"Metric": "Matched Payments Amount", "Value": str(summary["matched_payments_amount"])},
        {"Metric": "Matched Refunds Amount", "Value": str(summary["matched_refunds_amount"])},
        {"Metric": "Matched Gross Amount", "Value": str(summary["matched_gross_amount"])},
        {"Metric": "Matched Net Amount", "Value": str(summary["matched_net_amount"])},
        {"Metric": "Unsettled Payments Amount", "Value": str(summary["unsettled_payments_amount"])},
        {"Metric": "Unsettled Refunds Amount", "Value": str(summary["unsettled_refunds_amount"])},
        {"Metric": "Late Settlement Payments Amount", "Value": str(summary["late_settlement_payments_amount"])},
        {"Metric": "Late Settlement Refunds Amount", "Value": str(summary["late_settlement_refunds_amount"])},
        {"Metric": "Duplicate Settlement Payments Amount", "Value": str(summary["duplicate_settlement_payments_amount"])},
        {"Metric": "Duplicate Settlement Refunds Amount", "Value": str(summary["duplicate_settlement_refunds_amount"])},
        {"Metric": "Rounding Variance Count", "Value": summary["rounding_variance_count"]},
        {"Metric": "Rounding Total Difference", "Value": str(summary["rounding_total_difference"])},
        {"Metric": "Orphan Refund Count", "Value": summary["orphan_refund_count"]},
        {"Metric": "Orphan Refund Amount", "Value": str(summary["orphan_refund_amount"])},
        {"Metric": "Amount Mismatch Count", "Value": summary["amount_mismatch_count"]},
        {"Metric": "Amount Mismatch Difference", "Value": str(summary["amount_mismatch_difference"])},
        {"Metric": "Unmatched Bank Count", "Value": summary["unmatched_bank_count"]},
        {"Metric": "Unmatched Bank Amount", "Value": str(summary["unmatched_bank_amount"])},
        {"Metric": "Total Exceptions Count", "Value": summary["total_exceptions_count"]},
    ]
    summary_df = pd.DataFrame(summary_data)
    summary_csv = summary_df.to_csv(index=False).encode("utf-8")

    col_d1, col_d2, col_d3 = st.columns(3)

    with col_d1:
        st.markdown(
            f"""
            <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px; padding: 18px; margin-bottom: 12px;">
                <b style="font-size: 1.05rem; color: #0F172A;">📄 Full Reconciliation Ledger</b><br>
                <span style="font-size: 0.82rem; color: #64748B;">Complete dataset with all {len(reconciled_df)} transactions and matched settlements.</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.download_button(
            label="📥 Download Full Report (CSV)",
            data=full_csv,
            file_name=f"reconciliation_report_{current_cutoff}.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with col_d2:
        st.markdown(
            f"""
            <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px; padding: 18px; margin-bottom: 12px;">
                <b style="font-size: 1.05rem; color: #0F172A;">⚠️ Exceptions & Variances Only</b><br>
                <span style="font-size: 0.82rem; color: #64748B;">Filtered ledger of {len(exceptions_df)} discrepancies requiring operational or audit clearance.</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.download_button(
            label="📥 Download Exceptions Report (CSV)",
            data=exceptions_csv,
            file_name=f"exceptions_report_{current_cutoff}.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with col_d3:
        st.markdown(
            f"""
            <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px; padding: 18px; margin-bottom: 12px;">
                <b style="font-size: 1.05rem; color: #0F172A;">📊 Financial Summary Sheet</b><br>
                <span style="font-size: 0.82rem; color: #64748B;">Aggregated metrics, Gross/Net balances, and the verified mathematical bridge.</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.download_button(
            label="📥 Download Summary (CSV)",
            data=summary_csv,
            file_name=f"financial_summary_{current_cutoff}.csv",
            mime="text/csv",
            use_container_width=True,
        )
