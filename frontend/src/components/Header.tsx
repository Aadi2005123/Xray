import React from 'react';
import { Activity, Cpu, Layers } from 'lucide-react';
import { MedicalDisclaimer } from './MedicalDisclaimer';

interface HeaderProps {
  activeTab: 'landing' | 'analysis' | 'model';
  onSelectTab: (tab: 'landing' | 'analysis' | 'model') => void;
  isBackendConnected: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  activeTab,
  onSelectTab,
  isBackendConnected,
}) => {
  return (
    <header className="sticky top-0 z-40 bg-slate-950/95 backdrop-blur-md border-b border-slate-800">
      {/* Top micro disclaimer banner */}
      <div className="bg-amber-950/80 border-b border-amber-900/60 py-1 px-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between text-xs text-amber-200">
          <MedicalDisclaimer compact />
          <div className="hidden sm:flex items-center gap-4 text-slate-400">
            <span>No Data Stored · Stateless Mode</span>
            <span className="text-slate-600">|</span>
            <span>NIH ChestX-ray14 Baseline</span>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Platform Name */}
          <div className="flex items-center gap-3 cursor-pointer" onClick={() => onSelectTab('landing')}>
            <div className="w-10 h-10 rounded-lg bg-cyan-950 border border-cyan-700/60 flex items-center justify-center text-cyan-400 shadow-inner">
              <Activity className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-lg text-slate-100 tracking-tight">CXR-Explain</span>
                <span className="px-1.5 py-0.5 text-[10px] font-semibold tracking-wider text-cyan-300 bg-cyan-950/80 border border-cyan-800/80 rounded uppercase">
                  Research v2.4
                </span>
              </div>
              <p className="text-xs text-slate-400">Explainable Chest Radiograph Screening System</p>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="flex items-center gap-1 sm:gap-2">
            <button
              onClick={() => onSelectTab('landing')}
              className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
                activeTab === 'landing'
                  ? 'bg-slate-800 text-cyan-300'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
              }`}
            >
              Overview
            </button>
            <button
              onClick={() => onSelectTab('analysis')}
              className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors flex items-center gap-1.5 ${
                activeTab === 'analysis'
                  ? 'bg-cyan-900/60 text-cyan-200 border border-cyan-700/50'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
              }`}
            >
              <Layers className="w-4 h-4" />
              Analyze Radiograph
            </button>
            <button
              onClick={() => onSelectTab('model')}
              className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors flex items-center gap-1.5 ${
                activeTab === 'model'
                  ? 'bg-slate-800 text-cyan-300'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
              }`}
            >
              <Cpu className="w-4 h-4" />
              Architecture
            </button>
          </nav>

          {/* System Environment Badge */}
          <div className="hidden md:flex items-center gap-2.5">
            <div
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${
                isBackendConnected
                  ? 'bg-emerald-950/50 border-emerald-800/60 text-emerald-300'
                  : 'bg-cyan-950/40 border-cyan-800/50 text-cyan-300'
              }`}
            >
              <span
                className={`w-2 h-2 rounded-full ${
                  isBackendConnected ? 'bg-emerald-400 animate-pulse' : 'bg-cyan-400'
                }`}
              />
              {isBackendConnected ? 'FastAPI Engine Active' : 'Edge Research Mode'}
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};
