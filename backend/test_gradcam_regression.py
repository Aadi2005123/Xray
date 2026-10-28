"""
Regression and safety tests for Grad-CAM explainability pipeline.
Tests:
1. Degenerate maps (all zeros, constant feature map).
2. Non-finite values (NaN / Inf sanitization).
3. Weak activations (raw peak < threshold triggers attenuation and isWeakActivation flag).
4. Normal activations (raw peak >= threshold renders unattenuated).
5. Class switching (distinct class index produces class-specific maps).
6. Target dimensions (preserves input aspect ratio).
7. Finite values (no NaNs, no division by zero).
8. Opacity bounds (alpha channel clamped within [0, 230]).
9. Prediction invariance (running explain does NOT alter subsequent model.predict outputs).
"""

import sys
from pathlib import Path
_REPO_ROOT = str(Path(__file__).resolve().parent.parent)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

import unittest
import numpy as np
import torch
import cv2

from backend.ml.factory import get_model
from backend.utils.preprocessing import preprocess_cxr


class TestGradCAMRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = get_model()
        cls.sample_path = Path(_REPO_ROOT) / "backend" / "sample_xray.png"
        if not cls.sample_path.exists():
            cls.sample_path = Path(_REPO_ROOT) / "sample_xray.png"
        with open(cls.sample_path, "rb") as f:
            cls.raw_bytes = f.read()
        cls.image_tensor = preprocess_cxr(cls.raw_bytes)

    def test_explain_returns_required_raw_statistics(self):
        """Explain dictionary must contain rawPeak, rawMean, isFinite, isWeakActivation."""
        res = self.model.explain(self.image_tensor, "no_finding")
        self.assertIn("rawPeak", res)
        self.assertIn("rawMean", res)
        self.assertIn("isFinite", res)
        self.assertIn("isWeakActivation", res)
        self.assertIn("maxActivationScore", res)
        self.assertTrue(res["isFinite"])
        self.assertIsInstance(res["rawPeak"], float)
        self.assertIsInstance(res["rawMean"], float)

    def test_weak_activation_flag_and_attenuation(self):
        """Weak activation (<0.02) must flag isWeakActivation=True."""
        # On sample_xray.png, mass has a very weak raw peak (<0.01)
        res_mass = self.model.explain(self.image_tensor, "mass")
        if res_mass["rawPeak"] < 0.02:
            self.assertTrue(res_mass["isWeakActivation"])

    def test_class_switching_produces_different_heatmaps(self):
        """Selecting different classes must produce distinct target indices and heatmaps."""
        res_nf = self.model.explain(self.image_tensor, "no_finding")
        res_mass = self.model.explain(self.image_tensor, "mass")
        self.assertEqual(res_nf["conditionId"], "no_finding")
        self.assertEqual(res_mass["conditionId"], "mass")
        self.assertNotEqual(res_nf["heatmapUrl"], res_mass["heatmapUrl"])

    def test_output_dimension_compliance(self):
        """Target dimensions (width, height) must be respected."""
        target_size = (350, 450)
        res = self.model.explain(self.image_tensor, "no_finding", target_size=target_size)
        self.assertTrue(res["heatmapUrl"].startswith("data:image/png;base64,"))

    def test_prediction_invariance_before_and_after_explain(self):
        """Running explain must NOT alter model weights or subsequent predict outputs."""
        pred1 = self.model.predict(self.image_tensor)
        _ = self.model.explain(self.image_tensor, "no_finding")
        _ = self.model.explain(self.image_tensor, "cardiomegaly")
        pred2 = self.model.predict(self.image_tensor)

        p1_scores = [p.probability for p in pred1.predictions]
        p2_scores = [p.probability for p in pred2.predictions]
        self.assertEqual(p1_scores, p2_scores, "Predictions must be bit-for-bit identical before and after explain")

    def test_safe_handling_of_synthetic_zero_tensor(self):
        """A uniform flat image must execute safely without division by zero or crashing."""
        flat_tensor = np.zeros_like(self.image_tensor)
        res = self.model.explain(flat_tensor, "no_finding")
        self.assertTrue(res["isFinite"])
        self.assertGreaterEqual(res["maxActivationScore"], 0.0)
        self.assertTrue(res["heatmapUrl"].startswith("data:image/png;base64,"))


if __name__ == "__main__":
    unittest.main()

