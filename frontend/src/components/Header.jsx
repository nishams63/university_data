import React from 'react';
import { Building2, Play, RefreshCw, CheckCircle, AlertTriangle } from 'lucide-react';

export default function Header({ metrics, onRunDemo, isRunningDemo, activeTab, setActiveTab }) {
  const tabs = [
    { id: 'dashboard', label: 'Dashboard' },
    { id: 'reports', label: 'Reports' },
    { id: 'events', label: 'Events' },
    { id: 'review', label: 'Review', count: metrics?.pending_reviews },
    { id: 'audit', label: 'Audit' },
    { id: 'experiment', label: 'Experiment' }
  ];

  return (
    <header className="bg-slate-900 border-b border-slate-800 sticky top-0 z-30 shadow-md">
      {/* Simulation Disclaimer Banner */}
      <div className="bg-slate-950 border-b border-slate-800 px-4 py-1.5 text-xs text-slate-300 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <span className="w-2 h-2 rounded-full bg-amber-400"></span>
          <span><strong>RATHINAM TECHNICAL CAMPUS</strong> — Synthetic Demonstration Data</span>
        </div>
        <div className="text-[11px] text-slate-300">
          Late Delay Threshold: 24h | High-Impact Drift: ≥15%
        </div>
      </div>

      {/* Main Header Container */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          
          {/* Identity */}
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-lg bg-indigo-600 flex items-center justify-center text-white font-bold shadow">
              <Building2 className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight text-white flex items-center space-x-2">
                <span>RATHINAM TECHNICAL CAMPUS</span>
              </h1>
              <p className="text-xs font-medium text-slate-300">
                Late-Event Correction System — <span className="italic text-slate-400">"Correcting historical reports when university events arrive late."</span>
              </p>
            </div>
          </div>

          {/* Primary Demo Button */}
          <div className="flex items-center space-x-3">
            <button
              onClick={onRunDemo}
              disabled={isRunningDemo}
              className="flex items-center space-x-2 px-5 py-2.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-sm shadow transition-all disabled:opacity-50"
            >
              {isRunningDemo ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Executing Demo...</span>
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 fill-white" />
                  <span>RUN DEMONSTRATION</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* 6 Top-Level Navigation Tabs */}
        <nav className="flex space-x-1 mt-4 overflow-x-auto pb-1 border-b border-slate-800">
          {tabs.map((t) => (
            <button
              key={t.id}
              onClick={() => setActiveTab(t.id)}
              className={`px-4 py-2 text-sm font-semibold rounded-t-lg transition-colors whitespace-nowrap flex items-center space-x-2 ${
                activeTab === t.id
                  ? 'bg-indigo-600 text-white shadow'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
              }`}
            >
              <span>{t.label}</span>
              {t.count !== undefined && t.count > 0 && (
                <span className="ml-1 px-2 py-0.5 text-xs font-extrabold bg-rose-500 text-white rounded-full">
                  {t.count}
                </span>
              )}
            </button>
          ))}
        </nav>

      </div>
    </header>
  );
}
