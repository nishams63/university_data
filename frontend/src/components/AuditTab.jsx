import React, { useState } from 'react';
import { ScrollText, Search, Filter, Eye, ChevronDown, ChevronUp } from 'lucide-react';

export default function AuditTab({ auditLogs, onRefresh }) {
  const [domainFilter, setDomainFilter] = useState('');
  const [actionFilter, setActionFilter] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedLogId, setExpandedLogId] = useState(null);

  const filteredLogs = auditLogs.filter(log => {
    if (domainFilter && log.domain !== domainFilter) return false;
    if (actionFilter && log.action !== actionFilter) return false;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      const matchId = log.log_id.toLowerCase().includes(q);
      const matchEvt = log.event_id && log.event_id.toLowerCase().includes(q);
      const matchCorr = log.correction_id && log.correction_id.toLowerCase().includes(q);
      const matchActor = log.actor && log.actor.toLowerCase().includes(q);
      if (!matchId && !matchEvt && !matchCorr && !matchActor) return false;
    }
    return true;
  });

  return (
    <div className="space-y-6">
      
      {/* Header */}
      <div className="bg-slate-800 border border-slate-700 p-4 rounded-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center space-x-2">
            <ScrollText className="w-5 h-5 text-indigo-400" />
            <span>Audit History</span>
          </h2>
          <p className="text-xs text-slate-300 mt-0.5 font-medium">
            Every important data change is recorded so administrators can see what happened and why.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search IDs or actor..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="bg-slate-900 border border-slate-700 text-xs text-slate-200 rounded-lg pl-8 pr-3 py-1.5 w-44 focus:w-56 transition-all font-mono"
            />
          </div>

          <select
            value={domainFilter}
            onChange={(e) => setDomainFilter(e.target.value)}
            className="bg-slate-900 border border-slate-700 text-xs text-slate-200 rounded-lg px-3 py-1.5"
          >
            <option value="">All Domains</option>
            <option value="RTC-Attendance">RTC-Attendance</option>
            <option value="RTC-Assessment">RTC-Assessment</option>
            <option value="RTC-Learning">RTC-Learning</option>
            <option value="RTC-Placement">RTC-Placement</option>
          </select>

          <select
            value={actionFilter}
            onChange={(e) => setActionFilter(e.target.value)}
            className="bg-slate-900 border border-slate-700 text-xs text-slate-200 rounded-lg px-3 py-1.5"
          >
            <option value="">All Actions</option>
            <option value="INGEST_EVENT">INGEST_EVENT</option>
            <option value="DISCARD_DUPLICATE">DISCARD_DUPLICATE</option>
            <option value="DISCARD_INVALID">DISCARD_INVALID</option>
            <option value="APPLY_CORRECTION">APPLY_CORRECTION</option>
            <option value="QUEUE_FOR_REVIEW">QUEUE_FOR_REVIEW</option>
            <option value="APPROVE_CORRECTION">APPROVE_CORRECTION</option>
            <option value="ROLLBACK_EXECUTED">ROLLBACK_EXECUTED</option>
          </select>
        </div>
      </div>

      {/* Audit History Table */}
      <div className="bg-slate-800 border border-slate-700 rounded-xl overflow-hidden shadow">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-900 border-b border-slate-700 text-xs font-bold text-slate-400 uppercase tracking-wider">
                <th className="py-3 px-4">Audit ID</th>
                <th className="py-3 px-4">Timestamp</th>
                <th className="py-3 px-4">Action</th>
                <th className="py-3 px-4">Domain</th>
                <th className="py-3 px-4">Event ID</th>
                <th className="py-3 px-4">Actor</th>
                <th className="py-3 px-4 text-right">Technical Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700/60 text-xs font-mono">
              {filteredLogs.length === 0 ? (
                <tr>
                  <td colSpan="7" className="py-8 text-center text-slate-400 font-sans">
                    No audit records match the selected filters.
                  </td>
                </tr>
              ) : (
                filteredLogs.map((log) => {
                  const isExpanded = expandedLogId === log.log_id;
                  const logTime = new Date(log.timestamp).toLocaleString();
                  return (
                    <React.Fragment key={log.id}>
                      <tr className="hover:bg-slate-700/40 transition-colors">
                        <td className="py-3 px-4 font-bold text-slate-200">{log.log_id}</td>
                        <td className="py-3 px-4 text-slate-400 font-sans text-[11px]">{logTime}</td>
                        
                        <td className="py-3 px-4 font-sans">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            log.action === 'DISCARD_DUPLICATE' ? 'bg-blue-500/20 text-blue-300' :
                            log.action === 'APPLY_CORRECTION' ? 'bg-emerald-500/20 text-emerald-300' :
                            log.action === 'ROLLBACK_EXECUTED' ? 'bg-amber-500/20 text-amber-300' :
                            'bg-slate-700 text-slate-300'
                          }`}>
                            {log.action}
                          </span>
                        </td>

                        <td className="py-3 px-4 text-indigo-300 font-sans font-semibold">{log.domain}</td>
                        <td className="py-3 px-4 text-slate-300">{log.event_id || '-'}</td>
                        <td className="py-3 px-4 text-slate-300 font-sans">{log.actor}</td>

                        <td className="py-3 px-4 text-right font-sans">
                          <button
                            onClick={() => setExpandedLogId(isExpanded ? null : log.log_id)}
                            className="px-2.5 py-1 rounded bg-slate-700 hover:bg-slate-600 text-slate-200 text-xs font-medium inline-flex items-center space-x-1"
                          >
                            <span>{isExpanded ? 'Hide Details' : 'View Technical Details'}</span>
                            {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                          </button>
                        </td>
                      </tr>

                      {/* Collapsible Technical Details Row */}
                      {isExpanded && (
                        <tr className="bg-slate-950 border-b border-slate-800">
                          <td colSpan="7" className="p-4">
                            <div className="space-y-2 text-xs font-mono">
                              <div className="text-slate-400 font-sans font-semibold text-[11px] uppercase tracking-wider">
                                Raw Technical Payload (JSON)
                              </div>
                              <pre className="bg-slate-900 p-3 rounded border border-slate-800 text-emerald-400 text-[11px] overflow-x-auto">
                                {JSON.stringify(JSON.parse(log.details_json || '{}'), null, 2)}
                              </pre>
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  );
}
