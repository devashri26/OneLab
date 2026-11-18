"""Script to generate Onelab_Distilled_Prompt.docx.

Contains a concise, refined, executive-structured version of the requirements
for the Onelab Payment Reconciliation and Gap Detection System.
"""

import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

def set_cell_background(cell, fill_hex):
    """Set background color of a table cell."""
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=120, bottom=120, left=180, right=180):
    """Set cell padding in twips."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>'
        f'<w:top w:w="{top}" w:type="dxa"/>'
        f'<w:bottom w:w="{bottom}" w:type="dxa"/>'
        f'<w:left w:w="{left}" w:type="dxa"/>'
        f'<w:right w:w="{right}" w:type="dxa"/>'
        f'</w:tcMar>'
    )
    tcPr.append(tcMar)

def add_callout(doc, text, title="EXECUTIVE SUMMARY", bg_hex="F8FAFC", border_hex="2563EB"):
    """Create a styled callout box with a colored left border."""
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    
    cell = tbl.cell(0, 0)
    cell.width = Inches(6.5)
    set_cell_background(cell, bg_hex)
    set_cell_margins(cell, top=130, bottom=130, left=200, right=180)
    
    tcPr = cell._tc.get_or_add_tcPr()
    borders = parse_xml(
        f'<w:tcBorders {nsdecls("w")}>'
        f'<w:top w:val="none"/>'
        f'<w:left w:val="single" w:sz="36" w:space="0" w:color="{border_hex}"/>'
        f'<w:bottom w:val="none"/>'
        f'<w:right w:val="none"/>'
        f'</w:tcBorders>'
    )
    tcPr.append(borders)
    
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(2)
    run_t = p.add_run(f"[{title}] ")
    run_t.bold = True
    run_t.font.name = "Segoe UI"
    run_t.font.size = Pt(9.5)
    run_t.font.color.rgb = RGBColor(30, 58, 138)
    
    run_txt = p.add_run(text)
    run_txt.font.name = "Segoe UI"
    run_txt.font.size = Pt(9)
    run_txt.font.color.rgb = RGBColor(51, 65, 85)

def build_distilled_document(output_filename="Onelab_Distilled_Prompt.docx"):
    doc = Document()
    
    # Page Margins: 1.0 inch
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)
        section.different_first_page_header_footer = True
        
        # Header & Footer for pages 2+
        header = section.header
        hp = header.paragraphs[0]
        hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        hrun = hp.add_run("ONELAB AI FITNESS ASSESSMENT — DISTILLED SPECIFICATION")
        hrun.font.name = "Segoe UI"
        hrun.font.size = Pt(8.5)
        hrun.font.color.rgb = RGBColor(148, 163, 184)
        
        footer = section.footer
        fp = footer.paragraphs[0]
        fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        frun = fp.add_run("Payment Reconciliation and Gap Detection System • Distilled Technical Requirements")
        frun.font.name = "Segoe UI"
        frun.font.size = Pt(8.5)
        frun.font.color.rgb = RGBColor(148, 163, 184)

    # Base Styles
    styles = doc.styles
    normal_style = styles['Normal']
    normal_style.font.name = 'Segoe UI'
    normal_style.font.size = Pt(10)
    normal_style.font.color.rgb = RGBColor(30, 41, 59)
    normal_style.paragraph_format.line_spacing = 1.15
    normal_style.paragraph_format.space_after = Pt(5)

    # =========================================================================
    # TITLE PAGE
    # =========================================================================
    p_sp = doc.add_paragraph()
    p_sp.paragraph_format.space_before = Pt(80)
    
    # Category Tag
    p_tag = doc.add_paragraph()
    p_tag.paragraph_format.space_after = Pt(4)
    r_tag = p_tag.add_run("ONELAB — AI FITNESS ASSESSMENT")
    r_tag.font.name = "Segoe UI"
    r_tag.font.size = Pt(11.5)
    r_tag.font.bold = True
    r_tag.font.color.rgb = RGBColor(37, 99, 235)  # Royal Blue
    
    # Main Title
    p_main = doc.add_paragraph()
    p_main.paragraph_format.space_after = Pt(8)
    r_main = p_main.add_run("PAYMENT RECONCILIATION AND GAP DETECTION SYSTEM")
    r_main.font.name = "Segoe UI"
    r_main.font.size = Pt(23)
    r_main.font.bold = True
    r_main.font.color.rgb = RGBColor(15, 23, 42)
    
    # Subtitle
    p_sub = doc.add_paragraph()
    p_sub.paragraph_format.space_after = Pt(36)
    r_sub = p_sub.add_run("Distilled Master Requirements & Technical Specification Document")
    r_sub.font.name = "Segoe UI"
    r_sub.font.size = Pt(13)
    r_sub.font.color.rgb = RGBColor(71, 85, 105)

    # Metadata Block Table
    meta_table = doc.add_table(rows=5, cols=2)
    meta_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    meta_table.autofit = False
    
    meta_data = [
        ("Document Type:", "Distilled Technical Requirements & Prompt Specification"),
        ("System Architecture:", "Decoupled Reconciliation Engine + Streamlit Fintech Dashboard"),
        ("Technology Stack:", "Python 3.11+, Pandas, NumPy, Decimal, Streamlit, Plotly, Pytest"),
        ("Primary Deliverables:", "Engine, Web Dashboard, Synthetic Data Generator, Automated Test Suite, Docs"),
        ("Verification Standard:", "Exact Decimal Precision (0.00 Discrepancy), 21 Pytest Cases Passed"),
    ]
    
    for idx, (label, val) in enumerate(meta_data):
        row = meta_table.rows[idx]
        cell_lbl, cell_val = row.cells[0], row.cells[1]
        cell_lbl.width = Inches(2.2)
        cell_val.width = Inches(4.3)
        
        set_cell_background(cell_lbl, "F1F5F9")
        set_cell_background(cell_val, "FFFFFF")
        set_cell_margins(cell_lbl, top=90, bottom=90, left=140, right=140)
        set_cell_margins(cell_val, top=90, bottom=90, left=140, right=140)
        
        p0 = cell_lbl.paragraphs[0]
        p0.paragraph_format.space_after = Pt(0)
        r0 = p0.add_run(label)
        r0.font.bold = True
        r0.font.size = Pt(9)
        r0.font.color.rgb = RGBColor(30, 41, 59)
        
        p1 = cell_val.paragraphs[0]
        p1.paragraph_format.space_after = Pt(0)
        r1 = p1.add_run(val)
        r1.font.size = Pt(9)
        r1.font.color.rgb = RGBColor(51, 65, 85)

    doc.add_page_break()

    # =========================================================================
    # HELPER FUNCTIONS FOR SECTIONS
    # =========================================================================
    def add_h1(text):
        h = doc.add_paragraph()
        h.paragraph_format.space_before = Pt(16)
        h.paragraph_format.space_after = Pt(5)
        h.paragraph_format.keep_with_next = True
        r = h.add_run(text)
        r.font.name = "Segoe UI"
        r.font.size = Pt(14)
        r.font.bold = True
        r.font.color.rgb = RGBColor(15, 23, 42)
        return h

    def add_bullet(text, bold_prefix=""):
        p = doc.add_paragraph(style='List Bullet')
        p.paragraph_format.space_after = Pt(3)
        if bold_prefix:
            rb = p.add_run(bold_prefix)
            rb.font.bold = True
            rb.font.color.rgb = RGBColor(15, 23, 42)
        p.add_run(text)

    # Document Overview Callout
    add_callout(
        doc,
        "This document provides the concise, distilled master requirements for the Onelab Payment Reconciliation "
        "and Gap Detection System. It outlines the core objective, technology stack, synthetic data specs, four mandatory "
        "gap detection scenarios, financial accounting rules, dashboard features, testing standards, and QA criteria.",
        title="EXECUTIVE BRIEF",
        bg_hex="EFF6FF",
        border_hex="2563EB"
    )

    # 1. OBJECTIVE
    add_h1("1. System Objective")
    doc.add_paragraph(
        "Build a production-grade, modular financial reconciliation system that automatically compares internal payment "
        "platform transaction records against actual bank settlement statements. The system must identify missing transactions, "
        "quarantine duplicate settlements, classify cross-month timing differences, detect cumulative rounding variances, "
        "flag orphan refunds, calculate the net financial difference, and generate downloadable audit reports for finance teams."
    )

    # 2. TECHNOLOGY STACK
    add_h1("2. Core Technology Stack")
    add_bullet(" Python 3.11+ using Pandas, NumPy, and standard library Decimal (floating-point strictly prohibited).", "Backend Processing:")
    add_bullet(" Streamlit with a modern light fintech UI, dark navy typography, responsive grid, and custom CSS.", "User Interface:")
    add_bullet(" Plotly Graph Objects and Plotly Express for interactive waterfall, donut, and ranked horizontal charts.", "Visualizations:")
    add_bullet(" Pytest automated test harness with deterministic assertion fixtures.", "Testing:")
    add_bullet(" Structured CSV files for inputs, synthetic generation, and audit report downloads.", "Data Storage:")
    add_bullet(" Streamlit Community Cloud and GitHub for public hosting and version control.", "Deployment:")

    # 3. SYNTHETIC DATA GENERATION
    add_h1("3. Synthetic Data Requirements")
    doc.add_paragraph(
        "Generate realistic, reproducible synthetic payment transaction and bank settlement datasets using a fixed random seed (seed=42):"
    )
    add_bullet(" Generate between 100 and 200 platform transaction records (e.g., 135 transactions).", "Record Volume:")
    add_bullet(" transaction_id, transaction_date, amount, transaction_type (PAYMENT | REFUND), original_transaction_id, status (SUCCESS | REFUNDED).", "transactions.csv Schema:")
    add_bullet(" settlement_id, transaction_id, settlement_date, amount, transaction_type (PAYMENT | REFUND).", "settlements.csv Schema:")
    add_bullet(" Introduce realistic settlement clearing delays of 1–2 business days for normal payments.", "Clearing Window:")

    # 4. MANDATORY GAP DETECTION
    add_h1("4. Mandatory Gap Detection Scenarios")
    doc.add_paragraph(
        "The system must intentionally plant and deterministically detect all four mandatory financial anomaly scenarios with zero overlap:"
    )
    add_bullet(" Platform transaction executed on or before month-end cutoff (31 Jan 2026) with bank settlement arriving post-cutoff (1 Feb 2026). Must be classified as a timing difference (in-transit asset), not a financial loss.", "1. Late Settlement (LATE_SETTLEMENT):")
    add_bullet(" Multiple transactions with small individual decimal differences (<= ₹0.05) between platform and bank amounts that accumulate to a measurable variance across the aggregate portfolio.", "2. Aggregate Rounding Difference (ROUNDING_VARIANCE):")
    add_bullet(" A legitimate transaction with one valid settlement plus an additional repeated bank settlement. The duplicate must be quarantined and excluded from recognized revenue.", "3. Duplicate Bank Settlement (DUPLICATE_SETTLEMENT):")
    add_bullet(" Bank settlement recording a refund debit that references a non-existent platform transaction ID. Must be flagged as an unbacked payout for fraud/audit review.", "4. Orphan Refund (ORPHAN_REFUND):")
    add_bullet(" Normal matched payments, valid refunds, in-transit unsettled platform transactions, amount mismatches, and unmatched external bank credits.", "Additional Planted Flows:")

    # 5. RECONCILIATION ENGINE
    add_h1("5. Core Reconciliation Engine")
    doc.add_paragraph(
        "Implement all financial business logic in a decoupled module (reconciliation.py) without Streamlit dependencies. "
        "Provide a reusable function: reconcile_transactions(transactions, settlements, cutoff_date, rounding_tolerance) returning "
        "a reconciled dataframe, exception dataframe, financial summary dictionary, and validation report."
    )
    add_bullet(" Match on transaction ID and type. Compare amounts using exact Decimal precision within tolerance. Classify as MATCHED.", "Rule 1 (Normal Matching):")
    add_bullet(" Platform transaction within cutoff with no bank settlement. Classify as UNSETTLED (In-Transit).", "Rule 2 (Missing Settlement):")
    add_bullet(" Transaction in-period, bank settlement post-cutoff. Classify as LATE_SETTLEMENT and compute clearing days delay.", "Rule 3 (Late Settlement):")
    add_bullet(" Repeated bank settlements quarantined. Revenue protected from double-counting. Classify as DUPLICATE_SETTLEMENT.", "Rule 4 (Duplicate Settlement):")
    add_bullet(" Transaction exists in both datasets, but difference exceeds tolerance. Classify as AMOUNT_MISMATCH.", "Rule 5 (Amount Mismatch):")
    add_bullet(" Difference <= tolerance. Classify as ROUNDING_VARIANCE and aggregate cumulative difference.", "Rule 6 (Rounding Variance):")
    add_bullet(" Bank refund lacking valid platform payment reference. Classify as ORPHAN_REFUND.", "Rule 7 (Orphan Refund):")
    add_bullet(" External bank settlement credit with unknown transaction ID. Classify as UNMATCHED_BANK_ENTRY.", "Rule 8 (Unmatched Bank Entry):")
    add_bullet(" Verify original payment exists, is a PAYMENT, and cumulative refunds do not exceed original payment.", "Rule 9 (Refund Governance):")
    add_bullet(" Implement month-end boundary cutoff (default: 31 Jan 2026). Exclude subsequent period records from current audit.", "Rule 10 (Cutoff Boundary):")

    # 6. FINANCIAL REPORTING & MATHEMATICAL ACCURACY
    add_h1("6. Financial Reporting & Monetary Accuracy")
    doc.add_paragraph(
        "Calculate all metrics dynamically without hardcoding. Use Python Decimal for exact monetary arithmetic. Document that "
        "refunds represent contra-revenue/cash outflows. Present three distinct reconciliation dimensions:"
    )
    add_bullet(" Platform Expected Gross Payments vs. Bank Cleared Payments minus in-transit and late items plus duplicates and unmatched credits.", "1. Gross Payment Ledger:")
    add_bullet(" Platform Expected Refunds vs. Bank Cleared Refunds plus orphan refunds and duplicate refund debits.", "2. Refund Ledger:")
    add_bullet(" Bridge Platform Net Revenue to Bank Net Settled Cash with exact 0.00 paisa mathematical verification.", "3. Universal Net Bridge:")

    # 7. STREAMLIT DASHBOARD
    add_h1("7. Executive Streamlit Dashboard")
    doc.add_paragraph("Develop a modern fintech web interface (app.py) structured into seven functional sections:")
    add_bullet(" Accounting period selector, cutoff date picker, tolerance slider, CSV uploaders, sample data toggle, and reconcile button.", "A. Sidebar Controls:")
    add_bullet(" 6 KPI cards (Platform Volume, Bank Settlements, Matched, In-Transit, Net Gap, Exceptions) formatted in Indian Rupees (₹).", "B. Overview Dashboard:")
    add_bullet(" 3 tabs for Gross Payments, Refunds, and Net Reconciliation Bridge with an interactive Plotly Waterfall chart.", "C. Financial Reconciliation:")
    add_bullet(" Donut chart for exception volume and ranked horizontal bar chart for monetary impact.", "D. Discrepancy Analysis:")
    add_bullet(" Searchable and filterable table with quick preset buttons (All, Exceptions, Matched, Late, Duplicates) and INR columns.", "E. Transaction Explorer:")
    add_bullet(" 3-column comparative audit dossier showing Platform record, Bank record, Variance, Root cause, and Actionable advice.", "F. Exception Investigation:")
    add_bullet(" 1-click downloads for Full Reconciliation Report (CSV), Exceptions Report (CSV), and Financial Summary (CSV).", "G. Report Generation:")

    # 8. VALIDATION
    add_h1("8. CSV Upload & Data Validation")
    doc.add_paragraph(
        "Support custom user CSV uploads in the sidebar. Validate mandatory headers, missing transaction IDs, invalid date formats, "
        "negative payment amounts, and invalid refund references. Display itemized, user-friendly error alerts without crashing, "
        "and automatically fall back to the synthetic sample dataset when no files are uploaded."
    )

    # 9. TESTING
    add_h1("9. Automated Testing (Pytest)")
    doc.add_paragraph(
        "Implement comprehensive automated pytest test suites (tests/test_reconciliation.py and tests/test_audit_independent.py). "
        "Cover all 16 required core test cases (TC01 to TC16) plus 5 independent financial auditor test cases (cumulative partial "
        "refunds, chained refund validation, mixed unsettled items, late settlement disaggregation, and multi-anomaly bridge verification). "
        "All test cases must execute and achieve a 100% pass rate."
    )

    # 10. DOCUMENTATION
    add_h1("10. Technical Documentation Deliverables")
    add_bullet(" 17-section comprehensive guide with business problem, stack, architecture, algorithm, calculations, assumptions, setup, execution, testing, deployment, and production limitations.", "README.md:")
    add_bullet(" Business, accounting, clearing window, and Decimal precision principles.", "docs/assumptions.md:")
    add_bullet(" Test matrix detailing Test ID, scenario, input, expected result, actual result, and pass status.", "docs/test_cases.md:")
    add_bullet(" System architecture, Mermaid data flow diagrams, and module interface designs.", "docs/architecture.md:")
    add_bullet(" 2.5–3 minute video demonstration script with step-by-step narration and timestamps.", "docs/demo_script.md:")

    # 11. DEPLOYMENT
    add_h1("11. Cloud Deployment & GitHub Delivery")
    add_bullet(" Clean requirements.txt containing only essential dependencies (pandas, numpy, streamlit, plotly, pytest).")
    add_bullet(" Clean .gitignore ignoring virtual environments, pycache, and OS metadata.")
    add_bullet(" Verified local startup on port 8501 returning HTTP 200 OK.")
    add_bullet(" Code pushed to GitHub repository (main branch) and ready for 1-click deployment on Streamlit Community Cloud.")

    # 12. QUALITY ASSURANCE & AUDIT
    add_h1("12. Quality Assurance & Independent Audit Verification")
    add_bullet(" Conduct an independent financial reconciliation audit on all calculations, signs, and cutoff boundaries.")
    add_bullet(" Disaggregate Gross Matched Payments from Matched Refunds rather than lumping them together.")
    add_bullet(" Correct orphan refund cash variance sign to reflect negative net cash outflow (-b_amount).")
    add_bullet(" Prevent post-cutoff bank settlements from leaking into current-period unmatched bank credits.")
    add_bullet(" Implement stateful cumulative refund tracking capping partial refunds at original payment amount.")
    add_bullet(" Verify that the universal reconciliation bridge discrepancy is exact ₹0.00 paisa under all edge cases.")

    # Save document
    doc.save(output_filename)
    print(f"Successfully generated: {output_filename}")

if __name__ == "__main__":
    build_distilled_document("Onelab_Distilled_Prompt.docx")
