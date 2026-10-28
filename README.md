# CXR-Explain — Explainable Real-Time Chest X-Ray Disease Detection

> **Educational & Research Prototype · Not for Clinical Diagnostic Use**
>
> This is a college-level AI-assisted research and portfolio prototype. It is not evaluated by regulatory authorities and is not a substitute for professional radiological evaluation. Do not make medical decisions based on its outputs.

---

## 1. Project Overview

**CXR-Explain** is a full-stack, lightweight web application for multi-label chest radiograph pathology screening and explainability using deep learning (PyTorch DenseNet-121) and Grad-CAM (Gradient-Weighted Class Activation Mapping).

### Key Features
- **10 Thoracic Classes**: Evaluates Atelectasis, Cardiomegaly, Consolidation, Infiltration, Mass, Nodule, Pneumonia, Pneumothorax, Pleural Effusion, and No Finding.
- **Explainable AI (Grad-CAM)**: Visualizes localized thoracic activations using heatmaps and interactive side-by-side or blended radiograph overlays.
- **Dual Operating Modes**:
  - `demo`: Instant, deterministic simulation based on radiograph pixel statistics (no heavy dataset download or pre-trained weights required).
  - `real`: Loads a trained PyTorch DenseNet-121 `.pt` checkpoint to compute genuine neural network forward inference and Grad-CAM backpropagation.
- **Privacy First**: Stateless, ephemeral in-memory processing. No patient data or uploaded images are permanently stored.
- **Cross-IDE Compatibility**: Works seamlessly in both Visual Studio Code and Antigravity IDE using relative paths.

---

## 2. Technology Stack

- **Frontend**: React 19, TypeScript, Vite, Tailwind CSS v4, Lucide Icons.
- **Backend**: Python (3.11 or 3.12 compatible), FastAPI, Uvicorn, Pydantic v2.
- **Machine Learning**: PyTorch, torchvision, DenseNet-121, pandas, scikit-learn, OpenCV.

---

## 3. Project Directory Structure

```
Xray-main/
├── backend/
│   ├── api/
│   │   └── routes.py               # REST API endpoints (/health, /analyze, /explain, /report)
│   ├── config/
│   │   └── settings.py             # Server and ML environment configuration
│   ├── data/                       # Target directory for NIH ChestX-ray14 dataset
│   │   ├── Data_Entry_2017.csv     # (Place downloaded CSV here)
│   │   └── images/                 # (Extract downloaded PNG radiographs here)
│   ├── ml/
│   │   ├── base_model.py           # Base abstract class & inference dataclasses
│   │   ├── dataset.py              # PyTorch Dataset loader & patient-level disjoint splits
│   │   ├── demo_model.py           # Deterministic pixel-statistics simulation engine
│   │   ├── densenet121.py          # PyTorch DenseNet-121 wrapper with Grad-CAM hooks
│   │   ├── disease_labels.json     # Single source of truth for the 10 output classes
│   │   ├── evaluation.py           # Multi-label diagnostic metrics (AUROC, sensitivity, F1)
│   │   ├── factory.py              # Model loader switching between real & demo modes
│   │   ├── preprocessing_config.json # Canonical 224x224 standardization spec
│   │   ├── splits_manifest.json    # Patient-level partition ratio specifications
│   │   └── train.py                # DenseNet-121 multi-label training pipeline
│   ├── models/
│   │   └── weights/                # Saved model checkpoints (.pt)
│   ├── schemas/
│   │   └── analysis.py             # Pydantic v2 request/response schemas
│   ├── services/
│   │   └── analysis_service.py     # End-to-end analysis coordination service
│   ├── utils/
│   │   ├── preprocessing.py        # Image standardization & base64 utilities
│   │   └── validation.py           # Upload security & magic byte validation
│   ├── .env.example                # Backend environment configuration template
│   ├── requirements.txt            # Python dependencies (FastAPI + PyTorch)
│   └── main.py                     # FastAPI application entry point
├── frontend/
│   ├── src/
│   │   ├── components/             # Reusable UI components (viewer, list, disclaimer)
│   │   ├── pages/                  # LandingPage, AnalysisPage, ModelArchitecturePage
│   │   ├── services/               # API client service
│   │   ├── types/                  # TypeScript interface definitions
│   │   └── utils/                  # Medical formatters & 10-class constants
│   ├── package.json
│   ├── vite.config.ts
│   └── index.html
├── docs/                           # Architecture and decision documentation
├── .vscode/                        # VS Code / Antigravity workspace recommendations
├── .gitignore
└── README.md
```

---

## 4. Quick Start (Windows PowerShell)

### Step 4.1: Backend Setup

Open Windows PowerShell and navigate to the project directory:

```powershell
# 1. Navigate to inner repository directory (if extracted inside Xray-main)
cd "c:\Users\aditya singh\Downloads\Xray-main\Xray-main"

# 2. Navigate to backend
cd backend

# 3. Create a Python 3.11 or 3.12 virtual environment
py -3.12 -m venv .venv

# 4. Activate the virtual environment
.\.venv\Scripts\Activate.ps1

# 5. Install backend dependencies (FastAPI, PyTorch, torchvision, etc.)
pip install --upgrade pip
pip install -r requirements.txt

# 6. Create your local .env configuration file
Copy-Item .env.example .env

# 7. Start the FastAPI backend server
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

The backend API will be running at:
- **API URL**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive Documentation**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Health Check**: [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)

---

### Step 4.2: Frontend Setup

Open a **second** Windows PowerShell terminal:

```powershell
# 1. Navigate to frontend directory
cd "c:\Users\aditya singh\Downloads\Xray-main\Xray-main\frontend"

# 2. Install dependencies (using bun or npm)
bun install
# (or: npm install)

# 3. Start Vite development server
bun run dev
# (or: npm run dev)
```

The user interface will be live at:
- **Web App**: [http://localhost:5173](http://localhost:5173)

---

## 5. Dataset Setup Guide (NIH ChestX-ray14)

The project is designed to run immediately in **Demo Mode** without requiring the dataset. When your download of the **NIH ChestX-ray14** dataset finishes, follow these steps to prepare for model training:

### Files to Place

| Dataset File / Folder | Destination Path | Description |
|---|---|---|
| `Data_Entry_2017.csv` (or `Data_Entry_2017_v2020.csv`) | `backend/data/Data_Entry_2017.csv` | Official NIH metadata table containing `Image Index`, `Finding Labels`, and `Patient ID` |
| Image archives (`images_001.tar.gz`, etc.) | `backend/data/images/` | Extracted 1024x1024 radiograph PNG files (e.g. `00000001_000.png`) |

### Starting Model Training

Once the files are in place, activate your backend virtual environment and execute:

```powershell
cd "c:\Users\aditya singh\Downloads\Xray-main\Xray-main"
.\backend\.venv\Scripts\Activate.ps1

# Run training pipeline (configurable epochs and batch size)
python backend/ml/train.py --csv-path backend/data/Data_Entry_2017.csv --img-dir backend/data/images --epochs 5 --batch-size 16
```

### What `train.py` Does:
1. Validates that the metadata CSV and image folder exist.
2. Reads the 10 target disease classes from `backend/ml/disease_labels.json`.
3. Performs a **patient-level disjoint split** (70% train, 10% validation, 20% test) to prevent patient data leakage across partitions.
4. Normalizes images to 224x224 with ImageNet statistics.
5. Optimizes a DenseNet-121 multi-label classifier using `BCEWithLogitsLoss`.
6. Evaluates validation AUROC after each epoch and saves the best model checkpoint to `backend/models/weights/densenet121_cxr.pt`.
7. Evaluates the best checkpoint once on the held-out test partition and outputs a diagnostic performance report.

### Switching to Real Model Mode
To serve the newly trained model in the web application, edit `backend/.env`:
```ini
MODEL_MODE=real
MODEL_PATH=models/weights/densenet121_cxr.pt
```
Restart the backend server. The application will now execute real DenseNet-121 inference and real Grad-CAM backpropagation!

---

## 6. The 10 Target Thoracic Classes

The class-to-index mapping is maintained in `backend/ml/disease_labels.json`:

1. **Atelectasis** (Collapse of alveolar units)
2. **Cardiomegaly** (Enlargement of cardiac silhouette)
3. **Consolidation** (Alveolar airspace opacification)
4. **Infiltration** (Parenchymal fluid or cellular exudate)
5. **Mass** (Lesion greater than 3 cm)
6. **Nodule** (Rounded opacity less than 3 cm)
7. **Pneumonia** (Infectious parenchymal consolidation)
8. **Pneumothorax** (Gas in pleural cavity)
9. **Pleural Effusion** (Fluid in pleural space)
10. **No Finding** (Unremarkable radiograph screening)

---

## 7. Demo Mode vs. Real Mode

| Feature | Demo Mode (`MODEL_MODE=demo`) | Real Mode (`MODEL_MODE=real`) |
|---|---|---|
| **Weights Required** | None | Trained PyTorch checkpoint (`.pt`) |
| **Prediction Source** | Deterministic image pixel statistics | DenseNet-121 neural forward pass |
| **Grad-CAM Source** | Anatomically aligned focal gradient | Convolutional gradient backpropagation |
| **Fallback Safety** | Active by default | Automatically falls back to Demo mode if checkpoint is missing |
| **UI Indication** | Clearly labeled as `Demo Mode (Simulated / Prototype)` | Labeled as `DenseNet-121 (Trained Checkpoint)` |

---

## 8. Verification & Architectural Testing

Run the automated pre-training architectural validator:

```powershell
python backend/ml/validate_pretraining_strategy.py
```

Expected output:
```
[PASS] 10-Class Single Source of Truth Validation
[PASS] Frozen Patient-Level Disjoint Splits Manifest Validation
[PASS] Canonical Baseline Preprocessing Specification Validation

ALL PRE-TRAINING ARCHITECTURAL ASSERTIONS PASSED!
```

---

## 9. Disclaimer

This software is an **academic educational prototype**. It has not been clinically validated or evaluated for regulatory compliance. It must **never** be used as a primary diagnostic tool, for clinical triage, or for guiding patient treatment.
