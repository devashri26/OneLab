"""Automated Test Suite for Payment Reconciliation and Gap Detection Engine.

Covers all 16 specified test cases (TC01 to TC16) with exact Decimal precision.
"""

from datetime import date
from decimal import Decimal
import pandas as pd
import pytest

from config import (
    DEFAULT_CUTOFF_DATE,
    DEFAULT_ROUNDING_TOLERANCE,
    TransactionType,
    PlatformStatus,
    ReconciliationStatus,
)
from reconciliation import reconcile_transactions
from utils import validate_transactions_csv, validate_settlements_csv, to_decimal


def _create_sample_txn(
    txn_id: str = "TXN1001",
    txn_date: str = "2026-01-15",
    amount: str = "1000.00",
    txn_type: str = TransactionType.PAYMENT.value,
    orig_id: str = "",
    status: str = PlatformStatus.SUCCESS.value,
) -> dict:
    return {
        "transaction_id": txn_id,
        "transaction_date": txn_date,
        "amount": amount,
        "transaction_type": txn_type,
        "original_transaction_id": orig_id,
        "status": status,
    }


def _create_sample_settle(
    settle_id: str = "SET5001",
    txn_id: str = "TXN1001",
    settle_date: str = "2026-01-17",
    amount: str = "1000.00",
    txn_type: str = TransactionType.PAYMENT.value,
) -> dict:
    return {
        "settlement_id": settle_id,
        "transaction_id": txn_id,
        "settlement_date": settle_date,
        "amount": amount,
        "transaction_type": txn_type,
    }


# =====================================================================
# TC01: Normal Successful Matching
# =====================================================================
def test_tc01_normal_successful_matching():
    """TC01: Verify that identical transactions and settlements are classified as MATCHED."""
    txns = pd.DataFrame([_create_sample_txn("TXN1001", "2026-01-10", "1500.00")])
    settles = pd.DataFrame([_create_sample_settle("SET5001", "TXN1001", "2026-01-12", "1500.00")])

    reconciled_df, exceptions_df, summary, _ = reconcile_transactions(txns, settles)

    assert len(reconciled_df) == 1
    assert reconciled_df.iloc[0]["reconciliation_status"] == ReconciliationStatus.MATCHED.value
    assert reconciled_df.iloc[0]["difference"] == 0.0
    assert len(exceptions_df) == 0
    assert summary["matched_count"] == 1
    assert summary["matched_platform_amount"] == Decimal("1500.00")
    assert summary["matched_bank_amount"] == Decimal("1500.00")


# =====================================================================
# TC02: Platform Transaction with No Settlement (UNSETTLED)
# =====================================================================
def test_tc02_platform_transaction_no_settlement():
    """TC02: Verify that an unsettled platform transaction is classified as UNSETTLED."""
    txns = pd.DataFrame([_create_sample_txn("TXN1002", "2026-01-25", "2500.00")])
    settles = pd.DataFrame(columns=["settlement_id", "transaction_id", "settlement_date", "amount", "transaction_type"])

    reconciled_df, exceptions_df, summary, _ = reconcile_transactions(txns, settles)

    assert len(reconciled_df) == 1
    assert reconciled_df.iloc[0]["reconciliation_status"] == ReconciliationStatus.UNSETTLED.value
    assert len(exceptions_df) == 1
    assert summary["unsettled_count"] == 1
    assert summary["unsettled_amount"] == Decimal("2500.00")


# =====================================================================
# TC03: January Transaction Settled in February (LATE_SETTLEMENT)
# =====================================================================
def test_tc03_january_transaction_settled_in_february():
    """TC03: Scenario 1 - Transaction on Jan 31 settled on Feb 1 must be classified as LATE_SETTLEMENT."""
    txns = pd.DataFrame([_create_sample_txn("TXN1003", "2026-01-31", "4850.00")])
    settles = pd.DataFrame([_create_sample_settle("SET5003", "TXN1003", "2026-02-01", "4850.00")])

    reconciled_df, exceptions_df, summary, _ = reconcile_transactions(txns, settles, cutoff_date="2026-01-31")

    assert len(reconciled_df) == 1
    row = reconciled_df.iloc[0]
    assert row["reconciliation_status"] == ReconciliationStatus.LATE_SETTLEMENT.value
    assert row["transaction_date"] == "2026-01-31"
    assert row["settlement_date"] == "2026-02-01"
    assert row["days_to_settle"] == 1
    assert summary["late_settlement_count"] == 1
    assert summary["late_settlement_amount"] == Decimal("4850.00")


# =====================================================================
# TC04: Duplicate Bank Settlement (DUPLICATE_SETTLEMENT)
# =====================================================================
def test_tc04_duplicate_bank_settlement():
    """TC04: Scenario 3 - Repeated settlement records for one transaction must identify duplicate."""
    txns = pd.DataFrame([_create_sample_txn("TXN1004", "2026-01-18", "9500.00")])
    settles = pd.DataFrame([
        _create_sample_settle("SET5004A", "TXN1004", "2026-01-19", "9500.00"),
        _create_sample_settle("SET5004B", "TXN1004", "2026-01-20", "9500.00"),
    ])

    reconciled_df, exceptions_df, summary, _ = reconcile_transactions(txns, settles)

    # First settlement matches; second settlement is flagged as duplicate exception
    assert len(reconciled_df) == 2
    matched_entry = reconciled_df[reconciled_df["settlement_id"] == "SET5004A"].iloc[0]
    dup_entry = reconciled_df[reconciled_df["settlement_id"] == "SET5004B"].iloc[0]

    assert matched_entry["reconciliation_status"] == ReconciliationStatus.MATCHED.value
    assert dup_entry["reconciliation_status"] == ReconciliationStatus.DUPLICATE_SETTLEMENT.value
    assert len(exceptions_df) == 1
    assert summary["duplicate_settlement_count"] == 1
    assert summary["duplicate_settlement_amount"] == Decimal("9500.00")


# =====================================================================
# TC05: Amount Mismatch (AMOUNT_MISMATCH)
# =====================================================================
def test_tc05_amount_mismatch():
    """TC05: When amount difference exceeds tolerance, classify as AMOUNT_MISMATCH."""
    txns = pd.DataFrame([_create_sample_txn("TXN1005", "2026-01-12", "7500.00")])
    settles = pd.DataFrame([_create_sample_settle("SET5005", "TXN1005", "2026-01-14", "7450.00")])

    reconciled_df, exceptions_df, summary, _ = reconcile_transactions(txns, settles, rounding_tolerance=Decimal("0.05"))

    assert len(reconciled_df) == 1
    row = reconciled_df.iloc[0]
    assert row["reconciliation_status"] == ReconciliationStatus.AMOUNT_MISMATCH.value
    assert row["difference"] == -50.0
    assert summary["amount_mismatch_count"] == 1
    assert summary["amount_mismatch_difference"] == Decimal("-50.00")


# =====================================================================
# TC06: Individual Rounding Differences (ROUNDING_VARIANCE)
# =====================================================================
def test_tc06_individual_rounding_difference():
    """TC06: Variance within configured tolerance (<= 0.05) is classified as ROUNDING_VARIANCE."""
    txns = pd.DataFrame([_create_sample_txn("TXN1006", "2026-01-15", "3200.40")])
    settles = pd.DataFrame([_create_sample_settle("SET5006", "TXN1006", "2026-01-16", "3200.42")])

    reconciled_df, exceptions_df, summary, _ = reconcile_transactions(txns, settles, rounding_tolerance=Decimal("0.05"))

    assert len(reconciled_df) == 1
    row = reconciled_df.iloc[0]
    assert row["reconciliation_status"] == ReconciliationStatus.ROUNDING_VARIANCE.value
    assert round(row["difference"], 2) == 0.02
    assert summary["rounding_variance_count"] == 1


# =====================================================================
# TC07: Aggregate Rounding Variance
# =====================================================================
def test_tc07_aggregate_rounding_variance():
    """TC07: Scenario 2 - Multiple small decimal differences aggregate measurably."""
    txns_data = [
        _create_sample_txn("TXN701", "2026-01-15", "100.00"),
        _create_sample_txn("TXN702", "2026-01-16", "200.00"),
        _create_sample_txn("TXN703", "2026-01-17", "300.00"),
    ]
    settles_data = [
        _create_sample_settle("SET701", "TXN701", "2026-01-16", "100.02"),
        _create_sample_settle("SET702", "TXN702", "2026-01-17", "200.01"),
        _create_sample_settle("SET703", "TXN703", "2026-01-18", "300.02"),
    ]
    txns = pd.DataFrame(txns_data)
    settles = pd.DataFrame(settles_data)

    reconciled_df, exceptions_df, summary, _ = reconcile_transactions(txns, settles, rounding_tolerance=Decimal("0.05"))

    assert summary["rounding_variance_count"] == 3
    assert summary["rounding_platform_amount"] == Decimal("600.00")
    assert summary["rounding_bank_amount"] == Decimal("600.05")
    assert summary["rounding_total_difference"] == Decimal("0.05")


# =====================================================================
# TC08: Orphan Refund (ORPHAN_REFUND)
# =====================================================================
def test_tc08_orphan_refund():
    """TC08: Scenario 4 - Refund in bank settlement referencing non-existent platform transaction."""
    txns = pd.DataFrame([_create_sample_txn("TXN1001", "2026-01-10", "1500.00")])
    settles = pd.DataFrame([
        _create_sample_settle("SET5001", "TXN1001", "2026-01-12", "1500.00"),
        _create_sample_settle("SET_ORPHAN", "TXN_UNKNOWN_9999", "2026-01-20", "500.00", txn_type=TransactionType.REFUND.value),
    ])

    reconciled_df, exceptions_df, summary, _ = reconcile_transactions(txns, settles)

    orphan_rows = reconciled_df[reconciled_df["reconciliation_status"] == ReconciliationStatus.ORPHAN_REFUND.value]
    assert len(orphan_rows) == 1
    assert orphan_rows.iloc[0]["settlement_id"] == "SET_ORPHAN"
    assert summary["orphan_refund_count"] == 1
    assert summary["orphan_refund_amount"] == Decimal("500.00")


# =====================================================================
# TC09: Valid Refund (MATCHED)
# =====================================================================
def test_tc09_valid_refund_matching():
    """TC09: Legitimate refund referencing prior payment matches correctly."""
    txns = pd.DataFrame([
        _create_sample_txn("TXN1001", "2026-01-10", "2000.00", txn_type=TransactionType.PAYMENT.value),
        _create_sample_txn("TXN1002", "2026-01-14", "1000.00", txn_type=TransactionType.REFUND.value, orig_id="TXN1001", status=PlatformStatus.REFUNDED.value),
    ])
    settles = pd.DataFrame([
        _create_sample_settle("SET5001", "TXN1001", "2026-01-11", "2000.00", txn_type=TransactionType.PAYMENT.value),
        _create_sample_settle("SET5002", "TXN1002", "2026-01-15", "1000.00", txn_type=TransactionType.REFUND.value),
    ])

    reconciled_df, exceptions_df, summary, _ = reconcile_transactions(txns, settles)

    refund_row = reconciled_df[reconciled_df["transaction_id"] == "TXN1002"].iloc[0]
    assert refund_row["reconciliation_status"] == ReconciliationStatus.MATCHED.value
    assert len(exceptions_df) == 0
    assert summary["platform_total_refunds"] == Decimal("1000.00")
    assert summary["platform_net_amount"] == Decimal("1000.00")  # 2000 - 1000


# =====================================================================
# TC10: Refund Amount Exceeding Original Payment
# =====================================================================
def test_tc10_refund_exceeds_original_payment():
    """TC10: When a refund amount is greater than the original charge, flag discrepancy."""
    txns = pd.DataFrame([
        _create_sample_txn("TXN1001", "2026-01-10", "500.00", txn_type=TransactionType.PAYMENT.value),
        _create_sample_txn("TXN1002", "2026-01-14", "800.00", txn_type=TransactionType.REFUND.value, orig_id="TXN1001", status=PlatformStatus.REFUNDED.value),
    ])
    settles = pd.DataFrame([
        _create_sample_settle("SET5001", "TXN1001", "2026-01-11", "500.00", txn_type=TransactionType.PAYMENT.value),
        _create_sample_settle("SET5002", "TXN1002", "2026-01-15", "800.00", txn_type=TransactionType.REFUND.value),
    ])

    reconciled_df, exceptions_df, summary, _ = reconcile_transactions(txns, settles)

    excess_rows = reconciled_df[reconciled_df["reconciliation_status"] == ReconciliationStatus.REFUND_EXCEEDS_PAYMENT.value]
    assert len(excess_rows) == 1
    assert summary["refund_exceeds_payment_count"] == 1


# =====================================================================
# TC11: Unmatched Bank Settlement (UNMATCHED_BANK_ENTRY)
# =====================================================================
def test_tc11_unmatched_bank_settlement():
    """TC11: Bank credit settlement with no platform counterpart is UNMATCHED_BANK_ENTRY."""
    txns = pd.DataFrame(columns=["transaction_id", "transaction_date", "amount", "transaction_type", "original_transaction_id", "status"])
    settles = pd.DataFrame([_create_sample_settle("SET9999", "TXN_UNKNOWN_EXTERNAL", "2026-01-20", "6200.00")])

    reconciled_df, exceptions_df, summary, _ = reconcile_transactions(txns, settles)

    assert len(reconciled_df) == 1
    assert reconciled_df.iloc[0]["reconciliation_status"] == ReconciliationStatus.UNMATCHED_BANK_ENTRY.value
    assert summary["unmatched_bank_count"] == 1
    assert summary["unmatched_bank_amount"] == Decimal("6200.00")


# =====================================================================
# TC12: Invalid CSV Columns Validation
# =====================================================================
def test_tc12_invalid_csv_columns():
    """TC12: Schema validator reports missing columns without crashing."""
    bad_txns = pd.DataFrame([{"wrong_col": 123}])
    is_valid, errors = validate_transactions_csv(bad_txns)
    assert not is_valid
    assert any("Missing required transaction columns" in e for e in errors)

    bad_settles = pd.DataFrame([{"bad_col": 456}])
    s_valid, s_errors = validate_settlements_csv(bad_settles)
    assert not s_valid
    assert any("Missing required settlement columns" in e for e in s_errors)


# =====================================================================
# TC13: Empty Datasets
# =====================================================================
def test_tc13_empty_datasets():
    """TC13: Reconciling empty datasets returns empty DataFrames and zeroed metrics without crashing."""
    empty_txns = pd.DataFrame(columns=["transaction_id", "transaction_date", "amount", "transaction_type", "original_transaction_id", "status"])
    empty_settles = pd.DataFrame(columns=["settlement_id", "transaction_id", "settlement_date", "amount", "transaction_type"])

    reconciled_df, exceptions_df, summary, report = reconcile_transactions(empty_txns, empty_settles)

    assert reconciled_df.empty
    assert exceptions_df.empty
    assert summary["platform_total_payments"] == Decimal("0.00")
    assert summary["net_reconciliation_difference"] == Decimal("0.00")
    assert summary["total_exceptions_count"] == 0


# =====================================================================
# TC14: Month-end Cutoff Handling
# =====================================================================
def test_tc14_month_end_cutoff_handling():
    """TC14: Transactions after cutoff date are excluded from month's reconciliation."""
    txns = pd.DataFrame([
        _create_sample_txn("TXN_JAN", "2026-01-20", "1000.00"),
        _create_sample_txn("TXN_FEB", "2026-02-05", "2000.00"),
    ])
    settles = pd.DataFrame([
        _create_sample_settle("SET_JAN", "TXN_JAN", "2026-01-22", "1000.00"),
        _create_sample_settle("SET_FEB", "TXN_FEB", "2026-02-07", "2000.00"),
    ])

    reconciled_df, _, summary, _ = reconcile_transactions(txns, settles, cutoff_date="2026-01-31")

    # TXN_FEB is past cutoff, so platform period records must be only 1
    assert summary["platform_total_records"] == 1
    assert summary["platform_total_payments"] == Decimal("1000.00")


# =====================================================================
# TC15: Duplicate and Amount Mismatch Together
# =====================================================================
def test_tc15_duplicate_and_amount_mismatch_together():
    """TC15: When first settlement has amount mismatch and second is duplicate, both are categorized."""
    txns = pd.DataFrame([_create_sample_txn("TXN1015", "2026-01-10", "1000.00")])
    settles = pd.DataFrame([
        _create_sample_settle("SET15A", "TXN1015", "2026-01-12", "900.00"),   # Mismatch (-100)
        _create_sample_settle("SET15B", "TXN1015", "2026-01-13", "1000.00"),  # Duplicate entry
    ])

    reconciled_df, exceptions_df, summary, _ = reconcile_transactions(txns, settles)

    assert len(reconciled_df) == 2
    statuses = set(reconciled_df["reconciliation_status"])
    assert ReconciliationStatus.AMOUNT_MISMATCH.value in statuses
    assert ReconciliationStatus.DUPLICATE_SETTLEMENT.value in statuses
    assert summary["amount_mismatch_count"] == 1
    assert summary["duplicate_settlement_count"] == 1


# =====================================================================
# TC16: Exact Cutoff Date Handling
# =====================================================================
def test_tc16_exact_cutoff_date_handling():
    """TC16: Transaction on Jan 31 settled on Jan 31 matches; settled on Feb 1 is late."""
    txns = pd.DataFrame([
        _create_sample_txn("TXN_SAME_DAY", "2026-01-31", "1200.00"),
        _create_sample_txn("TXN_NEXT_DAY", "2026-01-31", "1800.00"),
    ])
    settles = pd.DataFrame([
        _create_sample_settle("SET_SAME", "TXN_SAME_DAY", "2026-01-31", "1200.00"),
        _create_sample_settle("SET_NEXT", "TXN_NEXT_DAY", "2026-02-01", "1800.00"),
    ])

    reconciled_df, exceptions_df, summary, _ = reconcile_transactions(txns, settles, cutoff_date="2026-01-31")

    same_day = reconciled_df[reconciled_df["transaction_id"] == "TXN_SAME_DAY"].iloc[0]
    next_day = reconciled_df[reconciled_df["transaction_id"] == "TXN_NEXT_DAY"].iloc[0]

    assert same_day["reconciliation_status"] == ReconciliationStatus.MATCHED.value
    assert next_day["reconciliation_status"] == ReconciliationStatus.LATE_SETTLEMENT.value
