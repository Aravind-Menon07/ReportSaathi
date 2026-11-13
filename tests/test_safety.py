"""Unit tests for Deterministic Safety Engine (13 tests).
Covers range classifications, missing range discipline, red-flag triggers, and banned phrase sanitization.
"""
import unittest
from backend.safety.rules import evaluate_biomarker, check_red_flags
from backend.safety.banned_phrases import (
    contains_banned_phrases,
    sanitize_ai_output,
    APPROVED_SAFETY_DISCLAIMER,
)


class TestSafetyEngine(unittest.TestCase):
    """Safety rules test suite."""

    # TC-01: Classification inside range returns 'normal'
    def test_tc01_normal_classification(self):
        status = evaluate_biomarker("Hemoglobin", 14.0, "g/dL", 12.0, 16.0)
        self.assertEqual(status, "normal")

    # TC-02: Classification within 5% of low boundary returns 'borderline'
    def test_tc02_borderline_low_boundary(self):
        # Range 10.0 to 20.0, span=10.0, 5% delta=0.5
        # 10.2 is within 0.5 of low boundary (10.0)
        status = evaluate_biomarker("Biomarker", 10.2, "mg/dL", 10.0, 20.0)
        self.assertEqual(status, "borderline")

    # TC-03: Classification within 5% of high boundary returns 'borderline'
    def test_tc03_borderline_high_boundary(self):
        # Range 10.0 to 20.0, span=10.0, 5% delta=0.5
        # 19.8 is within 0.5 of high boundary (20.0)
        status = evaluate_biomarker("Biomarker", 19.8, "mg/dL", 10.0, 20.0)
        self.assertEqual(status, "borderline")

    # TC-04: Classification above range returns 'needs_attention'
    def test_tc04_above_range_needs_attention(self):
        status = evaluate_biomarker("Total Cholesterol", 242, "mg/dL", 125, 200)
        self.assertEqual(status, "needs_attention")

    # TC-05: Classification below range returns 'needs_attention'
    def test_tc05_below_range_needs_attention(self):
        status = evaluate_biomarker("Hemoglobin", 9.2, "g/dL", 12.0, 15.0)
        self.assertEqual(status, "needs_attention")

    # TC-06: Missing printed range (low=None or high=None) returns 'no_range_on_report'
    def test_tc06_missing_printed_range(self):
        self.assertEqual(evaluate_biomarker("CRP", 18.5, "mg/L", None, None), "no_range_on_report")
        self.assertEqual(evaluate_biomarker("CRP", 18.5, "mg/L", 10.0, None), "no_range_on_report")
        self.assertEqual(evaluate_biomarker("CRP", 18.5, "mg/L", None, 20.0), "no_range_on_report")

    # TC-07: Red-flag trigger for critical high Potassium (>= 6.2)
    def test_tc07_critical_high_potassium(self):
        alerts = check_red_flags([{"name": "Serum Potassium", "value": 6.8, "unit": "mmol/L"}])
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0]["biomarker"], "Potassium")
        self.assertEqual(alerts[0]["severity"], "critical")
        self.assertIn("Severe Hyperkalemia", alerts[0]["action_prompt"])

    # TC-08: Red-flag trigger for critical low Potassium (<= 2.8)
    def test_tc08_critical_low_potassium(self):
        alerts = check_red_flags([{"name": "Potassium", "value": 2.5, "unit": "mmol/L"}])
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0]["biomarker"], "Potassium")
        self.assertEqual(alerts[0]["severity"], "critical")
        self.assertIn("Severe Hypokalemia", alerts[0]["action_prompt"])

    # TC-09: Red-flag trigger for critical low Platelets (<= 20,000)
    def test_tc09_critical_low_platelets(self):
        alerts = check_red_flags([{"name": "Platelet Count", "value": 18000, "unit": "/uL"}])
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0]["biomarker"], "Platelets")
        self.assertEqual(alerts[0]["severity"], "critical")
        self.assertIn("Critical Thrombocytopenia", alerts[0]["action_prompt"])

    # TC-10: Red-flag trigger for critical low Hemoglobin (<= 7.0)
    def test_tc10_critical_low_hemoglobin(self):
        alerts = check_red_flags([{"name": "Hemoglobin", "value": 6.2, "unit": "g/dL"}])
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0]["biomarker"], "Hemoglobin")
        self.assertIn("Severe Life-Threatening Anemia", alerts[0]["action_prompt"])

    # TC-11: Red-flag trigger for critical Glucose (<= 50 or >= 350)
    def test_tc11_critical_glucose_thresholds(self):
        alerts_low = check_red_flags([{"name": "Blood Glucose Fasting", "value": 45, "unit": "mg/dL"}])
        self.assertEqual(len(alerts_low), 1)
        self.assertIn("Severe Hypoglycemia", alerts_low[0]["action_prompt"])

        alerts_high = check_red_flags([{"name": "Fasting Blood Sugar", "value": 380, "unit": "mg/dL"}])
        self.assertEqual(len(alerts_high), 1)
        self.assertIn("DKA / HHS", alerts_high[0]["action_prompt"])

    # TC-12: Red-flag trigger for critical high Creatinine (>= 5.0)
    def test_tc12_critical_high_creatinine(self):
        alerts = check_red_flags([{"name": "Serum Creatinine", "value": 5.8, "unit": "mg/dL"}])
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0]["biomarker"], "Creatinine")
        self.assertIn("Acute Renal Failure", alerts[0]["action_prompt"])

    # TC-13: Banned phrases detection and AI output sanitization
    def test_tc13_banned_phrases_sanitization(self):
        unsafe_text_1 = "You have diabetes and you must discontinue your medication immediately."
        self.assertTrue(contains_banned_phrases(unsafe_text_1))
        sanitized_1 = sanitize_ai_output(unsafe_text_1)
        self.assertNotIn("you have diabetes", sanitized_1.lower())
        self.assertNotIn("discontinue your medication", sanitized_1.lower())

        unsafe_text_2 = "No need to see a doctor, you can self-treat."
        self.assertTrue(contains_banned_phrases(unsafe_text_2))
        sanitized_2 = sanitize_ai_output(unsafe_text_2)
        self.assertNotIn("no need to see a doctor", sanitized_2.lower())


if __name__ == "__main__":
    unittest.main()
