import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getHabitationDetail, runWhatIf } from '../api';
import { 
  SlidersHorizontal, 
  ArrowLeft, 
  Play, 
  RotateCcw, 
  CloudRain, 
  Users, 
  Droplet, 
  MapPin, 
  TrendingUp, 
  TrendingDown, 
  ArrowRight, 
  Sparkles, 
  AlertOctagon, 
  Split, 
  CheckCircle2, 
  RefreshCw,
  Info,
  ShieldAlert
} from 'lucide-react';

export default function WhatIf() {
  const { id } = useParams();
  const [habitation, setHabitation] = useState(null);
  const [loadingInitial, setLoadingInitial] = useState(true);

  // Scenario Controls State
  const [rainfallLevel, setRainfallLevel] = useState('moderate'); // 'low' | 'moderate' | 'extreme'
  const [population, setPopulation] = useState(3200);
  const [waterCapacity, setWaterCapacity] = useState('');
  const [relocationRadius, setRelocationRadius] = useState(20);

  // Simulation State
  const [computing, setComputing] = useState(false);
  const [simulationResult, setSimulationResult] = useState(null);

  useEffect(() => {
    fetchBaseline();
  }, [id]);

  const fetchBaseline = async () => {
    setLoadingInitial(true);
    try {
      const data = await getHabitationDetail(id);
      setHabitation(data);
      if (data) {
        setPopulation(data.population || 3200);
        setRainfallLevel('moderate');
        setWaterCapacity('');
        setRelocationRadius(20);
        setSimulationResult(null);
      }
    } catch (err) {
      console.error('Failed to load baseline detail:', err);
    } finally {
      setLoadingInitial(false);
    }
  };

  const handleRunScenario = async () => {
    setComputing(true);
    try {
      const result = await runWhatIf(id, {
        rainfall_level: rainfallLevel,
        population: Number(population),
        water_capacity: waterCapacity ? Number(waterCapacity) : null,
        relocation_radius_km: Number(relocationRadius)
      });
      setSimulationResult(result);
    } catch (err) {
      console.error('Failed to run scenario:', err);
    } finally {
      setComputing(false);
    }
  };

  const handleReset = () => {
    if (habitation) {
      setPopulation(habitation.population || 3200);
    }
    setRainfallLevel('moderate');
    setWaterCapacity('');
    setRelocationRadius(20);
    setSimulationResult(null);
  };

  // Helper for Status Badge
  const getRecStatusBadge = (status, isHighlighted = false) => {
    switch (status) {
      case 'recommended':
        return (
          <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-black border ${
            isHighlighted 
              ? 'bg-emerald-500 text-white border-emerald-600 shadow-sm' 
              : 'bg-emerald-100 text-[#22c55e] border-emerald-200'
          }`}>
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>Optimal Single Site</span>
          </span>
        );
      case 'multi_site':
        return (
          <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-black border ${
            isHighlighted 
              ? 'bg-blue-600 text-white border-blue-700 shadow-sm' 
              : 'bg-blue-100 text-blue-800 border-blue-200'
          }`}>
            <Split className="w-3.5 h-3.5" />
            <span>Multi-Site Split</span>
          </span>
        );
      case 'no_safe_site':
      default:
        return (
          <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-black border ${
            isHighlighted 
              ? 'bg-rose-600 text-white border-rose-700 shadow-sm' 
              : 'bg-rose-100 text-[#dc2626] border-rose-200'
          }`}>
            <AlertOctagon className="w-3.5 h-3.5" />
            <span>No Safe Site Found</span>
          </span>
        );
    }
  };

  // Helper for Priority Badge
  const getPriorityBadge = (priority, isHighlighted = false) => {
    switch (priority) {
      case 'P1':
        return (
          <span className={`px-3 py-1 rounded-full text-xs font-black border ${
            isHighlighted
              ? 'bg-[#dc2626] text-white border-red-700 shadow-xs'
              : 'bg-red-100 text-[#dc2626] border-red-200'
          }`}>
            P1 Critical
          </span>
        );
      case 'P2':
        return (
          <span className={`px-3 py-1 rounded-full text-xs font-black border ${
            isHighlighted
              ? 'bg-[#f97316] text-white border-orange-700 shadow-xs'
              : 'bg-orange-100 text-[#f97316] border-orange-200'
          }`}>
            P2 High
          </span>
        );
      case 'P3':
        return (
          <span className={`px-3 py-1 rounded-full text-xs font-black border ${
            isHighlighted
              ? 'bg-[#ca8a04] text-white border-yellow-700 shadow-xs'
              : 'bg-yellow-100 text-[#ca8a04] border-yellow-200'
          }`}>
            P3 Medium
          </span>
        );
      case 'P4':
      default:
        return (
          <span className={`px-3 py-1 rounded-full text-xs font-black border ${
            isHighlighted
              ? 'bg-[#22c55e] text-white border-emerald-700 shadow-xs'
              : 'bg-emerald-100 text-[#22c55e] border-emerald-200'
          }`}>
            P4 Low
          </span>
        );
    }
  };

  // Ring color helper
  const getRingColor = (score) => {
    if (score >= 70) return 'border-[#dc2626] text-[#dc2626] bg-red-50/60';
    if (score >= 40) return 'border-[#f97316] text-[#f97316] bg-orange-50/60';
    return 'border-[#22c55e] text-[#22c55e] bg-emerald-50/60';
  };

  if (loadingInitial) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        <div className="bg-white rounded-2xl border border-slate-200 p-8 shadow-xs animate-pulse space-y-4">
          <div className="h-6 bg-slate-200 rounded w-1/3"></div>
          <div className="h-10 bg-slate-100 rounded-xl"></div>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <div className="lg:col-span-5 bg-white rounded-2xl border border-slate-200 p-8 shadow-xs animate-pulse space-y-6">
            <div className="h-8 bg-slate-100 rounded-xl"></div>
            <div className="h-8 bg-slate-100 rounded-xl"></div>
            <div className="h-8 bg-slate-100 rounded-xl"></div>
          </div>
          <div className="lg:col-span-7 bg-white rounded-2xl border border-slate-200 p-8 shadow-xs animate-pulse">
            <div className="h-64 bg-slate-50 rounded-xl"></div>
          </div>
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
          <p className="text-sm text-slate-500">Could not resolve simulation parameters for ID: {id}</p>
          <Link to="/" className="inline-flex items-center gap-2 px-5 py-2.5 bg-blue-600 text-white rounded-xl text-xs font-bold shadow-xs">
            <ArrowLeft className="w-4 h-4" /> Back to Dashboard
          </Link>
        </div>
      </div>
    );
  }

  const basePop = habitation.population || 3200;
  const maxPop = basePop + 3000;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Top Breadcrumb */}
      <div className="flex items-center justify-between">
        <Link
          to={`/habitation/${id}`}
          className="inline-flex items-center gap-1.5 text-xs font-bold text-slate-600 hover:text-blue-600 bg-white px-3 py-1.5 rounded-lg border border-slate-200 shadow-xs transition"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to {habitation.name}</span>
        </Link>

        <button
          onClick={handleReset}
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-700 bg-white px-3 py-1.5 rounded-lg border border-slate-200 shadow-xs transition cursor-pointer"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          <span>Reset to Current</span>
        </button>
      </div>

      {/* 1. HEADER */}
      <div className="bg-white rounded-2xl border border-slate-200 p-8 shadow-xs">
        <div className="flex items-center gap-2 mb-1.5">
          <span className="font-mono text-xs font-bold bg-blue-50 text-blue-700 border border-blue-200 px-2.5 py-0.5 rounded-md">
            {id}
          </span>
          <span className="text-slate-300">•</span>
          <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">
            Scenario Sandbox
          </span>
        </div>

        <h1 className="text-3xl font-black text-slate-900 tracking-tight">
          What-If Simulator: <span className="text-blue-600">{habitation.name}</span>
        </h1>
        <p className="text-slate-600 text-sm mt-1">
          Simulate climate shocks, sudden demographic surges, and resource constraints to stress-test relocation feasibility.
        </p>
      </div>

      {/* 2. MAIN GRID: CONTROLS (LEFT) & BEFORE/AFTER (RIGHT) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* ========================================================================= */}
        {/* LEFT PANEL: SCENARIO PARAMETERS & CONTROLS (5 cols) */}
        {/* ========================================================================= */}
        <div className="lg:col-span-5 bg-white rounded-2xl border border-slate-200 p-6 sm:p-7 shadow-xs space-y-6">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h2 className="text-base font-extrabold text-slate-900 flex items-center gap-2">
              <SlidersHorizontal className="w-4 h-4 text-blue-600" />
              <span>Simulation Overrides</span>
            </h2>
            <span className="text-[11px] font-mono text-slate-400">Baseline Pop: {basePop.toLocaleString()}</span>
          </div>

          <div className="space-y-5">
            {/* Control 1: Rainfall Level */}
            <div className="space-y-2">
              <label className="flex items-center justify-between text-xs font-bold text-slate-700">
                <span className="flex items-center gap-1.5">
                  <CloudRain className="w-4 h-4 text-blue-600" />
                  <span>Rainfall Shock Anomaly</span>
                </span>
                <span className="text-[11px] font-mono text-blue-600 font-bold uppercase">
                  {rainfallLevel === 'extreme' ? '+15 Risk Pts' : rainfallLevel === 'moderate' ? '+5 Risk Pts' : 'Baseline'}
                </span>
              </label>

              <div className="grid grid-cols-3 gap-2 bg-slate-100 p-1 rounded-xl border border-slate-200">
                {[
                  { key: 'low', label: 'Low', desc: 'Normal' },
                  { key: 'moderate', label: 'Moderate', desc: '+25% Surge' },
                  { key: 'extreme', label: 'Extreme', desc: '+70% Cloudburst' }
                ].map(({ key, label, desc }) => (
                  <button
                    key={key}
                    type="button"
                    onClick={() => setRainfallLevel(key)}
                    className={`py-2 px-1 rounded-lg text-center transition cursor-pointer ${
                      rainfallLevel === key
                        ? 'bg-blue-600 text-white shadow-xs font-bold'
                        : 'text-slate-700 hover:bg-slate-200/70 font-semibold'
                    }`}
                  >
                    <div className="text-xs">{label}</div>
                    <div className={`text-[9px] ${rainfallLevel === key ? 'text-blue-100' : 'text-slate-400'}`}>
                      {desc}
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Control 2: Population Slider & Input */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs font-bold text-slate-700">
                <label className="flex items-center gap-1.5">
                  <Users className="w-4 h-4 text-indigo-600" />
                  <span>Simulated Population Surge</span>
                </label>
                <span className="font-mono text-indigo-700 text-sm font-black">
                  {Number(population).toLocaleString()} pax
                </span>
              </div>

              <input
                type="range"
                min={basePop}
                max={maxPop}
                step={50}
                value={population}
                onChange={(e) => setPopulation(Number(e.target.value))}
                className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-indigo-600"
              />

              <div className="flex justify-between text-[11px] text-slate-400 font-mono">
                <span>Current: {basePop.toLocaleString()}</span>
                <span>+{Math.max(0, population - basePop).toLocaleString()} extra</span>
                <span>Max: {maxPop.toLocaleString()}</span>
              </div>
            </div>

            {/* Control 3: Water Capacity (Optional) */}
            <div className="space-y-1.5">
              <label className="flex items-center justify-between text-xs font-bold text-slate-700">
                <span className="flex items-center gap-1.5">
                  <Droplet className="w-4 h-4 text-cyan-600" />
                  <span>Receptor Water Capacity (Optional)</span>
                </span>
                <span className="text-[10px] text-slate-400 uppercase">Cap Threshold</span>
              </label>

              <input
                type="number"
                value={waterCapacity}
                onChange={(e) => setWaterCapacity(e.target.value)}
                placeholder="e.g. 3000 pax (leave blank for unconstrained)"
                className="w-full px-3.5 py-2 rounded-xl border border-slate-200 bg-slate-50 text-xs text-slate-800 placeholder-slate-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 transition font-mono"
              />
              <p className="text-[11px] text-slate-400">
                Tests bottleneck if receptor supply is lower than demographic demand.
              </p>
            </div>

            {/* Control 4: Relocation Radius */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs font-bold text-slate-700">
                <label className="flex items-center gap-1.5">
                  <MapPin className="w-4 h-4 text-emerald-600" />
                  <span>Relocation Radius Perimeter</span>
                </label>
                <span className="font-mono text-emerald-700 text-sm font-black">
                  {relocationRadius} km
                </span>
              </div>

              <input
                type="range"
                min={5}
                max={50}
                step={1}
                value={relocationRadius}
                onChange={(e) => setRelocationRadius(Number(e.target.value))}
                className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-emerald-600"
              />

              <div className="flex justify-between text-[11px] text-slate-400 font-mono">
                <span>Tight: 5 km</span>
                <span>Standard: 20 km</span>
                <span>Regional: 50 km</span>
              </div>
            </div>
          </div>

          {/* Action Buttons: Run & Reset */}
          <div className="pt-4 border-t border-slate-100 space-y-2">
            <button
              onClick={handleRunScenario}
              disabled={computing}
              className="w-full py-3.5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-sm font-black flex items-center justify-center gap-2 shadow-xs transition cursor-pointer disabled:opacity-60"
            >
              {computing ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Computing Scenario Models (300ms)...</span>
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 fill-white" />
                  <span>Run Scenario Simulation</span>
                </>
              )}
            </button>

            <button
              onClick={handleReset}
              disabled={computing}
              className="w-full py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-bold transition cursor-pointer"
            >
              Reset to Baseline
            </button>
          </div>
        </div>

        {/* ========================================================================= */}
        {/* RIGHT PANEL: BEFORE / AFTER COMPARISON (7 cols) */}
        {/* ========================================================================= */}
        <div className="lg:col-span-7 flex flex-col justify-between">
          {!simulationResult ? (
            /* Empty State */
            <div className="bg-white rounded-2xl border-2 border-dashed border-slate-300 p-12 text-center h-full flex flex-col items-center justify-center space-y-4 shadow-xs">
              <div className="w-16 h-16 rounded-2xl bg-blue-50 border border-blue-100 flex items-center justify-center text-blue-600">
                <Sparkles className="w-8 h-8" />
              </div>
              <div className="max-w-md space-y-1">
                <h3 className="text-lg font-black text-slate-800">
                  Ready to Simulate
                </h3>
                <p className="text-xs text-slate-500 leading-relaxed">
                  Adjust scenario parameters on the left and click <strong>"Run Scenario Simulation"</strong> to inspect projected risk changes and updated relocation recommendations.
                </p>
              </div>
            </div>
          ) : (
            /* Active Comparison Results */
            <div className="space-y-6">
              <div className="bg-white rounded-2xl border border-slate-200 p-6 sm:p-7 shadow-xs space-y-6">
                <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                  <div>
                    <h2 className="text-base font-extrabold text-slate-900">
                      Scenario Impact Assessment
                    </h2>
                    <p className="text-xs text-slate-500">
                      Direct comparative output against baseline parameters.
                    </p>
                  </div>

                  {/* Overall Risk Delta Badge */}
                  <div className={`px-3 py-1.5 rounded-xl border flex items-center gap-1.5 text-xs font-black ${
                    simulationResult.after.delta > 0
                      ? 'bg-red-50 text-[#dc2626] border-red-300'
                      : simulationResult.after.delta < 0
                      ? 'bg-emerald-50 text-[#22c55e] border-emerald-300'
                      : 'bg-slate-100 text-slate-700 border-slate-200'
                  }`}>
                    {simulationResult.after.delta > 0 ? (
                      <>
                        <TrendingUp className="w-4 h-4 text-[#dc2626]" />
                        <span>+{simulationResult.after.delta} Risk Surge</span>
                      </>
                    ) : simulationResult.after.delta < 0 ? (
                      <>
                        <TrendingDown className="w-4 h-4 text-[#22c55e]" />
                        <span>{simulationResult.after.delta} Risk Drop</span>
                      </>
                    ) : (
                      <span>No Risk Delta (0)</span>
                    )}
                  </div>
                </div>

                {/* Side-by-Side Before / After Cards */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                  {/* BEFORE CARD */}
                  <div className="bg-slate-50 rounded-2xl border border-slate-200 p-5 space-y-4">
                    <div className="flex items-center justify-between pb-2 border-b border-slate-200">
                      <span className="text-xs font-black uppercase text-slate-500 tracking-wider">
                        Baseline (Before)
                      </span>
                      {getPriorityBadge(simulationResult.before.priority)}
                    </div>

                    <div className="flex items-center gap-4">
                      <div className={`w-20 h-20 rounded-full border-4 flex flex-col items-center justify-center shadow-inner ${getRingColor(simulationResult.before.risk_score)}`}>
                        <span className="text-2xl font-black leading-none">
                          {simulationResult.before.risk_score}
                        </span>
                        <span className="text-[9px] font-bold uppercase text-slate-400">/ 100</span>
                      </div>

                      <div className="space-y-1 text-xs">
                        <div className="font-bold text-slate-800">
                          {simulationResult.before.population.toLocaleString()} pax
                        </div>
                        <div className="text-[11px] text-slate-500">Normal Rainfall</div>
                        <div className="text-[11px] text-slate-500">Baseline Radius: 20 km</div>
                      </div>
                    </div>

                    <div className="pt-2 border-t border-slate-200 space-y-1">
                      <span className="text-[10px] font-bold uppercase text-slate-400 block">Baseline Policy:</span>
                      <div>{getRecStatusBadge(simulationResult.before.recommendation_status)}</div>
                    </div>
                  </div>

                  {/* AFTER CARD */}
                  {(() => {
                    const priorityChanged = simulationResult.before.priority !== simulationResult.after.priority;
                    const recChanged = simulationResult.before.recommendation_status !== simulationResult.after.recommendation_status;

                    return (
                      <div className={`rounded-2xl border-2 p-5 space-y-4 transition ${
                        simulationResult.after.delta > 0
                          ? 'bg-red-50/20 border-red-500 shadow-sm'
                          : 'bg-emerald-50/20 border-emerald-500 shadow-sm'
                      }`}>
                        <div className="flex items-center justify-between pb-2 border-b border-slate-200">
                          <span className="text-xs font-black uppercase text-blue-700 tracking-wider">
                            Simulated (After)
                          </span>
                          {getPriorityBadge(simulationResult.after.priority, priorityChanged)}
                        </div>

                        <div className="flex items-center gap-4">
                          <div className={`w-20 h-20 rounded-full border-4 flex flex-col items-center justify-center shadow-inner ${getRingColor(simulationResult.after.risk_score)}`}>
                            <span className="text-2xl font-black leading-none">
                              {simulationResult.after.risk_score}
                            </span>
                            <span className="text-[9px] font-bold uppercase text-slate-400">/ 100</span>
                          </div>

                          <div className="space-y-1 text-xs">
                            <div className="font-bold text-slate-800">
                              {simulationResult.after.population.toLocaleString()} pax
                            </div>
                            <div className="text-[11px] text-slate-600 capitalize">
                              Rainfall: <strong className="text-slate-900">{simulationResult.after.overrides.rainfall_level}</strong>
                            </div>
                            <div className="text-[11px] text-slate-600">
                              Radius: <strong className="text-slate-900">{simulationResult.after.overrides.relocation_radius_km} km</strong>
                            </div>
                          </div>
                        </div>

                        <div className="pt-2 border-t border-slate-200 space-y-1">
                          <span className="text-[10px] font-bold uppercase text-slate-400 block">Simulated Policy:</span>
                          <div>{getRecStatusBadge(simulationResult.after.recommendation_status, recChanged)}</div>
                        </div>
                      </div>
                    );
                  })()}
                </div>

                {/* Key Simulation Observations */}
                <div className="p-4 rounded-xl bg-blue-50/60 border border-blue-200 text-xs text-blue-950 space-y-1.5">
                  <div className="font-extrabold flex items-center gap-1.5">
                    <Info className="w-4 h-4 text-blue-700" />
                    <span>Scenario Narrative Summary</span>
                  </div>
                  <p className="leading-relaxed">
                    Under <span className="font-bold">{rainfallLevel} rainfall surge</span> and demographic loading of <span className="font-bold">{population.toLocaleString()} residents</span>, the composite vulnerability score shifted to <span className="font-bold">{simulationResult.after.risk_score}/100</span>. The policy recommendation automatically adjusts to <span className="font-bold capitalize">{simulationResult.after.recommendation_status.replace(/_/g, ' ')}</span>.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* 7. BOTTOM LINK: View Full Recommendation Details */}
          {simulationResult && (
            <div className="mt-6 bg-[#0b192c] text-white rounded-2xl p-6 shadow-md flex flex-col sm:flex-row items-center justify-between gap-4">
              <div>
                <h3 className="text-base font-bold">Inspect Decision Engine</h3>
                <p className="text-xs text-slate-300 mt-0.5">
                  Review the full multi-site split and candidate allocation matrix.
                </p>
              </div>

              <Link
                to={`/recommendation/${id}`}
                className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-bold shadow-xs transition"
              >
                <span>View Full Recommendation Details</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
