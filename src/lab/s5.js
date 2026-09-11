/**
 * S5, invented: Tee -> Badge. "The tee points directly at the badge" (the owner,
 * 2026-09-11). A tee pad is drawn on a course map pointing down the fairway, and
 * its badge is the first thing down that line, so the pairing does not need a
 * distance rule at all: it needs the tee's own direction, read off the tee's own
 * pixels, and a ray.
 *
 *   consumes  px.recovered.tees / .badges  (S4: clean AND recovered, one list per kind)
 *             px.components                 the bright mask the direction is measured on
 *             px.course.canonicalPixels     the frame the ray may not leave
 *   produces  px.teebadge.rays              per tee: origin, direction, the badge hit,
 *                                           the distance, and the miss reason if none
 *
 * The pointing end is DETERMINED, not assumed. A tee's major axis (the LAB's own
 * `majorAxisOf`, already ported into the component stats S2 publishes) gives a
 * line and two ends; nothing about an axis says which end is the front. What
 * says it is asymmetry: the bright material of the pad is not distributed evenly
 * about the centre of its own bbox, and the end it leans toward is the nose. So
 *
 *     offset    = (centroid of the pad's bright pixels) - (the ring centre)
 *     direction = the unit major axis whose dot product with that offset is
 *                 positive, provided |dot| is at least `minLeanPx`
 *
 * The reference point is the RING centre -- the enclosed hole S3 detected, which
 * is the one landmark on a tee that a nose does not move. (The bbox centre will
 * not do: a nose grows the bbox by as much as it shifts the material, and the
 * two cancel almost exactly.) A pad whose bright material is balanced about its
 * own ring to within `minLeanPx` therefore has NO pointing end -- including
 * every tee S4 recovered by component fallback, which has no ring at all. It is
 * reported that way -- `pointing: null`, with the lean it did measure -- and its
 * badge is left for a later stage rather than paired by proximity, which is the
 * whole difference between this Stage and the nearest-anchor fallback.
 */
import { labAddress, labDocument } from './address.js';
import { compiledStage } from './stage-sources.js';
import { compileMermaidPcr, lowerToPql } from './mermaid.js';

export const S5_ADDRESSES = {
  pointing: labAddress('px.teebadge.pointing'),
  hits: labAddress('px.teebadge.hits'),
  rays: labAddress('px.teebadge.rays'),
  check: 'px.exp.lab.s5.raycheck'
};

export const MIN_LEAN_PX = 0.5, RAY_STEP_PX = 1;

const round3 = value => Math.round(value * 1000) / 1000;
const centreOfBbox = ([x, y, width, height]) => [x + width / 2, y + height / 2];
const insideBbox = ([x, y, width, height], point) => point[0] >= x && point[0] < x + width && point[1] >= y && point[1] < y + height;

/** The centroid of the bright material inside a bbox: the pad, as the raster has it. */
export function brightCentroid(bbox, mask) {
  const [x0, y0, width, height] = bbox;
  let sx = 0, sy = 0, count = 0;
  for (let y = Math.max(0, y0); y < Math.min(mask.height, y0 + height); y++)
    for (let x = Math.max(0, x0); x < Math.min(mask.width, x0 + width); x++)
      if (mask.data[y * mask.width + x]) { sx += x; sy += y; count++; }
  return count ? { at: [sx / count, sy / count], count } : { at: null, count: 0 };
}

/** Tick 1. Which way each tee points, and by how much it leans that way. */
export function teePointing({ tees, fields, minLeanPx = MIN_LEAN_PX }) {
  const mask = fields.bright.mask;
  return {
    rule: 'the unit major axis whose dot product with (bright centroid - ring centre) is positive, when that dot product is at least minLeanPx',
    minLeanPx,
    tees: tees.objects.map(tee => {
      const centre = tee.at ?? centreOfBbox(tee.bbox), centroid = brightCentroid(tee.bbox, mask);
      const angle = tee.angleRad ?? 0, axis = [Math.cos(angle), Math.sin(angle)];
      if (!centroid.at) return { id: tee.id, basis: tee.basis, bbox: tee.bbox, at: centre, axisAngleDeg: null, lean: null, pointing: null, why: 'no bright material inside the pad bbox' };
      const offset = [centroid.at[0] - centre[0], centroid.at[1] - centre[1]];
      const dot = offset[0] * axis[0] + offset[1] * axis[1];
      const pointing = Math.abs(dot) >= minLeanPx ? [Math.sign(dot) * axis[0], Math.sign(dot) * axis[1]] : null;
      return {
        id: tee.id, basis: tee.basis, bbox: tee.bbox, at: centre.map(round3), centroid: centroid.at.map(round3),
        axisAngleDeg: round3((angle * 180 / Math.PI + 360) % 360),
        lean: { offset: offset.map(round3), alongAxisPx: round3(dot), brightPx: centroid.count },
        pointing: pointing ? pointing.map(round3) : null,
        why: pointing ? null : `the pad leans ${Math.abs(round3(dot))}px along its axis about its own ring, under the ${minLeanPx}px a nose has to show: this pad is symmetric and no end of it is the front`
      };
    })
  };
}

/** Tick 2. Cast each ray and see what badge it enters first. */
export function castRays({ pointing, badges, raster, stepPx = RAY_STEP_PX }) {
  const frame = { width: raster.widthPx, height: raster.heightPx };
  const targets = badges.objects.map(badge => ({ id: badge.id, bbox: badge.bbox, at: centreOfBbox(badge.bbox), reading: badge.reading?.value ?? null, basis: badge.basis }));
  const hits = pointing.tees.map(tee => {
    if (!tee.pointing) return { tee: tee.id, badge: null, distancePx: null, steps: 0, why: tee.why };
    const limit = Math.hypot(frame.width, frame.height) / stepPx;
    for (let step = 1; step <= limit; step++) {
      const point = [tee.at[0] + tee.pointing[0] * step * stepPx, tee.at[1] + tee.pointing[1] * step * stepPx];
      if (point[0] < 0 || point[1] < 0 || point[0] >= frame.width || point[1] >= frame.height)
        return { tee: tee.id, badge: null, distancePx: null, steps: step, why: `the ray left the ${frame.width}x${frame.height} raster after ${round3(step * stepPx)}px without crossing a badge` };
      const badge = targets.find(target => insideBbox(target.bbox, point));
      if (badge) return { tee: tee.id, badge: badge.id, reading: badge.reading, entryAt: point.map(round3), distancePx: round3(step * stepPx), steps: step, why: null };
    }
    return { tee: tee.id, badge: null, distancePx: null, steps: 0, why: 'the ray reached the raster diagonal without crossing a badge' };
  });
  return { frame, stepPx, targets, hits };
}

/** Tick 3. The rays, as one Part: a pairing, or a stated reason there is none. */
export function teeBadgeRays({ pointing, hits, badges }) {
  const claims = new Map();
  for (const hit of hits.hits) if (hit.badge) claims.set(hit.badge, [...(claims.get(hit.badge) ?? []), hit.tee]);
  const contested = [...claims.entries()].filter(([, tees]) => tees.length > 1).map(([badge, tees]) => ({ badge, tees }));
  const byId = new Map(pointing.tees.map(tee => [tee.id, tee]));
  const rays = hits.hits.map(hit => {
    const tee = byId.get(hit.tee), target = hits.targets.find(candidate => candidate.id === hit.badge) ?? null;
    const shared = claims.get(hit.badge)?.length > 1;
    return {
      tee: hit.tee, teeBasis: tee.basis, origin: tee.at, direction: tee.pointing, axisAngleDeg: tee.axisAngleDeg, lean: tee.lean,
      badge: shared || !target ? null : { id: target.id, reading: target.reading, bbox: target.bbox, at: target.at.map(round3), basis: target.basis },
      distancePx: shared ? null : hit.distancePx, entryAt: shared ? null : (hit.entryAt ?? null),
      why: shared ? `two tees point at ${hit.badge}: a contested badge is reported, never split` : hit.why
    };
  });
  const paired = rays.filter(ray => ray.badge);
  return {
    for: 'each tee paired with the badge it points at, by the direction its own pixels carry, or the reason there is no pair',
    from: ['px.recovered.tees', 'px.recovered.badges', 'px.components'].map(labAddress),
    rule: pointing.rule, minLeanPx: pointing.minLeanPx, stepPx: hits.stepPx,
    rays, paired: paired.length, contested,
    unpointed: rays.filter(ray => !ray.direction).map(ray => ({ tee: ray.tee, why: ray.why })),
    missed: rays.filter(ray => ray.direction && !ray.badge).map(ray => ({ tee: ray.tee, why: ray.why })),
    badgesWithNoRay: badges.objects.filter(badge => !paired.some(ray => ray.badge.id === badge.id)).map(badge => ({ id: badge.id, reading: badge.reading?.value ?? null, bbox: badge.bbox }))
  };
}

/** The invariants: a tee is paired by its own direction or not at all, and no badge is shared. */
export function checkRays({ rays, tees, badges }) {
  const checks = {
    everyTeeAppearsOnce: rays.rays.length === tees.objects.length && new Set(rays.rays.map(ray => ray.tee)).size === rays.rays.length,
    aPairingHasADirection: rays.rays.every(ray => (ray.badge === null) || (Array.isArray(ray.direction) && ray.distancePx > 0)),
    everyMissSaysWhy: rays.rays.every(ray => ray.badge ? ray.why === null : typeof ray.why === 'string' && ray.why.length > 10),
    noBadgeIsPairedTwice: new Set(rays.rays.filter(ray => ray.badge).map(ray => ray.badge.id)).size === rays.paired,
    everyBadgeIsPairedOrListed: badges.objects.length === rays.paired + rays.badgesWithNoRay.length,
    aSymmetricPadIsRefusedNotGuessed: rays.unpointed.every(entry => rays.rays.find(ray => ray.tee === entry.tee).badge === null)
  };
  return { tees: tees.objects.length, badges: badges.objects.length, paired: rays.paired, contested: rays.contested.length, checks, balanced: Object.values(checks).every(Boolean) };
}

export function registerS5(lab) {
  lab.register(labAddress('fn.Tee.pointing'), teePointing);
  lab.register(labAddress('fn.Tee.castRay'), castRays);
  lab.register(labAddress('fn.TeeBadge.pair'), teeBadgeRays);
  lab.register('fn.lab.s5.checkrays', checkRays);
}

export const S5_CONTRACT = {
  stage: 'S5', name: 'Tee -> Badge',
  for: 'the badge each tee points at, by the direction the tee pad itself carries, with a stated reason wherever there is no pair',
  consumes: ['px.recovered.tees', 'px.recovered.badges', 'px.components', 'px.course.canonicalPixels'].map(labAddress),
  produces: [S5_ADDRESSES.rays],
  ticks: ['Tee.pointing', 'Tee.castRay', 'TeeBadge.pair'],
  invariants: ['everyTeeAppearsOnce', 'aPairingHasADirection', 'everyMissSaysWhy', 'noBadgeIsPairedTwice', 'everyBadgeIsPairedOrListed', 'aSymmetricPadIsRefusedNotGuessed']
};

export function s5Ticks() {
  const px = address => labAddress(address);
  return [
    { name: 'Tee.pointing', Calculations: [{ call: labAddress('fn.Tee.pointing'), with: { tees: px('px.recovered.tees'), fields: px('px.components') }, args: { minLeanPx: MIN_LEAN_PX }, into: S5_ADDRESSES.pointing }] },
    { name: 'Tee.castRay', Calculations: [{ call: labAddress('fn.Tee.castRay'), with: { pointing: S5_ADDRESSES.pointing, badges: px('px.recovered.badges'), raster: px('px.course.canonicalPixels') }, args: { stepPx: RAY_STEP_PX }, into: S5_ADDRESSES.hits }] },
    { name: 'TeeBadge.pair', Calculations: [{ call: labAddress('fn.TeeBadge.pair'), with: { pointing: S5_ADDRESSES.pointing, hits: S5_ADDRESSES.hits, badges: px('px.recovered.badges') }, args: {}, into: S5_ADDRESSES.rays }] }
  ];
}

export function s5Document(lab) { return lab.document('S5', s5Ticks()); }
export function compiledS5() { return compiledStage('S5', compileMermaidPcr, lowerToPql, labDocument); }

export function s5InvariantDocument(lab) {
  return lab.document('S5.invariants', [
    { name: 'CheckRays', Calculations: [{ call: 'fn.lab.s5.checkrays', with: { rays: S5_ADDRESSES.rays, tees: labAddress('px.recovered.tees'), badges: labAddress('px.recovered.badges') }, args: {}, into: S5_ADDRESSES.check }] }
  ]);
}

/** The Stage as the studio runs it; the demo decides how a ray is drawn. */
export function s5Spec() {
  return {
    key: 's5', stage: 'S5', title: 'Tee to badge', composition: 'lab-s5',
    about: 'the badge each tee points at: the pointing end read off the pad\'s own pixels, then a ray.',
    needs: S5_CONTRACT.consumes, produces: S5_CONTRACT.produces,
    register: registerS5, ticks: lab => s5Document(lab).Ticks
  };
}

export function runS5(lab) {
  const composition = s5Document(lab), { run, receipt } = lab.run('S5', composition);
  const invariants = s5InvariantDocument(lab);
  lab.run('S5.invariants', invariants);
  return { run, receipt, composition, invariants, pointing: lab.get(S5_ADDRESSES.pointing), hits: lab.get(S5_ADDRESSES.hits), rays: lab.get(S5_ADDRESSES.rays), check: lab.get(S5_ADDRESSES.check) };
}
