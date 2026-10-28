import React, { useState } from 'react';
import {
  FileText,
  RefreshCw,
  AlertCircle,
  FileCheck,
  Clock,
  Fingerprint,
} from 'lucide-react';
import type {
  AnalysisProgressState,
  AnalysisResult,
  PathologyPrediction,
} from '../types';
import { analysisApi } from '../services/analysisApi';
import { MedicalDisclaimer } from '../components/MedicalDisclaimer';
import { UploadStation } from '../components/UploadStation';
import { AnalysisProgress } from '../components/AnalysisProgress';
import { ExplainabilityViewer } from '../components/ExplainabilityViewer';
import { PredictionList } from '../components/PredictionList';
import { DiseaseDetailModal } from '../components/DiseaseDetailModal';
import { ReportModal } from '../components/ReportModal';
import { FindingInterpretationPanel } from '../components/FindingInterpretationPanel';

export const AnalysisPage: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<{
    file: File | Blob;
    fileName: string;
    previewUrl: string;
  } | null>(null);

  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [progress, setProgress] = useState<AnalysisProgressState | null>(null);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [selectedConditionId, setSelectedConditionId] = useState<string>('pneumonia');
  const [activeInfoCondition, setActiveInfoCondition] = useState<PathologyPrediction | null>(null);
  const [showReportModal, setShowReportModal] = useState<boolean>(false);

  const handleFileSelect = (file: File | Blob, fileName: string) => {
    const previewUrl = URL.createObjectURL(file);
    setSelectedFile({ file, fileName, previewUrl });
    setResult(null);
    setError(null);
  };

  const handleClear = () => {
    if (selectedFile?.previewUrl) {
      URL.revokeObjectURL(selectedFile.previewUrl);
    }
    setSelectedFile(null);
    setResult(null);
    setProgress(null);
    setError(null);
  };

  const handleStartAnalysis = async () => {
    if (!selectedFile) return;

    setIsAnalyzing(true);
    setError(null);
    setProgress({
      step: 'validating',
      percentage: 10,
      message: 'Beginning radiograph ingestion...',
    });

    try {
      const data = await analysisApi.analyzeXray(
        selectedFile.file,
        selectedFile.fileName,
        (p) => setProgress(p)
      );

      setResult(data);
      if (data.topFinding && data.topFinding.id !== 'normal') {
        setSelectedConditionId(data.topFinding.id);
      } else if (data.predictions.length > 0) {
        setSelectedConditionId(data.predictions[0].id);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Unknown analysis error';
      setError(`Analysis pipeline encountered an error: ${msg}`);
    } finally {
      setIsAnalyzing(false);
      setProgress(null);
    }
  };

  return (
    <div className="space-y-6 py-4">
      {/* Top Medical Disclaimer Notice */}
      <MedicalDisclaimer />

      {/* Error Banner */}
      {error && (
        <div className="p-4 bg-rose-950/70 border border-rose-800 text-rose-200 text-xs rounded-xl flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-rose-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Pipeline Active Progress */}
      {isAnalyzing && progress && <AnalysisProgress progress={progress} />}

      {/* Analysis Workspace Layout */}
      {!result ? (
        /* Upload & Ingestion Step */
        <UploadStation
          onFileSelect={handleFileSelect}
          selectedFile={selectedFile}
          onClear={handleClear}
          isAnalyzing={isAnalyzing}
          onStartAnalysis={handleStartAnalysis}
        />
      ) : (
        /* Completed Results Dashboard */
        <div className="space-y-6">
          {/* Action Header Banner */}
          <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl flex flex-wrap items-center justify-between gap-4 shadow-sm">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-emerald-950 border border-emerald-800/80 text-emerald-400">
                <FileCheck className="w-5 h-5" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-sm font-semibold text-slate-100">
                    Analysis Completed: <span className="font-mono text-cyan-300">{result.analysisId}</span>
                  </h3>
                  {result.isSimulatedFallback && (
                    <span className="px-2 py-0.5 rounded text-[10px] bg-amber-950/80 text-amber-300 border border-amber-700/80 font-semibold">
                      Demo Mode (Simulated / Prototype)
                    </span>
                  )}
                </div>
                <div className="flex flex-wrap items-center gap-3 text-xs text-slate-400 mt-0.5">
                  <span className="flex items-center gap-1">
                    <Clock className="w-3.5 h-3.5 text-slate-500" />
                    Inference: {result.executionTimeMs} ms
                  </span>
                  <span>•</span>
                  <span className="flex items-center gap-1 font-mono text-[11px]">
                    <Fingerprint className="w-3.5 h-3.5 text-slate-500" />
                    {result.imageHashSha256.slice(0, 18)}...
                  </span>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => setShowReportModal(true)}
                className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-medium rounded-lg flex items-center gap-1.5 transition-colors shadow-sm cursor-pointer"
              >
                <FileText className="w-4 h-4" />
                Generate Clinical Report
              </button>
              <button
                onClick={handleClear}
                className="px-3.5 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium rounded-lg flex items-center gap-1.5 border border-slate-700 transition-colors"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                New Screening
              </button>
            </div>
          </div>

          {/* Clinical Findings Narrative Banner */}
          <div className="p-4 bg-slate-900/80 border border-slate-800 rounded-xl">
            <h4 className="text-xs uppercase tracking-wider font-semibold text-slate-400 mb-1">
              Automated Radiological Observation Summary
            </h4>
            <p className="text-xs sm:text-sm text-slate-200 leading-relaxed">
              {result.clinicalSummary}
            </p>
          </div>

          {/* Main Inspection Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
            {/* Left 7 Columns: Explainability Viewer */}
            <div className="lg:col-span-7">
              <ExplainabilityViewer
                result={result}
                selectedConditionId={selectedConditionId}
                onSelectCondition={(id) => setSelectedConditionId(id)}
              />
            </div>

            {/* Right 5 Columns: Predictions Probability Breakdown */}
            <div className="lg:col-span-5">
              <PredictionList
                predictions={result.predictions}
                selectedConditionId={selectedConditionId}
                onSelectCondition={(id) => setSelectedConditionId(id)}
                onOpenDiseaseInfo={(pred) => setActiveInfoCondition(pred)}
              />
            </div>
          </div>

          {/* Finding-Based Clinical Interpretation Section */}
          <FindingInterpretationPanel
            interpretation={result.findingInterpretation}
            selectedConditionId={selectedConditionId}
            onSelectCondition={(id) => setSelectedConditionId(id)}
          />
        </div>
      )}

      {/* Disease Detail Modal */}
      <DiseaseDetailModal
        prediction={activeInfoCondition}
        onClose={() => setActiveInfoCondition(null)}
      />

      {/* Clinical Report Export Modal */}
      {result && showReportModal && (
        <ReportModal
          result={result}
          onClose={() => setShowReportModal(false)}
        />
      )}
    </div>
  );
};
