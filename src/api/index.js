import habitationsData from '../mocks/habitations.json';
import habitationDetailsData from '../mocks/habitation_details.json';
import sitesByHabitationData from '../mocks/sites_by_habitation.json';
import initialDecisions from '../mocks/decisions.json';
import recRecommended from '../mocks/recommendation_recommended.json';
import recMultiSite from '../mocks/recommendation_multisite.json';
import recNoSafeSite from '../mocks/recommendation_no_safe_site.json';

// ============================================================
// AASHRAY AI/ML API
// ============================================================

const AI_API_URL = 'https://aashray-sih26191.onrender.com';

const delay = (ms = 300) =>
  new Promise((resolve) => setTimeout(resolve, ms));

// ============================================================
// DEMO DECISION STORAGE
// ============================================================

const decisionsStore = [...initialDecisions];

// ============================================================
// FETCH REAL AASHRAY VILLAGES
// ============================================================

export async function getHabitations() {
  try {
    const response = await fetch(`${AI_API_URL}/api/villages`);

    if (!response.ok) {
      throw new Error('Failed to fetch villages from AASHRAY AI API');
    }

    const data = await response.json();

    return data.villages || [];
  } catch (error) {
    console.error('AASHRAY AI API error:', error);

    // Keep existing demo working if API is unavailable
    await delay(300);
    return habitationsData;
  }
}

// ============================================================
// FETCH REAL VILLAGE DETAILS
// ============================================================

export async function getHabitationDetail(id) {
  if (!id) return null;

  try {
    const response = await fetch(
      `${AI_API_URL}/api/village/${encodeURIComponent(id)}`
    );

    if (!response.ok) {
      throw new Error('Village not found in AASHRAY AI API');
    }

    const data = await response.json();

    return {
      id: data.id,
      name: data.name,
      vlcode: data.vlcode,

      block: data.block,
      district: data.district,

      priority: data.overall?.priority || 'P4',

      risk_score: data.overall?.score ?? null,
      risk_category: data.overall?.category || 'NO DATA',

      population: data.population,

      centroid: data.centroid,

      hazards: {
        coastal: data.hazards?.coastal ?? null,
        flood: data.hazards?.flood ?? null,
        cyclone: data.hazards?.cyclone ?? null,
        rainfall: data.hazards?.rainfall ?? null,
      },

      hazards_available: data.hazards_available || [],

      hazard_contribution: data.hazard_contribution || '',

      data_note: data.data_note || '',
    };
  } catch (error) {
    console.error('AASHRAY village API error:', error);

    // Fallback to existing mock data
    await delay(300);

    return habitationDetailsData[id] || null;
  }
}

// ============================================================
// RELOCATION SITES
// ============================================================
// Still using existing demo data.
// Real relocation optimization can be connected later.

export async function getSites(id) {
  await delay(300);

  if (!id || !habitationDetailsData[id]) {
    return [];
  }

  return sitesByHabitationData[id] || [];
}

// ============================================================
// RELOCATION RECOMMENDATION
// ============================================================
// Still using existing demo logic.
// We will connect this to the backend later.

export async function getRecommendation(id, state = null) {
  await delay(300);

  if (!id || !habitationDetailsData[id]) {
    return null;
  }

  // Manual demo states
  if (state === 'multi_site' || state === 'multisite') {
    return recMultiSite;
  }

  if (state === 'no_safe_site' || state === 'nosafe') {
    return recNoSafeSite;
  }

  if (state === 'recommended') {
    return getCustomizedRecommended(id);
  }

  // Existing demo behavior
  const detail = habitationDetailsData[id];

  if (id === 'KL-WYD-000123') {
    return recNoSafeSite;
  }

  if (id === 'KL-WYD-000124' || detail?.priority === 'P1') {
    return recMultiSite;
  }

  return getCustomizedRecommended(id);
}

function getCustomizedRecommended(id) {
  const sites =
    sitesByHabitationData[id] ||
    sitesByHabitationData['KL-WYD-000123'];

  const primarySite =
    sites?.[0] || recRecommended.site;

  const altSites =
    sites?.slice(1) || recRecommended.alternatives;

  return {
    status: 'recommended',
    site: primarySite,
    alternatives: altSites,
  };
}

// ============================================================
// WHAT-IF
// ============================================================
// Existing demo simulation.
// Real AI scenario simulation can be connected later.

export async function runWhatIf(
  habitationId,
  overrides = {}
) {
  await delay(300);

  const baseDetail =
    habitationDetailsData[habitationId];

  if (!baseDetail) return null;

  const baseRisk =
    baseDetail?.risk_score ?? 70;

  const basePopulation =
    baseDetail?.population ?? 3200;

  const basePriority =
    baseDetail?.priority ?? 'P2';

  const baseRecommendation =
    baseRisk >= 90
      ? 'no_safe_site'
      : baseRisk >= 80
        ? 'multi_site'
        : 'recommended';

  let delta = 0;

  // Rainfall
  if (overrides.rainfall_level === 'extreme') {
    delta += 15;
  } else if (
    overrides.rainfall_level === 'moderate'
  ) {
    delta += 5;
  }

  // Population
  const targetPopulation =
    overrides.population ?? basePopulation;

  if (targetPopulation > basePopulation) {
    const extraPop =
      targetPopulation - basePopulation;

    delta += Math.min(
      20,
      Math.round(extraPop / 200)
    );
  }

  // Water capacity
  if (
    overrides.water_capacity &&
    overrides.water_capacity < targetPopulation
  ) {
    delta += 6;
  }

  // Relocation radius
  if (
    overrides.relocation_radius_km &&
    overrides.relocation_radius_km < 10
  ) {
    delta += 4;
  }

  const simulatedRisk =
    Math.min(
      100,
      Math.max(0, baseRisk + delta)
    );

  let simulatedPriority = 'P4';

  if (simulatedRisk >= 80) {
    simulatedPriority = 'P1';
  } else if (simulatedRisk >= 60) {
    simulatedPriority = 'P2';
  } else if (simulatedRisk >= 40) {
    simulatedPriority = 'P3';
  }

  let simulatedRecommendation =
    'recommended';

  if (
    simulatedRisk >= 95 ||
    targetPopulation >= 5800
  ) {
    simulatedRecommendation =
      'no_safe_site';
  } else if (
    simulatedRisk >= 80 ||
    targetPopulation >= 3500
  ) {
    simulatedRecommendation =
      'multi_site';
  }

  return {
    before: {
      risk_score: baseRisk,
      priority: basePriority,
      population: basePopulation,
      recommendation_status:
        baseRecommendation,
    },

    after: {
      risk_score: simulatedRisk,
      priority: simulatedPriority,
      population: targetPopulation,
      recommendation_status:
        simulatedRecommendation,

      delta:
        simulatedRisk - baseRisk,

      overrides: {
        rainfall_level:
          overrides.rainfall_level ||
          'moderate',

        population:
          targetPopulation,

        water_capacity:
          overrides.water_capacity ||
          null,

        relocation_radius_km:
          overrides.relocation_radius_km ||
          20,
      },
    },
  };
}

// ============================================================
// APPROVE / REJECT DECISION
// ============================================================

export async function submitDecision(
  habitationId,
  {
    action,
    justification = '',
  }
) {
  await delay(300);

  const newDecision = {
    id: `DEC-${Date.now()}`,

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
      new Date().toISOString(),
  };

  const existingIdx =
    decisionsStore.findIndex(
      (d) =>
        d.habitation_id === habitationId
    );

  if (existingIdx >= 0) {
    decisionsStore[existingIdx] =
      newDecision;
  } else {
    decisionsStore.push(newDecision);
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

  if (!habitationId) return null;

  const decision =
    decisionsStore.find(
      (d) =>
        d.habitation_id === habitationId
    );

  return decision || null;
}