import re
import sqlite3
from datetime import datetime, date
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path

from models import ExtractedTender, TenderRecord, EvidenceItem, AnalysisResponse
from similarity import keyword_similarity
from database import get_db_connection

# Reference evaluation date (current project window reference: 2026-09-04)
REFERENCE_DATE = date(2026, 9, 4)

SUPPORTED_ADMIN_TYPES = {"corporation", "municipality", "town_panchayat"}
UNSUPPORTED_KEYWORDS = [
    "village panchayat",
    "block panchayat",
    "district panchayat",
    "rural development",
    "panchayat union",
    "rdpr",
    "tnstc",
    "state transport",
    "transport corporation",
    "electricity",
    "tangedco",
    "tneb",
    "police housing",
    "public works department",
    "highways"
]

SWM_KEYWORDS = [
    "solid waste",
    "solid waste management",
    "swm",
    "waste management",
    "waste-to-energy",
    "waste to energy",
    "windrow",
    "bio-mining",
    "biomining",
    "resource recovery",
    "dry waste",
    "wet waste",
    "compost",
    "composting",
    "material recovery",
    "recovery park",
    "battery operated vehicle",
    "battery-operated vehicle",
    "waste collection",
    "waste transportation",
    "waste segregation",
    "door-to-door collection",
    "municipal waste",
    "sanitation"
]

def is_urban_scope(tender: ExtractedTender) -> Tuple[bool, Optional[str]]:
    """
    Strict two-stage validation:
    Stage A: Supported urban authority (Coimbatore City Municipal Corporation, Municipality, Town Panchayat).
             Rejects rural/district bodies and unrelated state bodies (e.g. TNSTC).
             Never uses generic 'if corporation in authority' because TNSTC contains 'Corporation'.
    Stage B: SWM relevance (must contain Solid Waste Management signal).
             Rejects non-SWM civil works or unrelated nature of work.
    """
    auth_raw = f"{tender.authority or ''} {tender.department or ''} {tender.admin_type or ''} {tender.locality or ''} {tender.tender_id or ''}".lower()

    # 1. Reject explicitly unsupported entities / state corporations / rural bodies
    for kw in UNSUPPORTED_KEYWORDS:
        if kw in auth_raw:
            return False, f"This tender is outside the supported urban municipal scope ({kw})."

    admin = (tender.admin_type or "").lower().strip()
    auth = (tender.authority or "").lower()
    dept = (tender.department or "").lower()

    # Stage A: Verify urban municipal authority
    # A1. Coimbatore City Municipal Corporation (CCMC / MAWS)
    is_ccmc = (
        "coimbatore city municipal corporation" in auth
        or "coimbatore corporation" in auth
        or "ccmc" in auth
        or ("coimbatore" in auth and "corporation" in auth and "transport" not in auth)
        or (admin == "corporation" and "coimbatore" in f"{auth} {tender.locality or ''}".lower() and "transport" not in auth)
        or (admin == "corporation" and "maws" in dept)
    )

    # A2. Municipality
    is_municipality = (
        admin == "municipality"
        or "municipality" in auth
    )

    # A3. Town Panchayat
    is_town_panchayat = (
        admin == "town_panchayat"
        or "town panchayat" in auth
        or "directorate of town panchayats" in dept
    )

    if not (is_ccmc or is_municipality or is_town_panchayat):
        return False, "This tender is outside the supported urban municipal scope (unsupported authority or non-urban local body)."

    # Stage B: SWM Relevance Check
    # Verify presence of Solid Waste Management signal in title, work description, category, subcategory
    content_text = f"{tender.title or ''} {tender.work_description or ''} {getattr(tender, 'category', '') or ''} {getattr(tender, 'subcategory', '') or ''}".lower()

    has_swm_signal = False
    for kw in SWM_KEYWORDS:
        if kw == "swm":
            if re.search(r"\bswm\b", content_text):
                has_swm_signal = True
                break
        elif kw in content_text:
            has_swm_signal = True
            break

    if not has_swm_signal and re.search(r"\brr\s*parks?\b", content_text):
        has_swm_signal = True

    if not has_swm_signal:
        return False, "This is not an SWM-related municipal procurement. This tender is outside the supported urban municipal SWM scope."

    return True, None

def parse_date_str(d_str: Optional[str]) -> Optional[date]:
    if not d_str:
        return None
    d_clean = str(d_str).strip()
    # 1. ISO format: YYYY-MM-DD
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", d_clean)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            pass
    # 2. Live portal format: DD-Mon-YYYY (e.g. 04-Sep-2026 or 04-Sep-2026 02:15 PM)
    m_portal = re.search(r"(\d{1,2})-([A-Za-z]{3})-(\d{4})", d_clean)
    if m_portal:
        try:
            dt = datetime.strptime(f"{m_portal.group(1)}-{m_portal.group(2)}-{m_portal.group(3)}", "%d-%b-%Y")
            return dt.date()
        except ValueError:
            pass
    # 3. Year only
    if re.match(r"^\d{4}$", d_clean):
        return date(int(d_clean), 1, 1)
    return None

def compute_expected_completion(
    tender: ExtractedTender,
    conn: Optional[sqlite3.Connection] = None
) -> Tuple[Optional[date], Optional[str], Optional[str]]:
    """
    Calculate expected completion date based strictly on work_order_date + work_period_days.

    Timing Rules:
    1. Use work_order_date as the primary base date.
    2. Calculate: expected_completion = work_order_date + work_period_days.
    3. If work_order_date is missing, do NOT calculate expected completion.
    4. If expected completion cannot be reliably calculated, do NOT trigger the ORANGE completion-evidence-gap flag.
    5. Bid opening date, bid submission end date, tender closing date, and published date
       must NOT be treated as work start or completion dates.

    Returns:
        (expected_date, expected_date_iso, work_order_date_iso) or (None, None, None)
    """
    if not tender.work_period_days or tender.work_period_days <= 0:
        return None, None, None

    # Retrieve work_order_date from tender object
    wo_val = getattr(tender, "work_order_date", None)
    if not wo_val and isinstance(tender, dict):
        wo_val = tender.get("work_order_date")

    # If not on input tender, check historical record in connected SQLite database
    if not wo_val and conn and tender.tender_id:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT work_order_date FROM tenders WHERE tender_id = ?", (tender.tender_id,))
            row = cursor.fetchone()
            if row and row["work_order_date"]:
                wo_val = row["work_order_date"]
        except Exception:
            pass

    # Strictly require work_order_date - do NOT fallback to published_date or bid_opening_date
    if not wo_val:
        return None, None, None

    wo_date = parse_date_str(wo_val)
    if not wo_date:
        return None, None, None

    try:
        from datetime import timedelta
        expected_date = wo_date + timedelta(days=tender.work_period_days)
        return expected_date, expected_date.isoformat(), wo_date.isoformat()
    except Exception:
        return None, None, None

def check_silence(tender: ExtractedTender, conn: sqlite3.Connection) -> Tuple[bool, Optional[str]]:
    """
    Check for completion evidence gap (ORANGE).
    Accountability rule:
    - ORANGE only when work_order_date exists, expected completion date has passed,
      and completion evidence is missing from the connected public dataset.
    - If work_order_date is missing or expected completion cannot be reliably calculated,
      do NOT trigger the ORANGE completion-evidence-gap flag.
    - Bid opening date, bid submission end date, tender closing date, and published date
      must NEVER be treated as work start or completion dates.
    """
    expected_date, exp_iso, wo_iso = compute_expected_completion(tender, conn)
    if not expected_date:
        return False, None

    # Check if passed compared to reference date
    if expected_date <= REFERENCE_DATE:
        # Check evidence table for this tender
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM evidence WHERE tender_id = ?", (tender.tender_id or "",))
        ev_count = cursor.fetchone()[0]
        
        # Also check status_note in tenders table if exists
        cursor.execute("SELECT status, status_note FROM tenders WHERE tender_id = ?", (tender.tender_id or "",))
        t_row = cursor.fetchone()
        has_completion_record = False
        if t_row:
            note = f"{t_row['status'] or ''} {t_row['status_note'] or ''}".lower()
            if "completed" in note or "certificate" in note or "handover" in note:
                has_completion_record = True

        if ev_count == 0 and not has_completion_record:
            explanation = (
                f"Expected completion date ({exp_iso}) has passed based on work order date ({wo_iso}) and a "
                f"{tender.work_period_days}-day work period, but no completion evidence was found in the connected public dataset."
            )
            return True, explanation

    return False, None

def check_repetition(tender: ExtractedTender, conn: sqlite3.Connection) -> Tuple[bool, Optional[TenderRecord], float, Optional[int]]:
    """
    Check for repeated procurement within the past 18 months (~550 days).
    Respects administrative system:
    - Corporation: Prefer same ward, fallback to same zone, then corporation locality
    - Town Panchayat: Same town panchayat locality
    """
    cursor = conn.cursor()
    
    current_date = parse_date_str(tender.published_date) or REFERENCE_DATE
    current_text = f"{tender.title or ''} {tender.work_description or ''}"
    current_id = (tender.tender_id or "").strip()

    admin_type = (tender.admin_type or "").lower()
    zone = (tender.zone or "").strip()
    ward = (tender.ward or "").strip()
    locality = (tender.locality or "").strip()

    # Build query filter based on administrative model
    query_parts = ["tender_id != ?"]
    params: List[Any] = [current_id]

    if admin_type == "corporation":
        query_parts.append("admin_type = 'corporation'")
        # Prefer matching in same zone if available
        if zone:
            query_parts.append("(zone = ? OR zone IS NULL)")
            params.append(zone)
    elif admin_type in ["town_panchayat", "municipality"]:
        query_parts.append("admin_type = ?")
        params.append(admin_type)
        if locality:
            query_parts.append("locality LIKE ?")
            params.append(f"%{locality}%")

    sql = f"SELECT * FROM tenders WHERE {' AND '.join(query_parts)}"
    cursor.execute(sql, params)
    candidates = cursor.fetchall()

    best_match: Optional[TenderRecord] = None
    best_score: float = 0.0
    best_diff_days: Optional[int] = None

    for row in candidates:
        row_dict = dict(row)
        hist_date = parse_date_str(row_dict.get("published_date"))
        
        diff_days = None
        if hist_date and current_date:
            diff_days = abs((current_date - hist_date).days)
            # Filter within 18 months (~550 days)
            if diff_days > 550:
                continue
        
        hist_text = f"{row_dict.get('title') or ''} {row_dict.get('work_description') or ''} {row_dict.get('category') or ''} {row_dict.get('subcategory') or ''}"
        
        score = keyword_similarity(current_text, hist_text)

        # Ward bonus / zone alignment bonus
        if ward and row_dict.get("ward") and ward.lower() == str(row_dict.get("ward")).lower():
            score = min(1.0, score + 0.15)
        elif zone and row_dict.get("zone") and zone.lower() == str(row_dict.get("zone")).lower():
            score = min(1.0, score + 0.05)

        if score > best_score:
            best_score = score
            best_diff_days = diff_days
            best_match = TenderRecord(**row_dict)

    # Threshold for repetition flag: 0.50 keyword similarity within 18 months
    is_repeated = best_score >= 0.50 and best_match is not None
    return is_repeated, best_match, best_score, best_diff_days

def run_accountability_checks(tender: ExtractedTender) -> Dict[str, Any]:
    """Run full deterministic accountability checks."""
    valid_scope, scope_err = is_urban_scope(tender)
    if not valid_scope:
        return {
            "is_urban_scope": False,
            "scope_note": scope_err,
            "silence_flag": False,
            "repetition_flag": False,
            "status_code": "INFO",
            "status_headline": "Outside Supported SWM Scope",
            "similar_tender": None,
            "similarity_score": 0.0,
            "time_difference_days": None,
            "portal_search_note": "Official portal search requires user interaction.",
            "explanation": scope_err or "This tender is outside the supported urban municipal SWM scope.",
            "evidence_list": []
        }

    conn = get_db_connection()
    try:
        silence_flag, silence_exp = check_silence(tender, conn)
        repetition_flag, similar_tender, sim_score, diff_days = check_repetition(tender, conn)

        # Retrieve any existing evidence items from the database
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM evidence WHERE tender_id = ?", (tender.tender_id or "",))
        evidence_rows = [EvidenceItem(**dict(r)) for r in cursor.fetchall()]

        # When a historical match exists / repetition_flag is true:
        # Add current tender and matched historical tender as verifiable evidence
        if similar_tender is not None:
            # 1. Resolve source URL for current tender (distinct from historical tender)
            current_source_url = tender.source_url
            if not current_source_url:
                cursor.execute("SELECT source_url FROM tenders WHERE tender_id = ?", (tender.tender_id or "",))
                row = cursor.fetchone()
                if row and row["source_url"]:
                    current_source_url = row["source_url"]
            if not current_source_url and tender.tender_id:
                # Authentic portal link format for current tender
                current_source_url = f"https://tntenders.gov.in/nicgep/app?component=%24DirectLink&page=FrontEndTenderDetails&service=direct&session=T&sp={tender.tender_id}"
            if not current_source_url:
                current_source_url = "https://tntenders.gov.in/nicgep/app"

            current_loc = tender.locality or tender.ward or tender.zone or "Coimbatore"
            current_evidence = EvidenceItem(
                tender_id=tender.tender_id or "CURRENT_TENDER",
                title=tender.title or tender.work_description or "Current Tender Under Review",
                authority=tender.authority or "Municipal Authority",
                locality=current_loc,
                published_date=tender.published_date,
                similarity_score=1.0,
                time_difference_days=0,
                source_url=current_source_url,
                evidence_type="CURRENT_TENDER",
                evidence_text=f"Current tender under review: {tender.title or tender.work_description or tender.tender_id}"
            )

            # 2. Matched historical tender evidence
            hist_source_url = similar_tender.source_url or "https://tntenders.gov.in/nicgep/app"
            hist_loc = similar_tender.locality or similar_tender.ward or similar_tender.zone or "Coimbatore"
            matched_evidence = EvidenceItem(
                tender_id=similar_tender.tender_id,
                title=similar_tender.title or "Historical Procurement Record",
                authority=similar_tender.authority or "Municipal Authority",
                locality=hist_loc,
                published_date=similar_tender.published_date,
                similarity_score=round(float(sim_score), 2),
                time_difference_days=diff_days,
                source_url=hist_source_url,
                evidence_type="HISTORICAL_MATCH",
                evidence_text=f"Matched historical tender: {similar_tender.title} ({similar_tender.tender_id}) with {round(float(sim_score) * 100)}% similarity, published {diff_days or 'recent'} days prior."
            )

            existing_other = [
                e for e in evidence_rows
                if e.tender_id not in (tender.tender_id, similar_tender.tender_id)
            ]
            evidence_rows = [current_evidence, matched_evidence] + existing_other

        # Determine signal status
        if repetition_flag and silence_flag:
            status_code = "ORANGE_RED"
            status_headline = "Repeated Procurement & Completion Evidence Gap"
        elif repetition_flag:
            status_code = "RED"
            status_headline = "Repeated procurement detected"
        elif silence_flag:
            status_code = "ORANGE"
            status_headline = "Completion evidence gap"
        else:
            status_code = "GREEN"
            status_headline = "No accountability signal detected"

        # Deterministic plain language explanation
        explanations = []
        if repetition_flag and similar_tender:
            loc_label = tender.ward or tender.zone or tender.locality or "the same administrative area"
            explanations.append(
                f"Similar procurement detected (similarity score: {sim_score:.2f}). "
                f"A related tender ({similar_tender.tender_id}) was published in {loc_label} "
                f"within the past 18 months ({diff_days or 'recent'} days prior). "
                f"Available public records do not establish why this procurement was repeated."
            )
        if silence_flag and silence_exp:
            explanations.append(silence_exp)
        if not explanations:
            explanations.append(
                "No repetitive procurement or completion evidence gaps were identified in the connected public dataset for this administrative jurisdiction."
            )

        combined_explanation = " ".join(explanations)

        return {
            "is_urban_scope": True,
            "scope_note": None,
            "silence_flag": silence_flag,
            "repetition_flag": repetition_flag,
            "status_code": status_code,
            "status_headline": status_headline,
            "similar_tender": similar_tender,
            "similarity_score": sim_score,
            "time_difference_days": diff_days,
            "portal_search_note": "Official portal search requires user interaction.",
            "explanation": combined_explanation,
            "evidence_list": evidence_rows
        }
    finally:
        conn.close()
