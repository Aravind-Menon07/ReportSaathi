"""API Contract and HTTP Status Code Test Suite (13 tests).
Uses FastAPI TestClient to validate endpoints against docs/06c-api-contracts.md.
"""
import io
import unittest
from fastapi.testclient import TestClient

from backend.main import app, MAX_UPLOAD_SIZE


class TestAPIContract(unittest.TestCase):
    """API contract validation test suite."""

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    # TC-19: GET /api/health returns 200 and healthy status
    def test_tc19_health_check(self):
        resp = self.client.get("/api/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data.get("status"), "healthy")
        self.assertEqual(data.get("service"), "ReportSaathi API")

    # TC-20: POST /api/upload accepts valid PDF/PNG/JPG files under 10MB
    def test_tc20_upload_valid_file(self):
        fake_pdf = io.BytesIO(b"%PDF-1.4 test medical report content")
        resp = self.client.post(
            "/api/upload",
            files={"file": ("lab_report.pdf", fake_pdf, "application/pdf")},
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("document_id", data)
        self.assertEqual(data.get("status"), "uploaded")

    # TC-21: POST /api/upload rejects empty 0-byte file with 400 Bad Request
    def test_tc21_upload_empty_file_rejected(self):
        empty_file = io.BytesIO(b"")
        resp = self.client.post(
            "/api/upload",
            files={"file": ("empty.pdf", empty_file, "application/pdf")},
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Empty file", resp.json().get("detail", ""))

    # TC-22: POST /api/upload rejects file exceeding 10MB with 413 Payload Too Large
    def test_tc22_upload_oversized_file_rejected(self):
        oversized = io.BytesIO(b"X" * (MAX_UPLOAD_SIZE + 1024))
        resp = self.client.post(
            "/api/upload",
            files={"file": ("huge.pdf", oversized, "application/pdf")},
        )
        self.assertEqual(resp.status_code, 413)
        self.assertIn("exceeds maximum allowed size", resp.json().get("detail", ""))

    # TC-23: POST /api/upload rejects unsupported extension with 415 Unsupported Media Type
    def test_tc23_upload_unsupported_media_type(self):
        unsupported = io.BytesIO(b"binary executable")
        resp = self.client.post(
            "/api/upload",
            files={"file": ("malware.exe", unsupported, "application/octet-stream")},
        )
        self.assertEqual(resp.status_code, 415)
        self.assertIn("Unsupported media type", resp.json().get("detail", ""))

    # TC-24: POST /api/extract returns extracted biomarkers and clarity status
    def test_tc24_extract_text(self):
        payload = {
            "document_id": "test-doc-extract",
            "raw_text": "Hemoglobin 13.5 g/dL 12.0 - 15.5\nPlatelets 220000 /mcL 150000 - 450000"
        }
        resp = self.client.post("/api/extract", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data.get("status"), "ready")
        self.assertFalse(data.get("requires_verification"))
        self.assertEqual(len(data.get("biomarkers", [])), 2)

    # TC-25: POST /api/extract/{doc_id}/corrections rejects empty text with 422 Unprocessable Entity
    def test_tc25_corrections_empty_rejected(self):
        resp = self.client.post(
            "/api/extract/test-doc/corrections",
            json={"corrected_text": "   "}
        )
        self.assertEqual(resp.status_code, 422)

    # TC-26: POST /api/extract/{doc_id}/corrections succeeds with non-empty corrected text
    def test_tc26_corrections_success(self):
        payload = {"corrected_text": "Hemoglobin 14.2 g/dL 12.0 - 15.5\n"}
        resp = self.client.post(
            "/api/extract/test-doc/corrections",
            json=payload
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data.get("biomarkers", [])), 1)
        self.assertEqual(data["biomarkers"][0]["value"], 14.2)

    # TC-27: POST /api/explain includes mandatory disclaimer
    def test_tc27_explain_mandatory_disclaimer(self):
        payload = {
            "document_id": "test-doc-explain",
            "biomarkers": [
                {
                    "name": "Hemoglobin",
                    "value": 13.5,
                    "unit": "g/dL",
                    "printed_range_low": 12.0,
                    "printed_range_high": 15.5,
                    "raw_range": "12.0 - 15.5"
                }
            ],
            "language": "English",
            "reading_level": "Standard"
        }
        resp = self.client.post("/api/explain", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data.get("disclaimer"), "This explains your report. It does not replace your doctor.")
        self.assertTrue(len(data.get("biomarkers", [])) == 1)
        self.assertIn("explanation", data["biomarkers"][0])

    # TC-28: POST /api/explain rejects invalid language with 422
    def test_tc28_explain_invalid_language(self):
        payload = {
            "document_id": "test-doc-lang",
            "language": "French",
            "reading_level": "Standard"
        }
        resp = self.client.post("/api/explain", json=payload)
        self.assertEqual(resp.status_code, 422)

    # TC-29: POST /api/explain rejects invalid reading level with 422
    def test_tc29_explain_invalid_reading_level(self):
        payload = {
            "document_id": "test-doc-level",
            "language": "English",
            "reading_level": "UltraAdvanced"
        }
        resp = self.client.post("/api/explain", json=payload)
        self.assertEqual(resp.status_code, 422)

    # TC-30: POST /api/questions returns 3 to 6 non-directive doctor consultation questions
    def test_tc30_doctor_questions_generation(self):
        payload = {
            "biomarkers": [
                {"name": "Hemoglobin", "value": 9.2, "status": "needs_attention"}
            ],
            "language": "English"
        }
        resp = self.client.post("/api/questions", json=payload)
        self.assertEqual(resp.status_code, 200)
        questions = resp.json().get("doctor_questions", [])
        self.assertTrue(3 <= len(questions) <= 6)
        self.assertIn("Hemoglobin", questions[0])

    # TC-31: POST /api/feedback records rating between 1 and 5
    def test_tc31_feedback_submission(self):
        valid_resp = self.client.post("/api/feedback", json={"rating": 5, "feedback": "Very helpful!"})
        self.assertEqual(valid_resp.status_code, 200)

        invalid_resp = self.client.post("/api/feedback", json={"rating": 7})
        self.assertEqual(invalid_resp.status_code, 422)


if __name__ == "__main__":
    unittest.main()
