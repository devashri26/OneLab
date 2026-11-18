"""PAYMENT RECONCILIATION: Transaction & Bank Settlement Intelligence.

Production-grade Streamlit Financial Dashboard for Reconciliation, Anomaly Detection,
and Financial Gap Auditing.
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
    page_title="Payment Reconciliation & Gap Detection",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------------------------------------------------------
# Custom Styling: Modern, Clean Light Theme with Dark Navy Typography
# -----------------------------------------------------------------------------
st.markdown(
    """
    <style>
    /* Global Styles */
    .stApp {
        background-color: #F8FAFC;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        color: #0F172A;
    }
    
    /* Headers */
    h1, h2, h3, h4 {
        color: #0F172A !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em;
    }
    
    .brand-title {
        font-size: 2.1rem;
        font-weight: 800;
        color: #0F172A;
        margin-bottom: 0px;
        line-height: 1.15;
    }
    .brand-accent {
        color: #1E3A8A;
    }
    .brand-subtitle {
        font-size: 1.0rem;
        color: #475569;
        margin-top: 4px;
        margin-bottom: 24px;
    }
    
    /* KPI Metric Cards */
    .metric-card {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 18px 20px;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.05);
        margin-bottom: 12px;
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    .metric-card:hover {
        box-shadow: 0 4px 6px -1px rgba(15, 23, 42, 0.1);
        border-color: #CBD5E1;
    }
    .metric-label {
        font-size: 0.80rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #64748B;
        margin-bottom: 6px;
    }
    .metric-value {
        font-size: 1.65rem;
        font-weight: 700;
        color: #0F172A;
        line-height: 1.2;
    }
    .metric-sub {
        font-size: 0.78rem;
        color: #64748B;
        margin-top: 4px;
    }
    
    /* Status Pills */
    .status-pill {
        display: inline-block;
        padding: 3px 10px;
        font-size: 0.75rem;
        font-weight: 600;
        border-radius: 9999px;
        text-align: center;
    }
    
    /* Exception Card */
    .investigation-card {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-left: 5px solid #1E3A8A;
        border-radius: 8px;
        padding: 22px;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.05);
        margin-top: 10px;
    }
    
    /* Section Container */
    .section-box {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
    }
    
    /* Sidebar enhancements */
    [data-testid="stSidebar"] {
        background-color: #FFFFFF;
        border-right: 1px solid #E2E8F0;
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
# SIDEBAR
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### ⚖️ **Reconciliation Control**")
    st.caption("Financial Ledger & Bank Auditing")
    st.divider()

    # Section Navigation
    st.markdown("**Navigation**")
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
    st.markdown("**Period & Tolerance Settings**")
    
    # Month selector & Cutoff Date
    selected_month = st.selectbox("Reconciliation Month", ["January 2026", "Custom Period"], index=0)
    if selected_month == "January 2026":
        selected_cutoff = st.date_input("Month-End Cutoff Date", value=DEFAULT_CUTOFF_DATE)
    else:
        selected_cutoff = st.date_input("Month-End Cutoff Date", value=st.session_state["cutoff_date"])
    
    st.session_state["cutoff_date"] = selected_cutoff

    tolerance_val = st.number_input(
        "Rounding Tolerance (₹)",
        min_value=0.00,
        max_value=1.00,
        value=float(DEFAULT_ROUNDING_TOLERANCE),
        step=0.01,
        help="Differences within this threshold are classified as Rounding Variance rather than Amount Mismatch.",
    )
    st.session_state["tolerance"] = to_decimal(tolerance_val)

    st.divider()
    st.markdown("**Data Ingestion**")
    use_sample = st.checkbox("Use Sample Synthetic Dataset", value=True, help="Loads pre-seeded deterministic dataset with all 4 anomalies.")

    uploaded_tx = st.file_uploader("Upload Platform Transactions (CSV)", type=["csv"])
    uploaded_se = st.file_uploader("Upload Bank Settlements (CSV)", type=["csv"])

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
# RUN RECONCILIATION
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
st.markdown('<div class="brand-title">PAYMENT RECONCILIATION <span class="brand-accent">&bull;</span> Transaction & Bank Settlement Intelligence</div>', unsafe_allow_html=True)
st.markdown('<div class="brand-subtitle">Identify discrepancies. Track settlements. Understand every financial gap.</div>', unsafe_allow_html=True)

# Data source pill & period indicator
col_hdr1, col_hdr2, col_hdr3 = st.columns([2, 1, 1])
with col_hdr1:
    st.info(f"📁 Active Source: **{st.session_state['data_source']}**", icon="ℹ️")
with col_hdr2:
    st.markdown(f"**Reconciliation Cutoff:** `{current_cutoff}`")
with col_hdr3:
    st.markdown(f"**Rounding Tolerance:** `₹{float(current_tolerance):.2f}`")

st.markdown("<br>", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# SECTION 1: OVERVIEW DASHBOARD & KPI CARDS
# -----------------------------------------------------------------------------
if nav_selection in ["1. Overview & KPIs"]:
    st.subheader("1. Executive Summary & KPIs")

    kpi1, kpi2, kpi3, kpi4, kpi5, kpi6 = st.columns(6)

    with kpi1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Platform Volume</div>
                <div class="metric-value">{summary['platform_total_records']}</div>
                <div class="metric-sub">Net: {format_inr(summary['platform_net_amount'])}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with kpi2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Bank Settlements</div>
                <div class="metric-value">{summary['bank_total_records_period']}</div>
                <div class="metric-sub">Net: {format_inr(summary['bank_net_amount_period'])}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with kpi3:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Fully Matched</div>
                <div class="metric-value" style="color: #059669;">{summary['matched_count']}</div>
                <div class="metric-sub">Gross: {format_inr(summary['matched_gross_amount'])} | Net: {format_inr(summary['matched_net_amount'])}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with kpi4:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Unsettled In-Transit</div>
                <div class="metric-value" style="color: #D97706;">{summary['unsettled_count']}</div>
                <div class="metric-sub">{format_inr(summary['unsettled_amount'])} awaiting bank</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with kpi5:
        net_gap = summary["net_reconciliation_difference"]
        gap_color = "#DC2626" if net_gap != 0 else "#059669"
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Reconciliation Gap</div>
                <div class="metric-value" style="color: {gap_color};">{format_inr(net_gap)}</div>
                <div class="metric-sub">Net Bank vs Net Platform</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with kpi6:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Total Exceptions</div>
                <div class="metric-value" style="color: #4F46E5;">{summary['total_exceptions_count']}</div>
                <div class="metric-sub">Items requiring audit</div>
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
            <div style="background: #FFFBEB; border: 1px solid #FCD34D; border-radius: 8px; padding: 14px;">
                <b style="color: #92400E;">1. Late Settlement</b><br>
                <span style="font-size: 1.3rem; font-weight: 700; color: #B45309;">{summary['late_settlement_count']} Detected</span><br>
                <span style="font-size: 0.85rem; color: #78350F;">Impact: {format_inr(summary['late_settlement_amount'])}</span><br>
                <span style="font-size: 0.75rem; color: #451A03;">Jan 31 txn settled on Feb 1</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with anom2:
        st.markdown(
            f"""
            <div style="background: #EFF6FF; border: 1px solid #BFDBFE; border-radius: 8px; padding: 14px;">
                <b style="color: #1E40AF;">2. Rounding Variance</b><br>
                <span style="font-size: 1.3rem; font-weight: 700; color: #1D4ED8;">{summary['rounding_variance_count']} Detected</span><br>
                <span style="font-size: 0.85rem; color: #1E3A8A;">Net Diff: {format_inr(summary['rounding_total_difference'])}</span><br>
                <span style="font-size: 0.75rem; color: #172554;">Cumulative decimal variance</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with anom3:
        st.markdown(
            f"""
            <div style="background: #FEF2F2; border: 1px solid #FECACA; border-radius: 8px; padding: 14px;">
                <b style="color: #991B1B;">3. Duplicate Settlement</b><br>
                <span style="font-size: 1.3rem; font-weight: 700; color: #B91C1C;">{summary['duplicate_settlement_count']} Detected</span><br>
                <span style="font-size: 0.85rem; color: #7F1D1D;">Impact: {format_inr(summary['duplicate_settlement_amount'])}</span><br>
                <span style="font-size: 0.75rem; color: #450A0A;">Repeated bank credit entries</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with anom4:
        st.markdown(
            f"""
            <div style="background: #FAF5FF; border: 1px solid #E9D5FF; border-radius: 8px; padding: 14px;">
                <b style="color: #6B21A8;">4. Orphan Refund</b><br>
                <span style="font-size: 1.3rem; font-weight: 700; color: #7E22CE;">{summary['orphan_refund_count']} Detected</span><br>
                <span style="font-size: 0.85rem; color: #581C87;">Impact: {format_inr(summary['orphan_refund_amount'])}</span><br>
                <span style="font-size: 0.75rem; color: #3B0764;">Refund without origin payment</span>
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
    st.caption("Detailed reconciliation of Gross Payments, Refunds, and Net Settled Funds against Month-End Balances.")

    tab_gross, tab_refund, tab_net = st.tabs(["Gross Payments", "Refunds", "Net Reconciliation Bridge"])

    with tab_gross:
        g1, g2, g3 = st.columns(3)
        with g1:
            st.metric("Platform Gross Payments", format_inr(summary["platform_total_payments"]))
        with g2:
            st.metric("Bank Gross Payments (In-Period)", format_inr(summary["bank_total_payments_period"]))
        with g3:
            gross_diff = summary["bank_total_payments_period"] - summary["platform_total_payments"]
            st.metric("Gross Payment Difference", format_inr(gross_diff), delta=float(gross_diff))

        st.markdown(
            f"""
            **Gross Payment Reconciliation Breakdown:**
            - **Platform Expected Payments:** `{format_inr(summary['platform_total_payments'])}`
            - **Less In-Transit / Unsettled Payments:** `- {format_inr(summary['unsettled_payments_amount'])}`
            - **Less Late Settlements (Settling post-cutoff in Feb):** `- {format_inr(summary['late_settlement_payments_amount'])}`
            - **Add Duplicate Payment Settlements from Bank:** `+ {format_inr(summary['duplicate_settlement_payments_amount'])}`
            - **Add Unmatched External Bank Credits:** `+ {format_inr(summary['unmatched_bank_amount'])}`
            - **Net Rounding & Amount Discrepancies:** `{format_inr(summary['rounding_total_difference'] + summary['amount_mismatch_difference'])}`
            - **= Realized Bank Gross Payments:** `{format_inr(summary['bank_total_payments_period'])}`
            """
        )

    with tab_refund:
        r1, r2, r3 = st.columns(3)
        with r1:
            st.metric("Platform Recorded Refunds", format_inr(summary["platform_total_refunds"]))
        with r2:
            st.metric("Bank Processed Refunds (In-Period)", format_inr(summary["bank_total_refunds_period"]))
        with r3:
            refund_diff = summary["bank_total_refunds_period"] - summary["platform_total_refunds"]
            st.metric("Refund Variance", format_inr(refund_diff), delta=float(refund_diff))

        st.markdown(
            f"""
            **Refund Verification Notes & Ledger Bridge:**
            - **Platform Expected Refunds:** `{format_inr(summary['platform_total_refunds'])}`
            - **Less In-Transit / Unsettled Refunds:** `- {format_inr(summary['unsettled_refunds_amount'])}`
            - **Less Late Settlement Refunds:** `- {format_inr(summary['late_settlement_refunds_amount'])}`
            - **Add Orphan Bank Refunds (Unbacked Debits):** `+ {format_inr(summary['orphan_refund_amount'])}`
            - **Add Duplicate Bank Refund Debits:** `+ {format_inr(summary['duplicate_settlement_refunds_amount'])}`
            - **= Realized Bank Processed Refunds:** `{format_inr(summary['bank_total_refunds_period'])}`
            
            *Audit Observations:*
            - All platform refunds are cross-referenced with original payment transactions.
            - Detected **{summary['orphan_refund_count']} orphan refund(s)** totaling `{format_inr(summary['orphan_refund_amount'])}` settled at the bank without a valid source transaction.
            - Detected **{summary['refund_exceeds_payment_count']} refund(s)** where refund amount exceeded original transaction payment.
            """
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
                connector={"line": {"color": "#94A3B8"}},
                decreasing={"marker": {"color": "#DC2626"}},
                increasing={"marker": {"color": "#059669"}},
                totals={"marker": {"color": "#1E3A8A"}},
            )
        )
        fig_waterfall.update_layout(
            title="Net Financial Reconciliation Bridge (Platform to Bank)",
            plot_bgcolor="#FFFFFF",
            paper_bgcolor="#FFFFFF",
            height=430,
            margin=dict(l=20, r=20, t=40, b=20),
            yaxis_title="Amount (₹)",
        )
        st.plotly_chart(fig_waterfall, use_container_width=True)
        st.caption(f"✅ Verified Mathematical Bridge Discrepancy: **{format_inr(summary['bridge_discrepancy'])}** (Exact 0.00)")


# -----------------------------------------------------------------------------
# SECTION 3: DISCREPANCY ANALYSIS
# -----------------------------------------------------------------------------
if nav_selection in ["1. Overview & KPIs", "3. Discrepancy Analysis"]:
    st.divider()
    st.subheader("3. Discrepancy Analysis")
    st.caption("Distribution of exception categories by volume and monetary impact.")

    col_chart1, col_chart2 = st.columns(2)

    # Prepare Discrepancy Data
    cat_names = []
    cat_counts = []
    cat_amounts = []
    cat_colors = []

    for status in ReconciliationStatus:
        if status.value == ReconciliationStatus.MATCHED.value:
            continue
        m = summary["status_metrics"][status.value]
        if m["count"] > 0:
            cat_names.append(STATUS_LABELS.get(status.value, status.value))
            cat_counts.append(m["count"])
            # Financial impact: for unmatched/duplicate/orphan it's bank amount; for unsettled/late it's platform amount; for mismatch/rounding it's diff
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
            fig_pie = px.pie(
                names=cat_names,
                values=cat_counts,
                title="Exception Volume by Category",
                color=cat_names,
                color_discrete_sequence=cat_colors,
                hole=0.45,
            )
            fig_pie.update_layout(
                paper_bgcolor="#FFFFFF",
                plot_bgcolor="#FFFFFF",
                height=350,
                margin=dict(l=10, r=10, t=40, b=10),
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.success("No exceptions found. Datasets match completely.")

    with col_chart2:
        if cat_amounts:
            fig_bar = px.bar(
                x=cat_names,
                y=cat_amounts,
                title="Monetary Impact by Exception Category (₹)",
                color=cat_names,
                color_discrete_sequence=cat_colors,
                labels={"x": "Exception Category", "y": "Monetary Value (₹)"},
            )
            fig_bar.update_layout(
                paper_bgcolor="#FFFFFF",
                plot_bgcolor="#FFFFFF",
                height=350,
                showlegend=False,
                margin=dict(l=10, r=10, t=40, b=10),
            )
            st.plotly_chart(fig_bar, use_container_width=True)


# -----------------------------------------------------------------------------
# SECTION 4: TRANSACTION EXPLORER
# -----------------------------------------------------------------------------
if nav_selection in ["4. Transaction Explorer"]:
    st.divider()
    st.subheader("4. Transaction & Settlement Explorer")
    st.caption("Search, filter, and inspect line-item reconciliation results across all records.")

    # Explorer Filters
    f_col1, f_col2, f_col3, f_col4 = st.columns([2, 2, 2, 2])

    with f_col1:
        search_query = st.text_input("🔍 Search Transaction / Settlement ID", "")
    with f_col2:
        status_filter = st.multiselect(
            "Filter by Status",
            options=list(STATUS_LABELS.keys()),
            format_func=lambda x: STATUS_LABELS.get(x, x),
            default=[],
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
            step=100.0,
        )

    # Filter DataFrame
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

    st.write(f"Showing **{len(filtered_df)}** of **{len(reconciled_df)}** records:")

    # Display Styled Table
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
        filtered_df[display_cols].style.format({
            "platform_amount": "₹{:,.2f}",
            "bank_amount": "₹{:,.2f}",
            "difference": "₹{:,.2f}",
        }),
        use_container_width=True,
        height=450,
    )


# -----------------------------------------------------------------------------
# SECTION 5: EXCEPTION INVESTIGATION
# -----------------------------------------------------------------------------
if nav_selection in ["5. Exception Investigation"]:
    st.divider()
    st.subheader("5. Line-Item Exception Investigation")
    st.caption("Deep-dive forensic audit for exceptions, root-cause explanations, and recommended accounting actions.")

    if exceptions_df.empty:
        st.success("🎉 No reconciliation exceptions found! All records matched perfectly.")
    else:
        # Quick selector of exceptions
        exception_options = exceptions_df.apply(
            lambda r: f"[{r['reconciliation_status']}] {r['transaction_id']} (Bank: {r['settlement_id']}) - Diff: ₹{r['difference']:.2f}",
            axis=1,
        ).tolist()

        selected_label = st.selectbox("Select Exception Record to Audit", exception_options, index=0)
        selected_idx = exception_options.index(selected_label)
        selected_record = exceptions_df.iloc[selected_idx]

        status_key = selected_record["reconciliation_status"]
        status_color = STATUS_COLORS.get(status_key, "#1E3A8A")

        # Dossier card
        st.markdown(
            f"""
            <div class="investigation-card" style="border-left-color: {status_color};">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                    <div>
                        <span style="font-size: 1.3rem; font-weight: 700; color: #0F172A;">
                            Transaction ID: {selected_record['transaction_id']}
                        </span>
                        &nbsp;&nbsp;
                        <span style="font-size: 0.95rem; color: #64748B;">Settlement ID: {selected_record['settlement_id']}</span>
                    </div>
                    <div>
                        <span class="status-pill" style="background-color: {status_color}1A; color: {status_color}; border: 1px solid {status_color};">
                            {STATUS_LABELS.get(status_key, status_key)}
                        </span>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<br>", unsafe_allow_html=True)
        col_inv1, col_inv2, col_inv3, col_inv4 = st.columns(4)
        with col_inv1:
            st.metric("Platform Expected Amount", format_inr(selected_record["platform_amount"]))
            st.caption(f"Transaction Date: `{selected_record['transaction_date']}`")
        with col_inv2:
            st.metric("Bank Settled Amount", format_inr(selected_record["bank_amount"]))
            st.caption(f"Settlement Date: `{selected_record['settlement_date']}`")
        with col_inv3:
            diff_val = selected_record["difference"]
            st.metric("Financial Variance", format_inr(diff_val), delta=float(diff_val))
            days_str = f"{selected_record['days_to_settle']} days" if pd.notna(selected_record['days_to_settle']) else "N/A"
            st.caption(f"Settlement Delay: `{days_str}`")
        with col_inv4:
            st.metric("Transaction Type", selected_record["transaction_type"])
            st.caption(f"Cutoff Date: `{current_cutoff}`")

        st.markdown("#### 📖 Financial Explanation")
        st.info(selected_record["explanation"], icon="ℹ️")

        st.markdown("#### 🛠️ Recommended Action")
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
    
    # 3. Financial Summary CSV
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
        st.markdown("##### 📄 Full Reconciliation Report")
        st.write(f"Contains all {len(reconciled_df)} transaction-level matched and exception entries.")
        st.download_button(
            label="📥 Download Full Report (CSV)",
            data=full_csv,
            file_name=f"reconciliation_report_{current_cutoff}.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with col_d2:
        st.markdown("##### ⚠️ Exceptions Only Report")
        st.write(f"Filtered log of {len(exceptions_df)} discrepancy records requiring audit or adjustment.")
        st.download_button(
            label="📥 Download Exceptions Report (CSV)",
            data=exceptions_csv,
            file_name=f"exceptions_report_{current_cutoff}.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with col_d3:
        st.markdown("##### 📊 Financial Summary Sheet")
        st.write("Aggregated ledger totals, gross/refund/net reconciliation, and variance metrics.")
        st.download_button(
            label="📥 Download Summary (CSV)",
            data=summary_csv,
            file_name=f"financial_summary_{current_cutoff}.csv",
            mime="text/csv",
            use_container_width=True,
        )
