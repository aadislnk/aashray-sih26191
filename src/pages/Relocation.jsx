import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getSites, getHabitationDetail } from '../api';
import { 
  ArrowLeft, 
  MapPin, 
  Sparkles, 
  Users, 
  CheckCircle2, 
  AlertTriangle, 
  LayoutGrid, 
  Table as TableIcon,
  RefreshCw,
  Award,
  Layers,
  ArrowRight,
  ShieldCheck,
  ShieldAlert
} from 'lucide-react';

// CapacityBar Component: Proportional fill, green if capacity >= required, red/amber if deficit
function CapacityBar({ required = 0, capacity = 0 }) {
  const percentage = capacity > 0 ? Math.min(100, Math.round((required / capacity) * 100)) : 100;
  const isDeficit = required > capacity;
  const isTight = !isDeficit && required >= capacity * 0.85;

  return (
    <div className="space-y-1.5">
      <div className="flex justify-between text-xs font-semibold">
        <span className="text-slate-600">Capacity Utilization</span>
        <span className={isDeficit ? 'text-[#dc2626] font-bold' : isTight ? 'text-[#f97316] font-bold' : 'text-[#22c55e] font-bold'}>
          {required.toLocaleString()} / {capacity.toLocaleString()} ({percentage}%)
        </span>
      </div>

      <div className="w-full bg-slate-100 rounded-full h-2.5 overflow-hidden border border-slate-200">
        <div
          className={`h-full rounded-full transition-all duration-500 ${
            isDeficit 
              ? 'bg-[#dc2626]' 
              : isTight 
              ? 'bg-[#f97316]' 
              : 'bg-[#22c55e]'
          }`}
          style={{ width: `${Math.min(100, percentage)}%` }}
        />
      </div>

      <div className="flex justify-between text-[11px] text-slate-400">
        <span>Required: <strong className="text-slate-700">{required.toLocaleString()}</strong></span>
        <span>Max Capacity: <strong className="text-slate-700">{capacity.toLocaleString()}</strong></span>
      </div>
    </div>
  );
}

export default function Relocation() {
  const { id } = useParams();
  const [sites, setSites] = useState([]);
  const [habitation, setHabitation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState('cards'); // 'cards' | 'table'

  useEffect(() => {
    fetchData();
  }, [id]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [sitesData, habData] = await Promise.all([
        getSites(id),
        getHabitationDetail(id)
      ]);
      setSites(sitesData || []);
      setHabitation(habData);
    } catch (err) {
      console.error('Failed to load relocation data:', err);
    } finally {
      setLoading(false);
    }
  };

  const getBadgeColor = (level) => {
    switch (level?.toLowerCase()) {
      case 'high':
        return 'bg-emerald-100 text-[#22c55e] border-emerald-200';
      case 'medium':
        return 'bg-yellow-100 text-[#ca8a04] border-yellow-200';
      case 'low':
      default:
        return 'bg-red-100 text-[#dc2626] border-red-200';
    }
  };

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        <div className="bg-white rounded-2xl border border-slate-200 p-8 shadow-xs animate-pulse space-y-4">
          <div className="h-6 bg-slate-200 rounded w-1/3"></div>
          <div className="h-10 bg-slate-100 rounded-xl"></div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[1, 2, 3].map((n) => (
            <div key={n} className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs animate-pulse space-y-4">
              <div className="h-6 bg-slate-200 rounded w-1/3"></div>
              <div className="h-5 bg-slate-200 rounded w-3/4"></div>
              <div className="h-16 bg-slate-100 rounded-xl"></div>
              <div className="h-8 bg-slate-200 rounded"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (!habitation) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16 text-center">
        <div className="bg-white rounded-2xl border border-slate-200 p-12 shadow-xs space-y-4">
          <ShieldAlert className="w-12 h-12 text-slate-400 mx-auto" />
          <h2 className="text-xl font-black text-slate-800">Habitation Record Not Found</h2>
          <p className="text-sm text-slate-500">Could not resolve relocation sites for ID: {id}</p>
          <Link to="/" className="inline-flex items-center gap-2 px-5 py-2.5 bg-blue-600 text-white rounded-xl text-xs font-bold shadow-xs">
            <ArrowLeft className="w-4 h-4" /> Back to Dashboard
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Top Navigation & Breadcrumb */}
      <div className="flex items-center justify-between">
        <Link
          to={`/habitation/${id}`}
          className="inline-flex items-center gap-1.5 text-xs font-bold text-slate-600 hover:text-blue-600 bg-white px-3 py-1.5 rounded-lg border border-slate-200 shadow-xs transition"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to {habitation.name}</span>
        </Link>

        <button
          onClick={fetchData}
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-700 bg-white px-3 py-1.5 rounded-lg border border-slate-200 shadow-xs transition cursor-pointer"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh Sites</span>
        </button>
      </div>

      {/* 1. HEADER SECTION */}
      <div className="bg-white rounded-2xl border border-slate-200 p-8 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <span className="font-mono text-xs font-bold bg-blue-50 text-blue-700 border border-blue-200 px-2.5 py-0.5 rounded-md">
              {id}
            </span>
            <span className="text-slate-300">•</span>
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">
              Candidate Site Evaluation
            </span>
          </div>

          <h1 className="text-3xl font-black text-slate-900 tracking-tight">
            {habitation.name} — <span className="text-blue-600">Relocation Intelligence</span>
          </h1>

          <p className="text-slate-600 text-sm mt-1">
            Evaluated relocation receptors ranked by multi-sector carrying capacity, geotechnical safety, and proximity.
          </p>
        </div>

        {/* View Mode Toggle Button */}
        <div className="flex items-center bg-slate-100 p-1 rounded-xl border border-slate-200 self-start md:self-auto">
          <button
            onClick={() => setViewMode('cards')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition cursor-pointer ${
              viewMode === 'cards'
                ? 'bg-white text-slate-900 shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <LayoutGrid className="w-3.5 h-3.5" />
            <span>Card View</span>
          </button>
          <button
            onClick={() => setViewMode('table')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition cursor-pointer ${
              viewMode === 'table'
                ? 'bg-white text-slate-900 shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <TableIcon className="w-3.5 h-3.5" />
            <span>Table View</span>
          </button>
        </div>
      </div>

      {sites.length === 0 ? (
        <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center text-slate-500 shadow-xs">
          <ShieldAlert className="w-12 h-12 text-slate-400 mx-auto mb-3" />
          <h3 className="text-lg font-bold text-slate-800">No Candidate Sites Found</h3>
          <p className="text-sm text-slate-500 mt-1">No candidate sites mapped for habitation {id}.</p>
        </div>
      ) : (
        <>
          {/* 2. SITE COMPARISON CARDS (Card View) */}
          {viewMode === 'cards' && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {sites.map((site) => {
                const isRank1 = site.rank === 1;
                return (
                  <div
                    key={site.id}
                    className={`bg-white rounded-2xl border p-6 shadow-xs flex flex-col justify-between transition relative overflow-hidden ${
                      isRank1
                        ? 'border-blue-500 ring-2 ring-blue-500/20 bg-blue-50/10'
                        : 'border-slate-200 hover:border-slate-300'
                    }`}
                  >
                    {isRank1 && (
                      <div className="absolute top-0 right-0 bg-blue-600 text-white text-[10px] uppercase font-black px-3 py-0.5 rounded-bl-lg tracking-wider">
                        Top Rank
                      </div>
                    )}

                    <div className="space-y-4">
                      {/* Header: Rank + Name + ID */}
                      <div className="flex items-start gap-3">
                        <span
                          className={`w-9 h-9 rounded-xl flex items-center justify-center font-black text-sm shrink-0 border ${
                            isRank1
                              ? 'bg-blue-600 text-white border-blue-700 shadow-xs'
                              : 'bg-slate-100 text-slate-700 border-slate-300'
                          }`}
                        >
                          #{site.rank}
                        </span>
                        <div>
                          <h3 className="font-extrabold text-slate-900 text-base leading-snug">
                            {site.name}
                          </h3>
                          <div className="flex items-center gap-2 mt-0.5">
                            <span className="font-mono text-xs text-slate-400">{site.id}</span>
                            <span
                              className={`text-[10px] font-extrabold uppercase px-2 py-0.5 rounded-full border ${
                                site.status === 'recommended'
                                  ? 'bg-emerald-100 text-[#22c55e] border-emerald-200'
                                  : 'bg-slate-100 text-slate-600 border-slate-200'
                              }`}
                            >
                              {site.status?.replace(/_/g, ' ')}
                            </span>
                          </div>
                        </div>
                      </div>

                      {/* Suitability & Safety Badges */}
                      <div className="grid grid-cols-2 gap-2 pt-1">
                        <div className="bg-slate-50 p-2.5 rounded-xl border border-slate-200 text-center">
                          <span className="text-[10px] uppercase font-bold text-slate-400 block">Suitability</span>
                          <span className={`inline-block mt-1 px-2.5 py-0.5 rounded-full text-xs font-black border capitalize ${getBadgeColor(site.suitability)}`}>
                            {site.suitability}
                          </span>
                        </div>
                        <div className="bg-slate-50 p-2.5 rounded-xl border border-slate-200 text-center">
                          <span className="text-[10px] uppercase font-bold text-slate-400 block">Safety Level</span>
                          <span className={`inline-block mt-1 px-2.5 py-0.5 rounded-full text-xs font-black border capitalize ${getBadgeColor(site.safety)}`}>
                            {site.safety}
                          </span>
                        </div>
                      </div>

                      {/* CapacityBar Component */}
                      <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-200">
                        <CapacityBar 
                          required={site.required_capacity || habitation.population || 3200}
                          capacity={site.capacity}
                        />
                      </div>

                      {/* Binding Sector & Distance */}
                      <div className="flex items-center justify-between text-xs pt-1 border-t border-slate-100">
                        <div className="flex items-center gap-1.5 text-slate-600">
                          <MapPin className="w-4 h-4 text-blue-600 shrink-0" />
                          <span className="font-bold text-slate-900">{site.distance_km} km</span>
                          <span className="text-slate-400">away</span>
                        </div>

                        <span className="bg-slate-100 text-slate-700 border border-slate-200 px-2.5 py-0.5 rounded-md font-mono text-[11px]">
                          Limited by: <strong className="capitalize text-slate-900">{site.binding_sector?.replace(/_/g, ' ')}</strong>
                        </span>
                      </div>
                    </div>

                    {/* Allocated Population Footer */}
                    <div className="pt-4 mt-4 border-t border-slate-100 flex items-center justify-between text-xs">
                      <span className="text-slate-500 font-medium">Allocated Resettlement:</span>
                      <span className="font-extrabold text-blue-700 font-mono text-sm">
                        {site.allocated_population?.toLocaleString()} pax
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {/* 3. COMPARISON TABLE VIEW */}
          {viewMode === 'table' && (
            <div className="bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm text-slate-700">
                  <thead className="bg-slate-100/80 text-[11px] uppercase font-bold text-slate-500 tracking-wider border-b border-slate-200">
                    <tr>
                      <th className="px-6 py-4">Rank & Site</th>
                      <th className="px-6 py-4">Suitability</th>
                      <th className="px-6 py-4">Safety</th>
                      <th className="px-6 py-4">Capacity</th>
                      <th className="px-6 py-4">Required</th>
                      <th className="px-6 py-4">Distance</th>
                      <th className="px-6 py-4">Binding Sector</th>
                      <th className="px-6 py-4 text-right">Allocated</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200">
                    {sites.map((site) => (
                      <tr key={site.id} className="hover:bg-slate-50/80 transition">
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-2">
                            <span className="font-black text-slate-900 bg-slate-100 px-2 py-0.5 rounded text-xs">
                              #{site.rank}
                            </span>
                            <div>
                              <div className="font-bold text-slate-900">{site.name}</div>
                              <span className="font-mono text-xs text-slate-400">{site.id}</span>
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold border capitalize ${getBadgeColor(site.suitability)}`}>
                            {site.suitability}
                          </span>
                        </td>
                        <td className="px-6 py-4">
                          <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold border capitalize ${getBadgeColor(site.safety)}`}>
                            {site.safety}
                          </span>
                        </td>
                        <td className="px-6 py-4 font-bold text-slate-800">
                          {site.capacity?.toLocaleString()}
                        </td>
                        <td className="px-6 py-4 font-medium text-slate-600">
                          {(site.required_capacity || habitation.population || 3200).toLocaleString()}
                        </td>
                        <td className="px-6 py-4 font-mono text-slate-700">
                          {site.distance_km} km
                        </td>
                        <td className="px-6 py-4">
                          <span className="bg-slate-100 text-slate-700 border border-slate-200 px-2 py-0.5 rounded text-xs capitalize">
                            {site.binding_sector?.replace(/_/g, ' ')}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-right font-mono font-bold text-blue-700">
                          {site.allocated_population?.toLocaleString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* 4. BOTTOM ACTION BUTTON */}
          <div className="bg-[#0b192c] text-white rounded-2xl p-6 sm:p-8 shadow-md flex flex-col sm:flex-row items-center justify-between gap-4">
            <div>
              <h3 className="text-lg font-bold">Optimization Ready</h3>
              <p className="text-xs text-slate-300 mt-0.5">
                Run the multi-criteria optimization recommendation engine for {habitation.name}.
              </p>
            </div>

            <Link
              to={`/recommendation/${id}`}
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-sm font-bold shadow-xs transition cursor-pointer"
            >
              <Sparkles className="w-4 h-4" />
              <span>View Recommendation Engine</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </>
      )}
    </div>
  );
}
