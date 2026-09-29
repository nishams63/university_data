import React, { useState } from 'react';
import { ShieldAlert, CheckCircle, XCircle, AlertTriangle, ArrowRight, Info, UserCheck, HelpCircle, Clock, Calendar, Hash, FileText } from 'lucide-react';
import { handleReviewAction } from '../api/client';

export default function ReviewTab({ reviews, onRefresh }) {
  const [processingId, setProcessingId] = useState(null);
  const [showExplanation, setShowExplanation] = useState(true);
  const [activeModalAction, setActiveModalAction] = useState(null); // { correctionId, action, rev }
  const [modalReason, setModalReason] = useState('');
  const [actionFeedback, setActionFeedback] = useState(null);

  const handleConfirmAction = async () => {
    if (!activeModalAction) return;
    const { correctionId, action } = activeModalAction;

    setProcessingId(correctionId);
    setActionFeedback(null);
    try {
      const res = await handleReviewAction(
        correctionId, 
        action, 
        'RTC Data Administrator',
        modalReason.trim() || undefined
      );
      setActionFeedback({
        type: 'success',
        message: action === 'APPROVE'
          ? `Successfully approved correction ${correctionId}. New report aggregate: ${res.aggregate} (v${res.new_version}).`
          : `Successfully rejected correction ${correctionId}. Previous aggregate ${res.aggregate} retained.`
      });
      setModalReason('');
      setActiveModalAction(null);
      onRefresh();
    } catch (e) {
      console.error(e);
      setActionFeedback({
        type: 'error',
        message: `Action failed: ${e.message}`
      });
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
            <span>Human-in-the-Loop Governance & Review Queue</span>
          </h2>
          <p className="text-xs text-slate-300 mt-0.5 font-medium">
            High-impact (≥15% drift) and high-risk academic corrections require verified Data Administrator sign-off.
          </p>
        </div>
        <span className="px-3 py-1 rounded-full text-xs font-bold bg-rose-500/20 text-rose-300 border border-rose-500/30">
          {reviews.length} Pending Review(s)
        </span>
      </div>

      {/* Action Feedback Banner */}
      {actionFeedback && (
        <div className={`p-4 rounded-xl text-xs font-semibold flex items-center justify-between border ${
          actionFeedback.type === 'success' 
            ? 'bg-emerald-950/80 border-emerald-500/40 text-emerald-200' 
            : 'bg-rose-950/80 border-rose-500/40 text-rose-200'
        }`}>
          <div className="flex items-center space-x-2">
            {actionFeedback.type === 'success' ? (
              <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0" />
            ) : (
              <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
            )}
            <span>{actionFeedback.message}</span>
          </div>
          <button 
            onClick={() => setActionFeedback(null)}
            className="text-xs opacity-70 hover:opacity-100 font-mono ml-3"
          >
            ✕
          </button>
        </div>
      )}

      {/* Explanation Banner: "Why is this correction waiting for review?" */}
      {showExplanation && (
        <div className="bg-slate-800/90 border border-indigo-700/40 p-4 rounded-xl shadow relative">
          <div className="flex items-start space-x-3">
            <HelpCircle className="w-5 h-5 text-indigo-400 shrink-0 mt-0.5" />
            <div className="text-xs space-y-1">
              <div className="font-bold text-slate-200">
                Institutional Policy: Why is an event routed to the Review Queue?
              </div>
              <p className="text-slate-300 leading-relaxed font-medium">
                Under Rathinam Technical Campus data governance, minor corrections (&lt;15% aggregate shift) are applied autonomously. Events are escalated to this human-in-the-loop queue under three conditions:
              </p>
              <ul className="list-disc list-inside space-y-0.5 text-slate-400 pt-1">
                <li><strong className="text-rose-300">High-Impact Threshold:</strong> The out-of-order event alters the historical aggregate by ≥ 15.0%.</li>
                <li><strong className="text-amber-300">High-Risk Outcome Alteration:</strong> The event modifies a pass/fail grade status or official placement drive offer.</li>
                <li><strong className="text-indigo-300">Bounded Watermark Violation:</strong> Event delay exceeds the 24-hour watermark window, requiring administrative audit.</li>
              </ul>
            </div>
          </div>
          <button 
            onClick={() => setShowExplanation(false)}
            className="absolute top-3 right-3 text-slate-500 hover:text-slate-300 text-xs font-mono"
            title="Dismiss explanation"
          >
            ✕
          </button>
        </div>
      )}

      {/* Review Cards Grid */}
      {reviews.length === 0 ? (
        <div className="bg-slate-800 border border-slate-700 p-12 text-center rounded-xl shadow">
          <CheckCircle className="w-12 h-12 text-emerald-400 mx-auto mb-3" />
          <h3 className="text-base font-bold text-white">No Reviews Pending</h3>
          <p className="text-xs text-slate-400 mt-1">
            All historical reports have converged with ground truth. Zero unreviewed high-impact drifts exist.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          {reviews.map((rev) => (
            <div key={rev.correction_id} className="bg-slate-800 border border-rose-500/40 p-5 rounded-xl space-y-4 shadow flex flex-col justify-between">
              
              <div className="space-y-3">
                
                {/* Card Header */}
                <div className="flex items-center justify-between border-b border-slate-700 pb-3">
                  <div className="flex items-center space-x-2">
                    <span className="px-2.5 py-0.5 rounded text-[10px] font-bold bg-rose-500/20 text-rose-300 border border-rose-500/30">
                      DRIFT: {rev.impact_percentage}%
                    </span>
                    <span className="px-2.5 py-0.5 rounded text-[10px] font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                      {rev.domain}
                    </span>
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30">
                      {rev.status}
                    </span>
                  </div>
                  <span className="text-xs font-mono text-slate-300 font-bold flex items-center space-x-1">
                    <Calendar className="w-3.5 h-3.5 text-slate-400" />
                    <span>{rev.reporting_date}</span>
                  </span>
                </div>

                {/* Primary Identifiers */}
                <div className="grid grid-cols-2 gap-2 text-xs bg-slate-900/60 p-2.5 rounded-lg border border-slate-800">
                  <div>
                    <span className="text-slate-400 block text-[10px] uppercase tracking-wider">Correction ID</span>
                    <span className="font-mono font-bold text-slate-200">{rev.correction_id}</span>
                  </div>
                  <div>
                    <span className="text-slate-400 block text-[10px] uppercase tracking-wider">Student ID</span>
                    <span className="font-mono font-bold text-indigo-300">{rev.student_id}</span>
                  </div>
                  <div className="col-span-2 pt-1 border-t border-slate-800/80">
                    <span className="text-slate-400 block text-[10px] uppercase tracking-wider">Trigger Event ID</span>
                    <span className="font-mono text-xs text-slate-300 truncate block">{rev.event_id}</span>
                  </div>
                </div>

                {/* Timestamps & Lateness Metrics */}
                <div className="grid grid-cols-3 gap-2 text-center text-xs font-mono bg-slate-950 p-2.5 rounded-lg border border-slate-800">
                  <div>
                    <span className="text-[10px] text-slate-400 font-sans block">Event Time</span>
                    <span className="text-slate-300 text-[11px] truncate block">
                      {rev.event_timestamp ? rev.event_timestamp.replace('T', ' ') : 'Historical'}
                    </span>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-400 font-sans block">Arrival Time</span>
                    <span className="text-slate-300 text-[11px] truncate block">
                      {rev.arrival_timestamp ? rev.arrival_timestamp.replace('T', ' ') : 'Recent'}
                    </span>
                  </div>
                  <div>
                    <span className="text-[10px] text-rose-400 font-sans font-bold block">Observed Delay</span>
                    <span className="text-rose-400 font-bold text-[11px]">
                      {rev.delay_hours !== undefined && rev.delay_hours !== null ? `${rev.delay_hours} hrs` : '> 24 hrs'}
                    </span>
                  </div>
                </div>

                {/* Step 25: Before / After Visual Comparison */}
                <div>
                  <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1.5 flex items-center space-x-1">
                    <FileText className="w-3 h-3 text-slate-400" />
                    <span>Stateful Aggregate Comparison:</span>
                  </div>
                  <div className="grid grid-cols-4 gap-2 bg-slate-950 p-2.5 rounded-lg border border-slate-700/80 text-center font-mono">
                    <div className="bg-slate-900/80 p-2 rounded border border-slate-800">
                      <span className="text-[10px] text-slate-400 font-sans block uppercase">Before</span>
                      <span className="text-sm font-bold text-slate-200">{rev.previous_value}</span>
                    </div>
                    <div className="bg-amber-950/40 p-2 rounded border border-amber-800/40">
                      <span className="text-[10px] text-amber-300 font-sans block uppercase">Delta</span>
                      <span className="text-sm font-bold text-amber-400">
                        {rev.delta_value > 0 ? `+${rev.delta_value}` : rev.delta_value}
                      </span>
                    </div>
                    <div className="bg-emerald-950/40 p-2 rounded border border-emerald-800/40">
                      <span className="text-[10px] text-emerald-300 font-sans block uppercase">Proposed</span>
                      <span className="text-sm font-bold text-emerald-400">{rev.corrected_value}</span>
                    </div>
                    <div className="bg-rose-950/40 p-2 rounded border border-rose-800/40">
                      <span className="text-[10px] text-rose-300 font-sans block uppercase">Impact</span>
                      <span className="text-sm font-bold text-rose-400">{rev.impact_percentage}%</span>
                    </div>
                  </div>
                </div>

                {/* Step 24: Dynamic Textual Explanation */}
                <div className="bg-indigo-950/40 border border-indigo-500/30 p-3 rounded-lg text-xs text-indigo-200">
                  <div className="flex items-center space-x-1.5 font-bold text-indigo-300 mb-1">
                    <Info className="w-3.5 h-3.5 text-indigo-400" />
                    <span>Dynamic System Justification:</span>
                  </div>
                  <p className="leading-relaxed">
                    {rev.dynamic_explanation || (
                      `This ${rev.domain.replace('RTC-', '')} event arrived ${rev.delay_hours ? rev.delay_hours.toFixed(1) : '96.0'} hours late and changes the historical aggregate from ${rev.previous_value} to ${rev.corrected_value}. The resulting ${rev.impact_percentage}% impact exceeds the configured 15% review threshold.`
                    )}
                  </p>
                </div>

                <div className="bg-amber-500/10 border border-amber-500/20 p-2 rounded-lg text-xs text-amber-300">
                  <strong>Escalation Trigger:</strong> {rev.reason}
                </div>

              </div>

              {/* Step 26: Action Buttons */}
              <div className="flex items-center space-x-3 pt-3 border-t border-slate-700">
                <button
                  disabled={processingId === rev.correction_id}
                  onClick={() => {
                    setModalReason('');
                    setActiveModalAction({ correctionId: rev.correction_id, action: 'APPROVE', rev });
                  }}
                  className="flex-1 py-2.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs shadow flex items-center justify-center space-x-1.5 disabled:opacity-50 transition-all"
                >
                  <CheckCircle className="w-4 h-4" />
                  <span>APPROVE CORRECTION</span>
                </button>

                <button
                  disabled={processingId === rev.correction_id}
                  onClick={() => {
                    setModalReason('');
                    setActiveModalAction({ correctionId: rev.correction_id, action: 'REJECT', rev });
                  }}
                  className="flex-1 py-2.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white font-bold text-xs shadow flex items-center justify-center space-x-1.5 disabled:opacity-50 transition-all"
                >
                  <XCircle className="w-4 h-4" />
                  <span>REJECT</span>
                </button>
              </div>

            </div>
          ))}
        </div>
      )}

      {/* Confirmation & Rejection Modal */}
      {activeModalAction && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-xl max-w-lg w-full p-6 space-y-4 shadow-2xl">
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
              <span className="font-mono text-indigo-300 font-bold">{activeModalAction.correctionId}</span> for{' '}
              <strong>{activeModalAction.rev?.domain}</strong> on historical date{' '}
              <strong>{activeModalAction.rev?.reporting_date}</strong>.
            </p>

            <div className="bg-slate-950 p-3 rounded-lg border border-slate-800 text-xs font-mono space-y-1">
              <div className="flex justify-between">
                <span className="text-slate-400">Current Aggregate:</span>
                <span className="text-slate-200 font-bold">{activeModalAction.rev?.previous_value}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Proposed Aggregate:</span>
                <span className="text-emerald-400 font-bold">{activeModalAction.rev?.corrected_value}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Impact Drift:</span>
                <span className="text-rose-400 font-bold">{activeModalAction.rev?.impact_percentage}%</span>
              </div>
            </div>

            {/* Optional Reason Input for Rejection / Approval Justification */}
            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-300 block">
                {activeModalAction.action === 'REJECT' ? 'Rejection Reason (Audit Evidence):' : 'Approval Justification Note (Optional):'}
              </label>
              <textarea
                rows={2}
                value={modalReason}
                onChange={(e) => setModalReason(e.target.value)}
                placeholder={
                  activeModalAction.action === 'REJECT'
                    ? 'e.g., Verified sensor anomaly; physical attendance register confirms student was absent.'
                    : 'e.g., Verified with departmental Dean; approved late submission.'
                }
                className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2.5 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
              />
            </div>

            <div className="flex justify-end space-x-3 pt-2">
              <button
                onClick={() => {
                  setActiveModalAction(null);
                  setModalReason('');
                }}
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
