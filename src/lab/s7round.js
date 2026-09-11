/**
 * S7 Pathfinding, second half: the Round. The route that respects the map the
 * course half drew.
 *
 *   consumes  px.course.graph     (the course half: the holes in play order, the edges of the
 *                                  round, the cell grid and the walkable cells)
 *             px.course.summary   (the course half: what is not in the course)
 *   produces  px.round.legs       one leg per edge: its cells, its length, its cost
 *             px.round.path       the whole round as one path
 *             px.round.summary    what was walked, what was not, and why
 *
 * The search is A* over the course's cells, and every part of it is fixed in advance:
 *
 *   moves     the eight neighbours, orthogonal cost 10 and diagonal cost 14
 *             (integers, so two runs add up to the same number on any machine);
 *             a diagonal step is refused unless BOTH of its orthogonal
 *             neighbours are walkable, so a leg cannot squeeze through the
 *             corner between two obstacle cells;
 *   heuristic octile distance with the same 10 and 14: admissible, so the first
 *             path A* settles on is a shortest one;
 *   ties      the frontier is ordered by (f, g, cell index) and the neighbours
 *             are visited in a fixed order, so the path is a function of the
 *             map and the two anchors alone -- no clock, no random, no Date, no
 *             insertion order that depends on how a Map was built.
 *
 * The one thing this Stage may not do is invent a leg. A tee with no walkable
 * path to its basket is reported `reachable: false` with the cells it could
 * reach, and the round carries it as unreachable. A straight line between the
 * anchors would cross the obstacle the course half found, which is precisely the claim
 * `noLegCrossesAnObstacle` refuses.
 */
import { labAddress, labDocument } from './address.js';
import { compiledStage } from './stage-sources.js';
import { compileMermaidPcr, lowerToPql } from './mermaid.js';
import { round3 } from './holes-nearest.js';
import { cellCenter, cellOf } from './s7course.js';

export const ROUND_ADDRESSES = {
  legs: labAddress('px.round.legs'),
  path: labAddress('px.round.path'),
  summary: labAddress('px.round.summary'),
  ledger: 'px.exp.lab.s7.roundledger',
  check: 'px.exp.lab.s7.roundcheck',
  vsStraight: 'px.exp.lab.s7.vsstraight'
};

export const ORTHOGONAL = 10, DIAGONAL = 14;
/** Fixed visit order: the four orthogonals first, then the four diagonals, each clockwise from north. */
export const MOVES = [[0, -1, ORTHOGONAL], [1, 0, ORTHOGONAL], [0, 1, ORTHOGONAL], [-1, 0, ORTHOGONAL], [1, -1, DIAGONAL], [1, 1, DIAGONAL], [-1, 1, DIAGONAL], [-1, -1, DIAGONAL]];

const octile = (ax, ay, bx, by) => {
  const dx = Math.abs(ax - bx), dy = Math.abs(ay - by);
  return ORTHOGONAL * (dx + dy) + (DIAGONAL - 2 * ORTHOGONAL) * Math.min(dx, dy);
};

/**
 * A* from one cell to another over a 0/1 walkable grid. Returns the cells of a
 * shortest path, or `null` with everything it could reach when there is none.
 * Deterministic by construction: the frontier is scanned in full and the best
 * entry is chosen by (f, g, cell), which is a total order.
 */
export function search(frame, walkable, startCell, goalCell) {
  const total = frame.cols * frame.rows;
  if (startCell < 0 || goalCell < 0 || startCell >= total || goalCell >= total) throw new Error(`lab s6: cell ${startCell} or ${goalCell} is outside the ${frame.cols}x${frame.rows} grid.`);
  if (!walkable[startCell] || !walkable[goalCell]) return { cells: null, cost: null, expanded: 0, reached: [startCell].filter(cell => walkable[cell]), why: 'an endpoint is an obstacle cell' };
  const gScore = new Int32Array(total).fill(-1), fScore = new Int32Array(total).fill(-1), cameFrom = new Int32Array(total).fill(-1), closed = new Uint8Array(total);
  const open = new Set([startCell]);
  const goalX = goalCell % frame.cols, goalY = Math.floor(goalCell / frame.cols);
  gScore[startCell] = 0; fScore[startCell] = octile(startCell % frame.cols, Math.floor(startCell / frame.cols), goalX, goalY);
  let expanded = 0;
  while (open.size) {
    let current = -1;
    for (const cell of open) if (current < 0 || fScore[cell] < fScore[current] || (fScore[cell] === fScore[current] && (gScore[cell] < gScore[current] || (gScore[cell] === gScore[current] && cell < current)))) current = cell;
    if (current === goalCell) {
      const cells = [];
      for (let cell = goalCell; cell !== -1; cell = cameFrom[cell]) cells.unshift(cell);
      return { cells, cost: gScore[goalCell], expanded, reached: null, why: null };
    }
    open.delete(current); closed[current] = 1; expanded++;
    const x = current % frame.cols, y = Math.floor(current / frame.cols);
    for (const [dx, dy, step] of MOVES) {
      const nx = x + dx, ny = y + dy;
      if (nx < 0 || ny < 0 || nx >= frame.cols || ny >= frame.rows) continue;
      const neighbour = ny * frame.cols + nx;
      if (!walkable[neighbour] || closed[neighbour]) continue;
      // No corner cutting: a diagonal needs both of its orthogonal neighbours open.
      if (step === DIAGONAL && (!walkable[y * frame.cols + nx] || !walkable[ny * frame.cols + x])) continue;
      const tentative = gScore[current] + step;
      if (gScore[neighbour] !== -1 && tentative >= gScore[neighbour]) continue;
      cameFrom[neighbour] = current; gScore[neighbour] = tentative;
      fScore[neighbour] = tentative + octile(nx, ny, goalX, goalY);
      open.add(neighbour);
    }
  }
  const reached = [];
  for (let cell = 0; cell < total; cell++) if (closed[cell]) reached.push(cell);
  return { cells: null, cost: null, expanded, reached, why: 'no walkable path joins the two cells' };
}

const polylineLength = points => round3(points.slice(1).reduce((sum, point, index) => sum + Math.hypot(point[0] - points[index][0], point[1] - points[index][1]), 0));

/** Tick 1. One leg per edge of the course graph, searched over the walkable cells. */
export function roundLegs({ graph }) {
  const frame = graph.frame, walkable = graph.walkable.cells, nodes = new Map(graph.nodes.map(node => [node.id, node]));
  return graph.edges.map(edge => {
    const from = nodes.get(edge.from), to = nodes.get(edge.to);
    if (!from || !to) throw new Error(`lab s6: edge ${edge.from}->${edge.to} names a node the graph does not have.`);
    const found = search(frame, walkable, from.cell, to.cell);
    const base = { kind: edge.kind, hole: edge.hole, from: { id: from.id, at: from.at, cell: from.cell }, to: { id: to.id, at: to.at, cell: to.cell }, straightLengthPx: edge.straightLengthPx, straightIsBlocked: edge.straightIsBlocked };
    if (!found.cells) return { ...base, reachable: false, cells: [], points: [], lengthPx: null, cost: null, expanded: found.expanded, why: found.why, reachedCells: found.reached.length };
    const points = [from.at, ...found.cells.slice(1, -1).map(cell => cellCenter(frame, cell).map(round3)), to.at];
    return { ...base, reachable: true, cells: found.cells, points, lengthPx: polylineLength(points), cost: found.cost, cellLengthPx: round3((found.cost / ORTHOGONAL) * frame.cellPx), expanded: found.expanded, why: null, bends: found.cells.length > 2 ? found.cells.length - 2 : 0 };
  });
}

/** Tick 2. The whole round, end to end, as one path. */
export function roundPath({ legs, graph }) {
  const walked = legs.filter(leg => leg.reachable);
  return {
    for: 'the round as one path over the canonical raster: every leg searched over the walkable cells, nothing straightened',
    course: graph.course, cellPx: graph.frame.cellPx,
    from: [labAddress('px.course.graph'), labAddress('px.course.walkable')],
    order: graph.order,
    waypoints: [...(walked[0] ? [{ id: walked[0].from.id, at: walked[0].from.at }] : []), ...walked.map(leg => ({ id: leg.to.id, at: leg.to.at }))],
    cells: walked.flatMap((leg, index) => (index ? leg.cells.slice(1) : leg.cells)),
    points: walked.flatMap((leg, index) => (index ? leg.points.slice(1) : leg.points)),
    lengthPx: round3(walked.reduce((sum, leg) => sum + leg.lengthPx, 0)),
    cost: walked.reduce((sum, leg) => sum + leg.cost, 0),
    playLengthPx: round3(walked.filter(leg => leg.kind === 'play').reduce((sum, leg) => sum + leg.lengthPx, 0)),
    walkLengthPx: round3(walked.filter(leg => leg.kind === 'walk').reduce((sum, leg) => sum + leg.lengthPx, 0)),
    unreachable: legs.filter(leg => !leg.reachable).map(leg => ({ kind: leg.kind, hole: leg.hole, from: leg.from.id, to: leg.to.id, why: leg.why }))
  };
}

/** Tick 3. The round in the numbers a reader reads first. */
export function roundSummary({ path, legs, course }) {
  return {
    for: 'what the round cost, how much of it was the obstacle, and what could not be walked at all',
    course: course.course, holes: course.holes, legs: legs.length,
    walked: legs.filter(leg => leg.reachable).length, unreachable: path.unreachable,
    lengthPx: path.lengthPx, straightLengthPx: round3(legs.filter(leg => leg.reachable).reduce((sum, leg) => sum + leg.straightLengthPx, 0)),
    detourPx: round3(path.lengthPx - legs.filter(leg => leg.reachable).reduce((sum, leg) => sum + leg.straightLengthPx, 0)),
    legsThatHadToBend: legs.filter(leg => leg.reachable && leg.straightIsBlocked).map(leg => `${leg.kind}:${leg.from.id}->${leg.to.id}`),
    cells: path.cells.length, unplaced: course.unplaced
  };
}

/* ------------------------------------------- the invariants, as the oracle */

export function accountRound({ legs, path, graph }) {
  return {
    edges: graph.edges.length, legs: legs.length,
    walked: legs.filter(leg => leg.reachable).length, unreachable: path.unreachable.length,
    cells: path.cells.length, cost: path.cost, lengthPx: path.lengthPx,
    obstacleCells: graph.obstacles.terrainCells.length, walkableCells: graph.walkable.count
  };
}

/** What a round may never do: cross an obstacle, skip an edge, or straighten a leg it could not walk. */
export function checkRound({ ledger, legs, path, graph }) {
  const frame = graph.frame, obstacles = new Set(graph.obstacles.terrainCells);
  const contiguous = cells => cells.every((cell, index) => {
    if (!index) return true;
    const previous = cells[index - 1];
    return Math.abs((cell % frame.cols) - (previous % frame.cols)) <= 1 && Math.abs(Math.floor(cell / frame.cols) - Math.floor(previous / frame.cols)) <= 1 && cell !== previous;
  });
  const checks = {
    noLegCrossesAnObstacle: legs.every(leg => leg.cells.every(cell => !obstacles.has(cell))),
    everyEdgeIsALeg: ledger.edges === ledger.legs && legs.every((leg, index) => leg.from.id === graph.edges[index].from && leg.to.id === graph.edges[index].to),
    unreachableIsReportedNotStraightened: legs.every(leg => leg.reachable ? leg.cells.length > 0 && leg.lengthPx !== null : leg.cells.length === 0 && leg.lengthPx === null && path.unreachable.some(entry => entry.from === leg.from.id && entry.to === leg.to.id)),
    everyLegIsContiguous: legs.every(leg => contiguous(leg.cells)),
    everyLegEndsOnItsAnchors: legs.filter(leg => leg.reachable).every(leg =>
      leg.cells[0] === leg.from.cell && leg.cells.at(-1) === leg.to.cell &&
      leg.points[0] === leg.from.at && leg.points.at(-1) === leg.to.at),
    aBentLegIsLongerThanItsStraightLine: legs.filter(leg => leg.reachable).every(leg => leg.lengthPx >= leg.straightLengthPx - 1e-6 || !leg.straightIsBlocked)
  };
  return { ...ledger, checks, balanced: Object.values(checks).every(Boolean) };
}

/* ---------------------------------- S6 against the straight route of task 114 */

/**
 * The straight round (route.js) and this one, leg by leg. The straight route was
 * not wrong about the anchors -- it binds the same holes to the same tees and
 * baskets -- it was wrong about the ground between them, and this Part is how
 * much: per leg, how far the straight line went, how far a leg that respects the
 * map has to go, and how many obstacle cells the straight line passed through.
 */
export function compareWithStraight({ legs, straight, graph }) {
  const frame = graph.frame, walkable = graph.walkable.cells;
  const crossed = (from, to) => {
    const steps = Math.max(1, Math.ceil(Math.hypot(to[0] - from[0], to[1] - from[1]) / (frame.cellPx / 2))), cells = new Set();
    for (let step = 0; step <= steps; step++) {
      const x = from[0] + ((to[0] - from[0]) * step) / steps, y = from[1] + ((to[1] - from[1]) * step) / steps;
      const cell = cellOf(frame, Math.min(frame.widthPx - 1, Math.max(0, x)), Math.min(frame.heightPx - 1, Math.max(0, y)));
      if (!walkable[cell]) cells.add(cell);
    }
    return [...cells].sort((left, right) => left - right);
  };
  const rows = legs.map(leg => {
    const straightLeg = straight.legs.find(entry => entry.kind === leg.kind && entry.from.id === leg.from.id && entry.to.id === leg.to.id) ?? null;
    const through = crossed(leg.from.at, leg.to.at);
    return {
      leg: `${leg.kind}:${leg.from.id}->${leg.to.id}`, hole: leg.hole,
      straightLengthPx: straightLeg?.lengthPx ?? leg.straightLengthPx,
      routedLengthPx: leg.lengthPx, reachable: leg.reachable,
      deltaPx: leg.reachable ? round3(leg.lengthPx - (straightLeg?.lengthPx ?? leg.straightLengthPx)) : null,
      detourRatio: leg.reachable ? round3(leg.lengthPx / Math.max(1e-9, straightLeg?.lengthPx ?? leg.straightLengthPx)) : null,
      obstacleCellsTheStraightLineCrosses: through.length, cells: through
    };
  });
  const walked = rows.filter(row => row.reachable);
  return {
    for: 'what respecting the obstacle map costs, measured against the straight-leg route this port landed first',
    straight: { address: labAddress('px.route.labfixture'), objective: straight.objective, totalLengthPx: straight.totalLengthPx },
    routed: { address: ROUND_ADDRESSES.path, objective: 'the same order over the same anchors, searched over the walkable cells' },
    sameHoles: JSON.stringify(straight.holes.map(hole => hole.number)) === JSON.stringify(graph.order),
    sameAnchors: straight.legs.every(entry => graph.edges.some(edge => edge.kind === entry.kind && edge.from === entry.from.id && edge.to === entry.to.id)),
    legs: rows,
    straightTotalPx: round3(walked.reduce((sum, row) => sum + row.straightLengthPx, 0)),
    routedTotalPx: round3(walked.reduce((sum, row) => sum + row.routedLengthPx, 0)),
    deltaPx: round3(walked.reduce((sum, row) => sum + row.deltaPx, 0)),
    legsTheStraightRouteWalkedThroughAnObstacle: rows.filter(row => row.obstacleCellsTheStraightLineCrosses > 0).map(row => row.leg),
    obstacleCellsTheStraightRouteCrosses: [...new Set(rows.flatMap(row => row.cells))].length
  };
}

export function registerRound(lab) {
  lab.register(labAddress('fn.Round.legs'), roundLegs);
  lab.register(labAddress('fn.Round.path'), roundPath);
  lab.register(labAddress('fn.Round.summary'), roundSummary);
  lab.register('fn.lab.s7.accountround', accountRound);
  lab.register('fn.lab.s7.checkround', checkRound);
  lab.register('fn.lab.s7.comparewithstraight', compareWithStraight);
}

export const ROUND_CONTRACT = {
  stage: 'S7', name: 'Round',
  for: 'the round actually walked: a deterministic search from each tee to its basket and on to the next tee, over the cells the course half says are walkable',
  consumes: [labAddress('px.course.graph'), labAddress('px.course.summary')],
  produces: [ROUND_ADDRESSES.legs, ROUND_ADDRESSES.path, ROUND_ADDRESSES.summary],
  ticks: ['Round.legs', 'Round.path', 'Round.summary'],
  invariants: ['noLegCrossesAnObstacle', 'everyEdgeIsALeg', 'unreachableIsReportedNotStraightened', 'everyLegIsContiguous', 'everyLegEndsOnItsAnchors', 'aBentLegIsLongerThanItsStraightLine'],
  search: { algorithm: 'A*', moves: 8, orthogonalCost: ORTHOGONAL, diagonalCost: DIAGONAL, heuristic: 'octile', cornerCutting: false, tieBreak: '(f, g, cell index)', clock: 'none', random: 'none' }
};

export function roundTicks() {
  return [
    { name: 'Round.legs', Calculations: [{ call: labAddress('fn.Round.legs'), with: { graph: labAddress('px.course.graph') }, args: {}, into: ROUND_ADDRESSES.legs }] },
    { name: 'Round.path', Calculations: [{ call: labAddress('fn.Round.path'), with: { legs: ROUND_ADDRESSES.legs, graph: labAddress('px.course.graph') }, args: {}, into: ROUND_ADDRESSES.path }] },
    { name: 'Round.summary', Calculations: [{ call: labAddress('fn.Round.summary'), with: { path: ROUND_ADDRESSES.path, legs: ROUND_ADDRESSES.legs, course: labAddress('px.course.summary') }, args: {}, into: ROUND_ADDRESSES.summary }] }
  ];
}

export function roundDocument(lab) { return lab.document('S7.round', roundTicks()); }

/** `stages/S7.round.mmd`, compiled: the same Calculations over the same addresses in the same order. */
export function compiledRound() { return compiledStage('S7.round', compileMermaidPcr, lowerToPql, labDocument); }

export function roundInvariantDocument(lab) {
  return lab.document('S7.round.invariants', [
    { name: 'AccountRound', Calculations: [{ call: 'fn.lab.s7.accountround', with: { legs: ROUND_ADDRESSES.legs, path: ROUND_ADDRESSES.path, graph: labAddress('px.course.graph') }, args: {}, into: ROUND_ADDRESSES.ledger }] },
    { name: 'CheckRound', Calculations: [{ call: 'fn.lab.s7.checkround', with: { ledger: ROUND_ADDRESSES.ledger, legs: ROUND_ADDRESSES.legs, path: ROUND_ADDRESSES.path, graph: labAddress('px.course.graph') }, args: {}, into: ROUND_ADDRESSES.check }] }
  ]);
}

/** The comparison with the straight route, as its own one-Tick composition over both rounds' Parts. */
export function roundCompareDocument(lab, { course = 'labfixture' } = {}) {
  return lab.document('S7.vs-straight', [
    { name: 'CompareWithStraight', Calculations: [{ call: 'fn.lab.s7.comparewithstraight', with: { legs: ROUND_ADDRESSES.legs, straight: labAddress(`px.route.${course}`), graph: labAddress('px.course.graph') }, args: {}, into: ROUND_ADDRESSES.vsStraight }] }
  ]);
}

/** The Stage as the studio runs it; the demo decides how a round is drawn. */
export function s7Spec() {
  return {
    key: 's7', stage: 'S7', title: 'Round', composition: 'lab-s7',
    about: 'the round walked over the cells the course half says are walkable: every leg searched, nothing straightened, an unreachable basket reported as one.',
    needs: ROUND_CONTRACT.consumes, produces: ROUND_CONTRACT.produces,
    register: registerRound, ticks: lab => roundDocument(lab).Ticks
  };
}

export function runRound(lab, { compareWith = null } = {}) {
  const composition = roundDocument(lab), { run, receipt } = lab.run('S7.round', composition);
  const invariants = roundInvariantDocument(lab);
  lab.run('S7.round.invariants', invariants);
  const comparison = compareWith ? roundCompareDocument(lab, { course: compareWith }) : null;
  if (comparison) lab.run('S7.vs-straight', comparison);
  return {
    run, receipt, composition, invariants, comparison,
    legs: lab.get(ROUND_ADDRESSES.legs), path: lab.get(ROUND_ADDRESSES.path), summary: lab.get(ROUND_ADDRESSES.summary),
    ledger: lab.get(ROUND_ADDRESSES.ledger), check: lab.get(ROUND_ADDRESSES.check),
    vsStraight: comparison ? lab.get(ROUND_ADDRESSES.vsStraight) : null
  };
}
