/**
 * Pathfinding, ported: `lab traverse` and `lab search` as a PxC composition.
 *
 * What the LAB has (scripts/chainspot-lab/traverse/operation.ts, search/searchState.ts):
 * a course manifest with a per-hole `sourceBox` viewport; a traversal standing at
 * one point of the canonical raster with a radius; six hex neighbours at
 * 270/330/30/90/150/210 degrees (`TRAVERSE_DIRECTIONS`); moves `hex n`, `xy dx,dy`,
 * `polar d,a` and absolute; a trail of points with `back` and `branch`; and an
 * event log (`traverse-start`, `traverse-move`, `path-add`, ...). What the LAB
 * does NOT have is an objective: `lab traverse` renders the seven panels and a
 * human or an agent picks the neighbour. The search is the eye in the loop.
 *
 * So the port keeps the LAB's geometry exactly and makes the objective explicit:
 *
 *   a path is a sequence of `hex` moves of one radius, from an anchor point to
 *   within `tolerance` pixels of a target anchor, never leaving the raster;
 *   the objective is the fewest such moves (A* on the triangular lattice the six
 *   directions generate, ties broken by neighbour number, so it is one path).
 *
 * Every step is `traverseTarget(current, radius, { kind: 'hex', neighbor })` --
 * the LAB's own move -- so the produce replays as `lab traverse move <n>` and the
 * event log is the LAB's `SearchEvent` shape.
 */
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { SOURCE } from './source.js';

export const TRAVERSE_DIRECTIONS = [
  { n: 1, angleDeg: 270 }, { n: 2, angleDeg: 330 }, { n: 3, angleDeg: 30 },
  { n: 4, angleDeg: 90 }, { n: 5, angleDeg: 150 }, { n: 6, angleDeg: 210 }
];
export const DEFAULT_TRAVERSE_RADIUS = 75;

export function polarOffset(distance, angleDeg) { const radians = angleDeg * Math.PI / 180; return [distance * Math.cos(radians), distance * Math.sin(radians)]; }

/** `traverse/operation.ts` `traverseTarget`, the four move kinds. */
export function traverseTarget(current, radiusPx, move) {
  if (move.kind === 'absolute') return { point: move.point, detail: `xy ${move.point[0] - current[0]},${move.point[1] - current[1]}` };
  if (move.kind === 'xy') return { point: [current[0] + move.dx, current[1] + move.dy], detail: `xy ${move.dx},${move.dy}` };
  if (move.kind === 'polar') {
    if (!Number.isFinite(move.distance) || move.distance <= 0) throw new Error('lab traverse: polar distance must be positive.');
    const offset = polarOffset(move.distance, move.angleDeg);
    return { point: [current[0] + offset[0], current[1] + offset[1]], detail: `polar ${move.distance},${move.angleDeg}` };
  }
  const direction = TRAVERSE_DIRECTIONS.find(candidate => candidate.n === move.neighbor);
  if (!direction) throw new Error('lab traverse: neighbor must be 1..6.');
  const offset = polarOffset(radiusPx, direction.angleDeg);
  return { point: [current[0] + offset[0], current[1] + offset[1]], detail: `hex ${move.neighbor} ${direction.angleDeg}deg r=${radiusPx}` };
}

export function traversalNeighbors(current, radiusPx) {
  return TRAVERSE_DIRECTIONS.map(direction => ({ n: direction.n, angleDeg: direction.angleDeg, point: traverseTarget(current, radiusPx, { kind: 'hex', neighbor: direction.n }).point }));
}

export function assertTraverseInside(point, width, height) {
  if (point[0] < 0 || point[1] < 0 || point[0] >= width || point[1] >= height) throw new Error(`lab traverse: target ${point[0].toFixed(1)},${point[1].toFixed(1)} leaves canonical raster ${width}x${height}.`);
}

const key = point => `${Math.round(point[0] * 1000)}:${Math.round(point[1] * 1000)}`;
const distance = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1]);

/**
 * The anchors a course offers. `lab scope hN` is blind: it uses the manifest's
 * own source-frame viewport, never the annotation truth, and fails loudly when
 * the course has no viewport table (LAB README, "Tutorial: one course, one
 * hole"). The anchor of a hole is the centre of its `sourceBox`.
 */
export function courseAnchors(course) {
  if (!course.holes || !Object.keys(course.holes).length) throw new Error(`lab scope: course '${course.course}' does not yet define a blind viewport; LAB never falls back to Annotation truth implicitly.`);
  return Object.fromEntries(Object.entries(course.holes).map(([hole, { sourceBox: [x, y, width, height] }]) => [`h${hole}`, [x + width / 2, y + height / 2]]));
}

/** `startTraversal`: a trail with one visible point, and the event that records it. */
export function startTraversal({ name, course, point, radiusPx = DEFAULT_TRAVERSE_RADIUS, page = 'scratch' }) {
  return {
    schemaVersion: 2, nextEventId: 2, page, course,
    trails: { [name]: { name, page, course, color: 0, points: [{ id: 1, point }], visiblePointIds: [1], nextPointId: 2 } },
    traversals: { [name]: { name, page, course, radiusPx, trailName: name } },
    events: [{ id: 1, op: 'traverse-start', page, traversal: name, trail: name, point, detail: `radius=${radiusPx}` }]
  };
}

/** `addTrailPoint` + the `traverse-move` event: one LAB move, applied to the state. */
export function applyMove(state, name, move) {
  const traversal = state.traversals[name], trail = state.trails[name];
  if (!traversal) throw new Error(`lab traverse: unknown traversal '${name}'.`);
  const current = trail.points.at(-1).point;
  const target = traverseTarget(current, traversal.radiusPx, move);
  const id = trail.nextPointId;
  return {
    ...state, nextEventId: state.nextEventId + 1,
    trails: { ...state.trails, [name]: { ...trail, points: [...trail.points, { id, point: target.point }], visiblePointIds: [...trail.visiblePointIds, id], nextPointId: id + 1 } },
    events: [...state.events, { id: state.nextEventId, op: 'traverse-move', page: trail.page, traversal: name, trail: name, pointId: id, point: target.point, detail: target.detail }]
  };
}

/**
 * The search: fewest hex moves from `from` to within `tolerance` of `to`.
 * A* with the admissible heuristic `distance / radius`; ties by neighbour number,
 * so the path is a function of the inputs alone.
 */
export function hexSearch({ from, to, radiusPx = DEFAULT_TRAVERSE_RADIUS, tolerance = radiusPx / 2, frame, maxExpansions = 20000 }) {
  const open = [{ point: from, moves: [], cost: 0 }], best = new Map([[key(from), 0]]);
  let expanded = 0;
  while (open.length) {
    open.sort((a, b) => (a.cost + distance(a.point, to) / radiusPx) - (b.cost + distance(b.point, to) / radiusPx) || a.cost - b.cost);
    const node = open.shift();
    if (distance(node.point, to) <= tolerance) return { reached: true, moves: node.moves, cost: node.cost, expanded, finalPoint: node.point, gap: distance(node.point, to) };
    if (++expanded > maxExpansions) break;
    for (const neighbor of traversalNeighbors(node.point, radiusPx)) {
      if (frame && (neighbor.point[0] < 0 || neighbor.point[1] < 0 || neighbor.point[0] >= frame.width || neighbor.point[1] >= frame.height)) continue;
      const at = key(neighbor.point), cost = node.cost + 1;
      if (best.has(at) && best.get(at) <= cost) continue;
      best.set(at, cost);
      open.push({ point: neighbor.point, moves: [...node.moves, neighbor.n], cost });
    }
  }
  return { reached: false, moves: [], cost: null, expanded, finalPoint: null, gap: null };
}

/** The Calculations: the search's stages, with the search state as the Part between them. */
export function registerPath(lab) {
  lab.register('fn.lab.path.anchors', ({ course }) => ({ course: course.course, radiusPx: DEFAULT_TRAVERSE_RADIUS, anchors: courseAnchors(course) }));
  lab.register('fn.lab.path.start', ({ anchors, from, name, frame }) => {
    const point = anchors.anchors[from];
    if (!point) throw new Error(`lab traverse: --start must name a hole anchor of ${anchors.course}; got '${from}'.`);
    if (frame) assertTraverseInside(point, frame.width, frame.height);
    return startTraversal({ name, course: anchors.course, point, radiusPx: anchors.radiusPx });
  });
  lab.register('fn.lab.path.search', ({ state, anchors, name, to, tolerance, frame }) => {
    const from = state.trails[name].points.at(-1).point, target = anchors.anchors[to];
    if (!target) throw new Error(`lab traverse: no anchor '${to}' on ${anchors.course}.`);
    const found = hexSearch({ from, to: target, radiusPx: state.traversals[name].radiusPx, tolerance: tolerance ?? state.traversals[name].radiusPx / 2, frame });
    let next = state;
    for (const neighbor of found.moves) next = applyMove(next, name, { kind: 'hex', neighbor });
    return [next, { ...found, from, to: target, objective: 'fewest hex moves of one radius to within tolerance of the target anchor, inside the raster' }];
  });
  lab.register('fn.lab.path.receipt', ({ state, found, anchors, name, from, to }) => ({
    for: 'a path found by the ported LAB traversal, as a Part a receipt can point at',
    course: anchors.course, from, to, radiusPx: state.traversals[name].radiusPx,
    objective: found.objective, reached: found.reached, steps: found.moves.length, expanded: found.expanded,
    gapPx: found.gap === null ? null : Math.round(found.gap * 1000) / 1000,
    moves: found.moves,
    // The same path as LAB commands: this trail is replayable in the LAB itself.
    replay: [`lab set ${anchors.course}`, `lab traverse start ${name} --start ${from} --radius ${state.traversals[name].radiusPx}`, ...found.moves.map(neighbor => `lab traverse move ${neighbor}`)],
    points: state.trails[name].points.map(point => point.point.map(value => Math.round(value * 1000) / 1000)),
    events: state.events.map(event => event.op)
  }));
}

/** One course, one pair of anchors, one composition: Anchors -> Start -> Search -> Receipt. */
export function pathDocument(lab, { course, name, from, to }) {
  const at = `px.exp.lab.path.${course}.${from}-${to}`;
  return {
    address: at,
    composition: lab.document(`path-${course}-${from}-${to}`, [
      { name: 'Anchors', Calculations: [{ call: 'fn.lab.path.anchors', with: { course: `px.exp.lab.course.${course}` }, args: {}, into: `${at}.anchors` }] },
      { name: 'Start', Calculations: [{ call: 'fn.lab.path.start', with: { anchors: `${at}.anchors` }, args: { name, from }, into: `${at}.state0` }] },
      { name: 'Search', Calculations: [{ call: 'fn.lab.path.search', with: { state: `${at}.state0`, anchors: `${at}.anchors` }, args: { name, to }, into: [`${at}.state`, `${at}.found`] }] },
      { name: 'Settle', Calculations: [{ call: 'fn.lab.path.receipt', with: { state: `${at}.state`, found: `${at}.found`, anchors: `${at}.anchors` }, args: { name, from, to }, into: at }] }
    ])
  };
}

/** The LAB's course manifests, as Parts: `px.exp.lab.course.<name>` (lowercased). */
export function putCourses(lab, names) {
  return names.map(name => {
    const course = JSON.parse(readFileSync(join(SOURCE, 'courses', `${name}.json`), 'utf8'));
    return lab.put(`px.exp.lab.course.${name.toLowerCase()}`, { for: 'the LAB course manifest, read as a Part: the blind per-hole viewport a traversal starts from', ...course });
  });
}
