# Financial & Accounting Assumptions

## 1. Executive Context
In digital payments, immediate transaction capture on the merchant platform contrasts with the delayed batch clearing cycle of acquiring and settlement banks. This timing asymmetry creates temporary ledger imbalances at period-end cutoffs. This document outlines the formal financial, accounting, and technical assumptions implemented in the Payment Reconciliation and Gap Detection System.

---

## 2. Settlement Cycle & Cutoff Mechanics
* **Instant Capture vs. Delayed Settlement**: Customer payments are authorized and captured in real-time (`T+0`) on the payment platform. Bank clearing operates on a standard `T+1` to `T+2` rolling business-day schedule.
* **Month-End Cutoff Boundary**: The default accounting cutoff is **31 January 2026 (23:59:59 IST)**.
* **Timing Differences vs. Permanent Losses**:
  * A transaction recorded on or before 31 January 2026 whose corresponding bank settlement arrives on or after 1 February 2026 is classified as a **Timing Difference (`LATE_SETTLEMENT`)**.
  * Timing differences do not represent financial loss or revenue leakage. In financial accounting, they are categorized as **Cash-in-Transit (Current Assets)** on the month-end balance sheet and roll forward into the subsequent month's reconciliation opening balance.
* **Unsettled Platform Records**: Transactions initiated near the cutoff (e.g., 30–31 January) that have no bank settlement record as of the audit run date are classified as `UNSETTLED`. These remain under clearing surveillance.

---

## 3. Decimal Arithmetic & Rounding Policy
* **Floating-Point Avoidance**: Standard IEEE 754 floating-point operations (`float`) introduce binary conversion inaccuracies (e.g., `0.1 + 0.2 = 0.30000000000000004`). All monetary computations, comparisons, and aggregations are strictly executed using Python's `Decimal` module with explicit `ROUND_HALF_UP` quantization to two decimal places (`Decimal('0.01')`).
* **Configurable Rounding Tolerance**:
  * The default rounding tolerance is set to **₹0.05** (5 paise).
  * Individual differences `0 < |Difference| <= ₹0.05` are categorized as `ROUNDING_VARIANCE`. These arise from fractional tax (GST/TDS) calculations or micro-fee apportionment.
  * Individual differences `|Difference| > ₹0.05` are categorized as `AMOUNT_MISMATCH` and escalated for fee/MDR contract review.
  * The system tracks both individual variances and the cumulative **Aggregate Rounding Variance** across the entire transaction population.

---

## 4. Duplicate Settlement Quarantine
* **Primary Matching Priority**: When multiple bank settlements cite the same `transaction_id`, the chronological first settlement record is paired with the platform transaction.
* **No Silent Drops**: All subsequent settlement entries for that transaction ID are preserved in the exceptions registry under `DUPLICATE_SETTLEMENT`.
* **Revenue Protection**: Duplicate settlement credits are quarantined and excluded from net settled revenue. Treating duplicate bank credits as valid sales would artificially inflate gross receipts and corrupt bank reconciliation statements (BRS).

---

## 5. Refund Governance & Contra-Revenue Treatment
* **Contra-Flow Definition**: Refunds represent cash outflows from the business to the consumer. For net reconciliation:
  $$\text{Net Platform Revenue} = \text{Gross Platform Payments} - \text{Platform Refunds}$$
  $$\text{Net Bank Settlements} = \text{Gross Bank Settlement Credits} - \text{Bank Refund Debits}$$
* **Orphan Refund Integrity**: Every refund settlement must reference an existing platform payment. Bank refunds referencing non-existent transaction IDs are classified as `ORPHAN_REFUND`, indicating potential fraud, incorrect merchant terminal routing, or unsynchronized manual bank adjustments.
* **Over-Refund Validation**: A refund is validated against the original payment. While partial refunds are supported, the cumulative refund amount cannot exceed the original payment amount. Refunds violating this constraint are flagged as `REFUND_EXCEEDS_PAYMENT`.

---

## 6. Unmatched Bank Credits
* Bank credits with unknown transaction IDs are classified as `UNMATCHED_BANK_ENTRY`.
* These represent unidentified deposits, unmapped POS terminal settlements, direct wire transfers, or misrouted payments from affiliated corporate entities.

---

## 7. Currency & Regional Formatting
* Currency unit: **Indian Rupee (INR / ₹)**.
* Financial outputs utilize the Indian numbering standard (Lakhs and Crores grouping, e.g., `₹12,34,567.89`).
