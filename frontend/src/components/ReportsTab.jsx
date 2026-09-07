import React, { useState } from 'react';
import { FileText, Eye, RotateCcw, ChevronDown, ChevronUp, CheckCircle, Clock, AlertTriangle } from 'lucide-react';
import { fetchReportVersions, triggerRollback } from '../api/client';

export default function ReportsTab({ reports, onRefresh }) {
  const [selectedReport, setSelectedReport] = useState(null);
  const [versions, setVersions] = useState([]);
  const [showTechDetails, setShowTechDetails] = useState(false);
  const [isRollingBack, setIsRollingBack] = useState(false);

  const handleOpenDetails = async (rpt) => {
    setSelectedReport(rpt);
    setShowTechDetails(false);
    try {
      const vData = await fetchReportVersions(rpt.report_id);
      setVersions(vData);
    } catch (e) {
      console.error(e);
    }
  };

  const handleRollback = async (corrId) => {
    if (!selectedReport) return;
    const confirmMsg = `Rollback this correction?\n\nCurrent Aggregate: ${selectedReport.corrected_aggregate}\nRestored Aggregate: ${selectedReport.baseline_aggregate}\n\nRollback will be recorded in audit history as a compensating action.`;
    if (!window.confirm(confirmMsg)) return;

    setIsRollingBack(true);
    try {
      await triggerRollback(corrId, "Data Administrator manual rollback from Report Details");
      alert("Rollback recorded in audit history.");
      onRefresh();
      setSelectedReport(null);
    } catch (e) {
      console.error(e);
      alert(`Rollback failed: ${e.message}`);
    } finally {
      setIsRollingBack(false);
    }
  };

  return (
    <div className="space-y-6">
      
      {/* Header */}
      <div className="bg-slate-800 border border-slate-700 p-4 rounded-xl flex justify-between items-center">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center space-x-2">
            <FileText className="w-5 h-5 text-indigo-400" />
            <span>Daily Reports</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Comparing initial snapshot daily reports against historical corrected aggregates after late events arrive.
          </p>
        </div>
        <span className="text-xs font-semibold text-slate-300 bg-slate-900 px-3 py-1 rounded-full border border-slate-700">
          {reports.length} Total Reports
        </span>
      </div>

      {/* Simplified Reports Table */}
      <div className="bg-slate-800 border border-slate-700 rounded-xl overflow-hidden shadow">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-900 border-b border-slate-700 text-xs font-bold text-slate-400 uppercase tracking-wider">
                <th className="py-3 px-4">Date</th>
                <th className="py-3 px-4">Domain</th>
                <th className="py-3 px-4">Before (Baseline)</th>
                <th className="py-3 px-4">After (Corrected)</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700/60 text-xs font-mono">
              {reports.map((rpt) => {
                const isCorrected = rpt.corrected_aggregate !== rpt.baseline_aggregate || rpt.current_version > 1;
                return (
                  <tr key={rpt.report_id} className="hover:bg-slate-700/40 transition-colors">
                    <td className="py-3.5 px-4 font-bold text-slate-200 font-sans">{rpt.reporting_date}</td>
                    <td className="py-3.5 px-4 text-indigo-300 font-sans font-semibold">{rpt.domain}</td>
                    <td className="py-3.5 px-4 text-slate-300 font-bold">{rpt.baseline_aggregate}</td>
                    <td className={`py-3.5 px-4 font-bold ${isCorrected ? 'text-emerald-400' : 'text-slate-300'}`}>
                      {rpt.corrected_aggregate}
                    </td>
                    <td className="py-3.5 px-4 font-sans">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        isCorrected ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' : 'bg-slate-700 text-slate-300'
                      }`}>
                        {isCorrected ? 'CORRECTED' : 'NO CHANGE'}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-right font-sans">
                      <button
                        onClick={() => handleOpenDetails(rpt)}
                        className="px-3 py-1 rounded bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs inline-flex items-center space-x-1"
                      >
                        <Eye className="w-3.5 h-3.5" />
                        <span>Details</span>
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* REPORT DETAILS & ROLLBACK MODAL */}
      {selectedReport && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-xl max-w-xl w-full p-6 space-y-5 shadow-2xl">
            
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <h3 className="text-base font-bold text-white flex items-center space-x-2">
                  <FileText className="w-5 h-5 text-indigo-400" />
                  <span>REPORT DETAILS</span>
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">{selectedReport.domain} — {selectedReport.reporting_date}</p>
              </div>
              <button
                onClick={() => setSelectedReport(null)}
                className="text-slate-400 hover:text-white text-lg font-bold px-2 py-1"
              >
                ✕
              </button>
            </div>

            {/* Key Summary Cards */}
            <div className="grid grid-cols-2 gap-3 text-xs font-sans">
              <div className="bg-slate-800 p-3 rounded-lg border border-slate-700">
                <span className="text-slate-400 block text-[10px]">Reporting Date</span>
                <span className="font-bold text-white text-sm">{selectedReport.reporting_date}</span>
              </div>
              <div className="bg-slate-800 p-3 rounded-lg border border-slate-700">
                <span className="text-slate-400 block text-[10px]">Domain</span>
                <span className="font-bold text-indigo-300 text-sm">{selectedReport.domain}</span>
              </div>
              <div className="bg-slate-800 p-3 rounded-lg border border-slate-700">
                <span className="text-slate-400 block text-[10px]">Initial Report (Baseline)</span>
                <span className="font-mono font-bold text-slate-200 text-sm">{selectedReport.baseline_aggregate}</span>
              </div>
              <div className="bg-slate-800 p-3 rounded-lg border border-slate-700">
                <span className="text-slate-400 block text-[10px]">Corrected Report</span>
                <span className="font-mono font-bold text-emerald-400 text-sm">{selectedReport.corrected_aggregate}</span>
              </div>
              <div className="bg-slate-800 p-3 rounded-lg border border-slate-700">
                <span className="text-slate-400 block text-[10px]">Ground Truth (Independent)</span>
                <span className="font-mono font-bold text-emerald-400 text-sm">{selectedReport.ground_truth_aggregate}</span>
              </div>
              <div className="bg-slate-800 p-3 rounded-lg border border-slate-700">
                <span className="text-slate-400 block text-[10px]">Error Before → After</span>
                <span className="font-mono font-bold text-slate-200 text-sm">{selectedReport.baseline_error} → {selectedReport.corrected_error}</span>
              </div>
            </div>

            {/* Version & Rollback Action */}
            <div className="bg-slate-800/90 border border-slate-700 p-4 rounded-lg flex items-center justify-between">
              <div>
                <div className="text-xs font-bold text-slate-300">Report Version: <span className="text-indigo-400 font-mono font-bold">v{selectedReport.current_version}</span></div>
                <div className="text-xs text-slate-400 mt-0.5">
                  Current: <strong className="text-emerald-400">{selectedReport.corrected_aggregate}</strong> | Baseline: <strong className="text-slate-300">{selectedReport.baseline_aggregate}</strong>
                </div>
              </div>

              {selectedReport.current_version > 1 && (
                <button
                  disabled={isRollingBack}
                  onClick={() => handleRollback(versions[versions.length - 1]?.correction_id || `CORR-${selectedReport.report_id}`)}
                  className="px-3 py-2 rounded bg-amber-600 hover:bg-amber-500 text-white font-bold text-xs shadow flex items-center space-x-1 disabled:opacity-50"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                  <span>ROLLBACK</span>
                </button>
              )}
            </div>

            {/* Collapsible Technical Details */}
            <div className="border-t border-slate-800 pt-3">
              <button
                onClick={() => setShowTechDetails(!showTechDetails)}
                className="text-xs font-semibold text-slate-400 hover:text-slate-200 flex items-center space-x-1"
              >
                <span>Technical Details</span>
                {showTechDetails ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
              </button>

              {showTechDetails && (
                <div className="mt-3 bg-slate-950 p-3 rounded-lg border border-slate-800 font-mono text-[11px] text-slate-300 space-y-2">
                  <div>Report ID: <span className="text-indigo-300">{selectedReport.report_id}</span></div>
                  <div>Metric Name: <span className="text-slate-400">{selectedReport.metric_name}</span></div>
                  <div>Status: <span className="text-emerald-400">{selectedReport.status}</span></div>
                  <div>Version Count: <span className="text-slate-200">{versions.length}</span></div>
                </div>
              )}
            </div>

            <div className="flex justify-end pt-2">
              <button
                onClick={() => setSelectedReport(null)}
                className="px-4 py-1.5 rounded bg-slate-700 hover:bg-slate-600 text-xs font-semibold text-slate-200"
              >
                Close
              </button>
            </div>

          </div>
        </div>
      )}

    </div>
  );
}
