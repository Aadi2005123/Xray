import React from 'react';
import { AlertTriangle, ShieldCheck } from 'lucide-react';
import { MANDATORY_MEDICAL_DISCLAIMER } from '../utils/constants';

interface MedicalDisclaimerProps {
  compact?: boolean;
}

export const MedicalDisclaimer: React.FC<MedicalDisclaimerProps> = ({ compact = false }) => {
  if (compact) {
    return (
      <div
        className="flex items-center gap-2 px-3 py-1.5 text-xs font-medium text-amber-200 bg-amber-950/40 border border-amber-800/50 rounded-md"
        role="alert"
        aria-live="polite"
      >
        <AlertTriangle className="w-3.5 h-3.5 text-amber-400 shrink-0" />
        <span>{MANDATORY_MEDICAL_DISCLAIMER}</span>
      </div>
    );
  }

  return (
    <aside
      className="p-4 bg-slate-900/90 border-l-4 border-amber-500 border-y border-r border-slate-800 rounded-r-lg shadow-sm"
      role="region"
      aria-label="Medical Disclaimer"
    >
      <div className="flex items-start gap-3">
        <div className="p-2 bg-amber-500/10 rounded-md text-amber-400 shrink-0 mt-0.5">
          <AlertTriangle className="w-5 h-5" />
        </div>
        <div className="space-y-1">
          <h2 className="text-sm font-semibold tracking-wide text-amber-300 uppercase">
            Mandatory Research & Safety Notice
          </h2>
          <p className="text-xs md:text-sm text-slate-300 leading-relaxed font-medium">
            {MANDATORY_MEDICAL_DISCLAIMER}
          </p>
          <div className="flex flex-wrap items-center gap-3 pt-1 text-xs text-slate-400">
            <span className="flex items-center gap-1">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
              Ephemeral in-memory processing
            </span>
            <span>•</span>
            <span>Probability estimates are non-diagnostic statistical correlates</span>
            <span>•</span>
            <span>Requires evaluation by licensed radiologist</span>
          </div>
        </div>
      </div>
    </aside>
  );
};
