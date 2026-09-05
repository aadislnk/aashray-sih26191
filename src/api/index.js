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
// FETCH ALL 1508 REAL VILLAGES
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

    const data = await response.json();

    return (data.villages || []).map((village) => {
      const hasRisk =
        village.risk_score !== null &&
        village.risk_score !== undefined;

      const isDataOnly =
        !hasRisk ||
        village.risk_category === 'DATA-ONLY' ||
        village.priority === 'PENDING';

      return {
        id: village.id,
        name: village.name,
        vlcode: village.vlcode,

        state: village.state,
        district: village.district,
        block: village.block,

        // Never convert missing hazard/risk data into P4.
        priority: isDataOnly
          ? 'DATA-ONLY'
          : village.priority,

        risk_score: hasRisk
          ? village.risk_score
          : null,

        risk_category: isDataOnly
          ? 'DATA-ONLY'
          : village.risk_category,

        population:
          village.population ?? null,

        centroid:
          village.centroid || {
            lat: null,
            lon: null,
          },

        hazards:
          village.hazards || {
            coastal: null,
            flood: null,
            cyclone: null,
            rainfall: null,
          },

        hazards_available:
          village.hazards_available || [],

        hazard_contribution:
          village.hazard_contribution || '',

        profiles:
          village.profiles || {},

        data_note:
          isDataOnly
            ? 'Hazard risk assessment is not yet available for this village.'
            : '',
      };
    });
  } catch (error) {
    console.error(
      'AASHRAY AI API error:',
      error
    );

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
      throw new Error(
        'Village not found in AASHRAY AI API'
      );
    }

    const data = await response.json();

    const hasRisk =
      data.overall?.score !== null &&
      data.overall?.score !== undefined;

    const isDataOnly =
      !hasRisk ||
      data.overall?.category === 'DATA-ONLY' ||
      data.overall?.priority === 'PENDING';

    return {
      id: data.id,
      name: data.name,
      vlcode: data.vlcode,

      state: data.state,
      block: data.block,
      district: data.district,

      priority: isDataOnly
        ? 'DATA-ONLY'
        : data.overall?.priority,

      risk_score: hasRisk
        ? data.overall?.score
        : null,

      risk_category: isDataOnly
        ? 'DATA-ONLY'
        : data.overall?.category,

      population:
        data.population ?? null,

      centroid:
        data.centroid || {
          lat: null,
          lon: null,
        },

      hazards: {
        coastal:
          data.hazards?.coastal ?? null,

        flood:
          data.hazards?.flood ?? null,

        cyclone:
          data.hazards?.cyclone ?? null,

        rainfall:
          data.hazards?.rainfall ?? null,
      },

      hazards_available:
        data.hazards_available || [],

      hazard_contribution:
        data.hazard_contribution || '',

      profiles:
        data.profiles || {},

      raw_data:
        data.raw_data || {},

      data_note:
        isDataOnly
          ? 'Hazard risk assessment is not yet available for this village.'
          : data.data_note || '',
    };
  } catch (error) {
    console.error(
      'AASHRAY village API error:',
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
// Existing demo data retained.

export async function getSites(id) {
  await delay(300);

  if (!id || !habitationDetailsData[id]) {
    return [];
  }

  return (
    sitesByHabitationData[id] || []
  );
}

// ============================================================
// RELOCATION RECOMMENDATION
// ============================================================
// Existing demo logic retained.

export async function getRecommendation(
  id,
  state = null
) {
  await delay(300);

  if (
    !id ||
    !habitationDetailsData[id]
  ) {
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

  const primarySite =
    sites?.[0] ||
    recRecommended.site;

  const altSites =
    sites?.slice(1) ||
    recRecommended.alternatives;

  return {
    status: 'recommended',
    site: primarySite,
    alternatives: altSites,
  };
}

// ============================================================
// WHAT-IF
// ============================================================
// Existing demo simulation retained.

export async function runWhatIf(
  habitationId,
  overrides = {}
) {
  await delay(300);

  const baseDetail =
    habitationDetailsData[
      habitationId
    ];

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

  if (
    overrides.rainfall_level ===
    'extreme'
  ) {
    delta += 15;
  } else if (
    overrides.rainfall_level ===
    'moderate'
  ) {
    delta += 5;
  }

  const targetPopulation =
    overrides.population ??
    basePopulation;

  if (
    targetPopulation >
    basePopulation
  ) {
    const extraPop =
      targetPopulation -
      basePopulation;

    delta += Math.min(
      20,
      Math.round(extraPop / 200)
    );
  }

  if (
    overrides.water_capacity &&
    overrides.water_capacity <
      targetPopulation
  ) {
    delta += 6;
  }

  if (
    overrides.relocation_radius_km &&
    overrides.relocation_radius_km <
      10
  ) {
    delta += 4;
  }

  const simulatedRisk =
    Math.min(
      100,
      Math.max(
        0,
        baseRisk + delta
      )
    );

  let simulatedPriority = 'P4';

  if (simulatedRisk >= 80) {
    simulatedPriority = 'P1';
  } else if (
    simulatedRisk >= 60
  ) {
    simulatedPriority = 'P2';
  } else if (
    simulatedRisk >= 40
  ) {
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

  if (!habitationId) return null;

  const decision =
    decisionsStore.find(
      (d) =>
        d.habitation_id ===
        habitationId
    );

  return decision || null;
}