/**
 * S6, invented: the straight holes. "3pts make a line so continue the
 * TeeBadgeRay and you'll find all the straight holes" (the owner, 2026-09-11).
 *
 *   consumes  px.teebadge.rays      (S5: tee, direction, the badge it points at)
 *             px.recovered.baskets  (S4: clean and recovered baskets, one list)
 *             px.recovered.badges   (S4: so a badge with no ray is still counted)
 *   produces  px.holes.straight     tee, badge, basket, the collinearity residual, the length
 *             px.holes.unresolved   every badge this cannot finish, and why
 *
 * The third point is not searched for; it is the same line, continued. The ray
 * that found the badge carries on past it, and the first basket it enters is the
 * hole's basket. That makes the claim falsifiable in a way a nearest-basket rule
 * never is: the basket's centre has a perpendicular distance to the ray -- the
 * residual -- and a hole whose residual is over `maxResidualPx` is NOT a straight
 * hole, however close the basket happens to be.
 *
 * A badge whose tee never pointed at it, or whose ray leaves the raster with no
 * basket on it, is a DOGLEG: the hole bends, the three points are not on a line,
 * and no continuation of a straight ray can find its basket. Those are listed,
 * with the reason, for a stage that can follow a bend. Nothing here guesses one.
 */
import { labAddress, labDocument } from './address.js';
import { compiledStage } from './stage-sources.js';
import { compileMermaidPcr, lowerToPql } from './mermaid.js';

export const S6_ADDRESSES = {
  hits: labAddress('px.holes.rayhits'),
  straight: labAddress('px.holes.straight'),
  unresolved: labAddress('px.holes.unresolved'),
  check: 'px.exp.lab.s6.straightcheck'
};

export const MAX_RESIDUAL_PX = 12, RAY_STEP_PX = 1;

const round3 = value => Math.round(value * 1000) / 1000;
const centreOfBbox = ([x, y, width, height]) => [x + width / 2, y + height / 2];
const insideBbox = ([x, y, width, height], point) => point[0] >= x && point[0] < x + width && point[1] >= y && point[1] < y + height;
/** Perpendicular distance from a point to the line through `origin` with unit direction `direction`. */
export const residualOf = (origin, direction, point) => Math.abs(direction[0] * (point[1] - origin[1]) - direction[1] * (point[0] - origin[0]));

/** Tick 1. Continue each paired ray past its badge and see which basket it enters. */
export function continueRay({ rays, baskets, stepPx = RAY_STEP_PX, maxResidualPx = MAX_RESIDUAL_PX }) {
  const targets = baskets.objects.map(basket => ({ id: basket.id, bbox: basket.bbox, at: centreOfBbox(basket.bbox), basis: basket.basis }));
  const frame = rays.rays.length ? null : null;
  const hits = rays.rays.filter(ray => ray.badge).map(ray => {
    const start = ray.distancePx + Math.max(ray.badge.bbox[2], ray.badge.bbox[3]);
    const limit = start + 4096;
    for (let step = start; step <= limit; step += stepPx) {
      const point = [ray.origin[0] + ray.direction[0] * step, ray.origin[1] + ray.direction[1] * step];
      const basket = targets.find(target => insideBbox(target.bbox, point));
      if (!basket) continue;
      const residual = residualOf(ray.origin, ray.direction, basket.at);
      return {
        tee: ray.tee, badge: ray.badge.id, reading: ray.badge.reading, basket: basket.id, basketAt: basket.at.map(round3), basketBasis: basket.basis,
        entryAt: point.map(round3), distancePx: round3(step), residualPx: round3(residual),
        straight: residual <= maxResidualPx,
        why: residual <= maxResidualPx ? null : `the basket centre is ${round3(residual)}px off the tee-to-badge line, over the ${maxResidualPx}px a straight hole may be: these three points are not on a line`
      };
    }
    return { tee: ray.tee, badge: ray.badge.id, reading: ray.badge.reading, basket: null, residualPx: null, distancePx: null, straight: false, why: 'the ray carried on past the badge and entered no basket: this hole bends' };
  });
  return { rule: 'the tee-to-badge ray, continued past the badge; the first basket it enters is the hole basket', maxResidualPx, stepPx, targets, hits };
}

/** Tick 2. The straight holes, in badge-reading order. */
export function straightHoles({ hits, rays }) {
  const byTee = new Map(rays.rays.map(ray => [ray.tee, ray]));
  const taken = new Set();
  return hits.hits.filter(hit => hit.straight && hit.basket).filter(hit => {
    if (taken.has(hit.basket)) return false;                 // a basket belongs to one hole
    taken.add(hit.basket);
    return true;
  }).map(hit => {
    const ray = byTee.get(hit.tee);
    return {
      number: /^[0-9]+$/.test(hit.reading ?? '') ? Number(hit.reading) : null, reading: hit.reading,
      tee: { id: hit.tee, at: ray.origin, basis: ray.teeBasis }, badge: { id: hit.badge, at: ray.badge.at, basis: ray.badge.basis },
      basket: { id: hit.basket, at: hit.basketAt, basis: hit.basketBasis },
      direction: ray.direction, teeToBadgePx: ray.distancePx, teeToBasketPx: hit.distancePx,
      residualPx: hit.residualPx, basis: 'tee-badge-ray-continued',
      has: {
        pointing: { fn: labAddress('fn.Tee.pointing'), lean: ray.lean },
        castRay: { fn: labAddress('fn.Tee.castRay'), axisAngleDeg: ray.axisAngleDeg },
        continueRay: { fn: labAddress('fn.Hole.continueRay'), residualPx: hit.residualPx, entryAt: hit.entryAt }
      }
    };
  }).sort((left, right) => (left.number ?? Infinity) - (right.number ?? Infinity) || left.tee.at[1] - right.tee.at[1]);
}

/** Tick 3. Everything the ray could not finish: the doglegs, and the tees and baskets left over. */
export function unresolvedHoles({ hits, rays, badges, baskets, holes }) {
  const resolvedBadges = new Set(holes.map(hole => hole.badge.id)), resolvedBaskets = new Set(holes.map(hole => hole.basket.id));
  const reasonFor = badge => {
    const hit = hits.hits.find(entry => entry.badge === badge.id);
    if (hit) return hit.why ?? 'the ray found a basket another hole had already taken';
    const ray = rays.rays.find(entry => entry.badge && entry.badge.id === badge.id);
    if (ray) return 'the ray reached this badge but the hole was not completed';
    return 'no tee points at this badge: ' + (rays.unpointed.length ? 'the pads that could have are symmetric, so no end of them is the front' : 'no ray reached it');
  };
  return {
    for: 'the badges the straight-line rule cannot finish -- the doglegs -- and what is left over with them, so that a stage that can follow a bend knows exactly what it inherits',
    doglegs: badges.objects.filter(badge => !resolvedBadges.has(badge.id)).map(badge => ({ badge: badge.id, reading: badge.reading?.value ?? null, bbox: badge.bbox, why: reasonFor(badge) })),
    baskets: baskets.objects.filter(basket => !resolvedBaskets.has(basket.id)).map(basket => ({ id: basket.id, at: centreOfBbox(basket.bbox).map(round3), why: 'no straight ray entered it' })),
    tees: rays.rays.filter(ray => !holes.some(hole => hole.tee.id === ray.tee)).map(ray => ({ id: ray.tee, why: ray.why ?? 'its ray found a badge but no basket beyond it' })),
    counts: { badges: badges.objects.length, straight: holes.length, doglegs: badges.objects.length - holes.length }
  };
}

/** The invariants: every badge leaves through exactly one door, and nothing is resolved off the line. */
export function checkStraight({ holes, unresolved, hits, badges, baskets }) {
  const checks = {
    everyBadgeLeavesOnce: badges.objects.length === holes.length + unresolved.doglegs.length &&
      new Set([...holes.map(hole => hole.badge.id), ...unresolved.doglegs.map(entry => entry.badge)]).size === badges.objects.length,
    everyBasketUsedAtMostOnce: new Set(holes.map(hole => hole.basket.id)).size === holes.length,
    everyTeeUsedAtMostOnce: new Set(holes.map(hole => hole.tee.id)).size === holes.length,
    threePointsAreOnALine: holes.every(hole => hole.residualPx <= hits.maxResidualPx),
    theBasketIsBeyondTheBadge: holes.every(hole => hole.teeToBasketPx > hole.teeToBadgePx),
    everyDoglegSaysWhy: unresolved.doglegs.every(entry => typeof entry.why === 'string' && entry.why.length > 10),
    nothingIsGuessed: holes.every(hole => hole.basis === 'tee-badge-ray-continued' && Array.isArray(hole.direction)),
    everyLeftoverBasketIsListed: baskets.objects.length === holes.length + unresolved.baskets.length
  };
  return { straight: holes.length, doglegs: unresolved.doglegs.length, checks, balanced: Object.values(checks).every(Boolean) };
}

export function registerS6(lab) {
  lab.register(labAddress('fn.Hole.continueRay'), continueRay);
  lab.register(labAddress('fn.Hole.straight'), straightHoles);
  lab.register(labAddress('fn.Hole.unresolved'), unresolvedHoles);
  lab.register('fn.lab.s6.checkstraight', checkStraight);
}

export const S6_CONTRACT = {
  stage: 'S6', name: 'Straight holes',
  for: 'the holes three points make a line for: the tee-to-badge ray continued past the badge until it enters a basket, with the residual that says it really is a line',
  consumes: ['px.teebadge.rays', 'px.recovered.baskets', 'px.recovered.badges'].map(labAddress),
  produces: [S6_ADDRESSES.straight, S6_ADDRESSES.unresolved],
  ticks: ['Hole.continueRay', 'Hole.straight', 'Hole.unresolved'],
  invariants: ['everyBadgeLeavesOnce', 'everyBasketUsedAtMostOnce', 'everyTeeUsedAtMostOnce', 'threePointsAreOnALine', 'theBasketIsBeyondTheBadge', 'everyDoglegSaysWhy', 'nothingIsGuessed', 'everyLeftoverBasketIsListed']
};

export function s6Ticks() {
  const px = address => labAddress(address);
  return [
    { name: 'Hole.continueRay', Calculations: [{ call: labAddress('fn.Hole.continueRay'), with: { rays: px('px.teebadge.rays'), baskets: px('px.recovered.baskets') }, args: { stepPx: RAY_STEP_PX, maxResidualPx: MAX_RESIDUAL_PX }, into: S6_ADDRESSES.hits }] },
    { name: 'Hole.straight', Calculations: [{ call: labAddress('fn.Hole.straight'), with: { hits: S6_ADDRESSES.hits, rays: px('px.teebadge.rays') }, args: {}, into: S6_ADDRESSES.straight }] },
    { name: 'Hole.unresolved', Calculations: [{ call: labAddress('fn.Hole.unresolved'), with: { hits: S6_ADDRESSES.hits, rays: px('px.teebadge.rays'), badges: px('px.recovered.badges'), baskets: px('px.recovered.baskets'), holes: S6_ADDRESSES.straight }, args: {}, into: S6_ADDRESSES.unresolved }] }
  ];
}

export function s6Document(lab) { return lab.document('S6', s6Ticks()); }
export function compiledS6() { return compiledStage('S6', compileMermaidPcr, lowerToPql, labDocument); }

export function s6InvariantDocument(lab) {
  return lab.document('S6.invariants', [
    { name: 'CheckStraight', Calculations: [{ call: 'fn.lab.s6.checkstraight', with: { holes: S6_ADDRESSES.straight, unresolved: S6_ADDRESSES.unresolved, hits: S6_ADDRESSES.hits, badges: labAddress('px.recovered.badges'), baskets: labAddress('px.recovered.baskets') }, args: {}, into: S6_ADDRESSES.check }] }
  ]);
}

/** The Stage as the studio runs it; the demo decides how a straight hole is drawn. */
export function s6Spec() {
  return {
    key: 's6', stage: 'S6', title: 'Straight holes', composition: 'lab-s6',
    about: 'three points make a line: the tee-to-badge ray continued past the badge finds the basket, and the badges it cannot finish are the doglegs.',
    needs: S6_CONTRACT.consumes, produces: S6_CONTRACT.produces,
    register: registerS6, ticks: lab => s6Document(lab).Ticks
  };
}

export function runS6(lab) {
  const composition = s6Document(lab), { run, receipt } = lab.run('S6', composition);
  const invariants = s6InvariantDocument(lab);
  lab.run('S6.invariants', invariants);
  return { run, receipt, composition, invariants, hits: lab.get(S6_ADDRESSES.hits), holes: lab.get(S6_ADDRESSES.straight), unresolved: lab.get(S6_ADDRESSES.unresolved), check: lab.get(S6_ADDRESSES.check) };
}
