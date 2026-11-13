"""Unit tests for Privacy, PHI log scrubbing, and Ephemeral Storage (9 tests).
Covers TC-25 (log scrubbing), TC-26 (on-demand wipe), and DPDP zero-retention compliance.
"""
import logging
import os
import shutil
import tempfile
import time
import unittest
from pathlib import Path

from backend.safety.privacy import (
    sanitize_log_message,
    PrivacyPreservingLogFilter,
    EphemeralStorageManager,
)


class TestPrivacyEngine(unittest.TestCase):
    """Privacy and data protection test suite."""

    # TC-32: PHI log scrubbing redacts Indian phone numbers
    def test_tc32_redact_phone_numbers(self):
        msg = "Patient contact: +91 9876543210 called regarding report."
        scrubbed = sanitize_log_message(msg)
        self.assertNotIn("9876543210", scrubbed)
        self.assertIn("[REDACTED_PHONE]", scrubbed)

    # TC-33: PHI log scrubbing redacts Aadhaar format numbers
    def test_tc33_redact_aadhaar_numbers(self):
        msg = "Patient Aadhaar: 1234 5678 9012 recorded at reception."
        scrubbed = sanitize_log_message(msg)
        self.assertNotIn("1234 5678 9012", scrubbed)
        self.assertIn("[REDACTED_ID]", scrubbed)

    # TC-34: PHI log scrubbing redacts email addresses
    def test_tc34_redact_email_addresses(self):
        msg = "Notification sent to patient.care@example.com."
        scrubbed = sanitize_log_message(msg)
        self.assertNotIn("patient.care@example.com", scrubbed)
        self.assertIn("[REDACTED_EMAIL]", scrubbed)

    # TC-35: PHI log scrubbing redacts numerical lab values with units
    def test_tc35_redact_numerical_lab_values(self):
        msg = "Processing Hemoglobin result 13.5 g/dL and Glucose 118 mg/dL."
        scrubbed = sanitize_log_message(msg)
        self.assertNotIn("13.5 g/dL", scrubbed)
        self.assertNotIn("118 mg/dL", scrubbed)
        self.assertIn("[REDACTED_LAB_VALUE]", scrubbed)

    # TC-36: PHI log scrubbing redacts known medication names
    def test_tc36_redact_medication_names(self):
        msg = "Prescription includes Metformin and Amlodipine."
        scrubbed = sanitize_log_message(msg)
        self.assertNotIn("Metformin", scrubbed)
        self.assertNotIn("Amlodipine", scrubbed)
        self.assertIn("[REDACTED_MED]", scrubbed)

    # TC-37: PrivacyPreservingLogFilter integrates with python logging stream
    def test_tc37_logging_filter_stream(self):
        logger = logging.getLogger("test_privacy_logger")
        logger.setLevel(logging.INFO)
        logger.handlers.clear()

        log_capture = []
        class TestHandler(logging.Handler):
            def emit(self, record):
                log_capture.append(record.getMessage())

        handler = TestHandler()
        handler.addFilter(PrivacyPreservingLogFilter())
        logger.addHandler(handler)

        logger.info("Patient 9876543210 has Glucose 140 mg/dL taking Paracetamol")
        self.assertEqual(len(log_capture), 1)
        logged = log_capture[0]
        self.assertNotIn("9876543210", logged)
        self.assertNotIn("140 mg/dL", logged)
        self.assertNotIn("Paracetamol", logged)

    # TC-38: EphemeralStorageManager blocks path traversal with '../'
    def test_tc38_path_traversal_defense(self):
        temp_dir = tempfile.mkdtemp()
        try:
            manager = EphemeralStorageManager(base_dir=temp_dir)
            with self.assertRaises(ValueError):
                manager.create_document_dir("../../etc/passwd")
            with self.assertRaises(ValueError):
                manager.get_document_dir("..\\..\\windows\\system32")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    # TC-39: EphemeralStorageManager blocks null bytes '\0'
    def test_tc39_null_byte_defense(self):
        temp_dir = tempfile.mkdtemp()
        try:
            manager = EphemeralStorageManager(base_dir=temp_dir)
            with self.assertRaises(ValueError):
                manager.create_document_dir("malicious_id\0extra")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    # TC-40: EphemeralStorageManager cleanup_document and cleanup_expired purge ephemeral files
    def test_tc40_ephemeral_storage_cleanup(self):
        temp_dir = tempfile.mkdtemp()
        try:
            manager = EphemeralStorageManager(base_dir=temp_dir, default_ttl_seconds=1)
            # Create a document
            doc_id = "test-doc-wipe"
            doc_path = manager.create_document_dir(doc_id)
            sample_file = doc_path / "report.pdf"
            sample_file.write_text("sample content", encoding="utf-8")
            self.assertTrue(sample_file.exists())

            # Test on-demand wipe (TC-26)
            wipe_success = manager.cleanup_document(doc_id)
            self.assertTrue(wipe_success)
            self.assertFalse(doc_path.exists())

            # Test TTL expiration purge
            expired_id = "expired-doc"
            exp_path = manager.create_document_dir(expired_id)
            # Wait for TTL to expire
            time.sleep(1.2)
            purged_count = manager.cleanup_expired(max_age_seconds=1)
            self.assertGreaterEqual(purged_count, 1)
            self.assertFalse(exp_path.exists())
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()

