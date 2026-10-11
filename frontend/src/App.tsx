import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Navbar } from './components/Navbar';
import { SurvivorHelp } from './pages/SurvivorHelp';
import { ResponderDashboard } from './pages/ResponderDashboard';
import { TeamOperations } from './pages/TeamOperations';

export const App: React.FC = () => {
  return (
    <Router>
      <div className="min-h-screen bg-disaster-dark flex flex-col font-sans text-gray-100">
        <Navbar />

        <main className="flex-1">
          <Routes>
            <Route path="/" element={<SurvivorHelp />} />
            <Route path="/help" element={<SurvivorHelp />} />
            <Route path="/responder" element={<ResponderDashboard />} />
            <Route path="/teams" element={<TeamOperations />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>

        <footer className="bg-disaster-card border-t border-disaster-cardBorder py-6 text-center text-xs text-gray-400">
          <div className="max-w-7xl mx-auto px-4">
            <p className="font-semibold text-gray-300">
              FloodRescue AI — Environmental Disaster Response Platform
            </p>
            <p className="mt-1 text-[11px] text-gray-400">
              Built for <span className="text-amber-400 font-medium">WeMakeDevs × AWS Environmental Hackathon 2026</span> (Heat & Water Track)
            </p>
            <p className="mt-2 text-[10px] text-gray-400 max-w-xl mx-auto">
              Simulated demonstration environment. AI agent recommendations assist triage and must be verified by authorized emergency responders before dispatch.
            </p>
          </div>
        </footer>
      </div>
    </Router>
  );
};

export default App;
