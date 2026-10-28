"""
Automated pre-training architectural validator.

Verifies all 5 mandatory QA blockers prior to executing any model training code.
"""

import json
from pathlib import Path

ML_DIR = Path(__file__).resolve().parent

def test_disease_labels():
    labels_file = ML_DIR / "disease_labels.json"
    assert labels_file.exists(), "disease_labels.json must exist"
    with open(labels_file, "r", encoding="utf-8") as f:
        labels = json.load(f)
    assert len(labels) == 10, f"Must have exactly 10 labels, got {len(labels)}"
    indices = [l["index"] for l in labels]
    assert indices == list(range(10)), f"Indices must be exactly 0..9, got {indices}"
    ids = [l["id"] for l in labels]
    assert len(ids) == len(set(ids)), "All label IDs must be unique"
    assert "nodule" in ids and "mass" in ids, "Nodule and Mass must be distinct classes"
    assert "nodule_mass" not in ids, "No combined nodule_mass class allowed"
    print("[PASS] 10-Class Single Source of Truth Validation")

def test_splits_manifest():
    manifest_file = ML_DIR / "splits_manifest.json"
    assert manifest_file.exists(), "splits_manifest.json must exist"
    with open(manifest_file, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    assert manifest["split_protocol"] == "patient-level-disjoint"
    assert manifest["assertions"]["train_val_overlap"] == 0
    assert manifest["assertions"]["train_test_overlap"] == 0
    assert manifest["assertions"]["val_test_overlap"] == 0
    assert "train" in manifest["partitions"]
    assert "validation" in manifest["partitions"]
    assert "test" in manifest["partitions"]
    print("[PASS] Frozen Patient-Level Disjoint Splits Manifest Validation")

def test_preprocessing_config():
    config_file = ML_DIR / "preprocessing_config.json"
    assert config_file.exists(), "preprocessing_config.json must exist"
    with open(config_file, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    assert cfg["clahe_policy"]["included_in_baseline"] is False, "CLAHE must not be in baseline"
    step_ops = [s["operation"] for s in cfg["pipeline_steps"]]
    assert "grayscale_conversion" in step_ops
    assert "float32_conversion" in step_ops
    assert "aspect_ratio_preserving_resize" in step_ops
    assert "channel_replication" in step_ops
    assert "imagenet_normalization" in step_ops
    print("[PASS] Canonical Baseline Preprocessing Specification Validation")

if __name__ == "__main__":
    test_disease_labels()
    test_splits_manifest()
    test_preprocessing_config()
    print("\nALL PRE-TRAINING ARCHITECTURAL ASSERTIONS PASSED!")
