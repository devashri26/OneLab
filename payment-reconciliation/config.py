"""Configuration constants, schemas, and definitions for Payment Reconciliation System."""

from decimal import Decimal
from datetime import date
from enum import Enum

# Default Dates and Tolerances
DEFAULT_CUTOFF_DATE = date(2026, 1, 31)
DEFAULT_ROUNDING_TOLERANCE = Decimal("0.05")  # Up to 5 paise considered rounding difference

# Transaction Types
class TransactionType(str, Enum):
    PAYMENT = "PAYMENT"
    REFUND = "REFUND"

# Platform Transaction Statuses
class PlatformStatus(str, Enum):
    SUCCESS = "SUCCESS"
    REFUNDED = "REFUNDED"

# Reconciliation Classifications
class ReconciliationStatus(str, Enum):
    MATCHED = "MATCHED"
    LATE_SETTLEMENT = "LATE_SETTLEMENT"
    ROUNDING_VARIANCE = "ROUNDING_VARIANCE"
    DUPLICATE_SETTLEMENT = "DUPLICATE_SETTLEMENT"
    ORPHAN_REFUND = "ORPHAN_REFUND"
    UNSETTLED = "UNSETTLED"
    AMOUNT_MISMATCH = "AMOUNT_MISMATCH"
    UNMATCHED_BANK_ENTRY = "UNMATCHED_BANK_ENTRY"
    REFUND_EXCEEDS_PAYMENT = "REFUND_EXCEEDS_PAYMENT"

# Required Schema Definitions
REQUIRED_TRANSACTION_COLUMNS = [
    "transaction_id",
    "transaction_date",
    "amount",
    "transaction_type",
    "original_transaction_id",
    "status",
]

REQUIRED_SETTLEMENT_COLUMNS = [
    "settlement_id",
    "transaction_id",
    "settlement_date",
    "amount",
    "transaction_type",
]

# Color mapping for UI status indicators
STATUS_COLORS = {
    ReconciliationStatus.MATCHED.value: "#059669",             # Green
    ReconciliationStatus.LATE_SETTLEMENT.value: "#D97706",      # Amber
    ReconciliationStatus.ROUNDING_VARIANCE.value: "#2563EB",    # Royal Blue
    ReconciliationStatus.DUPLICATE_SETTLEMENT.value: "#DC2626", # Crimson Red
    ReconciliationStatus.ORPHAN_REFUND.value: "#7C3AED",        # Purple
    ReconciliationStatus.UNSETTLED.value: "#F59E0B",            # Orange
    ReconciliationStatus.AMOUNT_MISMATCH.value: "#E11D48",      # Rose Red
    ReconciliationStatus.UNMATCHED_BANK_ENTRY.value: "#475569", # Slate
    ReconciliationStatus.REFUND_EXCEEDS_PAYMENT.value: "#991B1B",# Dark Red
}

# Human-readable status labels
STATUS_LABELS = {
    ReconciliationStatus.MATCHED.value: "Fully Matched",
    ReconciliationStatus.LATE_SETTLEMENT.value: "Late Settlement (Timing Difference)",
    ReconciliationStatus.ROUNDING_VARIANCE.value: "Rounding Variance",
    ReconciliationStatus.DUPLICATE_SETTLEMENT.value: "Duplicate Bank Settlement",
    ReconciliationStatus.ORPHAN_REFUND.value: "Orphan Refund (No Source Payment)",
    ReconciliationStatus.UNSETTLED.value: "Unsettled (In-Transit / Outstanding)",
    ReconciliationStatus.AMOUNT_MISMATCH.value: "Amount Mismatch",
    ReconciliationStatus.UNMATCHED_BANK_ENTRY.value: "Unmatched Bank Settlement",
    ReconciliationStatus.REFUND_EXCEEDS_PAYMENT.value: "Refund Exceeds Original Payment",
}
