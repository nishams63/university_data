import React from 'react';
import { 
  CheckCircle, AlertTriangle, ArrowRight, Play, Clock, 
  Check, FileCheck, ShieldAlert, History, ShieldCheck, Info
} from 'lucide-react';

export default function DashboardTab({ metrics, auditLogs = [], onRunDemo, isRunningDemo, onNavigate }) {
  if (!metrics) return null;

  const isHealthy = metrics.pending_reviews === 0;
  const recentLogs = (auditLogs || []).slice(0, 5);

  return (
    <div className="space-y-6">
      
      {/* 1. TODAY'S DATA STATUS CARD */}
      <div className="bg-slate-800 border border-slate-700 p-5 rounded-xl shadow">
        <div className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">
          Today's Data Status — Rathinam Technical Campus
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          
          {/* Status Indicator */}
          <div className="bg-slate-900/80 p-4 rounded-lg border border-slate-700/80 flex items-center justify-between">
            <div>
              <div className="text-xs text-slate-400 font-medium">System Health</div>
              <div className={`text-lg font-extrabold mt-0.5 ${isHealthy ? 'text-emerald-400' : 'text-amber-400'}`}>
                {isHealthy ? 'HEALTHY' : 'NEEDS ATTENTION'}
              </div>
            </div>
            {isHealthy ? (
              <CheckCircle className="w-7 h-7 text-emerald-400" />
            ) : (
              <AlertTriangle className="w-7 h-7 text-amber-400 animate-pulse" />
            )}
          </div>

          {/* Late Events */}
          <div className="bg-slate-900/80 p-4 rounded-lg border border-slate-700/80 flex items-center justify-between">
            <div>
              <div className="text-xs text-slate-400 font-medium">Late Events Detected</div>
              <div className="text-2xl font-bold text-amber-400 mt-0.5">{metrics.late_events}</div>
            </div>
            <Clock className="w-7 h-7 text-amber-400" />
          </div>

          {/* Corrected Reports */}
          <div className="bg-slate-900/80 p-4 rounded-lg border border-slate-700/80 flex items-center justify-between">
            <div>
              <div className="text-xs text-slate-400 font-medium">Reports Corrected</div>
              <div className="text-2xl font-bold text-indigo-400 mt-0.5">{metrics.corrected_reports}</div>
            </div>
            <FileCheck className="w-7 h-7 text-indigo-400" />
          </div>

          {/* Pending Review */}
          <div className="bg-slate-900/80 p-4 rounded-lg border border-slate-700/80 flex items-center justify-between">
            <div>
              <div className="text-xs text-slate-400 font-medium">Review Required</div>
              <div className={`text-2xl font-bold mt-0.5 ${metrics.pending_reviews > 0 ? 'text-rose-400' : 'text-slate-300'}`}>
                {metrics.pending_reviews}
              </div>
            </div>
            <ShieldAlert className={`w-7 h-7 ${metrics.pending_reviews > 0 ? 'text-rose-400' : 'text-slate-500'}`} />
          </div>

        </div>
      </div>

      {/* 2. WHAT DOES THIS SYSTEM DO? CARD */}
      <div className="bg-slate-800 border border-slate-700 p-6 rounded-xl shadow">
        <div className="flex items-center space-x-2 text-indigo-400 mb-2">
          <Info className="w-5 h-5" />
          <h2 className="text-base font-bold text-white uppercase tracking-wider">What Does This System Do?</h2>
        </div>
        <p className="text-slate-200 text-sm leading-relaxed max-w-4xl font-medium">
          University data does not always arrive on time. For example, an attendance event may happen on <strong>August 20</strong> but reach the central system on <strong>August 23</strong>. A normal reporting system would place it on the wrong day. This system automatically detects the delay, updates the original August 20 report, prevents duplicate counting, and maintains a complete audit trail.
        </p>
      </div>

      {/* 3. HOW THE SYSTEM WORKS (5-STEP VISUAL PIPELINE) */}
      <div className="bg-slate-800 border border-slate-700 p-6 rounded-xl shadow">
        <div className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-4">
          How The System Works
        </div>

        <div className="grid grid-cols-1 md:grid-cols-5 gap-3 text-center">
          
          <div className="bg-slate-900 p-4 rounded-lg border border-slate-700 flex flex-col justify-between">
            <div className="text-xs text-slate-400 font-bold">1. EVENT OCCURS</div>
            <div className="text-sm font-bold text-white my-2">Aug 20</div>
            <div className="text-[11px] text-slate-400">Activity happens at RTC</div>
          </div>

          <div className="bg-slate-900 p-4 rounded-lg border border-slate-700 flex flex-col justify-between">
            <div className="text-xs text-slate-400 font-bold">2. ARRIVES LATE</div>
            <div className="text-sm font-bold text-amber-400 my-2">Aug 23</div>
            <div className="text-[11px] text-slate-400">Received 3 days late</div>
          </div>

          <div className="bg-slate-900 p-4 rounded-lg border border-slate-700 flex flex-col justify-between">
            <div className="text-xs text-slate-400 font-bold">3. LATE DETECTED</div>
            <div className="text-xs font-bold text-amber-300 my-2 px-2 py-1 bg-amber-500/20 rounded">
              3 Days Delay
            </div>
            <div className="text-[11px] text-slate-400">Routes to original date</div>
          </div>

          <div className="bg-slate-900 p-4 rounded-lg border border-slate-700 flex flex-col justify-between">
            <div className="text-xs text-slate-400 font-bold">4. REPORT FIXED</div>
            <div className="text-sm font-mono font-bold text-emerald-400 my-2">
              Aug 20: 900 → 901
            </div>
            <div className="text-[11px] text-slate-400">Historical date updated</div>
          </div>

          <div className="bg-slate-900 p-4 rounded-lg border border-slate-700 flex flex-col justify-between">
            <div className="text-xs text-slate-400 font-bold">5. AUDIT SAVED</div>
            <div className="text-xs font-bold text-indigo-300 my-2">
              Audit Record
            </div>
            <div className="text-[11px] text-slate-400">Version history logged</div>
          </div>

        </div>
      </div>

      {/* 4. EXPLAIN EVENT TIME VS ARRIVAL TIME & LIVE EXAMPLE */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Why Did Report Need Correction */}
        <div className="bg-slate-800 border border-slate-700 p-6 rounded-xl shadow flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-bold text-white uppercase tracking-wider mb-4">
              Why Did The Report Need Correction?
            </h3>

            <div className="grid grid-cols-2 gap-3 text-center mb-4">
              <div className="bg-slate-900 p-3.5 rounded-lg border border-slate-700">
                <div className="text-[11px] text-slate-400 font-semibold">EVENT TIME</div>
                <div className="text-xs text-slate-400 italic">"When it actually happened"</div>
                <div className="text-sm font-bold text-indigo-300 mt-2">August 20 — 10:00 AM</div>
              </div>

              <div className="bg-slate-900 p-3.5 rounded-lg border border-slate-700">
                <div className="text-[11px] text-slate-400 font-semibold">ARRIVAL TIME</div>
                <div className="text-xs text-slate-400 italic">"When RTC received it"</div>
                <div className="text-sm font-bold text-amber-300 mt-2">August 23 — 2:00 PM</div>
              </div>
            </div>

            <div className="bg-amber-500/10 border border-amber-500/20 p-3 rounded-lg text-xs text-amber-300 font-medium text-center">
              Because these dates are different, the event is <strong>LATE</strong>.
            </div>
          </div>
        </div>

        {/* Live Example Card */}
        <div className="bg-slate-800 border border-slate-700 p-6 rounded-xl shadow flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-bold text-white uppercase tracking-wider mb-4">
              Live Demonstration Example
            </h3>

            <div className="bg-slate-900 p-4 rounded-lg border border-slate-700 space-y-3 font-mono text-xs">
              <div className="flex justify-between text-slate-300 border-b border-slate-800 pb-2">
                <span>Event Date: <strong className="text-indigo-300 font-sans">Aug 20</strong></span>
                <span>Arrival Date: <strong className="text-amber-300 font-sans">Aug 23</strong></span>
              </div>
              <div className="flex items-center justify-between text-sm pt-1">
                <span className="text-slate-400">Before: <strong className="text-slate-200">900</strong></span>
                <span className="text-slate-400">After: <strong className="text-emerald-400">901</strong></span>
                <span className="text-slate-400">Ground Truth: <strong className="text-emerald-400">901</strong></span>
              </div>
            </div>

            <div className="flex items-center justify-around text-xs font-semibold text-emerald-400 mt-4">
              <span className="flex items-center space-x-1"><Check className="w-4 h-4" /> <span>Corrected</span></span>
              <span className="flex items-center space-x-1"><Check className="w-4 h-4" /> <span>No Double Counting</span></span>
              <span className="flex items-center space-x-1"><Check className="w-4 h-4" /> <span>Audited</span></span>
            </div>
          </div>
        </div>

      </div>

      {/* 5. PRIMARY DEMO BUTTON & RECENT ACTIVITY GRID */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Primary Demo Card */}
        <div className="bg-gradient-to-r from-emerald-950/60 to-slate-800 border border-emerald-500/30 p-6 rounded-xl shadow flex flex-col justify-between">
          <div>
            <h3 className="text-base font-bold text-white flex items-center space-x-2">
              <Play className="w-5 h-5 text-emerald-400 fill-emerald-400" />
              <span>Interactive Demonstration</span>
            </h3>
            <p className="text-xs text-slate-300 mt-1">
              Run the step-by-step 6-stage timeline scenario to see how late events are ingested, corrected, duplicate-checked, reviewed, and audited.
            </p>
          </div>

          <button
            onClick={onRunDemo}
            disabled={isRunningDemo}
            className="w-full mt-5 py-3 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-extrabold text-sm shadow flex items-center justify-center space-x-2 transition-all disabled:opacity-50"
          >
            <Play className="w-4 h-4 fill-white" />
            <span>RUN DEMONSTRATION</span>
          </button>
        </div>

        {/* Recent System Activity Log */}
        <div className="lg:col-span-2 bg-slate-800 border border-slate-700 p-5 rounded-xl shadow">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center space-x-2">
              <History className="w-4 h-4 text-indigo-400" />
              <span>Recent System Activity</span>
            </h3>
            <button
              onClick={() => onNavigate('audit')}
              className="text-xs text-indigo-400 hover:text-indigo-300 font-semibold flex items-center space-x-1"
            >
              <span>View Audit</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="space-y-2.5">
            {recentLogs.length === 0 ? (
              <div className="text-xs text-slate-400 py-4 text-center">No recent activity logged yet.</div>
            ) : (
              recentLogs.map((log) => {
                const logTime = new Date(log.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                return (
                  <div key={log.id} className="flex items-center justify-between text-xs p-2.5 rounded-lg bg-slate-900/80 border border-slate-700/60 font-mono">
                    <div className="flex items-center space-x-3">
                      <span className="text-slate-400 font-sans text-[11px]">{logTime}</span>
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold font-sans ${
                        log.action === 'DISCARD_DUPLICATE' ? 'bg-blue-500/20 text-blue-300' :
                        log.action === 'APPLY_CORRECTION' ? 'bg-emerald-500/20 text-emerald-300' :
                        log.action === 'QUEUE_FOR_REVIEW' ? 'bg-rose-500/20 text-rose-300' :
                        'bg-slate-700 text-slate-300'
                      }`}>
                        {log.action}
                      </span>
                      <span className="text-slate-200 font-sans font-medium">
                        {log.action === 'INGEST_EVENT' ? 'Late attendance event received' :
                         log.action === 'APPLY_CORRECTION' ? 'Historical report corrected' :
                         log.action === 'DISCARD_DUPLICATE' ? 'Duplicate event rejected (+0)' :
                         log.action === 'QUEUE_FOR_REVIEW' ? 'High-impact correction pending review' :
                         log.action === 'ROLLBACK_EXECUTED' ? 'Compensating rollback executed' : log.action}
                      </span>
                    </div>
                    <span className="text-indigo-300 text-[11px] font-sans font-semibold hidden sm:inline">{log.domain}</span>
                  </div>
                );
              })
            )}
          </div>
        </div>

      </div>

    </div>
  );
}
