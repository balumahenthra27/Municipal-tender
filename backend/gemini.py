import os
import re
import json
import logging
from typing import Optional, Dict, Any
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent / ".env")
load_dotenv(Path(__file__).parent.parent / ".env")

logger = logging.getLogger("watchdog.gemini")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

def get_gemini_client():
    if not GEMINI_API_KEY:
        return None
    try:
        from google import genai
        return genai.Client(api_key=GEMINI_API_KEY)
    except Exception as e:
        logger.warning(f"Could not initialize google-genai client: {e}")
        return None

def normalize_numeric_value(val: Any) -> Optional[float]:
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    val_str = str(val).strip().replace(",", "").replace("₹", "").replace("Rs.", "").replace("INR", "").strip()
    try:
        return float(val_str)
    except ValueError:
        return None

def normalize_integer_days(val: Any) -> Optional[int]:
    if val is None:
        return None
    if isinstance(val, int):
        return val
    if isinstance(val, float):
        return int(val)
    val_str = str(val).strip()
    m = re.search(r"\b(\d+)\b", val_str)
    if m:
        try:
            return int(m.group(1))
        except ValueError:
            return None
    return None

def heuristic_extraction(raw_text: str, hints: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Robust deterministic heuristic extractor that parses tender page text
    when Gemini API is unavailable or as a fallback.
    """
    hints = hints or {}
    data: Dict[str, Any] = {
        "tender_id": hints.get("tender_id"),
        "reference_no": hints.get("reference_no"),
        "department": hints.get("department"),
        "admin_type": hints.get("admin_type"),
        "authority": hints.get("authority"),
        "locality": hints.get("locality"),
        "zone": hints.get("zone"),
        "ward": hints.get("ward"),
        "title": hints.get("title"),
        "work_description": hints.get("work_description"),
        "tender_value": normalize_numeric_value(hints.get("tender_value")),
        "published_date": hints.get("published_date"),
        "bid_opening_date": hints.get("bid_opening_date"),
        "work_order_date": hints.get("work_order_date"),
        "work_period_days": normalize_integer_days(hints.get("work_period_days")),
        "status": hints.get("status") or "Published",
        "source_url": hints.get("source_url")
    }

    # 1. Tender ID: e.g. 2026_MAWS_649427_5 or 2024_DTP_429629_1 or 2026_TNSTC_701169_1
    if not data["tender_id"]:
        m_id = re.search(r"\b(202\d_[A-Za-z0-9]{2,8}_\d+_\d+)\b", raw_text)
        if m_id:
            data["tender_id"] = m_id.group(1)

    # 2. Reference No
    if not data["reference_no"]:
        m_ref = re.search(r"(?:Tender\s+Reference(?:\s+Number)?|Ref\s*No\.?)[\s:]+([^\n\r,]+)", raw_text, re.IGNORECASE)
        if m_ref:
            data["reference_no"] = m_ref.group(1).strip()

    # 3. Authority & Admin Type
    if not data["authority"]:
        m_org = re.search(r"(?:Organisation\s+Chain|Organization\s+Chain)[\s:]*([^\n\r]+)", raw_text, re.IGNORECASE)
        org_text = m_org.group(1).strip() if m_org else ""
        if "Coimbatore City Municipal Corporation" in raw_text or "Coimbatore Corporation" in raw_text or "CCMC" in raw_text or "CCMC" in org_text:
            data["authority"] = "Coimbatore City Municipal Corporation"
            data["admin_type"] = "corporation"
            data["department"] = data["department"] or "MAWS"
            data["locality"] = data["locality"] or "Coimbatore"
        elif "Municipality" in org_text or "Municipality" in raw_text:
            m_mun = re.search(r"([A-Za-z\s]+Municipality)", org_text or raw_text, re.IGNORECASE)
            if m_mun:
                data["authority"] = m_mun.group(1).strip()
                data["admin_type"] = "municipality"
                data["department"] = data["department"] or "MAWS"
                data["locality"] = data["locality"] or re.sub(r"\s*Municipality", "", data["authority"], flags=re.IGNORECASE).strip()
        else:
            m_tp = re.search(r"([A-Za-z\s]+Town\s+Panchayat)", org_text or raw_text, re.IGNORECASE)
            if m_tp:
                data["authority"] = m_tp.group(1).strip()
                data["admin_type"] = "town_panchayat"
                data["department"] = data["department"] or "Directorate of Town Panchayats"
                data["locality"] = data["locality"] or re.sub(r"\s*Town\s*Panchayat", "", data["authority"], flags=re.IGNORECASE).strip()
            elif org_text:
                parts = [p.strip() for p in org_text.split("||") if p.strip()]
                if parts:
                    data["authority"] = parts[-1]
                    if len(parts) > 1 and not data["department"]:
                        data["department"] = parts[0]

    # 4. Zone
    if not data["zone"]:
        m_zone = re.search(r"(North|South|East|West|Central)\s*Zone", raw_text, re.IGNORECASE)
        if m_zone:
            data["zone"] = f"{m_zone.group(1).capitalize()} Zone"

    # 5. Ward: strictly only when explicitly mentioned
    if not data["ward"]:
        m_ward = re.search(r"Ward\s*(?:No\.?|Number)?\s*([0-9A-Za-z]+)", raw_text, re.IGNORECASE)
        if m_ward:
            data["ward"] = f"Ward {m_ward.group(1).lstrip('0') or '0'}"

    # 6. Title
    if not data["title"]:
        m_title = re.search(r"(?:Tender\s+Title|Title|Name\s+of\s+Work)[\s:]+([^\n\r]+)", raw_text, re.IGNORECASE)
        if m_title:
            data["title"] = m_title.group(1).strip()
        else:
            m_work = re.search(r"(?:Work\s+Description|Description\s+of\s+Work)[\s:]+([^\n\r]+)", raw_text, re.IGNORECASE)
            if m_work:
                data["title"] = m_work.group(1).strip()
            else:
                lines = [l.strip() for l in raw_text.splitlines() if len(l.strip()) > 10 and not l.strip().startswith("http")]
                if lines:
                    data["title"] = lines[0][:150]

    # 7. Work Description
    if not data["work_description"]:
        m_desc = re.search(r"(?:Work\s+Description|Description\s+of\s+Work)[\s:]+([^\n\r]+)", raw_text, re.IGNORECASE)
        if m_desc:
            data["work_description"] = m_desc.group(1).strip()
        elif data.get("title"):
            data["work_description"] = data["title"]

    # 8. Tender Value (supports "Tender Value in Rs.: 3250000", "Tender Value in ₹: 30,10,000", "&#8377;", etc.)
    if data["tender_value"] is None:
        m_val = re.search(r"(?:Tender\s+Value|Estimated\s+Cost|ECV|Contract\s+Value)(?:\s*(?:in|amount)?\s*(?:Rs\.?|INR|₹|\(₹\)|\(Rs\.?\)|\&\#8377;|\&amp;\#8377;))?[\s:]*([\d,]+(?:\.\d+)?)", raw_text, re.IGNORECASE)
        if m_val:
            data["tender_value"] = normalize_numeric_value(m_val.group(1))

    # 9. Dates
    if not data["published_date"]:
        m_date_mon = re.search(r"(?:Published\s+Date|Publish\s+Date|Date\s+of\s+Publication)[\s:]*([0-9]{1,2}-[A-Za-z]{3}-[0-9]{4})", raw_text, re.IGNORECASE)
        if m_date_mon:
            try:
                from datetime import datetime
                dt = datetime.strptime(m_date_mon.group(1), "%d-%b-%Y")
                data["published_date"] = dt.strftime("%Y-%m-%d")
            except Exception:
                data["published_date"] = m_date_mon.group(1).strip()
        if not data["published_date"]:
            m_date = re.search(r"(?:Published\s+Date|Publish\s+Date|Date\s+of\s+Publication)[\s:]*([0-9]{4}-[0-9]{2}-[0-9]{2})", raw_text, re.IGNORECASE)
            if not m_date:
                m_date = re.search(r"(?:Published\s+Date|Publish\s+Date)[\s:]*([0-9]{2}[/-][0-9]{2}[/-][0-9]{4})", raw_text, re.IGNORECASE)
            if not m_date:
                m_date = re.search(r"\b(202[4-6]-[0-1][0-9]-[0-3][0-9])\b", raw_text)
            if m_date:
                d_str = m_date.group(1).strip()
                if re.match(r"^\d{2}[/-]\d{2}[/-]\d{4}$", d_str):
                    parts = re.split(r"[/-]", d_str)
                    data["published_date"] = f"{parts[2]}-{parts[1]}-{parts[0]}"
    # 9B. Work Order Date
    if not data.get("work_order_date"):
        m_wo = re.search(r"(?:Work\s+Order\s+Date|Date\s+of\s+Work\s+Order|Award\s+Date)[\s:]*([0-9]{4}-[0-9]{2}-[0-9]{2})", raw_text, re.IGNORECASE)
        if not m_wo:
            m_wo = re.search(r"(?:Work\s+Order\s+Date|Date\s+of\s+Work\s+Order|Award\s+Date)[\s:]*([0-9]{2}[/-][0-9]{2}[/-][0-9]{4})", raw_text, re.IGNORECASE)
        if m_wo:
            d_str = m_wo.group(1).strip()
            if re.match(r"^\d{2}[/-]\d{2}[/-]\d{4}$", d_str):
                parts = re.split(r"[/-]", d_str)
                data["work_order_date"] = f"{parts[2]}-{parts[1]}-{parts[0]}"
            else:
                data["work_order_date"] = d_str

    # 10. Work Period Days (supports "Period Of Work(Days): 120", "Period of Work: 60", "90 days", etc.)
    if data["work_period_days"] is None:
        m_period = re.search(r"(?:Period\s+Of\s+Work|Work\s+Period|Completion\s+Period|Execution\s+Period)(?:\s*\([^\)]+\))?[\s:]*(\d+)", raw_text, re.IGNORECASE)
        if m_period:
            data["work_period_days"] = normalize_integer_days(m_period.group(1))
        if data["work_period_days"] is None:
            m_days = re.search(r"(\d+)\s*(?:days|Days|Day|days\b)", raw_text)
            if m_days:
                data["work_period_days"] = normalize_integer_days(m_days.group(1))

    return data

def parse_gemini_json_response(raw_text: str) -> Optional[Dict[str, Any]]:
    """
    Safely parse Gemini response into a single dictionary.
    Handles:
    - dictionary/object JSON
    - list JSON (e.g. [{"tender_id": ...}] or [{"key": ..., "value": ...}])
    - markdown code fences (```json ... ```)
    - plain text containing JSON
    - wrapped objects ({"tender": {...}})
    Never returns a list or primitive.
    """
    if not raw_text or not str(raw_text).strip():
        return None
    
    cleaned = str(raw_text).strip()
    
    # 1. Strip markdown code fences
    if "```json" in cleaned:
        cleaned = cleaned.split("```json")[1].split("```")[0].strip()
    elif "```" in cleaned:
        cleaned = cleaned.split("```")[1].split("```")[0].strip()

    parsed = None
    # 2. Try direct json parse
    try:
        parsed = json.loads(cleaned)
    except Exception:
        # 3. Fallback: extract outer JSON object {...} or list [...] with regex
        m_obj = re.search(r"\{[\s\S]*\}", cleaned)
        if m_obj:
            try:
                parsed = json.loads(m_obj.group(0))
            except Exception:
                pass
        if parsed is None:
            m_arr = re.search(r"\[[\s\S]*\]", cleaned)
            if m_arr:
                try:
                    parsed = json.loads(m_arr.group(0))
                except Exception:
                    pass

    if parsed is None:
        return None

    # 4. Normalize to a single dictionary
    # Case A: parsed is a list
    if isinstance(parsed, list):
        if not parsed:
            return None
        # Check if list of key/value pairs
        is_kv_list = all(isinstance(x, dict) and any(k in x for k in ("key", "field", "name")) and "value" in x for x in parsed)
        if is_kv_list:
            merged = {}
            for item in parsed:
                k = item.get("key") or item.get("field") or item.get("name")
                if k:
                    merged[str(k).strip()] = item.get("value")
            parsed = merged
        # Check if list of dicts (e.g. [{"tender_id": "..."}])
        elif isinstance(parsed[0], dict):
            merged = {}
            for d in parsed:
                if isinstance(d, dict):
                    merged.update(d)
            parsed = merged
        # Check if list of 2-element pairs [["key", "val"], ...]
        elif all(isinstance(x, (list, tuple)) and len(x) == 2 for x in parsed):
            parsed = {str(k): v for k, v in parsed}
        else:
            return None

    # Case B: parsed is a dict
    if isinstance(parsed, dict):
        for wrapper_key in ("tender", "data", "result", "tender_details", "extracted"):
            if wrapper_key in parsed and isinstance(parsed[wrapper_key], dict):
                parsed = parsed[wrapper_key]
                break
        return parsed

    return None

def extract_tender_with_gemini(raw_text: str, hints: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Extract structured fields from tender text using Gemini API,
    falling back to heuristic extraction if API is unavailable.
    """
    # Compute deterministic baseline first
    deterministic = heuristic_extraction(raw_text, hints)

    client = get_gemini_client()
    if not client:
        return deterministic

    prompt = (
        "Extract structured information from this municipal tender page.\n"
        "Return a single JSON object only.\n"
        "Never invent missing fields.\n"
        "Use null when the field is not explicitly stated.\n"
        "Do not infer ward numbers.\n"
        "If the authority is a Town Panchayat, preserve the Town Panchayat/locality.\n"
        "If it is Coimbatore Corporation, identify zone/ward only when explicitly present.\n\n"
        "Expected JSON format:\n"
        "{\n"
        '  "tender_id": null,\n'
        '  "reference_no": null,\n'
        '  "department": null,\n'
        '  "admin_type": null,\n'
        '  "authority": null,\n'
        '  "locality": null,\n'
        '  "zone": null,\n'
        '  "ward": null,\n'
        '  "title": null,\n'
        '  "work_description": null,\n'
        '  "tender_value": null,\n'
        '  "published_date": null,\n'
        '  "bid_opening_date": null,\n'
        '  "work_period_days": null,\n'
        '  "status": null\n'
        "}\n\n"
        f"PAGE CONTENT:\n{raw_text[:6000]}"
    )

    # Use available Gemini Flash models for this API account
    models_to_try = ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-3.6-flash"]
    for model_name in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt
            )
            resp_text = (response.text or "").strip()
            parsed = parse_gemini_json_response(resp_text)
            
            if parsed is None or not isinstance(parsed, dict):
                logger.warning(f"Gemini model {model_name} did not return a valid dictionary, continuing fallback...")
                continue
            
            # Normalize types in parsed response
            if parsed.get("tender_value") is not None:
                parsed["tender_value"] = normalize_numeric_value(parsed["tender_value"])
            if parsed.get("work_period_days") is not None:
                parsed["work_period_days"] = normalize_integer_days(parsed["work_period_days"])
            if parsed.get("admin_type"):
                adm_lower = str(parsed["admin_type"]).lower().replace(" ", "_").replace("-", "_")
                if "panchayat" in adm_lower:
                    parsed["admin_type"] = "town_panchayat"
                elif "corporation" in adm_lower:
                    parsed["admin_type"] = "corporation"
                elif "municipality" in adm_lower:
                    parsed["admin_type"] = "municipality"
            if parsed.get("authority") and parsed.get("admin_type") == "town_panchayat":
                if "town panchayat" not in str(parsed["authority"]).lower():
                    parsed["authority"] = f"{parsed['authority'].strip()} Town Panchayat"

            # Never overwrite successfully extracted deterministic values with null/empty
            for k, v in deterministic.items():
                if (parsed.get(k) is None or str(parsed.get(k)).strip() == "") and v is not None:
                    parsed[k] = v

            logger.info("Gemini extraction: LIVE (model: %s)", model_name)
            print(f"Gemini extraction: LIVE (model: {model_name})")
            return parsed
        except Exception as e:
            safe_err = re.sub(r"(?:key|api_key|token)[=:][A-Za-z0-9_\-]+", "[REDACTED]", str(e), flags=re.IGNORECASE)
            logger.warning(f"Gemini model {model_name} extraction failed: {safe_err}")
            continue

    logger.info("Gemini extraction: FALLBACK")
    print("Gemini extraction: FALLBACK")
    return deterministic

def generate_plain_explanation_with_gemini(
    current_tender: Dict[str, Any],
    similar_tender: Optional[Dict[str, Any]],
    similarity_score: float,
    silence_flag: bool,
    repetition_flag: bool,
    evidence_list: list,
    time_diff_days: Optional[int] = None
) -> str:
    """
    Generate plain-language citizen summary using Gemini or fallback.
    Rules:
    - no accusation
    - no invented evidence
    - no claim of corruption
    - no claim of project failure unless explicit source evidence exists
    - explain uncertainty
    - mention that verification is required
    """
    # Deterministic fallback text
    fallback_parts = []
    if repetition_flag and similar_tender:
        loc = current_tender.get("ward") or current_tender.get("zone") or current_tender.get("locality") or "the same administrative area"
        fallback_parts.append(
            f"Similar procurement detected (similarity score: {similarity_score:.2f}). "
            f"A similar municipal requirement appears for {loc} within the selected 18-month period "
            f"({time_diff_days or 'recent'} days prior, Tender ID: {similar_tender.get('tender_id')}). "
            f"The available records do not establish why the requirement was repeated, and verification via official work orders is required."
        )
    if silence_flag:
        fallback_parts.append(
            "Completion evidence gap detected. The expected completion date has passed based on the recorded work period, "
            "but no completion evidence or completion certificate was found in the connected public dataset. "
            "Note that absence of evidence in the dataset does not constitute proof of non-completion."
        )
    if not fallback_parts:
        fallback_parts.append(
            "No accountability signals detected. No repeated procurement or completion evidence gaps were identified "
            "for this tender within the connected public records."
        )
    fallback_summary = " ".join(fallback_parts)

    client = get_gemini_client()
    if not client:
        return fallback_summary

    prompt = (
        "You are an objective civic accountability assistant for Municipal Tender Watchdog in Coimbatore.\n"
        "Summarize the following tender accountability analysis in 2 to 3 concise, citizen-friendly sentences.\n\n"
        "CRITICAL RULES:\n"
        "- Do NOT accuse anyone of corruption, fraud, or intentional wrongdoing.\n"
        "- Do NOT claim the project failed unless explicit evidence exists.\n"
        "- Explain that absence of completion evidence in the database is not proof of non-completion.\n"
        "- Explicitly mention that verification through official RTI or department records is recommended.\n"
        "- State facts clearly and neutrally.\n\n"
        f"CURRENT TENDER: {json.dumps(current_tender, default=str)}\n"
        f"HISTORICAL MATCH: {json.dumps(similar_tender, default=str) if similar_tender else 'None'}\n"
        f"SIMILARITY SCORE: {similarity_score}\n"
        f"TIME DIFFERENCE (DAYS): {time_diff_days}\n"
        f"REPETITION FLAG: {repetition_flag}\n"
        f"SILENCE FLAG: {silence_flag}\n"
        f"EVIDENCE: {json.dumps(evidence_list, default=str)}\n"
    )

    models_to_try = ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-3.6-flash"]
    for model_name in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt
            )
            text = (response.text or "").strip()
            if text:
                logger.info("Gemini summary: LIVE (model: %s)", model_name)
                print(f"Gemini summary: LIVE (model: {model_name})")
                return text
        except Exception as e:
            safe_err = re.sub(r"(?:key|api_key|token)[=:][A-Za-z0-9_\-]+", "[REDACTED]", str(e), flags=re.IGNORECASE)
            logger.warning(f"Gemini model {model_name} summary failed: {safe_err}")
            continue

    logger.info("Gemini summary: FALLBACK")
    print("Gemini summary: FALLBACK")
    return fallback_summary
