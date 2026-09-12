/**
 * S7 Pathfinding, first half: the Course. S6 says which holes the picture
 * actually supports -- the ones whose tee, badge and basket are on one line --
 * and which badges it cannot finish; this says what the course IS: those holes
 * as a graph over the canonical raster, and what lies between their anchors.
 *
 * It binds `px.holes.straight`, not the nearest-anchor fallback's
 * `px.holes.objects`. The two lists are different claims about the same
 * picture: the fallback always produces a hole, the ray produces one only where
 * three points really are on a line. A round that is played over guesses while a
 * ray-resolved list sits beside it is a round nobody can check, so the doglegs
 * S6 refused to finish arrive here as `unplayed` and are never quietly routed.
 *
 *   consumes  px.holes.straight      (S6: the holes three points make a line for)
 *             px.holes.unresolved    (S6: the badges whose hole bends)
 *             px.course.canonicalPixels (S0: the frame every coordinate is in)
 *             px.remaining.afterBadges  (S1: every pixel no Badge owns or mutes)
 *             px.components          (S2: the bright and dark masks and labels)
 *             px.baskets / px.tees   (S2, S3: the pixels those objects own)
 *   produces  px.course.graph        holes in play order, hole geometry, the
 *                                    obstacle map, and the walkable cells
 *             px.course.summary      hole count, total length, and what is unplayed
 *
 * The obstacle map is a derivation, not a detector. Every pixel of the raster
 * leaves through exactly one door:
 *
 *   badge    a pixel S1 owns or mutes  (that is, NOT in px.remaining.afterBadges)
 *   basket   a pixel an S2 Basket owns
 *   tee      a pixel an S3 Tee owns
 *   terrain  what is left that is still dark in S1's mask: structure that made
 *            it through every Stage and that no Stage object claims
 *   open     what is left
 *
 * and a cell of the grid takes the first of those classes present in it, in
 * that order, so the classes partition the grid. Only `terrain` is an obstacle:
 * a badge, a basket and a tee are symbols printed on a map, and one of them is
 * where the round is going. That choice is stated here rather than implied, and
 * `px.course.graph.walkableRule` carries it into the Part.
 *
 * The graph's edges are the round the course implies -- each hole tee to basket,
 * then basket to the next hole's tee -- carrying their straight geometry AND
 * whether that straight line crosses an obstacle cell. S5 does not route around
 * anything; it says which straight lines cannot be walked, which is the question
 * the round half of S7 answers.
 */
import { labAddress, labDocument } from './address.js';
import { compiledStage } from './stage-sources.js';
import { compileMermaidPcr, lowerToPql } from './mermaid.js';
import { centerOf, distance, round3 } from './holes-nearest.js';

export const COURSE_ADDRESSES = {
  holes: labAddress('px.course.holes'),
  obstacles: labAddress('px.course.obstacles'),
  walkable: labAddress('px.course.walkable'),
  graph: labAddress('px.course.graph'),
  summary: labAddress('px.course.summary'),
  ledger: 'px.exp.lab.s7.courseledger',
  check: 'px.exp.lab.s7.coursecheck'
};

export const CELL_PX = 16;
export const CLASSES = ['terrain', 'basket', 'tee', 'badge', 'open'];
export const WALKABLE_RULE = 'every class but terrain: a badge, a basket and a tee are printed on the map, and a tee or a basket is where a leg ends';

/** The cell grid over the canonical raster: `cell(x, y)` is one index, `cols * rows` of them. */
export function grid(widthPx, heightPx, cellPx = CELL_PX) {
  const cols = Math.ceil(widthPx / cellPx), rows = Math.ceil(heightPx / cellPx);
  return { cellPx, cols, rows, cells: cols * rows, widthPx, heightPx };
}
export const cellOf = (frame, x, y) => Math.floor(y / frame.cellPx) * frame.cols + Math.floor(x / frame.cellPx);
export const cellCenter = (frame, cell) => [(cell % frame.cols) * frame.cellPx + frame.cellPx / 2, Math.floor(cell / frame.cols) * frame.cellPx + frame.cellPx / 2];

/**
 * Tick 1. Hole geometry: the tee-to-basket vector and its length in raster px.
 * An anchor outside the canonical raster refuses the Stage -- a course whose
 * geometry leaves its own frame is not a course with a bad number in it, it is
 * a course built from anchors that were never checked.
 */
export function holeGeometry({ holes, unresolved, raster }) {
  const frame = { widthPx: raster.widthPx, heightPx: raster.heightPx };
  const inside = point => point[0] >= 0 && point[1] >= 0 && point[0] < frame.widthPx && point[1] < frame.heightPx;
  const placed = [];
  for (const hole of holes) {
    for (const [role, anchor] of [['tee', hole.tee], ['basket', hole.basket]])
      if (!inside(anchor.at)) throw new Error(`lab s7: hole ${hole.number}'s ${role} at ${anchor.at.map(value => value.toFixed(1)).join(',')} leaves canonical raster ${frame.widthPx}x${frame.heightPx}.`);
    const vector = [round3(hole.basket.at[0] - hole.tee.at[0]), round3(hole.basket.at[1] - hole.tee.at[1])];
    placed.push({
      number: hole.number, badge: hole.badge.id, basis: hole.basis,
      tee: { id: hole.tee.id, at: hole.tee.at.map(round3) }, basket: { id: hole.basket.id, at: hole.basket.at.map(round3) },
      vector, lengthPx: round3(distance(hole.tee.at, hole.basket.at)),
      bearingDeg: round3((Math.atan2(vector[1], vector[0]) * 180 / Math.PI + 360) % 360),
      // What S6 measured for this hole, carried on: the perpendicular distance
      // from the basket to the tee-to-badge ray. A course made of straight holes
      // has a residual per hole, and it is the reason each hole is in the round.
      residualPx: hole.residualPx ?? null
    });
  }
  // Every badge S6 could not finish. They are NOT holes with something missing:
  // they are holes whose shape the straight-line rule cannot express.
  const unplayed = (unresolved?.doglegs ?? []).map(entry => ({ badge: entry.badge, reading: entry.reading, why: entry.why }));
  return { frame, order: placed.map(hole => hole.number), holes: placed, unplayed, spare: { tees: (unresolved?.tees ?? []).map(entry => entry.id), baskets: (unresolved?.baskets ?? []).map(entry => entry.id) } };
}

/**
 * Tick 2. The obstacle map: one class per pixel, one class per cell, counted.
 * `remaining` is the complement of what S1 owns and mutes, so the badge class
 * needs no Badge Part of its own.
 */
export function obstacleMap({ remaining, fields, baskets, tees, raster, cellPx = CELL_PX }) {
  const width = raster.widthPx, height = raster.heightPx, total = width * height;
  const frame = grid(width, height, cellPx);
  const isRemaining = new Uint8Array(total);
  for (const pixel of remaining.pixels) isRemaining[pixel] = 1;
  const owned = new Uint8Array(total);                       // 1 basket, 2 tee
  for (const basket of baskets) for (const pixel of basket.px) owned[pixel] = 1;
  for (const tee of tees) for (const pixel of tee.px) owned[pixel] = 2;
  const dark = fields.dark.mask.data;
  const perClass = Object.fromEntries(CLASSES.map(name => [name, 0]));
  const cellCounts = CLASSES.map(() => new Int32Array(frame.cells));
  const terrainPixels = [];
  for (let pixel = 0; pixel < total; pixel++) {
    const x = pixel % width, cell = Math.floor((pixel - x) / width / cellPx) * frame.cols + Math.floor(x / cellPx);
    let klass;
    if (!isRemaining[pixel]) klass = 'badge';
    else if (owned[pixel] === 1) klass = 'basket';
    else if (owned[pixel] === 2) klass = 'tee';
    else if (dark[pixel]) { klass = 'terrain'; terrainPixels.push(pixel); }
    else klass = 'open';
    perClass[klass]++;
    cellCounts[CLASSES.indexOf(klass)][cell]++;
  }
  const cells = new Array(frame.cells).fill('open');
  for (let cell = 0; cell < frame.cells; cell++)
    cells[cell] = CLASSES.find((_, index) => cellCounts[index][cell] > 0) ?? 'open';
  const cellsByClass = Object.fromEntries(CLASSES.map(name => [name, cells.filter(value => value === name).length]));
  return {
    for: 'what is between the anchors: one class per pixel and per cell, derived from the Parts the Stages published and from nothing else',
    from: ['px.remaining.afterBadges', 'px.components', 'px.baskets', 'px.tees'].map(labAddress),
    frame, classes: CLASSES, priority: 'a cell takes the first class present in it, in the order above',
    pixelsByClass: perClass, cellsByClass, cells,
    terrain: { pixels: terrainPixels, cells: cells.reduce((list, value, cell) => (value === 'terrain' ? [...list, cell] : list), []) }
  };
}

/** Tick 3. The walkable cells: the partition's other half, and the rule that draws the line. */
export function walkableCells({ obstacles }) {
  const walkable = obstacles.cells.map(value => (value === 'terrain' ? 0 : 1));
  return {
    rule: WALKABLE_RULE, frame: obstacles.frame, walkable,
    count: walkable.reduce((sum, value) => sum + value, 0),
    obstacleCells: obstacles.terrain.cells
  };
}

/** Does the straight line between two points pass through an obstacle cell? Sampled at half a cell. */
export function straightIsBlocked(frame, walkable, from, to) {
  const steps = Math.max(1, Math.ceil(distance(from, to) / (frame.cellPx / 2)));
  for (let step = 0; step <= steps; step++) {
    const x = from[0] + ((to[0] - from[0]) * step) / steps, y = from[1] + ((to[1] - from[1]) * step) / steps;
    if (!walkable[cellOf(frame, Math.min(frame.widthPx - 1, Math.max(0, x)), Math.min(frame.heightPx - 1, Math.max(0, y)))]) return true;
  }
  return false;
}

/** Tick 4. The graph: the holes in play order, the round's edges, and the map they are drawn on. */
export function courseGraph({ geometry, obstacles, walkable, course }) {
  const frame = walkable.frame, nodes = [], edges = [];
  geometry.holes.forEach((hole, index) => {
    nodes.push({ id: hole.tee.id, kind: 'tee', hole: hole.number, at: hole.tee.at, cell: cellOf(frame, hole.tee.at[0], hole.tee.at[1]) });
    nodes.push({ id: hole.basket.id, kind: 'basket', hole: hole.number, at: hole.basket.at, cell: cellOf(frame, hole.basket.at[0], hole.basket.at[1]) });
    edges.push({ kind: 'play', hole: hole.number, from: hole.tee.id, to: hole.basket.id, straightLengthPx: hole.lengthPx, straightIsBlocked: straightIsBlocked(frame, walkable.walkable, hole.tee.at, hole.basket.at) });
    const next = geometry.holes[index + 1];
    if (next) edges.push({ kind: 'walk', hole: next.number, from: hole.basket.id, to: next.tee.id, straightLengthPx: round3(distance(hole.basket.at, next.tee.at)), straightIsBlocked: straightIsBlocked(frame, walkable.walkable, hole.basket.at, next.tee.at) });
  });
  return {
    for: 'the course as a graph over the canonical raster: which holes are in play, in what order, over what ground',
    course, frame, walkableRule: walkable.rule,
    order: geometry.order, holes: geometry.holes, nodes, edges,
    obstacles: { classes: obstacles.classes, cellsByClass: obstacles.cellsByClass, pixelsByClass: obstacles.pixelsByClass, cells: obstacles.cells, terrainCells: obstacles.terrain.cells },
    walkable: { cells: walkable.walkable, count: walkable.count }
  };
}

/** Tick 5. The summary a reader reads first. */
export function courseSummary({ graph, geometry }) {
  return {
    for: 'the course in five numbers, and what is not in it',
    course: graph.course, holes: graph.holes.length, order: graph.order,
    from: labAddress('px.holes.straight'),
    totalLengthPx: round3(graph.holes.reduce((sum, hole) => sum + hole.lengthPx, 0)),
    longestHole: graph.holes.reduce((longest, hole) => (!longest || hole.lengthPx > longest.lengthPx ? hole : longest), null)?.number ?? null,
    blockedStraightLegs: graph.edges.filter(edge => edge.straightIsBlocked).map(edge => `${edge.kind}:${edge.from}->${edge.to}`),
    cellPx: graph.frame.cellPx, walkableCells: graph.walkable.count, obstacleCells: graph.obstacles.terrainCells.length,
    // A dogleg is not routed by the fallback and not straightened: it is named.
    unplayed: { doglegs: geometry.unplayed, tees: geometry.spare.tees, baskets: geometry.spare.baskets },
    residualPx: graph.holes.map(hole => hole.residualPx)
  };
}

/* ------------------------------------------- the invariants, as the oracle */

export function accountCourse({ obstacles, walkable, graph, geometry }) {
  return {
    pixels: Object.values(obstacles.pixelsByClass).reduce((sum, value) => sum + value, 0),
    pixelsInFrame: obstacles.frame.widthPx * obstacles.frame.heightPx,
    cells: obstacles.frame.cells, cellsByClass: obstacles.cellsByClass,
    walkableCells: walkable.count, obstacleCells: obstacles.terrain.cells.length,
    holes: graph.holes.length, unplayed: geometry.unplayed.length,
    anchors: graph.nodes.length, edges: graph.edges.length
  };
}

/** Three invariants: the anchors are in the frame, the map is a partition, and the play order is S4's. */
export function checkCourse({ ledger, graph, holes, obstacles, summary }) {
  const frame = graph.frame;
  const inFrame = point => point[0] >= 0 && point[1] >= 0 && point[0] < frame.widthPx && point[1] < frame.heightPx;
  const checks = {
    anchorsInsideTheRaster: graph.nodes.every(node => inFrame(node.at) && node.cell >= 0 && node.cell < frame.cells),
    everyPixelLeavesOnce: ledger.pixels === ledger.pixelsInFrame,
    theMapIsAPartition: ledger.walkableCells + ledger.obstacleCells === ledger.cells &&
      Object.values(ledger.cellsByClass).reduce((sum, value) => sum + value, 0) === ledger.cells &&
      graph.walkable.cells.every((value, cell) => (value === 1) === (obstacles.cells[cell] !== 'terrain')),
    terrainIsWhatNoStageOwns: obstacles.pixelsByClass.terrain === obstacles.terrain.pixels.length,
    playOrderIsTheStraightHoleOrder: JSON.stringify(graph.order) === JSON.stringify(holes.map(hole => hole.number)),
    everyEdgeIsAnchored: graph.edges.every(edge => graph.nodes.some(node => node.id === edge.from) && graph.nodes.some(node => node.id === edge.to)),
    // No dogleg sneaks into the course by another door.
    everyDoglegIsNamedNotRouted: (summary?.unplayed?.doglegs ?? []).every(entry => !graph.holes.some(hole => hole.badge === entry.badge))
  };
  return { ...ledger, checks, balanced: Object.values(checks).every(Boolean) };
}

export function registerCourse(lab) {
  lab.register(labAddress('fn.Course.holeGeometry'), holeGeometry);
  lab.register(labAddress('fn.Course.obstacleMap'), obstacleMap);
  lab.register(labAddress('fn.Course.walkable'), walkableCells);
  lab.register(labAddress('fn.Course.graph'), courseGraph);
  lab.register(labAddress('fn.Course.summary'), courseSummary);
  lab.register('fn.lab.s7.accountcourse', accountCourse);
  lab.register('fn.lab.s7.checkcourse', checkCourse);
}

export const COURSE_CONTRACT = {
  stage: 'S7', name: 'Course',
  for: 'the course as a graph over the canonical raster, with the obstacle map derived from what the Stages left unclaimed',
  consumes: ['px.holes.straight', 'px.holes.unresolved', 'px.course.canonicalPixels', 'px.remaining.afterBadges', 'px.components', 'px.baskets', 'px.tees'].map(labAddress),
  produces: [COURSE_ADDRESSES.graph, COURSE_ADDRESSES.summary],
  ticks: ['Course.holeGeometry', 'Course.obstacleMap', 'Course.walkable', 'Course.graph', 'Course.summary'],
  invariants: ['anchorsInsideTheRaster', 'everyPixelLeavesOnce', 'theMapIsAPartition', 'terrainIsWhatNoStageOwns', 'playOrderIsTheStraightHoleOrder', 'everyEdgeIsAnchored', 'everyDoglegIsNamedNotRouted']
};

export function courseTicks({ course = 'labfixture', cellPx = CELL_PX } = {}) {
  return [
    { name: 'Course.holeGeometry', Calculations: [{ call: labAddress('fn.Course.holeGeometry'), with: { holes: labAddress('px.holes.straight'), unresolved: labAddress('px.holes.unresolved'), raster: labAddress('px.course.canonicalPixels') }, args: {}, into: COURSE_ADDRESSES.holes }] },
    { name: 'Course.obstacleMap', Calculations: [{ call: labAddress('fn.Course.obstacleMap'), with: { remaining: labAddress('px.remaining.afterBadges'), fields: labAddress('px.components'), baskets: labAddress('px.baskets'), tees: labAddress('px.tees'), raster: labAddress('px.course.canonicalPixels') }, args: { cellPx }, into: COURSE_ADDRESSES.obstacles }] },
    { name: 'Course.walkable', Calculations: [{ call: labAddress('fn.Course.walkable'), with: { obstacles: COURSE_ADDRESSES.obstacles }, args: {}, into: COURSE_ADDRESSES.walkable }] },
    { name: 'Course.graph', Calculations: [{ call: labAddress('fn.Course.graph'), with: { geometry: COURSE_ADDRESSES.holes, obstacles: COURSE_ADDRESSES.obstacles, walkable: COURSE_ADDRESSES.walkable }, args: { course }, into: COURSE_ADDRESSES.graph }] },
    { name: 'Course.summary', Calculations: [{ call: labAddress('fn.Course.summary'), with: { graph: COURSE_ADDRESSES.graph, geometry: COURSE_ADDRESSES.holes }, args: {}, into: COURSE_ADDRESSES.summary }] }
  ];
}

export function courseDocument(lab, options = {}) { return lab.document('S7.course', courseTicks(options)); }

/** `stages/S7.course.mmd`, compiled: the same Calculations over the same addresses in the same order. */
export function compiledCourse() { return compiledStage('S7.course', compileMermaidPcr, lowerToPql, labDocument); }

export function courseInvariantDocument(lab) {
  return lab.document('S7.course.invariants', [
    { name: 'AccountCourse', Calculations: [{ call: 'fn.lab.s7.accountcourse', with: { obstacles: COURSE_ADDRESSES.obstacles, walkable: COURSE_ADDRESSES.walkable, graph: COURSE_ADDRESSES.graph, geometry: COURSE_ADDRESSES.holes }, args: {}, into: COURSE_ADDRESSES.ledger }] },
    { name: 'CheckCourse', Calculations: [{ call: 'fn.lab.s7.checkcourse', with: { ledger: COURSE_ADDRESSES.ledger, graph: COURSE_ADDRESSES.graph, holes: labAddress('px.holes.straight'), obstacles: COURSE_ADDRESSES.obstacles, summary: COURSE_ADDRESSES.summary }, args: {}, into: COURSE_ADDRESSES.check }] }
  ]);
}

/** The Stage as the studio runs it; the demo decides how a course is drawn. */
export function s7CourseSpec(options = {}) {
  return {
    key: 's7-course', stage: 'S7', title: 'Course', composition: 'lab-s7-course',
    about: 'the holes as a graph over the canonical raster, with the obstacle map derived from every pixel no Stage object owns.',
    needs: COURSE_CONTRACT.consumes, produces: COURSE_CONTRACT.produces,
    register: registerCourse, ticks: lab => courseDocument(lab, options).Ticks
  };
}

export function runCourse(lab, options = {}) {
  const composition = courseDocument(lab, options), { run, receipt } = lab.run('S7.course', composition);
  const invariants = courseInvariantDocument(lab);
  lab.run('S7.course.invariants', invariants);
  return {
    run, receipt, composition, invariants,
    geometry: lab.get(COURSE_ADDRESSES.holes), obstacles: lab.get(COURSE_ADDRESSES.obstacles), walkable: lab.get(COURSE_ADDRESSES.walkable),
    graph: lab.get(COURSE_ADDRESSES.graph), summary: lab.get(COURSE_ADDRESSES.summary),
    ledger: lab.get(COURSE_ADDRESSES.ledger), check: lab.get(COURSE_ADDRESSES.check)
  };
}
