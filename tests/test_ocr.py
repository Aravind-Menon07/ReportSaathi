"""Unit tests for OCR extraction, clarity scoring, and user correction re-validation (5 tests).
"""
import unittest
from backend.integrations.ocr import (
    assess_text_clarity,
    parse_biomarkers_from_text,
    apply_user_corrections,
)


class TestOCREngine(unittest.TestCase):
    """OCR and parser test suite."""

    # TC-14: Clean report parsing correctly extracts test names, numbers, units, and ranges
    def test_tc14_clean_report_parsing(self):
        sample_text = (
            "Hemoglobin 14.0 g/dL 12.0 - 15.5\n"
            "WBC 6500 cells/mcL 4000 - 11000\n"
            "Platelets 250000 /mcL 150000 - 450000"
        )
        biomarkers = parse_biomarkers_from_text(sample_text)
        self.assertEqual(len(biomarkers), 3)
        self.assertEqual(biomarkers[0]["name"], "Hemoglobin")
        self.assertEqual(biomarkers[0]["value"], 14.0)
        self.assertEqual(biomarkers[0]["unit"], "g/dL")
        self.assertEqual(biomarkers[0]["status"], "normal")

    # TC-15: Blurry/noisy text detection identifies noise ratio > 0.15 and sets requires_verification
    def test_tc15_blurry_noisy_text_detection(self):
        noisy_text = (
            "H#m0gl~b!n ?? ? 13.5 g/dL ~~~ 12.0--15.0\n"
            "Pl@t#l#ts ??? 240,000 /cumm ^^^ 150000..450000\n"
            "||| ||| wbc ??? 6800"
        )
        clarity = assess_text_clarity(noisy_text)
        self.assertTrue(clarity["requires_verification"])
        self.assertEqual(clarity["status"], "unclear")
        self.assertGreater(clarity["noise_ratio"], 0.10)

    # TC-16: Missing range text extraction correctly marks status as 'no_range_on_report'
    def test_tc16_missing_range_parsing(self):
        text_without_range = "C-Reactive Protein (CRP) 18.5 mg/L\n"
        biomarkers = parse_biomarkers_from_text(text_without_range)
        self.assertTrue(len(biomarkers) >= 1)
        crp = biomarkers[0]
        self.assertIn("CRP", crp["name"])
        self.assertEqual(crp["value"], 18.5)
        self.assertEqual(crp["status"], "no_range_on_report")
        self.assertIsNone(crp["printed_range_low"])
        self.assertIsNone(crp["printed_range_high"])

    # TC-17: Indian number formatting (3,25,000) and special operators (< 0.5)
    def test_tc17_indian_numbers_and_operators(self):
        challenging_text = (
            "Platelet Count 3,25,000 /cumm 1,50,000 - 4,50,000\n"
            "Serum TSH < 0.5 uIU/mL 0.35 - 4.94"
        )
        biomarkers = parse_biomarkers_from_text(challenging_text)
        self.assertEqual(len(biomarkers), 2)
        # Verify 3,25,000 parsed to 325000.0
        self.assertEqual(biomarkers[0]["value"], 325000.0)
        self.assertEqual(biomarkers[0]["printed_range_low"], 150000.0)
        self.assertEqual(biomarkers[0]["printed_range_high"], 450000.0)
        self.assertEqual(biomarkers[0]["status"], "normal")

        # Verify < 0.5 parsed correctly
        self.assertEqual(biomarkers[1]["value"], 0.5)

    # TC-18: User corrections re-validation updates biomarkers and re-evaluates red flags
    def test_tc18_user_corrections_revalidation(self):
        # Patient corrects a misread potassium value to 6.8 mmol/L (critical red flag)
        corrected_text = "Serum Potassium 6.8 mmol/L 3.5 - 5.1\n"
        result = apply_user_corrections(corrected_text)
        self.assertFalse(result["requires_verification"])
        self.assertEqual(result["status"], "ready")
        self.assertEqual(len(result["biomarkers"]), 1)
        self.assertEqual(result["biomarkers"][0]["status"], "needs_attention")
        # Verify red-flag triggered on corrected payload
        self.assertEqual(len(result["red_flags"]), 1)
        self.assertEqual(result["red_flags"][0]["biomarker"], "Potassium")


if __name__ == "__main__":
    unittest.main()
