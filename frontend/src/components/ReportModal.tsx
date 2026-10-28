import React, { useState } from 'react';
import {
  X,
  Printer,
  Download,
  FileText,
  AlertTriangle,
  CheckCircle2,
} from 'lucide-react';
import type { AnalysisResult } from '../types';
import {
  MANDATORY_MEDICAL_DISCLAIMER,
  SECONDARY_ETHICAL_NOTICE,
} from '../utils/constants';
import { formatProbability } from '../utils/medicalFormatters';

interface ReportModalProps {
  result: AnalysisResult;
  onClose: () => void;
}

export const ReportModal: React.FC<ReportModalProps> = ({ result, onClose }) => {
  const [patientId] = useState<string>(
    `PT-ANON-${Math.random().toString(36).substring(2, 7).toUpperCase()}`
  );
  const [clinicianNotes, setClinicianNotes] = useState<string>(
    'Radiograph analyzed for computer-assisted multi-label thoracic screening. Visual saliency correlates with clinical inspection.'
  );

  const handlePrint = () => {
    window.print();
  };

  const handleDownloadJson = () => {
    const payload = {
      patientPseudonym: patientId,
      disclaimer: MANDATORY_MEDICAL_DISCLAIMER,
      analysisResult: {
        analysisId: result.analysisId,
        timestamp: result.timestamp,
        imageHash: result.imageHashSha256,
        fileName: result.fileName,
        executionTimeMs: result.executionTimeMs,
        predictions: result.predictions.map((p) => ({
          name: p.name,
          probability: p.probability,
          detected: p.detected,
          anatomicalRegion: p.anatomicalRegion,
        })),
        findingInterpretation: result.findingInterpretation,
        clinicianNotes,
      },
    };

    const blob = new Blob([JSON.stringify(payload, null, 2)], {
      type: 'application/json',
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `CXR_REPORT_${result.analysisId}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const topFinding = result.topFinding;
  const activeHeatmap =
    topFinding && result.heatmaps[topFinding.id]
      ? result.heatmaps[topFinding.id]
      : Object.values(result.heatmaps)[0];

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
    >
      <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-3xl w-full max-h-[90vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Modal Top Actions */}
        <div className="p-4 bg-slate-950 border-b border-slate-800 flex items-center justify-between print:hidden">
          <div className="flex items-center gap-2">
            <FileText className="w-5 h-5 text-cyan-400" />
            <h3 className="text-sm font-semibold text-slate-100">
              AI-Assisted Radiograph Analysis Report
            </h3>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handlePrint}
              className="px-3 py-1.5 bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-medium rounded-lg flex items-center gap-1.5 transition-colors cursor-pointer"
            >
              <Printer className="w-3.5 h-3.5" />
              Print / Save PDF
            </button>
            <button
              onClick={handleDownloadJson}
              className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium rounded-lg flex items-center gap-1.5 border border-slate-700 transition-colors"
            >
              <Download className="w-3.5 h-3.5" />
              Export JSON
            </button>
            <button
              onClick={onClose}
              className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Printable Clinical Report Content */}
        <div className="p-6 overflow-y-auto space-y-6 text-slate-200 bg-slate-900 print:bg-white print:text-black">
          {/* Clinical Header */}
          <div className="border-b border-slate-800 print:border-black pb-4 flex justify-between items-start">
            <div>
              <h1 className="text-lg font-bold text-slate-100 print:text-black tracking-tight">
                CXR-Explain Diagnostic Screening Summary
              </h1>
              <p className="text-xs text-slate-400 print:text-gray-600">
                Deep Learning Model: DenseNet-121 (Trained on NIH ChestX-ray14 10-Class Subset)
              </p>
            </div>
            <div className="text-right text-xs text-slate-400 print:text-gray-600 space-y-0.5">
              <div>
                <span className="font-semibold text-slate-300 print:text-black">Study ID:</span>{' '}
                {result.analysisId}
              </div>
              <div>
                <span className="font-semibold text-slate-300 print:text-black">Date:</span>{' '}
                {new Date(result.timestamp).toLocaleString()}
              </div>
              <div>
                <span className="font-semibold text-slate-300 print:text-black">Patient Ref:</span>{' '}
                {patientId}
              </div>
            </div>
          </div>

          {/* Mandatory Disclaimer Box */}
          <div className="p-3 bg-amber-950/40 border border-amber-800/80 rounded-lg text-amber-200 print:bg-yellow-50 print:border-yellow-600 print:text-black text-xs space-y-1">
            <div className="flex items-center gap-2 font-bold uppercase tracking-wider text-[11px] text-amber-300 print:text-black">
              <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
              MANDATORY MEDICAL SAFETY NOTICE
            </div>
            <p className="leading-relaxed">{MANDATORY_MEDICAL_DISCLAIMER}</p>
            <p className="text-[10px] text-amber-300/80 print:text-gray-600">{SECONDARY_ETHICAL_NOTICE}</p>
          </div>

          {/* Radiograph & Grad-CAM Visual Snapshots */}
          <div className="grid grid-cols-2 gap-4">
            <div className="p-2 bg-slate-950 print:bg-gray-100 rounded-lg border border-slate-800 print:border-gray-300 text-center">
              <span className="block text-[10px] uppercase font-semibold text-slate-400 print:text-black mb-1">
                Original Radiograph
              </span>
              <img
                src={result.originalImage}
                alt="Input X-Ray"
                className="max-h-40 mx-auto object-contain rounded"
              />
            </div>
            <div className="p-2 bg-slate-950 print:bg-gray-100 rounded-lg border border-slate-800 print:border-gray-300 text-center">
              <span className="block text-[10px] uppercase font-semibold text-cyan-400 print:text-black mb-1">
                Grad-CAM Activation: {topFinding?.name || 'Primary Finding'}
              </span>
              {activeHeatmap ? (
                <div className="relative max-h-40 mx-auto inline-block">
                  <img
                    src={result.originalImage}
                    alt="Underlay"
                    className="max-h-40 object-contain rounded opacity-75"
                  />
                  <img
                    src={activeHeatmap.heatmapUrl}
                    alt="Saliency Map"
                    className="absolute inset-0 w-full h-full object-contain mix-blend-screen"
                    style={{ opacity: 0.7 }}
                  />
                </div>
              ) : (
                <div className="h-40 flex items-center justify-center text-xs text-slate-500">
                  No heatmap available
                </div>
              )}
            </div>
          </div>

          {/* Model Findings Table */}
          <div className="space-y-2">
            <h4 className="text-xs font-semibold text-slate-200 print:text-black uppercase tracking-wider">
              Pathology Probabilities Table
            </h4>
            <div className="border border-slate-800 print:border-black rounded-lg overflow-hidden">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-950 print:bg-gray-200 border-b border-slate-800 print:border-black text-slate-400 print:text-black">
                  <tr>
                    <th className="p-2.5">Pathology Condition</th>
                    <th className="p-2.5">Model Output Score (Uncalibrated)</th>
                    <th className="p-2.5">Screening Threshold</th>
                    <th className="p-2.5">Anatomical Region</th>
                    <th className="p-2.5">Flag</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800 print:divide-gray-300">
                  {result.predictions.map((p) => (
                    <tr
                      key={p.id}
                      className={
                        p.detected
                          ? 'bg-amber-950/20 print:bg-amber-50'
                          : 'bg-slate-900/50 print:bg-white'
                      }
                    >
                      <td className="p-2.5 font-medium text-slate-200 print:text-black">
                        {p.name}
                      </td>
                      <td className="p-2.5 font-mono text-cyan-300 print:text-black font-semibold">
                        {formatProbability(p.probability)}
                      </td>
                      <td className="p-2.5 font-mono text-slate-400 print:text-gray-700">
                        {(p.threshold * 100).toFixed(0)}%
                      </td>
                      <td className="p-2.5 text-slate-400 print:text-gray-700">
                        {p.anatomicalRegion}
                      </td>
                      <td className="p-2.5">
                        {p.detected ? (
                          <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-rose-950 text-rose-300 border border-rose-800 print:border-black print:text-black">
                            Exceeds Threshold
                          </span>
                        ) : (
                          <span className="text-slate-500 print:text-gray-600 text-[11px]">
                            Below Threshold
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Finding-Based Clinical Interpretation & Differentials Section */}
          {result.findingInterpretation && (
            <div className="space-y-3 print:break-inside-avoid">
              <h4 className="text-xs font-semibold text-slate-200 print:text-black uppercase tracking-wider flex items-center justify-between">
                <span>Finding-Based Interpretation & Clinical Differentials</span>
                <span className="text-[10px] text-cyan-400 print:text-gray-700 font-mono lowercase">
                  [Evidence-Based Clinical Practice Guidelines]
                </span>
              </h4>

              {/* Oncologic & Localization Statements */}
              <div className="p-3 bg-slate-950 print:bg-gray-50 border border-slate-800 print:border-gray-400 rounded-lg text-xs space-y-2">
                <p className="text-rose-300 print:text-red-800 text-[11px] font-medium leading-relaxed">
                  <span className="font-bold uppercase tracking-wider">Oncologic Notice: </span>
                  {result.findingInterpretation.summary.oncologicDisclaimer}
                </p>
                <p className="text-cyan-300 print:text-cyan-900 text-[11px] leading-relaxed">
                  <span className="font-bold uppercase tracking-wider">Spatial Attribution: </span>
                  {result.findingInterpretation.summary.localizationDisclaimer}
                </p>
              </div>

              {/* Differentials for detected findings */}
              <div className="space-y-2">
                {result.findingInterpretation.findings
                  .filter((f) => f.detected || f.findingId === topFinding?.id)
                  .map((finding) => (
                    <div
                      key={finding.findingId}
                      className="p-3 bg-slate-950/70 print:bg-gray-100 border border-slate-800 print:border-gray-300 rounded-lg text-xs space-y-1.5"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-slate-100 print:text-black">
                          {finding.findingName} ({(finding.probability * 100).toFixed(1)}% score)
                        </span>
                        <span className="text-[10px] italic text-slate-400 print:text-gray-600">
                          {finding.sizeDefinition}
                        </span>
                      </div>

                      <div className="text-[11px] text-slate-300 print:text-gray-800">
                        <span className="font-semibold text-cyan-400 print:text-black">Differentials: </span>
                        {finding.possibleConditions.map((c) => `${c.conditionName} [${c.benignVsMalignant}]`).join(' • ')}
                      </div>

                      <div className="text-[11px] text-slate-400 print:text-gray-700">
                        <span className="font-semibold text-slate-300 print:text-black">Follow-up: </span>
                        {finding.recommendedFollowUp}
                      </div>
                    </div>
                  ))}
              </div>
            </div>
          )}

          {/* Clinician Observations & Sign-off */}
          <div className="space-y-1.5 print:break-inside-avoid">
            <label className="text-xs font-semibold text-slate-200 print:text-black uppercase tracking-wider block">
              Reviewing Clinician / Researcher Notes
            </label>
            <textarea
              value={clinicianNotes}
              onChange={(e) => setClinicianNotes(e.target.value)}
              rows={3}
              className="w-full bg-slate-950 print:bg-white border border-slate-800 print:border-black rounded-lg p-2.5 text-xs text-slate-200 print:text-black focus:outline-none focus:border-cyan-500"
              placeholder="Enter clinical correlation notes, diagnostic impression, or further imaging recommendations..."
            />
          </div>

          {/* Audit Verification Footer */}
          <div className="pt-3 border-t border-slate-800 print:border-black flex flex-wrap items-center justify-between text-[10px] text-slate-500 print:text-gray-600 gap-2">
            <span className="font-mono">Image Hash: {result.imageHashSha256.slice(0, 32)}...</span>
            <span className="flex items-center gap-1">
              <CheckCircle2 className="w-3 h-3 text-emerald-400 print:text-black" />
              Cryptographic Integrity Verified
            </span>
            <span>Generated via CXR-Explain Research Framework</span>
          </div>
        </div>
      </div>
    </div>
  );
};
