import React, { useState } from 'react';
import { ShieldAlert, CheckCircle, XCircle, AlertTriangle, ArrowRight } from 'lucide-react';
import { handleReviewAction } from '../api/client';

export default function ReviewTab({ reviews, onRefresh }) {
  const [processingId, setProcessingId] = useState(null);

  const onAction = async (correctionId, action) => {
    const actionText = action.toLowerCase();
    const confirmMsg = `Are you sure you want to ${actionText} this high-impact correction?\nThis will update official reports for Rathinam Technical Campus.`;
    if (!window.confirm(confirmMsg)) return;

    setProcessingId(correctionId);
    try {
      await handleReviewAction(correctionId, action, 'RTC Data Administrator');
      onRefresh();
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
      <div className="bg-slate-800 border border-slate-700 p-4 rounded-xl flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center space-x-2">
            <ShieldAlert className="w-5 h-5 text-rose-400" />
            <span>Review Required</span>
          </h2>
          <p className="text-xs text-slate-300 mt-0.5 font-medium">
            High-impact changes require a Data Administrator to approve them before becoming official.
          </p>
        </div>
        <span className="px-3 py-1 rounded-full text-xs font-bold bg-rose-500/20 text-rose-300 border border-rose-500/30">
          {reviews.length} Pending Approval(s)
        </span>
      </div>

      {/* Review Cards */}
      {reviews.length === 0 ? (
        <div className="bg-slate-800 border border-slate-700 p-12 text-center rounded-xl">
          <CheckCircle className="w-12 h-12 text-emerald-400 mx-auto mb-3" />
          <h3 className="text-base font-bold text-white">No Reviews Pending</h3>
          <p className="text-xs text-slate-400 mt-1">
            All high-impact historical corrections have been approved or processed cleanly.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {reviews.map((rev) => (
            <div key={rev.correction_id} className="bg-slate-800 border border-rose-500/30 p-5 rounded-xl space-y-4 shadow">
              
              <div className="flex items-center justify-between border-b border-slate-700 pb-3">
                <div className="flex items-center space-x-2">
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500/20 text-rose-300 border border-rose-500/30">
                    HIGH IMPACT ({rev.impact_percentage}%)
                  </span>
                </div>
                <span className="text-xs font-semibold text-indigo-300">{rev.domain}</span>
              </div>

              <div className="grid grid-cols-2 gap-2 text-xs">
                <div>
                  <span className="text-slate-400 block text-[10px]">Report Date</span>
                  <span className="font-bold text-slate-200">{rev.reporting_date || '2026-08-20'}</span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[10px]">Correction ID</span>
                  <span className="font-mono text-slate-300">{rev.correction_id}</span>
                </div>
              </div>

              {/* Values Diff */}
              <div className="bg-slate-900 p-3 rounded-lg border border-slate-700 flex items-center justify-between text-xs font-mono">
                <div>
                  <span className="text-slate-400 block text-[10px] font-sans">Previous</span>
                  <span className="text-slate-300 font-bold text-sm">{rev.previous_value}</span>
                </div>
                <ArrowRight className="w-4 h-4 text-amber-400" />
                <div className="text-right">
                  <span className="text-slate-400 block text-[10px] font-sans">Proposed</span>
                  <span className="text-emerald-400 font-bold text-sm">{rev.corrected_value}</span>
                </div>
              </div>

              <div className="bg-amber-500/10 border border-amber-500/20 p-2.5 rounded-lg text-xs text-amber-300">
                <strong>Reason:</strong> {rev.reason}
              </div>

              {/* Action Buttons */}
              <div className="flex items-center space-x-3 pt-2">
                <button
                  disabled={processingId === rev.correction_id}
                  onClick={() => onAction(rev.correction_id, 'APPROVE')}
                  className="flex-1 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs shadow flex items-center justify-center space-x-1.5 disabled:opacity-50"
                >
                  <CheckCircle className="w-4 h-4" />
                  <span>APPROVE</span>
                </button>

                <button
                  disabled={processingId === rev.correction_id}
                  onClick={() => onAction(rev.correction_id, 'REJECT')}
                  className="flex-1 py-2 rounded-lg bg-rose-600 hover:bg-rose-500 text-white font-bold text-xs shadow flex items-center justify-center space-x-1.5 disabled:opacity-50"
                >
                  <XCircle className="w-4 h-4" />
                  <span>REJECT</span>
                </button>
              </div>

            </div>
          ))}
        </div>
      )}

    </div>
  );
}
