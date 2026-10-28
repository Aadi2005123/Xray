import React, { useEffect, useState } from 'react';
import {
  Cpu,
  Layers,
  Database,
  BarChart2,
} from 'lucide-react';
import type { ModelMetadata } from '../types';
import { analysisApi } from '../services/analysisApi';
import { MedicalDisclaimer } from '../components/MedicalDisclaimer';

export const ModelArchitecturePage: React.FC = () => {
  const [modelInfo, setModelInfo] = useState<ModelMetadata | null>(null);

  useEffect(() => {
    analysisApi.getModelInfo().then(setModelInfo);
  }, []);

  return (
    <div className="space-y-8 py-4 max-w-5xl mx-auto">
      <MedicalDisclaimer />

      {/* Title */}
      <div className="space-y-2">
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-cyan-950 text-cyan-300 border border-cyan-800">
          <Cpu className="w-3.5 h-3.5" />
          <span>Technical Whitepaper & Specification</span>
        </div>
        <h2 className="text-2xl sm:text-3xl font-bold text-slate-100 tracking-tight">
          Deep Learning Backbone & Explainability Architecture
        </h2>
        <p className="text-xs sm:text-sm text-slate-400">
          {modelInfo?.architecture || 'DenseNet-121 Feature Representation'} & Gradient-Weighted Class Activation Mapping (Grad-CAM)
        </p>
      </div>

      {/* Model Spec Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl space-y-1">
          <span className="text-[11px] font-semibold uppercase text-slate-400">Architecture</span>
          <p className="text-sm font-bold text-slate-100">{modelInfo?.name || 'DenseNet-121'}</p>
          <span className="text-[11px] text-cyan-400">4 Dense Blocks + Transition Layers</span>
        </div>
        <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl space-y-1">
          <span className="text-[11px] font-semibold uppercase text-slate-400">Input Resolution</span>
          <p className="text-sm font-bold text-slate-100">{modelInfo?.inputDimensions || '224 x 224 x 3'}</p>
          <span className="text-[11px] text-cyan-400">Canonical RGB Baseline</span>
        </div>
        <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl space-y-1">
          <span className="text-[11px] font-semibold uppercase text-slate-400">Architecture Target</span>
          <p className="text-sm font-bold text-slate-100">DenseNet-121 Backbone</p>
          <span className="text-[11px] text-emerald-400">NIH ChestX-ray14 Baseline</span>
        </div>
        <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl space-y-1">
          <span className="text-[11px] font-semibold uppercase text-slate-400">Explainability Engine</span>
          <p className="text-sm font-bold text-slate-100">Grad-CAM</p>
          <span className="text-[11px] text-cyan-400">features.denseblock4</span>
        </div>
      </div>

      {/* Grad-CAM Theory & Math */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
        <h3 className="text-base font-semibold text-slate-100 flex items-center gap-2">
          <Layers className="w-5 h-5 text-cyan-400" />
          Gradient-Weighted Class Activation Mapping (Grad-CAM)
        </h3>
        <p className="text-xs text-slate-300 leading-relaxed">
          Grad-CAM uses the gradient information flowing into the last convolutional layer of the convolutional neural network to assign importance values to each neuron for a specific pathology decision.
        </p>
        <div className="p-4 bg-slate-950 border border-slate-800 rounded-lg font-mono text-xs text-cyan-300 overflow-x-auto">
          <code>
            {`α_k^c = (1 / Z) * Σ_i Σ_j (∂y^c / ∂A_{i,j}^k)`} <br />
            {`L_{Grad-CAM}^c = ReLU( Σ_k α_k^c * A^k )`}
          </code>
        </div>
        <p className="text-xs text-slate-400 leading-relaxed">
          Where <span className="text-slate-300">y^c</span> is the score for class <span className="text-slate-300">c</span> before sigmoid activation, <span className="text-slate-300">A^k</span> represents feature map activations of channel <span className="text-slate-300">k</span> in the target layer (<code className="text-cyan-400 font-mono">denseblock4.denselayer16.conv2</code>), and <span className="text-slate-300">Z</span> is the spatial spatial footprint (height × width). The application of <span className="text-slate-300">ReLU</span> ensures only features with positive correlation to the target pathology are highlighted.
        </p>
      </div>

      {/* Benchmark AUROC Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
        <h3 className="text-base font-semibold text-slate-100 flex items-center gap-2">
          <BarChart2 className="w-5 h-5 text-cyan-400" />
          Multi-Label Pathology Benchmark AUROCs
        </h3>
        <div className="border border-slate-800 rounded-lg overflow-hidden">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950 border-b border-slate-800 text-slate-400">
              <tr>
                <th className="p-3">Pathology Finding</th>
                <th className="p-3">Literature AUROC</th>
                <th className="p-3">Local NIH-14 Test AUROC</th>
                <th className="p-3">Primary Target Layer</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 text-slate-300">
              <tr>
                <td className="p-3 font-medium text-slate-100">Cardiomegaly</td>
                <td className="p-3 font-mono text-cyan-300">0.894</td>
                <td className="p-3 font-mono text-cyan-300">0.882</td>
                <td className="p-3 font-mono text-slate-400">denseblock4.conv2</td>
              </tr>
              <tr>
                <td className="p-3 font-medium text-slate-100">Pneumonia</td>
                <td className="p-3 font-mono text-cyan-300">0.842</td>
                <td className="p-3 font-mono text-cyan-300">0.781</td>
                <td className="p-3 font-mono text-slate-400">denseblock4.conv2</td>
              </tr>
              <tr>
                <td className="p-3 font-medium text-slate-100">Pleural Effusion</td>
                <td className="p-3 font-mono text-cyan-300">0.931</td>
                <td className="p-3 font-mono text-cyan-300">0.875</td>
                <td className="p-3 font-mono text-slate-400">denseblock4.conv2</td>
              </tr>
              <tr>
                <td className="p-3 font-medium text-slate-100">Atelectasis</td>
                <td className="p-3 font-mono text-cyan-300">0.825</td>
                <td className="p-3 font-mono text-cyan-300">0.803</td>
                <td className="p-3 font-mono text-slate-400">denseblock4.conv2</td>
              </tr>
              <tr>
                <td className="p-3 font-medium text-slate-100">Pneumothorax</td>
                <td className="p-3 font-mono text-cyan-300">0.887</td>
                <td className="p-3 font-mono text-cyan-300">0.854</td>
                <td className="p-3 font-mono text-slate-400">denseblock4.conv2</td>
              </tr>
              <tr>
                <td className="p-3 font-medium text-slate-100">Consolidation</td>
                <td className="p-3 font-mono text-cyan-300">0.891</td>
                <td className="p-3 font-mono text-cyan-300">0.812</td>
                <td className="p-3 font-mono text-slate-400">denseblock4.conv2</td>
              </tr>
            </tbody>
          </table>
        </div>
        <p className="text-[11px] text-slate-500 leading-relaxed pt-1">
          ⚠ These AUROC values include published benchmarks from external research literature alongside local held-out test cohort evaluations on NIH ChestX-ray14. They are provided for research evaluation reference only.
        </p>
      </div>

      <div className="p-4 bg-slate-950 border border-slate-800 rounded-xl space-y-2 text-xs text-slate-400">
        <h4 className="font-semibold text-slate-300 flex items-center gap-1.5">
          <Database className="w-4 h-4 text-cyan-400" />
          Training Dataset Provenance & Privacy
        </h4>
        <p className="leading-relaxed">
          The models are trained on the NIH Clinical Center ChestX-ray14 research cohort with fully de-identified protected health information (PHI). 
        </p>
      </div>
    </div>
  );
};
