"""Synthetic Data Generator for Payment Transactions and Bank Settlements.

Generates realistic payment platform transactions and corresponding bank settlements,
incorporating normal matched flows, 1-2 day settlement delays, valid refunds, and
specifically isolated planted anomalies.
"""

import os
from datetime import date, timedelta
from decimal import Decimal
import random
import pandas as pd

from config import TransactionType, PlatformStatus


def generate_synthetic_datasets(seed: int = 42, total_txns: int = 160) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Generate realistic platform transactions and bank settlements with planted anomalies.
    
    Args:
        seed: Random seed for exact determinism and reproducibility.
        total_txns: Target number of transactions (minimum 100-200).
        
    Returns:
        (transactions_df, settlements_df, planted_manifest)
    """
    random.seed(seed)
    
    transactions = []
    settlements = []
    
    # Tracking planted anomalies
    manifest = {
        "normal_matched_payments": 0,
        "valid_refunds": 0,
        "late_settlements": [],
        "rounding_variances": [],
        "duplicate_settlements": [],
        "orphan_refunds": [],
        "unsettled_transactions": [],
        "amount_mismatches": [],
        "unmatched_bank_entries": [],
    }

    start_date = date(2026, 1, 1)
    cutoff_date = date(2026, 1, 31)
    
    txn_counter = 1000
    settle_counter = 5000

    # 1. Base normal payments (around 120 payments)
    normal_payments = []
    for _ in range(115):
        txn_counter += 1
        txn_id = f"TXN{txn_counter}"
        
        # Transaction dates distributed from Jan 1 to Jan 28
        day_offset = random.randint(0, 27)
        txn_date = start_date + timedelta(days=day_offset)
        
        # Realistic amounts between ₹150.00 and ₹25,000.00
        amount = Decimal(str(random.randint(150, 25000))) + Decimal(str(random.choice([0, 25, 50, 75, 99]))) / Decimal("100")
        
        transactions.append({
            "transaction_id": txn_id,
            "transaction_date": txn_date.strftime("%Y-%m-%d"),
            "amount": f"{amount:.2f}",
            "transaction_type": TransactionType.PAYMENT.value,
            "original_transaction_id": "",
            "status": PlatformStatus.SUCCESS.value,
        })
        
        # Settle after 1-2 days
        settle_delay = random.choice([1, 2])
        settle_date = txn_date + timedelta(days=settle_delay)
        
        settle_counter += 1
        settlements.append({
            "settlement_id": f"SET{settle_counter}",
            "transaction_id": txn_id,
            "settlement_date": settle_date.strftime("%Y-%m-%d"),
            "amount": f"{amount:.2f}",
            "transaction_type": TransactionType.PAYMENT.value,
        })
        
        normal_payments.append((txn_id, txn_date, amount))
        manifest["normal_matched_payments"] += 1

    # 2. Valid Refunds (6 refunds referencing earlier successful payments)
    for i in range(6):
        target_payment = normal_payments[i * 10]
        orig_id, orig_date, orig_amount = target_payment
        
        txn_counter += 1
        refund_txn_id = f"TXN{txn_counter}"
        
        # Refund date is 2-5 days after original payment
        refund_date = orig_date + timedelta(days=random.randint(2, 4))
        # Full or partial refund
        refund_amount = orig_amount if i % 2 == 0 else (orig_amount * Decimal("0.50")).quantize(Decimal("0.01"))
        
        transactions.append({
            "transaction_id": refund_txn_id,
            "transaction_date": refund_date.strftime("%Y-%m-%d"),
            "amount": f"{refund_amount:.2f}",
            "transaction_type": TransactionType.REFUND.value,
            "original_transaction_id": orig_id,
            "status": PlatformStatus.REFUNDED.value,
        })
        
        settle_counter += 1
        refund_settle_date = refund_date + timedelta(days=1)
        settlements.append({
            "settlement_id": f"SET{settle_counter}",
            "transaction_id": refund_txn_id,
            "settlement_date": refund_settle_date.strftime("%Y-%m-%d"),
            "amount": f"{refund_amount:.2f}",
            "transaction_type": TransactionType.REFUND.value,
        })
        manifest["valid_refunds"] += 1

    # 3. SCENARIO 1: LATE SETTLEMENT (Mandatory Anomaly 1)
    # A transaction on 31 January 2026. Corresponding bank settlement arrives on 1 February 2026.
    # We plant 2 distinct late settlement transactions on 2026-01-31.
    for i in range(2):
        txn_counter += 1
        late_id = f"TXN{txn_counter}"
        late_amount = Decimal("4850.00") if i == 0 else Decimal("12400.50")
        txn_date = date(2026, 1, 31)
        settle_date = date(2026, 2, 1)  # February 1st
        
        transactions.append({
            "transaction_id": late_id,
            "transaction_date": txn_date.strftime("%Y-%m-%d"),
            "amount": f"{late_amount:.2f}",
            "transaction_type": TransactionType.PAYMENT.value,
            "original_transaction_id": "",
            "status": PlatformStatus.SUCCESS.value,
        })
        
        settle_counter += 1
        settlements.append({
            "settlement_id": f"SET{settle_counter}",
            "transaction_id": late_id,
            "settlement_date": settle_date.strftime("%Y-%m-%d"),
            "amount": f"{late_amount:.2f}",
            "transaction_type": TransactionType.PAYMENT.value,
        })
        manifest["late_settlements"].append({
            "transaction_id": late_id,
            "transaction_date": str(txn_date),
            "settlement_date": str(settle_date),
            "amount": str(late_amount),
        })

    # 4. SCENARIO 2: AGGREGATE ROUNDING DIFFERENCE (Mandatory Anomaly 2)
    # Multiple transactions with small decimal differences (<= 0.05), measurable when aggregated.
    rounding_diffs = [Decimal("0.02"), Decimal("-0.01"), Decimal("0.03"), Decimal("-0.02"), Decimal("0.02")]
    for idx, diff in enumerate(rounding_diffs):
        txn_counter += 1
        rnd_id = f"TXN{txn_counter}"
        platform_amt = Decimal("3200.40") + Decimal(idx * 500)
        bank_amt = platform_amt + diff
        
        txn_date = date(2026, 1, 15 + idx)
        settle_date = txn_date + timedelta(days=1)
        
        transactions.append({
            "transaction_id": rnd_id,
            "transaction_date": txn_date.strftime("%Y-%m-%d"),
            "amount": f"{platform_amt:.2f}",
            "transaction_type": TransactionType.PAYMENT.value,
            "original_transaction_id": "",
            "status": PlatformStatus.SUCCESS.value,
        })
        
        settle_counter += 1
        settlements.append({
            "settlement_id": f"SET{settle_counter}",
            "transaction_id": rnd_id,
            "settlement_date": settle_date.strftime("%Y-%m-%d"),
            "amount": f"{bank_amt:.2f}",
            "transaction_type": TransactionType.PAYMENT.value,
        })
        manifest["rounding_variances"].append({
            "transaction_id": rnd_id,
            "platform_amount": str(platform_amt),
            "bank_amount": str(bank_amt),
            "difference": str(diff),
        })

    # 5. SCENARIO 3: DUPLICATE BANK ENTRY (Mandatory Anomaly 3)
    # Legitimate platform transaction with matching settlement + an additional duplicate bank settlement.
    txn_counter += 1
    dup_txn_id = f"TXN{txn_counter}"
    dup_amount = Decimal("9500.00")
    txn_date = date(2026, 1, 18)
    settle_date = date(2026, 1, 19)
    
    transactions.append({
        "transaction_id": dup_txn_id,
        "transaction_date": txn_date.strftime("%Y-%m-%d"),
        "amount": f"{dup_amount:.2f}",
        "transaction_type": TransactionType.PAYMENT.value,
        "original_transaction_id": "",
        "status": PlatformStatus.SUCCESS.value,
    })
    
    # Original legitimate bank settlement
    settle_counter += 1
    first_settle_id = f"SET{settle_counter}"
    settlements.append({
        "settlement_id": first_settle_id,
        "transaction_id": dup_txn_id,
        "settlement_date": settle_date.strftime("%Y-%m-%d"),
        "amount": f"{dup_amount:.2f}",
        "transaction_type": TransactionType.PAYMENT.value,
    })
    
    # Duplicate bank settlement record
    settle_counter += 1
    second_settle_id = f"SET{settle_counter}"
    settlements.append({
        "settlement_id": second_settle_id,
        "transaction_id": dup_txn_id,
        "settlement_date": (settle_date + timedelta(days=1)).strftime("%Y-%m-%d"),
        "amount": f"{dup_amount:.2f}",
        "transaction_type": TransactionType.PAYMENT.value,
    })
    manifest["duplicate_settlements"].append({
        "transaction_id": dup_txn_id,
        "original_settlement_id": first_settle_id,
        "duplicate_settlement_id": second_settle_id,
        "amount": str(dup_amount),
    })

    # 6. SCENARIO 4: ORPHAN REFUND (Mandatory Anomaly 4)
    # A refund record in bank settlements referencing a non-existent platform transaction.
    orphan_ref_id = "TXN_NONEXISTENT_9999"
    orphan_amount = Decimal("2400.00")
    settle_counter += 1
    settlements.append({
        "settlement_id": f"SET{settle_counter}",
        "transaction_id": orphan_ref_id,
        "settlement_date": "2026-01-22",
        "amount": f"{orphan_amount:.2f}",
        "transaction_type": TransactionType.REFUND.value,
    })
    manifest["orphan_refunds"].append({
        "settlement_id": f"SET{settle_counter}",
        "transaction_id": orphan_ref_id,
        "amount": str(orphan_amount),
        "settlement_date": "2026-01-22",
    })

    # 7. Unsettled Platform Transactions (Recorded <= cutoff, but no bank settlement at all)
    for i in range(4):
        txn_counter += 1
        unsettled_id = f"TXN{txn_counter}"
        unsettled_amt = Decimal("1800.00") + Decimal(i * 350)
        unsettled_date = date(2026, 1, 30) if i < 2 else date(2026, 1, 31)
        
        transactions.append({
            "transaction_id": unsettled_id,
            "transaction_date": unsettled_date.strftime("%Y-%m-%d"),
            "amount": f"{unsettled_amt:.2f}",
            "transaction_type": TransactionType.PAYMENT.value,
            "original_transaction_id": "",
            "status": PlatformStatus.SUCCESS.value,
        })
        manifest["unsettled_transactions"].append({
            "transaction_id": unsettled_id,
            "date": str(unsettled_date),
            "amount": str(unsettled_amt),
        })

    # 8. Amount Mismatch (Exists in both datasets, but difference > tolerance, e.g. bank fee deduction or error)
    for i in range(2):
        txn_counter += 1
        mismatch_id = f"TXN{txn_counter}"
        platform_amt = Decimal("7500.00") if i == 0 else Decimal("15000.00")
        # Bank settled ₹50 less or ₹120 more
        bank_amt = platform_amt - Decimal("50.00") if i == 0 else platform_amt + Decimal("120.00")
        txn_date = date(2026, 1, 12 + i * 5)
        settle_date = txn_date + timedelta(days=1)
        
        transactions.append({
            "transaction_id": mismatch_id,
            "transaction_date": txn_date.strftime("%Y-%m-%d"),
            "amount": f"{platform_amt:.2f}",
            "transaction_type": TransactionType.PAYMENT.value,
            "original_transaction_id": "",
            "status": PlatformStatus.SUCCESS.value,
        })
        
        settle_counter += 1
        settlements.append({
            "settlement_id": f"SET{settle_counter}",
            "transaction_id": mismatch_id,
            "settlement_date": settle_date.strftime("%Y-%m-%d"),
            "amount": f"{bank_amt:.2f}",
            "transaction_type": TransactionType.PAYMENT.value,
        })
        manifest["amount_mismatches"].append({
            "transaction_id": mismatch_id,
            "platform_amount": str(platform_amt),
            "bank_amount": str(bank_amt),
            "difference": str(bank_amt - platform_amt),
        })

    # 9. Unmatched Bank Settlement (Payment settled in bank with unknown transaction_id)
    settle_counter += 1
    unknown_bank_id = f"SET{settle_counter}"
    unmatched_amt = Decimal("6200.00")
    settlements.append({
        "settlement_id": unknown_bank_id,
        "transaction_id": "TXN_UNKNOWN_EXTERNAL_8888",
        "settlement_date": "2026-01-20",
        "amount": f"{unmatched_amt:.2f}",
        "transaction_type": TransactionType.PAYMENT.value,
    })
    manifest["unmatched_bank_entries"].append({
        "settlement_id": unknown_bank_id,
        "transaction_id": "TXN_UNKNOWN_EXTERNAL_8888",
        "amount": str(unmatched_amt),
    })

    txns_df = pd.DataFrame(transactions)
    settles_df = pd.DataFrame(settlements)
    
    return txns_df, settles_df, manifest


def save_synthetic_data(data_dir: str = "data") -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Generate datasets and persist them to CSV files."""
    os.makedirs(data_dir, exist_ok=True)
    txns_df, settles_df, manifest = generate_synthetic_datasets(seed=42)
    
    txns_path = os.path.join(data_dir, "transactions.csv")
    settles_path = os.path.join(data_dir, "settlements.csv")
    
    txns_df.to_csv(txns_path, index=False)
    settles_df.to_csv(settles_path, index=False)
    
    return txns_df, settles_df, manifest


if __name__ == "__main__":
    txns, settles, manifest = save_synthetic_data("data")
    print(f"Generated {len(txns)} transactions and {len(settles)} settlements.")
    print("Planted Manifest Summary:")
    print(f"- Normal Matched Payments: {manifest['normal_matched_payments']}")
    print(f"- Valid Refunds: {manifest['valid_refunds']}")
    print(f"- Late Settlements (Scenario 1): {len(manifest['late_settlements'])} planted")
    print(f"- Rounding Variances (Scenario 2): {len(manifest['rounding_variances'])} planted")
    print(f"- Duplicate Settlements (Scenario 3): {len(manifest['duplicate_settlements'])} planted")
    print(f"- Orphan Refunds (Scenario 4): {len(manifest['orphan_refunds'])} planted")
    print(f"- Unsettled Transactions: {len(manifest['unsettled_transactions'])} planted")
    print(f"- Amount Mismatches: {len(manifest['amount_mismatches'])} planted")
    print(f"- Unmatched Bank Entries: {len(manifest['unmatched_bank_entries'])} planted")
