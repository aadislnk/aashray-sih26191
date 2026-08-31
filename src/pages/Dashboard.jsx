import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { getHabitations } from '../api';
import { 
  Building2, 
  AlertOctagon, 
  Users, 
  Activity, 
  MapPin, 
  ArrowRight,
  Filter,
  RefreshCw,
  ChevronRight
} from 'lucide-react';

export default function Dashboard() {
  const [habitations, setHabitations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filterPriority, setFilterPriority] = useState('All');
  const navigate = useNavigate();

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const data = await getHabitations();
      setHabitations(data);
    } catch (err) {
      console.error('Failed to fetch habitations:', err);
    } finally {
      setLoading(false);
    }
  };

  // Calculations for KPI Cards
  const totalCount = habitations.length;
  const p1Count = habitations.filter((h) => h.priority === 'P1').length;
  const totalPopulation = habitations.reduce((acc, h) => acc + (h.population || 0), 0);
  const avgRiskScore = totalCount > 0 
    ? Math.round(habitations.reduce((acc, h) => acc + (h.risk_score || 0), 0) / totalCount) 
    : 0;

  // Filtered & Sorted by risk_score descending
  const filteredHabitations = habitations
    .filter((h) => filterPriority === 'All' || h.priority === filterPriority)
    .sort((a, b) => b.risk_score - a.risk_score);

  const getPriorityBadge = (priority) => {
    switch (priority) {
      case 'P1':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-extrabold bg-red-100 text-[#dc2626] border border-red-200">
            P1 Critical
          </span>
        );
      case 'P2':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-extrabold bg-orange-100 text-[#f97316] border border-orange-200">
            P2 High
          </span>
        );
      case 'P3':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-extrabold bg-yellow-100 text-[#ca8a04] border border-yellow-200">
            P3 Medium
          </span>
        );
      case 'P4':
      default:
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-extrabold bg-emerald-100 text-[#22c55e] border border-emerald-200">
            P4 Low
          </span>
        );
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Top Section Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="bg-blue-100 text-blue-800 text-[11px] font-mono font-bold px-2 py-0.5 rounded">
              Route: /
            </span>
            <span className="text-slate-400 text-xs">•</span>
            <span className="text-slate-500 text-xs font-medium uppercase tracking-wider">Executive Overview</span>
          </div>
          <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">
            Vulnerability & Relocation Dashboard
          </h1>
          <p className="text-slate-600 text-sm mt-1">
            Multi-hazard disaster risk index and priority resettlement tracking across surveyed habitation clusters.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={fetchData}
            disabled={loading}
            className="inline-flex items-center gap-2 px-4 py-2 bg-white hover:bg-slate-50 text-slate-700 rounded-lg text-sm font-semibold border border-slate-200 shadow-xs transition cursor-pointer disabled:opacity-60"
          >
            <RefreshCw className={`w-4 h-4 text-slate-500 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
          <Link
            to="/map"
            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-semibold shadow-xs transition"
          >
            <MapPin className="w-4 h-4" />
            <span>Geospatial Map</span>
          </Link>
        </div>
      </div>

      {/* 1. TOP KPI ROW (4 Cards) */}
      {loading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          {[1, 2, 3, 4].map((n) => (
            <div key={n} className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs animate-pulse space-y-3">
              <div className="h-4 bg-slate-200 rounded w-1/2"></div>
              <div className="h-8 bg-slate-200 rounded w-3/4"></div>
              <div className="h-3 bg-slate-100 rounded w-1/3"></div>
            </div>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          {/* Card 1: Total Habitations */}
          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs hover:shadow-md transition">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Total Habitations</span>
              <div className="w-10 h-10 rounded-lg bg-blue-50 flex items-center justify-center text-blue-600">
                <Building2 className="w-5 h-5" />
              </div>
            </div>
            <div className="mt-3">
              <div className="text-3xl font-extrabold text-slate-900 tracking-tight">{totalCount}</div>
              <p className="text-xs text-slate-500 mt-1">Surveyed cluster units</p>
            </div>
          </div>

          {/* Card 2: P1 Critical Count */}
          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs hover:shadow-md transition">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-[#dc2626] uppercase tracking-wider">P1 Critical Count</span>
              <div className="w-10 h-10 rounded-lg bg-red-50 flex items-center justify-center text-[#dc2626]">
                <AlertOctagon className="w-5 h-5" />
              </div>
            </div>
            <div className="mt-3">
              <div className="text-3xl font-extrabold text-[#dc2626] tracking-tight">{p1Count}</div>
              <p className="text-xs text-slate-500 mt-1">Immediate relocation required</p>
            </div>
          </div>

          {/* Card 3: Total Population Affected */}
          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs hover:shadow-md transition">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Total Population</span>
              <div className="w-10 h-10 rounded-lg bg-indigo-50 flex items-center justify-center text-indigo-600">
                <Users className="w-5 h-5" />
              </div>
            </div>
            <div className="mt-3">
              <div className="text-3xl font-extrabold text-slate-900 tracking-tight">{totalPopulation.toLocaleString()}</div>
              <p className="text-xs text-slate-500 mt-1">Individuals in mapped zones</p>
            </div>
          </div>

          {/* Card 4: Average Risk Score */}
          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs hover:shadow-md transition">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Average Risk Score</span>
              <div className="w-10 h-10 rounded-lg bg-amber-50 flex items-center justify-center text-amber-600">
                <Activity className="w-5 h-5" />
              </div>
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-3xl font-extrabold text-slate-900 tracking-tight">{avgRiskScore}</span>
              <span className="text-xs font-medium text-slate-500">/ 100</span>
            </div>
            <p className="text-xs text-slate-500 mt-1">Combined multi-hazard mean</p>
          </div>
        </div>
      )}

      {/* 2. PRIORITY FILTER & TABLE SECTION */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
        {/* Filter and Table Control Header */}
        <div className="p-6 border-b border-slate-200 bg-slate-50/60 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-lg font-bold text-slate-900">Habitation Risk Roster</h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Ranked in descending order of compound hazard susceptibility score.
            </p>
          </div>

          {/* Priority Filter (5 buttons/pills: All, P1, P2, P3, P4) */}
          <div className="flex items-center gap-1.5 flex-wrap">
            <span className="text-xs font-bold text-slate-500 mr-2 flex items-center gap-1">
              <Filter className="w-3.5 h-3.5 text-slate-400" /> Filter:
            </span>
            {[
              { key: 'All', label: 'All' },
              { key: 'P1', label: 'P1' },
              { key: 'P2', label: 'P2' },
              { key: 'P3', label: 'P3' },
              { key: 'P4', label: 'P4' },
            ].map(({ key, label }) => {
              const active = filterPriority === key;
              return (
                <button
                  key={key}
                  onClick={() => setFilterPriority(key)}
                  className={`px-3.5 py-1.5 rounded-lg text-xs font-bold transition cursor-pointer ${
                    active
                      ? 'bg-slate-900 text-white shadow-xs'
                      : 'bg-white text-slate-700 border border-slate-200 hover:bg-slate-100'
                  }`}
                >
                  {label}
                </button>
              );
            })}
          </div>
        </div>

        {/* 4. LOADING SKELETON / TABLE */}
        {loading ? (
          <div className="p-6 space-y-4">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <div key={i} className="h-14 bg-slate-100 rounded-lg animate-pulse"></div>
            ))}
          </div>
        ) : filteredHabitations.length === 0 ? (
          <div className="p-12 text-center text-slate-500">
            <p className="text-sm font-medium">No habitations matching priority {filterPriority}.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-700">
              <thead className="bg-slate-100/80 text-[11px] uppercase font-bold text-slate-500 tracking-wider border-b border-slate-200">
                <tr>
                  <th className="px-6 py-4">Habitation Name & Code</th>
                  <th className="px-6 py-4">Priority Level</th>
                  <th className="px-6 py-4">Risk Score</th>
                  <th className="px-6 py-4">Population</th>
                  <th className="px-6 py-4 text-right">Quick Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                {filteredHabitations.map((h) => (
                  <tr
                    key={h.id}
                    onClick={() => navigate(`/habitation/${h.id}`)}
                    className="hover:bg-blue-50/60 transition cursor-pointer group"
                  >
                    {/* Name & ID */}
                    <td className="px-6 py-4">
                      <div className="font-bold text-slate-900 group-hover:text-blue-600 transition flex items-center gap-2">
                        <span>{h.name}</span>
                        <ChevronRight className="w-4 h-4 text-slate-300 opacity-0 group-hover:opacity-100 transition" />
                      </div>
                      <span className="font-mono text-xs text-slate-400">{h.id}</span>
                    </td>

                    {/* Priority Badge */}
                    <td className="px-6 py-4">
                      {getPriorityBadge(h.priority)}
                    </td>

                    {/* Risk Score */}
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className="w-20 bg-slate-200 rounded-full h-2 overflow-hidden">
                          <div
                            className={`h-full rounded-full ${
                              h.risk_score >= 80 ? 'bg-[#dc2626]' :
                              h.risk_score >= 60 ? 'bg-[#f97316]' :
                              h.risk_score >= 40 ? 'bg-[#eab308]' : 'bg-[#22c55e]'
                            }`}
                            style={{ width: `${h.risk_score}%` }}
                          />
                        </div>
                        <span className="font-black text-slate-900 font-mono text-sm">{h.risk_score}</span>
                      </div>
                    </td>

                    {/* Population */}
                    <td className="px-6 py-4 font-semibold text-slate-800">
                      {h.population?.toLocaleString()} <span className="text-xs text-slate-400 font-normal">pax</span>
                    </td>

                    {/* View on Map Icon/Link */}
                    <td className="px-6 py-4 text-right" onClick={(e) => e.stopPropagation()}>
                      <div className="flex items-center justify-end gap-2">
                        <Link
                          to="/map"
                          title="Locate centroid on map"
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-slate-100 hover:bg-blue-100 text-slate-700 hover:text-blue-700 rounded-lg text-xs font-semibold border border-slate-200 transition"
                        >
                          <MapPin className="w-3.5 h-3.5 text-blue-600" />
                          <span>View on Map</span>
                        </Link>
                        <Link
                          to={`/habitation/${h.id}`}
                          className="inline-flex items-center gap-1 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold shadow-xs transition"
                        >
                          <span>Profile</span>
                          <ArrowRight className="w-3 h-3" />
                        </Link>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
