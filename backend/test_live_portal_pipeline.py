import sys
import json
import urllib.request
import sqlite3
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_URL = "http://127.0.0.1:8000"

def test_live_portal_suite():
    print("==========================================================")
    print("   RUNNING LIVE-PORTAL-FIRST VERIFICATION TEST SUITE     ")
    print("==========================================================")

    # 1. Live-like tender HTML/table extraction (Simulating live NIC-GEP portal table)
    live_portal_text = """
Organisation Chain MAWS||Tirumangalam Municipality
Tender Reference Number 1831/2026/E1
Tender ID 2026_MAWS_701608_1 Withdrawal Allowed No
Title Supply of Labour contract for Maintenance of Water supply works in Tirumangalam Municipal limit Area
Work Description Supply of Labour contract for Maintenance of Water supply works in Tirumangalam Municipal limit Area
Tender Value in &#8377; 15,00,000 Product Category Miscellaneous Works
Contract Type Tender Bid Validity(Days) 90 Period Of Work(Days) 90&nbsp;
Location TIRUMANGALAM MUNICIPALITY Pincode 625706
Published Date 04-Sep-2026 02:15 PM Bid Opening Date 22-Sep-2026 03:30 PM
"""
    try:
        req = urllib.request.Request(
            f"{BASE_URL}/extract",
            data=json.dumps({
                "raw_page_text": live_portal_text,
                "source_url": "https://tntenders.gov.in/nicgep/app?component=%24DirectLink&page=Home&service=direct&session=T&sp=SeY12VsW6FbpIFgmlOw4Y2w%3D%3D"
            }).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        res = urllib.request.urlopen(req, timeout=90)
        assert res.status == 200
        extracted = json.loads(res.read().decode("utf-8"))
        assert extracted["tender_id"] == "2026_MAWS_701608_1"
        assert extracted["reference_no"] == "1831/2026/E1"
        assert extracted["admin_type"] == "municipality"
        assert "Tirumangalam" in extracted["authority"]
        assert extracted["tender_value"] == 1500000.0
        assert extracted["work_period_days"] == 90
        print("✓ [TEST 1] Live-like tender HTML extraction passed:")
        print(f"    Tender ID: {extracted['tender_id']} | Value: ₹{extracted['tender_value']:,.0f} | Period: {extracted['work_period_days']}d")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"✗ [FAIL] Live-like extraction failed: {e}")
        sys.exit(1)

    # 2. Urban Scope Classification: Urban (Corporation, Municipality, Town Panchayat) vs Rural/State Utility
    try:
        # A: Rural Block Panchayat (Outside urban scope)
        rural_req = {
            "tender": {
                "tender_id": "2026_RDPR_999999_1",
                "authority": "Harur Block Panchayat",
                "admin_type": "block_panchayat",
                "department": "Rural Development and Panchayat Raj",
                "title": "Providing New Borewell in Village",
                "published_date": "2026-09-01"
            }
        }
        req = urllib.request.Request(f"{BASE_URL}/analyze", data=json.dumps(rural_req).encode("utf-8"), headers={"Content-Type": "application/json"})
        res = urllib.request.urlopen(req, timeout=90)
        rural_ans = json.loads(res.read().decode("utf-8"))
        assert rural_ans["is_urban_scope"] is False
        assert rural_ans["status_code"] == "INFO"
        assert "rural" in rural_ans["scope_note"].lower() or "outside" in rural_ans["scope_note"].lower()
        print("✓ [TEST 2A] Rural block panchayat correctly rejected (Outside Urban Scope, Status: INFO)")

        # B: Non-SWM Municipal civil works (Correctly rejected with INFO)
        urban_mun_non_swm_req = {"tender": extracted}
        req = urllib.request.Request(f"{BASE_URL}/analyze", data=json.dumps(urban_mun_non_swm_req).encode("utf-8"), headers={"Content-Type": "application/json"})
        res = urllib.request.urlopen(req, timeout=90)
        non_swm_ans = json.loads(res.read().decode("utf-8"))
        assert non_swm_ans["is_urban_scope"] is False
        assert non_swm_ans["status_code"] == "INFO"
        print("✓ [TEST 2B] Non-SWM municipal civil works correctly classified as INFO (Outside SWM Scope)")

        # C: Urban Municipality SWM procurement (Inside scope)
        swm_mun_req = {
            "tender": {
                "tender_id": "2026_MAWS_SWM_01",
                "authority": "Tirumangalam Municipality",
                "admin_type": "municipality",
                "locality": "Tirumangalam",
                "title": "Solid Waste Management Door-to-Door Collection and Transportation",
                "published_date": "2026-09-01"
            }
        }
        req = urllib.request.Request(f"{BASE_URL}/analyze", data=json.dumps(swm_mun_req).encode("utf-8"), headers={"Content-Type": "application/json"})
        res = urllib.request.urlopen(req, timeout=90)
        swm_ans = json.loads(res.read().decode("utf-8"))
        assert swm_ans["is_urban_scope"] is True
        print("✓ [TEST 2C] Urban municipality SWM tender correctly accepted (Inside Urban SWM Scope)")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"✗ [FAIL] Urban scope classification failed: {e}")
        sys.exit(1)

    # 3. Corporation Ward Matching: Explicit Ward vs Zone fallback
    try:
        # Explicit Ward match (e.g. Ward 24) with SWM relevance
        cbe_ward_tender = {
            "tender": {
                "tender_id": "2026_MAWS_TEST_WARD24",
                "authority": "Coimbatore City Municipal Corporation",
                "admin_type": "corporation",
                "locality": "Coimbatore",
                "zone": "East Zone",
                "ward": "Ward 24",
                "title": "Providing Fencing and Borewell at SWM Resource Recovery Park in Ward 24",
                "work_description": "Providing Fencing and Borewell at SWM Resource Recovery Gowthampuri Park in Ward 24",
                "published_date": "2026-09-03"
            }
        }
        req = urllib.request.Request(f"{BASE_URL}/analyze", data=json.dumps(cbe_ward_tender).encode("utf-8"), headers={"Content-Type": "application/json"})
        res = urllib.request.urlopen(req, timeout=90)
        ward_ans = json.loads(res.read().decode("utf-8"))
        assert ward_ans["repetition_flag"] is True
        assert ward_ans["similar_tender"]["tender_id"] == "2026_MAWS_649427_5"
        print(f"✓ [TEST 3] Corporation explicit ward matching succeeded (Matched Ward 24 historical tender {ward_ans['similar_tender']['tender_id']})")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"✗ [FAIL] Corporation ward matching failed: {e}")
        sys.exit(1)

    # 4. Town Panchayat Locality Matching: Matching by Town Panchayat/locality without forcing ward
    try:
        tp_tender = {
            "tender": {
                "tender_id": "2026_DTP_554159_2",
                "authority": "Ettimadai Town Panchayat",
                "admin_type": "town_panchayat",
                "locality": "Ettimadai",
                "ward": None,  # No ward forced
                "title": "Providing Windrow Pad with Roofing 2.5 MT at Resource Recovery Park",
                "published_date": "2026-08-10",
                "work_period_days": 120
            }
        }
        req = urllib.request.Request(f"{BASE_URL}/analyze", data=json.dumps(tp_tender).encode("utf-8"), headers={"Content-Type": "application/json"})
        res = urllib.request.urlopen(req, timeout=90)
        tp_ans = json.loads(res.read().decode("utf-8"))
        assert tp_ans["repetition_flag"] is True
        assert tp_ans["similar_tender"]["tender_id"] == "2025_DTP_554159_1"
        assert tp_ans["similar_tender"]["locality"] == "Ettimadai"
        print(f"✓ [TEST 4] Town Panchayat locality matching succeeded without forcing ward (Matched {tp_ans['similar_tender']['tender_id']})")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"✗ [FAIL] Town Panchayat locality matching failed: {e}")
        sys.exit(1)

    # 5. Evidence List & Portal Interaction Notice
    try:
        assert len(tp_ans["evidence_list"]) >= 2
        curr_ev = next((e for e in tp_ans["evidence_list"] if e["tender_id"] == "2026_DTP_554159_2"), None)
        hist_ev = next((e for e in tp_ans["evidence_list"] if e["tender_id"] == "2025_DTP_554159_1"), None)
        assert curr_ev and hist_ev, "Expected both current and historical evidence records"
        assert curr_ev["source_url"] != hist_ev["source_url"], "Current and Historical evidence must each use their own distinct source_url"
        for ev in tp_ans["evidence_list"]:
            assert ev["tender_id"]
            assert ev["title"]
            assert ev["authority"]
            assert ev["source_url"]
        assert tp_ans.get("portal_search_note") == "Official portal search requires user interaction."
        print(f"✓ [TEST 5] Evidence list contains {len(tp_ans['evidence_list'])} verified items with distinct official source URLs")
        print(f"    Portal Search Note: \"{tp_ans['portal_search_note']}\"")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"✗ [FAIL] Evidence list / Portal notice check failed: {e}")
        sys.exit(1)

    # 6. RTI Draft Generation (Draft Only - Never Automatically Submitted)
    try:
        rti_req = {
            "tender_id": tp_tender["tender"]["tender_id"],
            "authority": tp_tender["tender"]["authority"],
            "title": tp_tender["tender"]["title"],
            "repetition_flag": tp_ans["repetition_flag"],
            "silence_flag": tp_ans["silence_flag"],
            "similar_tender_id": tp_ans["similar_tender"]["tender_id"],
            "similarity_score": tp_ans["similarity_score"]
        }
        req = urllib.request.Request(f"{BASE_URL}/rti-draft", data=json.dumps(rti_req).encode("utf-8"), headers={"Content-Type": "application/json"})
        res = urllib.request.urlopen(req, timeout=15)
        rti_res = json.loads(res.read().decode("utf-8"))
        assert len(rti_res["questions"]) >= 5
        assert "right to information" in rti_res["full_draft_text"].lower() or "rti" in rti_res["full_draft_text"].lower()
        print(f"✓ [TEST 6] RTI draft generated cleanly ({len(rti_res['questions'])} customized accountability questions)")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"✗ [FAIL] RTI draft failed: {e}")
        sys.exit(1)

    # 7. No API key fallback test: heuristic extraction works deterministically without Gemini API
    try:
        from gemini import heuristic_extraction
        h_res = heuristic_extraction(live_portal_text)
        assert h_res["tender_id"] == "2026_MAWS_701608_1"
        assert h_res["admin_type"] == "municipality"
        assert h_res["tender_value"] == 1500000.0
        assert h_res["work_period_days"] == 90
        print("✓ [TEST 7] Heuristic extraction functions 100% deterministically when API key is unavailable")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"✗ [FAIL] Fallback test failed: {e}")
        sys.exit(1)

    print("==========================================================")
    print("   ALL 7 LIVE-PORTAL-FIRST TESTS PASSED SUCCESSFULLY!    ")
    print("==========================================================")

if __name__ == "__main__":
    test_live_portal_suite()
