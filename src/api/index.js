import habitationsData from '../mocks/habitations.json';
import habitationDetailsData from '../mocks/habitation_details.json';
import sitesByHabitationData from '../mocks/sites_by_habitation.json';
import initialDecisions from '../mocks/decisions.json';
import recRecommended from '../mocks/recommendation_recommended.json';
import recMultiSite from '../mocks/recommendation_multisite.json';
import recNoSafeSite from '../mocks/recommendation_no_safe_site.json';

const AI_API_URL = 'https://aashray-sih26191.onrender.com';

const delay = (ms = 300) =>
  new Promise((resolve) => setTimeout(resolve, ms));

const decisionsStore = [...initialDecisions];

// ============================================================
// REAL API DATA NORMALIZATION
// ============================================================

function getRiskScore(village) {
  const score =
    village?.overall?.score ??
    village?.risk_score ??
    village?.aashray_risk_score ??
    (
      village?.multi_hazard_score != null
        ? Number(village.multi_hazard_score) * 100
        : null
    );

  if (score == null) {
    return null;
  }

  const numericScore = Number(score);

  return Number.isFinite(numericScore)
    ? numericScore
    : null;
}

function getPriority(village, riskScore) {
  if (village?.priority) {
    return village.priority;
  }

  if (riskScore == null) {
    return 'P4';
  }

  if (riskScore >= 75) return 'P1';
  if (riskScore >= 50) return 'P2';
  if (riskScore >= 25) return 'P3';

  return 'P4';
}

function getRiskCategory(village, riskScore) {
  const category =
    village?.overall?.category ??
    village?.risk_category ??
    village?.multi_hazard_category;

  if (category) {
    return category;
  }

  if (riskScore == null) {
    return 'NO DATA';
  }

  if (riskScore >= 75) return 'VERY HIGH';
  if (riskScore >= 50) return 'HIGH';
  if (riskScore >= 25) return 'MODERATE';

  return 'LOW';
}

function getCentroid(village) {
  const lat = Number(
    village?.centroid?.lat ??
    village?.centroid?.latitude ??
    village?.latitude
  );

  const lon = Number(
    village?.centroid?.lon ??
    village?.centroid?.lng ??
    village?.centroid?.longitude ??
    village?.longitude
  );

  if (
    Number.isFinite(lat) &&
    Number.isFinite(lon)
  ) {
    return {
      lat,
      lon,
      lng: lon
    };
  }

  return null;
}

function getHazardValue(value) {
  if (
    value === null ||
    value === undefined ||
    value === ''
  ) {
    return null;
  }

  const numericValue = Number(value);

  return Number.isFinite(numericValue)
    ? numericValue
    : null;
}

function getHazards(village) {
  const hazards = village?.hazards || {};

  return {
    coastal: getHazardValue(
      hazards.coastal ??
      village?.coastal_hazard_score
    ),

    flood: getHazardValue(
      hazards.flood ??
      village?.flood_hazard_score
    ),

    cyclone: getHazardValue(
      hazards.cyclone ??
      village?.cyclone_hazard_score
    ),

    rainfall: getHazardValue(
      hazards.rainfall ??
      village?.rainfall_hazard_score
    )
  };
}

function getHazardsAvailable(village) {
  if (Array.isArray(village?.hazards_available)) {
    return village.hazards_available;
  }

  if (
    typeof village?.hazards_available ===
    'string'
  ) {
    return village.hazards_available
      .split(',')
      .map((x) => x.trim())
      .filter(Boolean);
  }

  return [];
}

function normalizeVillage(village) {
  const riskScore =
    getRiskScore(village);

  return {
    id:
      village?.id ??
      village?.vlcode ??
      village?.village,

    name:
      village?.name ??
      village?.village ??
      'Unknown Village',

    vlcode:
      village?.vlcode ??
      null,

    state:
      village?.state ??
      null,

    district:
      village?.district ??
      null,

    block:
      village?.block ??
      null,

    priority:
      getPriority(
        village,
        riskScore
      ),

    risk_score:
      riskScore,

    risk_category:
      getRiskCategory(
        village,
        riskScore
      ),

    population:
      village?.population ??
      village?.total_population_village ??
      0,

    households:
      village?.total_households ??
      0,

    area:
      village?.total_geographical_area ??
      0,

    centroid:
      getCentroid(village),

    hazards:
      getHazards(village),

    hazards_available:
      getHazardsAvailable(village),

    hazard_contribution:
      village?.hazard_contribution ??
      '',

    forest_area:
      village?.forest_area ??
      null,

    net_area_sown:
      village?.net_area_sown ??
      null,

    nearest_town_distance:
      village?.nearest_town_distance_from_village ??
      null,

    risk_model:
      village?.risk_model ??
      null,

    risk_model_note:
      village?.risk_model_note ??
      null,

    raw_data:
      village
  };
}

// ============================================================
// FETCH REAL VILLAGES
// ============================================================

export async function getHabitations() {
  try {
    const response = await fetch(
      `${AI_API_URL}/api/villages`
    );

    if (!response.ok) {
      throw new Error(
        'Failed to fetch AASHRAY villages'
      );
    }

    const data =
      await response.json();

    const villages =
      Array.isArray(data?.villages)
        ? data.villages
        : [];

    return villages.map(
      normalizeVillage
    );
  } catch (error) {
    console.error(
      'AASHRAY API error:',
      error
    );

    await delay(300);

    return habitationsData;
  }
}

// ============================================================
// FETCH VILLAGE DETAIL
// ============================================================

export async function getHabitationDetail(id) {
  if (!id) {
    return null;
  }

  try {
    const response = await fetch(
      `${AI_API_URL}/api/village/${encodeURIComponent(id)}`
    );

    if (!response.ok) {
      throw new Error(
        'Village not found'
      );
    }

    const data =
      await response.json();

    const village =
      data?.data ??
      data?.village ??
      data;

    const normalized =
      normalizeVillage(village);

    return {
      ...normalized,

      id:
        data?.id ??
        normalized.id,

      name:
        data?.name ??
        normalized.name,

      vlcode:
        data?.vlcode ??
        normalized.vlcode,

      priority:
        data?.overall?.priority ??
        normalized.priority,

      risk_score:
        data?.overall?.score ??
        normalized.risk_score,

      risk_category:
        data?.overall?.category ??
        normalized.risk_category,

      population:
        data?.population ??
        normalized.population,

      centroid:
        data?.centroid ??
        normalized.centroid,

      hazards:
        data?.hazards ??
        normalized.hazards,

      hazards_available:
        data?.hazards_available ??
        normalized.hazards_available,

      hazard_contribution:
        data?.hazard_contribution ??
        normalized.hazard_contribution,

      data_note:
        data?.data_note ??
        normalized.risk_model_note ??
        '',

      raw_data:
        data
    };
  } catch (error) {
    console.error(
      'Village detail API error:',
      error
    );

    await delay(300);

    return (
      habitationDetailsData[id] ||
      null
    );
  }
}

// ============================================================
// RELOCATION SITES
// ============================================================

export async function getSites(id) {
  await delay(300);

  if (!id) {
    return [];
  }

  return (
    sitesByHabitationData[id] ||
    []
  );
}

// ============================================================
// RECOMMENDATION
// ============================================================

export async function getRecommendation(
  id,
  state = null
) {
  await delay(300);

  if (!id) {
    return null;
  }

  if (
    state === 'multi_site' ||
    state === 'multisite'
  ) {
    return recMultiSite;
  }

  if (
    state === 'no_safe_site' ||
    state === 'nosafe'
  ) {
    return recNoSafeSite;
  }

  if (state === 'recommended') {
    return getCustomizedRecommended(id);
  }

  const detail =
    habitationDetailsData[id];

  if (id === 'KL-WYD-000123') {
    return recNoSafeSite;
  }

  if (
    id === 'KL-WYD-000124' ||
    detail?.priority === 'P1'
  ) {
    return recMultiSite;
  }

  return getCustomizedRecommended(id);
}

function getCustomizedRecommended(id) {
  const sites =
    sitesByHabitationData[id] ||
    sitesByHabitationData[
      'KL-WYD-000123'
    ];

  return {
    status: 'recommended',

    site:
      sites?.[0] ||
      recRecommended.site,

    alternatives:
      sites?.slice(1) ||
      recRecommended.alternatives
  };
}

// ============================================================
// WHAT-IF SCENARIO ENGINE
// ============================================================
//
// Uses the REAL AASHRAY village risk score and population.
// Scenario adjustments are transparent stress-test assumptions,
// not official forecasts.
// ============================================================

export async function runWhatIf(
  habitationId,
  overrides = {}
) {
  try {
    // ----------------------------------------------------------
    // Load REAL village data from Render API
    // ----------------------------------------------------------
    const baseDetail =
      await getHabitationDetail(habitationId);

    if (!baseDetail) {
      return null;
    }

    const baseRisk = Math.max(
      0,
      Math.min(
        100,
        Number(baseDetail.risk_score) || 0
      )
    );

    const basePopulation = Math.max(
      0,
      Number(baseDetail.population) || 0
    );

    const basePriority =
      baseDetail.priority ||
      getPriority(
        baseDetail,
        baseRisk
      );

    // ----------------------------------------------------------
    // Scenario parameters
    // ----------------------------------------------------------

    const rainfallLevel =
      overrides.rainfall_level ||
      'moderate';

    const targetPopulation =
      Math.max(
        0,
        Number(
          overrides.population ??
          basePopulation
        )
      );

    const waterCapacity =
      overrides.water_capacity !== null &&
      overrides.water_capacity !== undefined &&
      overrides.water_capacity !== ''
        ? Math.max(
            0,
            Number(
              overrides.water_capacity
            )
          )
        : null;

    const relocationRadius =
      Math.max(
        5,
        Number(
          overrides.relocation_radius_km ??
          20
        )
      );

    // ----------------------------------------------------------
    // Calculate scenario stress
    // ----------------------------------------------------------

    let riskMultiplier = 1;

    // Rainfall stress
    if (rainfallLevel === 'moderate') {
      riskMultiplier += 0.05;
    } else if (rainfallLevel === 'extreme') {
      riskMultiplier += 0.15;
    }

    // Population stress
    if (basePopulation > 0) {
      const populationIncrease =
        Math.max(
          0,
          (
            targetPopulation -
            basePopulation
          ) /
            basePopulation
        );

      riskMultiplier += Math.min(
        0.20,
        populationIncrease * 0.20
      );
    }

    // Water-capacity stress
    let waterStress = 0;

    if (
      waterCapacity !== null &&
      targetPopulation >
        waterCapacity
    ) {
      waterStress =
        Math.min(
          0.10,
          (
            (
              targetPopulation -
              waterCapacity
            ) /
              Math.max(
                targetPopulation,
                1
              )
          ) *
            0.10
        );

      riskMultiplier += waterStress;
    }

    // Relocation-radius stress
    if (relocationRadius < 10) {
      riskMultiplier += 0.04;
    } else if (relocationRadius < 20) {
      riskMultiplier += 0.02;
    }

    // ----------------------------------------------------------
    // Calculate simulated risk
    // ----------------------------------------------------------

    const simulatedRisk =
      Math.round(
        Math.max(
          0,
          Math.min(
            100,
            baseRisk *
              riskMultiplier
          )
        )
      );

    const delta =
      simulatedRisk -
      Math.round(baseRisk);

    // ----------------------------------------------------------
    // Calculate simulated priority
    // ----------------------------------------------------------

    let simulatedPriority = 'P4';

    if (simulatedRisk >= 75) {
      simulatedPriority = 'P1';
    } else if (simulatedRisk >= 50) {
      simulatedPriority = 'P2';
    } else if (simulatedRisk >= 25) {
      simulatedPriority = 'P3';
    }

    // ----------------------------------------------------------
    // Calculate relocation recommendation
    // ----------------------------------------------------------

    let simulatedRecommendation =
      'recommended';

    if (
      simulatedRisk >= 80 ||
      (
        waterCapacity !== null &&
        targetPopulation >
          waterCapacity * 1.5
      )
    ) {
      simulatedRecommendation =
        'no_safe_site';
    } else if (
      simulatedRisk >= 60 ||
      relocationRadius < 10 ||
      (
        waterCapacity !== null &&
        targetPopulation >
          waterCapacity
      )
    ) {
      simulatedRecommendation =
        'multi_site';
    }

    // ----------------------------------------------------------
    // Baseline recommendation
    // ----------------------------------------------------------

    let baseRecommendation =
      'recommended';

    if (baseRisk >= 80) {
      baseRecommendation =
        'no_safe_site';
    } else if (baseRisk >= 60) {
      baseRecommendation =
        'multi_site';
    }

    // ----------------------------------------------------------
    // Return exact structure expected by WhatIf.jsx
    // ----------------------------------------------------------

    return {
      before: {
        risk_score:
          Math.round(baseRisk),

        priority:
          basePriority,

        population:
          basePopulation,

        recommendation_status:
          baseRecommendation
      },

      after: {
        risk_score:
          simulatedRisk,

        priority:
          simulatedPriority,

        population:
          targetPopulation,

        recommendation_status:
          simulatedRecommendation,

        delta,

        overrides: {
          rainfall_level:
            rainfallLevel,

          population:
            targetPopulation,

          water_capacity:
            waterCapacity,

          relocation_radius_km:
            relocationRadius
        },

        scenario_method: {
          baseline_source:
            'AASHRAY live village risk score',

          rainfall_adjustment:
            rainfallLevel === 'extreme'
              ? '+15% stress'
              : rainfallLevel === 'moderate'
                ? '+5% stress'
                : '0% stress',

          population_adjustment:
            basePopulation > 0
              ? 'Up to +20% based on population increase'
              : 'Not applied: baseline population unavailable',

          water_capacity_adjustment:
            waterStress > 0
              ? 'Applied because demand exceeds capacity'
              : 'Not applied',

          relocation_adjustment:
            relocationRadius < 10
              ? '+4% stress'
              : relocationRadius < 20
                ? '+2% stress'
                : '0% stress',

          note:
            'Scenario estimate for decision support; not an official forecast.'
        }
      }
    };
  } catch (error) {
    console.error(
      'What-If simulation failed:',
      error
    );

    return null;
  }
}

// ============================================================
// DECISION
// ============================================================

export async function submitDecision(
  habitationId,
  {
    action,
    justification = ''
  }
) {
  await delay(300);

  const newDecision = {
    id:
      `DEC-${Date.now()}`,

    habitation_id:
      habitationId,

    action:
      action.toLowerCase(),

    justification:
      justification.trim() ||
      'None provided',

    officer_id:
      'OFFICER-001',

    timestamp:
      new Date().toISOString()
  };

  const existingIdx =
    decisionsStore.findIndex(
      (d) =>
        d.habitation_id ===
        habitationId
    );

  if (existingIdx >= 0) {
    decisionsStore[
      existingIdx
    ] = newDecision;
  } else {
    decisionsStore.push(
      newDecision
    );
  }

  return newDecision;
}

// ============================================================
// GET DECISION
// ============================================================

export async function getDecision(
  habitationId
) {
  await delay(150);

  if (!habitationId) {
    return null;
  }

  return (
    decisionsStore.find(
      (d) =>
        d.habitation_id ===
        habitationId
    ) || null
  );
}