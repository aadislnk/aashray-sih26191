import habitationsData from '../mocks/habitations.json';
import habitationDetailsData from '../mocks/habitation_details.json';
import sitesByHabitationData from '../mocks/sites_by_habitation.json';
import initialDecisions from '../mocks/decisions.json';
import recRecommended from '../mocks/recommendation_recommended.json';
import recMultiSite from '../mocks/recommendation_multisite.json';
import recNoSafeSite from '../mocks/recommendation_no_safe_site.json';

const delay = (ms = 300) => new Promise((resolve) => setTimeout(resolve, ms));

// In-memory module-level persistence for recorded decisions during the demo session
const decisionsStore = [...initialDecisions];

/**
 * Fetch list of all habitations
 */
export async function getHabitations() {
  await delay(300);
  return habitationsData;
}

/**
 * Fetch detailed information for a single habitation by ID
 */
export async function getHabitationDetail(id) {
  await delay(300);
  if (!id) return null;
  return habitationDetailsData[id] || null;
}

/**
 * Fetch candidate relocation sites for a specific habitation
 */
export async function getSites(id) {
  await delay(300);
  if (!id || !habitationDetailsData[id]) return null;
  return sitesByHabitationData[id] || [];
}

/**
 * Fetch relocation recommendation for a habitation
 * Automatically determines default state based on habitation risk priority if state is not provided
 */
export async function getRecommendation(id, state = null) {
  await delay(300);
  if (!id || !habitationDetailsData[id]) return null;

  // 1. Manual override state for demo switcher
  if (state === 'multi_site' || state === 'multisite') {
    return recMultiSite;
  }
  if (state === 'no_safe_site' || state === 'nosafe') {
    return recNoSafeSite;
  }
  if (state === 'recommended') {
    return getCustomizedRecommended(id);
  }

  // 2. Default state based on habitation ID / priority
  const detail = habitationDetailsData[id];
  if (id === 'KL-WYD-000123') {
    // Show high-criticality no-safe-site shortfall
    return recNoSafeSite;
  }
  if (id === 'KL-WYD-000124' || detail?.priority === 'P1') {
    // Show complex multi-site split allocation
    return recMultiSite;
  }

  // Default for P2, P3, P4 is single optimal recommended site
  return getCustomizedRecommended(id);
}

// Helper to inject actual site details into recommended response
function getCustomizedRecommended(id) {
  const sites = sitesByHabitationData[id] || sitesByHabitationData['KL-WYD-000123'];
  const primarySite = sites?.[0] || recRecommended.site;
  const altSites = sites?.slice(1) || recRecommended.alternatives;

  return {
    status: 'recommended',
    site: primarySite,
    alternatives: altSites
  };
}

/**
 * Run What-If scenario simulation on a habitation
 * 
 * NOTE: This is simplified mock scenario logic for demo purposes only. 
 * Real computation belongs to backend/AI in production.
 */
export async function runWhatIf(habitationId, overrides = {}) {
  await delay(300);
  const baseDetail = habitationDetailsData[habitationId];
  if (!baseDetail) return null;

  const baseRisk = baseDetail?.risk_score ?? 70;
  const basePopulation = baseDetail?.population ?? 3200;
  const basePriority = baseDetail?.priority ?? 'P2';

  // Determine initial baseline recommendation status
  const baseRecommendation = baseRisk >= 90 ? 'no_safe_site' : baseRisk >= 80 ? 'multi_site' : 'recommended';

  // Calculate simulated risk adjustments
  let delta = 0;

  // Rainfall surge modifier
  if (overrides.rainfall_level === 'extreme') {
    delta += 15;
  } else if (overrides.rainfall_level === 'moderate') {
    delta += 5;
  }

  // Population stress modifier (+1 point per 200 extra people)
  const targetPopulation = overrides.population ?? basePopulation;
  if (targetPopulation > basePopulation) {
    const extraPop = targetPopulation - basePopulation;
    delta += Math.min(20, Math.round(extraPop / 200));
  }

  // Water capacity deficit modifier
  if (overrides.water_capacity && overrides.water_capacity < targetPopulation) {
    delta += 6;
  }

  // Relocation radius constraint modifier
  if (overrides.relocation_radius_km && overrides.relocation_radius_km < 10) {
    delta += 4;
  }

  // Compute final risk score clamped between 0 and 100
  const simulatedRisk = Math.min(100, Math.max(0, baseRisk + delta));

  // Derive new priority level
  let simulatedPriority = 'P4';
  if (simulatedRisk >= 80) {
    simulatedPriority = 'P1';
  } else if (simulatedRisk >= 60) {
    simulatedPriority = 'P2';
  } else if (simulatedRisk >= 40) {
    simulatedPriority = 'P3';
  }

  // Derive new recommendation status
  let simulatedRecommendation = 'recommended';
  if (simulatedRisk >= 95 || targetPopulation >= 5800) {
    simulatedRecommendation = 'no_safe_site';
  } else if (simulatedRisk >= 80 || targetPopulation >= 3500) {
    simulatedRecommendation = 'multi_site';
  }

  return {
    before: {
      risk_score: baseRisk,
      priority: basePriority,
      population: basePopulation,
      recommendation_status: baseRecommendation
    },
    after: {
      risk_score: simulatedRisk,
      priority: simulatedPriority,
      population: targetPopulation,
      recommendation_status: simulatedRecommendation,
      delta: simulatedRisk - baseRisk,
      overrides: {
        rainfall_level: overrides.rainfall_level || 'moderate',
        population: targetPopulation,
        water_capacity: overrides.water_capacity || null,
        relocation_radius_km: overrides.relocation_radius_km || 20
      }
    }
  };
}

/**
 * Submit an approval or rejection policy decision for a habitation
 */
export async function submitDecision(habitationId, { action, justification = '' }) {
  await delay(300);

  const newDecision = {
    id: `DEC-${Date.now()}`,
    habitation_id: habitationId,
    action: action.toLowerCase(), // 'approve' | 'reject'
    justification: justification.trim() || 'None provided',
    officer_id: 'OFFICER-001',
    timestamp: new Date().toISOString()
  };

  // Replace existing decision for this habitation or append new one
  const existingIdx = decisionsStore.findIndex((d) => d.habitation_id === habitationId);
  if (existingIdx >= 0) {
    decisionsStore[existingIdx] = newDecision;
  } else {
    decisionsStore.push(newDecision);
  }

  return newDecision;
}

/**
 * Get recorded decision for a habitation if one exists
 */
export async function getDecision(habitationId) {
  await delay(150);
  if (!habitationId) return null;
  const decision = decisionsStore.find((d) => d.habitation_id === habitationId);
  return decision || null;
}
