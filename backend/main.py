import os
import sqlite3
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from fastapi.staticfiles import StaticFiles

from models import (
    TenderRecord,
    ExtractionRequest,
    ExtractedTender,
    AnalysisRequest,
    AnalysisResponse,
    RTIDraftRequest,
    RTIDraftResponse,
    EvidenceItem
)
from database import get_db_connection, init_db
from detector import run_accountability_checks
from gemini import extract_tender_with_gemini, generate_plain_explanation_with_gemini

# Initialize Database on startup
init_db()

app = FastAPI(
    title="Municipal Tender Watchdog API",
    description="Backend service for detecting procurement repetition and completion evidence gaps in municipal tenders.",
    version="1.0.0"
)

# Enable CORS for Chrome Extension and local demo pages
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount demo folder for easy local testing & evaluation
DEMO_DIR = Path(__file__).resolve().parent.parent / "demo"
if DEMO_DIR.exists():
    app.mount("/demo", StaticFiles(directory=str(DEMO_DIR), html=True), name="demo")


@app.get("/health")
def health_check():
    """Health check endpoint specified in Section 9."""
    return {"status": "ok"}

@app.get("/tenders/search")
def search_tenders(
    q: Optional[str] = Query(None, description="Keyword search in title, reference, or description"),
    locality: Optional[str] = Query(None, description="Filter by locality"),
    zone: Optional[str] = Query(None, description="Filter by zone"),
    ward: Optional[str] = Query(None, description="Filter by ward"),
    admin_type: Optional[str] = Query(None, description="Filter by admin type (corporation/town_panchayat)"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Search historical tenders from SQLite database."""
    conn = get_db_connection()
    try:
        query_parts = []
        params: List[Any] = []

        if q:
            query_parts.append("(title LIKE ? OR reference_no LIKE ? OR work_description LIKE ? OR tender_id LIKE ? OR category LIKE ? OR subcategory LIKE ? OR locality LIKE ? OR authority LIKE ?)")
            term = f"%{q.strip()}%"
            params.extend([term] * 8)

        if locality:
            query_parts.append("locality LIKE ?")
            params.append(f"%{locality.strip()}%")

        if zone:
            query_parts.append("zone = ?")
            params.append(zone.strip())

        if ward:
            query_parts.append("ward = ?")
            params.append(ward.strip())

        if admin_type:
            query_parts.append("admin_type = ?")
            params.append(admin_type.strip().lower())

        where_clause = f"WHERE {' AND '.join(query_parts)}" if query_parts else ""

        # Total count
        count_sql = f"SELECT COUNT(*) FROM tenders {where_clause}"
        cursor = conn.cursor()
        cursor.execute(count_sql, params)
        total = cursor.fetchone()[0]

        # Results
        sql = f"SELECT * FROM tenders {where_clause} ORDER BY published_date DESC LIMIT ? OFFSET ?"
        cursor.execute(sql, params + [limit, offset])
        rows = [dict(r) for r in cursor.fetchall()]

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "results": rows
        }
    finally:
        conn.close()

@app.get("/tenders/{tender_id}")
def get_tender_by_id(tender_id: str):
    """Retrieve single tender by ID."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tenders WHERE tender_id = ?", (tender_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Tender not found")
        return dict(row)
    finally:
        conn.close()

@app.get("/evidence/{tender_id}")
def get_evidence_for_tender(tender_id: str):
    """Retrieve evidence items associated with a tender."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM evidence WHERE tender_id = ?", (tender_id,))
        rows = [dict(r) for r in cursor.fetchall()]
        return {"tender_id": tender_id, "evidence": rows}
    finally:
        conn.close()

@app.post("/extract", response_model=ExtractedTender)
def extract_tender(request: ExtractionRequest):
    """
    Stage 1: Extract structured fields from raw page text using Gemini
    with deterministic fallback.
    """
    if not request.raw_page_text or not request.raw_page_text.strip():
        raise HTTPException(status_code=400, detail="Page text is empty")

    extracted_dict = extract_tender_with_gemini(
        request.raw_page_text,
        request.structured_hints
    )
    if request.source_url and not extracted_dict.get("source_url"):
        extracted_dict["source_url"] = request.source_url

    return ExtractedTender(**extracted_dict)

@app.post("/analyze", response_model=AnalysisResponse)
def analyze_tender(request: AnalysisRequest):
    """
    Three-stage AI-assisted pipeline:
    1. Gemini/heuristic structured fields (already in request.tender)
    2. Deterministic tracking logic (Repetition & Silence checks)
    3. Gemini plain-language explanation agent
    """
    tender = request.tender
    
    # Run deterministic checks
    check_results = run_accountability_checks(tender)

    if not check_results["is_urban_scope"]:
        return AnalysisResponse(
            current_tender=tender,
            is_urban_scope=False,
            scope_note=check_results["scope_note"],
            silence_flag=False,
            repetition_flag=False,
            status_code=check_results.get("status_code", "INFO"),
            status_headline=check_results.get("status_headline", "Outside Supported SWM Scope"),
            similar_tender=None,
            similarity_score=0.0,
            time_difference_days=None,
            explanation=check_results["explanation"],
            evidence_list=[]
        )

    # Stage 3: Gemini summary agent
    current_dict = tender.model_dump()
    sim_dict = check_results["similar_tender"].model_dump() if check_results["similar_tender"] else None
    
    explanation_text = generate_plain_explanation_with_gemini(
        current_tender=current_dict,
        similar_tender=sim_dict,
        similarity_score=check_results["similarity_score"],
        silence_flag=check_results["silence_flag"],
        repetition_flag=check_results["repetition_flag"],
        evidence_list=[e.model_dump() for e in check_results["evidence_list"]],
        time_diff_days=check_results["time_difference_days"]
    )

    # Save to analysis_results table for audit trail
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO analysis_results (
            current_tender_id, silence_flag, repetition_flag,
            similar_tender_id, similarity_score, time_difference_days,
            explanation, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            tender.tender_id or "UNKNOWN",
            1 if check_results["silence_flag"] else 0,
            1 if check_results["repetition_flag"] else 0,
            check_results["similar_tender"].tender_id if check_results["similar_tender"] else None,
            check_results["similarity_score"],
            check_results["time_difference_days"],
            explanation_text,
            datetime.now().isoformat()
        ))
        conn.commit()
    finally:
        conn.close()

    return AnalysisResponse(
        current_tender=tender,
        is_urban_scope=True,
        scope_note=None,
        portal_search_note=check_results.get("portal_search_note", "Official portal search requires user interaction."),
        silence_flag=check_results["silence_flag"],
        repetition_flag=check_results["repetition_flag"],
        status_code=check_results["status_code"],
        status_headline=check_results["status_headline"],
        similar_tender=check_results["similar_tender"],
        similarity_score=check_results["similarity_score"],
        time_difference_days=check_results["time_difference_days"],
        explanation=explanation_text,
        evidence_list=check_results["evidence_list"]
    )

@app.post("/rti-draft", response_model=RTIDraftResponse)
def generate_rti_draft(request: RTIDraftRequest):
    """
    Generate an RTI draft application based on accountability flags (Section 20).
    """
    authority_name = request.authority or "Public Information Officer, Local Urban Body"
    tender_ref = f"Tender ID: {request.tender_id}" + (f" (Ref: {request.reference_no})" if request.reference_no else "")
    work_title = request.title or "Municipal Works Procurement"

    questions = [
        "Please provide an attested copy of the work order / purchase order issued for the above tender.",
        "Please provide delivery challans, stock register entries, or receipt details for the materials/services provided.",
        "Please provide a copy of the official completion / acceptance certificate or measurement book (MB) records.",
        "Please provide the detailed payment voucher copies, disbursement dates, and total amount settled to date.",
        "Please provide relevant file notings, administrative sanction, and technical sanction approvals for this procurement.",
        "Please provide copies of any inspection, quality audit, or monitoring reports submitted in relation to this work."
    ]

    # Add specific repetition question if repetition flag was triggered
    if request.repetition_flag and request.similar_tender_id:
        questions.append(
            f"Please state the specific administrative or technical reasons for issuing this tender when a similar work "
            f"(Tender ID: {request.similar_tender_id}) was previously initiated within the same administrative jurisdiction."
        )
    else:
        questions.append(
            "Please state the reasons for any subsequent retender or repeated procurement if applicable."
        )

    questions_formatted = "\n".join([f"{i+1}. {q}" for i, q in enumerate(questions)])

    full_draft = f"""APPLICATION UNDER SECTION 6(1) OF THE RIGHT TO INFORMATION ACT, 2005

To:
The Public Information Officer (PIO)
{authority_name}
Coimbatore District, Tamil Nadu

Subject: Request for information regarding municipal procurement under {tender_ref}

Sir / Madam,

Kindly provide the following certified information and records regarding the public tender described below:

Procurement Details:
- Tender ID: {request.tender_id}
- Reference No: {request.reference_no or 'N/A'}
- Work Description: {work_title}
- Public Authority: {authority_name}

Information Required:
{questions_formatted}

Application Fee:
Prescribed application fee of Rs. 10/- is attached herewith (Court fee stamp / Postal order).

Please furnish the information within the statutory period of 30 days as prescribed under Section 7(1) of the RTI Act, 2005.

Yours faithfully,
Citizen Applicant
Date: {datetime.now().strftime("%d-%m-%Y")}
Place: Coimbatore
"""

    return RTIDraftResponse(
        tender_id=request.tender_id,
        subject=f"Request for information regarding municipal procurement under {tender_ref}",
        recipient=f"The Public Information Officer, {authority_name}",
        questions=questions,
        full_draft_text=full_draft
    )
