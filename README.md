# Municipal Tender Watchdog
### Civic Accountability AI for Coimbatore Urban Solid-Waste Procurement

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Google Gemini](https://img.shields.io/badge/Google%20Gemini-Flash-4285F4?logo=google&logoColor=white)](https://ai.google.dev/)
[![Chrome Extension](https://img.shields.io/badge/Chrome%20Extension-Manifest%20V3-4285F4?logo=google-chrome&logoColor=white)](https://developer.chrome.com/docs/extensions/mv3/intro/)
[![Database](https://img.shields.io/badge/Database-SQLite3-003B57?logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Civic Tool](https://img.shields.io/badge/Compliance-RTI%20Act%202005%20Sec%206(1)-orange)](#-one-click-rti-draft-generator)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> **Civic-Tech & Gov-Tech Hackathon Project**  
> An automated civic accountability tool designed to detect repeated procurement cycles and completion evidence gaps in municipal solid-waste management (SWM) tenders across urban local bodies in Coimbatore, Tamil Nadu.

---

## 📑 Table of Contents
1. [Executive Summary](#-executive-summary)
2. [The Civic Problem](#-the-civic-problem)
3. [System Architecture & Workflow](#-system-architecture--workflow)
4. [Key Features](#-key-features)
5. [Deterministic Accountability Logic & Safeguards](#-deterministic-accountability-logic--safeguards)
6. [Administrative Jurisdictions & Dataset Provenance](#-administrative-jurisdictions--dataset-provenance)
7. [Repository Structure](#-repository-structure)
8. [Installation & Setup](#-installation--setup)
9. [Chrome Extension Installation](#-chrome-extension-installation)
10. [Interactive Demo Walkthrough (Judging Scenarios)](#-interactive-demo-walkthrough-judging-scenarios)
11. [REST API Documentation](#-rest-api-documentation)
12. [Ethical Guardrails & Non-Defamation Policy](#-ethical-guardrails--non-defamation-policy)
13. [Future Roadmap (V2.0)](#-future-roadmap-v20)
14. [Contributing & License](#-contributing--license)

---

## 📌 Executive Summary

Public municipal procurement in India amounts to lakhs of crores annually. In Tamil Nadu, urban local bodies (City Municipal Corporations, Municipalities, and Town Panchayats) issue hundreds of tenders every month under the **Solid Waste Management Rules (2016)** and **Swachh Bharat Mission Urban (SBM-U 2.0)**—procuring micro-composting centers (MCCs), resource recovery parks (RRPs), windrow composting pads, waste collection vehicles (LCVs / BOVs), and dump-yard biomining equipment.

Despite the existence of the official Tamil Nadu Government e-Procurement Portal ([tntenders.gov.in](https://tntenders.gov.in/)), citizens and civic volunteers face massive obstacles in conducting oversight:
1. Portals operate as transactional bulletin boards rather than accountability databases.
2. Tenders expire without public repository records of completion certificates or measurement book (MB) records.
3. Repetitive tenders for identical works in the same ward slip through unmonitored.
4. Drafting formal Right to Information (RTI) queries requires legal precision that deters civic participation.

**Municipal Tender Watchdog** solves this by providing a browser-native watchdog that extracts live tender details, matches them deterministically against an indexed historical dataset, flags potential irregularities without sensationalism, and outputs ready-to-file RTI application drafts under Section 6(1) of the RTI Act, 2005.

---

## 🔍 The Civic Problem

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       THE CIVIC ACCOUNTABILITY GAP                          │
├──────────────────────────────┬──────────────────────────────────────────────┤
│ 1. Information Fragmentation │ Portals index tenders individually; linking  │
│                              │ previous contracts in the same ward requires │
│                              │ manual search through thousands of records.  │
├──────────────────────────────┼──────────────────────────────────────────────┤
│ 2. The Duplicate Spend Loop  │ A composting shed or vehicle is tendered in  │
│    (Repeated Procurement)    │ 2024; in 2025/2026, an identical tender is   │
│                              │ issued for the same site with no audit note. │
├──────────────────────────────┼──────────────────────────────────────────────┤
│ 3. The Evidence Black Hole   │ Contracts expire (e.g. 60-90 days), but      │
│    (Unverified Completion)   │ portals offer zero proactive proof of        │
│                              │ completion or inspection.                    │
├──────────────────────────────┼──────────────────────────────────────────────┤
│ 4. Administrative Ambiguity  │ Mixing Corporation wards with Town Panchayat │
│                              │ boundaries leads to confusion and evasion.   │
├──────────────────────────────┼──────────────────────────────────────────────┤
│ 5. Citizen Friction          │ Citizens lack legal templates and exact      │
│                              │ tender citations to file formal queries.     │
└──────────────────────────────┴──────────────────────────────────────────────┘
```

---

## 🏗️ System Architecture & Workflow

The platform operates on a **hybrid three-stage AI-assisted pipeline backed by strict deterministic tracking logic**:

```
                       USER BROWSER
    Live Portal (tntenders.gov.in) OR Offline Demo (demo/tender.html)
                           │
                           ▼
              [ Chrome Extension (Manifest V3) ]
           (Collects visible text, labels & DOM metadata)
                           │
                           ▼ POST /extract
         ┌─────────────────────────────────────┐
         │     STAGE 1: DUAL EXTRACTOR         │
         │  • Primary: Google Gemini Flash     │
         │  • Fallback: Regex Deterministic    │
         │  (100% offline & zero-quota safe)   │
         └─────────────────┬───────────────────┘
                           │ Extracted JSON
                           ▼ POST /analyze
         ┌─────────────────────────────────────┐
         │ STAGE 2: DETERMINISTIC ENGINE       │
         │  1. Urban SWM Scope Gatekeeper      │
         │  2. 18-Month Historical Window      │
         │  3. Administrative Key Matching     │
         │     (Ward -> Zone -> Locality)      │
         │  4. Weighted Token Similarity       │
         │     (Dice-Sørensen + Jaccard)       │
         │  5. Strict Completion Timing Logic  │
         │     (work_order_date + days)        │
         └─────────────────┬───────────────────┘
                           │ Status Signals & Evidence List
                           ▼
         ┌─────────────────────────────────────┐
         │ STAGE 3: CITIZEN EXPLANATION AGENT  │
         │  • Objective, neutral language      │
         │  • Defamation-proof & factual       │
         │  • Deterministic template fallback  │
         └─────────────────┬───────────────────┘
                           │
                           ▼
         ┌─────────────────────────────────────┐
         │     STAGE 4: CITIZEN EMPOWERMENT    │
         │  • 4-Tier Color Status Badge        │
         │  • Side-by-Side Evidence Cards      │
         │  • One-Click Section 6(1) RTI Draft │
         └─────────────────────────────────────┘
```

---

## ✨ Key Features

- **🌐 Live-Portal-First Detection:** Works directly on active tender details pages on the official Tamil Nadu Government e-Procurement Portal (`tntenders.gov.in`) as well as local offline simulation pages.
- **⚡ Dual-Engine Structured Parsing:** Extracts 15+ procurement parameters using Google Gemini Flash, with instantaneous fallback to a resilient deterministic regex parser when offline or when no API key is provided.
- **🛡️ 100% Deterministic Accountability Flags:** No LLM guesswork in assigning violation signals. All repetition calculations and completion gap checks are strictly mathematical and rule-based.
- **🏷️ 4-Tier Visual Badge System:**
  - 🟢 **GREEN (Clean):** No repetition or completion flags found.
  - 🟠 **ORANGE (Completion Evidence Gap):** Work period elapsed with no verified completion record.
  - 🔴 **RED (Repeated Procurement):** High similarity to past contract in the same locality within 18 months.
  - ℹ️ **INFO (Outside Scope):** Non-SWM civil works (e.g. borewells, bus depots) or rural bodies.
- **📜 Verified Evidence Cards:** Provides side-by-side comparative inspection between current tender and historical match, including direct links back to official government records.
- **⚖️ One-Click Legal RTI Draft Generator:** Generates a complete, pre-addressed application under Section 6(1) of the Right to Information Act, 2005, containing 6 to 8 legally framed questions ready to be filed with the Public Information Officer (PIO).

---

## 📐 Deterministic Accountability Logic & Safeguards

### 1. Transparent Token Similarity Engine (`backend/similarity.py`)
Procurement descriptions are normalized by substituting common municipal abbreviations:
- `LCV` $\leftrightarrow$ `Light Commercial Vehicle`
- `SWM` $\leftrightarrow$ `Solid Waste Management`
- `MCC` $\leftrightarrow$ `Micro Composting Centre`
- `RRP` $\leftrightarrow$ `Resource Recovery Park`
- `BOV` $\leftrightarrow$ `Battery Operated Vehicle`

After stopword removal, similarity between text $A$ and text $B$ is computed using a weighted combination of the Sørensen-Dice coefficient and Jaccard Index:

$$\text{Dice}(A, B) = \frac{2 \times |A \cap B|}{|A| + |B|}, \quad \text{Jaccard}(A, B) = \frac{|A \cap B|}{|A \cup B|}$$

$$\text{Similarity Score} = 0.70 \times \text{Dice}(A, B) + 0.30 \times \text{Jaccard}(A, B)$$

A repetition flag (🔴 **RED**) is triggered only if:
1. $\text{Similarity Score} \ge 0.50$ (calibrated for high precision).
2. The administrative entity matches (same Ward/Zone in CCMC, or same Town Panchayat).
3. The historical tender published date is within the preceding **18 months (~550 days)**.

### 2. Flawless Completion Timing Logic (`backend/detector.py`)
To prevent false alarms in public works:
- Expected completion is computed strictly as:
  $$\text{Expected Completion Date} = \text{Work Order Date} + \text{Work Period (Days)}$$
- If `work_order_date` is missing, the completion gap check is **not executed**.
- Publication dates, tender submission deadlines, and bid opening dates are **strictly excluded** from being treated as contract commencement dates.

### 3. Urban SWM Scope Gatekeeper
- **Supported Bodies:** Coimbatore City Municipal Corporation (CCMC), Municipalities (Pollachi, Mettupalayam, etc.), and Town Panchayats (Ettimadai, Pooluvapatti, etc.).
- **Excluded Bodies:** Rural village/block panchayats, state transport corporations (TNSTC), electricity boards (TANGEDCO), and housing boards.
- **Domain Gatekeeper:** The work description must match Solid Waste Management keywords. Non-SWM civil works are categorized as ℹ️ **INFO**.

---

## 🏛️ Administrative Jurisdictions & Dataset Provenance

The system incorporates a curated historical baseline dataset covering Coimbatore urban solid-waste procurement from approximately **September 2024 to September 2026**, derived from official public tender records on `tntenders.gov.in`.

### Jurisdictions Handled:
1. **Coimbatore City Municipal Corporation (CCMC):**
   - Department: `MAWS` (Municipal Administration and Water Supply)
   - Zones: North, East, Central, West, South
   - Wards: Recorded **only when explicitly present** in the public tender document. Never guessed or hallucinated.
2. **Town Panchayats:**
   - Department: `Directorate of Town Panchayats` (DTP)
   - Covered Localities: Ettimadai, Pooluvapatti, Kannampalayam, Chettipalayam, Kinathukadavu, Mopperipalayam, Thondamuthur, Kottur, Samathur, Narasimhanaickenpalayam.
   - Wards: Handled as `NULL` unless explicitly stated in the public reference.

---

## 📁 Repository Structure

```text
Municipal-Tender-Watchdog/
├── backend/
│   ├── main.py                      # FastAPI application & REST routing
│   ├── detector.py                  # Deterministic accountability & timing logic
│   ├── similarity.py                # Token similarity & abbreviation normalizer
│   ├── gemini.py                    # Gemini Flash extractor & civic explainer
│   ├── database.py                  # SQLite schema definitions & connection pool
│   ├── importer.py                  # Seeding script importing dataset to SQLite
│   ├── models.py                    # Pydantic schemas for requests & responses
│   ├── tenders.sqlite               # Pre-populated SQLite database (20 records)
│   ├── requirements.txt             # Python dependencies
│   ├── .env.example                 # Example environment template
│   ├── test_pipeline.py             # Automated end-to-end regression tests
│   ├── test_live_portal_pipeline.py # Live portal scraping tests
│   └── test_timing_verification.py  # Timing logic & date calculation tests
├── extension/
│   ├── manifest.json                # Chrome Extension Manifest V3 configuration
│   ├── content.js                   # In-page DOM parser & tender scraper
│   ├── popup.html                   # Extension popup interface
│   ├── popup.css                    # Modern, dark-mode civic tech UI
│   ├── popup.js                     # Popup controller & API client
│   └── icons/                       # Extension badge icons (16, 48, 128)
├── demo/
│   ├── tender.html                  # Offline interactive portal replica
│   ├── tender.css                   # Realistic styling matching NIC-GEP portal
│   └── tender.js                    # Scenario switcher & demo interactions
├── data/
│   └── source_dataset.xlsx          # Verified source records from tntenders.gov.in
├── HACKATHON_PROJECT_REPORT.md      # Comprehensive project dossier & evaluation guide
├── run_backend.bat                  # One-click Windows startup script
├── main.py                          # Root launcher script
└── README.md                        # Documentation & setup guide
```

---

## 🚀 Installation & Setup

### Prerequisites
- **Python:** Version 3.10 or higher (Tested on 3.10, 3.11, 3.12, 3.13)
- **Browser:** Google Chrome, Brave, Edge, or any Chromium-based browser
- **Git:** Installed on system

### Step 1: Clone the Repository
```bash
git clone https://github.com/Arunkumar30102006/Municipal-tender.git
cd Municipal-tender
```

### Step 2: Install Backend Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### Step 3: Configure Gemini API Key (Optional)
The system functions out-of-the-box using the built-in deterministic fallback parser even without an API key. To enable Google Gemini Flash features:
```bash
cp .env.example .env
```
Edit `backend/.env` and add your Gemini API key:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

### Step 4: Verify or Re-seed the Database
The repository comes with a pre-indexed `tenders.sqlite` database. You can re-import or verify records anytime:
```bash
python importer.py
```
*Expected output: `Imported 20 records, Skipped 0 duplicates, Warnings: 0`.*

### Step 5: Start the Backend Server
```bash
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```
*(On Windows, you can also double-click `run_backend.bat` in the root folder).*

Verify backend health in your browser:
- [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health) $\rightarrow$ `{"status": "ok"}`
- Interactive API Docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 🧩 Chrome Extension Installation

1. Open Google Chrome.
2. Navigate to `chrome://extensions/`.
3. Toggle on **Developer mode** in the top right corner.
4. Click **Load unpacked** in the top left corner.
5. Select the `extension/` folder from this repository.
6. The **Municipal Tender Watchdog** shield icon (🛡️) will appear in your extensions toolbar. Pin it for quick access.

---

## 🧪 Interactive Demo Walkthrough (Judging Scenarios)

The project includes an interactive portal replica at `demo/tender.html` (also mounted automatically at `http://localhost:8000/demo/tender.html`).

1. Open `demo/tender.html` in your browser.
2. Use the scenario switcher at the top to test the 4 distinct civic cases:
   - **Scenario 1: Normal Active Tender (CCMC East Zone, 2026)**  
     *Expected Signal:* 🟢 **No accountability signal detected**  
     *Finding:* First-time tender in Ward 24 within the 18-month window.
   - **Scenario 2: Completion Evidence Gap (Pooluvapatti Town Panchayat, 2024)**  
     *Expected Signal:* 🟠 **Completion evidence gap**  
     *Finding:* 60-day contract period has elapsed without public completion verification.
   - **Scenario 3: Repeated Procurement (Ettimadai Town Panchayat, 2026)**  
     *Expected Signal:* 🔴 **Repeated procurement detected**  
     *Finding:* High similarity (0.83) to an identical Resource Recovery Park tender published in 2025.
   - **Scenario 4: Non-SWM Civil Works (Borewell / Park Fencing)**  
     *Expected Signal:* ℹ️ **Outside Supported SWM Scope**  
     *Finding:* Correctly rejected by the urban SWM domain gatekeeper.
3. Click the extension icon and hit **[ ANALYZE LIVE TENDER ]**.
4. Inspect the **Detailed Comparison** drawer and click **[ Generate RTI ]** $\rightarrow$ **[ COPY RTI DRAFT ]**.

---

## 📡 REST API Documentation

### 1. Health Check
```http
GET /health
```
**Response (200 OK):**
```json
{
  "status": "ok"
}
```

### 2. Extract Tender Parameters
```http
POST /extract
Content-Type: application/json
```
**Request Body:**
```json
{
  "raw_page_text": "Tender ID: 2026_MAWS_649427_1 ... Coimbatore City Municipal Corporation ...",
  "structured_hints": {},
  "source_url": "https://tntenders.gov.in/nicgep/app?component=view&page=FrontEndTenderDetails"
}
```

### 3. Analyze Tender for Accountability Signals
```http
POST /analyze
Content-Type: application/json
```
**Request Body:**
```json
{
  "tender": {
    "tender_id": "2026_DTP_649500_1",
    "reference_no": "Roc.No.142/2026/A1",
    "department": "Directorate of Town Panchayats",
    "admin_type": "town_panchayat",
    "authority": "Ettimadai Town Panchayat",
    "locality": "Ettimadai",
    "title": "Renovation of Resource Recovery Park and Shed at Ettimadai TP",
    "work_description": "Renovation and shed works at Resource Recovery Park (RRP) for SWM",
    "tender_value": 450000.0,
    "published_date": "2026-02-15"
  }
}
```
**Response (200 OK):**
```json
{
  "current_tender": { ... },
  "is_urban_scope": true,
  "silence_flag": false,
  "repetition_flag": true,
  "status_code": "RED",
  "status_headline": "Repeated procurement detected",
  "similarity_score": 0.83,
  "time_difference_days": 210,
  "explanation": "This tender indicates a high similarity (83%) to a previously issued procurement for Resource Recovery Park renovation within Ettimadai Town Panchayat issued 210 days prior. Verification of previous work completion via RTI is recommended.",
  "evidence_list": [ ... ]
}
```

### 4. Generate RTI Application Draft
```http
POST /rti-draft
Content-Type: application/json
```
**Request Body:**
```json
{
  "tender_id": "2026_DTP_649500_1",
  "authority": "Executive Officer, Ettimadai Town Panchayat",
  "title": "Renovation of Resource Recovery Park",
  "repetition_flag": true,
  "similar_tender_id": "2025_DTP_589120_1"
}
```
**Response (200 OK):**
```json
{
  "tender_id": "2026_DTP_649500_1",
  "subject": "Request for information regarding municipal procurement under Tender ID: 2026_DTP_649500_1",
  "recipient": "The Public Information Officer, Executive Officer, Ettimadai Town Panchayat",
  "questions": [
    "1. Please provide an attested copy of the work order / purchase order issued for the above tender.",
    "2. Please provide delivery challans, stock register entries, or receipt details for the materials/services provided.",
    "3. Please provide a copy of the official completion / acceptance certificate or measurement book (MB) records.",
    "4. Please state the specific administrative reasons for issuing this tender when a similar work (Tender ID: 2025_DTP_589120_1) was previously initiated within the same administrative jurisdiction."
  ],
  "full_draft_text": "APPLICATION UNDER SECTION 6(1) OF THE RIGHT TO INFORMATION ACT, 2005\n\nTo:\nThe Public Information Officer (PIO)\n..."
}
```

---

## ⚖️ Ethical Guardrails & Non-Defamation Policy

1. **No Allegations of Corruption:** Municipal Tender Watchdog does not claim or imply corruption, fraud, or intentional wrongdoing. It highlights procedural patterns (unrecorded completion documents, short-interval re-tendering) that warrant public verification.
2. **Absence $\neq$ Non-Execution:** Absence of evidence in public databases is an accountability signal indicating that documentation is not publicly accessible; it is not definitive proof that work was left undone.
3. **No Fabricated Jurisdictions:** Corporation wards are extracted solely when explicitly cited in official documents. Wards are never inferred or artificially assigned to Town Panchayats.
4. **Constitutional Empowerment:** By channeling signals directly into Section 6(1) RTI applications, the tool promotes constructive civic dialogue and official departmental verification.

---

## 🔮 Future Roadmap (V2.0)

- **📍 Crowdsourced Geo-Tagged Verification:** Mobile interface enabling residents to photograph micro-composting centres and upload timestamped, GPS-verified images mapped against tender work specifications.
- **🕸️ Contractor Network Graph Analysis:** Correlating winning bidders across urban local bodies to detect bidding cartels, shared contact addresses, and single-bidder patterns.
- **🗣️ Multilingual Tamil/English NLP:** Dense vector embeddings capable of cross-lingual semantic matching between English and Tamil procurement notices.
- **🗺️ GIS Ward-Level Infrastructure Heatmap:** Interactive map of Coimbatore visualizing waste generation rates, operational micro-composting centers, and localized tender expenditure density.

---

## 👥 Contributing & License

Contributions from civic tech enthusiasts, urban governance researchers, and developers are warmly welcomed!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/CivicFeature`)
3. Commit your Changes (`git commit -m 'Add new civic verification rule'`)
4. Push to the Branch (`git push origin feature/CivicFeature`)
5. Open a Pull Request

### License
Distributed under the **MIT License**. See `LICENSE` for more information.

---

<div align="center">
  <sub>Built with ❤️ for Civic Transparency & Smart City Accountability in Tamil Nadu.</sub>
</div>
