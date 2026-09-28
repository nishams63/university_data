import React, { useState } from 'react';
import { ShieldAlert, CheckCircle, XCircle, AlertTriangle, ArrowRight, Info, UserCheck, HelpCircle } from 'lucide-react';
import { handleReviewAction } from '../api/client';

export default function ReviewTab({ reviews, onRefresh }) {
  const [processingId, setProcessingId] = useState(null);
  const [showExplanation, setShowExplanation] = useState(true);
  const [activeModalAction, setActiveModalAction] = useState(null); // { correctionId, action, rev }

  const handleConfirmAction = async () => {
    if (!activeModalAction) return;
    const { correctionId, action } = activeModalAction;

    setProcessingId(correctionId);
    try {
      await handleReviewAction(correctionId, action, 'RTC Data Administrator');
      onRefresh();
      setActiveModalAction(null);
    } catch (e) {
      console.error(e);
      alert(`Error processing review: ${e.message}`);
    } finally {
      setProcessingId(null);
    }
  };

  return (
    <div className="space-y-6">
      
      {/* Header */}
      <div className="bg-slate-800 border border-slate-700 p-4 rounded-xl flex items-center justify-between shadow">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center space-x-2">
            <ShieldAlert className="w-5 h-5 text-rose-400" />
            <span>Human-in-the-Loop Review Queue</span>
          </h2>
          <p className="text-xs text-slate-300 mt-0.5 font-medium">
            High-impact and high-risk corrections require Data Administrator verification before official report updating.
          </p>
        </div>
        <span className="px-3 py-1 rounded-full text-xs font-bold bg-rose-500/20 text-rose-300 border border-rose-500/30">
          {reviews.length} Pending Review(s)
        </span>
      </div>

      {/* Explanation Banner: "Why is this correction waiting for review?" */}
      {showExplanation && (
        <div className="bg-slate-800/90 border border-indigo-700/40 p-4 rounded-xl shadow relative">
          <div className="flex items-start space-x-3">
            <HelpCircle className="w-5 h-5 text-indigo-400 shrink-0 mt-0.5" />
            <div className="text-xs space-y-1">
              <div className="font-bold text-slate-200">
                Why is an event flagged for Administrator Review?
              </div>
              <p className="text-slate-300 leading-relaxed font-medium">
                The Rathinam Technical Campus reporting policy dictates that routine corrections (&lt;15% aggregate shift) are applied automatically. However, events are routed to this human-in-the-loop review queue if:
              </p>
              <ul className="list-disc list-inside space-y-0.5 text-slate-400 pt-1">
                <li><strong className="text-rose-300">High-Impact Threshold:</strong> The late event causes an aggregate metric delta of ≥ 15%.</li>
                <li><strong className="text-amber-300">High-Risk Outcome Change:</strong> The late event alters a pass/fail grade status or official placement drive offer.</li>
                <li><strong className="text-indigo-300">Relational Boundary Violation:</strong> Historical records older than the standard watermark window require institutional sign-off.</li>
              </ul>
            </div>
          </div>
          <button 
            onClick={() => setShowExplanation(false)}
            className="absolute top-3 right-3 text-slate-500 hover:text-slate-300 text-xs font-mono"
          >
            ✕
          </button>
        </div>
      )}

      {/* Review Cards */}
      {reviews.length === 0 ? (
        <div className="bg-slate-800 border border-slate-700 p-12 text-center rounded-xl shadow">
          <CheckCircle className="w-12 h-12 text-emerald-400 mx-auto mb-3" />
          <h3 className="text-base font-bold text-white">No Reviews Pending</h3>
          <p className="text-xs text-slate-400 mt-1">
            All high-impact historical corrections have been approved or processed cleanly.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {reviews.map((rev) => (
            <div key={rev.correction_id} className="bg-slate-800 border border-rose-500/40 p-5 rounded-xl space-y-4 shadow flex flex-col justify-between">
              
              <div className="space-y-3">
                <div className="flex items-center justify-between border-b border-slate-700 pb-3">
                  <div className="flex items-center space-x-2">
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500/20 text-rose-300 border border-rose-500/30">
                      HIGH IMPACT ({rev.impact_percentage}%)
                    </span>
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-700 text-slate-300">
                      {rev.domain}
                    </span>
                  </div>
                  <span className="text-xs font-mono text-slate-400">{rev.reporting_date}</span>
                </div>

                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div>
                    <span className="text-slate-400 block text-[10px]">Student ID</span>
                    <span className="font-bold text-slate-200 font-mono">{rev.student_id}</span>
                  </div>
                  <div>
                    <span className="text-slate-400 block text-[10px]">Trigger Event ID</span>
                    <span className="font-mono text-indigo-300 truncate block">{rev.event_id}</span>
                  </div>
                </div>

                {/* Before / After Diff Visualizer */}
                <div className="bg-slate-900 p-3.5 rounded-lg border border-slate-700/80 flex items-center justify-between text-xs font-mono">
                  <div>
                    <span className="text-slate-400 block text-[10px] font-sans">Current Aggregate</span>
                    <span className="text-slate-300 font-bold text-sm">{rev.previous_value}</span>
                  </div>
                  <div className="text-center px-2">
                    <span className="text-[10px] text-amber-400 font-sans font-bold block">
                      +{rev.delta_value} ({rev.impact_percentage}%)
                    </span>
                    <ArrowRight className="w-4 h-4 text-amber-400 mx-auto" />
                  </div>
                  <div className="text-right">
                    <span className="text-slate-400 block text-[10px] font-sans">Proposed Aggregate</span>
                    <span className="text-emerald-400 font-bold text-sm">{rev.corrected_value}</span>
                  </div>
                </div>

                <div className="bg-amber-500/10 border border-amber-500/20 p-2.5 rounded-lg text-xs text-amber-300">
                  <strong>Trigger Reason:</strong> {rev.reason}
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center space-x-3 pt-3 border-t border-slate-700">
                <button
                  disabled={processingId === rev.correction_id}
                  onClick={() => setActiveModalAction({ correctionId: rev.correction_id, action: 'APPROVE', rev })}
                  className="flex-1 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs shadow flex items-center justify-center space-x-1.5 disabled:opacity-50 transition-all"
                >
                  <CheckCircle className="w-4 h-4" />
                  <span>APPROVE CORRECTION</span>
                </button>

                <button
                  disabled={processingId === rev.correction_id}
                  onClick={() => setActiveModalAction({ correctionId: rev.correction_id, action: 'REJECT', rev })}
                  className="flex-1 py-2 rounded-lg bg-rose-600 hover:bg-rose-500 text-white font-bold text-xs shadow flex items-center justify-center space-x-1.5 disabled:opacity-50 transition-all"
                >
                  <XCircle className="w-4 h-4" />
                  <span>REJECT</span>
                </button>
              </div>

            </div>
          ))}
        </div>
      )}

      {/* Confirmation Modal */}
      {activeModalAction && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-xl max-w-md w-full p-6 space-y-4 shadow-2xl">
            <div className="flex items-center space-x-3">
              {activeModalAction.action === 'APPROVE' ? (
                <CheckCircle className="w-6 h-6 text-emerald-400" />
              ) : (
                <XCircle className="w-6 h-6 text-rose-400" />
              )}
              <h3 className="text-base font-bold text-white">
                Confirm {activeModalAction.action === 'APPROVE' ? 'Approval' : 'Rejection'}
              </h3>
            </div>

            <p className="text-xs text-slate-300 font-medium leading-relaxed">
              You are about to <strong>{activeModalAction.action}</strong> correction{' '}
              <span className="font-mono text-indigo-300">{activeModalAction.correctionId}</span> for{' '}
              <strong>{activeModalAction.rev?.domain}</strong> on date{' '}
              <strong>{activeModalAction.rev?.reporting_date}</strong>.
            </p>

            <div className="bg-slate-950 p-3 rounded-lg border border-slate-800 text-xs font-mono">
              <div>Previous Value: {activeModalAction.rev?.previous_value}</div>
              <div>Proposed Value: {activeModalAction.rev?.corrected_value}</div>
              <div>Relative Impact: {activeModalAction.rev?.impact_percentage}%</div>
            </div>

            <div className="flex justify-end space-x-3 pt-2">
              <button
                onClick={() => setActiveModalAction(null)}
                className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold"
              >
                Cancel
              </button>
              <button
                disabled={processingId !== null}
                onClick={handleConfirmAction}
                className={`px-4 py-2 rounded-lg text-white font-bold text-xs shadow flex items-center space-x-1.5 ${
                  activeModalAction.action === 'APPROVE'
                    ? 'bg-emerald-600 hover:bg-emerald-500'
                    : 'bg-rose-600 hover:bg-rose-500'
                }`}
              >
                <span>Confirm {activeModalAction.action}</span>
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
