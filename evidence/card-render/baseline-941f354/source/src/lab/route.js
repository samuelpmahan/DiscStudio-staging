/**
 * Pathfinding on the Stage outputs.
 *
 * The first port of `lab traverse` (path.js) kept the LAB's hex walk: six
 * neighbours at one radius, an agent picking one, and an objective the port had
 * to invent because the LAB has none. That tool stays what it is -- the
 * human-in-the-loop search over a raster nobody has read yet.
 *
 * This is the other thing, the one the Stages make possible. Once S1 has read
 * the badges (hole numbers), S2 has found the baskets and S3 the visible tees,
 * the objective is not invented at all: it is the course. A path is
 *
 *     for each hole in badge order: its tee to its basket,
 *     then that basket to the next hole's tee,
 *
 * over the canonical raster, with every anchor taken from a Stage's produce Part
 * rather than from the course manifest. Four Ticks: Anchors (read the Parts),
 * Order (badge readings decide the holes, nearest unused tee and basket bind to
 * each), Route (the legs), Settle (the path as one Part with its receipt).
 */
import { labAddress } from './address.js';

export const ROUTE_ADDRESSES = {
  anchors: 'px.exp.lab.route.anchors',
  order: 'px.exp.lab.route.order',
  legs: 'px.exp.lab.route.legs',
  path: course => `px.exp.lab.route.${course}`
};

const centerOf = ([x, y, width, height]) => [x + width / 2, y + height / 2];
const distance = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1]);
const round3 = value => Math.round(value * 1000) / 1000;

/** Every anchor a route can use, read from the Stage Parts: badges, baskets, tees. */
export function anchors({ badges, baskets, tees, raster }) {
  return {
    frame: { width: raster.widthPx, height: raster.heightPx },
    badges: badges.map(badge => ({
      id: badge.id, reading: badge.reading?.value ?? null, status: badge.reading?.status ?? 'unread',
      bbox: badge.unaccountedButOwned.bbox, at: centerOf(badge.unaccountedButOwned.bbox)
    })),
    baskets: baskets.map((basket, index) => ({ id: `basket-${index + 1}`, bbox: basket.bbox, at: centerOf(basket.bbox) })),
    tees: tees.map((tee, index) => ({ id: `tee-${index + 1}`, bbox: tee.bbox, at: tee.center }))
  };
}

/**
 * The holes, in badge order. A badge S1 could not read has no number and cannot
 * take its turn, so it is reported unplaced rather than guessed at; each hole
 * binds the nearest tee and basket not already taken, nearest first, so the
 * binding is a function of the anchors alone.
 */
export function order({ anchors }) {
  const read = anchors.badges.filter(badge => badge.status === 'read' && badge.reading !== null);
  const unreadable = anchors.badges.filter(badge => badge.status !== 'read' || badge.reading === null).map(badge => badge.id);
  const numbered = read.map(badge => ({ badge, number: Number(badge.reading) }))
    .sort((left, right) => left.number - right.number || left.badge.at[1] - right.badge.at[1] || left.badge.at[0] - right.badge.at[0]);
  const claims = (pool, hole) => {
    const free = pool.filter(candidate => !candidate.taken);
    if (!free.length) return null;
    const best = free.map(candidate => ({ candidate, gap: distance(candidate.at, hole.badge.at) }))
      .sort((left, right) => left.gap - right.gap || left.candidate.id.localeCompare(right.candidate.id))[0];
    best.candidate.taken = true;
    return { id: best.candidate.id, at: best.candidate.at, gapFromBadgePx: round3(best.gap) };
  };
  const tees = anchors.tees.map(tee => ({ ...tee })), baskets = anchors.baskets.map(basket => ({ ...basket }));
  const holes = numbered.map(hole => ({ number: hole.number, badge: hole.badge.id, at: hole.badge.at, tee: claims(tees, hole), basket: claims(baskets, hole) }));
  return {
    holes, unreadable,
    unbound: { tees: tees.filter(tee => !tee.taken).map(tee => tee.id), baskets: baskets.filter(basket => !basket.taken).map(basket => basket.id) },
    incomplete: holes.filter(hole => !hole.tee || !hole.basket).map(hole => hole.number)
  };
}

/** The legs: play each hole, then walk to the next tee. Straight lines over the canonical raster. */
export function route({ order, anchors }) {
  const legs = [];
  const playable = order.holes.filter(hole => hole.tee && hole.basket);
  playable.forEach((hole, index) => {
    legs.push({ kind: 'play', hole: hole.number, from: { id: hole.tee.id, at: hole.tee.at }, to: { id: hole.basket.id, at: hole.basket.at }, lengthPx: round3(distance(hole.tee.at, hole.basket.at)) });
    const next = playable[index + 1];
    if (next) legs.push({ kind: 'walk', hole: next.number, from: { id: hole.basket.id, at: hole.basket.at }, to: { id: next.tee.id, at: next.tee.at }, lengthPx: round3(distance(hole.basket.at, next.tee.at)) });
  });
  for (const leg of legs) for (const point of [leg.from.at, leg.to.at])
    if (point[0] < 0 || point[1] < 0 || point[0] >= anchors.frame.width || point[1] >= anchors.frame.height)
      throw new Error(`lab route: anchor ${point[0].toFixed(1)},${point[1].toFixed(1)} leaves canonical raster ${anchors.frame.width}x${anchors.frame.height}.`);
  return legs;
}

/** The path, as one Part: what was played, in what order, how far, and out of which Stage Parts. */
export function settle({ legs, order, anchors, course }) {
  const played = order.holes.filter(hole => hole.tee && hole.basket);
  return {
    for: 'a round over one course, ordered by the badge numbers S1 read and anchored on the tees and baskets S3 and S2 found',
    course,
    objective: 'play the holes in badge order: each hole tee to basket, then basket to the next hole tee, over the canonical raster',
    from: ['px.badges.objects', 'px.baskets', 'px.tees'].map(labAddress),
    holes: played.map(hole => ({ number: hole.number, badge: hole.badge, tee: hole.tee.id, basket: hole.basket.id })),
    waypoints: [legs[0]?.from, ...legs.map(leg => leg.to)].filter(Boolean).map(point => ({ id: point.id, at: point.at.map(round3) })),
    legs,
    playLengthPx: round3(legs.filter(leg => leg.kind === 'play').reduce((sum, leg) => sum + leg.lengthPx, 0)),
    walkLengthPx: round3(legs.filter(leg => leg.kind === 'walk').reduce((sum, leg) => sum + leg.lengthPx, 0)),
    totalLengthPx: round3(legs.reduce((sum, leg) => sum + leg.lengthPx, 0)),
    unplaced: { badges: order.unreadable, tees: order.unbound.tees, baskets: order.unbound.baskets, incompleteHoles: order.incomplete }
  };
}

export function registerRoute(lab) {
  lab.register('fn.lab.route.anchors', anchors);
  lab.register('fn.lab.route.order', order);
  lab.register('fn.lab.route.route', route);
  lab.register('fn.lab.route.settle', settle);
}

/** Anchors -> Order -> Route -> Settle, over the Parts the Stages published. */
export function routeDocument(lab, { course }) {
  const at = ROUTE_ADDRESSES.path(course);
  return {
    address: at,
    composition: lab.document(`route-${course}`, [
      { name: 'Anchors', Calculations: [{ call: 'fn.lab.route.anchors', with: { badges: labAddress('px.badges.objects'), baskets: labAddress('px.baskets'), tees: labAddress('px.tees'), raster: labAddress('px.course.canonicalPixels') }, args: {}, into: ROUTE_ADDRESSES.anchors }] },
      { name: 'Order', Calculations: [{ call: 'fn.lab.route.order', with: { anchors: ROUTE_ADDRESSES.anchors }, args: {}, into: ROUTE_ADDRESSES.order }] },
      { name: 'Route', Calculations: [{ call: 'fn.lab.route.route', with: { order: ROUTE_ADDRESSES.order, anchors: ROUTE_ADDRESSES.anchors }, args: {}, into: ROUTE_ADDRESSES.legs }] },
      { name: 'Settle', Calculations: [{ call: 'fn.lab.route.settle', with: { legs: ROUTE_ADDRESSES.legs, order: ROUTE_ADDRESSES.order, anchors: ROUTE_ADDRESSES.anchors }, args: { course }, into: at }] }
    ])
  };
}

export function runRoute(lab, { course }) {
  const { address, composition } = routeDocument(lab, { course });
  const { run, receipt } = lab.run(composition.PrincipleComponentRender, composition);
  return { address, run, receipt, composition, path: lab.get(address) };
}
