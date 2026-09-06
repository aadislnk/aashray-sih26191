import React, { useEffect, useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import {
  ArrowLeft,
  CloudRain,
  Users,
  Droplets,
  MapPin,
  Play,
  RotateCcw,
  AlertTriangle,
  CheckCircle2,
  ShieldAlert,
  SlidersHorizontal,
} from 'lucide-react';

import {
  getHabitationDetail,
  runWhatIf,
} from '../api';

export default function WhatIf() {
  const { id } = useParams();

  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(true);

  const [rainfall, setRainfall] = useState('moderate');
  const [populationIncrease, setPopulationIncrease] = useState(0);
  const [waterCapacity, setWaterCapacity] = useState(100);
  const [relocationRadius, setRelocationRadius] = useState(20);

  const [result, setResult] = useState(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadVillage();
  }, [id]);

  const loadVillage = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await getHabitationDetail(id);

      if (!data) {
        throw new Error(
          `No live habitation record found for ${id}`
        );
      }

      setDetail(data);
    } catch (err) {
      console.error(err);
      setDetail(null);
      setError(
        err?.message ||
          'Unable to load live habitation data.'
      );
    } finally {
      setLoading(false);
    }
  };

  const baselineRisk = Number(
    detail?.risk_score ?? 0
  );

  const baselinePopulation = Number(
    detail?.population ??
      detail?.total_population_village ??
      0
  );

  const simulatedPopulation = Math.round(
    baselinePopulation *
      (1 + populationIncrease / 100)
  );

  const locationText = [
    detail?.block,
    detail?.district,
    detail?.state,
  ]
    .filter(Boolean)
    .join(', ');

  const rainfallLabel = useMemo(() => {
    if (rainfall === 'low') return 'Low';
    if (rainfall === 'extreme') return 'Extreme';
    return 'Moderate';
  }, [rainfall]);

  const runScenario = async () => {
    if (!detail) return;

    setRunning(true);
    setError(null);

    try {
      const scenario = await runWhatIf(
        detail.id,
        {
          rainfall,
          populationIncrease,
          waterCapacity,
          relocationRadius,
        }
      );

      setResult(scenario);
    } catch (err) {
      console.error(err);

      setError(
        err?.message ||
          'Unable to run the scenario.'
      );
    } finally {
      setRunning(false);
    }
  };

  const resetScenario = () => {
    setRainfall('moderate');
    setPopulationIncrease(0);
    setWaterCapacity(100);
    setRelocationRadius(20);
    setResult(null);
    setError(null);
  };

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white rounded-2xl border border-slate-200 p-10 animate-pulse space-y-5">
          <div className="h-5 bg-slate-200 rounded w-1/4" />
          <div className="h-10 bg-slate-200 rounded w-2/3" />
          <div className="h-32 bg-slate-100 rounded-xl" />
        </div>
      </div>
    );
  }

  if (!detail) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16">
        <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center space-y-4">

          <ShieldAlert className="w-12 h-12 text-slate-400 mx-auto" />

          <h2 className="text-xl font-bold text-slate-800">
            Live Habitation Not Found
          </h2>

          <p className="text-sm text-slate-500">
            The What-If engine could not resolve:
          </p>

          <div className="font-mono text-xs bg-slate-100 border border-slate-200 rounded-lg px-3 py-2 inline-block">
            {id}
          </div>

          <p className="text-xs text-slate-400 max-w-md mx-auto">
            Select a habitation from the live AASHRAY dashboard or map before running a scenario.
          </p>

          {error && (
            <p className="text-xs text-red-500">
              {error}
            </p>
          )}

          <Link
            to="/"
            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-semibold"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Dashboard
          </Link>

        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">

      {/* ======================================================
          TOP BAR
      ====================================================== */}

      <div className="flex items-center justify-between gap-3">

        <Link
          to={`/habitation/${detail.id}`}
          className="inline-flex items-center gap-1.5 text-xs font-bold text-slate-600 hover:text-blue-600 bg-white px-3 py-1.5 rounded-lg border border-slate-200 shadow-xs"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Habitation
        </Link>

        <div className="font-mono text-xs text-slate-400">
          LIVE ID: {detail.id}
        </div>

      </div>

      {/* ======================================================
          HEADER
      ====================================================== */}

      <div className="bg-white rounded-2xl border border-slate-200 p-7 shadow-xs">

        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">

          <div>

            <div className="flex items-center gap-2 text-xs font-bold text-blue-600 uppercase tracking-wider">
              <SlidersHorizontal className="w-4 h-4" />
              AASHRAY What-If Engine
            </div>

            <h1 className="text-3xl font-black text-slate-900 mt-2">
              Climate & Settlement Scenario
            </h1>

            <p className="text-sm text-slate-500 mt-2">
              Test how selected climate, population and relocation assumptions affect the modelled risk.
            </p>

            <div className="flex flex-wrap items-center gap-3 mt-4">

              <span className="font-semibold text-sm text-slate-800">
                {detail.name}
              </span>

              {locationText && (
                <span className="inline-flex items-center gap-1 text-xs text-slate-500">
                  <MapPin className="w-3.5 h-3.5" />
                  {locationText}
                </span>
              )}

            </div>

          </div>

          <div className="bg-slate-50 border border-slate-200 rounded-2xl p-5 min-w-[220px]">

            <div className="text-xs uppercase font-bold tracking-wider text-slate-400">
              Baseline Risk
            </div>

            <div className="text-4xl font-black text-slate-900 mt-1">
              {Math.round(baselineRisk)}
              <span className="text-base text-slate-400">
                /100
              </span>
            </div>

            <div className="text-xs text-slate-500 mt-1">
              Priority: {detail.priority}
            </div>

          </div>

        </div>

      </div>

      {/* ======================================================
          CONTROLS
      ====================================================== */}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

        {/* RAINFALL */}

        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs">

          <div className="flex items-center gap-3">

            <div className="p-3 rounded-xl bg-indigo-50 text-indigo-600">
              <CloudRain className="w-6 h-6" />
            </div>

            <div>
              <h2 className="font-extrabold text-slate-900">
                Rainfall Shock
              </h2>

              <p className="text-xs text-slate-500">
                Simulate increased rainfall pressure.
              </p>
            </div>

          </div>

          <div className="grid grid-cols-3 gap-2 mt-5">

            {[
              ['low', 'Low'],
              ['moderate', 'Moderate'],
              ['extreme', 'Extreme'],
            ].map(([value, label]) => (

              <button
                key={value}
                onClick={() => setRainfall(value)}
                className={`py-3 rounded-xl border text-sm font-bold transition ${
                  rainfall === value
                    ? 'bg-blue-600 text-white border-blue-600'
                    : 'bg-white text-slate-600 border-slate-200 hover:border-blue-300'
                }`}
              >
                {label}
              </button>

            ))}

          </div>

          <div className="text-xs text-slate-500 mt-4">
            Selected rainfall scenario:{' '}
            <strong>{rainfallLabel}</strong>
          </div>

        </div>

        {/* POPULATION */}

        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs">

          <div className="flex items-center gap-3">

            <div className="p-3 rounded-xl bg-indigo-50 text-indigo-600">
              <Users className="w-6 h-6" />
            </div>

            <div>
              <h2 className="font-extrabold text-slate-900">
                Population Increase
              </h2>

              <p className="text-xs text-slate-500">
                Simulate future settlement pressure.
              </p>
            </div>

          </div>

          <div className="mt-5">

            <div className="flex justify-between text-sm font-bold text-slate-700">
              <span>Increase</span>
              <span>{populationIncrease}%</span>
            </div>

            <input
              type="range"
              min="0"
              max="20"
              step="1"
              value={populationIncrease}
              onChange={(e) =>
                setPopulationIncrease(
                  Number(e.target.value)
                )
              }
              className="w-full mt-3"
            />

            <div className="flex justify-between text-xs text-slate-400 mt-2">
              <span>0%</span>
              <span>10%</span>
              <span>20%</span>
            </div>

            <div className="mt-4 text-xs text-slate-500">
              Simulated population:{' '}
              <strong>
                {simulatedPopulation.toLocaleString('en-IN')}
              </strong>
            </div>

          </div>

        </div>

        {/* WATER */}

        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs">

          <div className="flex items-center gap-3">

            <div className="p-3 rounded-xl bg-cyan-50 text-cyan-600">
              <Droplets className="w-6 h-6" />
            </div>

            <div>
              <h2 className="font-extrabold text-slate-900">
                Water Capacity
              </h2>

              <p className="text-xs text-slate-500">
                Test infrastructure capacity against demand.
              </p>
            </div>

          </div>

          <div className="mt-5">

            <div className="flex justify-between text-sm font-bold text-slate-700">
              <span>Capacity</span>
              <span>{waterCapacity}%</span>
            </div>

            <input
              type="range"
              min="50"
              max="150"
              step="5"
              value={waterCapacity}
              onChange={(e) =>
                setWaterCapacity(
                  Number(e.target.value)
                )
              }
              className="w-full mt-3"
            />

            <div className="flex justify-between text-xs text-slate-400 mt-2">
              <span>50%</span>
              <span>100%</span>
              <span>150%</span>
            </div>

          </div>

        </div>

        {/* RELOCATION */}

        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs">

          <div className="flex items-center gap-3">

            <div className="p-3 rounded-xl bg-emerald-50 text-emerald-600">
              <MapPin className="w-6 h-6" />
            </div>

            <div>
              <h2 className="font-extrabold text-slate-900">
                Relocation Radius
              </h2>

              <p className="text-xs text-slate-500">
                Set the search radius for relocation candidates.
              </p>
            </div>

          </div>

          <div className="mt-5">

            <div className="flex justify-between text-sm font-bold text-slate-700">
              <span>Radius</span>
              <span>{relocationRadius} km</span>
            </div>

            <input
              type="range"
              min="5"
              max="50"
              step="5"
              value={relocationRadius}
              onChange={(e) =>
                setRelocationRadius(
                  Number(e.target.value)
                )
              }
              className="w-full mt-3"
            />

            <div className="flex justify-between text-xs text-slate-400 mt-2">
              <span>5 km</span>
              <span>25 km</span>
              <span>50 km</span>
            </div>

          </div>

        </div>

      </div>

      {/* ======================================================
          ACTIONS
      ====================================================== */}

      <div className="flex flex-wrap gap-3">

        <button
          onClick={runScenario}
          disabled={running}
          className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white rounded-xl text-sm font-bold shadow-xs transition"
        >
          <Play className="w-4 h-4" />

          {running
            ? 'Running Scenario...'
            : 'Run What-If Scenario'}
        </button>

        <button
          onClick={resetScenario}
          className="inline-flex items-center justify-center gap-2 px-5 py-3 bg-white hover:bg-slate-50 text-slate-700 rounded-xl text-sm font-bold border border-slate-200 shadow-xs"
        >
          <RotateCcw className="w-4 h-4" />
          Reset
        </button>

      </div>

      {error && (
        <div className="rounded-xl border border-red-200 bg-red-50 p-4 flex items-start gap-3">

          <AlertTriangle className="w-5 h-5 text-red-500 mt-0.5" />

          <div>

            <div className="font-bold text-sm text-red-700">
              Scenario Error
            </div>

            <div className="text-xs text-red-600 mt-1">
              {error}
            </div>

          </div>

        </div>
      )}

      {/* ======================================================
          RESULT
      ====================================================== */}

      {result && (
        <div className="space-y-6">

          <div className="bg-white rounded-2xl border border-slate-200 p-7 shadow-xs">

            <div className="flex items-center gap-2">

              <CheckCircle2 className="w-5 h-5 text-emerald-500" />

              <h2 className="text-xl font-extrabold text-slate-900">
                Scenario Result
              </h2>

            </div>

            <p className="text-xs text-slate-500 mt-1">
              Scenario estimate based on the selected assumptions.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">

              <div className="rounded-xl bg-slate-50 border border-slate-200 p-5">

                <div className="text-xs uppercase font-bold tracking-wider text-slate-400">
                  Baseline Risk
                </div>

                <div className="text-3xl font-black text-slate-900 mt-1">
                  {Math.round(
                    result.baselineRisk ??
                      baselineRisk
                  )}
                </div>

              </div>

              <div className="rounded-xl bg-blue-50 border border-blue-200 p-5">

                <div className="text-xs uppercase font-bold tracking-wider text-blue-500">
                  Simulated Risk
                </div>

                <div className="text-3xl font-black text-blue-700 mt-1">
                  {Math.round(
                    result.simulatedRisk ??
                      result.risk_score ??
                      baselineRisk
                  )}
                </div>

              </div>

              <div className="rounded-xl bg-slate-50 border border-slate-200 p-5">

                <div className="text-xs uppercase font-bold tracking-wider text-slate-400">
                  Risk Delta
                </div>

                <div className="text-3xl font-black text-slate-900 mt-1">
                  {Number(
                    result.riskDelta ??
                      result.risk_delta ??
                      0
                  ) >= 0
                    ? '+'
                    : ''}
                  {Math.round(
                    result.riskDelta ??
                      result.risk_delta ??
                      0
                  )}
                </div>

              </div>

            </div>

          </div>

          <div className="bg-[#0b192c] text-white rounded-2xl p-7 shadow-md">

            <div className="flex items-start gap-3">

              <AlertTriangle className="w-5 h-5 text-blue-400 mt-0.5" />

              <div>

                <h3 className="font-bold text-lg">
                  Policy Interpretation
                </h3>

                <p className="text-sm text-slate-300 mt-2 leading-relaxed">
                  {result.recommendation ||
                    result.summary ||
                    'Review the simulated risk alongside relocation feasibility and local infrastructure capacity.'}
                </p>

              </div>

            </div>

          </div>

          <div className="text-[11px] text-slate-400 bg-slate-50 border border-slate-200 rounded-xl p-4">
            <strong>Important:</strong> What-If results are scenario estimates generated by AASHRAY from the selected assumptions. They are not official government forecasts or final relocation decisions.
          </div>

        </div>
      )}

    </div>
  );
}