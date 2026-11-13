"""Banned phrases and safety sanitization engine.
Scans and neutralizes any unauthorized diagnostic claims, medication changes, or doctor bypass instructions.
"""
import re
from typing import List, Tuple

# Patterns detecting prohibited clinical statements
BANNED_PATTERNS: List[Tuple[str, str]] = [
    # 1. Diagnostic Assertions
    (r"\b(you have|diagnosed with|confirms a case of|you are suffering from|you do not have|you are disease[- ]free|this proves you have|you definitely have)\b", "diagnostic assertion"),
    (r"\b(indicates you have (diabetes|cancer|leukemia|anemia|kidney failure|hypertension))\b", "specific condition diagnosis"),
    
    # 2. Dosage / Prescription Alterations
    (r"\b(discontinue (your )?medication|stop taking|increase your dose|decrease (the |your )?dosage|take \d+\s*(mg|tablet|pill|ml) instead|change your medication|skip your medication|do not take this medicine)\b", "medication dosage alteration"),
    (r"\b(prescribe|start taking|substitute with)\b", "unauthorized prescribing"),

    # 3. Physician Bypass Advice
    (r"\b(no need to see (a|your) doctor|do not (see|visit|consult) (a|your) doctor|you can self[- ]treat|no need to consult (a|your) doctor|skip your doctor appointment)\b", "physician bypass advice")
]

APPROVED_SAFETY_DISCLAIMER = (
    "This explains your report. It does not replace your doctor. "
    "Please consult your healthcare provider for clinical diagnosis, treatment evaluation, or changes to prescribed medications."
)


def contains_banned_phrases(text: str) -> bool:
    """Returns True if any prohibited clinical assertions or medication modifications are found."""
    if not text:
        return False
    for pattern, _ in BANNED_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


def get_detected_banned_phrases(text: str) -> List[str]:
    """Returns a list of descriptions for all banned patterns matched."""
    if not text:
        return []
    matches = []
    for pattern, desc in BANNED_PATTERNS:
        found = re.findall(pattern, text, re.IGNORECASE)
        if found:
            matches.append(desc)
    return matches


def sanitize_ai_output(text: str) -> str:
    """Scans text and neutralizes any detected prohibited statements with approved clinical guidance."""
    if not text:
        return APPROVED_SAFETY_DISCLAIMER

    sanitized = text
    for pattern, _ in BANNED_PATTERNS:
        if re.search(pattern, sanitized, re.IGNORECASE):
            # Replace the unsafe matched sentence or clause with clinical safe guidance
            sanitized = re.sub(
                pattern,
                "[Clarification: Only your physician can diagnose conditions or adjust medications.]",
                sanitized,
                flags=re.IGNORECASE
            )

    return sanitized

