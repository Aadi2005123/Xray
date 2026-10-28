import React, { useEffect, useState } from 'react';
import { Header } from './components/Header';
import { LandingPage } from './pages/LandingPage';
import { AnalysisPage } from './pages/AnalysisPage';
import { ModelArchitecturePage } from './pages/ModelArchitecturePage';
import { analysisApi } from './services/analysisApi';
import { MANDATORY_MEDICAL_DISCLAIMER } from './utils/constants';
import { Activity, ShieldCheck } from 'lucide-react';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'landing' | 'analysis' | 'model'>('analysis');
  const [isBackendConnected, setIsBackendConnected] = useState<boolean>(false);

  useEffect(() => {
    // Check backend health
    const verifyHealth = async () => {
      try {
        const res = await analysisApi.checkHealth();
        setIsBackendConnected(res.status === 'ok');
      } catch {
        setIsBackendConnected(false);
      }
    };
    verifyHealth();
    const interval = setInterval(verifyHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col selection:bg-cyan-500 selection:text-white">
      {/* Navigation Header */}
      <Header
        activeTab={activeTab}
        onSelectTab={setActiveTab}
        isBackendConnected={isBackendConnected}
      />

      {/* Main Page Content */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 pb-16">
        {activeTab === 'landing' && (
          <LandingPage
            onStartAnalysis={() => setActiveTab('analysis')}
            onViewModelArchitecture={() => setActiveTab('model')}
          />
        )}
        {activeTab === 'analysis' && <AnalysisPage />}
        {activeTab === 'model' && <ModelArchitecturePage />}
      </main>

      {/* Global Clinical Footer */}
      <footer className="bg-slate-950 border-t border-slate-800/80 py-8 px-4 text-xs text-slate-400">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2.5">
            <div className="w-6 h-6 rounded bg-cyan-950 border border-cyan-800 flex items-center justify-center text-cyan-400">
              <Activity className="w-3.5 h-3.5" />
            </div>
            <span className="font-semibold text-slate-200">CXR-Explain Research Consortium</span>
            <span className="text-slate-600">|</span>
            <span>Version 2.4.0 (DenseNet-121 + Grad-CAM)</span>
          </div>

          <div className="text-center md:text-right text-[11px] text-slate-400 max-w-xl">
            <span className="font-medium text-amber-300/90">{MANDATORY_MEDICAL_DISCLAIMER}</span>
            <div className="flex items-center justify-center md:justify-end gap-3 mt-1 text-slate-400">
              <span className="flex items-center gap-1">
                <ShieldCheck className="w-3 h-3 text-emerald-400" />
                Stateless Memory Pipeline
              </span>
              <span>•</span>
              <span>CheXpert / NIH ChestX-ray14 Standards</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default App;
