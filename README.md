# Payment Reconciliation and Gap Detection System
### Transaction & Bank Settlement Intelligence for Finance Teams

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35%2B-FF4B4B.svg)](https://streamlit.io/)
[![Plotly](https://img.shields.io/badge/Plotly-5.20%2B-3F4F75.svg)](https://plotly.com/)
[![Pytest](https://img.shields.io/badge/Pytest-21%20Passed-brightgreen.svg)](https://pytest.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)]()

---

## 1. Project Overview
The **Payment Reconciliation and Gap Detection System** is an enterprise-grade financial data engineering and analytics solution designed to automatically compare payment platform transactions against actual bank settlement records. Built with Python, Pandas, Streamlit, and Plotly, the system automates the detection of financial discrepancies, isolates timing variances from permanent losses, prevents revenue leakage from duplicate bank credits, and produces auditable reconciliation reports formatted in Indian Rupees (INR).

---

## 2. Business Problem
A modern payments platform captures customer transactions immediately in real time (`T+0`). However, acquiring partner banks process and settle corresponding funds after a 1–2 business day delay (`T+1` or `T+2`). At the end of each month, the company expects its platform transaction ledger to reconcile with the bank settlement statement. 

In practice, the two datasets fail to balance due to:
* **Timing cutoffs**: End-of-month transactions settling in the subsequent calendar month.
* **Missing settlements**: Platform transactions with no corresponding bank credit.
* **Duplicate settlements**: Bank clearing engines settling the same transaction multiple times.
* **Rounding variances**: Fractional fee/tax calculations that diverge slightly per transaction but aggregate into meaningful variance across millions of payments.
* **Orphan refunds**: Refund debits appearing on bank statements that lack any matching payment record on the platform.
* **Fee deductions**: Unannounced interchange/MDR fee withholdings by the bank causing amount mismatches.

Without automated reconciliation, finance teams spend days manually cross-referencing spreadsheets, increasing the risk of uncollected funds, incorrect revenue recognition, and audit non-compliance.

---

## 3. Objectives
1. **Automate Comparison**: Ingest platform transactions and bank settlements and execute line-item matching across IDs, transaction types, dates, and amounts.
2. **Isolate Gaps**: Detect and classify all discrepancies into distinct financial exception categories.
3. **Guard Revenue**: Quarantine duplicate bank settlements to prevent double-counting of income.
4. **Distinguish Timing from Loss**: Identify late settlements crossing the month-end boundary as timing differences (in-transit assets) rather than bad debts.
5. **Exact Decimal Precision**: Eliminate floating-point calculation errors using Python's `Decimal` module.
6. **Plain Financial Language**: Provide non-technical explanations and suggested corrective actions for every discrepancy.
7. **Executive Visuals**: Surface KPI metrics, waterfall reconciliation bridges, and interactive charts.
8. **Exportable Audit Trail**: Generate downloadable CSV reconciliation reports, exception logs, and financial summary sheets.

---

## 4. Key Features
* **10 Automated Reconciliation Rules**: Normal matching, in-transit detection, cross-month late settlement handling, duplicate quarantine, fee amount mismatch detection, aggregate rounding analysis, orphan refund identification, refund-exceeds-payment check, unmatched bank entry tracking, and month-end cutoff separation.
* **Forensic Investigation Dossier**: Interactive card displaying transaction ID, bank settlement ID, expected vs. actual amounts, day delay, root-cause explanation, and actionable next steps.
* **Indian Rupee Formatting**: Dynamic Lakh/Crore grouping (`₹12,34,567.89`) across all dashboards and reports.
* **Dynamic Waterfall Reconciliation Bridge**: Interactive Plotly waterfall chart visualizing the bridge from Platform Net Revenue to Bank Net Settled Cash.
* **Robust CSV Validation Engine**: Comprehensive schema and data type validation guarding against missing headers, invalid dates, negative payment amounts, and malformed files without crashing.
* **21 Automated Pytest Cases**: Comprehensive automated test coverage for all rules, cumulative refunds, and independent auditor edge cases.

---

## 5. Technology Stack
* **Language & Runtime**: Python 3.11+
* **Data Processing & Analytics**: Pandas, NumPy
* **Monetary Precision**: Python Standard Library `decimal.Decimal`
* **Web UI Framework**: Streamlit
* **Interactive Visualizations**: Plotly Graph Objects & Plotly Express
* **Automated Testing**: Pytest
* **Data Storage / Interchange**: Structured CSV
* **Target Deployment**: Streamlit Community Cloud / GitHub

---

## 6. Project Architecture
The system decouples the presentation layer from the underlying reconciliation engine:
```
Ingestion (CSV / Generator) 
    ↳ Validation Engine (utils.py)
        ↳ Cleansing & Decimal Quantization
            ↳ Reconciliation Engine (reconciliation.py)
                ↳ Month-End Cutoff Segmentation
                ↳ 10 Financial Rules Application
                ↳ Exact Decimal Aggregator
                    ↳ Streamlit Dashboard (app.py) & Plotly Charts
                    ↳ Audit CSV Exporter (outputs/)
```
For a detailed diagram and deep-dive technical specification, see [`docs/architecture.md`](docs/architecture.md).

---

## 7. Folder Structure
```
payment-reconciliation/
│
├── app.py                      # Streamlit interactive financial dashboard
├── reconciliation.py           # Core decoupled reconciliation business engine
├── data_generator.py           # Deterministic synthetic data generator (seed=42)
├── config.py                   # Central constants, enums, schemas, and color palettes
├── utils.py                    # Decimal helpers, INR formatter, and CSV validators
├── requirements.txt            # Minimal production Python dependencies
├── README.md                   # Comprehensive project documentation
├── .gitignore                  # Git ignore rules for Python, cache, and Streamlit
│
├── data/                       # Ingested and generated datasets
│   ├── transactions.csv        # Platform transaction ledger (135 records)
│   └── settlements.csv         # Bank settlement statement (134 records)
│
├── outputs/                    # Exported reconciliation artifacts
│   └── reconciliation_report.csv # Comprehensive line-item reconciliation report
│
├── tests/                      # Automated test suite
│   ├── __init__.py
│   ├── test_reconciliation.py  # 16 core automated test cases (TC01 - TC16)
│   └── test_audit_independent.py # 5 independent financial auditor test cases (AUDIT-01 to AUDIT-05)
│
└── docs/                       # Project documentation
    ├── assumptions.md          # Business, accounting, and technical assumptions
    ├── test_cases.md           # 16 test cases matrix with inputs and actual results
    ├── architecture.md         # Architecture diagrams, data flow, and schemas
    └── demo_script.md          # 2–3 minute video presentation walkthrough
```

---

## 8. Dataset Description
The system operates on two tabular CSV files:

### A. Platform Transactions (`data/transactions.csv`)
| Column | Type | Description |
| :--- | :--- | :--- |
| `transaction_id` | String | Unique platform transaction identifier (`TXN1001`) |
| `transaction_date` | Date (`YYYY-MM-DD`) | Date customer payment was captured |
| `amount` | Decimal String | Monetary value in INR |
| `transaction_type` | Enum | `PAYMENT` or `REFUND` |
| `original_transaction_id`| String | Reference to parent `PAYMENT` if type is `REFUND` |
| `status` | Enum | `SUCCESS` or `REFUNDED` |

### B. Bank Settlements (`data/settlements.csv`)
| Column | Type | Description |
| :--- | :--- | :--- |
| `settlement_id` | String | Unique bank clearing sequence identifier (`SET5001`) |
| `transaction_id` | String | Platform transaction identifier cited by bank |
| `settlement_date` | Date (`YYYY-MM-DD`) | Date funds cleared and settled in bank account |
| `amount` | Decimal String | Monetary value credited/debited by bank |
| `transaction_type` | Enum | `PAYMENT` (credit) or `REFUND` (debit) |

---

## 9. Four Mandatory Anomaly Scenarios

The synthetic dataset specifically plants and isolates all four required anomalies with zero accidental overlap:

1. **Scenario 1: LATE SETTLEMENT**
   * *Injected Record*: Transaction on 31 January 2026 (`TXN1122`, ₹4,850.00; `TXN1123`, ₹12,400.50). Corresponding bank settlement arrives on 1 February 2026.
   * *Classification*: `LATE_SETTLEMENT`.
   * *Accounting Treatment*: Categorized as Cash-in-Transit (Current Asset) at January 31 month-end close. Rolls forward to February opening balance.

2. **Scenario 2: AGGREGATE ROUNDING DIFFERENCE**
   * *Injected Records*: 5 transactions (`TXN1124` to `TXN1128`) with individual micro-variances of +₹0.02, -₹0.01, +₹0.03, -₹0.02, +₹0.02.
   * *Classification*: `ROUNDING_VARIANCE`.
   * *Accounting Treatment*: Individual differences fall within the ₹0.05 tolerance. The cumulative aggregate difference (+₹0.05) is tracked and routed to the Rounding/FX variance ledger.

3. **Scenario 3: DUPLICATE BANK ENTRY**
   * *Injected Record*: Legitimate platform transaction `TXN1129` (₹9,500.00) matches settlement `SET5129`. A duplicate bank credit `SET5130` (₹9,500.00) is inserted.
   * *Classification*: `DUPLICATE_SETTLEMENT`.
   * *Accounting Treatment*: Quarantined immediately. Excluded from valid recognized revenue to avoid double-counting cash receipts.

4. **Scenario 4: ORPHAN REFUND**
   * *Injected Record*: Bank settlement `SET5131` records a refund debit of ₹2,400.00 referencing `TXN_NONEXISTENT_9999`.
   * *Classification*: `ORPHAN_REFUND`.
   * *Accounting Treatment*: Flagged for immediate fraud/operations audit because no customer payment exists to justify the payout.

---

## 10. Reconciliation Algorithm
The core function `reconcile_transactions(transactions, settlements, cutoff_date, rounding_tolerance)` operates through deterministic matching steps:
1. **Schema & Date Ingestion**: Parses dates into standard date objects; converts amounts into `Decimal` quantized to 2 decimal places.
2. **Index Construction**: Indexes platform transactions by `transaction_id`; groups settlements by `transaction_id`.
3. **Period Partitioning**: Selects platform transactions where `transaction_date <= cutoff_date`.
4. **Primary Matching**:
   * If zero settlements match $\to$ `UNSETTLED`.
   * If settlement date $>$ `cutoff_date` $\to$ `LATE_SETTLEMENT`.
   * If refund lacks valid parent payment $\to$ `ORPHAN_REFUND`.
   * If refund exceeds original payment $\to$ `REFUND_EXCEEDS_PAYMENT`.
   * If $\Delta = 0 \to$ `MATCHED`.
   * If $0 < |\Delta| \le \text{Tolerance} \to$ `ROUNDING_VARIANCE`.
   * If $|\Delta| > \text{Tolerance} \to$ `AMOUNT_MISMATCH`.
5. **Duplicate Quarantine**: Traverses bank settlements where more than one credit exists for a single transaction ID; marks secondary records as `DUPLICATE_SETTLEMENT`.
6. **Unmatched Bank Clearance**: Classifies remaining orphan bank credits as `UNMATCHED_BANK_ENTRY`.

---

## 11. Financial Calculation Methodology
All financial aggregates are computed dynamically using exact Decimal arithmetic:
* **Gross Platform Payments**: $\sum \text{Payment Transactions}_{\le \text{Cutoff}}$
* **Platform Refunds**: $\sum \text{Refund Transactions}_{\le \text{Cutoff}}$
* **Net Platform Expected Revenue**: $\text{Gross Platform Payments} - \text{Platform Refunds}$
* **In-Period Bank Gross Settlements**: $\sum \text{Bank Payment Credits}_{\le \text{Cutoff}}$
* **In-Period Bank Refunds**: $\sum \text{Bank Refund Debits}_{\le \text{Cutoff}}$
* **Net Bank Settled Cash**: $\text{In-Period Bank Gross Settlements} - \text{In-Period Bank Refunds}$
* **Net Reconciliation Gap**:
  $$\text{Reconciliation Gap} = \text{Net Bank Settled Cash} - \text{Net Platform Expected Revenue}$$
  This gap is fully bridged by:
  $$\text{Gap} = -\text{Unsettled} - \text{Late Settlements} + \text{Duplicates} + \text{Unmatched Bank} - \text{Orphan Refunds} + \text{Mismatches \& Rounding}$$

---

## 12. Assumptions
Full accounting principles and operational assumptions are detailed in [`docs/assumptions.md`](docs/assumptions.md).

---

## 13. Installation Instructions

### Prerequisites
* Python 3.11, 3.12, or 3.13 installed
* Git

### Step-by-Step Setup
1. Clone or navigate to the project directory:
   ```bash
   cd payment-reconciliation
   ```
2. (Optional) Create and activate a Python virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```
3. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

---

## 14. Execution Instructions

### A. Run Data Generator (Optional / Pre-Generated)
To regenerate the synthetic datasets from seed 42:
```bash
python data_generator.py
```

### B. Launch Streamlit Financial Dashboard
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## 15. Testing Instructions
Execute the automated test suite with full verbose reporting:
```bash
pytest -v
```
All 16 test cases (TC01 to TC16) will execute and assert exact classifications and monetary differences.

For detailed test coverage documentation, see [`docs/test_cases.md`](docs/test_cases.md).

---

## 16. Deployment Instructions (Streamlit Community Cloud & GitHub)
1. Initialize Git repository and commit all project files:
   ```bash
   git init
   git add .
   git commit -m "feat: complete payment reconciliation system"
   ```
2. Push to your GitHub account:
   ```bash
   git remote add origin https://github.com/<YOUR-USERNAME>/payment-reconciliation.git
   git branch -M main
   git push -u origin main
   ```
3. Open [Streamlit Community Cloud](https://share.streamlit.io/).
4. Click **"New app"**.
5. Connect your GitHub repository:
   * **Repository**: `<YOUR-USERNAME>/payment-reconciliation`
   * **Branch**: `main`
   * **Main file path**: `app.py`
6. Click **"Deploy!"**.
7. The application will build dependencies from `requirements.txt` and launch your live public URL.

---

## 17. Known Production Limitations
As mandated for financial systems scaling from prototype to production:

1. **Settlement Schedules & Timezone Discrepancies**:
   The system may incorrectly flag legitimate settlement delays or mismatches if bank processing schedules (e.g., weekend/holiday RTGS/NEFT batch windows), time zones (UTC vs. IST), banking fees (MDR / interchange deductions), or complex transaction references are not modeled dynamically.

2. **Format Inconsistency & Complex Lifecycles**:
   The current implementation relies on structured CSV files and predefined reconciliation rules, so it may struggle with inconsistent multi-bank MT940/CAMT statement formats, split partial settlements, chargeback disputes, pre-arbitration reversals, and multi-currency foreign exchange adjustments.

3. **Enterprise Security & Governance Controls**:
   A production implementation would require secure, encrypted host-to-host bank API integrations (SFTP/REST with mTLS), immutable audit logging, role-based access control (RBAC), configurable reconciliation tolerance policies by payment rails, and multi-tier maker-checker human approval workflows before posting financial adjusting journal entries to the ERP / General Ledger.
