"""Deterministic Clinical Safety Rules Engine.
Evaluates laboratory reference ranges and triggers life-threatening emergency alerts.
"""
from typing import List, Dict, Any, Optional, Union
import re


def _parse_float(val: Any) -> Optional[float]:
    """Helper to safely parse numeric values from strings or numbers."""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        # Clean Indian formatted commas (e.g., 3,25,000) and whitespace
        cleaned = val.replace(",", "").strip()
        # Extract first decimal or integer number
        match = re.search(r"[-+]?\d*\.?\d+", cleaned)
        if match:
            try:
                return float(match.group(0))
            except ValueError:
                return None
    return None


def evaluate_biomarker(
    name: str,
    value: Union[float, int, str, None],
    unit: Optional[str] = None,
    low: Optional[Union[float, int, str]] = None,
    high: Optional[Union[float, int, str]] = None,
) -> str:
    """Evaluates values against printed report ranges.
    
    Rules:
    - If low or high is None, returns 'no_range_on_report'.
    - Classifies within 5% of boundaries as 'borderline'.
    - Classifies strictly outside as 'needs_attention'.
    - Classifies safely inside as 'normal'.
    """
    if low is None or high is None:
        return "no_range_on_report"

    num_val = _parse_float(value)
    num_low = _parse_float(low)
    num_high = _parse_float(high)

    if num_val is None or num_low is None or num_high is None:
        return "no_range_on_report"

    # Ensure low <= high
    if num_low > num_high:
        num_low, num_high = num_high, num_low

    span = num_high - num_low
    # 5% boundary threshold
    delta = span * 0.05 if span > 0 else (abs(num_high) * 0.05 if num_high != 0 else 0.05)

    # Check if within 5% of boundaries
    near_low = abs(num_val - num_low) <= delta
    near_high = abs(num_val - num_high) <= delta

    if near_low or near_high:
        return "borderline"
    elif num_val < num_low or num_val > num_high:
        return "needs_attention"
    else:
        return "normal"


def check_red_flags(biomarkers: List[Union[Dict[str, Any], Any]]) -> List[Dict[str, Any]]:
    """Evaluates life-threatening emergency thresholds strictly in pure Python.
    
    Thresholds:
    * Potassium: >= 6.2 mmol/L (Severe Hyperkalemia) or <= 2.8 mmol/L (Severe Hypokalemia)
    * Platelets: <= 20,000 /uL (Critical Thrombocytopenia)
    * Hemoglobin: <= 7.0 g/dL (Severe Life-Threatening Anemia)
    * Glucose: <= 50 mg/dL (Severe Hypoglycemia) or >= 350 mg/dL (DKA/HHS risk)
    * Creatinine: >= 5.0 mg/dL (Acute Renal Failure)
    """
    alerts: List[Dict[str, Any]] = []

    for item in biomarkers:
        # Support dict or pydantic model
        if hasattr(item, "model_dump"):
            b = item.model_dump()
        elif hasattr(item, "__dict__"):
            b = item.__dict__
        elif isinstance(item, dict):
            b = item
        else:
            continue

        raw_name = str(b.get("name", "")).lower().strip()
        val = _parse_float(b.get("value"))
        if val is None:
            continue

        # 1. Potassium
        if "potassium" in raw_name or raw_name == "k" or raw_name == "k+":
            if val >= 6.2:
                alerts.append({
                    "biomarker": "Potassium",
                    "value": val,
                    "severity": "critical",
                    "action_prompt": "Emergency Attention Required: Critical Potassium Level (Severe Hyperkalemia). Seek emergency medical care immediately.",
                    "message": f"Potassium of {val} mmol/L is dangerously elevated (>= 6.2 mmol/L), posing a severe risk of fatal cardiac arrhythmias."
                })
            elif val <= 2.8:
                alerts.append({
                    "biomarker": "Potassium",
                    "value": val,
                    "severity": "critical",
                    "action_prompt": "Emergency Attention Required: Critical Potassium Level (Severe Hypokalemia). Seek emergency medical care immediately.",
                    "message": f"Potassium of {val} mmol/L is critically low (<= 2.8 mmol/L), posing a severe risk of cardiac dysrhythmias and respiratory failure."
                })

        # 2. Platelets
        elif "platelet" in raw_name or "plt" in raw_name:
            if val <= 20000:
                alerts.append({
                    "biomarker": "Platelets",
                    "value": val,
                    "severity": "critical",
                    "action_prompt": "Emergency Attention Required: Critical Thrombocytopenia. Seek immediate medical evaluation.",
                    "message": f"Platelet count of {val:,.0f} /uL is dangerously low (<= 20,000 /uL), indicating an extreme risk of spontaneous hemorrhage."
                })

        # 3. Hemoglobin
        elif "hemoglobin" in raw_name or raw_name == "hb" or raw_name == "hgb":
            if val <= 7.0:
                alerts.append({
                    "biomarker": "Hemoglobin",
                    "value": val,
                    "severity": "critical",
                    "action_prompt": "Urgent Medical Attention Required: Severe Life-Threatening Anemia. Contact a doctor or emergency department immediately.",
                    "message": f"Hemoglobin of {val} g/dL is severely low (<= 7.0 g/dL), indicating critical oxygen transport compromise."
                })

        # 4. Glucose / Blood Sugar
        elif "glucose" in raw_name or "sugar" in raw_name or "fbs" in raw_name or "rbs" in raw_name or "ppbs" in raw_name:
            if val <= 50:
                alerts.append({
                    "biomarker": "Glucose",
                    "value": val,
                    "severity": "critical",
                    "action_prompt": "Emergency Attention Required: Severe Hypoglycemia. Consume fast-acting sugar and seek urgent medical assistance immediately.",
                    "message": f"Blood glucose of {val} mg/dL is dangerously low (<= 50 mg/dL), with immediate risk of neuroglycopenia, seizure, or loss of consciousness."
                })
            elif val >= 350:
                alerts.append({
                    "biomarker": "Glucose",
                    "value": val,
                    "severity": "critical",
                    "action_prompt": "Emergency Attention Required: Severe Hyperglycemia (DKA / HHS risk). Seek immediate emergency medical care.",
                    "message": f"Blood glucose of {val} mg/dL is critically high (>= 350 mg/dL), posing a severe risk of Diabetic Ketoacidosis or Hyperosmolar Hyperglycemic State."
                })

        # 5. Creatinine
        elif "creatinine" in raw_name or "creat" in raw_name:
            if val >= 5.0:
                alerts.append({
                    "biomarker": "Creatinine",
                    "value": val,
                    "severity": "critical",
                    "action_prompt": "Emergency Attention Required: Severe Renal Impairment / Acute Renal Failure. Seek immediate nephrology or emergency medical care.",
                    "message": f"Serum creatinine of {val} mg/dL is critically elevated (>= 5.0 mg/dL), indicating potential acute kidney failure or severe renal injury."
                })

    return alerts

