import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getHabitations } from '../api';
import Map from '../components/Map';
import { 
  Layers, 
  RefreshCw, 
  MapPin, 
  ArrowRight, 
  ArrowLeft,
  ShieldAlert, 
  Info,
  SlidersHorizontal,
  Compass
} from 'lucide-react';

export default function MapView() {
  const [habitations, setHabitations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedHabitation, setSelectedHabitation] = useState(null);

  // Layer toggle state
  const [showHabitations, setShowHabitations] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const data = await getHabitations();
      setHabitations(data);
      if (data.length > 0) {
        setSelectedHabitation(data[0]);
      }
    } catch (err) {
      console.error('Failed to load map data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleMarkerClick = (habitation) => {
    setSelectedHabitation(habitation);
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Top Breadcrumb */}
      <div className="flex items-center justify-between">
        <Link
          to="/"
          className="inline-flex items-center gap-1.5 text-xs font-bold text-slate-600 hover:text-blue-600 bg-white px-3 py-1.5 rounded-lg border border-slate-200 shadow-xs transition"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Dashboard</span>
        </Link>

        <button
          onClick={fetchData}
          disabled={loading}
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-700 bg-white px-3 py-1.5 rounded-lg border border-slate-200 shadow-xs transition cursor-pointer"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Reload Habitations</span>
        </button>
      </div>

      {/* Route Header Banner */}
      <div className="bg-white rounded-2xl border border-slate-200 p-8 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="bg-blue-100 text-blue-800 text-[11px] font-mono font-bold px-2 py-0.5 rounded">
              Route: /map
            </span>
            <span className="text-slate-400 text-xs">•</span>
            <span className="text-slate-500 text-xs font-medium uppercase tracking-wider">Geospatial GIS Engine</span>
          </div>
          <h1 className="text-3xl font-black text-slate-900 tracking-tight flex items-center gap-2">
            <span>MapView</span>
            <span className="text-xs bg-emerald-100 text-[#22c55e] border border-emerald-300 font-extrabold px-2.5 py-0.5 rounded-full uppercase">
              MapLibre GL
            </span>
          </h1>
          <p className="text-slate-600 text-sm mt-1">
            Interactive OpenStreetMap raster canvas with centroid risk overlays and dynamic layer controls.
          </p>
        </div>
      </div>

      {loading ? (
        <div className="bg-white rounded-2xl border border-slate-200 p-16 text-center text-slate-500 shadow-xs space-y-3">
          <div className="inline-block animate-spin w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full"></div>
          <p className="text-sm font-semibold">Initializing MapLibre GL instance and loading coordinates...</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Main Interactive Map Container with Floating Overlay Panels */}
          <div className="lg:col-span-3 relative h-[600px] rounded-2xl overflow-hidden shadow-sm border border-slate-300 bg-slate-100">
            {/* The Map Component */}
            <Map 
              habitations={habitations}
              onMarkerClick={handleMarkerClick}
              showHabitations={showHabitations}
            />

            {/* Floating Layer Toggle Panel (Top-Right Corner) */}
            <div className="absolute top-3 right-3 z-10 bg-white/95 backdrop-blur-md p-3.5 rounded-xl shadow-lg border border-slate-200 text-xs w-52 space-y-2.5">
              <div className="flex items-center justify-between border-b border-slate-200 pb-1.5 font-bold text-slate-900">
                <span className="flex items-center gap-1.5">
                  <Layers className="w-3.5 h-3.5 text-blue-600" />
                  <span>Map Layers</span>
                </span>
              </div>

              <div className="space-y-2">
                {/* 1. Habitations (Functional) */}
                <label className="flex items-center justify-between cursor-pointer group">
                  <span className="flex items-center gap-2 text-slate-800 font-medium group-hover:text-blue-600 transition">
                    <input 
                      type="checkbox"
                      checked={showHabitations}
                      onChange={(e) => setShowHabitations(e.target.checked)}
                      className="rounded border-slate-300 text-blue-600 focus:ring-blue-500 h-3.5 w-3.5 cursor-pointer accent-blue-600"
                    />
                    <span>Habitations</span>
                  </span>
                  <span className="text-[10px] font-mono font-bold bg-blue-100 text-blue-800 px-1.5 py-0.2 rounded">
                    {habitations.length} pts
                  </span>
                </label>

                {/* 2. Flood (Disabled) */}
                <label className="flex items-center justify-between text-slate-400 cursor-not-allowed">
                  <span className="flex items-center gap-2">
                    <input 
                      type="checkbox"
                      disabled
                      className="rounded border-slate-300 h-3.5 w-3.5 cursor-not-allowed opacity-50"
                    />
                    <span>Flood Risk</span>
                  </span>
                  <span className="text-[9px] uppercase font-bold bg-slate-100 text-slate-400 px-1.5 py-0.2 rounded">
                    coming soon
                  </span>
                </label>

                {/* 3. Landslide (Disabled) */}
                <label className="flex items-center justify-between text-slate-400 cursor-not-allowed">
                  <span className="flex items-center gap-2">
                    <input 
                      type="checkbox"
                      disabled
                      className="rounded border-slate-300 h-3.5 w-3.5 cursor-not-allowed opacity-50"
                    />
                    <span>Landslide</span>
                  </span>
                  <span className="text-[9px] uppercase font-bold bg-slate-100 text-slate-400 px-1.5 py-0.2 rounded">
                    coming soon
                  </span>
                </label>

                {/* 4. Risk (Disabled) */}
                <label className="flex items-center justify-between text-slate-400 cursor-not-allowed">
                  <span className="flex items-center gap-2">
                    <input 
                      type="checkbox"
                      disabled
                      className="rounded border-slate-300 h-3.5 w-3.5 cursor-not-allowed opacity-50"
                    />
                    <span>Risk Heatmap</span>
                  </span>
                  <span className="text-[9px] uppercase font-bold bg-slate-100 text-slate-400 px-1.5 py-0.2 rounded">
                    coming soon
                  </span>
                </label>
              </div>
            </div>

            {/* Floating Priority Legend Card (Bottom-Left Corner) */}
            <div className="absolute bottom-6 left-3 z-10 bg-white/95 backdrop-blur-md p-3 rounded-xl shadow-lg border border-slate-200 text-xs w-48 space-y-2">
              <div className="font-bold text-slate-900 border-b border-slate-200 pb-1 flex items-center justify-between">
                <span>Priority Legend</span>
                <span className="text-[10px] text-slate-400 font-normal">Risk Index</span>
              </div>
              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="flex items-center gap-2 text-slate-700">
                    <span className="w-3.5 h-3.5 rounded-full bg-[#dc2626] border border-white shadow-xs inline-block"></span>
                    <span className="font-semibold">P1 Critical</span>
                  </span>
                  <span className="text-[11px] font-mono text-slate-500">80 - 100</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="flex items-center gap-2 text-slate-700">
                    <span className="w-3 h-3 rounded-full bg-[#f97316] border border-white shadow-xs inline-block"></span>
                    <span className="font-semibold">P2 High</span>
                  </span>
                  <span className="text-[11px] font-mono text-slate-500">60 - 79</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="flex items-center gap-2 text-slate-700">
                    <span className="w-2.5 h-2.5 rounded-full bg-[#eab308] border border-white shadow-xs inline-block"></span>
                    <span className="font-semibold">P3 Medium</span>
                  </span>
                  <span className="text-[11px] font-mono text-slate-500">40 - 59</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="flex items-center gap-2 text-slate-700">
                    <span className="w-2 h-2 rounded-full bg-[#22c55e] border border-white shadow-xs inline-block"></span>
                    <span className="font-semibold">P4 Low</span>
                  </span>
                  <span className="text-[11px] font-mono text-slate-500">&lt; 40</span>
                </div>
              </div>
            </div>
          </div>

          {/* Inspector Sidebar for Quick Habitation Detail Preview */}
          <div className="bg-white rounded-2xl border border-slate-200 shadow-xs p-6 flex flex-col justify-between h-[600px] overflow-y-auto">
            {selectedHabitation ? (
              <div className="space-y-4">
                <div className="border-b border-slate-200 pb-3">
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] font-bold text-blue-600 uppercase tracking-wider font-mono">
                      Selected Node
                    </span>
                    <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-extrabold border ${
                      selectedHabitation.priority === 'P1' ? 'bg-red-100 text-[#dc2626] border-red-200' :
                      selectedHabitation.priority === 'P2' ? 'bg-orange-100 text-[#f97316] border-orange-200' :
                      selectedHabitation.priority === 'P3' ? 'bg-yellow-100 text-[#ca8a04] border-yellow-200' :
                      'bg-emerald-100 text-[#22c55e] border-emerald-200'
                    }`}>
                      {selectedHabitation.priority} Priority
                    </span>
                  </div>
                  <h3 className="text-base font-extrabold text-slate-900 mt-1">{selectedHabitation.name}</h3>
                  <p className="text-xs font-mono text-slate-500">{selectedHabitation.id}</p>
                </div>

                <div className="space-y-2.5 text-xs">
                  <div className="flex justify-between py-1 border-b border-slate-100">
                    <span className="text-slate-500">Risk Assessment:</span>
                    <span className="font-bold text-[#dc2626] text-sm">{selectedHabitation.risk_score} / 100</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-100">
                    <span className="text-slate-500">Population:</span>
                    <span className="font-bold text-slate-800">{selectedHabitation.population?.toLocaleString()} pax</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-100">
                    <span className="text-slate-500">Coordinates:</span>
                    <span className="font-mono text-slate-700">{selectedHabitation.centroid.lat}, {selectedHabitation.centroid.lon}</span>
                  </div>
                </div>

                <div className="p-3 bg-blue-50/70 rounded-xl border border-blue-200 text-xs text-blue-900">
                  <p className="font-semibold flex items-center gap-1 mb-1">
                    <Info className="w-3.5 h-3.5 text-blue-700" />
                    Interactive Map Hint
                  </p>
                  <p className="text-[11px] text-slate-600 leading-relaxed">
                    Click any colored marker on the map to open its interactive popup with a direct "View Details" button.
                  </p>
                </div>

                <div className="pt-2 space-y-2">
                  <Link
                    to={`/habitation/${selectedHabitation.id}`}
                    className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-bold shadow-xs transition"
                  >
                    <span>View Habitation Profile</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                  <Link
                    to={`/habitation/${selectedHabitation.id}/relocation`}
                    className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold transition"
                  >
                    <span>Inspect Relocation Sites</span>
                  </Link>
                </div>
              </div>
            ) : (
              <div className="text-center py-16 text-slate-400 text-xs">
                Select a marker on the map
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
