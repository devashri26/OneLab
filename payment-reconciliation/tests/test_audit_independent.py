"""Independent Financial Reconciliation Auditor Verification Test Suite.

Specifically audits:
- Duplicate settlement handling (credits and debits)
- Cumulative partial refunds exceeding original payment
- Invalid refund references (refund pointing to another refund)
- Unsettled payments vs. unsettled refunds
- Late settlement of payments vs. late settlement of refunds
- Strict month-end cutoff boundaries without post-cutoff leakage
- Exact 0.00 paisa mathematical reconciliation bridge
"""

from datetime import date
from decimal import Decimal
import pandas as pd
import pytest

from config import (
    TransactionType,
    PlatformStatus,
    ReconciliationStatus,
)
from reconciliation import reconcile_transactions


# =====================================================================
# AUDIT TC01: Cumulative Partial Refunds Exceeding Original Payment
# =====================================================================
def test_audit_cumulative_partial_refunds():
    """Verify that multiple partial refunds against a single payment are tracked cumulatively."""
    txns = pd.DataFrame([
        {
            "transaction_id": "TXN_ORIG",
            "transaction_date": "2026-01-05",
            "amount": "2000.00",
            "transaction_type": TransactionType.PAYMENT.value,
            "original_transaction_id": "",
            "status": PlatformStatus.SUCCESS.value,
        },
        {
            "transaction_id": "TXN_REF1",
            "transaction_date": "2026-01-10",
            "amount": "800.00",
            "transaction_type": TransactionType.REFUND.value,
            "original_transaction_id": "TXN_ORIG",
            "status": PlatformStatus.REFUNDED.value,
        },
        {
            "transaction_id": "TXN_REF2",
            "transaction_date": "2026-01-15",
            "amount": "1000.00",
            "transaction_type": TransactionType.REFUND.value,
            "original_transaction_id": "TXN_ORIG",
            "status": PlatformStatus.REFUNDED.value,
        },
        {
            "transaction_id": "TXN_REF3_EXCESS",
            "transaction_date": "2026-01-20",
            "amount": "500.00",  # 800 + 1000 + 500 = 2300 > 2000
            "transaction_type": TransactionType.REFUND.value,
            "original_transaction_id": "TXN_ORIG",
            "status": PlatformStatus.REFUNDED.value,
        },
    ])
    settles = pd.DataFrame([
        {"settlement_id": "SET_ORIG", "transaction_id": "TXN_ORIG", "settlement_date": "2026-01-07", "amount": "2000.00", "transaction_type": TransactionType.PAYMENT.value},
        {"settlement_id": "SET_REF1", "transaction_id": "TXN_REF1", "settlement_date": "2026-01-12", "amount": "800.00", "transaction_type": TransactionType.REFUND.value},
        {"settlement_id": "SET_REF2", "transaction_id": "TXN_REF2", "settlement_date": "2026-01-17", "amount": "1000.00", "transaction_type": TransactionType.REFUND.value},
        {"settlement_id": "SET_REF3", "transaction_id": "TXN_REF3_EXCESS", "settlement_date": "2026-01-22", "amount": "500.00", "transaction_type": TransactionType.REFUND.value},
    ])

    reconciled_df, exceptions_df, summary, _ = reconcile_transactions(txns, settles)

    ref1 = reconciled_df[reconciled_df["transaction_id"] == "TXN_REF1"].iloc[0]
    ref2 = reconciled_df[reconciled_df["transaction_id"] == "TXN_REF2"].iloc[0]
    ref3 = reconciled_df[reconciled_df["transaction_id"] == "TXN_REF3_EXCESS"].iloc[0]

    assert ref1["reconciliation_status"] == ReconciliationStatus.MATCHED.value
    assert ref2["reconciliation_status"] == ReconciliationStatus.MATCHED.value
    assert ref3["reconciliation_status"] == ReconciliationStatus.REFUND_EXCEEDS_PAYMENT.value
    assert summary["refund_exceeds_payment_count"] == 1


# =====================================================================
# AUDIT TC02: Refund Referencing Another Refund is Rejected
# =====================================================================
def test_audit_refund_referencing_non_payment():
    """Verify that a refund citing an original transaction that is NOT a payment is classified as ORPHAN_REFUND."""
    txns = pd.DataFrame([
        {
            "transaction_id": "TXN_REF_BASE",
            "transaction_date": "2026-01-05",
            "amount": "500.00",
            "transaction_type": TransactionType.REFUND.value,
            "original_transaction_id": "",
            "status": PlatformStatus.REFUNDED.value,
        },
        {
            "transaction_id": "TXN_INVALID_CHAIN",
            "transaction_date": "2026-01-10",
            "amount": "500.00",
            "transaction_type": TransactionType.REFUND.value,
            "original_transaction_id": "TXN_REF_BASE",
            "status": PlatformStatus.REFUNDED.value,
        },
    ])
    settles = pd.DataFrame([
        {"settlement_id": "SET_A", "transaction_id": "TXN_REF_BASE", "settlement_date": "2026-01-07", "amount": "500.00", "transaction_type": TransactionType.REFUND.value},
        {"settlement_id": "SET_B", "transaction_id": "TXN_INVALID_CHAIN", "settlement_date": "2026-01-12", "amount": "500.00", "transaction_type": TransactionType.REFUND.value},
    ])

    reconciled_df, exceptions_df, summary, _ = reconcile_transactions(txns, settles)

    chain_row = reconciled_df[reconciled_df["transaction_id"] == "TXN_INVALID_CHAIN"].iloc[0]
    assert chain_row["reconciliation_status"] == ReconciliationStatus.ORPHAN_REFUND.value


# =====================================================================
# AUDIT TC03: Unsettled Payments vs. Unsettled Refunds Disaggregation
# =====================================================================
def test_audit_unsettled_payments_and_refunds():
    """Verify that unsettled payments (missing credit) and unsettled refunds (missing debit) are disaggregated."""
    txns = pd.DataFrame([
        {
            "transaction_id": "TXN_UNSETTLED_PAY",
            "transaction_date": "2026-01-30",
            "amount": "1500.00",
            "transaction_type": TransactionType.PAYMENT.value,
            "original_transaction_id": "",
            "status": PlatformStatus.SUCCESS.value,
        },
        {
            "transaction_id": "TXN_UNSETTLED_REF",
            "transaction_date": "2026-01-30",
            "amount": "300.00",
            "transaction_type": TransactionType.REFUND.value,
            "original_transaction_id": "TXN_UNSETTLED_PAY",
            "status": PlatformStatus.REFUNDED.value,
        },
    ])
    settles = pd.DataFrame(columns=["settlement_id", "transaction_id", "settlement_date", "amount", "transaction_type"])

    reconciled_df, exceptions_df, summary, _ = reconcile_transactions(txns, settles)

    assert summary["unsettled_payments_count"] == 1
    assert summary["unsettled_payments_amount"] == Decimal("1500.00")
    assert summary["unsettled_refunds_count"] == 1
    assert summary["unsettled_refunds_amount"] == Decimal("300.00")
    assert summary["bridge_discrepancy"] == Decimal("0.00")


# =====================================================================
# AUDIT TC04: Late Settlement of Payments vs. Late Settlement of Refunds
# =====================================================================
def test_audit_late_settlements_payments_and_refunds():
    """Verify that late payments and late refunds crossing month-end are handled with correct cash signs."""
    txns = pd.DataFrame([
        {
            "transaction_id": "TXN_LATE_PAY",
            "transaction_date": "2026-01-31",
            "amount": "4000.00",
            "transaction_type": TransactionType.PAYMENT.value,
            "original_transaction_id": "",
            "status": PlatformStatus.SUCCESS.value,
        },
        {
            "transaction_id": "TXN_LATE_REF",
            "transaction_date": "2026-01-31",
            "amount": "800.00",
            "transaction_type": TransactionType.REFUND.value,
            "original_transaction_id": "TXN_LATE_PAY",
            "status": PlatformStatus.REFUNDED.value,
        },
    ])
    settles = pd.DataFrame([
        {"settlement_id": "SET_LP", "transaction_id": "TXN_LATE_PAY", "settlement_date": "2026-02-01", "amount": "4000.00", "transaction_type": TransactionType.PAYMENT.value},
        {"settlement_id": "SET_LR", "transaction_id": "TXN_LATE_REF", "settlement_date": "2026-02-01", "amount": "800.00", "transaction_type": TransactionType.REFUND.value},
    ])

    reconciled_df, exceptions_df, summary, _ = reconcile_transactions(txns, settles, cutoff_date="2026-01-31")

    assert summary["late_settlement_payments_amount"] == Decimal("4000.00")
    assert summary["late_settlement_refunds_amount"] == Decimal("800.00")
    assert summary["bridge_discrepancy"] == Decimal("0.00")


# =====================================================================
# AUDIT TC05: Complete Multi-Anomaly Universal Reconciliation Bridge
# =====================================================================
def test_audit_universal_reconciliation_bridge():
    """Exhaustive test featuring every anomaly and verifying that the bridge equation balances to 0.00 paisa."""
    txns = pd.DataFrame([
        # Matched Payment & Refund
        {"transaction_id": "TXN_M_PAY", "transaction_date": "2026-01-10", "amount": "10000.00", "transaction_type": "PAYMENT", "original_transaction_id": "", "status": "SUCCESS"},
        {"transaction_id": "TXN_M_REF", "transaction_date": "2026-01-12", "amount": "1000.00", "transaction_type": "REFUND", "original_transaction_id": "TXN_M_PAY", "status": "REFUNDED"},
        # Late Settlement (cross cutoff)
        {"transaction_id": "TXN_LATE", "transaction_date": "2026-01-31", "amount": "3000.00", "transaction_type": "PAYMENT", "original_transaction_id": "", "status": "SUCCESS"},
        # Unsettled (in-transit)
        {"transaction_id": "TXN_UNSETTLE", "transaction_date": "2026-01-31", "amount": "1200.00", "transaction_type": "PAYMENT", "original_transaction_id": "", "status": "SUCCESS"},
        # Rounding Variance
        {"transaction_id": "TXN_RND", "transaction_date": "2026-01-15", "amount": "500.00", "transaction_type": "PAYMENT", "original_transaction_id": "", "status": "SUCCESS"},
        # Amount Mismatch
        {"transaction_id": "TXN_MIS", "transaction_date": "2026-01-16", "amount": "800.00", "transaction_type": "PAYMENT", "original_transaction_id": "", "status": "SUCCESS"},
        # Duplicate Base
        {"transaction_id": "TXN_DUP", "transaction_date": "2026-01-18", "amount": "2500.00", "transaction_type": "PAYMENT", "original_transaction_id": "", "status": "SUCCESS"},
    ])

    settles = pd.DataFrame([
        # Matched
        {"settlement_id": "SET_MP", "transaction_id": "TXN_M_PAY", "settlement_date": "2026-01-11", "amount": "10000.00", "transaction_type": "PAYMENT"},
        {"settlement_id": "SET_MR", "transaction_id": "TXN_M_REF", "settlement_date": "2026-01-13", "amount": "1000.00", "transaction_type": "REFUND"},
        # Late settlement arriving in Feb
        {"settlement_id": "SET_LATE", "transaction_id": "TXN_LATE", "settlement_date": "2026-02-01", "amount": "3000.00", "transaction_type": "PAYMENT"},
        # Rounding (+0.03)
        {"settlement_id": "SET_RND", "transaction_id": "TXN_RND", "settlement_date": "2026-01-16", "amount": "500.03", "transaction_type": "PAYMENT"},
        # Mismatch (+50.00)
        {"settlement_id": "SET_MIS", "transaction_id": "TXN_MIS", "settlement_date": "2026-01-17", "amount": "850.00", "transaction_type": "PAYMENT"},
        # Duplicate (SET_DUP_1 matches, SET_DUP_2 is duplicate)
        {"settlement_id": "SET_DUP_1", "transaction_id": "TXN_DUP", "settlement_date": "2026-01-19", "amount": "2500.00", "transaction_type": "PAYMENT"},
        {"settlement_id": "SET_DUP_2", "transaction_id": "TXN_DUP", "settlement_date": "2026-01-20", "amount": "2500.00", "transaction_type": "PAYMENT"},
        # Orphan Refund
        {"settlement_id": "SET_ORPH", "transaction_id": "TXN_GHOST_REFUND", "settlement_date": "2026-01-22", "amount": "400.00", "transaction_type": "REFUND"},
        # Unmatched Bank Credit
        {"settlement_id": "SET_UNMATCH", "transaction_id": "TXN_GHOST_CREDIT", "settlement_date": "2026-01-23", "amount": "600.00", "transaction_type": "PAYMENT"},
    ])

    reconciled_df, exceptions_df, summary, _ = reconcile_transactions(txns, settles, cutoff_date="2026-01-31")

    # Assert exact 0.00 paisa reconciliation
    assert summary["bridge_discrepancy"] == Decimal("0.00")
    
    # Assert Disaggregated Gross Payment & Refund Ledgers
    assert summary["platform_total_payments"] == Decimal("18000.00")
    assert summary["platform_total_refunds"] == Decimal("1000.00")
    assert summary["platform_net_amount"] == Decimal("17000.00")

    assert summary["bank_total_payments_period"] == Decimal("16950.03")
    assert summary["bank_total_refunds_period"] == Decimal("1400.00")
    assert summary["bank_net_amount_period"] == Decimal("15550.03")

    # Net reconciliation gap
    assert summary["net_reconciliation_difference"] == Decimal("-1449.97")
