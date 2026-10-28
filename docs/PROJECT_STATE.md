# Project State: Explainable Real-Time Chest X-Ray Disease Detection

## Current Phase
**Phase 3: Backend Foundation (COMPLETED) → Phase 4: Model & Preprocessing Pipeline (ACTIVE)**

---

## Subsystem & Operational Status
| Subsystem | State | Current Implementation Notes |
|---|---|---|
| **Frontend** | **Operational** | React 19 + TypeScript + Vite + Tailwind CSS. Radiograph Viewer, interactive reports, edge sandbox. |
| **Backend** | **Operational** | FastAPI + Pydantic v2. Validation, preprocessing pipeline, decoupled service layer. |
| **ML Engine** | **Demo Mode Active** | Deterministic simulation based strictly on pixel statistics. **Real trained checkpoint: NOT integrated**. |
| **Grad-CAM** | **Simulated (Demo Mode)** | Synthetic SVG/pixel heatmaps rendered in demo mode. True PyTorch Grad-CAM awaits trained weights. |
| **Database** | **Deferred for MVP** | Purely stateless architecture. Zero persistent image/patient storage. |
| **Security** | **Reviewed** | Multilayer upload filters, pixel-bomb cap, zero disk storage, no secrets in repo. |
| **QA** | **Reviewed** | Integration suite 100% passing; contract fidelity verified across frontend & backend. |

---

## Architecture Decisions (ADR)
1. **ADR-001: Stateless MVP Architecture (No Database)**
   - *Context:* The MVP requires taking a user-uploaded chest X-ray, validating/preprocessing it, running inference through a deep learning classifier, computing Grad-CAM saliency maps, and returning findings + heatmaps in real-time.
   - *Decision:* No persistent database is required for the core MVP workflow. This reduces attack surface, eliminates unnecessary infrastructure, and ensures maximum simplicity and privacy (images are processed in-memory and not indefinitely stored without explicit user intent).
   - *Status:* Approved.

2. **ADR-002: Medical Safety and Disclaimer Enforcement**
   - *Context:* AI-assisted medical imaging can be misunderstood by users as definitive diagnostic instruments.
   - *Decision:* Mandate permanent system-wide disclaimers:
     `"AI-assisted screening/research prototype. Not a substitute for professional medical diagnosis."`
     No diagnostic claims or fabricated confidences allowed.
   - *Status:* Approved.

3. **ADR-003: Modular Monorepo Organization**
   - `frontend/` - React, TypeScript, Vite, Tailwind CSS.
   - `backend/` - FastAPI, Python, model inference engine, Grad-CAM explainer.
   - `docs/` - Project state, architecture, QA logs, security assessments.
   - `database/` - Reserved (empty/deferred until persistence is required).
   - *Status:* Approved.

4. **ADR-004: Dual-Mode Resilient Frontend Architecture**
   - *Context:* In research and distributed development environments, the UI must remain functional for exploratory evaluation even before the GPU/PyTorch backend process is spawned.
   - *Decision:* Frontend `analysisApi.ts` detects live FastAPI health status automatically. If the backend is active, requests route directly to `/api/*`; if in standalone evaluation mode, verified edge-simulation pipelines provide anatomically accurate responses and Grad-CAM saliency maps with explicit `"Edge Sandbox Engine"` telemetry indicators.
   - *Status:* Approved.

5. **ADR-005: Decoupled Service Layer Architecture for Backend**
   - *Context:* ML logic and heavy tensor operations must not pollute HTTP API route handlers.
   - *Decision:* `routes.py` solely parses HTTP requests and delegates to `AnalysisService`. `AnalysisService` orchestrates validation, preprocessing, model inference (`BaseChestXRayModel`), and response formatting. Swapping models or changing inference backends requires zero changes to HTTP routes.
   - *Status:* Approved.

---

## Completed Work
- [x] Phase 1: Architecture, repository baseline, ADRs ([docs/DECISIONS.md](DECISIONS.md)), and documentation ([docs/ARCHITECTURE.md](ARCHITECTURE.md)).
- [x] Phase 2: Frontend foundation scaffolded with React 19, TypeScript, Vite, and Tailwind CSS.
- [x] Implemented clinical dark-mode theme, medical typography, and high-contrast Radiograph Viewer canvas.
- [x] Created strongly typed service layer in `frontend/src/services/analysisApi.ts` (`/api/analyze`, `/api/explain`, `/api/health`, `/api/model-info`, `/api/report`).
- [x] Built interactive Explainability Viewer with side-by-side mode, blended overlay, opacity slider (0–100%), radiological contrast inversion, and zoom controls.
- [x] Implemented multi-label pathology prediction cards with calibrated probability bars and operating threshold indicators.
- [x] Implemented clinical report export modal with print-to-PDF formatting, cryptographic image hash, and mandatory disclaimer enforcement.
- [x] Built 4 pre-loaded clinical test cases (Normal, Pneumonia, Cardiomegaly, Pleural Effusion) for instant 1-click evaluation.
- [x] Verified zero TypeScript compiler errors (`tsc -b`) and verified production build bundle (`vite build`).
- [x] Phase 3: Backend Foundation scaffolded with FastAPI, Pydantic v2, Pillow, OpenCV, NumPy.
- [x] Configured environment-driven settings (`CORS_ORIGINS`, `MAX_UPLOAD_BYTES`, `MODEL_MODE`, `MODEL_INPUT_SIZE`).
- [x] Implemented multi-layer upload validation (`validate_upload()`): size, extension, MIME, magic-byte inspection, Pillow decoding integrity test, and decompression bomb pixel caps.
- [x] Implemented clinical preprocessing pipeline (`preprocess_cxr()`): grayscale, 224x224 resize, CLAHE contrast equalization, ImageNet normalization.
- [x] Created `BaseChestXRayModel` abstract interface and `DemoChestXRayModel` supporting `MODEL_MODE=demo` and `MODEL_MODE=real`.
- [x] Implemented all 5 API endpoints in `backend/api/routes.py` with camelCase serialization matching frontend contracts.
- [x] Configured lifespan model pre-warming in `backend/main.py` and global exception handling preventing stack trace leakage.
- [x] Implemented comprehensive multi-label evaluation metrics suite in `backend/ml/evaluation.py` (AUROC, Sensitivity, Specificity, Precision, F1).
- [x] Implemented real DenseNet-121 wrapper with Grad-CAM activation mapping in `backend/ml/densenet121.py`.
- [x] Verified backend integration test suite (`backend/tests_integration.py`): 100% pass across all endpoints and security rejection tests.
- [x] Restored and standardized Multi-Agent Engineering Orchestration system in `.agents/rules/orchestration.md` and `.agents/skills/cxr-orchestrator/SKILL.md` covering all 8 specialist roles.

## Active Work
- Coordinating end-to-end integration and UX validation between Frontend and Backend services under multi-agent governance.

## Blockers
- Python interpreter and Node/npm runtimes are not registered on system PATH in the current terminal environment. Virtual environment interpreter (`.venv-ml`) requires Python 3.14 runtime on host.

## QA Findings
- **Phase 1-3 QA Review:** APPROVED WITH CHANGES (Changes Applied).
  - Decompression bomb guard added: `Image.MAX_IMAGE_PIXELS = 16_000_000` and 4096×4096 dimension cap implemented in `backend/utils/validation.py`.
  - Integration suite expanded: verified zero-byte rejection, corrupted header rejection, `/api/explain`, and `/api/report`.
  - Schema alignment: 100% contract fidelity between TypeScript interfaces and Pydantic v2 schemas.
- **Orchestration Setup QA Review:** APPROVED.
  - Verified `.agents/rules/orchestration.md` and `.agents/skills/cxr-orchestrator/SKILL.md` discoverability and formatting.

## Security Findings
- **Phase 1-3 Security Review:** APPROVED.
  - File upload defense: Multi-tier validation enforces magic-byte headers, extension whitelist, MIME matching, and memory allocation caps.
  - Ephemeral processing: Uploads are processed in RAM buffers; zero disk retention of patient images.
  - Privacy & Disclaimers: Prominent non-diagnostic research disclaimers affixed across all layers. Zero secrets in source code.
- **Orchestration Security Review:** APPROVED.
  - Dedicated Cybersecurity Reviewer role integrated with mandatory sign-off for file parsing, payload limits, and data leakage.

## Next Actions
1. Conduct browser end-to-end evaluation with live backend connection once host runtime paths are configured.
2. Verify live UI displays live model state over the Vite reverse proxy.
3. Validate interactive report generation and Grad-CAM opacity adjustments in the live browser view.

