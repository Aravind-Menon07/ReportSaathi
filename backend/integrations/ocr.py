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
    which_path = shutil.which("tesseract")
    if which_path:
        return which_path

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
    except Exception:
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

    # Count noise characters (garbled OCR artifacts)
    noise_chars = len(re.findall(r"[^\w\s\.,;:/\-()<>%+=|]", stripped))

    # Check for unreadable artifact tokens
    unreadable_token_matches = re.findall(r"(\?{2,}|\b[a-zA-Z]{1}\b(?:\s+[a-zA-Z]{1}\b){3,})", stripped)
    unreadable_token_count = len(unreadable_token_matches)

    noise_ratio = noise_chars / max(1, total_chars)

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
    cleaned = re.sub(r"[^\d.\-+]", "", num_str.replace(",", ""))
    match = re.search(r"[-+]?\d*\.?\d+", cleaned)
    if match:
        try:
            return float(match.group(0))
        except ValueError:
            return None
    return None


def _normalize_line(line: str) -> str:
    """Normalize OCR artefacts: collapse multiple spaces, remove stray pipes used as column separators."""
    line = re.sub(r"\|+", " ", line)          # pipes → spaces (table columns)
    line = re.sub(r"\t+", " ", line)           # tabs   → spaces
    line = re.sub(r" {2,}", " ", line)         # multi-space → single space
    return line.strip()


def parse_biomarkers_from_text(raw_text: str) -> List[Dict[str, Any]]:
    """Extracts test names, observed values, units, and printed ranges from report text.

    Handles:
    - Indian formatted numbers (3,25,000)
    - Special operators (< 0.5, > 100, Negative, Positive, Non-Reactive)
    - Multi-column table rows separated by spaces, tabs, or pipe characters
    - Lines that contain only the name in one line and value+range in the next
    """
    if not raw_text:
        return []

    biomarkers: List[Dict[str, Any]] = []
    seen_names: set = set()

    # Extended units for Indian lab reports
    units_pattern = (
        r"(?:g/dL|mg/dL|mmol/L|mEq/L|/mcL|/cumm|cells/mcL|cells/cu\.mm"
        r"|uIU/mL|IU/mL|mIU/mL|ng/mL|pg/mL|mg/L|U/L|g/L|umol/L|nmol/L"
        r"|10\^3/uL|10\^6/uL|10\^9/L|K/uL|M/uL|/uL"
        r"|fL|fl|pg|%|sec|seconds|min|hours|ratio)"
    )

    # Number pattern that handles Indian comma formatting  
    num_pat = r"[<>]?\s*[\d,]+(?:\.\d+)?"

    # -------------------------------------------------------------------
    # Regex A: Full row — Name  Value  Unit  Low-High
    # e.g. "Hemoglobin  13.5  g/dL  12.0 - 15.5"
    # -------------------------------------------------------------------
    re_A = re.compile(
        rf"^(?P<name>[A-Za-z][A-Za-z0-9 \(\)\/\-\.\+\#]*?)\s+"
        rf"(?P<value>{num_pat}|Negative|Positive|Non-?Reactive|Reactive|Absent|Present)\s*"
        rf"(?P<unit>{units_pattern})?\s*"
        rf"(?P<low>[\d,]+(?:\.\d+)?)\s*[-–to]+\s*(?P<high>[\d,]+(?:\.\d+)?)",
        re.IGNORECASE,
    )

    # -------------------------------------------------------------------
    # Regex B: Name  Value  Unit  (no printed range)
    # e.g. "C-Reactive Protein  12.5  mg/L"
    # -------------------------------------------------------------------
    re_B = re.compile(
        rf"^(?P<name>[A-Za-z][A-Za-z0-9 \(\)\/\-\.\+\#]*?)\s+"
        rf"(?P<value>{num_pat}|Negative|Positive|Non-?Reactive|Reactive)\s+"
        rf"(?P<unit>{units_pattern})\s*$",
        re.IGNORECASE,
    )

    # -------------------------------------------------------------------
    # Regex C: Tabular — Name  Value  Low-High  (no explicit unit)
    # e.g. "Platelets  18000  150000 - 450000"
    # -------------------------------------------------------------------
    re_C = re.compile(
        r"^(?P<name>[A-Za-z][A-Za-z0-9 \(\)\/\-\.\+\#]*?)\s+"
        r"(?P<value>[\d,]+(?:\.\d+)?)\s+"
        r"(?P<low>[\d,]+(?:\.\d+)?)\s*[-–to]+\s*(?P<high>[\d,]+(?:\.\d+)?)",
        re.IGNORECASE,
    )

    # -------------------------------------------------------------------
    # Regex D: "Name  Value  Unit  < X" or "> X" (single-bound range)
    # e.g. "TSH  2.3  uIU/mL  < 4.5"
    # -------------------------------------------------------------------
    re_D = re.compile(
        rf"^(?P<name>[A-Za-z][A-Za-z0-9 \(\)\/\-\.\+\#]*?)\s+"
        rf"(?P<value>{num_pat})\s+"
        rf"(?P<unit>{units_pattern})?\s*"
        rf"(?P<bound>[<>]\s*[\d,]+(?:\.\d+)?)\s*$",
        re.IGNORECASE,
    )

    # -------------------------------------------------------------------
    # Regex E: "Name  :  Value  Unit  Low - High" (colon-separated label)
    # -------------------------------------------------------------------
    re_E = re.compile(
        rf"^(?P<name>[A-Za-z][A-Za-z0-9 \(\)\/\-\.\+\#]*?)\s*:\s*"
        rf"(?P<value>{num_pat}|Negative|Positive|Non-?Reactive|Reactive)\s*"
        rf"(?P<unit>{units_pattern})?\s*"
        rf"(?:(?P<low>[\d,]+(?:\.\d+)?)\s*[-–to]+\s*(?P<high>[\d,]+(?:\.\d+)?))?",
        re.IGNORECASE,
    )

    # Known clinical test names for keyword fallback
    known_tests = [
        "hemoglobin", "haemoglobin", "hb", "hgb",
        "wbc", "white blood cell", "white blood cells", "leukocyte",
        "rbc", "red blood cell", "red blood cells", "erythrocyte",
        "platelet", "platelets", "plt", "thrombocyte",
        "tlc", "total leucocyte count", "dlc", "differential",
        "hematocrit", "haematocrit", "packed cell volume", "pcv", "hct",
        "mcv", "mch", "mchc", "rdw",
        "neutrophil", "lymphocyte", "monocyte", "eosinophil", "basophil",
        "creatinine", "serum creatinine",
        "urea", "blood urea nitrogen", "bun",
        "uric acid", "urate",
        "potassium", "sodium", "chloride", "calcium", "phosphorus", "magnesium",
        "bicarbonate", "co2",
        "glucose", "blood sugar", "fasting glucose", "ppbs", "hba1c",
        "total cholesterol", "cholesterol", "hdl", "ldl", "vldl", "triglyceride",
        "alt", "sgpt", "ast", "sgot", "alp", "alkaline phosphatase",
        "total bilirubin", "direct bilirubin", "indirect bilirubin",
        "total protein", "albumin", "globulin",
        "tsh", "t3", "t4", "free t3", "free t4",
        "ferritin", "serum iron", "tibc", "transferrin",
        "crp", "c-reactive protein", "esr",
        "vitamin d", "vitamin b12", "folate",
        "psa", "prostate specific antigen",
    ]

    lines = raw_text.splitlines()
    i = 0
    while i < len(lines):
        raw_line = lines[i]
        line = _normalize_line(raw_line)
        i += 1

        if len(line) < 3:
            continue

        # Try multi-line lookahead: if this line is ONLY a test name (no digits at all)
        # and next line has numbers → merge them for parsing
        if i < len(lines) and not re.search(r"\d", line):
            next_line = _normalize_line(lines[i])
            if re.match(r"^[A-Za-z][A-Za-z0-9 \(\)\/\-\.\+\#]{2,50}$", line) and re.search(r"\d", next_line):
                merged = line + "  " + next_line
                if re_A.match(merged) or re_C.match(merged):
                    line = merged
                    i += 1  # consume next line

        def _add(name: str, value_str: str, unit: Optional[str],
                 low_str: Optional[str], high_str: Optional[str],
                 raw_range: str = "") -> bool:
            name = name.strip()
            key = name.lower()
            if key in seen_names or len(name) < 2:
                return False
            seen_names.add(key)

            num_val = _clean_number(value_str)
            low_val = _clean_number(low_str) if low_str else None
            high_val = _clean_number(high_str) if high_str else None

            status = evaluate_biomarker(
                name,
                num_val if num_val is not None else value_str,
                unit,
                low_val,
                high_val,
            )
            biomarkers.append({
                "name": name,
                "value": num_val if num_val is not None else value_str,
                "unit": unit or "",
                "printed_range_low": low_val,
                "printed_range_high": high_val,
                "raw_range": raw_range if raw_range else (
                    f"{low_val} - {high_val}" if (low_val is not None and high_val is not None) else ""
                ),
                "status": status,
            })
            return True

        # Try Regex A
        m = re_A.match(line)
        if m:
            rr = f"{m.group('low')} - {m.group('high')}"
            _add(m.group("name"), m.group("value"), m.group("unit"),
                 m.group("low"), m.group("high"), rr)
            continue

        # Try Regex E (colon form — do before D/B to avoid false B match)
        m = re_E.match(line)
        if m:
            low_s = m.group("low") if m.lastindex and "low" in m.groupdict() else None
            high_s = m.group("high") if m.lastindex and "high" in m.groupdict() else None
            _add(m.group("name"), m.group("value"), m.group("unit"), low_s, high_s)
            continue

        # Try Regex D (single-bound)
        m = re_D.match(line)
        if m:
            bound = m.group("bound").strip()
            bound_val = _clean_number(re.sub(r"[<>]", "", bound))
            if "<" in bound:
                low_s, high_s = "0", str(bound_val) if bound_val else None
            else:
                low_s, high_s = str(bound_val) if bound_val else None, None
            _add(m.group("name"), m.group("value"), m.group("unit"), low_s, high_s, bound)
            continue

        # Try Regex B (no range)
        m = re_B.match(line)
        if m:
            name = m.group("name").strip()
            key = name.lower()
            if key not in seen_names and len(name) >= 2:
                seen_names.add(key)
                num_val = _clean_number(m.group("value"))
                biomarkers.append({
                    "name": name,
                    "value": num_val if num_val is not None else m.group("value"),
                    "unit": m.group("unit") or "",
                    "printed_range_low": None,
                    "printed_range_high": None,
                    "raw_range": "",
                    "status": "no_range_on_report",
                })
            continue

        # Try Regex C (tabular, no unit)
        m = re_C.match(line)
        if m:
            rr = f"{m.group('low')} - {m.group('high')}"
            _add(m.group("name"), m.group("value"), None,
                 m.group("low"), m.group("high"), rr)
            continue

        # Fallback: keyword scan for known test names within unstructured lines
        lower_line = line.lower()
        for kt in known_tests:
            if re.search(rf"\b{re.escape(kt)}\b", lower_line):
                nums = re.findall(r"[<>]?\s*[\d,]+(?:\.\d+)?", line)
                nums = [n.strip() for n in nums if n.strip()]
                if nums:
                    val_str = nums[0]
                    low_str2 = nums[1] if len(nums) > 1 else None
                    high_str2 = nums[2] if len(nums) > 2 else None
                    # heuristic: if two numbers and they're plausibly a range
                    if low_str2 and high_str2:
                        lv = _clean_number(low_str2)
                        hv = _clean_number(high_str2)
                        vv = _clean_number(val_str)
                        # sanity: low < high
                        if lv is not None and hv is not None and lv < hv:
                            display_name = kt.title()
                            _add(display_name, val_str, None, low_str2, high_str2)
                            break
                    elif low_str2 is None:
                        # single value only → no_range
                        display_name = kt.title()
                        key = display_name.lower()
                        if key not in seen_names:
                            seen_names.add(key)
                            num_val = _clean_number(val_str)
                            biomarkers.append({
                                "name": display_name,
                                "value": num_val if num_val is not None else val_str,
                                "unit": "",
                                "printed_range_low": None,
                                "printed_range_high": None,
                                "raw_range": "",
                                "status": "no_range_on_report",
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
        "status": "ready",
    }
