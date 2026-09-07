import React, { useState } from 'react';
import { Zap, Plus, Filter, ShieldCheck, Clock, CopyX, FileX, CheckCircle } from 'lucide-react';
import { ingestEvent } from '../api/client';

export default function EventsTab({ events, metrics, onRefresh }) {
  const [domainFilter, setDomainFilter] = useState('');
  const [isInjecting, setIsInjecting] = useState(false);
  const [customEvent, setCustomEvent] = useState({
    domain: 'RTC-Attendance',
    student_id: 'RTC-STU-0001',
    event_timestamp: '2026-08-20T10:00:00',
    arrival_timestamp: '2026-08-23T14:00:00',
    batch_id: 'BATCH-MANUAL-INJECT',
    payload: { attendance_status: 'Present', class_id: 'CS-301', attendance_date: '2026-08-20' }
  });

  const filteredEvents = events.filter(e => !domainFilter || e.domain === domainFilter);

  const handleInject = async (e) => {
    e.preventDefault();
    setIsInjecting(true);
    try {
      const payloadToSend = {
        ...customEvent,
        event_id: `EVT-MANUAL-${Date.now().toString().slice(-6)}`
      };
      const res = await ingestEvent(payloadToSend);
      alert(`Event Ingested!\nStatus: ${res.status}\nIs Late: ${res.is_late}`);
      onRefresh();
    } catch (err) {
      console.error(err);
      alert(`Ingestion failed: ${err.message}`);
    } finally {
      setIsInjecting(false);
    }
  };

  return (
    <div className="space-y-6">
      
      {/* Header */}
      <div className="bg-slate-800 border border-slate-700 p-4 rounded-xl flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center space-x-2">
            <Zap className="w-5 h-5 text-amber-400" />
            <span>Events Stream</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Real-time synthetic event ingestion pipeline for Rathinam Technical Campus.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <span className="px-2.5 py-1 rounded text-xs font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30">
            SIMULATION MODE
          </span>
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
        </div>
      </div>

      {/* Metrics Row (Moved from main dashboard) */}
      {metrics && (
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 text-center">
          <div className="bg-slate-800 p-3 rounded-lg border border-slate-700">
            <span className="text-[11px] text-slate-400 block font-medium">Total Events</span>
            <span className="text-lg font-bold text-slate-100">{metrics.total_events}</span>
          </div>
          <div className="bg-slate-800 p-3 rounded-lg border border-slate-700">
            <span className="text-[11px] text-slate-400 block font-medium">On-Time Events</span>
            <span className="text-lg font-bold text-emerald-400">{metrics.on_time_events}</span>
          </div>
          <div className="bg-slate-800 p-3 rounded-lg border border-slate-700">
            <span className="text-[11px] text-slate-400 block font-medium">Late Events</span>
            <span className="text-lg font-bold text-amber-400">{metrics.late_events}</span>
          </div>
          <div className="bg-slate-800 p-3 rounded-lg border border-slate-700">
            <span className="text-[11px] text-slate-400 block font-medium">Duplicates</span>
            <span className="text-lg font-bold text-blue-400">{metrics.duplicate_events}</span>
          </div>
          <div className="bg-slate-800 p-3 rounded-lg border border-slate-700">
            <span className="text-[11px] text-slate-400 block font-medium">Invalid</span>
            <span className="text-lg font-bold text-rose-400">{metrics.invalid_events}</span>
          </div>
        </div>
      )}

      {/* Manual Synthetic Event Injector */}
      <div className="bg-slate-800 border border-slate-700 p-5 rounded-xl">
        <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-3">
          Inject Synthetic Test Event
        </h3>
        <form onSubmit={handleInject} className="grid grid-cols-1 sm:grid-cols-4 gap-3 text-xs">
          <div>
            <label className="text-slate-400 block mb-1">Domain</label>
            <select
              value={customEvent.domain}
              onChange={(e) => setCustomEvent({ ...customEvent, domain: e.target.value })}
              className="w-full bg-slate-900 border border-slate-700 text-slate-200 rounded px-2.5 py-1.5"
            >
              <option value="RTC-Attendance">RTC-Attendance</option>
              <option value="RTC-Assessment">RTC-Assessment</option>
              <option value="RTC-Learning">RTC-Learning</option>
              <option value="RTC-Placement">RTC-Placement</option>
            </select>
          </div>

          <div>
            <label className="text-slate-400 block mb-1">Event Date & Time</label>
            <input
              type="text"
              value={customEvent.event_timestamp}
              onChange={(e) => setCustomEvent({ ...customEvent, event_timestamp: e.target.value })}
              className="w-full bg-slate-900 border border-slate-700 text-slate-200 rounded px-2.5 py-1.5 font-mono"
            />
          </div>

          <div>
            <label className="text-slate-400 block mb-1">Arrival Date & Time</label>
            <input
              type="text"
              value={customEvent.arrival_timestamp}
              onChange={(e) => setCustomEvent({ ...customEvent, arrival_timestamp: e.target.value })}
              className="w-full bg-slate-900 border border-slate-700 text-slate-200 rounded px-2.5 py-1.5 font-mono"
            />
          </div>

          <div className="flex items-end">
            <button
              type="submit"
              disabled={isInjecting}
              className="w-full py-1.5 rounded bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs shadow flex items-center justify-center space-x-1"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Inject Event</span>
            </button>
          </div>
        </form>
      </div>

      {/* Events Table */}
      <div className="bg-slate-800 border border-slate-700 rounded-xl overflow-hidden shadow">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-900 border-b border-slate-700 text-xs font-bold text-slate-400 uppercase tracking-wider">
                <th className="py-3 px-4">Event ID</th>
                <th className="py-3 px-4">Domain</th>
                <th className="py-3 px-4">Event Date</th>
                <th className="py-3 px-4">Arrival Date</th>
                <th className="py-3 px-4">Delay</th>
                <th className="py-3 px-4">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700/60 text-xs font-mono">
              {filteredEvents.map((evt) => {
                const evtDate = evt.event_timestamp ? evt.event_timestamp.split('T')[0] : '-';
                const arrDate = evt.arrival_timestamp ? evt.arrival_timestamp.split('T')[0] : '-';
                const delayDays = evt.lateness_hours ? (evt.lateness_hours / 24).toFixed(1) : '0';

                return (
                  <tr key={evt.id} className="hover:bg-slate-700/40 transition-colors">
                    <td className="py-3 px-4 font-bold text-slate-200">{evt.event_id}</td>
                    <td className="py-3 px-4 text-indigo-300 font-sans font-semibold">{evt.domain}</td>
                    <td className="py-3 px-4 text-slate-300 font-sans">{evtDate}</td>
                    <td className="py-3 px-4 text-amber-300 font-sans">{arrDate}</td>
                    <td className="py-3 px-4 text-slate-300 font-sans">
                      {evt.is_late ? `${delayDays} days` : 'On-Time'}
                    </td>
                    <td className="py-3 px-4 font-sans">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        evt.status === 'DUPLICATE' ? 'bg-blue-500/20 text-blue-300' :
                        evt.status === 'INVALID' ? 'bg-rose-500/20 text-rose-300' :
                        evt.is_late ? 'bg-amber-500/20 text-amber-300' :
                        'bg-emerald-500/20 text-emerald-300'
                      }`}>
                        {evt.status === 'DUPLICATE' ? 'DUPLICATE' :
                         evt.status === 'INVALID' ? 'INVALID' :
                         evt.is_late ? 'LATE' : 'ON TIME'}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  );
}
