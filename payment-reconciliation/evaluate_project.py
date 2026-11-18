"""Independent Evaluator Verification Script."""

import os
import pandas as pd
from decimal import Decimal
from reconciliation import reconcile_transactions

def evaluate():
    tx = pd.read_csv("data/transactions.csv")
    se = pd.read_csv("data/settlements.csv")

    print("==================================================")
    print("1. ACTUAL DATASET COUNTS")
    print("==================================================")
    print(f"Platform Transactions: {len(tx)} records (Requirement: 100-200) -> {'PASS' if 100 <= len(tx) <= 200 else 'FAIL'}")
    print(f"Bank Settlements:      {len(se)} records")

    r, e, s, rep = reconcile_transactions(tx, se, cutoff_date="2026-01-31")

    print("\n==================================================")
    print("2. STATUS DISTRIBUTION")
    print("==================================================")
    for status, count in r["reconciliation_status"].value_counts().items():
        print(f"  {status:<25}: {count:>4} records")

    print("\n==================================================")
    print("3. FOUR MANDATORY ANOMALY SCENARIOS")
    print("==================================================")
    
    # Scenario 1: Late Settlement
    late = r[r["reconciliation_status"] == "LATE_SETTLEMENT"]
    print(f"[SCENARIO 1] LATE_SETTLEMENT: {len(late)} detected -> {'PASS' if len(late) >= 1 else 'FAIL'}")
    for _, row in late.iterrows():
        print(f"  Txn: {row['transaction_id']}, TxnDate: {row['transaction_date']}, SettleDate: {row['settlement_date']}, Amount: {row['platform_amount']}, Days: {row['days_to_settle']}")

    # Scenario 2: Rounding Variance
    rnd = r[r["reconciliation_status"] == "ROUNDING_VARIANCE"]
    print(f"\n[SCENARIO 2] ROUNDING_VARIANCE: {len(rnd)} detected -> {'PASS' if len(rnd) >= 2 else 'FAIL'}")
    print(f"  Platform Aggregate: {s['rounding_platform_amount']}, Bank Aggregate: {s['rounding_bank_amount']}, Total Net Diff: {s['rounding_total_difference']}")
    for _, row in rnd.iterrows():
        print(f"  Txn: {row['transaction_id']}, Platform: {row['platform_amount']}, Bank: {row['bank_amount']}, Diff: {row['difference']}")

    # Scenario 3: Duplicate Settlement
    dup = r[r["reconciliation_status"] == "DUPLICATE_SETTLEMENT"]
    print(f"\n[SCENARIO 3] DUPLICATE_SETTLEMENT: {len(dup)} detected -> {'PASS' if len(dup) >= 1 else 'FAIL'}")
    for _, row in dup.iterrows():
        print(f"  Txn: {row['transaction_id']}, SettleID: {row['settlement_id']}, Amount: {row['bank_amount']}, Diff: {row['difference']}")

    # Scenario 4: Orphan Refund
    orph = r[r["reconciliation_status"] == "ORPHAN_REFUND"]
    print(f"\n[SCENARIO 4] ORPHAN_REFUND: {len(orph)} detected -> {'PASS' if len(orph) >= 1 else 'FAIL'}")
    for _, row in orph.iterrows():
        print(f"  Txn: {row['transaction_id']}, SettleID: {row['settlement_id']}, BankAmount: {row['bank_amount']}, SettleDate: {row['settlement_date']}")

    print("\n==================================================")
    print("4. ADDITIONAL GAP TYPES")
    print("==================================================")
    unsettled = r[r["reconciliation_status"] == "UNSETTLED"]
    print(f"UNSETTLED:            {len(unsettled)} detected, Amount: {s['unsettled_amount']}")
    mismatch = r[r["reconciliation_status"] == "AMOUNT_MISMATCH"]
    print(f"AMOUNT_MISMATCH:      {len(mismatch)} detected, Net Diff: {s['amount_mismatch_difference']}")
    unmatched = r[r["reconciliation_status"] == "UNMATCHED_BANK_ENTRY"]
    print(f"UNMATCHED_BANK_ENTRY: {len(unmatched)} detected, Bank Amount: {s['unmatched_bank_amount']}")

    print("\n==================================================")
    print("5. FINANCIAL CALCULATIONS & BRIDGE VERIFICATION")
    print("==================================================")
    print(f"Platform Gross Payments: {s['platform_total_payments']}")
    print(f"Platform Gross Refunds:  {s['platform_total_refunds']}")
    print(f"Platform Net Revenue:    {s['platform_net_amount']}")
    print(f"Bank Period Payments:    {s['bank_total_payments_period']}")
    print(f"Bank Period Refunds:     {s['bank_total_refunds_period']}")
    print(f"Bank Net Settled Cash:   {s['bank_net_amount_period']}")
    print(f"Net Reconciliation Gap:  {s['net_reconciliation_difference']}")
    print(f"Bridge Discrepancy:      {s['bridge_discrepancy']} -> {'PASS' if s['bridge_discrepancy'] == Decimal('0.00') else 'FAIL'}")

    print("\n==================================================")
    print("6. CSV EXPORTS VERIFICATION")
    print("==================================================")
    out_file = "outputs/reconciliation_report.csv"
    if os.path.exists(out_file):
        out_df = pd.read_csv(out_file)
        print(f"{out_file} exists with {len(out_df)} rows -> PASS")
    else:
        print(f"{out_file} MISSING -> FAIL")

if __name__ == "__main__":
    evaluate()
