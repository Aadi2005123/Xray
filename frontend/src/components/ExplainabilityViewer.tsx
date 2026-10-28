import React, { useState, useEffect } from 'react';
import {
  ZoomIn,
  ZoomOut,
  RotateCcw,
  Sliders,
  Columns,
  Maximize2,
  Contrast,
  Layers,
  Sparkles,
  Info,
  Loader2,
  AlertCircle,
} from 'lucide-react';
import type { AnalysisResult, HeatmapData, PathologyPrediction } from '../types';
import { analysisApi } from '../services/analysisApi';

interface ExplainabilityViewerProps {
  result: AnalysisResult;
  selectedConditionId: string;
  onSelectCondition: (conditionId: string) => void;
}

export const ExplainabilityViewer: React.FC<ExplainabilityViewerProps> = ({
  result,
  selectedConditionId,
  onSelectCondition,
}) => {
  const [opacity, setOpacity] = useState<number>(65); // 0 to 100
  const [zoomLevel, setZoomLevel] = useState<number>(1); // 1x to 3x
  const [isInverted, setIsInverted] = useState<boolean>(false);
  const [viewMode, setViewMode] = useState<'original' | 'overlay' | 'side-by-side'>('overlay');
  const [isFullscreen, setIsFullscreen] = useState<boolean>(false);
  const [currentHeatmap, setCurrentHeatmap] = useState<HeatmapData | null>(null);
  const [isLoadingExplanation, setIsLoadingExplanation] = useState<boolean>(false);
  const [explanationError, setExplanationError] = useState<string | null>(null);

  const fetchExplanation = async (conditionId: string) => {
    if (!result.analysisId) return;
    setIsLoadingExplanation(true);
    setExplanationError(null);
    try {
      const data = await analysisApi.getGradCamExplanation(result.analysisId, conditionId);
      setCurrentHeatmap(data);
    } catch (err) {
      setExplanationError(err instanceof Error ? err.message : 'Failed to generate Grad-CAM explanation');
    } finally {
      setIsLoadingExplanation(false);
    }
  };

  // Sync heatmap whenever condition changes or result changes
  useEffect(() => {
    setExplanationError(null);

    // If pre-computed in result.heatmaps, use immediately
    if (result.heatmaps && result.heatmaps[selectedConditionId]) {
      setCurrentHeatmap(result.heatmaps[selectedConditionId]);
      return;
    }

    // Otherwise, request from backend
    if (result.analysisId) {
      let isCancelled = false;
      setIsLoadingExplanation(true);

      analysisApi
        .getGradCamExplanation(result.analysisId, selectedConditionId)
        .then((data) => {
          if (!isCancelled) {
            setCurrentHeatmap(data);
            setIsLoadingExplanation(false);
          }
        })
        .catch((err) => {
          if (!isCancelled) {
            setExplanationError(err instanceof Error ? err.message : 'Failed to load Grad-CAM');
            setIsLoadingExplanation(false);
          }
        });

      return () => {
        isCancelled = true;
      };
    }
  }, [selectedConditionId, result]);

  const activeHeatmap =
    currentHeatmap ||
    (result.heatmaps && result.heatmaps[selectedConditionId]) ||
    (result.heatmaps ? Object.values(result.heatmaps)[0] : null);

  const activePrediction =
    result.predictions.find((p) => p.id === selectedConditionId) || result.predictions[0];

  const handleZoomIn = () => setZoomLevel((z) => Math.min(3, +(z + 0.25).toFixed(2)));
  const handleZoomOut = () => setZoomLevel((z) => Math.max(1, +(z - 0.25).toFixed(2)));
  const handleReset = () => {
    setZoomLevel(1);
    setOpacity(65);
    setIsInverted(false);
  };

  return (
    <div
      className={`bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-lg transition-all ${
        isFullscreen ? 'fixed inset-0 z-50 rounded-none bg-slate-950 flex flex-col p-6' : ''
      }`}
    >
      {/* Top Toolbar */}
      <div className="p-4 bg-slate-950/80 border-b border-slate-800 flex flex-wrap items-center justify-between gap-4">
        {/* Active Condition Selector */}
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 text-xs text-slate-400">
            <Layers className="w-4 h-4 text-cyan-400" />
            <span className="font-semibold uppercase tracking-wider text-slate-300">Grad-CAM Target:</span>
          </div>
          <select
            value={selectedConditionId}
            onChange={(e) => onSelectCondition(e.target.value)}
            className="bg-slate-900 border border-slate-700 text-cyan-300 text-xs font-medium rounded-md px-3 py-1.5 focus:outline-none focus:border-cyan-500 cursor-pointer"
          >
            {result.predictions.map((p: PathologyPrediction) => (
              <option key={p.id} value={p.id}>
                {p.name} ({(p.probability * 100).toFixed(1)}%)
              </option>
            ))}
          </select>
          <button
            onClick={() => fetchExplanation(selectedConditionId)}
            disabled={isLoadingExplanation}
            className="px-2.5 py-1.5 bg-cyan-600 hover:bg-cyan-500 disabled:bg-slate-800 disabled:text-slate-500 text-white text-xs font-medium rounded-md flex items-center gap-1.5 transition-colors shadow-sm cursor-pointer"
            title="Generate or refresh Grad-CAM for selected pathology"
          >
            {isLoadingExplanation ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <Sparkles className="w-3.5 h-3.5" />
            )}
            <span>Explain</span>
          </button>
          <span className="hidden xl:inline-block px-2 py-0.5 text-[10px] font-mono text-cyan-300 bg-cyan-950/60 border border-cyan-800/60 rounded" title="Neural activation mapping — not an anatomical lesion boundary">
            Feature Attribution (Grad-CAM)
          </span>
          {result.isSimulatedFallback && (
            <span className="hidden sm:inline-block px-2 py-0.5 text-[10px] font-semibold text-amber-300 bg-amber-950/70 border border-amber-800/80 rounded">
              Demo Simulation Mode
            </span>
          )}
        </div>

        {/* View Controls & Interactive Modes */}
        <div className="flex items-center flex-wrap gap-2">
          {/* View Mode Toggle */}
          <div className="flex items-center bg-slate-900 border border-slate-700/80 rounded-lg p-0.5">
            <button
              onClick={() => setViewMode('overlay')}
              className={`px-2.5 py-1 text-xs font-medium rounded-md transition-colors ${
                viewMode === 'overlay'
                  ? 'bg-cyan-950 text-cyan-300 border border-cyan-800/80'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Overlay
            </button>
            <button
              onClick={() => setViewMode('side-by-side')}
              className={`px-2.5 py-1 text-xs font-medium rounded-md transition-colors flex items-center gap-1 ${
                viewMode === 'side-by-side'
                  ? 'bg-cyan-950 text-cyan-300 border border-cyan-800/80'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Columns className="w-3.5 h-3.5" />
              Side-by-Side
            </button>
            <button
              onClick={() => setViewMode('original')}
              className={`px-2.5 py-1 text-xs font-medium rounded-md transition-colors ${
                viewMode === 'original'
                  ? 'bg-cyan-950 text-cyan-300 border border-cyan-800/80'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Original
            </button>
          </div>

          {/* Contrast Inversion Button (Radiograph Negative Mode) */}
          <button
            onClick={() => setIsInverted(!isInverted)}
            title="Invert Contrast (Radiological Negative)"
            className={`p-1.5 rounded-lg border text-xs transition-colors ${
              isInverted
                ? 'bg-amber-950/60 border-amber-700 text-amber-300'
                : 'bg-slate-900 border-slate-700 text-slate-300 hover:text-white'
            }`}
          >
            <Contrast className="w-4 h-4" />
          </button>

          {/* Zoom Controls */}
          <div className="flex items-center bg-slate-900 border border-slate-700/80 rounded-lg p-0.5">
            <button
              onClick={handleZoomOut}
              disabled={zoomLevel <= 1}
              title="Zoom Out"
              className="p-1.5 text-slate-400 hover:text-white disabled:opacity-40"
            >
              <ZoomOut className="w-4 h-4" />
            </button>
            <span className="px-2 text-xs font-mono text-slate-300">{zoomLevel}x</span>
            <button
              onClick={handleZoomIn}
              disabled={zoomLevel >= 3}
              title="Zoom In"
              className="p-1.5 text-slate-400 hover:text-white disabled:opacity-40"
            >
              <ZoomIn className="w-4 h-4" />
            </button>
            <button
              onClick={handleReset}
              title="Reset Viewport"
              className="p-1.5 text-slate-400 hover:text-white border-l border-slate-800"
            >
              <RotateCcw className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Fullscreen Toggle */}
          <button
            onClick={() => setIsFullscreen(!isFullscreen)}
            title={isFullscreen ? 'Exit Fullscreen' : 'Enter Fullscreen'}
            className="p-1.5 bg-slate-900 border border-slate-700 rounded-lg text-slate-300 hover:text-white"
          >
            <Maximize2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {explanationError && (
        <div className="m-4 p-3 bg-rose-950/80 border border-rose-800 text-rose-200 text-xs rounded-lg flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
          <span>Grad-CAM Error: {explanationError}</span>
        </div>
      )}

      {/* Main Radiology Viewport Canvas */}
      <div className={`p-4 ${isFullscreen ? 'flex-1 overflow-auto' : ''}`}>
        {viewMode === 'original' ? (
          /* Original X-ray only */
          <div className="relative radiology-canvas border border-slate-800 rounded-xl overflow-hidden flex items-center justify-center min-h-[460px] sm:min-h-[520px]">
            <img
              src={result.originalImage}
              alt="Base Chest X-Ray"
              className={`max-h-[500px] w-auto max-w-full object-contain ${
                isInverted ? 'radiograph-inverted' : ''
              }`}
              style={{ transform: `scale(${zoomLevel})` }}
            />
          </div>
        ) : viewMode === 'overlay' ? (
          /* Single Blended Overlay Viewport */
          <div className="relative radiology-canvas border border-slate-800 rounded-xl overflow-hidden flex items-center justify-center min-h-[460px] sm:min-h-[520px]">
            <div
              className="relative inline-block max-w-full max-h-full transition-transform duration-150 origin-center"
              style={{ transform: `scale(${zoomLevel})` }}
            >
              {/* Layer 1: Base Radiograph */}
              <img
                src={result.originalImage}
                alt="Base Chest X-Ray"
                className={`max-h-[500px] w-auto max-w-full object-contain block select-none ${
                  isInverted ? 'radiograph-inverted' : ''
                }`}
              />

              {/* Layer 2: Genuine Grad-CAM Saliency Heatmap Overlay (Transparent RGBA) */}
              {activeHeatmap && (
                <img
                  src={activeHeatmap.heatmapUrl}
                  alt={`Grad-CAM heatmap for ${activePrediction?.name}`}
                  className="absolute inset-0 w-full h-full object-contain pointer-events-none transition-opacity duration-150"
                  style={{ opacity: opacity / 100 }}
                />
              )}

              {/* In-viewport Grad-CAM Computing State */}
              {isLoadingExplanation && (
                <div className="absolute inset-0 bg-slate-950/60 backdrop-blur-[1px] flex flex-col items-center justify-center gap-2 pointer-events-none z-20">
                  <Loader2 className="w-8 h-8 text-cyan-400 animate-spin" />
                  <span className="text-xs font-medium text-cyan-200">
                    Computing Grad-CAM for {activePrediction?.name}...
                  </span>
                </div>
              )}

              {/* Lead Anatomical Indicator Marker */}
              <div className="absolute top-3 left-4 text-xs font-mono font-bold text-slate-400 bg-slate-950/80 px-2 py-0.5 rounded border border-slate-800 pointer-events-none">
                R (PA)
              </div>
            </div>
          </div>
        ) : (
          /* Side-by-Side Comparative Viewport */
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Left: Original Radiograph */}
            <div className="radiology-canvas border border-slate-800 rounded-xl p-2 relative flex flex-col items-center justify-center min-h-[420px]">
              <span className="absolute top-3 left-3 text-[11px] font-semibold tracking-wider uppercase text-slate-400 bg-slate-950/80 px-2.5 py-1 rounded border border-slate-800 z-10">
                Original Radiograph
              </span>
              <img
                src={result.originalImage}
                alt="Original Radiograph"
                className={`max-h-[420px] max-w-full object-contain rounded ${
                  isInverted ? 'radiograph-inverted' : ''
                }`}
                style={{ transform: `scale(${zoomLevel})` }}
              />
            </div>

            {/* Right: Grad-CAM Saliency Overlay */}
            <div className="radiology-canvas border border-slate-800 rounded-xl p-2 relative flex flex-col items-center justify-center min-h-[420px]">
              <span className="absolute top-3 left-3 text-[11px] font-semibold tracking-wider uppercase text-cyan-300 bg-cyan-950/80 px-2.5 py-1 rounded border border-cyan-800/80 flex items-center gap-1.5 z-10">
                <Sparkles className="w-3 h-3 text-cyan-400" />
                Grad-CAM: {activePrediction?.name}
              </span>
              <div
                className="relative inline-block max-h-[420px]"
                style={{ transform: `scale(${zoomLevel})` }}
              >
                <img
                  src={result.originalImage}
                  alt="Original underlay"
                  className={`max-h-[420px] max-w-full object-contain rounded ${
                    isInverted ? 'radiograph-inverted' : ''
                  }`}
                />
                {activeHeatmap && (
                  <img
                    src={activeHeatmap.heatmapUrl}
                    alt="Grad-CAM Saliency"
                    className="absolute inset-0 w-full h-full object-contain rounded pointer-events-none transition-opacity duration-150"
                    style={{ opacity: opacity / 100 }}
                  />
                )}
                {isLoadingExplanation && (
                  <div className="absolute inset-0 bg-slate-950/60 backdrop-blur-[1px] flex flex-col items-center justify-center gap-2 pointer-events-none z-20">
                    <Loader2 className="w-8 h-8 text-cyan-400 animate-spin" />
                    <span className="text-xs font-medium text-cyan-200">
                      Computing Grad-CAM for {activePrediction?.name}...
                    </span>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Bottom Viewer Controls: Opacity Slider & Colormap Legend */}
        <div className="mt-4 p-3 bg-slate-950/70 border border-slate-800 rounded-lg flex flex-col sm:flex-row items-center justify-between gap-4">
          {/* Opacity Slider */}
          <div className="flex items-center gap-3 w-full sm:w-auto">
            <Sliders className="w-4 h-4 text-cyan-400 shrink-0" />
            <span className="text-xs font-medium text-slate-300 whitespace-nowrap">
              Heatmap Blending: <span className="text-cyan-300 font-mono">{opacity}%</span>
            </span>
            <input
              type="range"
              min="0"
              max="100"
              value={opacity}
              onChange={(e) => setOpacity(Number(e.target.value))}
              className="w-32 sm:w-44 accent-cyan-500 cursor-pointer h-1.5 bg-slate-800 rounded-lg"
              aria-label="Grad-CAM Heatmap Opacity"
            />
          </div>

          {/* Jet Colormap Scale Legend & Relative Normalization Disclosure */}
          <div className="flex flex-col sm:flex-row items-center gap-2">
            <div className="flex items-center gap-2">
              <span className="text-[11px] text-slate-400">Baseline</span>
              <div className="w-28 h-2.5 rounded-full bg-gradient-to-r from-blue-600 via-cyan-400 via-green-400 via-yellow-400 to-red-600 border border-slate-700" />
              <span className="text-[11px] text-rose-400 font-medium">Peak Activation</span>
            </div>
            {activeHeatmap?.isWeakActivation ? (
              <span
                className="text-[10px] text-amber-300 bg-amber-950/70 px-2 py-0.5 rounded border border-amber-800/60 font-mono"
                title="Raw gradient peak is below baseline salience threshold (0.02). Overlay opacity is attenuated to prevent visual over-interpretation of diffuse baseline gradient flow."
              >
                Weak activation (peak: {activeHeatmap.rawPeak !== undefined && activeHeatmap.rawPeak !== null ? activeHeatmap.rawPeak.toFixed(4) : activeHeatmap.maxActivationScore.toFixed(3)}) • Attenuated overlay
              </span>
            ) : activeHeatmap?.maxActivationScore !== undefined && activeHeatmap.maxActivationScore < 0.05 ? (
              <span
                className="text-[10px] text-amber-300 bg-amber-950/70 px-2 py-0.5 rounded border border-amber-800/60 font-mono"
                title="Relative min-max normalization scales faint gradients (<0.05) to peak colormap intensity. Overlay opacity is attenuated."
              >
                Faint raw peak ({activeHeatmap.maxActivationScore.toFixed(3)}) • Attenuated overlay
              </span>
            ) : null}
          </div>

          {/* Target Layer & Anatomical Info */}
          <div className="flex items-center gap-3 text-xs text-slate-400">
            {activeHeatmap?.targetLayer && (
              <span className="font-mono text-[11px] text-slate-400">
                Layer: <span className="text-cyan-400">{activeHeatmap.targetLayer}</span>
              </span>
            )}
            <div className="hidden lg:flex items-center gap-1.5">
              <Info className="w-3.5 h-3.5 text-slate-500" />
              <span>Region: {activePrediction?.anatomicalRegion}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
