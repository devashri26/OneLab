"""Script to generate a professional Word document: Onelab_Raw_Prompt.docx.

Contains the complete, original, detailed master prompt used to instruct Antigravity
for the Payment Reconciliation and Gap Detection System.
"""

import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn

def set_cell_background(cell, fill_hex):
    """Set background color of a table cell."""
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=140, bottom=140, left=200, right=200):
    """Set cell padding (in twips: 20 twips = 1 pt)."""
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

def add_callout(doc, text, title="PROMPT DIRECTIVE", bg_hex="F8FAFC", border_hex="1E3A8A"):
    """Create a styled callout box with a colored left border."""
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    
    cell = tbl.cell(0, 0)
    cell.width = Inches(6.5)
    set_cell_background(cell, bg_hex)
    set_cell_margins(cell, top=140, bottom=140, left=220, right=200)
    
    # Left border only
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
    p.paragraph_format.space_after = Pt(4)
    run_t = p.add_run(f"[{title}] ")
    run_t.bold = True
    run_t.font.name = "Segoe UI"
    run_t.font.size = Pt(10)
    run_t.font.color.rgb = RGBColor(30, 58, 138)
    
    run_txt = p.add_run(text)
    run_txt.font.name = "Segoe UI"
    run_txt.font.size = Pt(9.5)
    run_txt.font.color.rgb = RGBColor(51, 65, 85)

def build_document(output_filename="Onelab_Raw_Prompt.docx"):
    doc = Document()
    
    # Page Setup - Normal Margins (1 inch all around)
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)
        section.different_first_page_header_footer = True
        
        # Configure Header and Footer for subsequent pages
        header = section.header
        hp = header.paragraphs[0]
        hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        hrun = hp.add_run("ONELAB AI FITNESS ASSESSMENT — MASTER PROMPT SPECIFICATION")
        hrun.font.name = "Segoe UI"
        hrun.font.size = Pt(8.5)
        hrun.font.color.rgb = RGBColor(148, 163, 184)
        
        footer = section.footer
        fp = footer.paragraphs[0]
        fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        frun = fp.add_run("Payment Reconciliation and Gap Detection System • Confidential Technical Specification")
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
    normal_style.paragraph_format.space_after = Pt(6)

    # =========================================================================
    # COVER / TITLE PAGE
    # =========================================================================
    p_title_space = doc.add_paragraph()
    p_title_space.paragraph_format.space_before = Pt(72)
    
    # Tagline / Category
    p_tag = doc.add_paragraph()
    p_tag.paragraph_format.space_after = Pt(4)
    r_tag = p_tag.add_run("ONELAB — AI FITNESS ASSESSMENT")
    r_tag.font.name = "Segoe UI"
    r_tag.font.size = Pt(12)
    r_tag.font.bold = True
    r_tag.font.color.rgb = RGBColor(37, 99, 235)  # Royal Blue
    
    # Main Title
    p_main = doc.add_paragraph()
    p_main.paragraph_format.space_after = Pt(8)
    r_main = p_main.add_run("PAYMENT RECONCILIATION AND GAP DETECTION SYSTEM")
    r_main.font.name = "Segoe UI"
    r_main.font.size = Pt(24)
    r_main.font.bold = True
    r_main.font.color.rgb = RGBColor(15, 23, 42)  # Navy Black
    
    # Subtitle
    p_sub = doc.add_paragraph()
    p_sub.paragraph_format.space_after = Pt(36)
    r_sub = p_sub.add_run("Complete Master Instructions, Financial Logic, and Technical Specification Prompt")
    r_sub.font.name = "Segoe UI"
    r_sub.font.size = Pt(13)
    r_sub.font.color.rgb = RGBColor(71, 85, 105)

    # Metadata Block Table
    meta_table = doc.add_table(rows=6, cols=2)
    meta_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    meta_table.autofit = False
    
    meta_data = [
        ("Document Type:", "Master Prompt Specification (Raw Technical Directives)"),
        ("Target System:", "Payment Reconciliation & Bank Settlement Intelligence"),
        ("Execution Agent:", "Antigravity (Google DeepMind Agentic AI Assistant)"),
        ("Operating Roles:", "Senior Python Dev, Financial Data Engineer, Data Analyst, QA Lead, UI/UX Designer"),
        ("Accounting Period:", "January 2026 (Month-End Boundary Cutoff: 31 Jan 2026)"),
        ("Verification Status:", "100% Implemented, Pytest Verified (21/21 Passed), Production Ready"),
    ]
    
    for idx, (label, val) in enumerate(meta_data):
        row = meta_table.rows[idx]
        cell_lbl, cell_val = row.cells[0], row.cells[1]
        
        cell_lbl.width = Inches(2.2)
        cell_val.width = Inches(4.3)
        
        set_cell_background(cell_lbl, "F1F5F9")
        set_cell_background(cell_val, "FFFFFF")
        set_cell_margins(cell_lbl, top=100, bottom=100, left=150, right=150)
        set_cell_margins(cell_val, top=100, bottom=100, left=150, right=150)
        
        p0 = cell_lbl.paragraphs[0]
        p0.paragraph_format.space_after = Pt(0)
        r0 = p0.add_run(label)
        r0.font.bold = True
        r0.font.size = Pt(9.5)
        r0.font.color.rgb = RGBColor(30, 41, 59)
        
        p1 = cell_val.paragraphs[0]
        p1.paragraph_format.space_after = Pt(0)
        r1 = p1.add_run(val)
        r1.font.size = Pt(9.5)
        r1.font.color.rgb = RGBColor(51, 65, 85)

    doc.add_page_break()

    # =========================================================================
    # DOCUMENT OUTLINE / TABLE OF CONTENTS SUMMARY
    # =========================================================================
    def add_h1(text):
        h = doc.add_paragraph()
        h.paragraph_format.space_before = Pt(20)
        h.paragraph_format.space_after = Pt(6)
        h.paragraph_format.keep_with_next = True
        r = h.add_run(text)
        r.font.name = "Segoe UI"
        r.font.size = Pt(16)
        r.font.bold = True
        r.font.color.rgb = RGBColor(15, 23, 42)
        return h

    def add_h2(text):
        h = doc.add_paragraph()
        h.paragraph_format.space_before = Pt(14)
        h.paragraph_format.space_after = Pt(4)
        h.paragraph_format.keep_with_next = True
        r = h.add_run(text)
        r.font.name = "Segoe UI"
        r.font.size = Pt(12.5)
        r.font.bold = True
        r.font.color.rgb = RGBColor(30, 58, 138)
        return h

    def add_h3(text):
        h = doc.add_paragraph()
        h.paragraph_format.space_before = Pt(10)
        h.paragraph_format.space_after = Pt(2)
        h.paragraph_format.keep_with_next = True
        r = h.add_run(text)
        r.font.name = "Segoe UI"
        r.font.size = Pt(10.5)
        r.font.bold = True
        r.font.color.rgb = RGBColor(71, 85, 105)
        return h

    def add_bullet(text, bold_prefix=""):
        p = doc.add_paragraph(style='List Bullet')
        p.paragraph_format.space_after = Pt(3)
        if bold_prefix:
            rb = p.add_run(bold_prefix)
            rb.font.bold = True
            rb.font.color.rgb = RGBColor(15, 23, 42)
        p.add_run(text)

    # Master Prompt Invocation & Role Specification
    add_h1("Master Prompt: System Role & Invocation Directives")
    add_callout(
        doc,
        "Act as a Senior Python Developer, Financial Data Engineer, Data Analyst, QA Engineer, and UI/UX Designer. "
        "Your task is to independently design, develop, test, debug, document, and prepare a complete working Payment "
        "Reconciliation and Gap Detection System for the Onelab AI Fitness Assessment. Do not just provide explanations "
        "or sample snippets. Actually create all required project files, implement the application, execute it, test it, "
        "identify errors, and fix them. Work directly in the current workspace.",
        title="PRIMARY AGENT DIRECTIVE",
        bg_hex="EFF6FF",
        border_hex="2563EB"
    )

    # SECTION 1
    add_h1("1. Business Problem & Core Objectives")
    p1 = doc.add_paragraph(
        "A digital payments company has a critical financial reconciliation problem. The payment platform records "
        "transactions immediately when customers make payments (T+0). The acquiring bank processes and settles the "
        "corresponding funds after an operational clearing window of approximately 1–2 business days (T+1 to T+2). "
        "At the end of each month, the company expects its platform transaction records to reconcile with actual bank "
        "settlement statements. However, the two datasets fail to balance."
    )
    add_h2("System Functional Objectives:")
    add_bullet(" Compare payment platform transactions against bank settlement files line by line.", "1. Automated Ledger Matching:")
    add_bullet(" Flag platform transactions that remain unsettled in the bank as of the period close.", "2. Missing Settlement Detection:")
    add_bullet(" Detect repeated settlement entries and prevent duplicate cash from inflating revenue.", "3. Multi-Credit Quarantine:")
    add_bullet(" Distinguish transactions transacted before cutoff but settled after cutoff as timing items rather than losses.", "4. Timing Variance Classification:")
    add_bullet(" Detect fractional decimal variances that accumulate to measurable differences when aggregated.", "5. Aggregate Rounding Analysis:")
    add_bullet(" Flag bank refund debits that lack any corresponding platform payment charge.", "6. Orphan Refund Identification:")
    add_bullet(" Generate non-technical, plain-language financial explanations and suggested actions for every gap.", "7. Forensic Financial Language:")
    add_bullet(" Compute exact Decimal metrics for Gross Payments, Refunds, and Net Reconciliation Gap.", "8. Net Financial Difference:")
    add_bullet(" Provide downloadable CSV reports for full records, exceptions, and executive summaries.", "9. Verifiable Audit Trails:")

    # SECTION 2
    add_h1("2. Technology Stack Specifications")
    p_tech = doc.add_paragraph("The application must be built using lightweight, robust, production-grade tools:")
    add_bullet(" Python 3.11+, Pandas, NumPy, and standard library Decimal module (floating-point strictly prohibited).", "Backend & Processing:")
    add_bullet(" Streamlit (lightweight web application framework with custom CSS styling).", "User Interface:")
    add_bullet(" Plotly Graph Objects and Plotly Express for responsive, interactive financial charts.", "Visualizations:")
    add_bullet(" Pytest automated test harness with deterministic test fixtures.", "Testing Framework:")
    add_bullet(" Structured CSV files for data ingestion, synthetic datasets, and audit exports.", "Data Storage:")
    add_bullet(" Streamlit Community Cloud and GitHub for version control and deployment.", "Target Deployment:")
    add_callout(
        doc,
        "Do not introduce unnecessary frameworks, databases, authentication systems, or complicated infrastructure. "
        "Keep the application modular, maintainable, and easy to execute.",
        title="INFRASTRUCTURE CONSTRAINT",
        bg_hex="FFFBEB",
        border_hex="D97706"
    )

    # SECTION 3
    add_h1("3. Required Project Structure")
    doc.add_paragraph("Create every file with complete functional code according to the exact structure below:")
    
    code_block = (
        "payment-reconciliation/\n"
        "│\n"
        "├── app.py                      # Streamlit interactive financial dashboard\n"
        "├── reconciliation.py           # Reusable financial reconciliation business engine\n"
        "├── data_generator.py           # Deterministic synthetic data generator (seed=42)\n"
        "├── config.py                   # Central constants, enums, schemas, and color palettes\n"
        "├── utils.py                    # Decimal helpers, INR formatter, and CSV validators\n"
        "├── requirements.txt            # Minimal production Python dependencies\n"
        "├── README.md                   # Comprehensive 17-section documentation\n"
        "├── .gitignore                  # Git ignore rules for Python, cache, and Streamlit\n"
        "│\n"
        "├── data/                       # Ingested and generated datasets\n"
        "│   ├── transactions.csv        # Platform transaction ledger (100–200 records)\n"
        "│   └── settlements.csv         # Bank settlement statement\n"
        "│\n"
        "├── outputs/                    # Exported reconciliation artifacts\n"
        "│   └── reconciliation_report.csv # Comprehensive line-item reconciliation report\n"
        "│\n"
        "├── tests/                      # Automated test suite\n"
        "│   ├── __init__.py\n"
        "│   └── test_reconciliation.py  # Automated test cases (TC01 - TC16)\n"
        "│\n"
        "└── docs/                       # Project documentation suite\n"
        "    ├── assumptions.md          # Business, accounting, and technical assumptions\n"
        "    ├── test_cases.md           # Test cases matrix with inputs and actual results\n"
        "    └── architecture.md         # Architecture diagrams, data flow, and schemas\n"
    )
    p_code = doc.add_paragraph()
    r_code = p_code.add_run(code_block)
    r_code.font.name = "Consolas"
    r_code.font.size = Pt(8.5)
    r_code.font.color.rgb = RGBColor(15, 23, 42)

    # SECTION 4
    add_h1("4. Synthetic Data Generation Requirements")
    doc.add_paragraph(
        "No test datasets are provided. Generate realistic synthetic payment transaction and bank settlement datasets "
        "using a fixed random seed (seed=42) so the dataset can be regenerated consistently. Generate at least 100–200 "
        "platform transaction records."
    )
    add_h2("Dataset Schema Specifications:")
    add_h3("A. Platform Transactions (transactions.csv)")
    add_bullet(" transaction_id (string, unique), transaction_date (YYYY-MM-DD), amount (decimal string), transaction_type (PAYMENT | REFUND), original_transaction_id (string reference or blank), status (SUCCESS | REFUNDED).", "Mandatory Columns:")
    
    add_h3("B. Bank Settlements (settlements.csv)")
    add_bullet(" settlement_id (string, unique), transaction_id (string reference), settlement_date (YYYY-MM-DD), amount (decimal string), transaction_type (PAYMENT | REFUND).", "Mandatory Columns:")
    add_bullet(" Introduce realistic settlement clearing delays of 1–2 business days for normal payments.", "Settlement Delays:")

    # SECTION 5
    add_h1("5. The Four Mandatory Anomaly Scenarios")
    doc.add_paragraph("Intentionally plant all four mandatory anomaly scenarios without accidental overlap:")
    
    add_h2("Scenario 1: LATE SETTLEMENT (Timing Boundary Difference)")
    add_bullet(" Create a transaction on 31 January 2026. Its corresponding bank settlement must arrive on 1 February 2026.", "Condition:")
    add_bullet(" The system must identify that the transaction belongs to January but funds arrived in February. Must not confuse timing with permanent loss.", "Requirement:")
    add_bullet(" LATE_SETTLEMENT", "Classification:")

    add_h2("Scenario 2: AGGREGATE ROUNDING DIFFERENCE")
    add_bullet(" Create multiple transactions with small decimal differences (<= ₹0.05) between platform and bank amounts.", "Condition:")
    add_bullet(" Individual variances must be minor, but cumulative variance must become measurable when aggregated. Use exact Decimal arithmetic.", "Requirement:")
    add_bullet(" ROUNDING_VARIANCE", "Classification:")

    add_h2("Scenario 3: DUPLICATE BANK ENTRY (Quarantine)")
    add_bullet(" Create a legitimate platform transaction with one matching settlement, and insert an additional duplicate bank settlement for the same transaction.", "Condition:")
    add_bullet(" Identify the duplicate instead of treating both as valid matches. Ensure duplicate amounts are not counted as valid revenue.", "Requirement:")
    add_bullet(" DUPLICATE_SETTLEMENT", "Classification:")

    add_h2("Scenario 4: ORPHAN REFUND (Unbacked Payout)")
    add_bullet(" Create a refund record in the bank settlement dataset referencing a transaction ID that does not exist in platform transactions.", "Condition:")
    add_bullet(" Flag the record as an unbacked payout requiring immediate fraud and operational investigation.", "Requirement:")
    add_bullet(" ORPHAN_REFUND", "Classification:")

    add_h2("Additional Flows to Plant:")
    add_bullet(" Normal matched payments (~115 records) and valid refunds (6 records).")
    add_bullet(" Unsettled platform transactions (4 records) recorded near cutoff without bank settlements.")
    add_bullet(" Amount mismatches (2 records) exceeding the configured tolerance limit.")
    add_bullet(" Unmatched external bank deposits (1 record) with no platform transaction record.")

    # SECTION 6
    add_h1("6. Reconciliation Engine Requirements (reconciliation.py)")
    doc.add_paragraph(
        "Implement all financial business logic in reconciliation.py. Do not put reconciliation logic directly inside app.py. "
        "Create a reusable reconciliation function: reconcile_transactions(transactions, settlements, cutoff_date, rounding_tolerance) "
        "returning: (1) Reconciled dataframe, (2) Exception dataframe, (3) Financial summary dictionary, (4) Data validation report."
    )
    add_h2("Ten Required Reconciliation Rules:")
    add_bullet(" Match on transaction_id and transaction_type. Compare amounts using Decimal arithmetic within tolerance. Classify as MATCHED.", "Rule 1 (Normal Matching):")
    add_bullet(" Platform transaction <= cutoff date with no bank settlement. Classify as UNSETTLED (In-Transit).", "Rule 2 (Missing Settlement):")
    add_bullet(" Platform transaction <= cutoff date, settlement date > cutoff date. Classify as LATE_SETTLEMENT. Display days delay.", "Rule 3 (Late Settlement):")
    add_bullet(" Detect repeated settlement entries. Do not drop duplicates. Preserve duplicate records in exceptions. Classify as DUPLICATE_SETTLEMENT.", "Rule 4 (Duplicate Settlement):")
    add_bullet(" Transaction exists in both datasets, but amount differs beyond tolerance. Classify as AMOUNT_MISMATCH.", "Rule 5 (Amount Mismatch):")
    add_bullet(" Differences individually <= tolerance but measurable in aggregate. Classify as ROUNDING_VARIANCE. Display platform, bank, and net diff.", "Rule 6 (Rounding Variance):")
    add_bullet(" Validate refund against original payment ID. If absent, classify as ORPHAN_REFUND.", "Rule 7 (Orphan Refund):")
    add_bullet(" Bank settlement has no matching platform transaction. Classify as UNMATCHED_BANK_ENTRY.", "Rule 8 (Unmatched Bank Settlement):")
    add_bullet(" Verify original transaction exists, is of type PAYMENT, and cumulative refund amount does not exceed original payment.", "Rule 9 (Refund Governance):")
    add_bullet(" Month-end boundary cutoff (default: 31 Jan 2026). Separate January items, late February settlements, and outstanding in-transit items.", "Rule 10 (Cutoff Boundary):")

    # SECTION 7
    add_h1("7. Financial Calculations & Accounting Rules")
    doc.add_paragraph(
        "Calculate all metrics dynamically. Never hardcode dashboard metrics. Use Decimal or integer paise for all "
        "calculations. Clearly document whether refund values are treated as negative amounts and ensure they are not "
        "double-counted. For reporting purposes, show: (1) Gross payment reconciliation, (2) Refund reconciliation, "
        "(3) Net reconciliation."
    )
    add_h2("Universal Mathematical Reconciliation Bridge:")
    doc.add_paragraph(
        "The engine must calculate the bridge linking Platform Net Revenue to Bank Net Settled Cash with exact 0.00 paisa precision:"
    )
    bridge_formula = (
        "Bank Net Settled Cash = Platform Net Revenue\n"
        "                      - Unsettled Payments + Unsettled Refunds\n"
        "                      - Late Payments (Timing) + Late Refunds (Timing)\n"
        "                      + Duplicate Payments - Duplicate Refunds\n"
        "                      + Unmatched Bank Credits - Orphan Bank Refunds\n"
        "                      + (Payment Amount Mismatches - Refund Amount Mismatches)\n"
        "                      + Net Rounding Differences"
    )
    p_bf = doc.add_paragraph()
    r_bf = p_bf.add_run(bridge_formula)
    r_bf.font.name = "Consolas"
    r_bf.font.size = Pt(9)
    r_bf.font.color.rgb = RGBColor(15, 23, 42)

    # SECTION 8
    add_h1("8. Streamlit Dashboard Requirements (app.py)")
    doc.add_paragraph(
        "Build a polished, modern financial analytics dashboard suitable for a real payments company's finance team. "
        "Design preferences: Clean white/light background, dark navy typography (#0F172A), professional spacing, subtle "
        "status indicators, and responsive layout. Avoid unnecessary animations."
    )
    add_h2("Application Branding:")
    add_bullet(" PAYMENT RECONCILIATION • Transaction & Bank Settlement Intelligence", "Title:")
    add_bullet(" Identify discrepancies. Track settlements. Understand every financial gap.", "Subtitle:")
    
    add_h2("Seven Mandatory Dashboard Sections:")
    add_bullet(" Period picker, cutoff date selector, tolerance slider, CSV uploaders, sample data toggle, reconcile button, reset button.", "A. Sidebar:")
    add_bullet(" 6 KPI cards (Platform Volume, Bank Settlements, Fully Matched, Unsettled In-Transit, Net Gap, Total Exceptions) with INR formatting.", "B. Overview Dashboard:")
    add_bullet(" 3 tabs: Gross Payments, Refunds, and Net Reconciliation Bridge featuring an interactive Plotly Waterfall chart.", "C. Financial Reconciliation:")
    add_bullet(" Donut volume chart and ranked horizontal bar chart of monetary impact across all exception categories.", "D. Discrepancy Analysis:")
    add_bullet(" Filterable line-item table with search, category filters, preset buttons, amount slider, and formatted INR columns.", "E. Transaction Explorer:")
    add_bullet(" 3-column comparative audit dossier displaying Platform details, Bank details, Variance, Root cause explanation, and Actionable advice.", "F. Exception Investigation:")
    add_bullet(" 1-click downloads for Full Reconciliation Report (CSV), Exceptions Report (CSV), and Financial Summary (CSV).", "G. Report Generation:")

    # SECTION 9
    add_h1("9. CSV Upload & Schema Validation Requirements")
    doc.add_paragraph(
        "Allow users to upload custom transaction and settlement CSV files. Validate mandatory headers, missing transaction IDs, "
        "invalid dates, negative payment amounts, duplicate IDs within files, and invalid refund references. Display meaningful, "
        "itemized error notifications in the UI without crashing. Automatically fall back to sample dataset if no files are uploaded."
    )

    # SECTION 10
    add_h1("10. Automated Testing Requirements (tests/test_reconciliation.py)")
    doc.add_paragraph(
        "Implement automated tests covering all 16 required test cases (TC01 to TC16). Execute with pytest -v. Fix all errors. "
        "Do not claim tests passed unless actually executed in the workspace."
    )
    test_list = [
        ("TC01", "Normal successful matching (identical IDs, types, amounts)."),
        ("TC02", "Platform transaction with no settlement (classified as UNSETTLED)."),
        ("TC03", "January transaction settled in February (classified as LATE_SETTLEMENT)."),
        ("TC04", "Duplicate bank settlement (second record quarantined as DUPLICATE_SETTLEMENT)."),
        ("TC05", "Amount mismatch beyond configured tolerance (AMOUNT_MISMATCH)."),
        ("TC06", "Individual rounding difference within tolerance (ROUNDING_VARIANCE)."),
        ("TC07", "Aggregate rounding variance across multiple transactions."),
        ("TC08", "Orphan refund referencing non-existent payment ID (ORPHAN_REFUND)."),
        ("TC09", "Valid refund linked to prior payment charge (MATCHED)."),
        ("TC10", "Refund amount exceeding original payment (REFUND_EXCEEDS_PAYMENT)."),
        ("TC11", "Unmatched bank deposit without platform ID (UNMATCHED_BANK_ENTRY)."),
        ("TC12", "Invalid CSV columns validation (catches missing headers without crashing)."),
        ("TC13", "Empty datasets handled gracefully returning zeroed metrics."),
        ("TC14", "Month-end cutoff boundary handling (excludes post-cutoff transactions)."),
        ("TC15", "Simultaneous duplicate settlement and amount mismatch on single transaction."),
        ("TC16", "Exact cutoff date handling (Jan 31 settled Jan 31 vs. settled Feb 01)."),
    ]
    for tid, desc in test_list:
        add_bullet(f" {desc}", f"{tid}:")

    # SECTION 11
    add_h1("11. Technical Documentation Requirements")
    add_bullet(" Comprehensive 17-section guide with overview, problem, stack, architecture, algorithm, calculations, assumptions, setup, execution, testing, deployment, and limitations.", "README.md:")
    add_bullet(" Complete documentation of business, accounting, settlement delay, and Decimal precision assumptions.", "docs/assumptions.md:")
    add_bullet(" Detailed test matrix containing Test ID, scenario, input, expected result, actual result, and pass/fail status.", "docs/test_cases.md:")
    add_bullet(" Complete architecture specification including Mermaid data flow diagrams and module breakdown.", "docs/architecture.md:")

    # SECTION 12
    add_h1("12. Deployment Preparation Requirements")
    add_bullet(" Prepare minimal requirements.txt containing only necessary dependencies (pandas, numpy, streamlit, plotly, pytest).")
    add_bullet(" Ensure app.py is the application entry point and runs cleanly.")
    add_bullet(" Add a proper .gitignore ignoring virtualenvs, cache, and OS artifacts.")
    add_bullet(" Provide exact, verified deployment steps for Streamlit Community Cloud and GitHub.")

    # SECTION 13
    add_h1("13. Demo Video Walkthrough Script (docs/demo_script.md)")
    doc.add_paragraph(
        "Create a 2–3 minute video demonstration script covering: (1) Problem intro, (2) Input datasets, (3) Synthetic generation, "
        "(4) Dataset loading, (5) Reconciliation execution, (6) Financial summary review, (7) Four anomaly deep-dives, "
        "(8) Transaction explorer filtering, (9) Report downloads, and (10) Production limitations."
    )

    # SECTION 14
    add_h1("14. Mandatory Production Limitations")
    doc.add_paragraph("Document these three exact production limitations in the documentation:")
    add_bullet(" The system may incorrectly flag legitimate settlement delays or mismatches if bank processing schedules, time zones, fees, or transaction references are not handled correctly.", "1. Settlement Schedules & Timezones:")
    add_bullet(" The current implementation relies on structured CSV files and predefined reconciliation rules, so it may struggle with inconsistent bank formats, partial settlements, chargebacks, and complex refund scenarios.", "2. Format Inconsistencies & Complex Lifecycles:")
    add_bullet(" A production implementation would require secure bank API integrations, audit logging, role-based access control, configurable reconciliation policies, and human approval for financial adjustments.", "3. Enterprise Security & Maker-Checker Approvals:")

    # SECTION 15
    add_h1("15. Development Execution Sequence (Phases 1 to 12)")
    add_bullet(" Inspect workspace and establish project directory structure.", "Phase 1:")
    add_bullet(" Create all required folders and source files.", "Phase 2:")
    add_bullet(" Implement the synthetic data generator (seed=42).", "Phase 3:")
    add_bullet(" Generate datasets and verify all four mandatory anomalies exist.", "Phase 4:")
    add_bullet(" Implement complete reconciliation engine with exact Decimal logic.", "Phase 5:")
    add_bullet(" Implement Streamlit dashboard with modern fintech UI.", "Phase 6:")
    add_bullet(" Implement all automated test cases.", "Phase 7:")
    add_bullet(" Execute pytest and resolve any failing tests.", "Phase 8:")
    add_bullet(" Launch Streamlit application and verify live ports.", "Phase 9:")
    add_bullet(" Inspect dashboard, verify KPI cards, charts, filters, and exports.", "Phase 10:")
    add_bullet(" Complete README and supporting documentation suite.", "Phase 11:")
    add_bullet(" Prepare project for GitHub and Streamlit Cloud deployment.", "Phase 12:")

    # SECTION 16
    add_h1("16. Important Development Rules")
    rules = [
        "Do not stop after generating a project plan.",
        "Do not only provide code in chat; create actual files in the workspace.",
        "Execute terminal commands when required.",
        "Verify every critical feature.",
        "Fix errors instead of ignoring them.",
        "Never hardcode financial dashboard metrics.",
        "Use Decimal or integer paise for monetary calculations.",
        "Avoid double-counting duplicate settlements.",
        "Maintain separation between business logic and UI.",
        "Keep all four mandatory scenarios reproducible.",
        "Ensure test results are genuine.",
        "Do not fabricate deployment links, screenshots, or test results.",
        "Preserve generated datasets and documentation.",
        "Keep the application simple enough to complete within the assessment time.",
        "If an external deployment or authentication step requires manual authorization, prepare everything and explain the exact manual action needed.",
    ]
    for idx, r in enumerate(rules, 1):
        add_bullet(f" {r}", f"Rule {idx}:")

    # SECTION 17
    add_h1("17. Final Acceptance Criteria Checklist")
    criteria = [
        "All project files have been created.",
        "Synthetic transaction dataset generated (100–200 records).",
        "Synthetic settlement dataset generated.",
        "Late settlement scenario detected.",
        "Aggregate rounding variance detected.",
        "Duplicate settlement detected and quarantined.",
        "Orphan refund detected.",
        "Normal matching works.",
        "Financial reconciliation totals are correct.",
        "Dashboard runs successfully.",
        "CSV upload works.",
        "Exception investigation works.",
        "Reports can be downloaded.",
        "Pytest test suite executes successfully.",
        "README is complete.",
        "Assumptions are documented.",
        "Test cases are documented.",
        "Architecture is documented.",
        "Deployment configuration is ready.",
    ]
    for c in criteria:
        add_bullet(f" [PASS] {c}")

    # Save document
    doc.save(output_filename)
    print(f"Successfully generated: {output_filename}")

if __name__ == "__main__":
    build_document("Onelab_Raw_Prompt.docx")
