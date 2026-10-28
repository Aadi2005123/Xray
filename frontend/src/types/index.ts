export type SeverityLevel = 'normal' | 'low' | 'moderate' | 'high';

export interface PathologyPrediction {
  id: string;
  name: string;
  probability: number; // 0.0 to 1.0
  severity: SeverityLevel;
  threshold: number; // Clinical operating threshold
  detected: boolean;
  description: string;
  anatomicalRegion: string;
  clinicalSignificance: string;
}

export interface ModelMetadata {
  name: string;
  version: string;
  architecture: string;
  dataset: string;
  inputDimensions: string;
  benchmarkAurocMean?: number | null;
  benchmarkStatus?: string | null;
  lastUpdated: string;
  supportedClasses: string[];
}

export interface HeatmapData {
  conditionId: string;
  conditionName: string;
  heatmapUrl: string; // Base64 PNG data URL or direct URL
  overlayUrl: string; // Composite Base64 PNG data URL
  maxActivationScore: number;
  rawPeak?: number | null;
  rawMean?: number | null;
  isFinite?: boolean;
  isWeakActivation?: boolean;
  targetLayer: string;
}

export interface ConditionInterpretationItem {
  conditionName: string;
  likelihoodCategory: string;
  pathophysiology: string;
  clinicalContext: string;
  benignVsMalignant: string;
}

export interface FindingInterpretation {
  findingId: string;
  findingName: string;
  probability: number;
  threshold: number;
  detected: boolean;
  severity: SeverityLevel;
  sizeDefinition: string;
  possibleConditions: ConditionInterpretationItem[];
  uncertaintyStatement: string;
  diagnosticLimitations: string;
  evidenceBasis: string;
  recommendedFollowUp: string;
}

export interface OverallInterpretationSummary {
  primaryFindings: string[];
  secondaryFindings: string[];
  hasDetectedPathology: boolean;
  negativeFindingsDisclaimer: string;
  oncologicDisclaimer: string;
  localizationDisclaimer: string;
}

export interface ClinicalInterpretationResponse {
  summary: OverallInterpretationSummary;
  findings: FindingInterpretation[];
}

export interface AnalysisResult {
  analysisId: string;
  timestamp: string;
  originalImage: string; // Base64 data URL or blob URL
  fileName: string;
  fileSizeBytes: number;
  imageDimensions: { width: number; height: number };
  imageHashSha256: string;
  executionTimeMs: number;
  predictions: PathologyPrediction[];
  topFinding: PathologyPrediction | null;
  heatmaps: Record<string, HeatmapData>; // Keyed by conditionId
  clinicalSummary: string;
  isSimulatedFallback?: boolean;
  findingInterpretation?: ClinicalInterpretationResponse;
}

export type AnalysisStep = 'uploading' | 'validating' | 'preprocessing' | 'inferring' | 'gradcam' | 'finalizing';

export interface AnalysisProgressState {
  step: AnalysisStep;
  percentage: number;
  message: string;
}

export interface SampleCxrCase {
  id: string;
  title: string;
  category: 'Normal' | 'Pneumonia' | 'Cardiomegaly' | 'Effusion';
  summary: string;
  thumbnailSvg: string;
  fullDataUrl: string;
  expectedPrimaryFinding: string;
}

export interface ReportExportData {
  patientPseudonym: string;
  studyId: string;
  studyDate: string;
  clinicianNotes?: string;
  analysisResult: AnalysisResult;
}
