import React, {
  useEffect,
  useMemo,
  useState
} from 'react';

import {
  useParams,
  Link
} from 'react-router-dom';

import {
  getHabitations,
  getHabitationDetail
} from '../api';

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
  ArrowRight,
  ShieldCheck,
  ShieldAlert,
  Navigation,
  Target,
  Info,
  Search,
  CircleDot
} from 'lucide-react';

// ============================================================
// AASHRAY LIVE RELOCATION ENGINE
// ============================================================
//
// Candidate villages are selected from the LIVE 1508-village
// AASHRAY dataset.
//
// This page does NOT use the old mock relocation site list.
//
// Ranking factors:
//   1. Lower AASHRAY risk
//   2. Geographic proximity
//   3. Population/planning capacity proxy
//   4. Different village from source habitation
//
// IMPORTANT:
// The current public dataset does not contain an official
// government-certified "relocation capacity" field.
//
// Therefore the displayed capacity is explicitly labelled as
// a planning proxy derived from available village population
// data. It is NOT an approved carrying-capacity figure.
// ============================================================

// ------------------------------------------------------------
// Haversine distance
// ------------------------------------------------------------

function haversineDistance(
  lat1,
  lon1,
  lat2,
  lon2
) {
  const toRadians =
    (value) =>
      (value * Math.PI) / 180;

  const earthRadiusKm =
    6371;

  const dLat =
    toRadians(lat2 - lat1);

  const dLon =
    toRadians(lon2 - lon1);

  const a =
    Math.sin(dLat / 2) *
      Math.sin(dLat / 2) +
    Math.cos(
      toRadians(lat1)
    ) *
      Math.cos(
        toRadians(lat2)
      ) *
      Math.sin(dLon / 2) *
      Math.sin(dLon / 2);

  const c =
    2 *
    Math.atan2(
      Math.sqrt(a),
      Math.sqrt(1 - a)
    );

  return earthRadiusKm * c;
}

// ------------------------------------------------------------
// Safe numeric helper
// ------------------------------------------------------------

function numberOrZero(value) {
  const number =
    Number(value);

  return Number.isFinite(number)
    ? number
    : 0;
}

// ------------------------------------------------------------
// Risk helper
// ------------------------------------------------------------

function getVillageRisk(village) {
  const value =
    village?.risk_score ??
    village?.overall?.score ??
    village?.aashray_risk_score ??
    (
      village?.multi_hazard_score != null
        ? Number(
            village.multi_hazard_score
          ) * 100
        : null
    );

  const risk =
    Number(value);

  if (
    Number.isFinite(risk)
  ) {
    return Math.max(
      0,
      Math.min(
        100,
        risk
      )
    );
  }

  return 0;
}

// ------------------------------------------------------------
// Risk level
// ------------------------------------------------------------

function getRiskLevel(risk) {
  if (risk >= 75) {
    return 'high';
  }

  if (risk >= 50) {
    return 'medium';
  }

  return 'low';
}

// ------------------------------------------------------------
// Risk badge
// ------------------------------------------------------------

function getRiskBadge(level) {
  switch (
    String(level)
      .toLowerCase()
  ) {
    case 'high':
      return 'bg-red-100 text-[#dc2626] border-red-200';

    case 'medium':
      return 'bg-yellow-100 text-[#ca8a04] border-yellow-200';

    case 'low':
    default:
      return 'bg-emerald-100 text-[#22c55e] border-emerald-200';
  }
}

// ------------------------------------------------------------
// Capacity planning proxy
// ------------------------------------------------------------
//
// We do NOT claim that village population equals official
// carrying capacity.
//
// Instead, this gives the relocation engine a transparent
// planning proxy based on the available population field.
//
// A village with a larger population is treated as having
// greater existing settlement scale, but the UI clearly
// labels this as a planning proxy.
// ------------------------------------------------------------

function getPlanningCapacity(
  villagePopulation
) {
  const population =
    numberOrZero(
      villagePopulation
    );

  if (population <= 0) {
    return 0;
  }

  return Math.round(
    population * 1.25
  );
}

// ------------------------------------------------------------
// Suitability
// ------------------------------------------------------------

function getSuitability(
  risk,
  distance
) {
  if (
    risk < 40 &&
    distance <= 15
  ) {
    return 'high';
  }

  if (
    risk < 60 &&
    distance <= 30
  ) {
    return 'medium';
  }

  return 'low';
}

// ------------------------------------------------------------
// Safety
// ------------------------------------------------------------

function getSafety(
  risk
) {
  if (risk < 40) {
    return 'high';
  }

  if (risk < 60) {
    return 'medium';
  }

  return 'low';
}

// ------------------------------------------------------------
// Candidate score
// ------------------------------------------------------------

function calculateCandidateScore(
  risk,
  distance,
  population
) {
  // Lower risk = better
  const safetyScore =
    Math.max(
      0,
      100 - risk
    );

  // Closer = better
  const proximityScore =
    Math.max(
      0,
      100 -
        Math.min(
          distance,
          50
        ) *
          2
    );

  // Population is only used as a transparent
  // settlement-scale proxy.
  const populationScore =
    Math.min(
      100,
      Math.sqrt(
        Math.max(
          population,
          0
        )
      ) *
        2
    );

  return (
    safetyScore * 0.50 +
    proximityScore * 0.35 +
    populationScore * 0.15
  );
}

// ------------------------------------------------------------
// Candidate generator
// ------------------------------------------------------------

function buildCandidates(
  sourceVillage,
  villages
) {
  if (
    !sourceVillage ||
    !Array.isArray(villages)
  ) {
    return [];
  }

  const sourceId =
    sourceVillage.id ??
    sourceVillage.vlcode;

  const sourceCentroid =
    sourceVillage.centroid;

  if (
    !sourceCentroid ||
    !Number.isFinite(
      Number(sourceCentroid.lat)
    ) ||
    !Number.isFinite(
      Number(
        sourceCentroid.lon ??
        sourceCentroid.lng
      )
    )
  ) {
    return [];
  }

  const sourceLat =
    Number(
      sourceCentroid.lat
    );

  const sourceLon =
    Number(
      sourceCentroid.lon ??
      sourceCentroid.lng
    );

  const sourceRisk =
    getVillageRisk(
      sourceVillage
    );

  const candidates =
    villages
      .filter(
        (village) => {
          const villageId =
            village?.id ??
            village?.vlcode;

          return (
            villageId &&
            villageId !==
              sourceId
          );
        }
      )
      .map(
        (village) => {
          const centroid =
            village?.centroid;

          if (
            !centroid ||
            !Number.isFinite(
              Number(
                centroid.lat
              )
            ) ||
            !Number.isFinite(
              Number(
                centroid.lon ??
                centroid.lng
              )
            )
          ) {
            return null;
          }

          const lat =
            Number(
              centroid.lat
            );

          const lon =
            Number(
              centroid.lon ??
              centroid.lng
            );

          const distance =
            haversineDistance(
              sourceLat,
              sourceLon,
              lat,
              lon
            );

          const risk =
            getVillageRisk(
              village
            );

          const population =
            numberOrZero(
              village?.population
            );

          const capacity =
            getPlanningCapacity(
              population
            );

          const suitability =
            getSuitability(
              risk,
              distance
            );

          const safety =
            getSafety(
              risk
            );

          const score =
            calculateCandidateScore(
              risk,
              distance,
              population
            );

          return {
            id:
              village?.id ??
              village?.vlcode,

            name:
              village?.name ??
              village?.village ??
              'Unknown Village',

            state:
              village?.state ??
              '',

            district:
              village?.district ??
              '',

            block:
              village?.block ??
              '',

            rank: 0,

            risk_score:
              Math.round(risk),

            suitability,

            safety,

            capacity,

            required_capacity:
              numberOrZero(
                sourceVillage.population
              ),

            distance_km:
              Number(
                distance.toFixed(1)
              ),

            binding_sector:
              risk < 40
                ? 'risk safety'
                : distance > 30
                  ? 'proximity'
                  : 'multi-criteria',

            allocated_population:
              Math.min(
                capacity,
                numberOrZero(
                  sourceVillage.population
                )
              ),

            status:
              risk < 50
                ? 'recommended'
                : 'review',

            score:

              Number(
                score.toFixed(2)
              ),

            population,

            source_risk:
              Math.round(
                sourceRisk
              ),

            planning_capacity_proxy:
              true,

            raw_village:
              village
          };
        }
      )
      .filter(Boolean)
      .filter(
        (candidate) =>
          candidate.distance_km <=
          50
      )
      .filter(
        (candidate) =>
          candidate.risk_score <
          Math.max(
            sourceRisk,
            50
          )
      )
      .sort(
        (a, b) =>
          b.score -
          a.score
      )
      .slice(0, 12)
      .map(
        (
          candidate,
          index
        ) => ({
          ...candidate,
          rank:
            index + 1
        })
      );

  return candidates;
}

// ============================================================
// CAPACITY BAR
// ============================================================

function CapacityBar({
  required = 0,
  capacity = 0
}) {
  const safeRequired =
    numberOrZero(required);

  const safeCapacity =
    numberOrZero(capacity);

  const percentage =
    safeCapacity > 0
      ? Math.min(
          100,
          Math.round(
            (
              safeRequired /
              safeCapacity
            ) *
              100
          )
        )
      : 100;

  const isDeficit =
    safeRequired >
    safeCapacity;

  const isTight =
    !isDeficit &&
    safeRequired >=
      safeCapacity * 0.85;

  return (
    <div className="space-y-1.5">

      <div className="flex justify-between text-xs font-semibold">

        <span className="text-slate-600">
          Planning Capacity
        </span>

        <span
          className={
            isDeficit
              ? 'text-[#dc2626] font-bold'
              : isTight
                ? 'text-[#f97316] font-bold'
                : 'text-[#22c55e] font-bold'
          }
        >
          {safeRequired.toLocaleString()}
          {' / '}
          {safeCapacity.toLocaleString()}
          {' '}
          ({percentage}%)
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
          style={{
            width:
              `${Math.min(
                100,
                percentage
              )}%`
          }}
        />

      </div>

      <div className="flex justify-between text-[11px] text-slate-400">

        <span>
          Required:
          {' '}
          <strong className="text-slate-700">
            {safeRequired.toLocaleString()}
          </strong>
        </span>

        <span>
          Planning proxy:
          {' '}
          <strong className="text-slate-700">
            {safeCapacity.toLocaleString()}
          </strong>
        </span>

      </div>

    </div>
  );
}

// ============================================================
// MAIN COMPONENT
// ============================================================

export default function Relocation() {
  const { id } =
    useParams();

  const [
    villages,
    setVillages
  ] = useState([]);

  const [
    habitation,
    setHabitation
  ] = useState(null);

  const [
    sites,
    setSites
  ] = useState([]);

  const [
    loading,
    setLoading
  ] = useState(true);

  const [
    error,
    setError
  ] = useState(null);

  const [
    viewMode,
    setViewMode
  ] = useState('cards');

  // ==========================================================
  // LOAD LIVE DATA
  // ==========================================================

  useEffect(() => {
    let mounted = true;

    async function fetchData() {
      setLoading(true);
      setError(null);

      try {
        const [
          villageData,
          detailData
        ] =
          await Promise.all([
            getHabitations(),
            getHabitationDetail(id)
          ]);

        if (!mounted) {
          return;
        }

        const liveVillages =
          Array.isArray(
            villageData
          )
            ? villageData
            : [];

        setVillages(
          liveVillages
        );

        setHabitation(
          detailData
        );

        if (
          !detailData
        ) {
          setError(
            `Could not resolve live habitation ${id}.`
          );

          setSites([]);
          return;
        }

        // ------------------------------------------------------
        // Build candidates from LIVE villages
        // ------------------------------------------------------

        const candidates =
          buildCandidates(
            detailData,
            liveVillages
          );

        setSites(
          candidates
        );

        if (
          candidates.length === 0
        ) {
          setError(
            'No lower-risk relocation candidates with valid coordinates were found within 50 km.'
          );
        }

      } catch (err) {
        console.error(
          'Failed to load live relocation data:',
          err
        );

        if (
          mounted
        ) {
          setError(
            'Live relocation data could not be loaded.'
          );

          setSites([]);
        }

      } finally {
        if (
          mounted
        ) {
          setLoading(false);
        }
      }
    }

    fetchData();

    return () => {
      mounted = false;
    };
  }, [id]);

  // ==========================================================
  // SOURCE RISK
  // ==========================================================

  const sourceRisk =
    useMemo(
      () =>
        getVillageRisk(
          habitation
        ),
      [habitation]
    );

  // ==========================================================
  // SOURCE POPULATION
  // ==========================================================

  const sourcePopulation =
    useMemo(
      () =>
        numberOrZero(
          habitation?.population
        ),
      [habitation]
    );

  // ==========================================================
  // REFRESH
  // ==========================================================

  const refreshData =
    async () => {
      setLoading(true);
      setError(null);

      try {
        const [
          villageData,
          detailData
        ] =
          await Promise.all([
            getHabitations(),
            getHabitationDetail(id)
          ]);

        const liveVillages =
          Array.isArray(
            villageData
          )
            ? villageData
            : [];

        setVillages(
          liveVillages
        );

        setHabitation(
          detailData
        );

        const candidates =
          buildCandidates(
            detailData,
            liveVillages
          );

        setSites(
          candidates
        );

        if (
          candidates.length === 0
        ) {
          setError(
            'No lower-risk relocation candidates with valid coordinates were found within 50 km.'
          );
        }

      } catch (err) {
        console.error(
          'Relocation refresh failed:',
          err
        );

        setError(
          'Live relocation data could not be refreshed.'
        );

      } finally {
        setLoading(false);
      }
    };

  // ==========================================================
  // LOADING
  // ==========================================================

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">

        <div className="bg-white rounded-2xl border border-slate-200 p-8 shadow-xs animate-pulse space-y-4">

          <div className="h-6 bg-slate-200 rounded w-1/3"></div>

          <div className="h-10 bg-slate-100 rounded-xl"></div>

        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">

          {[1, 2, 3].map(
            (n) => (
              <div
                key={n}
                className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs animate-pulse space-y-4"
              >

                <div className="h-6 bg-slate-200 rounded w-1/3"></div>

                <div className="h-5 bg-slate-200 rounded w-3/4"></div>

                <div className="h-16 bg-slate-100 rounded-xl"></div>

                <div className="h-8 bg-slate-200 rounded"></div>

              </div>
            )
          )}

        </div>

      </div>
    );
  }

  // ==========================================================
  // HABITATION NOT FOUND
  // ==========================================================

  if (!habitation) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16 text-center">

        <div className="bg-white rounded-2xl border border-slate-200 p-12 shadow-xs space-y-4">

          <ShieldAlert className="w-12 h-12 text-slate-400 mx-auto" />

          <h2 className="text-xl font-black text-slate-800">
            Live Habitation Record Not Found
          </h2>

          <p className="text-sm text-slate-500">
            Could not resolve relocation data for ID:
          </p>

          <span className="inline-flex bg-slate-100 border border-slate-200 rounded-lg px-3 py-1 font-mono text-xs text-slate-700">
            {id}
          </span>

          <div>

            <Link
              to="/"
              className="inline-flex items-center gap-2 px-5 py-2.5 bg-blue-600 text-white rounded-xl text-xs font-bold shadow-xs"
            >
              <ArrowLeft className="w-4 h-4" />
              Back to Dashboard
            </Link>

          </div>

        </div>

      </div>
    );
  }

  // ==========================================================
  // MAIN
  // ==========================================================

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">

      {/* ======================================================
          TOP NAVIGATION
      ====================================================== */}

      <div className="flex items-center justify-between">

        <Link
          to={`/habitation/${encodeURIComponent(
            id
          )}`}
          className="inline-flex items-center gap-1.5 text-xs font-bold text-slate-600 hover:text-blue-600 bg-white px-3 py-1.5 rounded-lg border border-slate-200 shadow-xs transition"
        >

          <ArrowLeft className="w-4 h-4" />

          <span>
            Back to {habitation.name}
          </span>

        </Link>

        <button
          onClick={
            refreshData
          }
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-700 bg-white px-3 py-1.5 rounded-lg border border-slate-200 shadow-xs transition cursor-pointer"
        >

          <RefreshCw className="w-3.5 h-3.5" />

          <span>
            Refresh Live Sites
          </span>

        </button>

      </div>

      {/* ======================================================
          HEADER
      ====================================================== */}

      <div className="bg-white rounded-2xl border border-slate-200 p-8 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-6">

        <div>

          <div className="flex items-center gap-2 mb-1.5">

            <span className="font-mono text-xs font-bold bg-blue-50 text-blue-700 border border-blue-200 px-2.5 py-0.5 rounded-md">
              {id}
            </span>

            <span className="text-slate-300">
              •
            </span>

            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">
              Live Candidate Site Evaluation
            </span>

          </div>

          <h1 className="text-3xl font-black text-slate-900 tracking-tight">

            {habitation.name}

            {' — '}

            <span className="text-blue-600">
              Relocation Intelligence
            </span>

          </h1>

          <p className="text-slate-600 text-sm mt-1 max-w-3xl">

            Live AASHRAY villages are evaluated as potential
            relocation destinations using geographic proximity,
            current AASHRAY risk, and settlement-scale planning
            indicators.

          </p>

        </div>

        {/* VIEW TOGGLE */}

        <div className="flex items-center bg-slate-100 p-1 rounded-xl border border-slate-200 self-start md:self-auto">

          <button
            onClick={() =>
              setViewMode(
                'cards'
              )
            }
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition cursor-pointer ${
              viewMode === 'cards'
                ? 'bg-white text-slate-900 shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >

            <LayoutGrid className="w-3.5 h-3.5" />

            <span>
              Card View
            </span>

          </button>

          <button
            onClick={() =>
              setViewMode(
                'table'
              )
            }
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition cursor-pointer ${
              viewMode === 'table'
                ? 'bg-white text-slate-900 shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >

            <TableIcon className="w-3.5 h-3.5" />

            <span>
              Table View
            </span>

          </button>

        </div>

      </div>

      {/* ======================================================
          SOURCE VILLAGE SUMMARY
      ====================================================== */}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">

        {/* Population */}

        <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs">

          <div className="flex items-center gap-3">

            <div className="w-10 h-10 rounded-xl bg-blue-50 flex items-center justify-center">

              <Users className="w-5 h-5 text-blue-600" />

            </div>

            <div>

              <p className="text-[10px] uppercase tracking-wider font-bold text-slate-400">
                Exposed Population
              </p>

              <p className="text-xl font-black text-slate-900">
                {sourcePopulation.toLocaleString()}
              </p>

            </div>

          </div>

        </div>

        {/* Risk */}

        <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs">

          <div className="flex items-center gap-3">

            <div className="w-10 h-10 rounded-xl bg-red-50 flex items-center justify-center">

              <ShieldAlert className="w-5 h-5 text-red-600" />

            </div>

            <div>

              <p className="text-[10px] uppercase tracking-wider font-bold text-slate-400">
                AASHRAY Risk
              </p>

              <p className="text-xl font-black text-slate-900">
                {Math.round(
                  sourceRisk
                )}
              </p>

            </div>

          </div>

        </div>

        {/* Candidates */}

        <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs">

          <div className="flex items-center gap-3">

            <div className="w-10 h-10 rounded-xl bg-emerald-50 flex items-center justify-center">

              <Target className="w-5 h-5 text-emerald-600" />

            </div>

            <div>

              <p className="text-[10px] uppercase tracking-wider font-bold text-slate-400">
                Live Candidates
              </p>

              <p className="text-xl font-black text-slate-900">
                {sites.length}
              </p>

            </div>

          </div>

        </div>

      </div>

      {/* ======================================================
          TRANSPARENCY NOTICE
      ====================================================== */}

      <div className="bg-blue-50 border border-blue-200 rounded-2xl p-4 flex items-start gap-3">

        <Info className="w-5 h-5 text-blue-600 shrink-0 mt-0.5" />

        <div>

          <p className="text-sm font-bold text-blue-900">
            Live AASHRAY relocation screening
          </p>

          <p className="text-xs text-blue-800 mt-1 leading-relaxed">

            Candidate villages come from the live AASHRAY
            dataset. Distance is calculated from village
            centroids. Safety and suitability use the AASHRAY
            risk score. Capacity shown below is a transparent
            planning proxy derived from available settlement
            data and is not an official government-certified
            carrying-capacity determination.

          </p>

        </div>

      </div>

      {/* ======================================================
          ERROR / NO CANDIDATES
      ====================================================== */}

      {error && (
        <div className="bg-amber-50 border border-amber-200 rounded-2xl p-5 flex items-start gap-3">

          <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0" />

          <div>

            <h3 className="text-sm font-bold text-amber-900">
              Relocation screening notice
            </h3>

            <p className="text-xs text-amber-800 mt-1">
              {error}
            </p>

          </div>

        </div>
      )}

      {/* ======================================================
          CANDIDATES
      ====================================================== */}

      {sites.length > 0 ? (
        <>

          {/* ==================================================
              CARD VIEW
          ================================================== */}

          {viewMode === 'cards' && (

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">

              {sites.map(
                (site) => {

                  const isRank1 =
                    site.rank === 1;

                  const capacityDeficit =
                    site.required_capacity >
                    site.capacity;

                  return (

                    <div
                      key={
                        site.id
                      }
                      className={`bg-white rounded-2xl border p-6 shadow-xs flex flex-col justify-between transition relative overflow-hidden ${
                        isRank1
                          ? 'border-blue-500 ring-2 ring-blue-500/20 bg-blue-50/10'
                          : 'border-slate-200 hover:border-slate-300'
                      }`}
                    >

                      {/* TOP RANK */}

                      {isRank1 && (

                        <div className="absolute top-0 right-0 bg-blue-600 text-white text-[10px] uppercase font-black px-3 py-0.5 rounded-bl-lg tracking-wider">
                          Best Match
                        </div>

                      )}

                      <div className="space-y-4">

                        {/* HEADER */}

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

                          <div className="min-w-0">

                            <h3 className="font-extrabold text-slate-900 text-base leading-snug">
                              {site.name}
                            </h3>

                            <div className="flex items-center gap-2 mt-0.5 flex-wrap">

                              <span className="font-mono text-xs text-slate-400">
                                {site.id}
                              </span>

                              <span
                                className={`text-[10px] font-extrabold uppercase px-2 py-0.5 rounded-full border ${
                                  site.status ===
                                  'recommended'
                                    ? 'bg-emerald-100 text-[#22c55e] border-emerald-200'
                                    : 'bg-slate-100 text-slate-600 border-slate-200'
                                }`}
                              >
                                {site.status?.replace(
                                  /_/g,
                                  ' '
                                )}
                              </span>

                            </div>

                          </div>

                        </div>

                        {/* LOCATION */}

                        <div className="bg-slate-50 p-3 rounded-xl border border-slate-200">

                          <div className="flex items-start gap-2">

                            <MapPin className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />

                            <div>

                              <p className="text-xs font-bold text-slate-800">
                                {site.distance_km} km
                              </p>

                              <p className="text-[11px] text-slate-500 mt-0.5">

                                {[
                                  site.block,
                                  site.district,
                                  site.state
                                ]
                                  .filter(Boolean)
                                  .join(
                                    ', '
                                  )}

                              </p>

                            </div>

                          </div>

                        </div>

                        {/* SUITABILITY / SAFETY */}

                        <div className="grid grid-cols-2 gap-2 pt-1">

                          <div className="bg-slate-50 p-2.5 rounded-xl border border-slate-200 text-center">

                            <span className="text-[10px] uppercase font-bold text-slate-400 block">
                              Suitability
                            </span>

                            <span
                              className={`inline-block mt-1 px-2.5 py-0.5 rounded-full text-xs font-black border capitalize ${getRiskBadge(
                                site.suitability
                              )}`}
                            >
                              {site.suitability}
                            </span>

                          </div>

                          <div className="bg-slate-50 p-2.5 rounded-xl border border-slate-200 text-center">

                            <span className="text-[10px] uppercase font-bold text-slate-400 block">
                              Safety
                            </span>

                            <span
                              className={`inline-block mt-1 px-2.5 py-0.5 rounded-full text-xs font-black border capitalize ${getRiskBadge(
                                site.safety
                              )}`}
                            >
                              {site.safety}
                            </span>

                          </div>

                        </div>

                        {/* RISK */}

                        <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-200">

                          <div className="flex justify-between items-center">

                            <div>

                              <span className="text-[10px] uppercase font-bold text-slate-400 block">
                                AASHRAY Risk
                              </span>

                              <span className="text-2xl font-black text-slate-900">
                                {site.risk_score}
                              </span>

                            </div>

                            <ShieldCheck className="w-7 h-7 text-emerald-500" />

                          </div>

                        </div>

                        {/* CAPACITY */}

                        <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-200">

                          <CapacityBar
                            required={
                              site.required_capacity
                            }
                            capacity={
                              site.capacity
                            }
                          />

                        </div>

                        {/* BINDING FACTOR */}

                        <div className="flex items-center justify-between text-xs pt-1 border-t border-slate-100 gap-2">

                          <div className="flex items-center gap-1.5 text-slate-600">

                            <Navigation className="w-4 h-4 text-blue-600 shrink-0" />

                            <span className="font-bold text-slate-900">
                              {site.distance_km} km
                            </span>

                            <span className="text-slate-400">
                              away
                            </span>

                          </div>

                          <span className="bg-slate-100 text-slate-700 border border-slate-200 px-2.5 py-0.5 rounded-md font-mono text-[11px] text-right">

                            Score:
                            {' '}
                            <strong className="text-slate-900">
                              {site.score}
                            </strong>

                          </span>

                        </div>

                      </div>

                      {/* FOOTER */}

                      <div className="pt-4 mt-4 border-t border-slate-100 flex items-center justify-between text-xs">

                        <span className="text-slate-500 font-medium">
                          Planning allocation:
                        </span>

                        <span className="font-extrabold text-blue-700 font-mono text-sm">

                          {site.allocated_population?.toLocaleString()}
                          {' '}
                          pax

                        </span>

                      </div>

                    </div>
                  );
                }
              )}

            </div>

          )}

          {/* ==================================================
              TABLE VIEW
          ================================================== */}

          {viewMode === 'table' && (

            <div className="bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">

              <div className="overflow-x-auto">

                <table className="w-full text-left text-sm text-slate-700">

                  <thead className="bg-slate-100/80 text-[11px] uppercase font-bold text-slate-500 tracking-wider border-b border-slate-200">

                    <tr>

                      <th className="px-6 py-4">
                        Rank & Site
                      </th>

                      <th className="px-6 py-4">
                        Risk
                      </th>

                      <th className="px-6 py-4">
                        Suitability
                      </th>

                      <th className="px-6 py-4">
                        Safety
                      </th>

                      <th className="px-6 py-4">
                        Distance
                      </th>

                      <th className="px-6 py-4">
                        Planning Capacity
                      </th>

                      <th className="px-6 py-4 text-right">
                        Score
                      </th>

                    </tr>

                  </thead>

                  <tbody className="divide-y divide-slate-200">

                    {sites.map(
                      (site) => (

                        <tr
                          key={
                            site.id
                          }
                          className="hover:bg-slate-50/80 transition"
                        >

                          <td className="px-6 py-4">

                            <div className="flex items-center gap-2">

                              <span className="font-black text-slate-900 bg-slate-100 px-2 py-0.5 rounded text-xs">
                                #{site.rank}
                              </span>

                              <div>

                                <div className="font-bold text-slate-900">
                                  {site.name}
                                </div>

                                <span className="font-mono text-xs text-slate-400">
                                  {site.id}
                                </span>

                              </div>

                            </div>

                          </td>

                          <td className="px-6 py-4">

                            <span className="font-black text-slate-900">
                              {site.risk_score}
                            </span>

                          </td>

                          <td className="px-6 py-4">

                            <span
                              className={`px-2.5 py-0.5 rounded-full text-xs font-bold border capitalize ${getRiskBadge(
                                site.suitability
                              )}`}
                            >
                              {site.suitability}
                            </span>

                          </td>

                          <td className="px-6 py-4">

                            <span
                              className={`px-2.5 py-0.5 rounded-full text-xs font-bold border capitalize ${getRiskBadge(
                                site.safety
                              )}`}
                            >
                              {site.safety}
                            </span>

                          </td>

                          <td className="px-6 py-4 font-mono text-slate-700">

                            {site.distance_km}
                            {' '}
                            km

                          </td>

                          <td className="px-6 py-4">

                            <div className="font-bold text-slate-800">

                              {site.capacity?.toLocaleString()}

                            </div>

                            <div className="text-[10px] text-slate-400">
                              planning proxy
                            </div>

                          </td>

                          <td className="px-6 py-4 text-right font-mono font-bold text-blue-700">

                            {site.score}

                          </td>

                        </tr>

                      )
                    )}

                  </tbody>

                </table>

              </div>

            </div>

          )}

          {/* ==================================================
              OPTIMIZATION READY
          ================================================== */}

          <div className="bg-[#0b192c] text-white rounded-2xl p-6 sm:p-8 shadow-md flex flex-col sm:flex-row items-center justify-between gap-4">

            <div>

              <h3 className="text-lg font-bold">
                Relocation Screening Complete
              </h3>

              <p className="text-xs text-slate-300 mt-0.5">

                {sites.length}
                {' '}
                live candidate villages were identified
                from the AASHRAY dataset.

              </p>

            </div>

            <Link
              to={`/recommendation/${encodeURIComponent(
                id
              )}`}
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-sm font-bold shadow-xs transition cursor-pointer"
            >

              <Sparkles className="w-4 h-4" />

              <span>
                View Recommendation Engine
              </span>

              <ArrowRight className="w-4 h-4" />

            </Link>

          </div>

        </>

      ) : (

        /* ====================================================
           NO CANDIDATES
        ==================================================== */

        <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center text-slate-500 shadow-xs">

          <Search className="w-12 h-12 text-slate-400 mx-auto mb-3" />

          <h3 className="text-lg font-bold text-slate-800">
            No Live Candidate Sites Found
          </h3>

          <p className="text-sm text-slate-500 mt-1 max-w-xl mx-auto">

            The current AASHRAY dataset does not contain
            enough lower-risk villages with valid coordinates
            within the 50 km screening radius for this
            habitation.

          </p>

          <button
            onClick={
              refreshData
            }
            className="mt-5 inline-flex items-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-bold"
          >

            <RefreshCw className="w-4 h-4" />

            Refresh Live Data

          </button>

        </div>

      )}

    </div>
  );
}