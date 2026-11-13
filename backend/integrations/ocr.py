"""OCR extraction and text processing engine for ReportSaathi.
Integrates Tesseract OCR, algorithmic clarity scoring, regex biomarker parsing, and human corrections.
"""
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union

from backend.safety.rules import evaluate_biomarker, check_red_flags


def _find_tesseract_cmd() -> str:
    """Finds tesseract executable across system PATH and standard Windows locations."""
    # Check system PATH
    which_path = shutil.which("tesseract")
    if which_path:
        return which_path

    # Standard Windows install locations
    win_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        os.path.expanduser(r"~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"),
    ]
    for p in win_paths:
        if os.path.isfile(p):
            return p

    return "tesseract"


def run_tesseract(image_path: Union[str, Path], psm: int = 6) -> str:
    """Runs Tesseract CLI on the provided image and returns extracted raw text."""
    cmd = _find_tesseract_cmd()
    img_str = str(image_path)

    if not os.path.exists(img_str):
        raise FileNotFoundError(f"Image not found at path: {img_str}")

    try:
        proc = subprocess.run(
            [cmd, img_str, "stdout", "--psm", str(psm)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
            encoding="utf-8",
            errors="replace",
        )
        return proc.stdout
    except Exception as e:
        # Fallback if tesseract CLI errors or is mock tested
        return ""


def assess_text_clarity(text: str) -> Dict[str, Any]:
    """Algorithmic noise and readability assessment.
    
    If noise ratio > 0.15 or unreadable tokens exist, returns:
    requires_verification: true, status: 'unclear'
    """
    if not text or not text.strip():
        return {
            "clarity_score": 0.0,
            "noise_ratio": 1.0,
            "requires_verification": True,
            "status": "unclear",
            "message": "Empty or illegible document text."
        }

    stripped = text.strip()
    total_chars = len(stripped)
    
    # Count noise characters (garbled OCR artifacts like ~, ^, |, excessive non-alphanumeric/non-standard punctuation)
    noise_chars = len(re.findall(r"[^\w\s\.,;:/\-()<>%+=]", stripped))
    
    # Check for unreadable artifact tokens like '???', '', '|||', excessive isolated single characters
    unreadable_token_matches = re.findall(r"(\?{2,}|\b[a-zA-Z]{1}\b(?:\s+[a-zA-Z]{1}\b){3,}|[^\x00-\x7F]{2,})", stripped)
    unreadable_token_count = len(unreadable_token_matches)

    noise_ratio = noise_chars / max(1, total_chars)
    
    # Penalize if noise ratio > 0.15 or multiple garbled tokens
    is_unclear = (noise_ratio > 0.15) or (unreadable_token_count >= 2)
    clarity_score = max(0.0, min(1.0, 1.0 - (noise_ratio * 3.0) - (unreadable_token_count * 0.1)))

    return {
        "clarity_score": round(clarity_score, 2),
        "noise_ratio": round(noise_ratio, 3),
        "requires_verification": is_unclear,
        "status": "unclear" if is_unclear else "ready",
        "message": "Document contains visual noise or unreadable tokens requiring patient verification." if is_unclear else "Text clarity verified."
    }


def _clean_number(num_str: str) -> Optional[float]:
    """Converts a string representation of a number (including Indian formatted commas) into float."""
    if not num_str:
        return None
    cleaned = num_str.replace(",", "").strip()
    match = re.search(r"[-+]?\d*\.?\d+", cleaned)
    if match:
        try:
            return float(match.group(0))
        except ValueError:
            return None
    return None


def parse_biomarkers_from_text(raw_text: str) -> List[Dict[str, Any]]:
    """Extracts test names, observed values, units, and printed ranges from report text.
    Handles Indian formatted numbers (e.g., 3,25,000) and special operators (< 0.5, > 100, Negative).
    """
    if not raw_text:
        return []

    biomarkers: List[Dict[str, Any]] = []
    lines = raw_text.splitlines()

    # Units commonly present in Indian lab reports
    units_pattern = r"(g/dL|mg/dL|mmol/L|mEq/L|/mcL|/cumm|cells/mcL|cells/cu\.mm|uIU/mL|IU/mL|ng/mL|pg/mL|mg/L|U/L|%|sec|seconds|fl|pg)"

    # Regex 1: Full line with Name, Value, Unit, and Printed Range (e.g., "Hemoglobin 13.5 g/dL 12.0 - 15.5")
    # Also handles Indian commas: "Platelet Count 2,40,000 /cumm 1,50,000 - 4,50,000"
    regex_with_range = re.compile(
        rf"^(?P<name>[A-Za-z0-9\s\(\)\/\-\.\+]+?)\s+"
        rf"(?P<value>[<>]?\s*[\d,]+(?:\.\d+)?|Negative|Positive|Non-Reactive|Reactive)\s+"
        rf"(?P<unit>{units_pattern})?\s+"
        rf"(?P<range>(?:(?P<low>[\d,]+(?:\.\d+)?)\s*(?:-|to)\s*(?P<high>[\d,]+(?:\.\d+)?))|(?:[<>]\s*[\d,]+(?:\.\d+)?))",
        re.IGNORECASE
    )

    # Regex 2: Line with Name, Value, Unit but NO Range (e.g., "C-Reactive Protein (CRP) 12.5 mg/L")
    regex_no_range = re.compile(
        rf"^(?P<name>[A-Za-z0-9\s\(\)\/\-\.\+]+?)\s+"
        rf"(?P<value>[<>]?\s*[\d,]+(?:\.\d+)?|Negative|Positive)\s+"
        rf"(?P<unit>{units_pattern})\s*$",
        re.IGNORECASE
    )

    # Regex 3: Tabular or multi-column without standard unit (e.g., "Platelets 18000 150000-450000")
    regex_simple_table = re.compile(
        r"^(?P<name>[A-Za-z0-9\s\(\)\/\-\.\+]+?)\s+"
        r"(?P<value>[\d,]+(?:\.\d+)?)\s+"
        r"(?P<low>[\d,]+(?:\.\d+)?)\s*-\s*(?P<high>[\d,]+(?:\.\d+)?)",
        re.IGNORECASE
    )

    # Known common clinical test names for fallback keyword matching
    known_tests = [
        "hemoglobin", "hb", "hgb", "wbc", "rbc", "platelet", "tlc", "dlc",
        "creatinine", "urea", "bun", "uric acid",
        "potassium", "sodium", "chloride", "calcium",
        "glucose", "fasting blood sugar", "ppbs", "rbs", "hba1c",
        "cholesterol", "triglycerides", "hdl", "ldl", "vldl",
        "bilirubin", "sgot", "ast", "sgpt", "alt", "alkaline phosphatase", "alp",
        "tsh", "t3", "t4", "crp", "esr"
    ]

    for line in lines:
        cleaned_line = line.strip()
        if not cleaned_line or len(cleaned_line) < 4:
            continue

        # Skip headers like "Test Name Result Reference Interval"
        if re.search(r"\b(test name|investigation|parameter|reference interval|normal range|units?)\b", cleaned_line, re.IGNORECASE):
            continue

        # Try Regex 1 (Full line with range)
        m1 = regex_with_range.match(cleaned_line)
        if m1:
            name = m1.group("name").strip()
            val_str = m1.group("value").strip()
            unit = m1.group("unit")
            raw_range = m1.group("range")
            low_str = m1.group("low")
            high_str = m1.group("high")

            num_val = _clean_number(val_str)
            low_val = _clean_number(low_str) if low_str else None
            high_val = _clean_number(high_str) if high_str else None

            # Handle single bounded ranges like "< 200" or "> 50"
            if not low_val and not high_val and raw_range:
                if "<" in raw_range:
                    high_val = _clean_number(raw_range.replace("<", ""))
                    low_val = 0.0
                elif ">" in raw_range:
                    low_val = _clean_number(raw_range.replace(">", ""))
                    high_val = low_val * 3.0 if low_val else None

            status = evaluate_biomarker(name, num_val if num_val is not None else val_str, unit, low_val, high_val)
            biomarkers.append({
                "name": name,
                "value": num_val if num_val is not None else val_str,
                "unit": unit or "",
                "printed_range_low": low_val,
                "printed_range_high": high_val,
                "raw_range": raw_range or "",
                "status": status
            })
            continue

        # Try Regex 2 (Line with no printed range)
        m2 = regex_no_range.match(cleaned_line)
        if m2:
            name = m2.group("name").strip()
            val_str = m2.group("value").strip()
            unit = m2.group("unit")
            num_val = _clean_number(val_str)

            # Strict rule: If report lacks printed range -> 'no_range_on_report'
            biomarkers.append({
                "name": name,
                "value": num_val if num_val is not None else val_str,
                "unit": unit or "",
                "printed_range_low": None,
                "printed_range_high": None,
                "raw_range": "",
                "status": "no_range_on_report"
            })
            continue

        # Try Regex 3 (Simple table layout)
        m3 = regex_simple_table.match(cleaned_line)
        if m3:
            name = m3.group("name").strip()
            val_str = m3.group("value").strip()
            low_str = m3.group("low")
            high_str = m3.group("high")

            num_val = _clean_number(val_str)
            low_val = _clean_number(low_str)
            high_val = _clean_number(high_str)

            status = evaluate_biomarker(name, num_val if num_val is not None else val_str, None, low_val, high_val)
            biomarkers.append({
                "name": name,
                "value": num_val if num_val is not None else val_str,
                "unit": "",
                "printed_range_low": low_val,
                "printed_range_high": high_val,
                "raw_range": f"{low_str} - {high_str}",
                "status": status
            })
            continue

        # Fallback keyword matching for known test names embedded in unstructured text
        lower_line = cleaned_line.lower()
        for kt in known_tests:
            if re.search(rf"\b{re.escape(kt)}\b", lower_line):
                # Search for numbers in this line
                nums = re.findall(r"[\d,]+(?:\.\d+)?", cleaned_line)
                if nums:
                    val = _clean_number(nums[0])
                    low_val = _clean_number(nums[1]) if len(nums) > 1 else None
                    high_val = _clean_number(nums[2]) if len(nums) > 2 else None
                    raw_range = f"{low_val} - {high_val}" if (low_val is not None and high_val is not None) else ""
                    status = evaluate_biomarker(kt.title(), val, None, low_val, high_val)
                    biomarkers.append({
                        "name": kt.title(),
                        "value": val,
                        "unit": "",
                        "printed_range_low": low_val,
                        "printed_range_high": high_val,
                        "raw_range": raw_range,
                        "status": status
                    })
                break

    return biomarkers


def apply_user_corrections(corrected_text: str) -> Dict[str, Any]:
    """Re-parses user-corrected text, evaluates biomarker ranges, and re-triggers red-flag evaluation."""
    if not corrected_text or not corrected_text.strip():
        raise ValueError("Corrected text payload cannot be empty.")

    biomarkers = parse_biomarkers_from_text(corrected_text)
    red_flags = check_red_flags(biomarkers)
    clarity = assess_text_clarity(corrected_text)

    return {
        "biomarkers": biomarkers,
        "red_flags": red_flags,
        "clarity": clarity,
        "requires_verification": False,
        "status": "ready"
    }
