"""Privacy, Log Scrubbing, and Ephemeral Storage Management.
Enforces zero-retention compliance under DPDP Act 2023.
"""
import logging
import os
import re
import shutil
import time
from pathlib import Path
from typing import Optional


# Patterns for Personally Identifiable Information (PII) and Protected Health Information (PHI)
PHONE_PATTERN = re.compile(r"(\+91[\-\s]?)?[6-9]\d{9}\b")
AADHAAR_PATTERN = re.compile(r"\b\d{4}[\s\-]\d{4}[\s\-]\d{4}\b")
EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b")
NUMERICAL_LAB_PATTERN = re.compile(r"\b\d+(\.\d+)?\s*(g/dL|mg/dL|mmol/L|mEq/L|/mcL|/uL|cells/mcL|%)\b", re.IGNORECASE)
MEDICATION_NAME_PATTERN = re.compile(r"\b(Metformin|Amlodipine|Atorvastatin|Paracetamol|Amoxicillin|Pantoprazole|Azithromycin|Losartan|Insulin|Ferrous\s+Sulphate)\b", re.IGNORECASE)


def sanitize_log_message(msg: str) -> str:
    """Scrubs PII/PHI (phone numbers, emails, numerical lab values, drug names) from log strings."""
    if not isinstance(msg, str):
        msg = str(msg)

    scrubbed = PHONE_PATTERN.sub("[REDACTED_PHONE]", msg)
    scrubbed = AADHAAR_PATTERN.sub("[REDACTED_ID]", scrubbed)
    scrubbed = EMAIL_PATTERN.sub("[REDACTED_EMAIL]", scrubbed)
    scrubbed = NUMERICAL_LAB_PATTERN.sub("[REDACTED_LAB_VALUE]", scrubbed)
    scrubbed = MEDICATION_NAME_PATTERN.sub("[REDACTED_MED]", scrubbed)
    return scrubbed


class PrivacyPreservingLogFilter(logging.Filter):
    """Logging filter that scrubs sensitive clinical metrics and patient identifiers from log streams."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = sanitize_log_message(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {k: sanitize_log_message(str(v)) for k, v in record.args.items()}
            elif isinstance(record.args, tuple):
                record.args = tuple(sanitize_log_message(str(a)) for a in record.args)
        return True


class EphemeralStorageManager:
    """Manages ephemeral temporary upload directories with path traversal guards and TTL wipes."""

    def __init__(self, base_dir: Optional[str] = None, default_ttl_seconds: int = 900):
        if base_dir:
            self.base_dir = Path(base_dir).resolve()
        else:
            self.base_dir = (Path(__file__).parent.parent / "temp_uploads").resolve()
        self.default_ttl = default_ttl_seconds
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _validate_safe_id(self, document_id: str) -> Path:
        """Validates that document_id contains no path traversal (../, null bytes, absolute paths)."""
        if not document_id or "\0" in document_id:
            raise ValueError("Invalid document ID: Null byte detected or empty ID")

        # Reject path separators and parent directory traversal
        if ".." in document_id or "/" in document_id or "\\" in document_id:
            raise ValueError("Path traversal attempt detected in document ID")

        target_path = (self.base_dir / document_id).resolve()
        try:
            target_path.relative_to(self.base_dir)
        except ValueError:
            raise ValueError("Target path escapes base storage directory")

        return target_path

    def create_document_dir(self, document_id: str) -> Path:
        """Creates a dedicated ephemeral directory for a document."""
        doc_dir = self._validate_safe_id(document_id)
        doc_dir.mkdir(parents=True, exist_ok=True)
        # Touch a timestamp file for TTL tracking
        meta_file = doc_dir / ".created_at"
        meta_file.write_text(str(time.time()), encoding="utf-8")
        return doc_dir

    def get_document_dir(self, document_id: str) -> Optional[Path]:
        """Returns the document directory if it exists safely."""
        doc_dir = self._validate_safe_id(document_id)
        if doc_dir.exists() and doc_dir.is_dir():
            return doc_dir
        return None

    def cleanup_document(self, document_id: str) -> bool:
        """On-demand immediate wipe of uploaded files and extracted text."""
        try:
            doc_dir = self._validate_safe_id(document_id)
            if doc_dir.exists() and doc_dir.is_dir():
                shutil.rmtree(doc_dir, ignore_errors=True)
                return True
        except ValueError:
            return False
        return False

    def cleanup_expired(self, max_age_seconds: Optional[int] = None) -> int:
        """Purges any temporary documents exceeding TTL."""
        ttl = max_age_seconds if max_age_seconds is not None else self.default_ttl
        now = time.time()
        purged = 0

        for item in self.base_dir.iterdir():
            if item.is_dir():
                meta_file = item / ".created_at"
                created_at = None
                if meta_file.exists():
                    try:
                        created_at = float(meta_file.read_text(encoding="utf-8").strip())
                    except Exception:
                        created_at = None

                if created_at is None:
                    # Fallback to directory mtime
                    created_at = item.stat().st_mtime

                if (now - created_at) > ttl:
                    shutil.rmtree(item, ignore_errors=True)
                    purged += 1

        return purged
