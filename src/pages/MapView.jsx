import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getHabitations } from '../api';
import Map from '../components/Map';
import {
  Layers,
  RefreshCw,
  ArrowRight,
  ArrowLeft,
  Info
} from 'lucide-react';

export default function MapView() {
  const [habitations, setHabitations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedHabitation, setSelectedHabitation] =
    useState(null);

  const [showHabitations, setShowHabitations] =
    useState(true);

  const [showFlood, setShowFlood] =
    useState(false);

  const [showCyclone, setShowCyclone] =
    useState(false);

  const [showRainfall, setShowRainfall] =
    useState(false);

  const [showRisk, setShowRisk] =
    useState(false);

  const [showLandslide, setShowLandslide] =
    useState(false);

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
      console.error(
        'Failed to load map data:',
        err
      );
    } finally {
      setLoading(false);
    }
  };

  const handleMarkerClick = (habitation) => {
    setSelectedHabitation(habitation);
  };

  const isHazardAvailable = (value) => {
    return (
      value !== null &&
      value !== undefined &&
      Number.isFinite(Number(value))
    );
  };

  const formatHazard = (value) => {
    if (!isHazardAvailable(value)) {
      return 'Not available';
    }

    return `${(
      Number(value) * 100
    ).toFixed(1)}`;
  };

  const hasHazardData =
    selectedHabitation &&
    (
      isHazardAvailable(
        selectedHabitation.hazards?.coastal
      ) ||
      isHazardAvailable(
        selectedHabitation.hazards?.flood
      ) ||
      isHazardAvailable(
        selectedHabitation.hazards?.cyclone
      ) ||
      isHazardAvailable(
        selectedHabitation.hazards?.rainfall
      )
    );

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">

      {/* TOP NAVIGATION */}

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
          <RefreshCw
            className={`w-3.5 h-3.5 ${
              loading ? 'animate-spin' : ''
            }`}
          />

          <span>
            Reload Villages
          </span>
        </button>

      </div>

      {/* HEADER */}

      <div className="bg-white rounded-2xl border border-slate-200 p-8 shadow-xs">

        <div>

          <div className="flex items-center gap-2 mb-1">

            <span className="bg-blue-100 text-blue-800 text-[11px] font-mono font-bold px-2 py-0.5 rounded">
              Route: /map
            </span>

            <span className="text-slate-400 text-xs">
              •
            </span>

            <span className="text-slate-500 text-xs font-medium uppercase tracking-wider">
              Geospatial GIS Engine
            </span>

          </div>

          <h1 className="text-3xl font-black text-slate-900 tracking-tight flex items-center gap-2">

            <span>
              MapView
            </span>

            <span className="text-xs bg-emerald-100 text-[#22c55e] border border-emerald-300 font-extrabold px-2.5 py-0.5 rounded-full uppercase">
              MapLibre GL
            </span>

          </h1>

          <p className="text-slate-600 text-sm mt-1">
            Interactive multi-hazard GIS view using
            AASHRAY AI/ML risk data.
          </p>

        </div>

      </div>

      {/* LOADING */}

      {loading ? (

        <div className="bg-white rounded-2xl border border-slate-200 p-16 text-center text-slate-500 shadow-xs space-y-3">

          <div className="inline-block animate-spin w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full" />

          <p className="text-sm font-semibold">
            Loading AASHRAY AI/ML geospatial data...
          </p>

        </div>

      ) : (

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">

          {/* MAP */}

          <div className="lg:col-span-3 relative h-[600px] rounded-2xl overflow-hidden shadow-sm border border-slate-300 bg-slate-100">

            <Map
              habitations={habitations}
              onMarkerClick={handleMarkerClick}
              showHabitations={showHabitations}
              showFlood={showFlood}
              showCyclone={showCyclone}
              showRainfall={showRainfall}
              showRisk={showRisk}
              showLandslide={showLandslide}
            />

            {/* MAP LAYERS */}

            <div className="absolute top-3 right-3 z-10 bg-white/95 backdrop-blur-md p-3.5 rounded-xl shadow-lg border border-slate-200 text-xs w-56 space-y-2.5">

              <div className="flex items-center justify-between border-b border-slate-200 pb-1.5 font-bold text-slate-900">

                <span className="flex items-center gap-1.5">

                  <Layers className="w-3.5 h-3.5 text-blue-600" />

                  <span>
                    Map Layers
                  </span>

                </span>

              </div>

              {/* HABITATIONS */}

              <label className="flex items-center justify-between cursor-pointer group">

                <span className="flex items-center gap-2 text-slate-800 font-medium">

                  <input
                    type="checkbox"
                    checked={showHabitations}
                    onChange={(e) =>
                      setShowHabitations(
                        e.target.checked
                      )
                    }
                    className="rounded border-slate-300 h-3.5 w-3.5 cursor-pointer accent-blue-600"
                  />

                  <span>
                    Habitations
                  </span>

                </span>

                <span className="text-[10px] font-mono font-bold bg-blue-100 text-blue-800 px-1.5 py-0.2 rounded">
                  {habitations.length} pts
                </span>

              </label>

              {/* FLOOD */}

              <label className="flex items-center justify-between cursor-pointer">

                <span className="flex items-center gap-2 text-slate-800 font-medium">

                  <input
                    type="checkbox"
                    checked={showFlood}
                    onChange={(e) =>
                      setShowFlood(
                        e.target.checked
                      )
                    }
                    className="rounded border-slate-300 h-3.5 w-3.5 cursor-pointer accent-blue-600"
                  />

                  <span>
                    Flood Risk
                  </span>

                </span>

                <span className="text-[9px] uppercase font-bold bg-blue-100 text-blue-700 px-1.5 py-0.2 rounded">
                  AI/ML
                </span>

              </label>

              {/* CYCLONE */}

              <label className="flex items-center justify-between cursor-pointer">

                <span className="flex items-center gap-2 text-slate-800 font-medium">

                  <input
                    type="checkbox"
                    checked={showCyclone}
                    onChange={(e) =>
                      setShowCyclone(
                        e.target.checked
                      )
                    }
                    className="rounded border-slate-300 h-3.5 w-3.5 cursor-pointer accent-blue-600"
                  />

                  <span>
                    Cyclone Risk
                  </span>

                </span>

                <span className="text-[9px] uppercase font-bold bg-purple-100 text-purple-700 px-1.5 py-0.2 rounded">
                  AI/ML
                </span>

              </label>

              {/* RAINFALL */}

              <label className="flex items-center justify-between cursor-pointer">

                <span className="flex items-center gap-2 text-slate-800 font-medium">

                  <input
                    type="checkbox"
                    checked={showRainfall}
                    onChange={(e) =>
                      setShowRainfall(
                        e.target.checked
                      )
                    }
                    className="rounded border-slate-300 h-3.5 w-3.5 cursor-pointer accent-blue-600"
                  />

                  <span>
                    Rainfall Risk
                  </span>

                </span>

                <span className="text-[9px] uppercase font-bold bg-cyan-100 text-cyan-700 px-1.5 py-0.2 rounded">
                  IMD
                </span>

              </label>

              {/* MULTI HAZARD */}

              <label className="flex items-center justify-between cursor-pointer">

                <span className="flex items-center gap-2 text-slate-800 font-medium">

                  <input
                    type="checkbox"
                    checked={showRisk}
                    onChange={(e) =>
                      setShowRisk(
                        e.target.checked
                      )
                    }
                    className="rounded border-slate-300 h-3.5 w-3.5 cursor-pointer accent-blue-600"
                  />

                  <span>
                    Multi-Hazard Risk
                  </span>

                </span>

                <span className="text-[9px] uppercase font-bold bg-red-100 text-red-700 px-1.5 py-0.2 rounded">
                  AI
                </span>

              </label>

              {/* LANDSLIDE */}

              <label className="flex items-center justify-between text-slate-400">

                <span className="flex items-center gap-2">

                  <input
                    type="checkbox"
                    checked={showLandslide}
                    onChange={(e) =>
                      setShowLandslide(
                        e.target.checked
                      )
                    }
                    className="rounded border-slate-300 h-3.5 w-3.5 cursor-pointer accent-slate-500"
                  />

                  <span>
                    Landslide
                  </span>

                </span>

                <span className="text-[9px] uppercase font-bold bg-slate-100 text-slate-500 px-1.5 py-0.2 rounded">
                  Kerala
                </span>

              </label>

            </div>

            {/* LEGEND */}

            <div className="absolute bottom-6 left-3 z-10 bg-white/95 backdrop-blur-md p-3 rounded-xl shadow-lg border border-slate-200 text-xs w-52 space-y-2">

              <div className="font-bold text-slate-900 border-b border-slate-200 pb-1">
                Risk Legend
              </div>

              <div className="space-y-1.5">

                <div className="flex items-center justify-between">

                  <span className="flex items-center gap-2">

                    <span className="w-3.5 h-3.5 rounded-full bg-[#dc2626] border border-white shadow-xs" />

                    <span className="font-semibold">
                      Very High
                    </span>

                  </span>

                  <span>
                    ≥ 0.75
                  </span>

                </div>

                <div className="flex items-center justify-between">

                  <span className="flex items-center gap-2">

                    <span className="w-3.5 h-3.5 rounded-full bg-[#f97316] border border-white shadow-xs" />

                    <span className="font-semibold">
                      High
                    </span>

                  </span>

                  <span>
                    0.50–0.74
                  </span>

                </div>

                <div className="flex items-center justify-between">

                  <span className="flex items-center gap-2">

                    <span className="w-3.5 h-3.5 rounded-full bg-[#eab308] border border-white shadow-xs" />

                    <span className="font-semibold">
                      Moderate
                    </span>

                  </span>

                  <span>
                    0.25–0.49
                  </span>

                </div>

                <div className="flex items-center justify-between">

                  <span className="flex items-center gap-2">

                    <span className="w-3.5 h-3.5 rounded-full bg-[#22c55e] border border-white shadow-xs" />

                    <span className="font-semibold">
                      Low
                    </span>

                  </span>

                  <span>
                    &lt; 0.25
                  </span>

                </div>

              </div>

            </div>

          </div>

          {/* SIDEBAR */}

          <div className="bg-white rounded-2xl border border-slate-200 shadow-xs p-6 flex flex-col justify-between h-[600px] overflow-y-auto">

            {selectedHabitation ? (

              <div className="space-y-4">

                {/* SELECTED VILLAGE */}

                <div className="border-b border-slate-200 pb-3">

                  <div className="flex items-center justify-between">

                    <span className="text-[11px] font-bold text-blue-600 uppercase tracking-wider font-mono">
                      Selected Village
                    </span>

                    <span className="px-2.5 py-0.5 rounded-full text-[10px] font-extrabold bg-yellow-100 text-yellow-700 border border-yellow-200">
                      {selectedHabitation.priority}{' '}
                      Priority
                    </span>

                  </div>

                  <h3 className="text-base font-extrabold text-slate-900 mt-1">
                    {selectedHabitation.name}
                  </h3>

                  <p className="text-xs font-mono text-slate-500">
                    {selectedHabitation.id}
                  </p>

                </div>

                {/* BASIC INFORMATION */}

                <div className="space-y-2.5 text-xs">

                  <div className="flex justify-between py-1 border-b border-slate-100">

                    <span className="text-slate-500">
                      AASHRAY Risk Score:
                    </span>

                    <span className="font-bold text-red-600 text-sm">

                      {selectedHabitation.risk_score != null
                        ? `${Number(
                            selectedHabitation.risk_score
                          ).toFixed(1)} / 100`
                        : 'Not available'}

                    </span>

                  </div>

                  <div className="flex justify-between py-1 border-b border-slate-100">

                    <span className="text-slate-500">
                      Population:
                    </span>

                    <span className="font-bold text-slate-800">

                      {selectedHabitation.population ==
                      null
                        ? 'N/A'
                        : Number(
                            selectedHabitation.population
                          ).toLocaleString()}

                    </span>

                  </div>

                  <div className="flex justify-between py-1 border-b border-slate-100">

                    <span className="text-slate-500">
                      District:
                    </span>

                    <span className="font-semibold text-slate-700">
                      {selectedHabitation.district ||
                        'N/A'}
                    </span>

                  </div>

                  <div className="flex justify-between py-1 border-b border-slate-100">

                    <span className="text-slate-500">
                      Block:
                    </span>

                    <span className="font-semibold text-slate-700">
                      {selectedHabitation.block ||
                        'N/A'}
                    </span>

                  </div>

                </div>

                {/* HAZARDS */}

                <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">

                  <p className="font-semibold text-slate-800 flex items-center gap-1 mb-2">

                    <Info className="w-3.5 h-3.5 text-blue-600" />

                    Hazard Data Coverage

                  </p>

                  {hasHazardData ? (

                    <div className="space-y-1.5 text-[11px]">

                      <div className="flex justify-between">
                        <span>
                          Coastal
                        </span>

                        <strong>
                          {formatHazard(
                            selectedHabitation
                              .hazards
                              ?.coastal
                          )}
                        </strong>
                      </div>

                      <div className="flex justify-between">
                        <span>
                          Flood
                        </span>

                        <strong>
                          {formatHazard(
                            selectedHabitation
                              .hazards
                              ?.flood
                          )}
                        </strong>
                      </div>

                      <div className="flex justify-between">
                        <span>
                          Cyclone
                        </span>

                        <strong>
                          {formatHazard(
                            selectedHabitation
                              .hazards
                              ?.cyclone
                          )}
                        </strong>
                      </div>

                      <div className="flex justify-between">
                        <span>
                          Rainfall
                        </span>

                        <strong>
                          {formatHazard(
                            selectedHabitation
                              .hazards
                              ?.rainfall
                          )}
                        </strong>
                      </div>

                    </div>

                  ) : (

                    <div className="text-[11px] text-slate-500 leading-relaxed">

                      <p>
                        Village-level hazard layers
                        are not currently available
                        for this location.
                      </p>

                      <p className="mt-1 font-medium text-slate-600">
                        The displayed AASHRAY risk
                        score and priority are based
                        on the available vulnerability
                        and exposure data.
                      </p>

                    </div>

                  )}

                </div>

                {/* DATA SOURCE NOTE */}

                {selectedHabitation.state && (

                  <div className="text-[10px] text-slate-400 leading-relaxed">

                    <strong>
                      Data region:
                    </strong>{' '}

                    {selectedHabitation.state}

                    {selectedHabitation.state ===
                      'Odisha'
                      ? ' — multi-hazard layers available.'
                      : ' — vulnerability/exposure model available.'}

                  </div>

                )}

                {/* ACTIONS */}

                <div className="pt-2 space-y-2">

                  <Link
                    to={`/habitation/${selectedHabitation.id}`}
                    className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-bold shadow-xs transition"
                  >
                    <span>
                      View Village Profile
                    </span>

                    <ArrowRight className="w-3.5 h-3.5" />
                  </Link>

                  <Link
                    to={`/habitation/${selectedHabitation.id}/relocation`}
                    className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold transition"
                  >
                    <span>
                      Inspect Relocation Sites
                    </span>
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