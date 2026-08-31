import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getHabitationDetail } from '../api';
import { 
  Building2, 
  Users, 
  ShieldCheck, 
  Clock, 
  AlertTriangle, 
  Compass, 
  SlidersHorizontal, 
  ArrowLeft, 
  Waves, 
  Mountain, 
  CloudRain, 
  FileText,
  ShieldAlert,
  Info,
  RefreshCw
} from 'lucide-react';

export default function Habitation() {
  const { id } = useParams();
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDetail();
  }, [id]);

  const fetchDetail = async () => {
    setLoading(true);
    try {
      const data = await getHabitationDetail(id);
      setDetail(data);
    } catch (err) {
      console.error('Failed to fetch habitation detail:', err);
    } finally {
      setLoading(false);
    }
  };

  // Helper for Priority Badge
  const getPriorityBadge = (priority) => {
    switch (priority) {
      case 'P1':
        return (
          <span className="px-4 py-1.5 rounded-full text-sm font-extrabold bg-red-100 text-[#dc2626] border-2 border-red-300 shadow-xs">
            P1 — Critical Priority
          </span>
        );
      case 'P2':
        return (
          <span className="px-4 py-1.5 rounded-full text-sm font-extrabold bg-orange-100 text-[#f97316] border-2 border-orange-300 shadow-xs">
            P2 — High Priority
          </span>
        );
      case 'P3':
        return (
          <span className="px-4 py-1.5 rounded-full text-sm font-extrabold bg-yellow-100 text-[#ca8a04] border-2 border-yellow-300 shadow-xs">
            P3 — Medium Priority
          </span>
        );
      case 'P4':
      default:
        return (
          <span className="px-4 py-1.5 rounded-full text-sm font-extrabold bg-emerald-100 text-[#22c55e] border-2 border-emerald-300 shadow-xs">
            P4 — Low Priority
          </span>
        );
    }
  };

  // Helper for Hazard Icon
  const getHazardIcon = (hazardKey) => {
    switch (hazardKey) {
      case 'flood':
        return <Waves className="w-5 h-5 text-blue-500" />;
      case 'landslide':
        return <Mountain className="w-5 h-5 text-amber-600" />;
      case 'extreme_rainfall':
        return <CloudRain className="w-5 h-5 text-indigo-500" />;
      case 'coastal_erosion':
      default:
        return <Waves className="w-5 h-5 text-teal-500" />;
    }
  };

  // Confidence Dot Helper
  const getConfidenceDot = (conf) => {
    const color = conf === 'high' ? 'bg-emerald-500' : conf === 'medium' ? 'bg-yellow-500' : 'bg-red-500';
    return (
      <span className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-700 bg-white border border-slate-200 px-3 py-1 rounded-full shadow-xs">
        <span className={`w-2 h-2 rounded-full ${color}`}></span>
        <span className="capitalize">{conf} Confidence</span>
      </span>
    );
  };

  // Date Formatter Helper
  const formatDate = (isoString) => {
    if (!isoString) return 'N/A';
    try {
      const d = new Date(isoString);
      return d.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return isoString;
    }
  };

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        <div className="bg-white rounded-2xl border border-slate-200 p-8 shadow-xs animate-pulse space-y-4">
          <div className="h-4 bg-slate-200 rounded w-1/4"></div>
          <div className="h-8 bg-slate-200 rounded w-1/2"></div>
          <div className="h-20 bg-slate-100 rounded-xl"></div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map(n => (
            <div key={n} className="h-32 bg-white rounded-xl border border-slate-200 p-4 animate-pulse"></div>
          ))}
        </div>
      </div>
    );
  }

  if (!detail) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16 text-center">
        <div className="bg-white rounded-2xl border border-slate-200 p-12 shadow-xs space-y-4">
          <ShieldAlert className="w-12 h-12 text-slate-400 mx-auto" />
          <h2 className="text-xl font-bold text-slate-800">Habitation Record Not Found</h2>
          <p className="text-sm text-slate-500">Could not resolve habitation with ID: {id}</p>
          <Link to="/" className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-semibold">
            <ArrowLeft className="w-4 h-4" /> Back to Dashboard
          </Link>
        </div>
      </div>
    );
  }

  // Risk Score Ring Style Logic
  const isHighRisk = detail.risk_score >= 70;
  const isMedRisk = detail.risk_score >= 40 && detail.risk_score < 70;
  const ringColor = isHighRisk 
    ? 'border-[#dc2626] text-[#dc2626] bg-red-50/60' 
    : isMedRisk 
    ? 'border-[#f97316] text-[#f97316] bg-orange-50/60' 
    : 'border-[#22c55e] text-[#22c55e] bg-emerald-50/60';

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Top Breadcrumb Navigation */}
      <div className="flex items-center justify-between">
        <Link
          to="/"
          className="inline-flex items-center gap-1.5 text-xs font-bold text-slate-600 hover:text-blue-600 bg-white px-3 py-1.5 rounded-lg border border-slate-200 shadow-xs transition"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Dashboard</span>
        </Link>

        <button
          onClick={fetchDetail}
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-700 bg-white px-3 py-1.5 rounded-lg border border-slate-200 shadow-xs transition cursor-pointer"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh Data</span>
        </button>
      </div>

      {/* 1. HEADER SECTION: Name, ID, Large Priority Badge, Risk Score Ring */}
      <div className="bg-white rounded-2xl border border-slate-200 p-8 shadow-xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          {/* Name, ID, Priority */}
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs font-bold bg-blue-50 text-blue-700 border border-blue-200 px-2.5 py-0.5 rounded-md">
                {detail.id}
              </span>
              <span className="text-slate-300">•</span>
              <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                Habitation Profile
              </span>
            </div>

            <h1 className="text-3xl sm:text-4xl font-black text-slate-900 tracking-tight">
              {detail.name}
            </h1>

            <div>
              {getPriorityBadge(detail.priority)}
            </div>
          </div>

          {/* Big Risk Score with Colored Ring / Circle */}
          <div className="flex items-center gap-4 bg-slate-50 p-4 sm:p-5 rounded-2xl border border-slate-200 self-start md:self-auto">
            <div className={`w-20 h-20 sm:w-24 sm:h-24 rounded-full border-4 flex flex-col items-center justify-center shadow-inner ${ringColor}`}>
              <span className="text-2xl sm:text-3xl font-black tracking-tight leading-none">
                {detail.risk_score}
              </span>
              <span className="text-[10px] font-bold uppercase text-slate-400 mt-0.5">/ 100</span>
            </div>
            <div>
              <span className="text-xs font-bold uppercase tracking-wider text-slate-500">Risk Assessment</span>
              <div className="text-sm font-extrabold text-slate-800 mt-0.5">
                {isHighRisk ? 'Critical Vulnerability' : isMedRisk ? 'Moderate Vulnerability' : 'Low Vulnerability'}
              </div>
              <p className="text-[11px] text-slate-400 mt-0.5">Composite Hazard Index</p>
            </div>
          </div>
        </div>
      </div>

      {/* 2. METADATA ROW & 3. POPULATION CARD */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Metadata Card (Confidence, Freshness, Last Updated) */}
        <div className="md:col-span-2 bg-white rounded-2xl border border-slate-200 p-6 shadow-xs flex flex-wrap items-center justify-between gap-4">
          <div>
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block mb-2">
              Model Diagnostics
            </span>
            <div className="flex flex-wrap items-center gap-2.5">
              {getConfidenceDot(detail.confidence)}
              <span className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-700 bg-white border border-slate-200 px-3 py-1 rounded-full shadow-xs">
                <span className="w-2 h-2 rounded-full bg-blue-500"></span>
                <span className="capitalize">{detail.freshness_class?.replace(/_/g, ' ')}</span>
              </span>
            </div>
          </div>

          <div className="border-t sm:border-t-0 sm:border-l border-slate-200 pt-3 sm:pt-0 sm:pl-6">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block mb-1">
              Last Updated
            </span>
            <div className="flex items-center gap-1.5 text-xs font-mono font-bold text-slate-700">
              <Clock className="w-3.5 h-3.5 text-slate-400" />
              <span>{formatDate(detail.computed_at)}</span>
            </div>
          </div>
        </div>

        {/* 3. POPULATION CARD */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs flex items-center justify-between">
          <div>
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Settlement Population</span>
            <div className="text-3xl font-black text-slate-900 mt-1">
              {detail.population?.toLocaleString()}
            </div>
            <p className="text-xs text-slate-500 mt-0.5">Residents requiring risk mitigation</p>
          </div>
          <div className="w-14 h-14 rounded-2xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600">
            <Users className="w-7 h-7" />
          </div>
        </div>
      </div>

      {/* 4. HAZARD BREAKDOWN SECTION */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 sm:p-8 shadow-xs space-y-5">
        <div>
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-amber-600" />
            <h2 className="text-xl font-extrabold text-slate-900">Hazard Susceptibility Breakdown</h2>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Individual environmental model assessments evaluated across geological, hydrological, and meteorological domains.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {detail.hazards?.map((h, idx) => {
            const isApplicable = h.applicable !== false;
            return (
              <div
                key={idx}
                className={`rounded-xl border p-5 transition flex flex-col justify-between space-y-4 ${
                  isApplicable
                    ? 'bg-slate-50/60 border-slate-200 hover:border-slate-300 hover:shadow-xs'
                    : 'bg-slate-100/70 border-slate-200 opacity-60'
                }`}
              >
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <div className="p-2 rounded-lg bg-white shadow-xs border border-slate-200">
                      {getHazardIcon(h.hazard)}
                    </div>
                    {isApplicable ? (
                      <span className="text-[10px] font-bold font-mono text-slate-400 uppercase">
                        Conf: {h.confidence}
                      </span>
                    ) : null}
                  </div>

                  <h3 className="font-bold text-sm text-slate-900 capitalize">
                    {h.hazard?.replace(/_/g, ' ')}
                  </h3>
                </div>

                <div>
                  {isApplicable ? (
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-slate-500 font-medium">Susceptibility:</span>
                      <span
                        className={`px-2.5 py-0.5 rounded-md text-xs font-extrabold capitalize ${
                          h.susceptibility === 'high'
                            ? 'bg-red-100 text-[#dc2626] border border-red-200'
                            : h.susceptibility === 'medium'
                            ? 'bg-orange-100 text-[#f97316] border border-orange-200'
                            : 'bg-emerald-100 text-[#22c55e] border border-emerald-200'
                        }`}
                      >
                        {h.susceptibility}
                      </span>
                    </div>
                  ) : (
                    <div className="text-xs font-bold text-slate-400 bg-slate-200/60 rounded-md py-1 text-center">
                      Not Applicable
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* 5. "WHY THIS PRIORITY?" PANEL */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 sm:p-8 shadow-xs space-y-4">
        <div className="flex items-center gap-2">
          <FileText className="w-5 h-5 text-blue-600" />
          <h2 className="text-xl font-extrabold text-slate-900">Why This Priority?</h2>
        </div>
        <p className="text-xs text-slate-500">
          Key empirical rationale, historical event frequencies, and critical terrain factor reason codes.
        </p>

        <div className="space-y-3 pt-2">
          {detail.reason_codes?.map((code, idx) => (
            <div
              key={idx}
              className="p-4 rounded-xl bg-slate-50 border border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:bg-slate-100/80 transition"
            >
              <div>
                <div className="font-bold text-sm text-slate-900">{code.label}</div>
                <div className="text-xs text-slate-500 mt-0.5">{code.evidence}</div>
              </div>
              <span className="self-start sm:self-auto text-[11px] font-bold text-blue-700 bg-blue-50 border border-blue-200 px-3 py-1 rounded-full uppercase tracking-wider font-mono">
                {code.confidence} confidence
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* 6. BOTTOM ACTION BAR: View Relocation Options & Run What-If Scenario */}
      <div className="bg-[#0b192c] text-white rounded-2xl p-6 sm:p-8 shadow-md flex flex-col sm:flex-row items-center justify-between gap-4">
        <div>
          <h3 className="text-lg font-bold">Recommended Policy Next Steps</h3>
          <p className="text-xs text-slate-300 mt-0.5">
            Proceed with relocation candidate matching or run climate shock simulation models.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3 w-full sm:w-auto">
          {/* Button 1: View Relocation Options */}
          <Link
            to={`/habitation/${id}/relocation`}
            className="flex-1 sm:flex-none inline-flex items-center justify-center gap-2 px-5 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-sm font-bold shadow-xs transition cursor-pointer"
          >
            <Compass className="w-4 h-4" />
            <span>View Relocation Options</span>
          </Link>

          {/* Button 2: Run What-If Scenario */}
          <Link
            to={`/habitation/${id}/whatif`}
            className="flex-1 sm:flex-none inline-flex items-center justify-center gap-2 px-5 py-3 bg-slate-800 hover:bg-slate-700 text-slate-100 rounded-xl text-sm font-bold border border-slate-600 shadow-xs transition cursor-pointer"
          >
            <SlidersHorizontal className="w-4 h-4 text-blue-400" />
            <span>Run What-If Scenario</span>
          </Link>
        </div>
      </div>
    </div>
  );
}
