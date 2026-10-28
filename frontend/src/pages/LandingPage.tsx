import React from 'react';
import {
  Activity,
  Layers,
  ShieldCheck,
  Cpu,
  ArrowRight,
  Eye,
  FileCheck,
  CheckCircle,
} from 'lucide-react';
import { MedicalDisclaimer } from '../components/MedicalDisclaimer';

interface LandingPageProps {
  onStartAnalysis: () => void;
  onViewModelArchitecture: () => void;
}

export const LandingPage: React.FC<LandingPageProps> = ({
  onStartAnalysis,
  onViewModelArchitecture,
}) => {
  return (
    <div className="space-y-12 py-6">
      {/* Hero Section */}
      <section className="text-center space-y-6 max-w-4xl mx-auto">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-cyan-950/80 text-cyan-300 border border-cyan-800/80">
          <Activity className="w-3.5 h-3.5" />
          <span>Explainable Deep Learning in Medical Imaging</span>
        </div>

        <h1 className="text-3xl sm:text-5xl font-extrabold text-slate-100 tracking-tight leading-tight">
          Explainable Real-Time <br />
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-400">
            Chest X-Ray Disease Detection
          </span>
        </h1>

        <p className="text-base sm:text-lg text-slate-400 max-w-2xl mx-auto leading-relaxed">
          Screen chest radiographs for critical thoracic pathologies in milliseconds. 
          Correlate multi-label deep learning predictions with Gradient-weighted Class Activation Mapping (Grad-CAM) saliency overlays.
        </p>

        {/* Primary CTA Buttons */}
        <div className="flex flex-wrap items-center justify-center gap-4 pt-2">
          <button
            onClick={onStartAnalysis}
            className="px-6 py-3 bg-cyan-600 hover:bg-cyan-500 text-white font-medium text-sm rounded-lg flex items-center gap-2 shadow-md hover:shadow-cyan-900/40 transition-all cursor-pointer"
          >
            <Layers className="w-4 h-4" />
            <span>Launch Radiograph Screener</span>
            <ArrowRight className="w-4 h-4" />
          </button>
          <button
            onClick={onViewModelArchitecture}
            className="px-6 py-3 bg-slate-900 hover:bg-slate-800 text-slate-300 font-medium text-sm rounded-lg border border-slate-700 transition-colors flex items-center gap-2"
          >
            <Cpu className="w-4 h-4 text-cyan-400" />
            <span>Model Architecture & Metrics</span>
          </button>
        </div>
      </section>

      {/* Mandatory Medical Safety Disclaimer */}
      <section className="max-w-4xl mx-auto">
        <MedicalDisclaimer />
      </section>

      {/* Key Feature Pillars */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-6xl mx-auto">
        <div className="p-6 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
          <div className="w-10 h-10 rounded-lg bg-cyan-950 border border-cyan-800 flex items-center justify-center text-cyan-400">
            <Cpu className="w-5 h-5" />
          </div>
          <h3 className="text-base font-semibold text-slate-100">Multi-Label Classification</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Evaluates 10 thoracic classes concurrently (Atelectasis, Cardiomegaly, Consolidation, Infiltration, Mass, Nodule, Pneumonia, Pneumothorax, Pleural Effusion, No Finding) using calibrated operating thresholds.
          </p>
        </div>

        <div className="p-6 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
          <div className="w-10 h-10 rounded-lg bg-cyan-950 border border-cyan-800 flex items-center justify-center text-cyan-400">
            <Eye className="w-5 h-5" />
          </div>
          <h3 className="text-base font-semibold text-slate-100">Grad-CAM Visual Saliency</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Computes gradients of target pathology activation scores relative to the final convolutional feature maps, visually isolating exact anatomical regions of interest with adjustable heatmap opacity.
          </p>
        </div>

        <div className="p-6 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
          <div className="w-10 h-10 rounded-lg bg-cyan-950 border border-cyan-800 flex items-center justify-center text-cyan-400">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <h3 className="text-base font-semibold text-slate-100">Zero-Retention Privacy</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Architected strictly as a stateless in-memory pipeline. Patient radiographs are processed in RAM and never written to disk or stored in external databases, ensuring privacy by design.
          </p>
        </div>
      </section>

      {/* Clinical Workflow Roadmap */}
      <section className="bg-slate-900/60 border border-slate-800 rounded-xl p-8 max-w-6xl mx-auto space-y-6">
        <h2 className="text-lg font-semibold text-slate-100 text-center tracking-tight">
          Standard Clinical Screening Pipeline
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="p-4 bg-slate-950 rounded-lg border border-slate-800 space-y-1.5">
            <span className="text-[11px] font-mono text-cyan-400 font-semibold">STAGE 01</span>
            <h4 className="text-xs font-semibold text-slate-200">Ingestion & Validation</h4>
            <p className="text-[11px] text-slate-400 leading-normal">
              Accepts frontal radiographs, verifies MIME type, magic bytes, and checks for optimal contrast.
            </p>
          </div>
          <div className="p-4 bg-slate-950 rounded-lg border border-slate-800 space-y-1.5">
            <span className="text-[11px] font-mono text-cyan-400 font-semibold">STAGE 02</span>
            <h4 className="text-xs font-semibold text-slate-200">Canonical Standardization</h4>
            <p className="text-[11px] text-slate-400 leading-normal">
              Resizes to 224x224, formats 3-channel RGB representation, and applies canonical ImageNet normalization.
            </p>
          </div>
          <div className="p-4 bg-slate-950 rounded-lg border border-slate-800 space-y-1.5">
            <span className="text-[11px] font-mono text-cyan-400 font-semibold">STAGE 03</span>
            <h4 className="text-xs font-semibold text-slate-200">DenseNet-121 Inference</h4>
            <p className="text-[11px] text-slate-400 leading-normal">
              Extracts high-order pulmonary features and computes multi-label sigmoid prediction scores.
            </p>
          </div>
          <div className="p-4 bg-slate-950 rounded-lg border border-slate-800 space-y-1.5">
            <span className="text-[11px] font-mono text-cyan-400 font-semibold">STAGE 04</span>
            <h4 className="text-xs font-semibold text-slate-200">Explainable Reporting</h4>
            <p className="text-[11px] text-slate-400 leading-normal">
              Renders authentic Grad-CAM overlay viewer and compiles audit-ready clinical observation summaries.
            </p>
          </div>
        </div>
      </section>

      {/* Validation Benchmark Indicators */}
      <section className="text-center space-y-3 pt-4 border-t border-slate-800/80 max-w-4xl mx-auto">
        <div className="flex flex-wrap items-center justify-center gap-6 text-xs text-slate-400">
          <span className="flex items-center gap-1.5">
            <CheckCircle className="w-4 h-4 text-emerald-400" />
            NIH ChestX-ray14 10-Class Model (Test Mean AUROC: 0.7793)
          </span>
          <span className="flex items-center gap-1.5">
            <CheckCircle className="w-4 h-4 text-emerald-400" />
            NIH Clinical Center Multi-Cohort Representation
          </span>
          <span className="flex items-center gap-1.5">
            <FileCheck className="w-4 h-4 text-cyan-400" />
            DICOM / Standard CXR Compatible
          </span>
        </div>
      </section>
    </div>
  );
};
