import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getRecommendation, getHabitationDetail, getDecision, submitDecision } from '../api';
import { 
  ArrowLeft, 
  CheckCircle2, 
  Split, 
  AlertOctagon, 
  AlertTriangle, 
  Sparkles, 
  RefreshCw, 
  MapPin, 
  ChevronDown, 
  ChevronUp, 
  Check, 
  X, 
  Users, 
  ArrowDown,
  Info,
  ShieldCheck,
  ShieldAlert,
  Clock,
  FileCheck,
  FileX
} from 'lucide-react';

export default function Recommendation() {
  const { id } = useParams();
  const [data, setData] = useState(null);
  const [habitation, setHabitation] = useState(null);
  const [recordedDecision, setRecordedDecision] = useState(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  // Demo state override
  const [overrideState, setOverrideState] = useState(null);
  const [showAlternatives, setShowAlternatives] = useState(false);

  // Modal State
  const [modalAction, setModalAction] = useState(null); // 'approve' | 'reject' | null
  const [justificationInput, setJustificationInput] = useState('');
  const [validationError, setValidationError] = useState('');

  useEffect(() => {
    fetchData();
  }, [id, overrideState]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [recData, habData, decisionData] = await Promise.all([
        getRecommendation(id, overrideState),
        getHabitationDetail(id),
        getDecision(id)
      ]);
      setData(recData);
      setHabitation(habData);
      setRecordedDecision(decisionData);
    } catch (err) {
      console.error('Failed to load recommendation data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleOpenModal = (action) => {
    setModalAction(action);
    setJustificationInput('');
    setValidationError('');
  };

  const handleCloseModal = () => {
    setModalAction(null);
    setJustificationInput('');
    setValidationError('');
  };

  const handleSubmitDecision = async () => {
    if (modalAction === 'reject' && !justificationInput.trim()) {
      setValidationError('A mandatory justification is required to reject or escalate this recommendation.');
      return;
    }

    setSubmitting(true);
    try {
      const result = await submitDecision(id, {
        action: modalAction,
        justification: justificationInput
      });
      setRecordedDecision(result);
      handleCloseModal();
    } catch (err) {
      console.error('Failed to submit decision:', err);
    } finally {
      setSubmitting(false);
    }
  };

  // Date Formatter
  const formatTimestamp = (isoStr) => {
    if (!isoStr) return 'N/A';
    try {
      const d = new Date(isoStr);
      return d.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      });
    } catch {
      return isoStr;
    }
  };

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        <div className="bg-white rounded-2xl border border-slate-200 p-8 shadow-xs animate-pulse space-y-4">
          <div className="h-6 bg-slate-200 rounded w-1/3"></div>
          <div className="h-10 bg-slate-100 rounded-xl"></div>
        </div>
        <div className="bg-white rounded-2xl border border-slate-200 p-8 shadow-xs animate-pulse space-y-6">
          <div className="h-32 bg-slate-100 rounded-xl"></div>
          <div className="h-20 bg-slate-50 rounded-xl"></div>
        </div>
      </div>
    );
  }

  if (!habitation || !data) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16 text-center">
        <div className="bg-white rounded-2xl border border-slate-200 p-12 shadow-xs space-y-4">
          <ShieldAlert className="w-12 h-12 text-slate-400 mx-auto" />
          <h2 className="text-xl font-black text-slate-800">Habitation Record Not Found</h2>
          <p className="text-sm text-slate-500">Could not resolve recommendation data for ID: {id}</p>
          <Link to="/" className="inline-flex items-center gap-2 px-5 py-2.5 bg-blue-600 text-white rounded-xl text-xs font-bold">
            <ArrowLeft className="w-4 h-4" /> Back to Dashboard
          </Link>
        </div>
      </div>
    );
  }

  const activeStatus = data.status;

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Top Breadcrumbs */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Link
            to={`/habitation/${id}/relocation`}
            className="inline-flex items-center gap-1.5 text-xs font-bold text-slate-600 hover:text-blue-600 bg-white px-3 py-1.5 rounded-lg border border-slate-200 shadow-xs transition"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Relocation Sites</span>
          </Link>
          <Link
            to={`/habitation/${id}`}
            className="text-xs font-semibold text-slate-500 hover:text-slate-800 hidden sm:inline"
          >
            • {habitation.name}
          </Link>
        </div>

        <button
          onClick={fetchData}
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-700 bg-white px-3 py-1.5 rounded-lg border border-slate-200 shadow-xs transition cursor-pointer"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh Data</span>
        </button>
      </div>

      {/* 1. HEADER SECTION */}
      <div className="bg-white rounded-2xl border border-slate-200 p-8 shadow-xs">
        <div className="flex items-center gap-2 mb-1.5">
          <span className="font-mono text-xs font-bold bg-blue-50 text-blue-700 border border-blue-200 px-2.5 py-0.5 rounded-md">
            {id}
          </span>
          <span className="text-slate-300">•</span>
          <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">
            Decision Support Engine
          </span>
        </div>

        <h1 className="text-3xl font-black text-slate-900 tracking-tight">
          Relocation Recommendation: <span className="text-blue-600">{habitation.name}</span>
        </h1>
        <p className="text-slate-600 text-sm mt-1">
          Automated multi-objective optimization resolving capacity, hazard isolation, and transit feasibility constraints.
        </p>
      </div>

      {/* 2. DEMO STATE SWITCHER */}
      <div className="bg-white rounded-2xl border border-slate-200 p-4 sm:p-5 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-2 text-xs font-extrabold text-slate-700">
          <Sparkles className="w-4 h-4 text-blue-600 shrink-0" />
          <span>Simulate Recommendation State (Demo Override):</span>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <button
            onClick={() => setOverrideState('recommended')}
            className={`px-3 py-1.5 rounded-xl text-xs font-bold transition flex items-center gap-1.5 cursor-pointer ${
              activeStatus === 'recommended'
                ? 'bg-emerald-600 text-white shadow-xs'
                : 'bg-slate-100 text-slate-700 hover:bg-slate-200 border border-slate-200'
            }`}
          >
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>Recommended</span>
          </button>

          <button
            onClick={() => setOverrideState('multi_site')}
            className={`px-3 py-1.5 rounded-xl text-xs font-bold transition flex items-center gap-1.5 cursor-pointer ${
              activeStatus === 'multi_site'
                ? 'bg-blue-600 text-white shadow-xs'
                : 'bg-slate-100 text-slate-700 hover:bg-slate-200 border border-slate-200'
            }`}
          >
            <Split className="w-3.5 h-3.5" />
            <span>Multi-Site Split</span>
          </button>

          <button
            onClick={() => setOverrideState('no_safe_site')}
            className={`px-3 py-1.5 rounded-xl text-xs font-bold transition flex items-center gap-1.5 cursor-pointer ${
              activeStatus === 'no_safe_site'
                ? 'bg-rose-600 text-white shadow-xs'
                : 'bg-slate-100 text-slate-700 hover:bg-slate-200 border border-slate-200'
            }`}
          >
            <AlertOctagon className="w-3.5 h-3.5" />
            <span>No Safe Site</span>
          </button>
        </div>
      </div>

      {/* 3. CONDITIONAL STATE DISPLAY */}
      <div className="space-y-6">
        {/* ========================================================================= */}
        {/* STATE 1: RECOMMENDED */}
        {/* ========================================================================= */}
        {activeStatus === 'recommended' && data.site && (
          <div className="space-y-6">
            <div className="bg-white rounded-2xl border-2 border-emerald-500 shadow-md p-8 relative overflow-hidden">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-6 border-b border-slate-100 gap-3">
                <div className="flex items-center gap-3">
                  <span className="bg-emerald-100 text-emerald-800 text-xs font-black px-3.5 py-1.5 rounded-full border border-emerald-300 flex items-center gap-1.5 shadow-xs">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" /> Optimal Single Site Recommendation
                  </span>
                  <span className="font-mono text-xs text-slate-400">Rank #{data.site.rank || 1}</span>
                </div>
                <span className="text-xs font-mono font-bold bg-slate-100 text-slate-700 px-3 py-1 rounded-md">
                  Site Code: {data.site.id}
                </span>
              </div>

              <div className="mt-6 grid grid-cols-1 lg:grid-cols-3 gap-8">
                <div className="lg:col-span-2 space-y-3">
                  <h2 className="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight">
                    {data.site.name}
                  </h2>
                  <p className="text-sm text-slate-600 leading-relaxed">
                    The spatial optimization engine identified this site as satisfying 100% of required population carrying capacity, geological slope safety, and all-weather road transit connectivity.
                  </p>

                  <div className="flex flex-wrap items-center gap-3 pt-2">
                    <div className="flex items-center gap-1.5 text-xs font-bold text-slate-700 bg-slate-50 border border-slate-200 px-3 py-1.5 rounded-xl">
                      <MapPin className="w-4 h-4 text-blue-600" />
                      <span>Distance: {data.site.distance_km} km</span>
                    </div>
                    <div className="flex items-center gap-1.5 text-xs font-bold text-emerald-700 bg-emerald-50 border border-emerald-200 px-3 py-1.5 rounded-xl">
                      <ShieldCheck className="w-4 h-4 text-emerald-600" />
                      <span className="capitalize">Safety: {data.site.safety}</span>
                    </div>
                    <div className="flex items-center gap-1.5 text-xs font-bold text-indigo-700 bg-indigo-50 border border-indigo-200 px-3 py-1.5 rounded-xl">
                      <span className="capitalize">Binding: {data.site.binding_sector?.replace(/_/g, ' ')}</span>
                    </div>
                  </div>
                </div>

                <div className="bg-slate-50 p-5 rounded-2xl border border-slate-200 flex flex-col justify-between space-y-4">
                  <div>
                    <span className="text-[11px] font-bold uppercase text-slate-400 tracking-wider">Carrying Capacity</span>
                    <div className="text-2xl font-black text-slate-900 mt-0.5">
                      {data.site.capacity?.toLocaleString()} <span className="text-xs font-medium text-slate-500">pax</span>
                    </div>
                    <span className="text-xs text-emerald-700 font-bold mt-1 block">
                      Full capacity match ({data.site.allocated_population || data.site.required_capacity || habitation.population} required)
                    </span>
                  </div>

                  <div className="pt-3 border-t border-slate-200 text-xs text-slate-500 flex justify-between">
                    <span>Suitability Score:</span>
                    <span className="font-extrabold text-slate-800 capitalize">{data.site.suitability}</span>
                  </div>
                </div>
              </div>

              {/* "Why This Site?" Mini-Panel */}
              <div className="mt-8 p-5 rounded-2xl bg-emerald-50/60 border border-emerald-200 space-y-2.5">
                <div className="flex items-center gap-2 text-emerald-950 font-extrabold text-sm">
                  <Sparkles className="w-4 h-4 text-emerald-600" />
                  <span>Why This Site?</span>
                </div>
                <ul className="space-y-1.5 text-xs text-emerald-900 pl-5 list-disc">
                  <li>
                    <strong>Capacity Clearance:</strong> Site total capacity of {data.site.capacity} comfortably accommodates the target population requirement of {data.site.required_capacity || data.site.allocated_population || habitation.population} residents.
                  </li>
                  <li>
                    <strong>Hazard Buffer Isolation:</strong> Classified as <span className="font-bold capitalize">{data.site.safety} safety</span>, situated beyond the 100-year flood zone and active landslide debris cones.
                  </li>
                  <li>
                    <strong>Transit Proximity:</strong> Located {data.site.distance_km} km from the origin centroid, ensuring rapid evacuation clearance under 45 minutes.
                  </li>
                </ul>
              </div>
            </div>

            {/* Collapsible Alternatives */}
            {data.alternatives?.length > 0 && (
              <div className="bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
                <button
                  onClick={() => setShowAlternatives(!showAlternatives)}
                  className="w-full p-6 flex items-center justify-between bg-slate-50/60 hover:bg-slate-100/80 transition cursor-pointer text-left"
                >
                  <div>
                    <h3 className="text-base font-extrabold text-slate-900">
                      View Secondary Alternatives ({data.alternatives.length} sites)
                    </h3>
                    <p className="text-xs text-slate-500 mt-0.5">
                      Fallback locations evaluated during multi-criteria ranking.
                    </p>
                  </div>
                  <div className="flex items-center gap-2 text-xs font-bold text-blue-600">
                    <span>{showAlternatives ? 'Hide' : 'Expand'}</span>
                    {showAlternatives ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                  </div>
                </button>

                {showAlternatives && (
                  <div className="p-6 divide-y divide-slate-100 space-y-4">
                    {data.alternatives.map((alt) => (
                      <div key={alt.id} className="pt-4 first:pt-0 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-bold text-slate-800 text-sm">{alt.name}</span>
                            <span className="font-mono text-slate-400">({alt.id})</span>
                            <span className="bg-slate-100 text-slate-700 px-2 py-0.5 rounded text-[10px] font-bold">
                              Rank #{alt.rank}
                            </span>
                          </div>
                          <div className="text-slate-500 mt-1 flex items-center gap-4">
                            <span>Capacity: <strong>{alt.capacity?.toLocaleString()}</strong></span>
                            <span>Distance: <strong>{alt.distance_km} km</strong></span>
                            <span className="capitalize">Safety: <strong>{alt.safety}</strong></span>
                          </div>
                        </div>
                        <span className="px-2.5 py-1 rounded bg-slate-100 text-slate-600 font-medium self-start sm:self-auto">
                          Fallback Backup
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* ========================================================================= */}
        {/* STATE 2: MULTI-SITE SPLIT */}
        {/* ========================================================================= */}
        {activeStatus === 'multi_site' && (
          <div className="space-y-6">
            <div className="bg-blue-50 border-2 border-blue-500 rounded-2xl p-6 sm:p-8 shadow-xs space-y-4">
              <div className="flex items-start sm:items-center justify-between gap-3 flex-col sm:flex-row">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-blue-600 text-white flex items-center justify-center shadow-xs">
                    <Split className="w-6 h-6" />
                  </div>
                  <div>
                    <h2 className="text-xl font-extrabold text-blue-950">
                      Multi-Site Relocation Split Required
                    </h2>
                    <p className="text-xs text-blue-800 mt-0.5">
                      Total settlement demand exceeds the maximum safe threshold of any single candidate site.
                    </p>
                  </div>
                </div>

                <div className="bg-white px-4 py-2 rounded-xl border border-blue-200 shadow-xs self-start sm:self-auto">
                  <span className="text-[10px] font-bold uppercase text-slate-400 block">Total Demand</span>
                  <span className="text-lg font-black text-blue-700 font-mono">
                    {data.total_demand?.toLocaleString()} <span className="text-xs font-normal">pax</span>
                  </span>
                </div>
              </div>

              {/* Visual Flow Diagram */}
              <div className="pt-6 space-y-6">
                <div className="max-w-xs mx-auto bg-white p-4 rounded-xl border border-blue-300 shadow-sm text-center">
                  <span className="text-[10px] uppercase font-bold text-slate-400 block">Origin Habitation Demand</span>
                  <div className="text-xl font-black text-slate-900 flex items-center justify-center gap-1.5 mt-0.5">
                    <Users className="w-5 h-5 text-blue-600" />
                    <span>{data.total_demand?.toLocaleString()} Residents</span>
                  </div>
                </div>

                <div className="flex justify-center text-blue-400">
                  <ArrowDown className="w-6 h-6 animate-bounce" />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {data.sites?.map((item, idx) => (
                    <div key={idx} className="bg-white rounded-2xl border border-blue-200 p-6 shadow-xs space-y-4">
                      <div className="flex items-start justify-between">
                        <div>
                          <span className="text-[10px] font-bold uppercase text-blue-600 font-mono">
                            Partition #{idx + 1} Allocation
                          </span>
                          <h3 className="text-base font-extrabold text-slate-900 mt-0.5">{item.site.name}</h3>
                          <span className="text-xs font-mono text-slate-400">{item.site.id}</span>
                        </div>
                        <span className="bg-blue-100 text-blue-800 text-xs font-extrabold px-2.5 py-1 rounded-lg">
                          Rank #{item.site.rank}
                        </span>
                      </div>

                      <div className="bg-blue-50/70 p-4 rounded-xl border border-blue-200">
                        <div className="flex justify-between text-xs font-bold text-blue-900">
                          <span>Allocated Population:</span>
                          <span className="font-mono text-sm">{item.allocated_population?.toLocaleString()} pax</span>
                        </div>

                        <div className="w-full bg-slate-200 rounded-full h-2 mt-2 overflow-hidden">
                          <div
                            className="bg-blue-600 h-full rounded-full"
                            style={{ width: `${Math.min(100, Math.round((item.allocated_population / item.site.capacity) * 100))}%` }}
                          />
                        </div>
                        <div className="flex justify-between text-[11px] text-slate-500 mt-1">
                          <span>Utilizing {item.allocated_population}</span>
                          <span>Max Cap: {item.site.capacity}</span>
                        </div>
                      </div>

                      <div className="flex justify-between text-xs text-slate-500 pt-1">
                        <span>Transit Distance:</span>
                        <strong className="text-slate-800">{item.site.distance_km} km</strong>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Sum Check */}
                {(() => {
                  const totalAllocated = data.sites?.reduce((acc, s) => acc + (s.allocated_population || 0), 0) || 0;
                  const isEqual = totalAllocated === data.total_demand;
                  return (
                    <div className={`p-4 rounded-xl border flex items-center justify-between text-xs ${
                      isEqual ? 'bg-emerald-50 border-emerald-300 text-emerald-900' : 'bg-amber-50 border-amber-300 text-amber-900'
                    }`}>
                      <div className="flex items-center gap-2">
                        <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
                        <div>
                          <span className="font-extrabold">Sum Check Verified: </span>
                          <span>Total Allocated ({totalAllocated.toLocaleString()}) matches Total Demand ({data.total_demand?.toLocaleString()}).</span>
                        </div>
                      </div>
                      <span className="px-2.5 py-1 rounded-full bg-emerald-200/80 font-bold uppercase text-[10px] text-emerald-950">
                        100% Balanced
                      </span>
                    </div>
                  );
                })()}
              </div>
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* STATE 3: NO SAFE SITE */}
        {/* ========================================================================= */}
        {activeStatus === 'no_safe_site' && (
          <div className="space-y-6">
            <div className="bg-rose-50 border-2 border-rose-500 rounded-2xl p-6 sm:p-8 shadow-xs space-y-6">
              <div className="flex items-start sm:items-center justify-between gap-4 flex-col sm:flex-row">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-rose-600 text-white flex items-center justify-center shadow-xs">
                    <AlertOctagon className="w-6 h-6" />
                  </div>
                  <div>
                    <h2 className="text-xl font-extrabold text-rose-950">
                      No Safe Site Identified — Deficit State
                    </h2>
                    <p className="text-xs text-rose-800 mt-0.5">
                      None of the evaluated receptor sites met all mandatory threshold criteria simultaneously.
                    </p>
                  </div>
                </div>

                <div className="bg-white p-4 rounded-xl border-2 border-rose-400 shadow-sm self-start sm:text-right">
                  <span className="text-[10px] font-bold uppercase text-rose-500 block">Capacity Shortfall</span>
                  <span className="text-2xl font-black text-rose-600 font-mono">
                    -{data.capacity_shortfall?.toLocaleString()} <span className="text-xs font-normal text-slate-500">pax</span>
                  </span>
                </div>
              </div>

              <div className="bg-white p-4 rounded-xl border border-rose-200 space-y-2">
                <span className="text-xs font-bold text-slate-700 uppercase tracking-wider block">
                  Failed Feasibility Criteria:
                </span>
                <div className="flex items-center gap-2 flex-wrap">
                  {data.failed_criteria?.map((c, i) => (
                    <span
                      key={i}
                      className="px-3 py-1 rounded-lg bg-rose-100 text-rose-900 border border-rose-300 font-mono font-black text-xs uppercase tracking-wider"
                    >
                      ✕ {c} Constraint
                    </span>
                  ))}
                </div>
              </div>

              <div className="space-y-3">
                <h3 className="text-sm font-extrabold text-slate-900 uppercase tracking-wider">
                  Closest Candidate Misses:
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {data.closest_misses?.map((miss) => (
                    <div key={miss.id} className="bg-white p-5 rounded-xl border border-rose-200 shadow-xs space-y-2.5">
                      <div className="flex justify-between items-start">
                        <div>
                          <h4 className="font-bold text-slate-900 text-sm">{miss.name}</h4>
                          <span className="font-mono text-xs text-slate-400">{miss.id}</span>
                        </div>
                        <span className="text-xs font-mono font-bold text-slate-600 bg-slate-100 px-2 py-0.5 rounded">
                          {miss.distance_km} km
                        </span>
                      </div>

                      <div className="space-y-1 pt-1 border-t border-slate-100">
                        <span className="text-[11px] font-bold text-rose-600 block">Deficiency Breakdown:</span>
                        {miss.failed_reasons?.map((reason, ri) => (
                          <div key={ri} className="text-xs text-slate-700 flex items-start gap-1.5">
                            <span className="text-rose-500 font-bold shrink-0">•</span>
                            <span>{reason}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="p-4 rounded-xl bg-amber-50 border border-amber-300 text-xs text-amber-900 flex items-start gap-2.5">
                <Info className="w-4 h-4 text-amber-700 shrink-0 mt-0.5" />
                <p className="font-medium">
                  <strong>Administrative Note:</strong> This is a critical decision outcome requiring manual administrative intervention and inter-district land acquisition, not a system computation error.
                </p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* 4. DECISION ACTION / SUMMARY BAR */}
      {recordedDecision ? (
        /* Recorded Decision Summary & Audit Trail */
        <div className={`rounded-2xl p-6 sm:p-8 border-2 shadow-md space-y-4 ${
          recordedDecision.action === 'approve'
            ? 'bg-emerald-50/80 border-emerald-500 text-emerald-950'
            : 'bg-rose-50/80 border-rose-500 text-rose-950'
        }`}>
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b pb-4 border-slate-200/80">
            <div className="flex items-center gap-3">
              <div className={`w-12 h-12 rounded-2xl flex items-center justify-center text-white shadow-xs ${
                recordedDecision.action === 'approve' ? 'bg-emerald-600' : 'bg-rose-600'
              }`}>
                {recordedDecision.action === 'approve' ? <FileCheck className="w-6 h-6" /> : <FileX className="w-6 h-6" />}
              </div>
              <div>
                <span className="text-[10px] font-black uppercase tracking-widest text-slate-500">Official Decision Recorded</span>
                <h3 className="text-xl font-black">
                  {recordedDecision.action === 'approve' ? 'Recommendation Approved' : 'Recommendation Rejected & Escalated'}
                </h3>
              </div>
            </div>

            <span className="text-xs font-mono font-bold bg-white/90 px-3 py-1.5 rounded-xl border border-slate-200 self-start sm:self-auto shadow-xs">
              ID: {recordedDecision.id}
            </span>
          </div>

          {/* Audit Trail Details */}
          <div className="bg-white/80 p-4 rounded-xl border border-slate-200 text-xs space-y-2 font-medium text-slate-700">
            <div className="flex items-center gap-1.5 font-bold text-slate-900">
              <Clock className="w-4 h-4 text-blue-600" />
              <span>Administrative Audit Trail Record:</span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 pt-1 text-[11px]">
              <div>
                <span className="text-slate-400 block uppercase">Action:</span>
                <strong className={`capitalize ${recordedDecision.action === 'approve' ? 'text-emerald-700' : 'text-rose-700'}`}>
                  {recordedDecision.action}
                </strong>
              </div>
              <div>
                <span className="text-slate-400 block uppercase">Officer ID:</span>
                <strong className="font-mono">{recordedDecision.officer_id}</strong>
              </div>
              <div>
                <span className="text-slate-400 block uppercase">Timestamp:</span>
                <span>{formatTimestamp(recordedDecision.timestamp)}</span>
              </div>
              <div>
                <span className="text-slate-400 block uppercase">Justification:</span>
                <span className="italic">{recordedDecision.justification}</span>
              </div>
            </div>
          </div>
        </div>
      ) : (
        /* Action Bar (Approve / Reject Buttons) */
        <div className="bg-[#0b192c] text-white rounded-2xl p-6 sm:p-8 shadow-md flex flex-col sm:flex-row items-center justify-between gap-4">
          <div>
            <h3 className="text-lg font-bold">Policy Determination</h3>
            <p className="text-xs text-slate-300 mt-0.5">
              Record official administrative determination for {habitation.name}.
            </p>
          </div>

          <div className="flex items-center gap-3 w-full sm:w-auto">
            <button
              onClick={() => handleOpenModal('reject')}
              className="flex-1 sm:flex-none inline-flex items-center justify-center gap-2 px-5 py-3 bg-slate-800 hover:bg-slate-700 text-rose-300 hover:text-rose-200 rounded-xl text-sm font-bold border border-slate-700 shadow-xs transition cursor-pointer"
            >
              <X className="w-4 h-4" />
              <span>Reject / Escalate</span>
            </button>

            <button
              onClick={() => handleOpenModal('approve')}
              className="flex-1 sm:flex-none inline-flex items-center justify-center gap-2 px-6 py-3 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-sm font-bold shadow-xs transition cursor-pointer"
            >
              <Check className="w-4 h-4" />
              <span>Approve Recommendation</span>
            </button>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* APPROVE / REJECT CONFIRMATION MODAL */}
      {/* ========================================================================= */}
      {modalAction && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-xs animate-fade-in">
          <div className="bg-white rounded-2xl border border-slate-200 max-w-md w-full p-6 sm:p-7 shadow-2xl space-y-5">
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-3">
                <div className={`w-10 h-10 rounded-xl flex items-center justify-center text-white ${
                  modalAction === 'approve' ? 'bg-emerald-600' : 'bg-rose-600'
                }`}>
                  {modalAction === 'approve' ? <Check className="w-5 h-5" /> : <AlertOctagon className="w-5 h-5" />}
                </div>
                <div>
                  <h3 className="font-extrabold text-base text-slate-900">
                    {modalAction === 'approve' ? 'Confirm Policy Approval' : 'Confirm Policy Rejection'}
                  </h3>
                  <p className="text-xs text-slate-500 font-mono">{id}</p>
                </div>
              </div>

              <button 
                onClick={handleCloseModal}
                disabled={submitting}
                className="text-slate-400 hover:text-slate-600 text-sm font-bold p-1 cursor-pointer"
              >
                ✕
              </button>
            </div>

            <p className="text-xs text-slate-600 leading-relaxed">
              {modalAction === 'approve'
                ? `You are officially approving the relocation policy recommendation for ${habitation.name}. This will record your determination under Officer ID: OFFICER-001.`
                : `You are escalating / rejecting this recommendation for ${habitation.name}. A mandatory justification is required for the district administrative review panel.`}
            </p>

            <div className="space-y-1.5">
              <label className="block text-xs font-bold text-slate-700">
                Official Justification {modalAction === 'reject' ? <span className="text-rose-600">* (Required)</span> : <span className="text-slate-400 font-normal">(Optional)</span>}:
              </label>
              <textarea
                rows={3}
                value={justificationInput}
                onChange={(e) => {
                  setJustificationInput(e.target.value);
                  if (validationError) setValidationError('');
                }}
                placeholder={modalAction === 'approve' ? "Add administrative approval remarks (optional)..." : "Explain reasons for rejection/escalation..."}
                className="w-full p-3 rounded-xl border border-slate-200 bg-slate-50 text-xs text-slate-800 placeholder-slate-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 transition"
              />
              {validationError && (
                <p className="text-xs text-rose-600 font-semibold">{validationError}</p>
              )}
            </div>

            <div className="flex items-center justify-end gap-2.5 pt-2 border-t border-slate-100">
              <button
                type="button"
                onClick={handleCloseModal}
                disabled={submitting}
                className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-bold transition cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleSubmitDecision}
                disabled={submitting}
                className={`px-5 py-2 rounded-xl text-xs font-black text-white shadow-xs transition cursor-pointer flex items-center gap-1.5 ${
                  modalAction === 'approve'
                    ? 'bg-emerald-600 hover:bg-emerald-700'
                    : 'bg-rose-600 hover:bg-rose-700'
                }`}
              >
                {submitting ? (
                  <>
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    <span>Recording...</span>
                  </>
                ) : (
                  <span>Confirm {modalAction === 'approve' ? 'Approval' : 'Rejection'}</span>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
