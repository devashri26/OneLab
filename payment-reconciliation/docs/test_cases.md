# Test Cases & Verification Matrix

The test suite is automated using `pytest` located in `tests/test_reconciliation.py`. All 16 test cases execute deterministic data fixtures with exact Decimal verification.

| Test ID | Test Scenario | Input Data | Expected Result | Actual Result | Pass / Fail |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **TC01** | Normal Successful Matching | Platform `TXN1001` (₹1500.00, 2026-01-10) & Bank `SET5001` (₹1500.00, 2026-01-12) | Status: `MATCHED`, Difference: ₹0.00, Exceptions: 0 | Status: `MATCHED`, Difference: 0.0, Exceptions: 0 | **PASS** |
| **TC02** | Missing Settlement (Unsettled) | Platform `TXN1002` (₹2500.00, 2026-01-25) & Empty Settlements | Status: `UNSETTLED`, Added to exceptions, Unsettled amount: ₹2500.00 | Status: `UNSETTLED`, Exceptions: 1, Amount: ₹2500.00 | **PASS** |
| **TC03** | Late Settlement (Cross-Cutoff) | Platform `TXN1003` (2026-01-31, ₹4850.00) & Bank `SET5003` (2026-02-01, ₹4850.00) with Cutoff: 2026-01-31 | Status: `LATE_SETTLEMENT`, Delay: 1 day, Identified as timing difference | Status: `LATE_SETTLEMENT`, Delay: 1 day, Identified as timing difference | **PASS** |
| **TC04** | Duplicate Bank Settlement | Platform `TXN1004` (₹9500.00) & Two settlements `SET5004A` (₹9500.00) + `SET5004B` (₹9500.00) | `SET5004A`: `MATCHED`; `SET5004B`: `DUPLICATE_SETTLEMENT`, Duplicate amount: ₹9500.00 | First matched, second flagged `DUPLICATE_SETTLEMENT` | **PASS** |
| **TC05** | Amount Mismatch Beyond Tolerance | Platform `TXN1005` (₹7500.00) & Bank `SET5005` (₹7450.00), Tolerance: ₹0.05 | Status: `AMOUNT_MISMATCH`, Difference: -₹50.00 | Status: `AMOUNT_MISMATCH`, Difference: -₹50.00 | **PASS** |
| **TC06** | Individual Rounding Difference | Platform `TXN1006` (₹3200.40) & Bank `SET5006` (₹3200.42), Tolerance: ₹0.05 | Status: `ROUNDING_VARIANCE`, Difference: +₹0.02 | Status: `ROUNDING_VARIANCE`, Difference: +₹0.02 | **PASS** |
| **TC07** | Aggregate Rounding Variance | 3 transactions with individual variances (+0.02, +0.01, +0.02) | 3 records classified `ROUNDING_VARIANCE`, Aggregate net variance: ₹0.05 | Count: 3, Platform: ₹600.00, Bank: ₹600.05, Diff: ₹0.05 | **PASS** |
| **TC08** | Orphan Refund Identification | Bank `SET_ORPHAN` (₹500.00, REFUND, ID: `TXN_UNKNOWN_9999`) with no platform record | Status: `ORPHAN_REFUND`, Exception raised for audit, Amount: ₹500.00 | Status: `ORPHAN_REFUND`, Orphan amount: ₹500.00 | **PASS** |
| **TC09** | Valid Refund Matching | Platform Payment (₹2000.00) + Platform Refund (₹1000.00) with matching settlements | Refund matched, Platform net: ₹1000.00 | Status: `MATCHED`, Net Platform: ₹1000.00 | **PASS** |
| **TC10** | Refund Exceeding Original Payment | Original Payment `TXN1001` (₹500.00) & Attempted Refund `TXN1002` (₹800.00) | Status: `REFUND_EXCEEDS_PAYMENT`, Flagged for fraud/audit review | Status: `REFUND_EXCEEDS_PAYMENT`, Discrepancy logged | **PASS** |
| **TC11** | Unmatched Bank Settlement | Bank Credit `SET9999` (₹6200.00, PAYMENT, ID: `TXN_UNKNOWN_EXTERNAL`) | Status: `UNMATCHED_BANK_ENTRY`, Unmatched Bank Amount: ₹6200.00 | Status: `UNMATCHED_BANK_ENTRY`, Amount: ₹6200.00 | **PASS** |
| **TC12** | Invalid CSV Columns Validation | Datasets missing mandatory headers (`transaction_id`, `amount`, etc.) | Returns `is_valid=False` with itemized descriptive error messages without crashing | `is_valid=False`, Error details captured | **PASS** |
| **TC13** | Empty Datasets Reconciled | Empty transactions DataFrame and empty settlements DataFrame | Graceful handling, returns empty DataFrames, zeroed summaries | Clean exit, zero metrics, no exceptions | **PASS** |
| **TC14** | Month-End Cutoff Boundary | Platform transactions from Jan 20 (₹1000) and Feb 05 (₹2000), Cutoff: 2026-01-31 | Period platform total: ₹1000 (Feb transaction excluded from period) | Platform Period Records: 1, Amount: ₹1000.00 | **PASS** |
| **TC15** | Simultaneous Duplicate & Amount Mismatch | Platform `TXN1015` (₹1000) with Bank `SET15A` (₹900) and Bank `SET15B` (₹1000) | `SET15A`: `AMOUNT_MISMATCH`; `SET15B`: `DUPLICATE_SETTLEMENT` | Both categories flagged and tracked independently | **PASS** |
| **TC16** | Exact Cutoff Boundary Handling | Transacted Jan 31; Settled Jan 31 vs. Settled Feb 01, Cutoff: 2026-01-31 | Jan 31 settlement: `MATCHED`; Feb 01 settlement: `LATE_SETTLEMENT` | Same-day: `MATCHED`, Next-day: `LATE_SETTLEMENT` | **PASS** |

---

## Independent Financial Reconciliation Auditor Test Cases (`tests/test_audit_independent.py`)

| Test ID | Test Scenario | Input Data | Expected Result | Actual Result | Pass / Fail |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **AUDIT-01** | Cumulative Partial Refunds Exceeding Payment | Payment ₹2000; Refund 1: ₹800, Refund 2: ₹1000, Refund 3: ₹500 (Cumulative ₹2300 > ₹2000) | Refunds 1 & 2 `MATCHED`; Refund 3 classified `REFUND_EXCEEDS_PAYMENT` | Cumulative tracking flags Refund 3 as exceeding original charge | **PASS** |
| **AUDIT-02** | Invalid Refund Reference (Chained Refund) | Refund citing another refund ID rather than a payment ID | Status: `ORPHAN_REFUND` (invalid refund source reference) | Successfully rejected as `ORPHAN_REFUND` | **PASS** |
| **AUDIT-03** | Mixed Unsettled Disaggregation | 1 unsettled payment (₹1500) and 1 unsettled refund (₹300) | Disaggregated into `unsettled_payments` (₹1500) and `unsettled_refunds` (₹300); Bridge matches | Count: 1/1, Amount: ₹1500 / ₹300, Bridge Discrepancy: ₹0.00 | **PASS** |
| **AUDIT-04** | Mixed Late Settlements Disaggregation | 1 late payment (₹4000) and 1 late refund (₹800) settling in February | Disaggregated into `late_payments` (₹4000) and `late_refunds` (₹800); Bridge matches | Disaggregated cleanly, Bridge Discrepancy: ₹0.00 | **PASS** |
| **AUDIT-05** | Universal Multi-Anomaly Reconciliation Bridge | Exhaustive dataset featuring all anomaly types simultaneously | Mathematical Bridge Discrepancy: Exact ₹0.00; Net Gap bridged 100% | Bridge Discrepancy: `Decimal('0.00')`, Verified to 0.00 paisa | **PASS** |

---

## Automated Execution Summary
```bash
pytest -v
```
* **Collected**: 21 items (16 Core + 5 Independent Auditor)
* **Passed**: 21 items (100%)
* **Failed**: 0 items
* **Execution Time**: 1.66 seconds
