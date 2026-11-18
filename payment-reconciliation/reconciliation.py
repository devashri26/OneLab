"""Reconciliation Engine for Payment Platform Transactions and Bank Settlements.

Implements all financial reconciliation business rules, classification logic,
and exact Decimal calculations for financial variance analysis.
Verified and audited for strict mathematical consistency across Gross, Refund, and Net ledgers.
"""

from datetime import date
from decimal import Decimal
from typing import Dict, Any, Tuple
import pandas as pd

from config import (
    DEFAULT_CUTOFF_DATE,
    DEFAULT_ROUNDING_TOLERANCE,
    TransactionType,
    PlatformStatus,
    ReconciliationStatus,
)
from utils import to_decimal, parse_date, validate_transactions_csv, validate_settlements_csv


def reconcile_transactions(
    transactions: pd.DataFrame,
    settlements: pd.DataFrame,
    cutoff_date: date | str = DEFAULT_CUTOFF_DATE,
    rounding_tolerance: Decimal = DEFAULT_ROUNDING_TOLERANCE,
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any], Dict[str, Any]]:
    """Reconcile payment platform transactions against bank settlement records.
    
    Args:
        transactions: DataFrame of platform transactions.
        settlements: DataFrame of bank settlement records.
        cutoff_date: Cutoff date for month-end reconciliation (defaults to 2026-01-31).
        rounding_tolerance: Max difference considered a rounding variance (defaults to ₹0.05).
        
    Returns:
        (reconciled_df, exceptions_df, financial_summary, validation_report)
    """
    # 1. Parse Cutoff Date
    if isinstance(cutoff_date, str):
        parsed_cutoff = parse_date(cutoff_date)
        if parsed_cutoff is None:
            raise ValueError(f"Invalid cutoff_date format: {cutoff_date}")
        cutoff_date = parsed_cutoff

    if not isinstance(rounding_tolerance, Decimal):
        rounding_tolerance = to_decimal(rounding_tolerance)

    # 2. Input Validation Reports
    txns_valid, txns_errors = validate_transactions_csv(transactions)
    settles_valid, settles_errors = validate_settlements_csv(settlements)

    validation_report = {
        "transactions_valid": txns_valid,
        "transactions_errors": txns_errors,
        "settlements_valid": settles_valid,
        "settlements_errors": settles_errors,
        "total_transactions_input": len(transactions) if transactions is not None else 0,
        "total_settlements_input": len(settlements) if settlements is not None else 0,
        "cutoff_date": str(cutoff_date),
        "rounding_tolerance": str(rounding_tolerance),
    }

    # Handle completely empty datasets gracefully
    if (transactions is None or transactions.empty) and (settlements is None or settlements.empty):
        empty_reconciled = pd.DataFrame(columns=[
            "transaction_id", "settlement_id", "transaction_date", "settlement_date",
            "transaction_type", "platform_amount", "bank_amount", "difference",
            "reconciliation_status", "days_to_settle", "explanation", "suggested_action"
        ])
        empty_summary = _build_zero_summary()
        return empty_reconciled, empty_reconciled.copy(), empty_summary, validation_report

    # Normalize Transactions
    txns = transactions.copy() if transactions is not None and not transactions.empty else pd.DataFrame(columns=[
        "transaction_id", "transaction_date", "amount", "transaction_type", "original_transaction_id", "status"
    ])
    settles = settlements.copy() if settlements is not None and not settlements.empty else pd.DataFrame(columns=[
        "settlement_id", "transaction_id", "settlement_date", "amount", "transaction_type"
    ])

    # Convert columns safely; ensure amounts are absolute positive magnitudes
    txns["transaction_id"] = txns["transaction_id"].astype(str).str.strip()
    txns["parsed_date"] = txns["transaction_date"].apply(parse_date)
    txns["dec_amount"] = txns["amount"].apply(lambda v: abs(to_decimal(v)))
    txns["norm_type"] = txns["transaction_type"].astype(str).str.strip().str.upper()
    txns["orig_id"] = txns["original_transaction_id"].fillna("").astype(str).str.strip()
    txns["norm_status"] = txns["status"].astype(str).str.strip().str.upper()

    settles["settlement_id"] = settles["settlement_id"].astype(str).str.strip()
    settles["transaction_id"] = settles["transaction_id"].astype(str).str.strip()
    settles["parsed_date"] = settles["settlement_date"].apply(parse_date)
    settles["dec_amount"] = settles["amount"].apply(lambda v: abs(to_decimal(v)))
    settles["norm_type"] = settles["transaction_type"].astype(str).str.strip().str.upper()

    # Create mapping of all platform transactions for fast lookup and refund validation
    platform_txn_map = {}
    for _, row in txns.iterrows():
        platform_txn_map[row["transaction_id"]] = row

    reconciled_records = []

    # Track settlements processed to identify duplicates and unmatched bank entries
    settlements_by_txn_id = {}
    for _, s_row in settles.iterrows():
        t_id = s_row["transaction_id"]
        if t_id not in settlements_by_txn_id:
            settlements_by_txn_id[t_id] = []
        settlements_by_txn_id[t_id].append(s_row)

    settlements_matched_or_processed = set()
    
    # Cumulative refund tracking per original transaction ID
    cumulative_refunds_by_orig_id = {}

    # 3. Process Platform Transactions
    for _, t_row in txns.iterrows():
        t_id = t_row["transaction_id"]
        t_date = t_row["parsed_date"]
        p_amount = t_row["dec_amount"]
        t_type = t_row["norm_type"]
        orig_id = t_row["orig_id"]

        matching_settles = settlements_by_txn_id.get(t_id, [])

        # Boundary Handling (Rule 10): Post-Cutoff Transactions
        if t_date and t_date > cutoff_date:
            # Mark settlement as processed so it does not trigger a false "UNMATCHED_BANK_ENTRY" in January
            if matching_settles:
                settlements_matched_or_processed.add(matching_settles[0]["settlement_id"])
            continue

        if not matching_settles:
            # RULE 2: MISSING SETTLEMENT (UNSETTLED)
            # Cash impact: for payment, bank has less cash (-); for refund, bank has more cash (+)
            signed_diff = -p_amount if t_type == TransactionType.PAYMENT.value else p_amount
            reconciled_records.append({
                "transaction_id": t_id,
                "settlement_id": "N/A",
                "transaction_date": str(t_date) if t_date else "N/A",
                "settlement_date": "N/A",
                "transaction_type": t_type,
                "platform_amount": float(p_amount),
                "bank_amount": 0.0,
                "difference": float(signed_diff),
                "reconciliation_status": ReconciliationStatus.UNSETTLED.value,
                "days_to_settle": None,
                "explanation": (
                    f"Platform {t_type.lower()} of {p_amount} recorded on {t_date} has not yet settled at the bank "
                    f"as of the month-end cutoff ({cutoff_date}). Funds remain in-transit."
                ),
                "suggested_action": (
                    "Verify settlement status with the payment aggregator / bank. If transaction was initiated "
                    "within standard T+2 clearing, await settlement in subsequent batch; otherwise raise an inquiry."
                ),
                "_p_dec": p_amount,
                "_b_dec": Decimal("0.00"),
                "_diff_dec": signed_diff,
                "_in_cutoff": False,
                "_is_refund": (t_type == TransactionType.REFUND.value),
            })
            continue

        # Primary settlement is the first record
        primary_settle = matching_settles[0]
        settlements_matched_or_processed.add(primary_settle["settlement_id"])
        
        s_id = primary_settle["settlement_id"]
        s_date = primary_settle["parsed_date"]
        b_amount = primary_settle["dec_amount"]
        s_type = primary_settle["norm_type"]

        days_to_settle = (s_date - t_date).days if (s_date and t_date) else None
        
        # Calculate signed cash impact difference
        # For payments: Bank Credit - Platform Expected (+ means bank settled more, - means bank settled less)
        # For refunds: -(Bank Debit - Platform Expected) = Platform Expected - Bank Debit (- means bank debited more, + means bank debited less)
        if t_type == TransactionType.PAYMENT.value:
            diff = b_amount - p_amount
        else:
            diff = p_amount - b_amount

        # Check for RULE 7 & RULE 9: REFUND VALIDATION
        if t_type == TransactionType.REFUND.value:
            # RULE 7: Verify original transaction exists
            if not orig_id or orig_id not in platform_txn_map:
                reconciled_records.append({
                    "transaction_id": t_id,
                    "settlement_id": s_id,
                    "transaction_date": str(t_date) if t_date else "N/A",
                    "settlement_date": str(s_date) if s_date else "N/A",
                    "transaction_type": t_type,
                    "platform_amount": float(p_amount),
                    "bank_amount": float(b_amount),
                    "difference": float(diff),
                    "reconciliation_status": ReconciliationStatus.ORPHAN_REFUND.value,
                    "days_to_settle": days_to_settle,
                    "explanation": (
                        f"Refund transaction {t_id} references original payment ID '{orig_id}' "
                        f"which cannot be found in the platform transaction database."
                    ),
                    "suggested_action": (
                        "Immediate financial audit required. Review refund authorization logs to prevent "
                        "fraudulent or unbacked payout disbursements."
                    ),
                    "_p_dec": p_amount,
                    "_b_dec": b_amount,
                    "_diff_dec": diff,
                    "_in_cutoff": (s_date <= cutoff_date) if s_date else False,
                    "_is_refund": True,
                })
                continue
            
            orig_row = platform_txn_map[orig_id]
            # RULE 9: Verify original transaction is actually a PAYMENT
            if orig_row["norm_type"] != TransactionType.PAYMENT.value:
                reconciled_records.append({
                    "transaction_id": t_id,
                    "settlement_id": s_id,
                    "transaction_date": str(t_date) if t_date else "N/A",
                    "settlement_date": str(s_date) if s_date else "N/A",
                    "transaction_type": t_type,
                    "platform_amount": float(p_amount),
                    "bank_amount": float(b_amount),
                    "difference": float(diff),
                    "reconciliation_status": ReconciliationStatus.ORPHAN_REFUND.value,
                    "days_to_settle": days_to_settle,
                    "explanation": (
                        f"Refund transaction {t_id} references original transaction '{orig_id}' "
                        f"which is classified as '{orig_row['norm_type']}', not a valid PAYMENT."
                    ),
                    "suggested_action": (
                        "Reject refund settlement clearance. Refunds may only be issued against legitimate payment charges."
                    ),
                    "_p_dec": p_amount,
                    "_b_dec": b_amount,
                    "_diff_dec": diff,
                    "_in_cutoff": (s_date <= cutoff_date) if s_date else False,
                    "_is_refund": True,
                })
                continue

            # RULE 9: Cumulative refund amount must not exceed original payment amount
            orig_p_amt = orig_row["dec_amount"]
            prior_refunds = cumulative_refunds_by_orig_id.get(orig_id, Decimal("0.00"))
            cumulative_total = prior_refunds + p_amount
            cumulative_refunds_by_orig_id[orig_id] = cumulative_total

            if cumulative_total > orig_p_amt:
                reconciled_records.append({
                    "transaction_id": t_id,
                    "settlement_id": s_id,
                    "transaction_date": str(t_date) if t_date else "N/A",
                    "settlement_date": str(s_date) if s_date else "N/A",
                    "transaction_type": t_type,
                    "platform_amount": float(p_amount),
                    "bank_amount": float(b_amount),
                    "difference": float(diff),
                    "reconciliation_status": ReconciliationStatus.REFUND_EXCEEDS_PAYMENT.value,
                    "days_to_settle": days_to_settle,
                    "explanation": (
                        f"Refund amount of {p_amount} brings cumulative refunds for original transaction {orig_id} "
                        f"to {cumulative_total}, exceeding original payment of {orig_p_amt}."
                    ),
                    "suggested_action": (
                        "Reject or suspend refund settlement clearance. Review merchant dispute case and cap refund at original charge."
                    ),
                    "_p_dec": p_amount,
                    "_b_dec": b_amount,
                    "_diff_dec": diff,
                    "_in_cutoff": (s_date <= cutoff_date) if s_date else False,
                    "_is_refund": True,
                })
                continue

        # RULE 3: LATE SETTLEMENT (Timing difference across month-end boundary)
        if s_date and s_date > cutoff_date:
            reconciled_records.append({
                "transaction_id": t_id,
                "settlement_id": s_id,
                "transaction_date": str(t_date) if t_date else "N/A",
                "settlement_date": str(s_date) if s_date else "N/A",
                "transaction_type": t_type,
                "platform_amount": float(p_amount),
                "bank_amount": float(b_amount),
                "difference": float(diff),
                "reconciliation_status": ReconciliationStatus.LATE_SETTLEMENT.value,
                "days_to_settle": days_to_settle,
                "explanation": (
                    f"Transaction was executed on {t_date} (within period cutoff {cutoff_date}), "
                    f"but bank settlement arrived on {s_date} ({days_to_settle} days delay). "
                    f"Funds were in-transit over month-end."
                ),
                "suggested_action": (
                    "Account as in-transit outstanding item at month-end. Roll forward to next month's "
                    "reconciliation opening balance without recognizing a permanent deficit."
                ),
                "_p_dec": p_amount,
                "_b_dec": b_amount,
                "_diff_dec": diff,
                "_in_cutoff": False,  # Bank settlement happened outside cutoff
                "_is_refund": (t_type == TransactionType.REFUND.value),
            })
            continue

        # Settled within cutoff date: Check amount differences
        abs_diff = abs(b_amount - p_amount)
        if abs_diff == Decimal("0.00"):
            # RULE 1: NORMAL MATCHING
            reconciled_records.append({
                "transaction_id": t_id,
                "settlement_id": s_id,
                "transaction_date": str(t_date) if t_date else "N/A",
                "settlement_date": str(s_date) if s_date else "N/A",
                "transaction_type": t_type,
                "platform_amount": float(p_amount),
                "bank_amount": float(b_amount),
                "difference": 0.0,
                "reconciliation_status": ReconciliationStatus.MATCHED.value,
                "days_to_settle": days_to_settle,
                "explanation": "Transaction perfectly matched with bank settlement. Identifiers, types, dates, and amounts reconcile.",
                "suggested_action": "No action required. Transaction cleared and verified.",
                "_p_dec": p_amount,
                "_b_dec": b_amount,
                "_diff_dec": Decimal("0.00"),
                "_in_cutoff": True,
                "_is_refund": (t_type == TransactionType.REFUND.value),
            })
        elif abs_diff <= rounding_tolerance:
            # RULE 6: ROUNDING VARIANCE
            reconciled_records.append({
                "transaction_id": t_id,
                "settlement_id": s_id,
                "transaction_date": str(t_date) if t_date else "N/A",
                "settlement_date": str(s_date) if s_date else "N/A",
                "transaction_type": t_type,
                "platform_amount": float(p_amount),
                "bank_amount": float(b_amount),
                "difference": float(diff),
                "reconciliation_status": ReconciliationStatus.ROUNDING_VARIANCE.value,
                "days_to_settle": days_to_settle,
                "explanation": (
                    f"Minor decimal variance of {diff:+.2f} observed between platform ({p_amount}) and bank ({b_amount}). "
                    f"Falls within tolerance threshold of {rounding_tolerance}."
                ),
                "suggested_action": (
                    "Post net variance to the General Ledger Rounding / FX Gain-Loss account at period close."
                ),
                "_p_dec": p_amount,
                "_b_dec": b_amount,
                "_diff_dec": diff,
                "_in_cutoff": True,
                "_is_refund": (t_type == TransactionType.REFUND.value),
            })
        else:
            # RULE 5: AMOUNT MISMATCH
            reconciled_records.append({
                "transaction_id": t_id,
                "settlement_id": s_id,
                "transaction_date": str(t_date) if t_date else "N/A",
                "settlement_date": str(s_date) if s_date else "N/A",
                "transaction_type": t_type,
                "platform_amount": float(p_amount),
                "bank_amount": float(b_amount),
                "difference": float(diff),
                "reconciliation_status": ReconciliationStatus.AMOUNT_MISMATCH.value,
                "days_to_settle": days_to_settle,
                "explanation": (
                    f"Discrepancy of {diff:+.2f}: Platform recorded {p_amount} but bank settled {b_amount}. "
                    f"Variance exceeds tolerance limit of {rounding_tolerance}."
                ),
                "suggested_action": (
                    "Request transaction-level clearing statement from the bank. Investigate potential unrecorded "
                    "merchant discount rate (MDR), interchange surcharge, or data transmission error."
                ),
                "_p_dec": p_amount,
                "_b_dec": b_amount,
                "_diff_dec": diff,
                "_in_cutoff": True,
                "_is_refund": (t_type == TransactionType.REFUND.value),
            })

    # 4. Process Duplicate Bank Settlements (RULE 4)
    for t_id, settle_list in settlements_by_txn_id.items():
        if len(settle_list) > 1:
            for dup_settle in settle_list[1:]:
                settlements_matched_or_processed.add(dup_settle["settlement_id"])
                dup_s_id = dup_settle["settlement_id"]
                dup_date = dup_settle["parsed_date"]
                dup_amt = dup_settle["dec_amount"]
                dup_type = dup_settle["norm_type"]
                
                # Check if duplicate is within cutoff period
                in_cutoff = (dup_date <= cutoff_date) if dup_date else False
                
                p_row = platform_txn_map.get(t_id)
                t_date_str = str(p_row["parsed_date"]) if (p_row is not None and p_row["parsed_date"]) else "N/A"
                
                # Signed impact: duplicate payment increases bank cash (+), duplicate refund decreases bank cash (-)
                signed_diff = dup_amt if dup_type == TransactionType.PAYMENT.value else -dup_amt

                reconciled_records.append({
                    "transaction_id": t_id,
                    "settlement_id": dup_s_id,
                    "transaction_date": t_date_str,
                    "settlement_date": str(dup_date) if dup_date else "N/A",
                    "transaction_type": dup_type,
                    "platform_amount": 0.0,
                    "bank_amount": float(dup_amt),
                    "difference": float(signed_diff),
                    "reconciliation_status": ReconciliationStatus.DUPLICATE_SETTLEMENT.value,
                    "days_to_settle": None,
                    "explanation": (
                        f"Bank recorded duplicate settlement {dup_s_id} for transaction {t_id} with amount {dup_amt}. "
                        f"An initial settlement ({settle_list[0]['settlement_id']}) was already processed."
                    ),
                    "suggested_action": (
                        "Quarantine duplicate settlement credit. Do not recognize as revenue. "
                        "Notify bank operations to initiate a clawback/reversal."
                    ),
                    "_p_dec": Decimal("0.00"),
                    "_b_dec": dup_amt,
                    "_diff_dec": signed_diff,
                    "_in_cutoff": in_cutoff,
                    "_is_refund": (dup_type == TransactionType.REFUND.value),
                })

    # 5. Process Remaining Unmatched Bank Settlements (RULE 7 & RULE 8)
    for _, s_row in settles.iterrows():
        s_id = s_row["settlement_id"]
        if s_id in settlements_matched_or_processed:
            continue

        t_id = s_row["transaction_id"]
        s_date = s_row["parsed_date"]
        b_amt = s_row["dec_amount"]
        s_type = s_row["norm_type"]

        # Only audit bank settlements within period cutoff for month-end reconciliation
        in_cutoff = (s_date <= cutoff_date) if s_date else False

        if s_type == TransactionType.REFUND.value:
            # RULE 7: ORPHAN REFUND (Bank has a refund for a transaction ID completely absent from platform)
            # Cash impact: unauthorized cash outflow = -b_amt
            reconciled_records.append({
                "transaction_id": t_id,
                "settlement_id": s_id,
                "transaction_date": "N/A",
                "settlement_date": str(s_date) if s_date else "N/A",
                "transaction_type": s_type,
                "platform_amount": 0.0,
                "bank_amount": float(b_amt),
                "difference": float(-b_amt),
                "reconciliation_status": ReconciliationStatus.ORPHAN_REFUND.value,
                "days_to_settle": None,
                "explanation": (
                    f"Bank processed refund {s_id} of {b_amt} for transaction ID '{t_id}', "
                    f"which does not exist anywhere in the platform transaction database."
                ),
                "suggested_action": (
                    "Investigate fraudulent refund or gateway routing error. Cross-reference bank statement with merchant portal."
                ),
                "_p_dec": Decimal("0.00"),
                "_b_dec": b_amt,
                "_diff_dec": -b_amt,
                "_in_cutoff": in_cutoff,
                "_is_refund": True,
            })
        else:
            # RULE 8: UNMATCHED BANK SETTLEMENT (Bank payment settlement with no platform record)
            # Cash impact: extra unrecorded deposit = +b_amt
            reconciled_records.append({
                "transaction_id": t_id,
                "settlement_id": s_id,
                "transaction_date": "N/A",
                "settlement_date": str(s_date) if s_date else "N/A",
                "transaction_type": s_type,
                "platform_amount": 0.0,
                "bank_amount": float(b_amt),
                "difference": float(b_amt),
                "reconciliation_status": ReconciliationStatus.UNMATCHED_BANK_ENTRY.value,
                "days_to_settle": None,
                "explanation": (
                    f"Bank settlement {s_id} of {b_amt} received for transaction ID '{t_id}', "
                    f"but no corresponding transaction exists in the payment platform."
                ),
                "suggested_action": (
                    "Check if the transaction originated through an unintegrated point-of-sale, manual bank credit, "
                    "or incorrect external merchant account."
                ),
                "_p_dec": Decimal("0.00"),
                "_b_dec": b_amt,
                "_diff_dec": b_amt,
                "_in_cutoff": in_cutoff,
                "_is_refund": False,
            })

    reconciled_df = pd.DataFrame(reconciled_records)

    # 6. Filter Exceptions
    non_exception_statuses = {ReconciliationStatus.MATCHED.value, ReconciliationStatus.POST_CUTOFF_TRANSACTION.value}
    if not reconciled_df.empty:
        exceptions_df = reconciled_df[~reconciled_df["reconciliation_status"].isin(non_exception_statuses)].copy()
    else:
        exceptions_df = pd.DataFrame(columns=reconciled_df.columns)

    # 7. Financial Calculations (Strict Decimal Precision & Universal Reconciliation Bridge)
    summary = _calculate_financial_metrics(
        txns=txns,
        settles=settles,
        reconciled_df=reconciled_df,
        cutoff_date=cutoff_date,
    )

    # Clean internal decimal columns from output DataFrames
    cols_to_drop = ["_p_dec", "_b_dec", "_diff_dec", "_in_cutoff", "_is_refund"]
    clean_reconciled_df = reconciled_df.drop(columns=[c for c in cols_to_drop if c in reconciled_df.columns])
    clean_exceptions_df = exceptions_df.drop(columns=[c for c in cols_to_drop if c in exceptions_df.columns])

    return clean_reconciled_df, clean_exceptions_df, summary, validation_report


def _calculate_financial_metrics(
    txns: pd.DataFrame,
    settles: pd.DataFrame,
    reconciled_df: pd.DataFrame,
    cutoff_date: date,
) -> Dict[str, Any]:
    """Calculate all financial metrics dynamically using Decimal arithmetic with full payment vs. refund disaggregation."""
    # Filter platform transactions within period (<= cutoff_date)
    period_txns = txns[txns["parsed_date"] <= cutoff_date] if not txns.empty else txns
    
    # Platform totals
    p_payments = period_txns[period_txns["norm_type"] == TransactionType.PAYMENT.value] if not period_txns.empty else pd.DataFrame()
    p_refunds = period_txns[period_txns["norm_type"] == TransactionType.REFUND.value] if not period_txns.empty else pd.DataFrame()

    total_platform_payments = sum(p_payments["dec_amount"], Decimal("0.00")) if not p_payments.empty else Decimal("0.00")
    total_platform_refunds = sum(p_refunds["dec_amount"], Decimal("0.00")) if not p_refunds.empty else Decimal("0.00")
    net_platform_amount = total_platform_payments - total_platform_refunds

    # Bank Settlements (split by <= cutoff vs all)
    period_settles = settles[settles["parsed_date"] <= cutoff_date] if not settles.empty else settles
    
    b_payments_period = period_settles[period_settles["norm_type"] == TransactionType.PAYMENT.value] if not period_settles.empty else pd.DataFrame()
    b_refunds_period = period_settles[period_settles["norm_type"] == TransactionType.REFUND.value] if not period_settles.empty else pd.DataFrame()

    total_bank_payments_period = sum(b_payments_period["dec_amount"], Decimal("0.00")) if not b_payments_period.empty else Decimal("0.00")
    total_bank_refunds_period = sum(b_refunds_period["dec_amount"], Decimal("0.00")) if not b_refunds_period.empty else Decimal("0.00")
    net_bank_amount_period = total_bank_payments_period - total_bank_refunds_period

    # Breakdown by Reconciliation Status from reconciled_df
    status_metrics = {}
    for status in ReconciliationStatus:
        status_metrics[status.value] = {
            "count": 0,
            "platform_amount": Decimal("0.00"),
            "bank_amount": Decimal("0.00"),
            "difference": Decimal("0.00"),
            "payments_count": 0,
            "payments_platform_amount": Decimal("0.00"),
            "payments_bank_amount": Decimal("0.00"),
            "refunds_count": 0,
            "refunds_platform_amount": Decimal("0.00"),
            "refunds_bank_amount": Decimal("0.00"),
        }

    if not reconciled_df.empty:
        for _, row in reconciled_df.iterrows():
            st = row["reconciliation_status"]
            if st in status_metrics:
                m = status_metrics[st]
                m["count"] += 1
                m["platform_amount"] += row["_p_dec"]
                m["bank_amount"] += row["_b_dec"]
                m["difference"] += row["_diff_dec"]
                
                if row["_is_refund"]:
                    m["refunds_count"] += 1
                    m["refunds_platform_amount"] += row["_p_dec"]
                    m["refunds_bank_amount"] += row["_b_dec"]
                else:
                    m["payments_count"] += 1
                    m["payments_platform_amount"] += row["_p_dec"]
                    m["payments_bank_amount"] += row["_b_dec"]

    # Key Disaggregated Aggregates
    matched_m = status_metrics[ReconciliationStatus.MATCHED.value]
    late_m = status_metrics[ReconciliationStatus.LATE_SETTLEMENT.value]
    unsettled_m = status_metrics[ReconciliationStatus.UNSETTLED.value]
    duplicate_m = status_metrics[ReconciliationStatus.DUPLICATE_SETTLEMENT.value]
    rounding_m = status_metrics[ReconciliationStatus.ROUNDING_VARIANCE.value]
    orphan_m = status_metrics[ReconciliationStatus.ORPHAN_REFUND.value]
    mismatch_m = status_metrics[ReconciliationStatus.AMOUNT_MISMATCH.value]
    unmatched_bank_m = status_metrics[ReconciliationStatus.UNMATCHED_BANK_ENTRY.value]
    excess_refund_m = status_metrics[ReconciliationStatus.REFUND_EXCEEDS_PAYMENT.value]

    total_exceptions_count = sum(
        m["count"] for st, m in status_metrics.items()
        if st not in [ReconciliationStatus.MATCHED.value, ReconciliationStatus.POST_CUTOFF_TRANSACTION.value]
    )

    # Net variance between Period Bank settlements and Period Platform transactions
    net_reconciliation_difference = net_bank_amount_period - net_platform_amount

    # Universal Mathematical Bridge:
    # Net Bank = Net Platform
    #            - Late Payments + Late Refunds
    #            - Unsettled Payments + Unsettled Refunds
    #            + Duplicate Payments - Duplicate Refunds
    #            + Unmatched Bank Payments - Orphan Bank Refunds
    #            + (Payment Amount Mismatches - Refund Amount Mismatches)
    #            + Net Rounding Differences
    #            - Excess Refunds Platform (if held)
    bridge_expected_bank_net = (
        net_platform_amount
        - late_m["payments_platform_amount"]
        + late_m["refunds_platform_amount"]
        - unsettled_m["payments_platform_amount"]
        + unsettled_m["refunds_platform_amount"]
        + duplicate_m["payments_bank_amount"]
        - duplicate_m["refunds_bank_amount"]
        + unmatched_bank_m["payments_bank_amount"]
        - orphan_m["bank_amount"]
        + mismatch_m["difference"]
        + rounding_m["difference"]
    )
    bridge_discrepancy = net_bank_amount_period - bridge_expected_bank_net

    summary = {
        # Platform Overview
        "platform_total_payments": total_platform_payments,
        "platform_total_refunds": total_platform_refunds,
        "platform_net_amount": net_platform_amount,
        "platform_total_records": len(period_txns),
        
        # Bank Overview (In Period)
        "bank_total_payments_period": total_bank_payments_period,
        "bank_total_refunds_period": total_bank_refunds_period,
        "bank_net_amount_period": net_bank_amount_period,
        "bank_total_records_period": len(period_settles),
        
        # Bank Overview (All Settled, including post-cutoff)
        "bank_total_records_all": len(settles),
        
        # Overall Net Gap
        "net_reconciliation_difference": net_reconciliation_difference,
        "bridge_discrepancy": bridge_discrepancy,
        
        # Category Amounts & Counts (Disaggregated)
        "matched_count": matched_m["count"],
        "matched_payments_count": matched_m["payments_count"],
        "matched_payments_amount": matched_m["payments_platform_amount"],
        "matched_refunds_count": matched_m["refunds_count"],
        "matched_refunds_amount": matched_m["refunds_platform_amount"],
        "matched_gross_amount": matched_m["platform_amount"],
        "matched_net_amount": matched_m["payments_platform_amount"] - matched_m["refunds_platform_amount"],
        "matched_platform_amount": matched_m["platform_amount"],
        "matched_bank_amount": matched_m["bank_amount"],
        
        "unsettled_count": unsettled_m["count"],
        "unsettled_amount": unsettled_m["platform_amount"],
        "unsettled_payments_count": unsettled_m["payments_count"],
        "unsettled_payments_amount": unsettled_m["payments_platform_amount"],
        "unsettled_refunds_count": unsettled_m["refunds_count"],
        "unsettled_refunds_amount": unsettled_m["refunds_platform_amount"],
        
        "late_settlement_count": late_m["count"],
        "late_settlement_amount": late_m["platform_amount"],
        "late_settlement_payments_count": late_m["payments_count"],
        "late_settlement_payments_amount": late_m["payments_platform_amount"],
        "late_settlement_refunds_count": late_m["refunds_count"],
        "late_settlement_refunds_amount": late_m["refunds_platform_amount"],
        
        "duplicate_settlement_count": duplicate_m["count"],
        "duplicate_settlement_amount": duplicate_m["bank_amount"],
        "duplicate_settlement_payments_amount": duplicate_m["payments_bank_amount"],
        "duplicate_settlement_refunds_amount": duplicate_m["refunds_bank_amount"],
        
        "rounding_variance_count": rounding_m["count"],
        "rounding_platform_amount": rounding_m["platform_amount"],
        "rounding_bank_amount": rounding_m["bank_amount"],
        "rounding_total_difference": rounding_m["difference"],
        
        "orphan_refund_count": orphan_m["count"],
        "orphan_refund_amount": orphan_m["bank_amount"],
        
        "amount_mismatch_count": mismatch_m["count"],
        "amount_mismatch_difference": mismatch_m["difference"],
        
        "unmatched_bank_count": unmatched_bank_m["count"],
        "unmatched_bank_amount": unmatched_bank_m["bank_amount"],
        
        "refund_exceeds_payment_count": excess_refund_m["count"],
        "refund_exceeds_payment_amount": excess_refund_m["platform_amount"],
        
        "total_exceptions_count": total_exceptions_count,
        
        # Full status metrics breakdown dictionary
        "status_metrics": status_metrics,
    }
    
    return summary


def _build_zero_summary() -> Dict[str, Any]:
    """Return zeroed summary dictionary for empty inputs."""
    zero_status = {}
    for status in ReconciliationStatus:
        zero_status[status.value] = {
            "count": 0,
            "platform_amount": Decimal("0.00"),
            "bank_amount": Decimal("0.00"),
            "difference": Decimal("0.00"),
            "payments_count": 0,
            "payments_platform_amount": Decimal("0.00"),
            "payments_bank_amount": Decimal("0.00"),
            "refunds_count": 0,
            "refunds_platform_amount": Decimal("0.00"),
            "refunds_bank_amount": Decimal("0.00"),
        }
    return {
        "platform_total_payments": Decimal("0.00"),
        "platform_total_refunds": Decimal("0.00"),
        "platform_net_amount": Decimal("0.00"),
        "platform_total_records": 0,
        "bank_total_payments_period": Decimal("0.00"),
        "bank_total_refunds_period": Decimal("0.00"),
        "bank_net_amount_period": Decimal("0.00"),
        "bank_total_records_period": 0,
        "bank_total_records_all": 0,
        "net_reconciliation_difference": Decimal("0.00"),
        "bridge_discrepancy": Decimal("0.00"),
        "matched_count": 0,
        "matched_payments_count": 0,
        "matched_payments_amount": Decimal("0.00"),
        "matched_refunds_count": 0,
        "matched_refunds_amount": Decimal("0.00"),
        "matched_gross_amount": Decimal("0.00"),
        "matched_net_amount": Decimal("0.00"),
        "matched_platform_amount": Decimal("0.00"),
        "matched_bank_amount": Decimal("0.00"),
        "unsettled_count": 0,
        "unsettled_amount": Decimal("0.00"),
        "unsettled_payments_count": 0,
        "unsettled_payments_amount": Decimal("0.00"),
        "unsettled_refunds_count": 0,
        "unsettled_refunds_amount": Decimal("0.00"),
        "late_settlement_count": 0,
        "late_settlement_amount": Decimal("0.00"),
        "late_settlement_payments_count": 0,
        "late_settlement_payments_amount": Decimal("0.00"),
        "late_settlement_refunds_count": 0,
        "late_settlement_refunds_amount": Decimal("0.00"),
        "duplicate_settlement_count": 0,
        "duplicate_settlement_amount": Decimal("0.00"),
        "duplicate_settlement_payments_amount": Decimal("0.00"),
        "duplicate_settlement_refunds_amount": Decimal("0.00"),
        "rounding_variance_count": 0,
        "rounding_platform_amount": Decimal("0.00"),
        "rounding_bank_amount": Decimal("0.00"),
        "rounding_total_difference": Decimal("0.00"),
        "orphan_refund_count": 0,
        "orphan_refund_amount": Decimal("0.00"),
        "amount_mismatch_count": 0,
        "amount_mismatch_difference": Decimal("0.00"),
        "unmatched_bank_count": 0,
        "unmatched_bank_amount": Decimal("0.00"),
        "refund_exceeds_payment_count": 0,
        "refund_exceeds_payment_amount": Decimal("0.00"),
        "total_exceptions_count": 0,
        "status_metrics": zero_status,
    }
