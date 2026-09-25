import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn

def create_document():
    doc = docx.Document()

    # Configure Margins (0.8 inch for clean professional look)
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)

    # Color Palette Constants
    HEX_PRIMARY = "1A365D"      # Deep Navy
    HEX_SECONDARY = "2B6CB0"    # Ocean Blue
    HEX_ACCENT = "DD6B20"       # Civic Orange
    HEX_BG_LIGHT = "F7FAFC"     # Off-White / Light Grey
    HEX_BORDER = "CBD5E0"       # Border Grey
    HEX_TEXT = "2D3748"         # Charcoal Text

    COLOR_PRIMARY = RGBColor(26, 54, 93)
    COLOR_SECONDARY = RGBColor(43, 108, 176)
    COLOR_DARK = RGBColor(45, 55, 72)
    COLOR_MUTED = RGBColor(113, 128, 150)

    # Helper: Set Cell Background Color
    def set_cell_bg(cell, fill_hex):
        tcPr = cell._tc.get_or_add_tcPr()
        shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
        tcPr.append(shd)

    # Helper: Set Cell Margins (Padding)
    def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
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

    # Helper: Add Callout Box
    def add_callout(text, title="KEY TAKEAWAY", bg_hex="EBF8FF", border_color="3182CE"):
        table = doc.add_table(rows=1, cols=1)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        cell = table.cell(0, 0)
        set_cell_bg(cell, bg_hex)
        set_cell_margins(cell, top=140, bottom=140, left=200, right=200)
        
        # Border
        tcPr = cell._tc.get_or_add_tcPr()
        borders = parse_xml(
            f'<w:tcBorders {nsdecls("w")}>'
            f'<w:left w:val="single" w:sz="24" w:space="0" w:color="{border_color}"/>'
            f'<w:top w:val="none"/>'
            f'<w:right w:val="none"/>'
            f'<w:bottom w:val="none"/>'
            f'</w:tcBorders>'
        )
        tcPr.append(borders)

        p = cell.paragraphs[0]
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(4)
        run_title = p.add_run(f"📌 {title}\n")
        run_title.bold = True
        run_title.font.name = "Segoe UI"
        run_title.font.size = Pt(10.5)
        run_title.font.color.rgb = COLOR_SECONDARY

        run_text = p.add_run(text)
        run_text.font.name = "Segoe UI"
        run_text.font.size = Pt(10)
        run_text.font.color.rgb = COLOR_DARK
        doc.add_paragraph() # Spacing

    # ==================== TITLE / COVER HEADER ====================
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(0)
    p_title.paragraph_format.space_after = Pt(4)
    run_title = p_title.add_run("MUNICIPAL TENDER WATCHDOG")
    run_title.bold = True
    run_title.font.name = "Segoe UI"
    run_title.font.size = Pt(24)
    run_title.font.color.rgb = COLOR_PRIMARY

    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sub.paragraph_format.space_after = Pt(12)
    run_sub = p_sub.add_run("AI-Augmented Civic Accountability Co-Pilot for Urban Solid Waste Procurement")
    run_sub.font.name = "Segoe UI"
    run_sub.font.size = Pt(13)
    run_sub.font.color.rgb = COLOR_SECONDARY

    # Metadata Box
    meta_table = doc.add_table(rows=2, cols=2)
    meta_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    meta_data = [
        [("Track / Domain:", "Smart Cities / Transparent Gov-Tech / Civic AI"), ("Focus Geography:", "Coimbatore Urban Local Bodies (CCMC & Town Panchayats)")],
        [("Primary Target System:", "TN e-Procurement Portal (tntenders.gov.in)"), ("Evaluation Document:", "Hackathon Master Project Dossier & Review Guide")]
    ]
    for r_idx, row in enumerate(meta_table.rows):
        for c_idx, cell in enumerate(row.cells):
            set_cell_bg(cell, "F7FAFC")
            set_cell_margins(cell, 80, 80, 120, 120)
            lbl, val = meta_data[r_idx][c_idx]
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            r_lbl = p.add_run(f"{lbl} ")
            r_lbl.bold = True
            r_lbl.font.size = Pt(9.5)
            r_lbl.font.color.rgb = COLOR_PRIMARY
            r_val = p.add_run(val)
            r_val.font.size = Pt(9.5)
            r_val.font.color.rgb = COLOR_DARK

    doc.add_paragraph()

    # Helper for Headings
    def add_h1(text):
        h = doc.add_paragraph()
        h.paragraph_format.space_before = Pt(16)
        h.paragraph_format.space_after = Pt(6)
        h.paragraph_format.keep_with_next = True
        r = h.add_run(text)
        r.bold = True
        r.font.name = "Segoe UI"
        r.font.size = Pt(16)
        r.font.color.rgb = COLOR_PRIMARY
        return h

    def add_h2(text):
        h = doc.add_paragraph()
        h.paragraph_format.space_before = Pt(12)
        h.paragraph_format.space_after = Pt(4)
        h.paragraph_format.keep_with_next = True
        r = h.add_run(text)
        r.bold = True
        r.font.name = "Segoe UI"
        r.font.size = Pt(12.5)
        r.font.color.rgb = COLOR_SECONDARY
        return h

    def add_p(text, bold_prefix=None, italic=False):
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(5)
        p.paragraph_format.line_spacing = 1.15
        if bold_prefix:
            rb = p.add_run(bold_prefix)
            rb.bold = True
            rb.font.name = "Segoe UI"
            rb.font.size = Pt(10)
            rb.font.color.rgb = COLOR_DARK
        r = p.add_run(text)
        r.italic = italic
        r.font.name = "Segoe UI"
        r.font.size = Pt(10)
        r.font.color.rgb = COLOR_DARK
        return p

    def add_bullet(text, bold_prefix=None, level=0):
        p = doc.add_paragraph(style='List Bullet')
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.line_spacing = 1.15
        if bold_prefix:
            rb = p.add_run(bold_prefix)
            rb.bold = True
            rb.font.name = "Segoe UI"
            rb.font.size = Pt(10)
            rb.font.color.rgb = COLOR_DARK
        r = p.add_run(text)
        r.font.name = "Segoe UI"
        r.font.size = Pt(10)
        r.font.color.rgb = COLOR_DARK
        return p

    # ==================== SECTION 1: EXECUTIVE SUMMARY ====================
    add_h1("1. Executive Summary")
    add_p(
        "Public municipal procurement in India handles lakhs of crores annually. In Tamil Nadu, urban local bodies "
        "(Municipal Corporations, Municipalities, and Town Panchayats) issue hundreds of tenders every month for "
        "Solid Waste Management (SWM)—ranging from Micro Composting Centres, windrow composting sheds, and shredders to "
        "waste collection vehicles and dump-yard biomining."
    )
    add_p(
        "Despite the availability of the official government e-Procurement portal (tntenders.gov.in), meaningful citizen oversight "
        "is virtually non-existent because government portals act merely as transactional bulletin boards rather than accountability engines. "
        "They do not link new tenders to historical contracts in the same ward, and once a contract's work period expires, "
        "proactive proof of completion (such as completion certificates or Measurement Book entries) is rarely published."
    )
    add_callout(
        "Municipal Tender Watchdog provides a browser-native Chrome Extension (Manifest V3) that passively detects live tenders "
        "on tntenders.gov.in, extracts structured attributes using Gemini Flash + offline regex fallback, evaluates 18-month historical "
        "records in SQLite using deterministic civic heuristics, displays 4-tier accountability badges (GREEN/ORANGE/RED/INFO), "
        "and auto-generates Section 6(1) RTI applications for one-click citizen action.",
        title="THE CORE INNOVATION"
    )

    # ==================== SECTION 2: THE PROBLEM STATEMENT ====================
    add_h1("2. Deep Problem Statement Analysis")
    add_p(
        "Under the Solid Waste Management Rules (2016) and Swachh Bharat Mission Urban (SBM-U 2.0), municipal bodies receive "
        "substantial funding for decentralized solid waste processing infrastructure. However, systemic opacity leads to three critical civic failures:"
    )

    # Problem Table
    prob_table = doc.add_table(rows=5, cols=2)
    prob_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    headers = ["Systemic Governance Problem", "Impact on Citizens & Public Funds"]
    for idx, h in enumerate(headers):
        cell = prob_table.cell(0, idx)
        set_cell_bg(cell, HEX_PRIMARY)
        set_cell_margins(cell, 100, 100, 120, 120)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        r = p.add_run(h)
        r.bold = True
        r.font.size = Pt(10)
        r.font.color.rgb = RGBColor(255, 255, 255)

    prob_rows = [
        ("1. Information Fragmentation & Transactional Silos", "Government portals index tenders individually. Connecting a new tender to past contracts in the same ward requires manual searching through tens of thousands of PDF notices."),
        ("2. Duplicate Procurement Loop (Ghost Tenders)", "Assets such as windrow sheds, perimeter fencing, or shredding machines are tendered, and within 12–18 months, an identical tender is published for the same site without explanation."),
        ("3. Completion Evidence Silence Gap", "Contracts specify 60-day or 90-day timelines, but when deadlines pass, no completion certificates or physical inspection proofs are uploaded to the public domain."),
        ("4. High Civic Friction for RTI Scrutiny", "Drafting a formal query under the Right to Information Act (2005) requires legal references, administrative knowledge, and specific tender citations that ordinary citizens do not have.")
    ]
    for r_idx, (col1, col2) in enumerate(prob_rows, start=1):
        row = prob_table.rows[r_idx]
        for c_idx, text in enumerate([col1, col2]):
            cell = row.cells[c_idx]
            set_cell_bg(cell, "FFFFFF" if r_idx % 2 == 1 else HEX_BG_LIGHT)
            set_cell_margins(cell, 80, 80, 100, 100)
            p = cell.paragraphs[0]
            r = p.add_run(text)
            r.font.size = Pt(9.5)
            r.font.color.rgb = COLOR_DARK

    doc.add_paragraph()

    # ==================== SECTION 3: THE SOLUTION & ARCHITECTURE ====================
    add_h1("3. The Solution & System Architecture")
    add_p(
        "Municipal Tender Watchdog bridges the gap between massive government procurement systems and everyday citizen oversight "
        "through a 4-stage hybrid civic-tech architecture:"
    )

    add_bullet(" Scrapes visible DOM & text directly from live tender pages on tntenders.gov.in (and offline demo environment).", bold_prefix="Stage 1 - Browser Content Detection (Chrome Manifest V3):")
    add_bullet(" Google Gemini Flash parses messy procurement text into structured parameters, backed by a 100% offline regex fallback.", bold_prefix="Stage 2 - Hybrid Dual-Engine Extraction (FastAPI):")
    add_bullet(" Enforces scope gatekeepers, 18-month historical lookback, Ward/Locality matching, Jaccard acronym similarity (>= 0.50), and strict work-order completion timing.", bold_prefix="Stage 3 - Deterministic Accountability Engine (Python):")
    add_bullet(" Renders 4-tier visual badges (GREEN, ORANGE, RED, INFO), evidence comparison cards with official URLs, and auto-generates legal RTI drafts.", bold_prefix="Stage 4 - Citizen Empowerment & RTI Action:")

    doc.add_paragraph()

    # 4-Tier Badge Table
    add_h2("The 4-Tier Accountability Signal Badges")
    badge_table = doc.add_table(rows=5, cols=3)
    badge_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    b_headers = ["Badge / Status", "Trigger Conditions", "Citizen Meaning & Action"]
    for idx, h in enumerate(b_headers):
        cell = badge_table.cell(0, idx)
        set_cell_bg(cell, HEX_PRIMARY)
        set_cell_margins(cell, 100, 100, 120, 120)
        p = cell.paragraphs[0]
        r = p.add_run(h)
        r.bold = True
        r.font.size = Pt(10)
        r.font.color.rgb = RGBColor(255, 255, 255)

    badges_data = [
        ("🟢 GREEN (Clean)", "Supported urban SWM tender; no matching repetitive procurement within 18 months; work period currently active.", "Clean procurement cycle. No accountability anomalies detected."),
        ("🟠 ORANGE (Silence Gap)", "Supported urban SWM tender; work order date + work period has expired; zero completion evidence in public dataset.", "Completion Evidence Gap. The work period has lapsed without verified completion certificates uploaded."),
        ("🔴 RED (Repetition)", "Supported urban SWM tender; identical or highly similar work (similarity >= 0.50) tendered in the same Ward/Locality within 18 months.", "Repeated Procurement Detected. Similar work was recently tendered for this location; requires verification of past execution."),
        ("ℹ️ INFO (Outside Scope)", "Tender is from an unsupported authority (e.g. Rural Village Panchayat, TNSTC) or is non-SWM civil work (borewell, depot floor).", "Outside Supported SWM Scope. Verified government record, but excluded from solid-waste accountability scoring.")
    ]
    for r_idx, (col1, col2, col3) in enumerate(badges_data, start=1):
        row = badge_table.rows[r_idx]
        for c_idx, text in enumerate([col1, col2, col3]):
            cell = row.cells[c_idx]
            bg = "FFFFFF" if r_idx % 2 == 1 else HEX_BG_LIGHT
            if c_idx == 0:
                if "GREEN" in text: bg = "F0FFF4"
                elif "ORANGE" in text: bg = "FFFAF0"
                elif "RED" in text: bg = "FFF5F5"
                elif "INFO" in text: bg = "EDF2F7"
            set_cell_bg(cell, bg)
            set_cell_margins(cell, 80, 80, 100, 100)
            p = cell.paragraphs[0]
            r = p.add_run(text)
            r.font.size = Pt(9.5)
            r.font.color.rgb = COLOR_DARK

    doc.add_paragraph()

    # ==================== SECTION 4: WHAT WE DID & WHY ====================
    add_h1("4. Technical Deep Dive: What We Did & Why")
    
    add_h2("1. Live-Portal-First Workflow (Not Just a Mock Page)")
    add_p(
        "Why: Most hackathon projects only work on localhost mockup HTML files. Municipal Tender Watchdog works "
        "directly on live Tamil Nadu Government e-Procurement pages (tntenders.gov.in). The extension passively detects "
        "live tender URLs (FrontEndTenderDetails / FrontEndViewTender) and extracts live DOM content, while preserving a "
        "built-in 4-scenario local demo page for offline evaluations."
    )

    add_h2("2. Dual-Engine Extraction (Gemini LLM + Deterministic Regex)")
    add_p(
        "Why: Civic tools must never crash in the field due to cloud quota limits, API key expirations, or intermittent internet. "
        "When an API key is present, Google Gemini Flash extracts structured parameters from unstructured text. If Gemini encounters "
        "a 503 surge or the API key is absent, the system automatically falls back to a deterministic regex parser with 100% reliability."
    )

    add_h2("3. Deterministic Decision Engine (No LLM Guesswork for Flags)")
    add_p(
        "Why: Assigning a RED or ORANGE flag has legal, administrative, and ethical consequences. An LLM might hallucinate "
        "or misidentify a ward. Our accountability logic is 100% mathematical code: token Jaccard similarity augmented with "
        "SWM domain acronyms (MCC, RRP, SWM, MT), strict 18-month timestamp math, and administrative matching (Ward -> Zone -> Locality)."
    )

    add_h2("4. Accurate Completion-Evidence Timing Logic")
    add_p(
        "Why: In government procurement, tenders can be published months before technical evaluation, financial opening, and council "
        "approval take place. Calculating completion from the publication date creates false alarms. Our system enforces: "
        "expected_completion = work_order_date + work_period_days. If work_order_date is missing, expected completion is NOT calculated "
        "and never triggers false ORANGE alarms."
    )

    add_h2("5. Zero-Accusation, Defamation-Proof AI Explanations")
    add_p(
        "Why: Civic technology must protect public interest while treating authorities fairly. Sensationalist accusations expose "
        "users to legal liabilities. Our GenAI summarization prompt enforces strict guardrails: no accusations of corruption, "
        "clear disclaimers that absence of evidence in dataset is not proof of wrongdoing, and recommendations for formal RTI verification."
    )

    add_h2("6. Evidence Provenance & One-Click Section 6(1) RTI Generator")
    add_p(
        "Why: Every evidence item retains its own verified source URL pointing directly to the official government portal. "
        "Furthermore, our RTI generator automatically formulates 7 precise legal questions under Section 6(1) of the RTI Act 2005 "
        "(demanding administrative approvals, Measurement Book entries, and completion certificates) ready to copy and submit."
    )

    # ==================== SECTION 5: FEATURE MATRIX ====================
    add_h1("5. Complete Feature Matrix (Built & Tested)")
    
    feat_table = doc.add_table(rows=16, cols=3)
    feat_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    f_headers = ["#", "Feature Area & Capability", "Status & Verification"]
    for idx, h in enumerate(f_headers):
        cell = feat_table.cell(0, idx)
        set_cell_bg(cell, HEX_PRIMARY)
        set_cell_margins(cell, 80, 80, 100, 100)
        p = cell.paragraphs[0]
        r = p.add_run(h)
        r.bold = True
        r.font.size = Pt(9.5)
        r.font.color.rgb = RGBColor(255, 255, 255)

    features = [
        ("1", "Manifest V3 Chrome Extension (Zero-tracking, responsive popup, background polling)", "✅ Built & Verified"),
        ("2", "Live Portal Tender Auto-Detection (tntenders.gov.in FrontEnd URLs)", "✅ Built & Verified"),
        ("3", "Offline Demo Environment (demo/tender.html with 4 judging scenarios)", "✅ Built & Verified"),
        ("4", "Google Gemini Flash Structured Parameter Extraction", "✅ Built & Verified"),
        ("5", "Deterministic Regex Fallback Extractor (100% offline & zero-API safe)", "✅ Built & Verified"),
        ("6", "Two-Stage Scope Gatekeeper (Urban Body Filter + SWM Topic Filter)", "✅ Built & Verified"),
        ("7", "SQLite Historical Cache (20 verified records imported from Excel dataset)", "✅ Built & Verified"),
        ("8", "Administrative Hierarchy Matching (Ward -> Zone -> Town Panchayat Locality)", "✅ Built & Verified"),
        ("9", "Repetition Engine (Token similarity + SWM acronym expansion over 18 months)", "✅ Built & Verified"),
        ("10", "Accurate Silence Timing (work_order_date + work_period_days vs reference date)", "✅ Built & Verified"),
        ("11", "4-Tier Color Badge Signals (GREEN, ORANGE, RED, INFO)", "✅ Built & Verified"),
        ("12", "Objective, Zero-Accusation Citizen Explanation Agent", "✅ Built & Verified"),
        ("13", "Evidence Audit Cards with Distinct Official Source URLs", "✅ Built & Verified"),
        ("14", "Section 6(1) RTI Application Draft Generator (7 tailored legal questions)", "✅ Built & Verified"),
        ("15", "Automated End-to-End Test Suite (test_pipeline.py & test_live_portal_pipeline.py)", "✅ 100% Pass Rate")
    ]
    for r_idx, (col1, col2, col3) in enumerate(features, start=1):
        row = feat_table.rows[r_idx]
        for c_idx, text in enumerate([col1, col2, col3]):
            cell = row.cells[c_idx]
            set_cell_bg(cell, "FFFFFF" if r_idx % 2 == 1 else HEX_BG_LIGHT)
            set_cell_margins(cell, 60, 60, 80, 80)
            p = cell.paragraphs[0]
            if c_idx == 0: p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            r = p.add_run(text)
            r.font.size = Pt(9)
            r.font.color.rgb = COLOR_DARK

    doc.add_paragraph()

    # ==================== SECTION 6: ROADMAP FOR JUDGES ====================
    add_h1("6. Next-Generation Roadmap (Bonus for Hackathon Review)")
    add_p(
        "To demonstrate scalability and forward-thinking engineering to the hackathon judges, "
        "highlight these 6 high-impact roadmap features planned for Version 2.0:"
    )

    add_bullet(" Allow local residents to take a photo of the composting shed. The app verifies GPS coordinates against tender specs.", bold_prefix="1. 📍 Crowdsourced Geo-Tagged Photo Verification:")
    add_bullet(" Graph analysis connecting bidding contractors across tenders to uncover cartel networks and rotational bidding.", bold_prefix="2. 🕸️ Contractor Collusion & Cartel Graph Analysis:")
    add_bullet(" Citizens subscribe to their Ward (e.g. Ward 24 CCMC) to receive automated 2-line alerts when contracts are issued or expire.", bold_prefix="3. 📱 Citizen WhatsApp & Telegram Ward Alerts:")
    add_bullet(" Generates citizen summaries in everyday spoken Tamil with voice playback for sanitation workers and resident welfare groups.", bold_prefix="4. 🇮🇳 Multilingual Tamil Voice & Text Summaries:")
    add_bullet(" Integrates open satellite data (ISRO Bhuvan / Sentinel) to detect physical construction progress at designated coordinates.", bold_prefix="5. 🛰️ Satellite & Drone Verification:")
    add_bullet(" Connects directly with the Tamil Nadu RTI Online Portal (rtionline.tn.gov.in) API for 1-click filing and fee payment.", bold_prefix="6. ⚡ Direct RTI e-Filing Integration:")

    doc.add_paragraph()

    # ==================== SECTION 7: PITCH SCRIPT ====================
    add_h1("7. Hackathon Live Presentation & Demo Walkthrough")
    
    add_h2("3-Minute Presentation Pitch Script")
    add_p(
        "\"Good morning/afternoon, judges. Every year, municipal bodies spend hundreds of crores of taxpayer money on Solid Waste Management—"
        "constructing composting sheds, buying collection vehicles, and setting up processing units.\n\n"
        "Yet, government procurement portals like tntenders.gov.in are static transactional bulletin boards. They do not answer 3 vital civic questions:\n"
        "1. Was this exact same work already tendered and paid for in the same ward 12 months ago?\n"
        "2. Once the 60-day contract period expired, did the contractor actually finish the work, or is there a complete silence of evidence?\n"
        "3. How can an ordinary citizen hold the administration accountable without hiring a lawyer?\n\n"
        "Today, we introduce Municipal Tender Watchdog—an AI-powered civic accountability co-pilot that lives right inside the citizen's browser.\"",
        italic=True
    )

    add_h2("Live Demo Walkthrough Steps")
    add_bullet(" Open a tender on tntenders.gov.in or demo/tender.html. Show the extension banner: 'LIVE TENDER DETECTED'.", bold_prefix="Step 1 - Live Detection:")
    add_bullet(" Click 'ANALYZE LIVE TENDER'. Gemini Flash extracts parameters, cross-referencing 18 months of historical records.", bold_prefix="Step 2 - One-Click Analysis:")
    add_bullet(" Demonstrate Scenario 1 (Active CCMC East Zone tender) -> 🟢 GREEN (Clean).", bold_prefix="Step 3 - Clean Tender:")
    add_bullet(" Demonstrate Scenario 2 (Pooluvapatti Shed, expired 60-day period) -> 🟠 ORANGE (Completion Silence Gap).", bold_prefix="Step 4 - Silence Gap:")
    add_bullet(" Demonstrate Scenario 3 (Ettimadai Windrow Pad, duplicate of 2025 contract) -> 🔴 RED (Repeated Procurement).", bold_prefix="Step 5 - Repetition Loop:")
    add_bullet(" Click 'Generate RTI'. Show the auto-generated Section 6(1) RTI draft containing 7 legally sound questions ready to copy.", bold_prefix="Step 6 - Civic Action:")

    doc.add_paragraph()

    # ==================== SECTION 8: JUDGE Q&A DEFENSE ====================
    add_h1("8. Top Hackathon Judge Q&A Defense Guide")

    qa_list = [
        ("Q1: Why did you use Gemini if your decision logic is deterministic code?",
         "Answer: Government tender pages have messy, unpredictable layouts. Gemini Flash excels at extracting unstructured text into clean JSON parameters and generating neutral citizen explanations. But assigning RED or ORANGE flags carries legal and ethical weight; that decision must remain 100% deterministic, explainable, and auditable code."),
        
        ("Q2: How do you handle CAPTCHA on the government portal (tntenders.gov.in)?",
         "Answer: We do not run automated scraping bots that bypass CAPTCHAs. Our Chrome extension operates inside the citizen's active browser session. Tender details pages do not require CAPTCHA. For historical comparisons, our backend references a curated, verified SQLite cache."),
        
        ("Q3: What if there is a legitimate reason to repeat a tender (e.g. Phase 2 expansion)?",
         "Answer: That is why our system follows a strict Zero-Accusation policy. We do not accuse anyone of corruption. We inform the citizen that an identical contract was issued recently, and provide an RTI draft so the citizen can ask the municipal administration for official clarification."),
        
        ("Q4: Why did you calculate completion strictly from the Work Order date?",
         "Answer: Tenders can sit open for months during bidding and evaluation before a contract is awarded. Calculating completion from the publish date creates false alarms. Our system only triggers an ORANGE gap if an actual Work Order was issued and its work period expired without public proof."),
        
        ("Q5: Is this system scalable across Tamil Nadu and other Indian states?",
         "Answer: Yes. Most Indian states use the National Informatics Centre (NIC) GePNIC portal engine (e.g., eproc.karnataka.gov.in, mahatenders.gov.in). Our DOM extractors and civic heuristics are directly portable to any NIC-based procurement portal across India.")
    ]

    for q, a in qa_list:
        add_p(q, bold_prefix="🔷 ")
        add_p(a)
        doc.add_paragraph()

    # Save document
    output_path = "E:\\MY-PROJECT\\Municipal-Tender-Watchdog\\HACKATHON_PROJECT_REPORT.docx"
    doc.save(output_path)
    print(f"Document successfully created at: {output_path}")

if __name__ == "__main__":
    create_document()
