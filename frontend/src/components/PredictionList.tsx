import React, { useState } from 'react';
import {
  AlertTriangle,
  Info,
  CheckCircle,
  Eye,
  Filter,
} from 'lucide-react';
import type { PathologyPrediction } from '../types';
import { formatProbability, getSeverityBadgeStyles } from '../utils/medicalFormatters';

interface PredictionListProps {
  predictions: PathologyPrediction[];
  selectedConditionId: string;
  onSelectCondition: (conditionId: string) => void;
  onOpenDiseaseInfo: (prediction: PathologyPrediction) => void;
}

export const PredictionList: React.FC<PredictionListProps> = ({
  predictions,
  selectedConditionId,
  onSelectCondition,
  onOpenDiseaseInfo,
}) => {
  const [filterMode, setFilterMode] = useState<'all' | 'flagged'>('all');

  const displayedPredictions =
    filterMode === 'flagged'
      ? predictions.filter((p) => p.detected)
      : predictions;

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-md space-y-4">
      {/* Header and Filter */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-800">
        <div>
          <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
            <span>Pathology Model Scores</span>
            <span className="text-[11px] font-normal text-slate-400">
              (Multi-Label Sigmoid)
            </span>
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Uncalibrated screening scores across standard thoracic radiological findings
          </p>
        </div>

        <div className="flex items-center gap-1 bg-slate-950 border border-slate-800 rounded-lg p-0.5">
          <button
            onClick={() => setFilterMode('all')}
            className={`px-2.5 py-1 text-xs font-medium rounded-md transition-colors ${
              filterMode === 'all'
                ? 'bg-slate-800 text-cyan-300'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            All ({predictions.length})
          </button>
          <button
            onClick={() => setFilterMode('flagged')}
            className={`px-2.5 py-1 text-xs font-medium rounded-md transition-colors flex items-center gap-1 ${
              filterMode === 'flagged'
                ? 'bg-cyan-950 text-cyan-300 border border-cyan-800/60'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Filter className="w-3 h-3" />
            Detected ({predictions.filter((p) => p.detected).length})
          </button>
        </div>
      </div>

      {/* Prediction Cards List */}
      <div className="space-y-2.5 max-h-[560px] overflow-y-auto pr-1">
        {displayedPredictions.length === 0 ? (
          <div className="p-8 text-center text-xs text-slate-500 bg-slate-950/40 rounded-lg border border-slate-800">
            No pathologies detected above baseline screening threshold.
          </div>
        ) : (
          displayedPredictions.map((pred) => {
            const isSelected = pred.id === selectedConditionId;
            const badge = getSeverityBadgeStyles(pred.severity);
            const percentage = pred.probability * 100;

            return (
              <div
                key={pred.id}
                onClick={() => onSelectCondition(pred.id)}
                className={`p-3.5 rounded-lg border transition-all cursor-pointer ${
                  isSelected
                    ? 'bg-cyan-950/30 border-cyan-500/80 ring-1 ring-cyan-500/40 shadow-sm'
                    : 'bg-slate-950/70 border-slate-800 hover:border-slate-700 hover:bg-slate-900/80'
                }`}
              >
                <div className="flex items-start justify-between gap-3 mb-2">
                  <div className="flex items-center gap-2">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectCondition(pred.id);
                      }}
                      title={`Inspect Grad-CAM for ${pred.name}`}
                      className={`px-2.5 py-1 rounded text-xs font-medium flex items-center gap-1.5 transition-colors ${
                        isSelected
                          ? 'bg-cyan-600 text-white shadow-sm ring-1 ring-cyan-400'
                          : 'bg-slate-800 text-slate-300 hover:text-cyan-300 hover:bg-slate-700'
                      }`}
                    >
                      <Eye className="w-3.5 h-3.5" />
                      <span>Explain</span>
                    </button>
                    <div>
                      <h4 className="text-xs font-semibold text-slate-100 flex items-center gap-1.5">
                        {pred.name}
                        {pred.detected && (
                          <AlertTriangle className="w-3.5 h-3.5 text-amber-400 inline" />
                        )}
                      </h4>
                      <span className="text-[11px] text-slate-400">{pred.anatomicalRegion}</span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-semibold border ${badge.bg} ${badge.text} ${badge.border}`}
                    >
                      {badge.label}
                    </span>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onOpenDiseaseInfo(pred);
                      }}
                      title="Clinical pathophysiology & reference notes"
                      className="p-1 rounded hover:bg-slate-800 text-slate-400 hover:text-slate-200"
                    >
                      <Info className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>

                {/* Probability Bar */}
                <div className="space-y-1">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-[11px] text-slate-400">
                      Model Output Score:{' '}
                      <span className="font-mono font-medium text-slate-200">
                        {formatProbability(pred.probability)}
                      </span>
                    </span>
                    <span className="text-[10px] text-slate-500 font-mono">
                      Decision Threshold: {(pred.threshold * 100).toFixed(0)}%
                    </span>
                  </div>

                  <div className="relative w-full bg-slate-900 rounded-full h-2 overflow-hidden border border-slate-800">
                    {/* Diagnostic Threshold Indicator Line */}
                    <div
                      className="absolute top-0 bottom-0 w-0.5 bg-slate-500 z-10"
                      style={{ left: `${pred.threshold * 100}%` }}
                      title={`Screening Threshold: ${pred.threshold * 100}%`}
                    />
                    {/* Fill */}
                    <div
                      className={`h-2 rounded-full transition-all duration-300 ${
                        pred.severity === 'high'
                          ? 'bg-rose-500'
                          : pred.severity === 'moderate'
                          ? 'bg-amber-500'
                          : pred.severity === 'low'
                          ? 'bg-cyan-500'
                          : 'bg-emerald-500'
                      }`}
                      style={{ width: `${Math.min(100, percentage)}%` }}
                    />
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Safety Notice Footer in Prediction Panel */}
      <div className="p-2.5 bg-slate-950/60 border border-slate-800/80 rounded-lg text-[11px] text-slate-400 flex items-center gap-2">
        <CheckCircle className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
        <span>Model output scores (probabilities) are presented as-is, without clinical certainty guarantees.</span>
      </div>
    </div>
  );
};
