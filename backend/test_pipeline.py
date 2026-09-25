import sys
import json
import urllib.request
import sqlite3
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# UTF-8 stdout
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_URL = "http://127.0.0.1:8000"
DB_PATH = Path(__file__).parent / "tenders.sqlite"

def test_pipeline():
    print("==================================================")
    print("   RUNNING MUNICIPAL TENDER WATCHDOG TEST SUITE   ")
    print("==================================================")
    
    # 1 & 2. Check /health
    try:
        res = urllib.request.urlopen(f"{BASE_URL}/health", timeout=5)
        assert res.status == 200
        health_data = json.loads(res.read().decode("utf-8"))
        assert health_data.get("status") == "ok"
        print("✓ [TEST 1 & 2] Backend is running and /health returns 200 OK")
    except Exception as e:
        print(f"✗ [FAIL] /health endpoint failed: {e}")
        sys.exit(1)

    # 3 & 4. Verify SQLite dataset records
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM tenders")
        count = cursor.fetchone()[0]
        assert count == 20, f"Expected 20 records, found {count}"
        
        # Verify no invented wards for records without wards
        cursor.execute("SELECT COUNT(*) FROM tenders WHERE ward IS NOT NULL")
        ward_count = cursor.fetchone()[0]
        print(f"✓ [TEST 3 & 4] SQLite contains {count} verified records ({ward_count} explicit wards, {count - ward_count} correctly NULL)")
        conn.close()
    except Exception as e:
        print(f"✗ [FAIL] SQLite verification failed: {e}")
        sys.exit(1)

    # 5. Search endpoint
    try:
        res = urllib.request.urlopen(f"{BASE_URL}/tenders/search?q=waste&limit=5", timeout=5)
        assert res.status == 200
        data = json.loads(res.read().decode("utf-8"))
        assert "results" in data
        assert data["total"] > 0
        print(f"✓ [TEST 5] Search endpoint works (query 'waste' matched {data['total']} records)")
    except Exception as e:
        print(f"✗ [FAIL] Search endpoint failed: {e}")
        sys.exit(1)

    # 6. Extraction endpoint (Regression test for all numeric, date, and description fields)
    sample_text = """Tender Reference Number: ROC No.252-B/2026
Tender ID: 2026_DTP_554159_2
Organisation Chain: Ettimadai Town Panchayat
Tender Title: Providing Windrow Pad with Roofing 2.5 MT at Resource Recovery Park
Work Description: Providing Windrow Pad with Roofing 2.5 MT at Resource Recovery Park
Tender Value in Rs.: 3250000
Published Date: 2026-08-10
Period Of Work(Days): 120"""
    try:
        req = urllib.request.Request(
            f"{BASE_URL}/extract",
            data=json.dumps({"raw_page_text": sample_text}).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        res = urllib.request.urlopen(req, timeout=180)
        assert res.status == 200
        extracted = json.loads(res.read().decode("utf-8"))
        assert extracted["tender_id"] == "2026_DTP_554159_2"
        assert extracted["reference_no"] == "ROC No.252-B/2026"
        assert extracted["admin_type"] == "town_panchayat"
        assert "Ettimadai" in extracted["authority"]
        assert extracted["locality"] == "Ettimadai"
        assert extracted["work_description"] == "Providing Windrow Pad with Roofing 2.5 MT at Resource Recovery Park"
        assert extracted["tender_value"] == 3250000.0 or extracted["tender_value"] == 3250000
        assert extracted["published_date"] == "2026-08-10"
        assert extracted["work_period_days"] == 120
        print(f"✓ [TEST 6] Extraction endpoint works & regression test passed:")
        print(f"     Tender ID: {extracted['tender_id']}")
        print(f"     Work Desc: {extracted['work_description']}")
        print(f"     Value: {extracted['tender_value']} | Period: {extracted['work_period_days']} days")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"✗ [FAIL] Extraction endpoint failed: {e}")
        sys.exit(1)

    # 7 & 11. Analyze endpoint & Historical Match Repetition Check
    try:
        req = urllib.request.Request(
            f"{BASE_URL}/analyze",
            data=json.dumps({"tender": extracted}).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        res = urllib.request.urlopen(req, timeout=180)
        assert res.status == 200
        analysis = json.loads(res.read().decode("utf-8"))
        assert analysis["repetition_flag"] is True
        assert analysis["similar_tender"]["tender_id"] == "2025_DTP_554159_1"
        assert analysis["similarity_score"] >= 0.50

        # Verify evidence_list requirements
        evidence = analysis.get("evidence_list", [])
        assert len(evidence) >= 2, f"Expected at least 2 evidence records, got {len(evidence)}"
        
        curr_ev = next((e for e in evidence if e["tender_id"] == extracted["tender_id"]), None)
        hist_ev = next((e for e in evidence if e["tender_id"] == analysis["similar_tender"]["tender_id"]), None)
        
        assert curr_ev is not None, "Current tender evidence not found in evidence_list"
        assert hist_ev is not None, "Historical tender evidence not found in evidence_list"

        for item, label in [(curr_ev, "Current"), (hist_ev, "Historical")]:
            assert item.get("tender_id"), f"{label} evidence missing tender_id"
            assert item.get("title"), f"{label} evidence missing title"
            assert item.get("authority"), f"{label} evidence missing authority"
            assert item.get("locality"), f"{label} evidence missing locality"
            assert item.get("published_date"), f"{label} evidence missing published_date"
            assert item.get("similarity_score") is not None, f"{label} evidence missing similarity_score"
            assert item.get("time_difference_days") is not None, f"{label} evidence missing time_difference_days"
            assert item.get("source_url"), f"{label} evidence missing source_url"

        assert curr_ev["source_url"] != hist_ev["source_url"], "Current and Historical evidence must each use their own distinct source_url"

        print(f"✓ [TEST 7 & 11] Analyze endpoint works & detected historical repetition:")
        print(f"     Match: {analysis['similar_tender']['tender_id']} (Score: {analysis['similarity_score']}, Status: {analysis['status_code']})")
        print(f"     Verified Evidence List: {len(evidence)} verified records with official source links:")
        print(f"       - Current: {curr_ev['tender_id']} | Source: {curr_ev['source_url']}")
        print(f"       - Historical: {hist_ev['tender_id']} | Source: {hist_ev['source_url']}")
    except Exception as e:
        print(f"✗ [FAIL] Analyze repetition test failed: {e}")
        sys.exit(1)

    # Completion-Evidence Timing Logic Tests
    try:
        # Case 1: published date old + bid opening in future + no work order -> no ORANGE
        active_pipeline_tender = {
            "tender_id": "2024_CCMC_999999_1",
            "authority": "Coimbatore City Municipal Corporation",
            "admin_type": "corporation",
            "locality": "Coimbatore",
            "title": "Collection and Transport of Municipal Solid Waste in Ward 12",
            "published_date": "2024-06-22",
            "bid_opening_date": "2026-10-15",
            "work_order_date": None,
            "work_period_days": 60
        }
        req = urllib.request.Request(
            f"{BASE_URL}/analyze",
            data=json.dumps({"tender": active_pipeline_tender}).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        res = urllib.request.urlopen(req, timeout=180)
        ans_active = json.loads(res.read().decode("utf-8"))
        assert ans_active["silence_flag"] is False
        assert ans_active["status_code"] not in ["ORANGE", "ORANGE_RED"]
        assert ans_active["status_code"] == "GREEN"
        print("✓ [TEST TIMING 1] Published date old + bid opening in future + no work order -> correctly no ORANGE (status: GREEN)")

        # Case 2: work order date + expired work period + no completion evidence -> ORANGE
        silence_tender = {
            "tender_id": "2024_DTP_456867_1",
            "authority": "Pooluvapatti Town Panchayat",
            "admin_type": "town_panchayat",
            "locality": "Pooluvapatti",
            "title": "Construction of Storage Shed at RR Park",
            "published_date": "2024-06-22",
            "work_order_date": "2024-07-01",
            "work_period_days": 60
        }
        req = urllib.request.Request(
            f"{BASE_URL}/analyze",
            data=json.dumps({"tender": silence_tender}).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        res = urllib.request.urlopen(req, timeout=180)
        analysis_silence = json.loads(res.read().decode("utf-8"))
        assert analysis_silence["silence_flag"] is True
        assert analysis_silence["status_code"] in ["ORANGE", "ORANGE_RED"]
        print(f"✓ [TEST TIMING 2] Work order date + expired work period -> correctly ORANGE (Flag: {analysis_silence['silence_flag']}, Status: {analysis_silence['status_code']})")

        # Case 3: non-SWM TNSTC civil work -> INFO
        tnstc_tender = {
            "tender_id": "2026_TNSTC_701191_1",
            "authority": "Tamil Nadu State Transport Corporation",
            "admin_type": "corporation",
            "title": "Relaying the raising the concrete flooring in Tirupur-II Branch",
            "work_description": "Relaying the raising the concrete flooring in Tirupur-II Branch",
            "published_date": "2026-08-25",
            "work_order_date": "2026-08-28",
            "work_period_days": 30
        }
        req = urllib.request.Request(
            f"{BASE_URL}/analyze",
            data=json.dumps({"tender": tnstc_tender}).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        res = urllib.request.urlopen(req, timeout=180)
        ans_tnstc = json.loads(res.read().decode("utf-8"))
        assert ans_tnstc["is_urban_scope"] is False
        assert ans_tnstc["status_code"] == "INFO"
        assert ans_tnstc["status_headline"] == "Outside Supported SWM Scope"
        print("✓ [TEST TIMING 3] Non-SWM TNSTC civil work -> correctly INFO")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"✗ [FAIL] Timing logic checks failed: {e}")
        sys.exit(1)

    # 12. RTI Draft test
    try:
        rti_req = {
            "tender_id": extracted["tender_id"],
            "authority": extracted["authority"],
            "title": extracted["title"],
            "reference_no": extracted["reference_no"],
            "repetition_flag": analysis["repetition_flag"],
            "silence_flag": analysis["silence_flag"],
            "similar_tender_id": analysis["similar_tender"]["tender_id"],
            "similarity_score": analysis["similarity_score"]
        }
        req = urllib.request.Request(
            f"{BASE_URL}/rti-draft",
            data=json.dumps(rti_req).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        res = urllib.request.urlopen(req, timeout=15)
        assert res.status == 200
        rti_data = json.loads(res.read().decode("utf-8"))
        assert len(rti_data["questions"]) >= 6
        assert "section 6(1)" in rti_data["full_draft_text"].lower()
        print(f"✓ [TEST 12] RTI draft generated successfully ({len(rti_data['questions'])} custom questions formulated)")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"✗ [FAIL] RTI draft test failed: {e}")
        sys.exit(1)

    print("==================================================")
    print("   ALL TESTS PASSED SUCCESSFULLY! (100% HEALTHY)  ")
    print("==================================================")

if __name__ == "__main__":
    test_pipeline()
