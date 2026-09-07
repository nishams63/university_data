import React, { useState } from 'react';
import { Radio, PlusCircle, Filter, Clock, CheckCircle2, CopyX, FileX } from 'lucide-react';
import { ingestEvent } from '../api/client';

export default function LiveStreamTab({ events, onRefresh }) {
  const [domainFilter, setDomainFilter] = useState('');
  const [lateFilter, setLateFilter] = useState('');
  const [showInjector, setShowInjector] = useState(false);

  // Manual Injector form state
  const [injDomain, setInjDomain] = useState('RTC-Attendance');
  const [injStudentId, setInjStudentId] = useState('RTC-STU-0099');
  const [injDelayHours, setInjDelayHours] = useState(48); // 48h late
  const [injStatus, setInjStatus] = useState('Present');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const filteredEvents = events.filter(e => {
    if (domainFilter && e.domain !== domainFilter) return false;
    if (lateFilter === 'late' && !e.is_late) return false;
    if (lateFilter === 'ontime' && e.is_late) return false;
    return true;
  });

  const handleManualInject = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      const now = new Date();
      const eventTime = new Date(now.getTime() - injDelayHours * 3600 * 1000);
      const evtId = `RTC-EVT-MANUAL-${Date.now().toString().slice(-6)}`;
      
      let payload = {};
      if (injDomain === 'RTC-Attendance') {
        payload = { attendance_status: injStatus, class_id: 'CS-301', attendance_date: eventTime.toISOString().slice(0, 10) };
      } else if (injDomain === 'RTC-Assessment') {
        payload = { assessment_type: 'End-Sem', subject: 'Data Structures', score: 92.0, is_high_risk_outcome: true };
      } else if (injDomain === 'RTC-Learning') {
        payload = { module_id: 'MOD-101', quiz_score: 88.0, access_timestamp: eventTime.toISOString() };
      } else if (injDomain === 'RTC-Placement') {
        payload = { drive_id: 'DRIVE-GOOGLE', registration_status: 'Registered', offer_status: 'Offered', is_placement_status_change: true };
      }

      await ingestEvent({
        event_id: evtId,
        domain: injDomain,
        student_id: injStudentId,
        event_timestamp: eventTime.toISOString().slice(0, 19),
        arrival_timestamp: now.toISOString().slice(0, 19),
        batch_id: 'BATCH-MANUAL-INJECT',
        payload: payload
      });

      setShowInjector(false);
      onRefresh();
    } catch (err) {
      console.error(err);
      alert(`Error injecting event: ${err.message}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      
      {/* Header & Controls */}
      <div className="bg-slate-800/80 border border-slate-700/60 p-4 rounded-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center space-x-2">
            <Radio className="w-5 h-5 text-emerald-400 animate-pulse" />
            <span>Synthetic Event Stream Ingestion Feed</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Real-time feed of institutional events with explicit lateness and idempotency tags.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <select
            value={domainFilter}
            onChange={(e) => setDomainFilter(e.target.value)}
            className="bg-slate-900 border border-slate-700 text-xs text-slate-200 rounded-lg px-3 py-2"
          >
            <option value="">All Domains</option>
            <option value="RTC-Attendance">RTC-Attendance</option>
            <option value="RTC-Assessment">RTC-Assessment</option>
            <option value="RTC-Learning">RTC-Learning</option>
            <option value="RTC-Placement">RTC-Placement</option>
          </select>

          <select
            value={lateFilter}
            onChange={(e) => setLateFilter(e.target.value)}
            className="bg-slate-900 border border-slate-700 text-xs text-slate-200 rounded-lg px-3 py-2"
          >
            <option value="">All Lateness</option>
            <option value="ontime">On-Time Only</option>
            <option value="late">Late Only (&gt;24h)</option>
          </select>

          <button
            onClick={() => setShowInjector(!showInjector)}
            className="px-3 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs flex items-center space-x-1.5 shadow"
          >
            <PlusCircle className="w-4 h-4" />
            <span>Inject Synthetic Event</span>
          </button>
        </div>
      </div>

      {/* Manual Injector Panel */}
      {showInjector && (
        <form onSubmit={handleManualInject} className="bg-slate-800 border border-indigo-500/40 p-5 rounded-xl space-y-4 shadow-xl">
          <h3 className="text-sm font-bold text-white flex items-center space-x-2">
            <PlusCircle className="w-4 h-4 text-indigo-400" />
            <span>Inject Custom Synthetic Event</span>
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 text-xs">
            <div>
              <label className="block text-slate-400 mb-1 font-medium">RTC Domain</label>
              <select
                value={injDomain}
                onChange={(e) => setInjDomain(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 text-slate-200 rounded-lg p-2"
              >
                <option value="RTC-Attendance">RTC-Attendance</option>
                <option value="RTC-Assessment">RTC-Assessment</option>
                <option value="RTC-Learning">RTC-Learning</option>
                <option value="RTC-Placement">RTC-Placement</option>
              </select>
            </div>

            <div>
              <label className="block text-slate-400 mb-1 font-medium">Student ID</label>
              <input
                type="text"
                value={injStudentId}
                onChange={(e) => setInjStudentId(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 text-slate-200 rounded-lg p-2 font-mono"
              />
            </div>

            <div>
              <label className="block text-slate-400 mb-1 font-medium">Arrival Delay (Hours)</label>
              <input
                type="number"
                value={injDelayHours}
                onChange={(e) => setInjDelayHours(Number(e.target.value))}
                className="w-full bg-slate-900 border border-slate-700 text-slate-200 rounded-lg p-2 font-mono"
              />
            </div>

            <div>
              <label className="block text-slate-400 mb-1 font-medium">Attendance Status</label>
              <select
                value={injStatus}
                onChange={(e) => setInjStatus(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 text-slate-200 rounded-lg p-2"
              >
                <option value="Present">Present</option>
                <option value="Absent">Absent</option>
              </select>
            </div>
          </div>

          <div className="flex justify-end space-x-3 pt-2">
            <button
              type="button"
              onClick={() => setShowInjector(false)}
              className="px-4 py-1.5 rounded bg-slate-700 text-slate-300 text-xs font-medium"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-1.5 rounded bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs"
            >
              {isSubmitting ? 'Injecting...' : 'Submit Event'}
            </button>
          </div>
        </form>
      )}

      {/* Events Table */}
      <div className="bg-slate-800/80 border border-slate-700/60 rounded-xl overflow-hidden shadow-md">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-900/80 border-b border-slate-700 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                <th className="py-3 px-4">Event ID</th>
                <th className="py-3 px-4">Domain</th>
                <th className="py-3 px-4">Student ID</th>
                <th className="py-3 px-4">Event Timestamp</th>
                <th className="py-3 px-4">Arrival Timestamp</th>
                <th className="py-3 px-4">Delay</th>
                <th className="py-3 px-4">Lateness Tag</th>
                <th className="py-3 px-4">Payload Snippet</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700/50 text-xs font-mono">
              {filteredEvents.length === 0 ? (
                <tr>
                  <td colSpan="8" className="py-8 text-center text-slate-400 font-sans">
                    No stream events match current filters.
                  </td>
                </tr>
              ) : (
                filteredEvents.map((evt) => (
                  <tr key={evt.event_id} className="hover:bg-slate-700/30 transition-colors">
                    <td className="py-3 px-4 font-bold text-slate-200">{evt.event_id}</td>
                    <td className="py-3 px-4 text-indigo-300 font-semibold">{evt.domain}</td>
                    <td className="py-3 px-4 text-slate-300">{evt.student_id}</td>
                    <td className="py-3 px-4 text-slate-400">{evt.event_timestamp}</td>
                    <td className="py-3 px-4 text-slate-400">{evt.arrival_timestamp}</td>
                    <td className="py-3 px-4 text-slate-300">{evt.delay_hours}h</td>
                    
                    <td className="py-3 px-4">
                      {evt.is_late ? (
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/40 font-sans">
                          LATE ({evt.delay_hours}h)
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 font-sans">
                          ON-TIME
                        </span>
                      )}
                    </td>

                    <td className="py-3 px-4 text-slate-400 truncate max-w-xs text-[11px]">
                      {evt.payload_json}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  );
}
