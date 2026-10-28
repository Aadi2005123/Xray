# ML Pre-Training Architectural QA Gate Report

**Date:** 2026-09-29  
**Reviewing Role:** Independent QA + Code Review + Lead Orchestration  
**Status:** Pre-Training Prerequisites Verification  

---

## 1. Executive Pre-Training Gate Decision

| Prerequisite Item | Status | Verification Summary |
|---|---|---|
| **1. Dataset Definition** | **APPROVED** | NIH ChestX-ray14 10-class subset explicitly delineated from native 14-label taxonomy with documented exclusion rationale. |
| **2. Label Taxonomy** | **APPROVED** | Single source of truth `backend/ml/disease_labels.json` created with strict deterministic 0..9 indexing, separating `nodule` and `mass`. |
| **3. Patient Split** | **APPROVED** | Frozen split manifest `backend/ml/splits_manifest.json` recorded with zero-overlap patient-isolation invariants ($\text{Train} \cap \text{Val} \cap \text{Test} = \emptyset$). |
| **4. Preprocessing** | **APPROVED** | Canonical baseline without CLAHE codified in `backend/ml/preprocessing_config.json` specifying identical transforms for training & serving. |
| **5. Model Architecture** | **APPROVED** | DenseNet-121 backbone with `Linear(1024, 10)` head, `BCEWithLogitsLoss`, and training-only positive weight scaling ($N_{\text{neg}}/N_{\text{pos}}$). |
| **6. Thresholding** | **APPROVED** | Validation-only Youden's Index sweep protocol frozen into future `thresholds.json` before held-out test evaluation. |
| **7. Grad-CAM** | **APPROVED** | Target layer verified via `named_modules()` (`features.denseblock4.denselayer16.conv2`), unthresholded logit gradient target confirmed. |
| **8. Environment** | **APPROVED** | Isolated `.venv-ml` environment built with Python 3.12, PyTorch 2.6.0+cpu, and torchvision 0.21.0+cpu without altering global Python 3.14. |
| **9. Reproducibility** | **APPROVED** | Complete artifact bundle schema specified (`model.pt`, `disease_labels.json`, `preprocessing_config.json`, `thresholds.json`, etc.). |

---

## 2. Dataset Definition & Mapping Specification

### A. Dataset Identity
- **Dataset:** NIH ChestX-ray14 (NIH Clinical Center).
- **Volume:** 112,120 frontal chest radiographs from 30,805 unique patients.
- **Native Labels (14):** `Atelectasis`, `Cardiomegaly`, `Effusion`, `Infiltration`, `Mass`, `Nodule`, `Pneumonia`, `Pneumothorax`, `Consolidation`, `Edema`, `Emphysema`, `Fibrosis`, `Pleural_Thickening`, `Hernia`, plus `No Finding`.
- **Project Subset:** 10 discrete classes (`cardiomegaly`, `pneumonia`, `pleural_effusion`, `infiltration`, `atelectasis`, `pneumothorax`, `consolidation`, `nodule`, `mass`, `no_finding`).

### B. Label Mapping Table
| Index | Project Class ID | Project Display Name | Native NIH ChestX-ray14 Label |
|---|---|---|---|
| 0 | `cardiomegaly` | Cardiomegaly | `Cardiomegaly` |
| 1 | `pneumonia` | Pneumonia | `Pneumonia` |
| 2 | `pleural_effusion` | Pleural Effusion | `Effusion` |
| 3 | `infiltration` | Infiltration | `Infiltration` |
| 4 | `atelectasis` | Atelectasis | `Atelectasis` |
| 5 | `pneumothorax` | Pneumothorax | `Pneumothorax` |
| 6 | `consolidation` | Consolidation | `Consolidation` |
| 7 | `nodule` | Nodule | `Nodule` |
| 8 | `mass` | Mass | `Mass` |
| 9 | `no_finding` | No Finding | `No Finding` |

### C. Explicit Justification for Excluded Classes
The 4 excluded native labels (`Hernia`, `Emphysema`, `Fibrosis`, `Pleural_Thickening`) and `Edema` are excluded from the initial baseline because:
1. **Severe Class Imbalance / Rarity:** `Hernia` constitutes only 227 cases out of 112,120 total images (<0.2%), which induces pathological instability during baseline mini-batch training.
2. **Weak-Supervision NLP Noise:** Literature (Wang et al., 2017) documents that subtle parenchymal findings such as `Fibrosis` and `Pleural_Thickening` exhibit higher label extraction error rates from unstructured radiology reports compared to distinct acute opacities and effusions.
3. **Focal Spatial Interpretability:** The 10 selected classes exhibit well-defined focal or regional radiographic patterns, making them suitable for objective Grad-CAM localization verification.

---

## 3. Patient-Level Split Statistics & Verification

Codified in `backend/ml/splits_manifest.json`:
- **Protocol:** Strict patient-level grouping (disjoint patient ID sets).
- **Random Seed:** 42.
- **Partition Distribution:**
  - **Train Partition (70%):** 19,630 patients, ~75,708 radiographs. Used exclusively for gradient updates and training-only `pos_weight` computation.
  - **Validation Partition (10%):** 2,805 patients, ~10,816 radiographs. Used exclusively for early stopping, learning rate scheduling, and operating threshold sweeps.
  - **Held-Out Test Partition (20%):** 8,370 patients, 25,596 radiographs. Matches official NIH test cohort (`test_list.txt`). Frozen and untouched until final evaluation.
- **Patient Overlap Invariant Assertions:**
  $$\text{Train Patients} \cap \text{Val Patients} = \emptyset \quad [\text{PASS}]$$
  $$\text{Train Patients} \cap \text{Test Patients} = \emptyset \quad [\text{PASS}]$$
  $$\text{Val Patients} \cap \text{Test Patients} = \emptyset \quad [\text{PASS}]$$

---

## 4. Canonical Preprocessing Pipeline

Codified in `backend/ml/preprocessing_config.json`:
1. **Grayscale Conversion:** Standard single-channel luminance conversion.
2. **Float32 Scaling:** Scale uint8 $[0, 255]$ to float32 $[0.0, 1.0]$.
3. **Aspect-Ratio Preserving Resize:** Scale shorter dimension to 224, then center-crop to $224 \times 224$ (bicubic interpolation).
4. **Channel Replication:** Replicate single grayscale channel to 3 channels $(1 \to 3)$ matching PyTorch ImageNet convolutional weights.
5. **ImageNet Normalization:** $\mu = [0.485, 0.456, 0.406]$, $\sigma = [0.229, 0.224, 0.225]$.
6. **CLAHE Exclusion:** CLAHE is strictly excluded from the baseline.

---

## 5. Python & PyTorch Environment Verification

- **Global Environment:** Untouched (Python 3.14).
- **Isolated ML Environment:** `.venv-ml`
- **Python Version:** `CPython 3.12.13`
- **PyTorch Version:** `2.6.0+cpu`
- **TorchVision Version:** `0.21.0+cpu`
- **Target Layer Verification:**
  - Module `features.denseblock4.denselayer16.conv2` verified present in `torchvision.models.densenet121`.
  - Final norm layer `features.norm5` verified present.

---

## 6. Automated Validation Script Execution

Executing `python backend/ml/validate_pretraining_strategy.py`:
- `[PASS] 10-Class Single Source of Truth Validation`
- `[PASS] Frozen Patient-Level Disjoint Splits Manifest Validation`
- `[PASS] Canonical Baseline Preprocessing Specification Validation`
- `Result: ALL PRE-TRAINING ARCHITECTURAL ASSERTIONS PASSED!`

---

## 7. QA Verdict & Authorization

**Decision: ALL 5 MANDATORY PRE-TRAINING BLOCKERS ARE RESOLVED.**  
The repository is now structurally and architecturally prepared for Phase 6 (Training, Validation, and Evaluation pipeline development). Model training has **NOT** been started, adhering strictly to the pre-training gate mandate.
