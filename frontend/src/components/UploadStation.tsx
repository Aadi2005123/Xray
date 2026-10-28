import React, { useRef, useState } from 'react';
import {
  UploadCloud,
  FileCheck,
  AlertCircle,
  FileImage,
  ArrowRight,
  Sparkles,
} from 'lucide-react';
import type { SampleCxrCase } from '../types';
import { ACCEPTED_IMAGE_TYPES, MAX_FILE_SIZE_BYTES } from '../utils/constants';
import { formatFileSize } from '../utils/medicalFormatters';
import { SAMPLE_CXR_CASES } from '../utils/sampleData';

interface UploadStationProps {
  onFileSelect: (file: File | Blob, fileName: string) => void;
  selectedFile: { file: File | Blob; fileName: string; previewUrl: string } | null;
  onClear: () => void;
  isAnalyzing: boolean;
  onStartAnalysis: () => void;
}

export const UploadStation: React.FC<UploadStationProps> = ({
  onFileSelect,
  selectedFile,
  onClear,
  isAnalyzing,
  onStartAnalysis,
}) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const validateAndProcessFile = (file: File) => {
    setErrorMsg(null);

    // MIME type check
    if (!ACCEPTED_IMAGE_TYPES.includes(file.type)) {
      setErrorMsg(
        `Unsupported file type (${file.type || 'unknown'}). Please provide a standard chest radiograph in PNG, JPEG, or WebP format.`
      );
      return;
    }

    // Size limit check
    if (file.size > MAX_FILE_SIZE_BYTES) {
      setErrorMsg(
        `File size (${formatFileSize(file.size)}) exceeds maximum limit of 10MB. Please downscale radiograph.`
      );
      return;
    }

    onFileSelect(file, file.name);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      validateAndProcessFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      validateAndProcessFile(e.target.files[0]);
    }
  };

  const loadSampleCase = async (sample: SampleCxrCase) => {
    setErrorMsg(null);
    try {
      const res = await fetch(sample.fullDataUrl);
      const blob = await res.blob();
      onFileSelect(blob, `${sample.id}_${sample.category.toLowerCase()}.png`);
    } catch {
      setErrorMsg('Failed to load sample radiograph.');
    }
  };

  return (
    <div className="space-y-6">
      {/* Upload Dropzone Card */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-md">
        <div className="flex items-center justify-between pb-4 mb-4 border-b border-slate-800">
          <div>
            <h3 className="text-base font-semibold text-slate-100 flex items-center gap-2">
              <UploadCloud className="w-5 h-5 text-cyan-400" />
              Chest Radiograph Ingestion Station
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Upload standard Frontal (PA or AP) radiograph for automated anomaly screening
            </p>
          </div>
          <div className="text-right text-xs text-slate-400">
            <span>Accepted: PNG, JPEG, WebP</span>
            <span className="block text-slate-500">Max size: 10MB</span>
          </div>
        </div>

        {errorMsg && (
          <div
            className="mb-4 p-3 bg-rose-950/50 border border-rose-800/80 rounded-lg text-rose-200 text-xs flex items-center gap-2.5"
            role="alert"
          >
            <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        {!selectedFile ? (
          /* Empty / Ingestion State */
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`border-2 border-dashed rounded-xl p-8 sm:p-12 text-center cursor-pointer transition-all duration-200 ${
              isDragOver
                ? 'border-cyan-400 bg-cyan-950/20'
                : 'border-slate-700 hover:border-slate-500 bg-slate-950/50'
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".png,.jpg,.jpeg,.webp"
              onChange={handleFileInputChange}
              className="hidden"
            />
            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-300">
              <FileImage className="w-8 h-8 text-cyan-400" />
            </div>
            <h4 className="text-sm font-medium text-slate-200 mb-1">
              Drag & Drop Chest X-Ray Here, or <span className="text-cyan-400 underline">Browse</span>
            </h4>
            <p className="text-xs text-slate-400 max-w-md mx-auto">
              Ensure high signal-to-noise ratio. Anonymized frontal projection recommended for optimal DenseNet-121 feature activation.
            </p>
          </div>
        ) : (
          /* Preview State */
          <div className="bg-slate-950 border border-slate-800 rounded-xl p-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-center">
              <div className="md:col-span-1 radiology-canvas rounded-lg overflow-hidden border border-slate-800 flex items-center justify-center p-2">
                <img
                  src={selectedFile.previewUrl}
                  alt="Selected Chest Radiograph"
                  className="max-h-56 object-contain rounded"
                />
              </div>

              <div className="md:col-span-2 space-y-4">
                <div className="space-y-1.5">
                  <div className="flex items-center gap-2">
                    <FileCheck className="w-4 h-4 text-emerald-400" />
                    <span className="text-xs uppercase tracking-wider font-semibold text-emerald-400">
                      Radiograph Verified
                    </span>
                  </div>
                  <h4 className="text-sm font-semibold text-slate-100 truncate">
                    {selectedFile.fileName}
                  </h4>
                  <div className="flex items-center gap-4 text-xs text-slate-400">
                    <span>Size: {formatFileSize(selectedFile.file.size)}</span>
                    <span>•</span>
                    <span>Projection: Standard Frontal</span>
                    <span>•</span>
                    <span>Type: {selectedFile.file.type || 'image/png'}</span>
                  </div>
                </div>

                <div className="p-3 bg-slate-900 border border-slate-800 rounded-lg text-xs text-slate-300 space-y-1">
                  <span className="font-semibold text-slate-200">Preprocessing Pipeline Target:</span>
                  <p className="text-slate-400">
                    Spatial rescaling (224x224), 3-channel RGB replication, canonical ImageNet z-score normalization (strictly no CLAHE per baseline standard).
                  </p>
                </div>

                <div className="flex items-center gap-3 pt-2">
                  <button
                    onClick={onStartAnalysis}
                    disabled={isAnalyzing}
                    className="flex-1 px-4 py-2.5 bg-cyan-600 hover:bg-cyan-500 disabled:bg-cyan-800 disabled:opacity-60 text-white text-sm font-medium rounded-lg flex items-center justify-center gap-2 shadow-sm transition-colors cursor-pointer"
                  >
                    <span>{isAnalyzing ? 'Processing Pipeline...' : 'Run Deep Learning Analysis'}</span>
                    <ArrowRight className="w-4 h-4" />
                  </button>
                  <button
                    onClick={onClear}
                    disabled={isAnalyzing}
                    className="px-4 py-2.5 bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-slate-300 text-sm font-medium rounded-lg border border-slate-700 transition-colors"
                  >
                    Clear
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Pre-loaded Benchmark Sample Library */}
      <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-5">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-cyan-400" />
            <h4 className="text-xs uppercase font-semibold tracking-wider text-slate-300">
              Benchmark Clinical Test Cases (1-Click Instant Evaluation)
            </h4>
          </div>
          <span className="text-[11px] text-slate-500">Curated from NIH ChestX-ray14 Benchmark</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {SAMPLE_CXR_CASES.map((sample) => (
            <button
              key={sample.id}
              onClick={() => loadSampleCase(sample)}
              disabled={isAnalyzing}
              className="group text-left p-3 rounded-lg bg-slate-950 border border-slate-800 hover:border-cyan-600/70 hover:bg-slate-900 transition-all cursor-pointer"
            >
              <div className="flex gap-3 items-center">
                <div className="w-14 h-14 shrink-0 rounded bg-black border border-slate-800 overflow-hidden flex items-center justify-center">
                  <img
                    src={sample.thumbnailSvg}
                    alt={sample.title}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform"
                  />
                </div>
                <div className="min-w-0 flex-1">
                  <span className="inline-block text-[10px] font-semibold uppercase tracking-wider text-cyan-400">
                    {sample.category}
                  </span>
                  <p className="text-xs font-medium text-slate-200 truncate mt-0.5">
                    {sample.title}
                  </p>
                  <p className="text-[11px] text-slate-400 line-clamp-1 mt-0.5">
                    {sample.summary}
                  </p>
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};
