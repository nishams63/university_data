import React, { useState } from 'react';
import { CheckCircle, Play, ChevronRight, ChevronLeft, RotateCcw, ShieldCheck, Clock, FileCheck } from 'lucide-react';

export default function DemoModal({ demoResult, onClose }) {
  const [currentStepIndex, setCurrentStepIndex] = useState(0);

  if (!demoResult || !demoResult.timeline) return null;

  const timeline = demoResult.timeline;
  const currentStep = timeline[currentStepIndex];
  const totalSteps = timeline.length;

  return (
    <div className="fixed inset-0 bg-slate-950/85 backdrop-blur-md z-50 flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-700 rounded-2xl max-w-2xl w-full p-6 space-y-6 shadow-2xl">
        
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div>
            <div className="flex items-center space-x-2">
              <span className="px-2.5 py-0.5 rounded text-[11px] font-extrabold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
                LIVE DEMONSTRATION
              </span>
              <h2 className="text-lg font-bold text-white">System Execution Walkthrough</h2>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">Rathinam Technical Campus — Late Event & Correction Sequence</p>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white text-xl font-bold px-2 py-1"
          >
            ✕
          </button>
        </div>

        {/* Progress Indicator */}
        <div className="space-y-2">
          <div className="flex justify-between items-center text-xs font-bold text-slate-300">
            <span>Step {currentStepIndex + 1} of {totalSteps}</span>
            <span className="text-indigo-400">{currentStep.title}</span>
          </div>

          <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
            <div
              className="bg-indigo-500 h-full transition-all duration-300"
              style={{ width: `${((currentStepIndex + 1) / totalSteps) * 100}%` }}
            ></div>
          </div>
        </div>

        {/* Current Step Content */}
        <div className="bg-slate-800/90 border border-slate-700/80 p-5 rounded-xl space-y-4 shadow">
          <div className="flex items-center justify-between border-b border-slate-700/60 pb-2">
            <h3 className="text-base font-bold text-white flex items-center space-x-2">
              <span className="w-6 h-6 rounded-full bg-indigo-600 text-white text-xs flex items-center justify-center font-bold">
                {currentStep.step}
              </span>
              <span>{currentStep.title}</span>
            </h3>
            <span className="text-xs font-mono text-slate-400">{currentStep.timestamp}</span>
          </div>

          <p className="text-sm text-slate-200 font-medium leading-relaxed">
            {currentStep.description}
          </p>

          {/* Details Box */}
          <div className="bg-slate-950 p-4 rounded-lg border border-slate-800 text-xs font-mono space-y-1.5 text-slate-300">
            {Object.entries(currentStep.details || {}).map(([key, val]) => (
              <div key={key} className="flex justify-between border-b border-slate-900 pb-1">
                <span className="text-slate-400 font-sans">{key.replace(/_/g, ' ')}:</span>
                <span className="font-bold text-emerald-400">{String(val)}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Navigation Buttons */}
        <div className="flex items-center justify-between border-t border-slate-800 pt-4">
          <button
            disabled={currentStepIndex === 0}
            onClick={() => setCurrentStepIndex(prev => prev - 1)}
            className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold flex items-center space-x-1 disabled:opacity-40"
          >
            <ChevronLeft className="w-4 h-4" />
            <span>Previous Step</span>
          </button>

          {currentStepIndex < totalSteps - 1 ? (
            <button
              onClick={() => setCurrentStepIndex(prev => prev + 1)}
              className="px-5 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-extrabold flex items-center space-x-1 shadow"
            >
              <span>Next Step</span>
              <ChevronRight className="w-4 h-4" />
            </button>
          ) : (
            <button
              onClick={onClose}
              className="px-5 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-extrabold flex items-center space-x-1 shadow"
            >
              <CheckCircle className="w-4 h-4" />
              <span>Complete Walkthrough</span>
            </button>
          )}
        </div>

      </div>
    </div>
  );
}
