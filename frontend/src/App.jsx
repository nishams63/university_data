import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import DashboardTab from './components/DashboardTab';
import ReportsTab from './components/ReportsTab';
import EventsTab from './components/EventsTab';
import ReviewTab from './components/ReviewTab';
import AuditTab from './components/AuditTab';
import ExperimentTab from './components/ExperimentTab';
import DemoModal from './components/DemoModal';

import { 
  fetchMetricsSummary, fetchEvents, fetchDailyReports, 
  fetchPendingReviews, fetchAuditLogs, runControlledDemo 
} from './api/client';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [metrics, setMetrics] = useState(null);
  const [events, setEvents] = useState([]);
  const [reports, setReports] = useState([]);
  const [reviews, setReviews] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  // Demo modal state
  const [isRunningDemo, setIsRunningDemo] = useState(false);
  const [demoResult, setDemoResult] = useState(null);

  const loadAllData = async () => {
    try {
      const [mRes, eRes, rRes, revRes, aRes] = await Promise.all([
        fetchMetricsSummary(),
        fetchEvents(),
        fetchDailyReports(),
        fetchPendingReviews(),
        fetchAuditLogs()
      ]);
      setMetrics(mRes);
      setEvents(eRes);
      setReports(rRes);
      setReviews(revRes);
      setAuditLogs(aRes);
    } catch (e) {
      console.error("Failed to load backend data:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAllData();
    const interval = setInterval(loadAllData, 10000); // 10s auto-refresh
    return () => clearInterval(interval);
  }, []);

  const handleRunDemo = async () => {
    setIsRunningDemo(true);
    try {
      const result = await runControlledDemo();
      setDemoResult(result);
      await loadAllData();
    } catch (e) {
      console.error(e);
      alert(`Demo failed: ${e.message}`);
    } finally {
      setIsRunningDemo(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 flex flex-col font-sans">
      
      {/* Header & 6 Top Navigation Tabs */}
      <Header
        metrics={metrics}
        onRunDemo={handleRunDemo}
        isRunningDemo={isRunningDemo}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {loading && !metrics ? (
          <div className="py-20 text-center text-slate-400">
            <div className="inline-block w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin mb-3"></div>
            <p className="text-sm font-medium">Connecting to Rathinam Technical Campus Service...</p>
          </div>
        ) : (
          <>
            {activeTab === 'dashboard' && (
              <DashboardTab
                metrics={metrics}
                auditLogs={auditLogs}
                onRunDemo={handleRunDemo}
                isRunningDemo={isRunningDemo}
                onNavigate={setActiveTab}
              />
            )}

            {activeTab === 'reports' && (
              <ReportsTab reports={reports} onRefresh={loadAllData} />
            )}

            {activeTab === 'events' && (
              <EventsTab events={events} metrics={metrics} onRefresh={loadAllData} />
            )}

            {activeTab === 'review' && (
              <ReviewTab reviews={reviews} onRefresh={loadAllData} />
            )}

            {activeTab === 'audit' && (
              <AuditTab auditLogs={auditLogs} onRefresh={loadAllData} />
            )}

            {activeTab === 'experiment' && (
              <ExperimentTab />
            )}
          </>
        )}
      </main>

      {/* Institutional Footer */}
      <footer className="border-t border-slate-800 bg-slate-950 py-4 px-6 text-center text-xs text-slate-400">
        <p><strong>RATHINAM TECHNICAL CAMPUS</strong> — Late-Event Correction & Daily Reporting System</p>
        <p className="mt-1 text-slate-400">Integrated Domains: RTC-Learning | RTC-Assessment | RTC-Attendance | RTC-Placement</p>
      </footer>

      {/* Interactive Demo Modal */}
      {demoResult && (
        <DemoModal demoResult={demoResult} onClose={() => setDemoResult(null)} />
      )}

    </div>
  );
}
