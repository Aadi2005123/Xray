# Architecture Decision Records (ADRs)

Project: Explainable Real-Time Chest X-Ray Disease Detection using Deep Learning

---

## ADR-001: Stateless MVP Architecture (No Database)
- **Status:** Approved
- **Context:** The system screens chest X-rays by uploading an image, performing preprocessing, running inference, computing Grad-CAM heatmaps, and presenting results in real-time.
- **Decision:** No persistent database is required for the initial MVP. Image uploads are processed strictly in-memory and discarded upon completion of the HTTP response lifecycle.
- **Consequences:** Eliminates storage overhead, simplifies infrastructure, and reduces data-at-rest exposure risk (this project has not been formally evaluated for regulatory compliance). If user accounts or historical cohorts are needed in future phases, a lightweight relational DB (SQLite locally, PostgreSQL in production) will be evaluated.

---

## ADR-002: Medical Safety & Non-Diagnostic Disclaimer Enforcement
- **Status:** Approved
- **Context:** Deep learning classifications are probabilistic likelihoods and must never be misrepresented as definitive medical diagnoses.
- **Decision:** Mandate system-wide disclaimer on all UI views and API payloads:
  `"AI-assisted screening/research prototype. Not a substitute for professional medical diagnosis."`
- **Consequences:** Prohibits diagnostic certainty terms ("confirmed diagnosis", "patient definitely has"). All findings are presented with calibrated probability ranges and operating sensitivity thresholds.

---

## ADR-003: Monorepo Structure & Separation of Concerns
- **Status:** Approved
- **Context:** A cohesive full-stack codebase is required while maintaining strict boundary separation across disciplines.
- **Decision:**
  - `frontend/`: React 19 + TypeScript + Vite + Tailwind CSS
  - `backend/`: FastAPI + Pydantic v2 + Pillow + OpenCV + NumPy + PyTorch
  - `docs/`: Architecture diagrams, decision records, project state, QA/security reports
- **Consequences:** Allows independent testing and build pipelines for frontend and backend while maintaining contract alignment.

---

## ADR-004: Dual-Mode Resilient Frontend Architecture
- **Status:** Approved
- **Context:** In research environments or initial front-end testing, the backend server or GPU cluster may be offline or initializing.
- **Decision:** The frontend API service (`analysisApi.ts`) continuously queries `/api/health`. When the backend is online, requests route directly to the FastAPI server. If offline, the UI falls back gracefully to a high-fidelity client-side sandbox engine, explicitly tagged with `"isSimulatedFallback": true`.
- **Consequences:** Ensures zero developer downtime during frontend UX evaluations while making simulation status completely transparent.

---

## ADR-005: Decoupled Service Layer for ML Inference
- **Status:** Approved
- **Context:** Machine learning logic, tensor transformations, and Grad-CAM backpropagation must not be embedded directly inside HTTP route handlers.
- **Decision:** API routes (`backend/api/routes.py`) only parse and validate HTTP requests, delegating to `AnalysisService` (`backend/services/analysis_service.py`), which calls `BaseChestXRayModel` abstractions.
- **Consequences:** Allows backend models (DenseNet121, ResNet50, EfficientNet, ConvNeXt) or execution modes (`MODEL_MODE=real` vs. `MODEL_MODE=demo`) to be swapped without changing API contracts or route definitions.

---

## ADR-006: Multi-Tier Upload Validation & Pixel Flood Protection
- **Status:** Approved
- **Context:** Medical image upload endpoints are vulnerable to polyglot file attacks, corrupt byte streams, and decompression bombs.
- **Decision:** Validate file size (≤ 10MB), file extension whitelist, MIME header whitelist, magic-byte header inspection (PNG, JPEG, WebP), and set `Image.MAX_IMAGE_PIXELS = 16_000_000` with a $4096 \times 4096$ dimension ceiling.
- **Consequences:** Completely blocks pixel-flood DoS exploits and rejects malicious or corrupted payloads before tensor memory allocation.
