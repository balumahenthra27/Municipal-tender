import os
import re
import sys
import sqlite3
from datetime import datetime
from pathlib import Path
import openpyxl

# Set UTF-8 encoding for console output
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Path discovery
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
DATASET_PATH = PROJECT_ROOT / "data" / "source_dataset.xlsx"
DB_PATH = BASE_DIR / "tenders.sqlite"

# Verified official metadata for indexed records
VERIFIED_OFFICIAL_OVERLAYS = {
    "2026_MAWS_649427_5": {
        "title": "Providing Fencing and Drilling Of Bore Well at Gowthampuri Park Site in Ward No.24, East Zone",
        "work_description": "Providing Fencing and Drilling Of Bore Well at Gowthampuri Park Site in Ward No.24, East Zone",
        "category": "Civil Works",
        "subcategory": "Borewell & Fencing",
        "ward": "Ward 24",
        "zone": "East Zone"
    }
}

def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def parse_iso_date(val) -> str | None:
    if val is None:
        return None
    val_str = str(val).strip()
    if not val_str:
        return None
    # If already YYYY-MM-DD
    if re.match(r"^\d{4}-\d{2}-\d{2}$", val_str):
        return val_str
    # If standard datetime or date object
    if isinstance(val, (datetime,)):
        return val.strftime("%Y-%m-%d")
    # If just 4-digit year like "2025"
    if re.match(r"^\d{4}$", val_str):
        return f"{val_str}-01-01"
    # Try parsing other common formats
    for fmt in ("%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d", "%d-%b-%Y", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(val_str, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return val_str

def parse_numeric(val) -> float | None:
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    val_str = str(val).strip().replace(",", "").replace("₹", "").replace("Rs.", "").strip()
    try:
        return float(val_str)
    except ValueError:
        return None

def extract_ward(text: str) -> str | None:
    if not text:
        return None
    m = re.search(r"Ward\s*(?:No\.?|Number)?\s*([0-9A-Za-z]+)", text, re.IGNORECASE)
    if m:
        return f"Ward {m.group(1).lstrip('0') or '0'}"
    return None

def extract_zone(text: str) -> str | None:
    if not text:
        return None
    m = re.search(r"(North|South|East|West|Central)\s*Zone", text, re.IGNORECASE)
    if m:
        return f"{m.group(1).capitalize()} Zone"
    return None

def determine_admin_type(org_name: str, tender_id: str) -> str:
    org_lower = (org_name or "").lower()
    tid_lower = (tender_id or "").lower()
    if "corporation" in org_lower or "maws" in tid_lower:
        return "corporation"
    if "town panchayat" in org_lower or "dtp" in tid_lower:
        return "town_panchayat"
    if "municipality" in org_lower:
        return "municipality"
    return "urban_local_body"

def determine_department(admin_type: str, tender_id: str) -> str:
    if "maws" in (tender_id or "").lower() or admin_type == "corporation":
        return "MAWS"
    if "dtp" in (tender_id or "").lower() or admin_type == "town_panchayat":
        return "Directorate of Town Panchayats"
    return "Municipal Administration"

def determine_locality(org_name: str, location_col: str, admin_type: str) -> str:
    if admin_type == "corporation":
        return "Coimbatore"
    if admin_type == "town_panchayat":
        # Extract e.g. "Ettimadai" from "Ettimadai Town Panchayat"
        clean = re.sub(r"\s*Town\s*Panchayat\s*", "", org_name or "", flags=re.IGNORECASE).strip()
        return clean if clean else (location_col or "Coimbatore Urban")
    return location_col or "Coimbatore"

def import_dataset():
    # Make sure DB schema is created
    from database import init_db
    init_db()

    if not DATASET_PATH.exists():
        print(f"Error: Dataset not found at {DATASET_PATH}")
        sys.exit(1)

    wb = openpyxl.load_workbook(str(DATASET_PATH), data_only=True)
    
    conn = get_db()
    cursor = conn.cursor()

    imported_count = 0
    skipped_duplicates = 0
    warnings_count = 0

    # Sheets containing tender records
    target_sheets = [s for s in wb.sheetnames if s in ["10 CBE", "10 Panchayat"]]
    if not target_sheets:
        # Fallback to all non-summary sheets
        target_sheets = [s for s in wb.sheetnames if "summary" not in s.lower()]

    for sheet_name in target_sheets:
        sheet = wb[sheet_name]
        rows = list(sheet.iter_rows(values_only=True))
        if not rows:
            continue
        
        raw_headers = [str(cell).strip() if cell is not None else "" for cell in rows[0]]
        
        # Header mapping
        header_map = {}
        for idx, h in enumerate(raw_headers):
            hl = h.lower()
            if "tender id" in hl:
                header_map["tender_id"] = idx
            elif "reference" in hl:
                header_map["reference_no"] = idx
            elif "organisation" in hl or "local body" in hl:
                header_map["authority"] = idx
            elif "title" in hl or "work" in hl:
                header_map["title"] = idx
            elif "category" in hl:
                header_map["category"] = idx
            elif "tender value" in hl:
                header_map["tender_value"] = idx
            elif "published date" in hl:
                header_map["published_date"] = idx
            elif "location" in hl or "zone" in hl:
                header_map["location"] = idx
            elif "verification" in hl:
                header_map["verification"] = idx
            elif "source" in hl or "url" in hl or "link" in hl:
                header_map["source_url"] = idx

        for row in rows[1:]:
            # Skip empty rows
            if not any(row):
                continue

            def get_col(field_key):
                if field_key in header_map and header_map[field_key] < len(row):
                    val = row[header_map[field_key]]
                    return val if val is not None else None
                return None

            raw_tender_id = get_col("tender_id")
            if not raw_tender_id:
                warnings_count += 1
                continue
            
            tender_id = str(raw_tender_id).strip()
            
            # Check duplicate
            cursor.execute("SELECT id FROM tenders WHERE tender_id = ?", (tender_id,))
            if cursor.fetchone():
                skipped_duplicates += 1
                continue

            raw_ref = get_col("reference_no")
            reference_no = str(raw_ref).strip() if raw_ref else None

            raw_authority = get_col("authority")
            authority = str(raw_authority).strip() if raw_authority else "Urban Local Body"

            raw_title = get_col("title")
            title = str(raw_title).strip() if raw_title else "Municipal Works Tender"
            work_description = title

            raw_val = get_col("tender_value")
            tender_value = parse_numeric(raw_val)

            raw_pub_date = get_col("published_date")
            published_date = parse_iso_date(raw_pub_date)

            raw_location = get_col("location")
            loc_str = str(raw_location).strip() if raw_location else ""

            raw_verif = get_col("verification")
            status_note = str(raw_verif).strip() if raw_verif else "Public record from TN e-Procurement Portal"

            raw_source = get_col("source_url")
            source_url = str(raw_source).strip() if raw_source else None

            # Admin type & Department
            admin_type = determine_admin_type(authority, tender_id)
            department = determine_department(admin_type, tender_id)

            # Zone & Ward
            # Extract zone
            zone = extract_zone(loc_str) or extract_zone(title) or extract_zone(reference_no or "")
            
            # Ward: NEVER INVENT. Only extract if explicitly in title, reference, or location
            ward = extract_ward(title) or extract_ward(loc_str) or extract_ward(reference_no or "")

            # Locality
            locality = determine_locality(authority, loc_str, admin_type)

            # Category & Subcategory
            raw_category = get_col("category")
            cat_str = str(raw_category).strip() if raw_category else "Works"
            if "/" in cat_str:
                parts = [p.strip() for p in cat_str.split("/")]
                category = parts[0]
                subcategory = parts[1]
            elif "-" in cat_str:
                parts = [p.strip() for p in cat_str.split("-")]
                category = parts[0]
                subcategory = parts[1]
            else:
                category = cat_str
                subcategory = None

            # Check if official verified title overlay exists
            if tender_id in VERIFIED_OFFICIAL_OVERLAYS:
                overlay = VERIFIED_OFFICIAL_OVERLAYS[tender_id]
                title = overlay.get("title", title)
                work_description = overlay.get("work_description", work_description)
                category = overlay.get("category", category)
                subcategory = overlay.get("subcategory", subcategory)
                if "ward" in overlay:
                    ward = overlay["ward"]
                if "zone" in overlay:
                    zone = overlay["zone"]



            # Check if any completion certificate or note exists in verification
            status = "Published"
            bid_opening_date = None
            work_order_date = None
            work_period_days = None
            expected_completion_date = None

            cursor.execute("""
            INSERT INTO tenders (
                tender_id, reference_no, department, admin_type, authority,
                locality, zone, ward, title, work_description, tender_value,
                category, subcategory, published_date, bid_opening_date,
                work_order_date, work_period_days, expected_completion_date,
                status, status_note, source_url
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                tender_id, reference_no, department, admin_type, authority,
                locality, zone, ward, title, work_description, tender_value,
                category, subcategory, published_date, bid_opening_date,
                work_order_date, work_period_days, expected_completion_date,
                status, status_note, source_url
            ))
            
            imported_count += 1

    conn.commit()
    conn.close()

    print(f"Imported {imported_count} records")
    print(f"Skipped {skipped_duplicates} duplicates")
    print(f"Warnings: {warnings_count}")

if __name__ == "__main__":
    import_dataset()
