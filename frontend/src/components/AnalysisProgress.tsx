import React from 'react';
import { Loader2, CheckCircle2, Cpu, Eye, ShieldAlert } from 'lucide-react';
import type { AnalysisProgressState } from '../types';

interface AnalysisProgressProps {
  progress: AnalysisProgressState;
}

const PIPELINE_STAGES = [
  { key: 'validating', label: '1. Ingestion & Validation', icon: ShieldAlert },
  { key: 'preprocessing', label: '2. CLAHE & Standardization', icon: Eye },
  { key: 'inferring', label: '3. DenseNet-121 Inference', icon: Cpu },
  { key: 'gradcam', label: '4. Grad-CAM Saliency', icon: CheckCircle2 },
];

export const AnalysisProgress: React.FC<AnalysisProgressProps> = ({ progress }) => {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-lg space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-cyan-950 border border-cyan-800 flex items-center justify-center text-cyan-400">
            <Loader2 className="w-5 h-5 animate-spin" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-slate-100">Deep Learning Inference Pipeline Active</h3>
            <p className="text-xs text-slate-400">{progress.message}</p>
          </div>
        </div>
        <div className="text-right">
          <span className="text-base font-bold text-cyan-400 font-mono">{progress.percentage}%</span>
          <span className="block text-[10px] text-slate-500 uppercase tracking-wider">Progress</span>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="w-full bg-slate-950 rounded-full h-2 overflow-hidden border border-slate-800">
        <div
          className="bg-cyan-500 h-2 rounded-full transition-all duration-300 ease-out"
          style={{ width: `${progress.percentage}%` }}
        />
      </div>

      {/* Stage Indicators */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 pt-2">
        {PIPELINE_STAGES.map((stage, idx) => {
          const isDone =
            progress.percentage > (idx + 1) * 25 ||
            (progress.percentage === 100 && idx === 3);
          const isCurrent =
            progress.step === stage.key ||
            (progress.percentage >= idx * 25 && progress.percentage < (idx + 1) * 25);

          return (
            <div
              key={stage.key}
              className={`p-2.5 rounded-lg border text-xs transition-colors ${
                isDone
                  ? 'bg-emerald-950/30 border-emerald-800/60 text-emerald-300'
                  : isCurrent
                  ? 'bg-cyan-950/40 border-cyan-700 text-cyan-200 ring-1 ring-cyan-700/50'
                  : 'bg-slate-950 border-slate-800 text-slate-500'
              }`}
            >
              <div className="flex items-center gap-2">
                <span
                  className={`w-1.5 h-1.5 rounded-full ${
                    isDone ? 'bg-emerald-400' : isCurrent ? 'bg-cyan-400 animate-pulse' : 'bg-slate-700'
                  }`}
                />
                <span className="font-medium truncate">{stage.label}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
