"""Utility helpers for Decimal currency formatting, Indian number formatting, date parsing, and CSV schema validation."""

import re
from datetime import datetime, date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Tuple, List, Dict, Any
import pandas as pd

from config import (
    REQUIRED_TRANSACTION_COLUMNS,
    REQUIRED_SETTLEMENT_COLUMNS,
    TransactionType,
    PlatformStatus,
)


def to_decimal(value: Any, default: Decimal = Decimal("0.00")) -> Decimal:
    """Safely convert any numeric, float, or string value into an exact 2-decimal Decimal."""
    if value is None or pd.isna(value):
        return default
    try:
        # Stringify to avoid floating point precision quirks
        val_str = str(value).strip().replace(",", "")
        d = Decimal(val_str)
        return d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError, TypeError):
        return default


def parse_date(value: Any) -> date | None:
    """Parse various date formats into datetime.date."""
    if value is None or pd.isna(value):
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    val_str = str(value).strip()
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(val_str, fmt).date()
        except ValueError:
            continue
    return None


def format_inr(amount: Decimal | float | int | None) -> str:
    """Format a monetary amount in Indian Rupee format (Lakhs / Crores).
    
    Example:
        1234567.89 -> ₹12,34,567.89
        -5432.10   -> -₹5,432.10
    """
    if amount is None or pd.isna(amount):
        return "₹0.00"

    d = to_decimal(amount)
    is_negative = d < 0
    d_abs = abs(d)

    parts = f"{d_abs:.2f}".split(".")
    integer_part = parts[0]
    decimal_part = parts[1]

    # Indian Numbering formatting
    if len(integer_part) > 3:
        last_three = integer_part[-3:]
        remaining = integer_part[:-3]
        # Group in pairs of 2 from right to left
        chunks = []
        while len(remaining) > 2:
            chunks.insert(0, remaining[-2:])
            remaining = remaining[:-2]
        if remaining:
            chunks.insert(0, remaining)
        formatted_int = ",".join(chunks) + "," + last_three
    else:
        formatted_int = integer_part

    prefix = "-₹" if is_negative else "₹"
    return f"{prefix}{formatted_int}.{decimal_part}"


def validate_transactions_csv(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """Validate platform transactions dataframe against schema and business integrity rules.
    
    Returns:
        (is_valid, list_of_error_messages)
    """
    errors: List[str] = []
    if df is None or df.empty:
        return False, ["Platform transactions dataset is empty."]

    # 1. Required columns check
    missing_cols = [c for c in REQUIRED_TRANSACTION_COLUMNS if c not in df.columns]
    if missing_cols:
        return False, [f"Missing required transaction columns: {', '.join(missing_cols)}"]

    # 2. Check for null or empty transaction_id
    null_txn_ids = df["transaction_id"].isna().sum() + (df["transaction_id"].astype(str).str.strip() == "").sum()
    if null_txn_ids > 0:
        errors.append(f"Found {null_txn_ids} transaction records with missing or blank 'transaction_id'.")

    # 3. Check for duplicates in transaction_id within platform transactions
    duplicate_txns = df["transaction_id"].dropna().duplicated().sum()
    if duplicate_txns > 0:
        errors.append(f"Found {duplicate_txns} duplicate transaction_ids in platform transactions dataset.")

    # 4. Check for invalid transaction types
    valid_types = {TransactionType.PAYMENT.value, TransactionType.REFUND.value}
    invalid_types = set(df["transaction_type"].dropna().unique()) - valid_types
    if invalid_types:
        errors.append(f"Invalid transaction_type found: {', '.join(invalid_types)}. Expected {valid_types}.")

    # 5. Check for invalid platform status
    valid_statuses = {PlatformStatus.SUCCESS.value, PlatformStatus.REFUNDED.value}
    invalid_statuses = set(df["status"].dropna().unique()) - valid_statuses
    if invalid_statuses:
        errors.append(f"Invalid platform status found: {', '.join(invalid_statuses)}. Expected {valid_statuses}.")

    # 6. Validate amounts
    invalid_amount_count = 0
    negative_payment_count = 0
    zero_amount_count = 0
    for idx, row in df.iterrows():
        try:
            amt = to_decimal(row["amount"])
            t_type = str(row.get("transaction_type", "")).strip().upper()
            if amt == Decimal("0.00"):
                zero_amount_count += 1
            elif amt < 0 and t_type == TransactionType.PAYMENT.value:
                negative_payment_count += 1
        except Exception:
            invalid_amount_count += 1

    if invalid_amount_count > 0:
        errors.append(f"Found {invalid_amount_count} transactions with invalid or unparseable monetary amounts.")
    if negative_payment_count > 0:
        errors.append(f"Found {negative_payment_count} PAYMENT transactions with negative amounts.")
    if zero_amount_count > 0:
        errors.append(f"Found {zero_amount_count} transactions with zero monetary amounts.")

    # 7. Validate dates
    invalid_dates = 0
    for val in df["transaction_date"]:
        if parse_date(val) is None:
            invalid_dates += 1
    if invalid_dates > 0:
        errors.append(f"Found {invalid_dates} records with unparseable or invalid 'transaction_date'.")

    return (len(errors) == 0, errors)


def validate_settlements_csv(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """Validate bank settlements dataframe against schema and integrity rules.
    
    Returns:
        (is_valid, list_of_error_messages)
    """
    errors: List[str] = []
    if df is None or df.empty:
        return False, ["Bank settlements dataset is empty."]

    # 1. Required columns check
    missing_cols = [c for c in REQUIRED_SETTLEMENT_COLUMNS if c not in df.columns]
    if missing_cols:
        return False, [f"Missing required settlement columns: {', '.join(missing_cols)}"]

    # 2. Check for missing settlement_id or transaction_id
    null_settle_ids = df["settlement_id"].isna().sum() + (df["settlement_id"].astype(str).str.strip() == "").sum()
    if null_settle_ids > 0:
        errors.append(f"Found {null_settle_ids} settlement records with missing or blank 'settlement_id'.")

    null_txn_ids = df["transaction_id"].isna().sum() + (df["transaction_id"].astype(str).str.strip() == "").sum()
    if null_txn_ids > 0:
        errors.append(f"Found {null_txn_ids} settlement records with missing or blank 'transaction_id'.")

    # 3. Check for invalid transaction types
    valid_types = {TransactionType.PAYMENT.value, TransactionType.REFUND.value}
    invalid_types = set(df["transaction_type"].dropna().unique()) - valid_types
    if invalid_types:
        errors.append(f"Invalid settlement transaction_type found: {', '.join(invalid_types)}. Expected {valid_types}.")

    # 4. Validate amounts
    invalid_amount_count = 0
    non_positive_amounts = 0
    for idx, row in df.iterrows():
        try:
            amt = to_decimal(row["amount"])
            if amt <= 0:
                non_positive_amounts += 1
        except Exception:
            invalid_amount_count += 1

    if invalid_amount_count > 0:
        errors.append(f"Found {invalid_amount_count} settlements with invalid monetary amounts.")
    if non_positive_amounts > 0:
        errors.append(f"Found {non_positive_amounts} settlements with zero or negative amounts.")

    # 5. Validate dates
    invalid_dates = 0
    for val in df["settlement_date"]:
        if parse_date(val) is None:
            invalid_dates += 1
    if invalid_dates > 0:
        errors.append(f"Found {invalid_dates} records with unparseable or invalid 'settlement_date'.")

    return (len(errors) == 0, errors)
