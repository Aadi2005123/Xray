"""
End-to-end integration test for backend endpoints.
Tests validation, error handling, /api/health, /api/model-info, /api/analyze, /api/explain, /api/report.
"""

import io
import urllib.request
import urllib.error
import json
from PIL import Image

BASE_URL = "http://127.0.0.1:8000"


def test_health():
    res = urllib.request.urlopen(f"{BASE_URL}/api/health")
    data = json.loads(res.read().decode())
    assert res.status == 200
    assert data["status"] == "ok"
    assert data["modelLoaded"] is True
    print("[PASS] GET /api/health")


def test_model_info():
    res = urllib.request.urlopen(f"{BASE_URL}/api/model-info")
    data = json.loads(res.read().decode())
    assert res.status == 200
    assert "DenseNet-121" in data["architecture"]
    assert len(data["supportedClasses"]) == 10
    print("[PASS] GET /api/model-info")


last_analysis_id = None

def test_analyze():
    global last_analysis_id
    # Create synthetic test CXR image in memory
    img = Image.new("L", (300, 300), color=128)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    raw_png = buf.getvalue()

    boundary = "----WebKitFormBoundaryTestCxr123456"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="patient_test_case.png"\r\n'
        f"Content-Type: image/png\r\n\r\n"
    ).encode("ascii") + raw_png + f"\r\n--{boundary}--\r\n".encode("ascii")

    req = urllib.request.Request(
        f"{BASE_URL}/api/analyze",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    res = urllib.request.urlopen(req)
    assert res.status == 200
    data = json.loads(res.read().decode())
    assert "analysisId" in data
    assert "predictions" in data
    assert len(data["predictions"]) == 10
    assert data["isSimulatedFallback"] is False
    assert data["topFinding"] is not None
    assert "findingInterpretation" in data
    assert "summary" in data["findingInterpretation"]
    assert len(data["findingInterpretation"]["findings"]) == 10
    last_analysis_id = data["analysisId"]
    print(f"[PASS] POST /api/analyze (Top finding: {data['topFinding']['name']}, Prob: {data['topFinding']['probability']}, isSimulated: {data['isSimulatedFallback']})")


def test_analyze_clean_sample():
    import os
    clean_sample_paths = [
        "frontend/public/samples/sample_xray_clean.png",
        "sample_xray_clean.png",
        "../frontend/public/samples/sample_xray_clean.png"
    ]
    raw_png = None
    for p in clean_sample_paths:
        if os.path.exists(p):
            with open(p, "rb") as f:
                raw_png = f.read()
            break
    
    assert raw_png is not None, "sample_xray_clean.png must exist"
    
    boundary = "----WebKitFormBoundaryTestCleanCxr"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="sample_xray_clean.png"\r\n'
        f"Content-Type: image/png\r\n\r\n"
    ).encode("ascii") + raw_png + f"\r\n--{boundary}--\r\n".encode("ascii")

    req = urllib.request.Request(
        f"{BASE_URL}/api/analyze",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    res = urllib.request.urlopen(req)
    assert res.status == 200
    data = json.loads(res.read().decode())
    assert "analysisId" in data
    assert len(data["predictions"]) == 10
    assert data["isSimulatedFallback"] is False
    print(f"[PASS] POST /api/analyze on clean sample (Top finding: {data['topFinding']['name']}, Prob: {data['topFinding']['probability']})")
    
    # Request Grad-CAM explanation for the clean sample
    top_cond = data["topFinding"]["id"]
    explain_payload = json.dumps({"analysisId": data["analysisId"], "conditionId": top_cond}).encode("utf-8")
    req_explain = urllib.request.Request(
        f"{BASE_URL}/api/explain",
        data=explain_payload,
        headers={"Content-Type": "application/json"},
    )
    res_explain = urllib.request.urlopen(req_explain)
    assert res_explain.status == 200
    explain_data = json.loads(res_explain.read().decode())
    assert explain_data["conditionId"] == top_cond
    assert explain_data["heatmapUrl"].startswith("data:image/png;base64,")
    print(f"[PASS] POST /api/explain on clean sample for condition '{top_cond}' (Heatmap len: {len(explain_data['heatmapUrl'])})")


def test_validation_error():
    # Send empty payload to trigger validation error
    boundary = "----WebKitFormBoundaryBad"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="fake.exe"\r\n'
        f"Content-Type: application/octet-stream\r\n\r\n"
        f"NOT_AN_IMAGE_CONTENT"
        f"\r\n--{boundary}--\r\n"
    ).encode("ascii")

    req = urllib.request.Request(
        f"{BASE_URL}/api/analyze",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    try:
        urllib.request.urlopen(req)
        assert False, "Should have failed with 400"
    except urllib.error.HTTPError as e:
        assert e.code == 400
        error_json = json.loads(e.read().decode())
        assert "detail" in error_json
        print(f"[PASS] Validation security rejection (400): {error_json['detail']}")


def test_explain():
    global last_analysis_id
    payload = json.dumps({"analysisId": last_analysis_id or "CXR-123", "conditionId": "cardiomegaly"}).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}/api/explain",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    res = urllib.request.urlopen(req)
    assert res.status == 200
    data = json.loads(res.read().decode())
    assert data["conditionId"] == "cardiomegaly"
    assert "heatmapUrl" in data
    assert data["heatmapUrl"].startswith("data:image/png;base64,")
    print("[PASS] POST /api/explain")

    # Test unknown condition rejection (400)
    bad_payload = json.dumps({"analysisId": last_analysis_id, "conditionId": "invalid_condition"}).encode("utf-8")
    req_bad = urllib.request.Request(
        f"{BASE_URL}/api/explain",
        data=bad_payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        urllib.request.urlopen(req_bad)
        assert False, "Should have failed with 400"
    except urllib.error.HTTPError as e:
        assert e.code == 400
        print("[PASS] POST /api/explain invalid condition rejection (400)")


def test_interpret():
    global last_analysis_id
    payload = json.dumps({"analysisId": last_analysis_id}).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}/api/interpret",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    res = urllib.request.urlopen(req)
    assert res.status == 200
    data = json.loads(res.read().decode())
    assert "summary" in data
    assert "findings" in data
    assert len(data["findings"]) == 10
    assert "oncologicDisclaimer" in data["summary"]
    print(f"[PASS] POST /api/interpret (Has detected: {data['summary']['hasDetectedPathology']}, Primary: {data['summary']['primaryFindings']})")


def test_report():
    payload = json.dumps({
        "patientPseudonym": "PT-9042",
        "studyId": "STD-8841",
        "studyDate": "2026-09-29",
        "clinicianNotes": "Screening review.",
        "analysisResult": {"test": True},
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}/api/report",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    res = urllib.request.urlopen(req)
    assert res.status == 200
    data = json.loads(res.read().decode())
    assert data["success"] is True
    print("[PASS] POST /api/report")


def test_zero_byte_rejection():
    boundary = "----WebKitFormBoundaryEmpty"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="empty.png"\r\n'
        f"Content-Type: image/png\r\n\r\n"
        f"\r\n--{boundary}--\r\n"
    ).encode("ascii")

    req = urllib.request.Request(
        f"{BASE_URL}/api/analyze",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    try:
        urllib.request.urlopen(req)
        assert False, "Should have failed with 400"
    except urllib.error.HTTPError as e:
        assert e.code == 400
        error_json = json.loads(e.read().decode())
        assert "empty" in error_json["detail"].lower()
        print(f"[PASS] Zero-byte rejection (400): {error_json['detail']}")


if __name__ == "__main__":
    test_health()
    test_model_info()
    test_analyze()
    test_analyze_clean_sample()
    test_explain()
    test_interpret()
    test_report()
    test_validation_error()
    test_zero_byte_rejection()
    print("\nALL BACKEND API TESTS PASSED!")
