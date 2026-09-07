import React, { useState, useEffect } from 'react';
import { RotateCcw, AlertTriangle, CheckCircle2, History, ShieldAlert } from 'lucide-react';
import { fetchRollbackableCorrections, triggerRollback } from '../api/client';

export default function RollbackTab({ onRefresh }) {
  const [corrections, setCorrections] = useState([]);
  const [loading, setLoading] = useState(true);
  const [executingId, setExecutingId] = useState(null);

  const loadData = async () => {
    setLoading(true);
    try {
      const data = await fetchRollbackableCorrections();
      setCorrections(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleExecuteRollback = async (corr) => {
    const confirmMsg = `Are you sure you want to execute a compensating rollback for correction ${corr.correction_id}?\nThis will revert ${corr.domain} report aggregate on ${corr.reporting_date} back to ${corr.previous_value}.`;
    if (!window.confirm(confirmMsg)) return;

    setExecutingId(corr.correction_id);
    try {
      const res = await triggerRollback(corr.correction_id, 'Data Administrator Manual Compensating Rollback');
      alert(`Rollback Executed Successfully!\nRestored Aggregate: ${res.restored_val}\nNew Report Version: v${res.new_version}`);
      loadData();
      onRefresh();
    } catch (e) {
      console.error(e);
      alert(`Rollback failed: ${e.message}`);
    } finally {
      setExecutingId(null);
    }
  };

  return (
    <div className="space-y-6">
      
      {/* Header */}
      <div className="bg-slate-800/80 border border-slate-700/60 p-4 rounded-xl flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center space-x-2">
            <RotateCcw className="w-5 h-5 text-amber-400" />
            <span>Compensating Rollback Management System</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Execute stateful compensating rollbacks to revert incorrect late corrections without deleting history.
          </p>
        </div>
        <button
          onClick={loadData}
          className="px-3 py-1.5 rounded bg-slate-700 hover:bg-slate-600 text-xs font-semibold text-slate-200"
        >
          Refresh List
        </button>
      </div>

      {/* Corrections List */}
      {loading ? (
        <div className="py-12 text-center text-slate-400 text-sm">Loading corrections eligible for rollback...</div>
      ) : corrections.length === 0 ? (
        <div className="bg-slate-800/60 border border-slate-700/60 p-12 text-center rounded-xl">
          <CheckCircle2 className="w-12 h-12 text-emerald-400 mx-auto mb-3" />
          <h3 className="text-base font-bold text-white">No Corrections Pending Rollback</h3>
          <p className="text-xs text-slate-400 mt-1">
            All report corrections are in their expected state.
          </p>
        </div>
      ) : (
        <div className="bg-slate-800/80 border border-slate-700/60 rounded-xl overflow-hidden shadow-md">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-900/80 border-b border-slate-700 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                  <th className="py-3 px-4">Correction ID</th>
                  <th className="py-3 px-4">Date</th>
                  <th className="py-3 px-4">Domain</th>
                  <th className="py-3 px-4">Student ID</th>
                  <th className="py-3 px-4">Previous Val</th>
                  <th className="py-3 px-4">Applied Val</th>
                  <th className="py-3 px-4">Impact %</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-right">Compensating Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700/50 text-xs font-mono">
                {corrections.map((corr) => (
                  <tr key={corr.correction_id} className="hover:bg-slate-700/30 transition-colors">
                    <td className="py-3 px-4 font-bold text-slate-200">{corr.correction_id}</td>
                    <td className="py-3 px-4 text-slate-300 font-sans">{corr.reporting_date}</td>
                    <td className="py-3 px-4 text-indigo-300 font-sans font-semibold">{corr.domain}</td>
                    <td className="py-3 px-4 text-slate-300">{corr.student_id}</td>
                    <td className="py-3 px-4 text-slate-400 font-bold">{corr.previous_value}</td>
                    <td className="py-3 px-4 text-emerald-400 font-bold">{corr.corrected_value}</td>
                    <td className="py-3 px-4 text-amber-400 font-bold">{corr.impact_percentage}%</td>
                    
                    <td className="py-3 px-4 font-sans">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                        {corr.status}
                      </span>
                    </td>

                    <td className="py-3 px-4 text-right font-sans">
                      <button
                        disabled={executingId === corr.correction_id}
                        onClick={() => handleExecuteRollback(corr)}
                        className="px-3 py-1.5 rounded bg-amber-600 hover:bg-amber-500 text-white font-bold text-xs shadow inline-flex items-center space-x-1.5 disabled:opacity-50 transition-colors"
                      >
                        <RotateCcw className="w-3.5 h-3.5" />
                        <span>Rollback to {corr.previous_value}</span>
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

    </div>
  );
}
