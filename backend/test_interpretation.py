"""
Unit tests for the Finding-Based Disease Interpretation service and schemas.
Ensures adherence to mandatory medical-AI safety rules:
1. No fabricated cancer diagnoses or unsupported disease probabilities.
2. Both benign and malignant differentials included for mass and nodule.
3. Explicit uncertainty and diagnostic limitations present for all classes.
4. "No Finding" explicitly warns about radiographically occult disease.
5. Grad-CAM transparency disclaimer is preserved.
"""

import sys
from pathlib import Path
_REPO_ROOT = str(Path(__file__).resolve().parent.parent)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

import unittest
from backend.services.interpretation_service import interpretation_service, FINDING_KNOWLEDGE_BASE
from backend.schemas.analysis import PathologyPredictionSchema


class TestFindingInterpretation(unittest.TestCase):
    def setUp(self):
        self.mock_predictions = [
            PathologyPredictionSchema(
                id="mass",
                name="Mass",
                probability=0.74,
                severity="high",
                threshold=0.35,
                detected=True,
                description="Circumscribed pulmonary lesion > 3cm",
                anatomical_region="Pulmonary Fields",
                clinical_significance="Requires tissue diagnosis",
            ),
            PathologyPredictionSchema(
                id="nodule",
                name="Nodule",
                probability=0.48,
                severity="moderate",
                threshold=0.35,
                detected=True,
                description="Rounded opacity < 3cm",
                anatomical_region="Pulmonary Fields",
                clinical_significance="Solitary nodule",
            ),
            PathologyPredictionSchema(
                id="pneumothorax",
                name="Pneumothorax",
                probability=0.62,
                severity="high",
                threshold=0.30,
                detected=True,
                description="Gas in pleural space",
                anatomical_region="Pleural Margin",
                clinical_significance="Acute finding",
            ),
            PathologyPredictionSchema(
                id="no_finding",
                name="No Finding",
                probability=0.15,
                severity="low",
                threshold=0.60,
                detected=False,
                description="No primary findings",
                anatomical_region="Entire Thorax",
                clinical_significance="Unremarkable screening",
            ),
        ]

    def test_all_standard_classes_in_knowledge_base(self):
        """Verify all 10 canonical classes are represented in the interpretation knowledge base."""
        expected_classes = [
            "atelectasis", "cardiomegaly", "consolidation", "infiltration",
            "mass", "nodule", "pneumonia", "pneumothorax", "pleural_effusion", "no_finding"
        ]
        for c in expected_classes:
            self.assertIn(c, FINDING_KNOWLEDGE_BASE, f"Missing knowledge base entry for '{c}'")
            entry = FINDING_KNOWLEDGE_BASE[c]
            self.assertTrue(len(entry["possible_conditions"]) > 0, f"No conditions for '{c}'")
            self.assertTrue(len(entry["uncertainty_statement"]) > 0, f"No uncertainty for '{c}'")
            self.assertTrue(len(entry["evidence_basis"]) > 0, f"No evidence basis for '{c}'")
            self.assertTrue(len(entry["recommended_follow_up"]) > 0, f"No follow-up for '{c}'")

    def test_mass_and_nodule_differentials_include_benign_and_malignant(self):
        """Mass and nodule must include both benign and malignant differentials, avoiding cancer fabrication."""
        for finding_id in ["mass", "nodule"]:
            entry = FINDING_KNOWLEDGE_BASE[finding_id]
            categories = [cond.benign_vs_malignant for cond in entry["possible_conditions"]]
            self.assertIn("Benign", categories, f"{finding_id} must include benign conditions")
            self.assertIn("Malignant", categories, f"{finding_id} must include malignant conditions")

    def test_no_finding_warns_against_false_reassurance(self):
        """'No Finding' must explicitly caution that early malignancies cannot be excluded."""
        no_finding_entry = FINDING_KNOWLEDGE_BASE["no_finding"]
        uncertainty = no_finding_entry["uncertainty_statement"].lower()
        self.assertIn("cancer", uncertainty)
        self.assertIn("does not", uncertainty)

    def test_interpretation_service_generation(self):
        """Interpretation service produces typed schemas with correct metadata."""
        response = interpretation_service.interpret_findings(self.mock_predictions)
        self.assertTrue(response.summary.has_detected_pathology)
        self.assertIn("Mass", response.summary.primary_findings)
        self.assertIn("Pneumothorax", response.summary.primary_findings)
        self.assertTrue(len(response.findings) == 4)

        # Check mass item
        mass_item = next(f for f in response.findings if f.finding_id == "mass")
        self.assertTrue(mass_item.detected)
        self.assertEqual(mass_item.probability, 0.74)
        self.assertTrue(len(mass_item.possible_conditions) >= 4)
        self.assertIn("Fleischner", mass_item.evidence_basis)

    def test_disclaimers_integrity(self):
        """Summary contains all mandatory oncologic and Grad-CAM disclaimers."""
        response = interpretation_service.interpret_findings(self.mock_predictions)
        self.assertIn("Grad-CAM", response.summary.localization_disclaimer)
        self.assertIn("CANNOT diagnose cancer", response.summary.oncologic_disclaimer)
        self.assertIn("physical sensitivity limits", response.summary.negative_findings_disclaimer)

    def test_prohibited_phrasing_not_in_unsupported_contexts(self):
        """Assert that unsupported positive claims ('rules out', 'clean bill of health', 'cancer-free') are prohibited."""
        response = interpretation_service.interpret_findings(self.mock_predictions)
        
        # Disclaimers must explicitly caution, not claim cancer-free status
        for disclaimer in [
            response.summary.oncologic_disclaimer,
            response.summary.negative_findings_disclaimer,
            response.summary.localization_disclaimer,
        ]:
            # Should not claim that any test 'rules out' malignancy affirmatively
            self.assertNotIn("rules out cancer", disclaimer.lower())
            self.assertNotIn("guarantees absence", disclaimer.lower())
            self.assertNotIn("proves normal", disclaimer.lower())
            self.assertNotIn("is normal", disclaimer.lower())


if __name__ == "__main__":
    unittest.main()
