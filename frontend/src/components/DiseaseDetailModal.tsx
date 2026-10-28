import React from 'react';
import { X, BookOpen, AlertTriangle, ShieldCheck } from 'lucide-react';
import type { PathologyPrediction } from '../types';
import { MANDATORY_MEDICAL_DISCLAIMER } from '../utils/constants';

interface DiseaseDetailModalProps {
  prediction: PathologyPrediction | null;
  onClose: () => void;
}

export const DiseaseDetailModal: React.FC<DiseaseDetailModalProps> = ({
  prediction,
  onClose,
}) => {
  if (!prediction) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
    >
      <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-lg w-full overflow-hidden shadow-2xl animate-in fade-in zoom-in-95 duration-150">
        {/* Modal Header */}
        <div className="p-4 bg-slate-950 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-md bg-cyan-950 text-cyan-400 border border-cyan-800">
              <BookOpen className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-slate-100">{prediction.name}</h3>
              <span className="text-[11px] text-slate-400">Radiological Reference Guide</span>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-5 space-y-4 max-h-[75vh] overflow-y-auto text-xs text-slate-300">
          <div className="p-3 bg-amber-950/30 border border-amber-800/50 rounded-lg text-amber-200 flex items-start gap-2.5">
            <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
            <p className="leading-relaxed">{MANDATORY_MEDICAL_DISCLAIMER}</p>
          </div>

          <div className="space-y-1.5">
            <h4 className="font-semibold text-slate-200 uppercase tracking-wider text-[11px] text-cyan-400">
              Anatomical Region
            </h4>
            <p className="bg-slate-950 p-2.5 rounded-lg border border-slate-800 text-slate-300">
              {prediction.anatomicalRegion}
            </p>
          </div>

          <div className="space-y-1.5">
            <h4 className="font-semibold text-slate-200 uppercase tracking-wider text-[11px] text-cyan-400">
              Radiological Description
            </h4>
            <p className="bg-slate-950 p-2.5 rounded-lg border border-slate-800 leading-relaxed text-slate-300">
              {prediction.description}
            </p>
          </div>

          <div className="space-y-1.5">
            <h4 className="font-semibold text-slate-200 uppercase tracking-wider text-[11px] text-cyan-400">
              Clinical Significance & Action
            </h4>
            <p className="bg-slate-950 p-2.5 rounded-lg border border-slate-800 leading-relaxed text-slate-300">
              {prediction.clinicalSignificance}
            </p>
          </div>

          <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 text-slate-400 flex items-center justify-between text-[11px]">
            <span>Model Screening Threshold: {(prediction.threshold * 100).toFixed(0)}%</span>
            <span className="flex items-center gap-1 text-emerald-400">
              <ShieldCheck className="w-3.5 h-3.5" />
              NIH ChestX-ray14 Standard Taxonomy
            </span>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="p-3 bg-slate-950 border-t border-slate-800 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium rounded-lg border border-slate-700 transition-colors"
          >
            Close Guide
          </button>
        </div>
      </div>
    </div>
  );
};
