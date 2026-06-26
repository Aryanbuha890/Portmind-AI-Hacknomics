/**
 * Port Operations Simulation Engine
 * 
 * Transparent calculation logic for the "What-If" scenario simulator.
 * Each KPI formula is documented with source assumptions.
 * 
 * INPUTS:
 *   vessels        {number} Active inbound vessels (5–50 ships)
 *   craneSpeed     {number} Crane operations speed (8–40 moves/hour)
 *   windKnots      {number} Wind & weather severity (2–50 knots)
 *   gateCapacity   {number} Inbound gate flow capacity (20–100 %)
 * 
 * OUTPUT: { delayHours, teuCapacityLoss, vesselsAffected, revenueLoss, confidence, riskLevel }
 */

export const DEFAULTS = {
  vessels: 20,
  craneSpeed: 32,
  windKnots: 5,
  gateCapacity: 90,
};

// ─── Constants (tunable) ──────────────────────────────────────────────────────

const MAX_CRANE_SPEED        = 40;   // moves/hour at full capacity
const AVG_TEU_PER_VESSEL     = 1650; // typical port average (mix of small & large vessels)
const CRANE_MOVES_PER_TEU    = 1.3;  // moves needed per TEU (some containers need repositioning)
const CRANES_PER_BERTH       = 3;    // cranes assigned per active berth
const BERTHS_AVAILABLE       = 12;   // total berths at the port
const OPERATING_HOURS        = 24;   // hours/day port is active

// Revenue model
const HANDLING_FEE_PER_TEU   = 180;  // USD — port handling fee per TEU
const DEMURRAGE_PER_HOUR     = 3500; // USD per vessel per delay hour
const PENALTY_RATE           = 0.15; // 15% cargo value penalty for late delivery contracts

// Weather thresholds (knots)
const WIND_SLOW_THRESHOLD    = 20;   // cranes slow above this
const WIND_STOP_THRESHOLD    = 35;   // crane ops halt above this

// Gate thresholds
const GATE_CONGESTION_LIMIT  = 70;   // below this %, gate causes inland delays

// ─── Helper utilities ─────────────────────────────────────────────────────────

function windThroughputMultiplier(windKnots) {
  if (windKnots <= WIND_SLOW_THRESHOLD) return 1.0;
  if (windKnots >= WIND_STOP_THRESHOLD) return 0.0;
  return 1 - (windKnots - WIND_SLOW_THRESHOLD) / (WIND_STOP_THRESHOLD - WIND_SLOW_THRESHOLD);
}

function effectiveCraneSpeed(craneSpeed, windKnots) {
  return craneSpeed * windThroughputMultiplier(windKnots);
}

function teuThroughputPerBerth(effectiveSpeed) {
  return (effectiveSpeed * OPERATING_HOURS * CRANES_PER_BERTH) / CRANE_MOVES_PER_TEU;
}

function calculateBackloggedVessels(vessels, effectiveSpeed, gateCapacity) {
  const totalThroughput = teuThroughputPerBerth(effectiveSpeed) * BERTHS_AVAILABLE;
  const totalDemand     = vessels * AVG_TEU_PER_VESSEL;
  const gateFactor      = gateCapacity < GATE_CONGESTION_LIMIT
    ? gateCapacity / GATE_CONGESTION_LIMIT
    : 1.0;
  const adjustedThroughput = totalThroughput * gateFactor;

  if (adjustedThroughput >= totalDemand) return 0;
  const unprocessedTEUs   = totalDemand - adjustedThroughput;
  const backloggedVessels = Math.ceil(unprocessedTEUs / AVG_TEU_PER_VESSEL);
  return Math.min(backloggedVessels, vessels);
}

// ─── Core KPI calculations ────────────────────────────────────────────────────

function calcDelayHours(vessels, craneSpeed, windKnots, gateCapacity) {
  const effSpeed         = effectiveCraneSpeed(craneSpeed, windKnots);
  const backlogged       = calculateBackloggedVessels(vessels, effSpeed, gateCapacity);
  if (backlogged === 0) return 0;
  const hourlyThroughput = teuThroughputPerBerth(effSpeed);
  const gateFactor       = gateCapacity < GATE_CONGESTION_LIMIT
    ? gateCapacity / GATE_CONGESTION_LIMIT
    : 1.0;
  let totalDelay = 0;
  for (let i = 1; i <= backlogged; i++) {
    const waitHours = (AVG_TEU_PER_VESSEL * i) / (hourlyThroughput * gateFactor);
    totalDelay += waitHours;
  }
  return Math.round(totalDelay * 10) / 10;
}

function calcTEUCapacityLoss(vessels, craneSpeed, windKnots, gateCapacity) {
  const effSpeed   = effectiveCraneSpeed(craneSpeed, windKnots);
  const backlogged = calculateBackloggedVessels(vessels, effSpeed, gateCapacity);
  return backlogged * AVG_TEU_PER_VESSEL;
}

function calcVesselsAffected(vessels, craneSpeed, windKnots, gateCapacity) {
  const effSpeed = effectiveCraneSpeed(craneSpeed, windKnots);
  return calculateBackloggedVessels(vessels, effSpeed, gateCapacity);
}

function calcRevenueLoss(vessels, craneSpeed, windKnots, gateCapacity) {
  const effSpeed       = effectiveCraneSpeed(craneSpeed, windKnots);
  const backlogged     = calculateBackloggedVessels(vessels, effSpeed, gateCapacity);
  const lostTEUs       = backlogged * AVG_TEU_PER_VESSEL;
  const delayHrs       = calcDelayHours(vessels, craneSpeed, windKnots, gateCapacity);
  const handlingLoss   = lostTEUs * HANDLING_FEE_PER_TEU;
  const demurrageLoss  = backlogged * delayHrs * DEMURRAGE_PER_HOUR;
  const penaltyLoss    = lostTEUs * AVG_TEU_PER_VESSEL * PENALTY_RATE;
  const total = handlingLoss + demurrageLoss + penaltyLoss;
  return Math.round(total / 1e6 * 100) / 100;
}

function calcConfidence(vessels, craneSpeed, windKnots, gateCapacity) {
  let confidence = 98;
  if (vessels > 40) confidence -= 8;
  else if (vessels > 30) confidence -= 3;
  if (windKnots > 28 && windKnots < 38) confidence -= 12;
  else if (windKnots >= 38) confidence -= 6;
  if (gateCapacity < 35) confidence -= 10;
  else if (gateCapacity < 50) confidence -= 4;
  if (craneSpeed < 15 && vessels > 30) confidence -= 8;
  return Math.max(60, Math.min(98, confidence));
}

function calcRiskLevel(delayHours, vesselsAffected, revenueLoss) {
  if (delayHours === 0 && vesselsAffected === 0) return 'Normal';
  if (revenueLoss > 100 || delayHours > 400 || vesselsAffected > 15) return 'High Risk';
  if (revenueLoss > 40  || delayHours > 150 || vesselsAffected > 8)  return 'Medium Risk';
  return 'Low Risk';
}

// ─── Main simulation function ─────────────────────────────────────────────────

export function runSimulation({ vessels, craneSpeed, windKnots, gateCapacity } = DEFAULTS) {
  vessels      = Math.max(5,  Math.min(50,  vessels));
  craneSpeed   = Math.max(8,  Math.min(40,  craneSpeed));
  windKnots    = Math.max(2,  Math.min(50,  windKnots));
  gateCapacity = Math.max(20, Math.min(100, gateCapacity));

  const effSpeed          = effectiveCraneSpeed(craneSpeed, windKnots);
  const windMultiplier    = windThroughputMultiplier(windKnots);
  const dailyThroughput   = teuThroughputPerBerth(effSpeed) * BERTHS_AVAILABLE;
  const totalDemand       = vessels * AVG_TEU_PER_VESSEL;
  const backlogged        = calculateBackloggedVessels(vessels, effSpeed, gateCapacity);

  const delayHours        = calcDelayHours(vessels, craneSpeed, windKnots, gateCapacity);
  const teuCapacityLoss   = calcTEUCapacityLoss(vessels, craneSpeed, windKnots, gateCapacity);
  const vesselsAffected   = calcVesselsAffected(vessels, craneSpeed, windKnots, gateCapacity);
  const revenueLoss       = calcRevenueLoss(vessels, craneSpeed, windKnots, gateCapacity);
  const confidence        = calcConfidence(vessels, craneSpeed, windKnots, gateCapacity);
  const riskLevel         = calcRiskLevel(delayHours, vesselsAffected, revenueLoss);

  return {
    delayHours,
    teuCapacityLoss,
    vesselsAffected,
    revenueLoss,
    confidence,
    riskLevel,
    breakdown: {
      inputs: { vessels, craneSpeed, windKnots, gateCapacity },
      effectiveCraneSpeed:    Math.round(effSpeed * 10) / 10,
      windThroughputFactor:   Math.round(windMultiplier * 100),
      dailyPortCapacityTEUs:  Math.round(dailyThroughput),
      totalDemandTEUs:        totalDemand,
      capacitySurplusTEUs:    Math.round(dailyThroughput - totalDemand),
      backloggedVessels:      backlogged,
      revenueBreakdown: {
        handlingFeesLostM:  Math.round(teuCapacityLoss * HANDLING_FEE_PER_TEU / 1e6 * 100) / 100,
        demurrageCostsM:    Math.round(backlogged * delayHours * DEMURRAGE_PER_HOUR / 1e6 * 100) / 100,
        penaltyCostsM:      Math.round(teuCapacityLoss * AVG_TEU_PER_VESSEL * PENALTY_RATE / 1e6 * 100) / 100,
      },
    },
  };
}
