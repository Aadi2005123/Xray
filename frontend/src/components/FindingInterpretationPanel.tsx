import React, { useState } from 'react';
import {
  Stethoscope,
  AlertTriangle,
  ShieldAlert,
  CheckCircle2,
  ExternalLink,
  Crosshair,
  Layers,
  BookOpen,
} from 'lucide-react';
import type { ClinicalInterpretationResponse, FindingInterpretation } from '../types';

interface FindingInterpretationPanelProps {
  interpretation?: ClinicalInterpretationResponse;
  selectedConditionId: string;
  onSelectCondition: (conditionId: string) => void;
}

export const FindingInterpretationPanel: React.FC<FindingInterpretationPanelProps> = ({
  interpretation,
  selectedConditionId,
  onSelectCondition,
}) => {
  const [activeTab, setActiveTab] = useState<'differentials' | 'localization' | 'uncertainty' | 'followup'>(
    'differentials'
  );

  if (!interpretation) {
    return (
      <div className="p-6 bg-slate-900 border border-slate-800 rounded-xl text-center text-slate-400 text-xs">
        <Stethoscope className="w-6 h-6 mx-auto mb-2 text-slate-500 opacity-60" />
        No clinical interpretation data available for this analysis session.
      </div>
    );
  }

  const { summary, findings } = interpretation;

  // Active finding to display in detail view
  const activeFinding: FindingInterpretation =
    findings.find((f) => f.findingId === selectedConditionId) || findings[0];

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-lg space-y-0">
      {/* Header Banner */}
      <div className="p-5 bg-gradient-to-r from-slate-950 via-slate-900 to-slate-950 border-b border-slate-800">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <div className="flex items-center gap-2">
              <div className="p-1.5 rounded-lg bg-cyan-950 border border-cyan-800/80 text-cyan-400">
                <Stethoscope className="w-4 h-4" />
              </div>
              <h3 className="text-sm font-semibold text-slate-100 tracking-wide">
                Finding-Based Clinical Interpretation & Diagnostic Context
              </h3>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-cyan-950 text-cyan-300 border border-cyan-800/70">
                Research v2.4
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-1 max-w-3xl leading-relaxed">
              Maps objective model findings to established radiological differential considerations
              (encompassing both benign and malignant etiologies), diagnostic uncertainties, and clinical follow-up criteria.
            </p>
          </div>

          <div className="flex items-center gap-1.5 shrink-0">
            <span className="px-2.5 py-1 text-[11px] rounded-md bg-slate-800/90 text-slate-300 border border-slate-700 font-medium">
              Evidence-Based Clinical Guidelines
            </span>
          </div>
        </div>

        {/* Tab Selection Bar */}
        <div className="flex items-center gap-2 mt-4 pt-3 border-t border-slate-800/80 overflow-x-auto pb-1">
          <button
            onClick={() => setActiveTab('differentials')}
            className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-colors flex items-center gap-1.5 whitespace-nowrap cursor-pointer ${
              activeTab === 'differentials'
                ? 'bg-cyan-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
            }`}
          >
            <BookOpen className="w-3.5 h-3.5" />
            Possible Clinical Conditions ({activeFinding.possibleConditions.length})
          </button>

          <button
            onClick={() => setActiveTab('localization')}
            className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-colors flex items-center gap-1.5 whitespace-nowrap cursor-pointer ${
              activeTab === 'localization'
                ? 'bg-cyan-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
            }`}
          >
            <Crosshair className="w-3.5 h-3.5" />
            Attribution vs. Lesion Localization
          </button>

          <button
            onClick={() => setActiveTab('uncertainty')}
            className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-colors flex items-center gap-1.5 whitespace-nowrap cursor-pointer ${
              activeTab === 'uncertainty'
                ? 'bg-cyan-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
            }`}
          >
            <ShieldAlert className="w-3.5 h-3.5" />
            Uncertainty & Oncologic Boundaries
          </button>

          <button
            onClick={() => setActiveTab('followup')}
            className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-colors flex items-center gap-1.5 whitespace-nowrap cursor-pointer ${
              activeTab === 'followup'
                ? 'bg-cyan-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
            }`}
          >
            <ExternalLink className="w-3.5 h-3.5" />
            Recommended Clinical Follow-Up
          </button>
        </div>
      </div>

      {/* Mandatory Safety Notices Banner */}
      <div className="p-4 bg-slate-950 border-b border-slate-800 grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
        {/* Oncologic Disclaimer */}
        <div className="p-3 rounded-lg bg-rose-950/40 border border-rose-900/60 flex items-start gap-2.5">
          <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <span className="font-semibold text-rose-300">Oncologic Diagnosis Limitation</span>
            <p className="text-[11px] text-rose-200/90 leading-relaxed">
              {summary.oncologicDisclaimer}
            </p>
          </div>
        </div>

        {/* Grad-CAM vs Localization Transparency */}
        <div className="p-3 rounded-lg bg-cyan-950/40 border border-cyan-900/60 flex items-start gap-2.5">
          <Layers className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <span className="font-semibold text-cyan-300">Spatial Attribution Saliency Notice</span>
            <p className="text-[11px] text-cyan-200/90 leading-relaxed">
              {summary.localizationDisclaimer}
            </p>
          </div>
        </div>
      </div>

      {/* Finding Selector Chips */}
      <div className="p-3 bg-slate-950/70 border-b border-slate-800 flex items-center gap-2 overflow-x-auto">
        <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider pl-2 shrink-0">
          Inspect Finding:
        </span>
        <div className="flex items-center gap-1.5">
          {findings.map((f) => {
            const isSelected = f.findingId === selectedConditionId;
            return (
              <button
                key={f.findingId}
                onClick={() => onSelectCondition(f.findingId)}
                className={`px-3 py-1 rounded-md text-xs font-medium transition-all flex items-center gap-1.5 shrink-0 cursor-pointer ${
                  isSelected
                    ? 'bg-cyan-950 text-cyan-300 border border-cyan-500/80 shadow-sm'
                    : 'bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800'
                }`}
              >
                <span>{f.findingName}</span>
                <span
                  className={`text-[10px] px-1.5 py-0.2 rounded font-mono ${
                    f.detected
                      ? 'bg-rose-950 text-rose-300 border border-rose-800/80'
                      : 'bg-slate-800 text-slate-400'
                  }`}
                >
                  {(f.probability * 100).toFixed(0)}%
                </span>
                {f.detected && <span className="w-1.5 h-1.5 rounded-full bg-rose-400 shrink-0 animate-pulse" />}
              </button>
            );
          })}
        </div>
      </div>

      {/* Active Tab Content Area */}
      <div className="p-5">
        {activeTab === 'differentials' && (
          <div className="space-y-4">
            {/* Header of Active Finding */}
            <div className="flex flex-wrap items-center justify-between gap-2 pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2.5">
                <span className="text-sm font-semibold text-slate-100">{activeFinding.findingName}</span>
                <span className="text-xs text-slate-400 font-mono">
                  Score: {(activeFinding.probability * 100).toFixed(1)}% | Threshold: {(activeFinding.threshold * 100).toFixed(0)}%
                </span>
                <span
                  className={`text-[11px] px-2 py-0.5 rounded-full font-medium ${
                    activeFinding.detected
                      ? 'bg-rose-950 text-rose-300 border border-rose-800'
                      : 'bg-slate-800 text-slate-300'
                  }`}
                >
                  {activeFinding.detected ? 'Exceeds Screening Threshold' : 'Sub-Threshold'}
                </span>
              </div>
              <span className="text-xs text-slate-400 italic">
                {activeFinding.sizeDefinition}
              </span>
            </div>

            {/* Differential Diagnoses Cards Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
              {activeFinding.possibleConditions.map((cond, idx) => (
                <div
                  key={idx}
                  className="p-4 bg-slate-950/80 border border-slate-800 rounded-lg space-y-2 hover:border-slate-700 transition-colors"
                >
                  <div className="flex items-start justify-between gap-2">
                    <h5 className="text-xs font-semibold text-slate-100 flex items-center gap-1.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
                      {cond.conditionName}
                    </h5>
                    <span
                      className={`text-[10px] px-2 py-0.5 rounded font-semibold uppercase tracking-wider shrink-0 ${
                        cond.benignVsMalignant === 'Malignant'
                          ? 'bg-rose-950/80 text-rose-300 border border-rose-800'
                          : cond.benignVsMalignant === 'Benign'
                          ? 'bg-emerald-950/80 text-emerald-300 border border-emerald-800'
                          : cond.benignVsMalignant.includes('Baseline') || cond.benignVsMalignant.includes('Non-Neoplastic')
                          ? 'bg-slate-800 text-slate-300 border border-slate-700'
                          : 'bg-amber-950/80 text-amber-300 border border-amber-800'
                      }`}
                    >
                      {cond.benignVsMalignant}
                    </span>
                  </div>

                  <div className="text-[11px] font-medium text-cyan-300">
                    Category: {cond.likelihoodCategory}
                  </div>

                  <p className="text-xs text-slate-300 leading-relaxed">
                    {cond.pathophysiology}
                  </p>

                  <div className="text-[11px] text-slate-400 pt-1 border-t border-slate-800/80">
                    <span className="font-semibold text-slate-300">Clinical Context: </span>
                    {cond.clinicalContext}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'localization' && (
          <div className="space-y-4">
            <div className="p-4 bg-slate-950 border border-slate-800 rounded-lg space-y-3">
              <h4 className="text-xs font-semibold text-cyan-300 uppercase tracking-wider flex items-center gap-2">
                <Crosshair className="w-4 h-4" />
                Scientific Distinction: Grad-CAM Saliency vs. Genuine Lesion Localization
              </h4>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs text-slate-300">
                <div className="p-3.5 bg-slate-900 border border-slate-800 rounded-lg space-y-2">
                  <div className="font-semibold text-amber-300 flex items-center gap-1.5">
                    <Layers className="w-3.5 h-3.5" />
                    What Grad-CAM Visualizes (Feature Attribution)
                  </div>
                  <ul className="space-y-1.5 text-slate-300 list-disc list-inside">
                    <li>Computes gradients of class logits with respect to final denseblock4 feature maps.</li>
                    <li>Reflects which pixel clusters contributed most to the model's global prediction score.</li>
                    <li>Low spatial resolution (7x7 receptive fields) upsampled by interpolation.</li>
                    <li>
                      <span className="text-rose-300 font-semibold">NOT an anatomical boundary:</span> A bright
                      activation does NOT prove a lesion is located there.
                    </li>
                  </ul>
                </div>

                <div className="p-3.5 bg-slate-900 border border-slate-800 rounded-lg space-y-2">
                  <div className="font-semibold text-emerald-300 flex items-center gap-1.5">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    What True Lesion Localization Requires
                  </div>
                  <ul className="space-y-1.5 text-slate-300 list-disc list-inside">
                    <li>Supervision via radiologist-drawn bounding boxes ($[x, y, w, h]$) or pixel segmentation masks.</li>
                    <li>Dedicated detection networks (e.g., YOLOv8, Faster R-CNN, nnU-Net).</li>
                    <li>Evaluation via Intersection over Union (IoU) and mean Average Precision (mAP).</li>
                    <li>
                      <span className="text-cyan-300 font-semibold">Current System Status:</span> Image-level classifier
                      only. Localization datasets (NIH Bounding Boxes / VinDr-CXR) require dedicated model retraining (Gate D).
                    </li>
                  </ul>
                </div>
              </div>
            </div>

            <div className="p-3.5 bg-slate-950/60 border border-slate-800 rounded-lg text-xs text-slate-400">
              <span className="font-semibold text-slate-300">Target Layer Hooked: </span>
              <span className="font-mono text-cyan-400">DenseNet-121.features.denseblock4.denselayer16.conv2</span>.
              Grad-CAM activations are normalized to [0, 1] and thresholded (&lt; 0.12 transparent) to minimize background noise.
            </div>
          </div>
        )}

        {activeTab === 'uncertainty' && (
          <div className="space-y-4">
            <div className="p-4 bg-slate-950 border border-slate-800 rounded-lg space-y-3">
              <h4 className="text-xs font-semibold text-rose-300 uppercase tracking-wider flex items-center gap-2">
                <ShieldAlert className="w-4 h-4" />
                Clinical Uncertainty & Model Boundaries for {activeFinding.findingName}
              </h4>

              <div className="space-y-3 text-xs text-slate-300 leading-relaxed">
                <div className="p-3 bg-slate-900 border border-slate-800 rounded-lg">
                  <span className="font-semibold text-amber-300 block mb-1">Uncertainty Statement:</span>
                  <p>{activeFinding.uncertaintyStatement}</p>
                </div>

                <div className="p-3 bg-slate-900 border border-slate-800 rounded-lg">
                  <span className="font-semibold text-cyan-300 block mb-1">Imaging Technique Limitations:</span>
                  <p>{activeFinding.diagnosticLimitations}</p>
                </div>

                <div className="p-3 bg-slate-900 border border-slate-800 rounded-lg">
                  <span className="font-semibold text-slate-300 block mb-1">Negative Predictive Value Notice:</span>
                  <p>{summary.negativeFindingsDisclaimer}</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'followup' && (
          <div className="space-y-4">
            <div className="p-4 bg-slate-950 border border-slate-800 rounded-lg space-y-3">
              <h4 className="text-xs font-semibold text-cyan-300 uppercase tracking-wider flex items-center gap-2">
                <ExternalLink className="w-4 h-4" />
                Recommended Clinical Follow-Up & Evidence Basis for {activeFinding.findingName}
              </h4>

              <div className="space-y-3 text-xs text-slate-300 leading-relaxed">
                <div className="p-3 bg-slate-900 border border-slate-800 rounded-lg">
                  <span className="font-semibold text-emerald-300 block mb-1">Recommended Follow-Up Workup:</span>
                  <p className="text-slate-200">{activeFinding.recommendedFollowUp}</p>
                </div>

                <div className="p-3 bg-slate-900 border border-slate-800 rounded-lg">
                  <span className="font-semibold text-cyan-300 block mb-1">Evidence Basis / Clinical Practice Guidelines:</span>
                  <p className="text-cyan-200 font-medium">{activeFinding.evidenceBasis}</p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
