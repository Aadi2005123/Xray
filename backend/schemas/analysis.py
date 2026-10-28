"""
Pydantic response/request schemas matching the frontend TypeScript contracts.
"""

from pydantic import BaseModel, Field


# ── Health ────────────────────────────────────────────────────────────
class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "1.0.0"
    device: str = "cpu"
    model_loaded: bool = Field(alias="modelLoaded", default=False)

    model_config = {"populate_by_name": True}


# ── Model metadata ───────────────────────────────────────────────────
class ModelInfoResponse(BaseModel):
    name: str
    version: str
    architecture: str
    dataset: str
    input_dimensions: str = Field(alias="inputDimensions")
    benchmark_auroc_mean: float | None = Field(default=None, alias="benchmarkAurocMean")
    benchmark_status: str | None = Field(default=None, alias="benchmarkStatus")
    last_updated: str = Field(alias="lastUpdated")
    supported_classes: list[str] = Field(alias="supportedClasses")

    model_config = {"populate_by_name": True}


# ── Prediction ────────────────────────────────────────────────────────
class PathologyPredictionSchema(BaseModel):
    id: str
    name: str
    probability: float
    severity: str
    threshold: float
    detected: bool
    description: str
    anatomical_region: str = Field(alias="anatomicalRegion")
    clinical_significance: str = Field(alias="clinicalSignificance")

    model_config = {"populate_by_name": True}


# ── Heatmap ───────────────────────────────────────────────────────────
class HeatmapDataSchema(BaseModel):
    condition_id: str = Field(alias="conditionId")
    condition_name: str = Field(alias="conditionName")
    heatmap_url: str = Field(alias="heatmapUrl")
    overlay_url: str = Field(alias="overlayUrl")
    max_activation_score: float = Field(alias="maxActivationScore")
    raw_peak: float | None = Field(default=None, alias="rawPeak")
    raw_mean: float | None = Field(default=None, alias="rawMean")
    is_finite: bool = Field(default=True, alias="isFinite")
    is_weak_activation: bool = Field(default=False, alias="isWeakActivation")
    target_layer: str = Field(alias="targetLayer")

    model_config = {"populate_by_name": True}


# ── Finding-Based Disease Interpretation Schemas ─────────────────────
class ConditionInterpretationItem(BaseModel):
    condition_name: str = Field(alias="conditionName")
    likelihood_category: str = Field(alias="likelihoodCategory")
    pathophysiology: str
    clinical_context: str = Field(alias="clinicalContext")
    benign_vs_malignant: str = Field(alias="benignVsMalignant")

    model_config = {"populate_by_name": True}


class FindingInterpretation(BaseModel):
    finding_id: str = Field(alias="findingId")
    finding_name: str = Field(alias="findingName")
    probability: float
    threshold: float
    detected: bool
    severity: str
    size_definition: str = Field(alias="sizeDefinition")
    possible_conditions: list[ConditionInterpretationItem] = Field(alias="possibleConditions")
    uncertainty_statement: str = Field(alias="uncertaintyStatement")
    diagnostic_limitations: str = Field(alias="diagnosticLimitations")
    evidence_basis: str = Field(alias="evidenceBasis")
    recommended_follow_up: str = Field(alias="recommendedFollowUp")

    model_config = {"populate_by_name": True}


class OverallInterpretationSummary(BaseModel):
    primary_findings: list[str] = Field(alias="primaryFindings")
    secondary_findings: list[str] = Field(alias="secondaryFindings")
    has_detected_pathology: bool = Field(alias="hasDetectedPathology")
    negative_findings_disclaimer: str = Field(alias="negativeFindingsDisclaimer")
    oncologic_disclaimer: str = Field(alias="oncologicDisclaimer")
    localization_disclaimer: str = Field(alias="localizationDisclaimer")

    model_config = {"populate_by_name": True}


class ClinicalInterpretationResponse(BaseModel):
    summary: OverallInterpretationSummary
    findings: list[FindingInterpretation]

    model_config = {"populate_by_name": True}


# ── Full analysis result ──────────────────────────────────────────────
class AnalysisResultResponse(BaseModel):
    analysis_id: str = Field(alias="analysisId")
    timestamp: str
    original_image: str = Field(alias="originalImage")
    file_name: str = Field(alias="fileName")
    file_size_bytes: int = Field(alias="fileSizeBytes")
    image_dimensions: dict = Field(alias="imageDimensions")
    image_hash_sha256: str = Field(alias="imageHashSha256")
    execution_time_ms: float = Field(alias="executionTimeMs")
    predictions: list[PathologyPredictionSchema]
    top_finding: PathologyPredictionSchema | None = Field(alias="topFinding")
    heatmaps: dict[str, HeatmapDataSchema]
    clinical_summary: str = Field(alias="clinicalSummary")
    is_simulated_fallback: bool = Field(default=False, alias="isSimulatedFallback")
    finding_interpretation: ClinicalInterpretationResponse | None = Field(
        default=None, alias="findingInterpretation"
    )

    model_config = {"populate_by_name": True}


# ── Interpret request ────────────────────────────────────────────────
class InterpretRequest(BaseModel):
    analysis_id: str = Field(alias="analysisId")

    model_config = {"populate_by_name": True}


# ── Explain request ──────────────────────────────────────────────────
class ExplainRequest(BaseModel):
    analysis_id: str = Field(alias="analysisId")
    condition_id: str = Field(alias="conditionId")

    model_config = {"populate_by_name": True}


# ── Report request ───────────────────────────────────────────────────
class ReportRequest(BaseModel):
    patient_pseudonym: str = Field(alias="patientPseudonym")
    study_id: str = Field(alias="studyId")
    study_date: str = Field(alias="studyDate")
    clinician_notes: str | None = Field(default=None, alias="clinicianNotes")
    # analysis_result is passed as a dict to avoid circular nesting complexity
    analysis_result: dict = Field(alias="analysisResult")

    model_config = {"populate_by_name": True}


class ReportResponse(BaseModel):
    success: bool = True
    report_url: str | None = Field(default=None, alias="reportUrl")

    model_config = {"populate_by_name": True}


# ── Generic error ─────────────────────────────────────────────────────
class ErrorResponse(BaseModel):
    detail: str
