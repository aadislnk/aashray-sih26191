import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Navbar from './components/Navbar';
import { ErrorBoundary } from './components/ErrorBoundary';
import Dashboard from './pages/Dashboard';
import MapView from './pages/MapView';
import Habitation from './pages/Habitation';
import Relocation from './pages/Relocation';
import WhatIf from './pages/WhatIf';
import Recommendation from './pages/Recommendation';

export default function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <div className="min-h-screen bg-slate-50 flex flex-col font-sans selection:bg-blue-600 selection:text-white">
          {/* Top Navigation Bar - Always visible across all pages */}
          <Navbar />

          {/* Main Content Area */}
          <main className="flex-1">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/map" element={<MapView />} />
              <Route path="/habitation/:id" element={<Habitation />} />
              <Route path="/habitation/:id/relocation" element={<Relocation />} />
              <Route path="/habitation/:id/whatif" element={<WhatIf />} />
              <Route path="/recommendation/:id" element={<Recommendation />} />
              {/* Fallback route */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </main>

          {/* Government Style Footer */}
          <footer className="bg-slate-900 text-slate-400 text-xs border-t border-slate-800 py-6 mt-12">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4">
              <div>
                <p className="font-semibold text-slate-300">Aashray Resettlement Decision Support Engine</p>
                <p className="text-[11px] text-slate-400 mt-0.5">Automated Disaster Relocation & Risk Modeling System</p>
              </div>
              <div className="text-[11px] text-slate-400 flex items-center gap-4">
                <span>National Disaster Management Authority</span>
                <span>•</span>
                <span>Kerala State Disaster Management Authority</span>
              </div>
            </div>
          </footer>
        </div>
      </BrowserRouter>
    </ErrorBoundary>
  );
}
