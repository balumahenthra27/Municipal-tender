import sys
from models import ExtractedTender
from detector import compute_expected_completion, check_silence, run_accountability_checks
from database import get_db_connection

def test_timing_cases():
    conn = get_db_connection()

    print("=== CASE 1: published date old + bid opening in future + no work order ===")
    t1 = ExtractedTender(
        tender_id="2024_CCMC_999999_1",
        authority="Coimbatore City Municipal Corporation",
        admin_type="corporation",
        locality="Coimbatore",
        title="Collection and Transport of Municipal Solid Waste in Ward 12",
        published_date="2024-06-22",
        bid_opening_date="2026-10-15",
        work_order_date=None,
        work_period_days=60
    )
    exp_date1, base_field1, err1 = compute_expected_completion(t1, conn)
    silence1, reason1 = check_silence(t1, conn)
    res1 = run_accountability_checks(t1)
    print(f"Expected completion: {exp_date1}, Base field: {base_field1}")
    print(f"Silence flag: {silence1}, Reason: {reason1}")
    print(f"Status code: {res1['status_code']}")
    assert exp_date1 is None, "Expected completion must be None when work_order_date is missing"
    assert silence1 is False, "Silence flag must be False when work_order_date is missing"
    assert res1["status_code"] not in ["ORANGE", "ORANGE_RED"], "Status code must not be ORANGE"
    assert res1["status_code"] == "GREEN", "Status code must be GREEN"
    print("--> PASS: No ORANGE triggered\n")

    print("=== CASE 2: work order date + expired work period + no completion evidence ===")
    t2 = ExtractedTender(
        tender_id="2024_DTP_456867_1",
        authority="Pooluvapatti Town Panchayat",
        admin_type="town_panchayat",
        locality="Pooluvapatti",
        title="Construction of Storage Shed at RR Park",
        published_date="2024-06-22",
        work_order_date="2024-07-01",
        work_period_days=60
    )
    exp_date2, base_field2, err2 = compute_expected_completion(t2, conn)
    silence2, reason2 = check_silence(t2, conn)
    res2 = run_accountability_checks(t2)
    print(f"Expected completion: {exp_date2}, Base field: {base_field2}")
    print(f"Silence flag: {silence2}, Reason: {reason2}")
    print(f"Status code: {res2['status_code']}")
    assert exp_date2 is not None, "Expected completion must be calculated"
    assert exp_date2.strftime("%Y-%m-%d") == "2024-08-30", f"Expected completion date 2024-08-30, got {exp_date2}"
    assert silence2 is True, "Silence flag must be True"
    assert res2["status_code"] in ["ORANGE", "ORANGE_RED"], "Status code must be ORANGE"
    print("--> PASS: Correctly triggered ORANGE completion-evidence gap\n")

    print("=== CASE 3: non-SWM TNSTC civil work ===")
    t3 = ExtractedTender(
        tender_id="2026_TNSTC_701191_1",
        authority="Tamil Nadu State Transport Corporation",
        admin_type="corporation",
        title="Relaying the raising the concrete flooring in Tirupur-II Branch",
        work_description="Relaying the raising the concrete flooring in Tirupur-II Branch",
        published_date="2026-08-25",
        work_order_date="2026-08-28",
        work_period_days=30
    )
    res3 = run_accountability_checks(t3)
    print(f"Is urban scope: {res3['is_urban_scope']}")
    print(f"Status code: {res3['status_code']}")
    print(f"Headline: {res3['status_headline']}")
    assert res3["is_urban_scope"] is False, "Must be outside urban SWM scope"
    assert res3["status_code"] == "INFO", "Must be INFO"
    print("--> PASS: Correctly classified as INFO\n")

    conn.close()
    print("ALL 3 TIMING VERIFICATION CHECKS PASSED PERFECTLY!")

if __name__ == "__main__":
    test_timing_cases()
