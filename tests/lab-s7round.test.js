/** S7 Pathfinding, the round half: the Round, searched over the course's walkable cells, against the straight route. */
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { createLab } from '../src/lab/lab.js';
import { labAddress } from '../src/lab/address.js';
import { structuralDigest } from '../src/lab/mermaid.js';
import { STAGES } from '../src/lab/source.js';
import { registerS0, runS0 } from '../src/lab/s0.js';
import { registerS1, runS1, s1YamlDocument } from '../src/lab/s1.js';
import { registerS2, runS2 } from '../src/lab/s2.js';
import { registerS3, runS3 } from '../src/lab/s3.js';
import { registerHolesNearest, runHolesNearest } from '../src/lab/holes-nearest.js';
import { registerCourse, runCourse, grid, cellOf } from '../src/lab/s7course.js';
import { registerRound, runRound, roundDocument, compiledRound, search, roundLegs, roundPath, checkRound, accountRound, ROUND_ADDRESSES, ROUND_CONTRACT, MOVES } from '../src/lab/s7round.js';
import { registerRoute, runRoute } from '../src/lab/route.js';
import { fixtureCapture } from '../src/lab/fixtures.js';

function round(options = { hole11: true, obstacle: true }) {
  const lab = createLab();
  registerS0(lab); registerS1(lab); registerS2(lab); registerS3(lab); registerHolesNearest(lab); registerCourse(lab); registerRound(lab); registerRoute(lab);
  const s0 = runS0(lab, { decoded: fixtureCapture(20260911, options), label: 'fixture' });
  runS1(lab, { croppedImage: s0.croppedImage, document: s1YamlDocument(lab), seedRaster: true });
  runS2(lab); runS3(lab); runHolesNearest(lab);
  const s5 = runCourse(lab);
  const straight = runRoute(lab, { course: 'labfixture' });
  return { lab, s5, straight, s6: runRound(lab, { compareWith: 'labfixture' }) };
}

/** A hand-built graph: one 8x8 room, a wall with a gap, two anchors. */
function room({ wall = true, sealed = false } = {}) {
  const frame = grid(128, 128, 16);
  const cells = new Array(frame.cells).fill('open');
  if (wall) for (let column = 0; column < (sealed ? frame.cols : frame.cols - 1); column++) cells[4 * frame.cols + column] = 'terrain';
  const walkable = cells.map(value => (value === 'terrain' ? 0 : 1));
  const from = { id: 'tee-1', kind: 'tee', hole: 1, at: [8, 8], cell: cellOf(frame, 8, 8) };
  const to = { id: 'basket-1', kind: 'basket', hole: 1, at: [8, 120], cell: cellOf(frame, 8, 120) };
  return {
    course: 'room', frame, order: [1], holes: [], walkableRule: 'test',
    nodes: [from, to], edges: [{ kind: 'play', hole: 1, from: 'tee-1', to: 'basket-1', straightLengthPx: 112, straightIsBlocked: wall }],
    obstacles: { classes: [], cellsByClass: {}, pixelsByClass: {}, cells, terrainCells: cells.reduce((list, value, cell) => (value === 'terrain' ? [...list, cell] : list), []) },
    walkable: { cells: walkable, count: walkable.reduce((sum, value) => sum + value, 0) }
  };
}

test('the round runs the document its contract declares, over the course graph', () => {
  const { lab, s6 } = round();
  assert.deepEqual(s6.composition.Ticks.map(tick => tick.name), ROUND_CONTRACT.ticks);
  assert.deepEqual(ROUND_CONTRACT.produces, ['px.exp.lab.round.legs', 'px.exp.lab.round.path', 'px.exp.lab.round.summary']);
  assert.deepEqual(s6.composition.Ticks[0].Calculations[0].with, { graph: labAddress('px.course.graph') });
  assert.deepEqual(s6.run.Ticks.map(tick => tick.Calculations[0].call), ['fn.lab.round.legs', 'fn.lab.round.path', 'fn.lab.round.summary']);
  for (const address of ROUND_CONTRACT.produces) assert.ok(lab.has(address), address);
});

test('S7.round.mmd compiles to the same document the round runs', () => {
  const lab = createLab(); registerRound(lab);
  const { document, local } = compiledRound();
  assert.deepEqual(local, []);
  assert.equal(structuralDigest(document), structuralDigest(roundDocument(lab)));
  for (const name of ['s7round.js']) {
    const source = readFileSync(join(STAGES, '..', name), 'utf8');
    assert.deepEqual([...source.matchAll(/^\s*import\s[^\n]*?from\s*'([^']+)'/gm)].map(match => match[1]).filter(specifier => specifier.startsWith('node:')), []);
  }
});

test('every leg is walked over cells, and no leg crosses an obstacle cell', () => {
  const { s5, s6 } = round();
  const obstacles = new Set(s5.graph.obstacles.terrainCells);
  assert.deepEqual(s6.legs.map(leg => `${leg.kind}:${leg.from.id}->${leg.to.id}`), ['play:tee-3->basket-2', 'walk:basket-2->tee-2', 'play:tee-2->basket-1']);
  for (const leg of s6.legs) {
    assert.equal(leg.reachable, true);
    assert.ok(leg.cells.length > 1);
    for (const cell of leg.cells) assert.ok(!obstacles.has(cell), `leg ${leg.from.id}->${leg.to.id} crosses obstacle cell ${cell}`);
    assert.equal(leg.cells[0], leg.from.cell);
    assert.equal(leg.cells.at(-1), leg.to.cell);
    assert.deepEqual(leg.points[0], leg.from.at);
    assert.deepEqual(leg.points.at(-1), leg.to.at);
  }
  assert.equal(s6.check.balanced, true);
  assert.deepEqual(Object.keys(s6.check.checks), ROUND_CONTRACT.invariants);
});

test('the two legs the course said were blocked are the two that bend, and they get longer', () => {
  const { s6 } = round();
  assert.deepEqual(s6.summary.legsThatHadToBend, ['walk:basket-2->tee-2', 'play:tee-2->basket-1']);
  for (const leg of s6.legs) if (leg.straightIsBlocked) assert.ok(leg.lengthPx > leg.straightLengthPx, `${leg.from.id}->${leg.to.id}`);
  assert.ok(s6.summary.detourPx > 0);
  assert.equal(s6.summary.walked, 3);
  assert.deepEqual(s6.summary.unreachable, []);
});

test('the round is one path: the legs chain, and the whole path is the legs end to end', () => {
  const { s6 } = round();
  const { path, legs } = s6;
  assert.deepEqual(path.waypoints.map(point => point.id), ['tee-3', 'basket-2', 'tee-2', 'basket-1']);
  assert.equal(path.cells.length, legs.reduce((sum, leg) => sum + leg.cells.length, 0) - (legs.length - 1));
  assert.equal(path.lengthPx, Math.round(legs.reduce((sum, leg) => sum + leg.lengthPx, 0) * 1000) / 1000);
  assert.equal(path.cost, legs.reduce((sum, leg) => sum + leg.cost, 0));
  assert.equal(Math.round((path.playLengthPx + path.walkLengthPx) * 1000) / 1000, path.lengthPx);
  assert.deepEqual(path.from, ['px.exp.lab.course.graph', 'px.exp.lab.course.walkable']);
});

test('a basket with no walkable path to it is reported unreachable, never straightened', () => {
  const graph = room({ sealed: true });
  const legs = roundLegs({ graph });
  assert.equal(legs[0].reachable, false);
  assert.deepEqual(legs[0].cells, []);
  assert.equal(legs[0].lengthPx, null);
  assert.match(legs[0].why, /no walkable path/);
  assert.ok(legs[0].reachedCells > 0, 'the search says what it could reach');
  const path = roundPath({ legs, graph });
  assert.equal(path.lengthPx, 0);
  assert.deepEqual(path.unreachable, [{ kind: 'play', hole: 1, from: 'tee-1', to: 'basket-1', why: legs[0].why }]);
  const ledger = accountRound({ legs, path, graph });
  assert.equal(checkRound({ ledger, legs, path, graph }).balanced, true);
  // The straight line is exactly what a route that did not look would have drawn.
  assert.equal(legs[0].straightLengthPx, 112);
});

test('the same room with a gap in the wall is walked through the gap', () => {
  const graph = room({ wall: true });
  const legs = roundLegs({ graph });
  assert.equal(legs[0].reachable, true);
  const wallRow = 4;
  const crossing = legs[0].cells.filter(cell => Math.floor(cell / graph.frame.cols) === wallRow);
  assert.deepEqual(crossing, [wallRow * graph.frame.cols + graph.frame.cols - 1], 'the one cell of the wall row that is open');
  assert.ok(legs[0].lengthPx > legs[0].straightLengthPx);
});

test('the search is a function of the map and the anchors: no clock, no random, same cells every time', () => {
  const graph = room();
  const once = roundLegs({ graph })[0].cells, twice = roundLegs({ graph })[0].cells;
  assert.deepEqual(once, twice);
  // And two independent runs of the whole Stage agree, board and all.
  const left = round(), right = round();
  assert.deepEqual(left.s6.legs.map(leg => leg.cells), right.s6.legs.map(leg => leg.cells));
  assert.equal(left.s6.path.lengthPx, right.s6.path.lengthPx);
  assert.equal(left.s6.path.cost, right.s6.path.cost);
});

test('a diagonal may not cut the corner between two obstacle cells', () => {
  const frame = grid(48, 48, 16), walkable = new Array(frame.cells).fill(1);
  walkable[cellOf(frame, 24, 8)] = 0; walkable[cellOf(frame, 8, 24)] = 0;
  const found = search(frame, walkable, cellOf(frame, 8, 8), cellOf(frame, 24, 24));
  assert.equal(found.cells, null, 'the only way through was the corner, and the corner is closed');
  assert.deepEqual(MOVES.slice(0, 4).map(move => move[2]), [10, 10, 10, 10]);
  assert.deepEqual(MOVES.slice(4).map(move => move[2]), [14, 14, 14, 14]);
  assert.throws(() => search(frame, walkable, -1, 0), /outside the/);
  assert.equal(search(frame, walkable, cellOf(frame, 24, 8), cellOf(frame, 8, 8)).why, 'an endpoint is an obstacle cell');
});

test('against the straight route: the same holes and anchors, and what the map costs', () => {
  const { s6, straight } = round();
  const comparison = s6.vsStraight;
  assert.equal(comparison.sameHoles, true);
  assert.equal(comparison.sameAnchors, true);
  assert.equal(comparison.straightTotalPx, straight.path.totalLengthPx);
  assert.ok(comparison.routedTotalPx > comparison.straightTotalPx);
  assert.equal(comparison.deltaPx, Math.round((comparison.routedTotalPx - comparison.straightTotalPx) * 1000) / 1000);
  // The straight route walked through the obstacle on exactly the legs S5 called blocked.
  assert.deepEqual(comparison.legsTheStraightRouteWalkedThroughAnObstacle, ['walk:basket-2->tee-2', 'play:tee-2->basket-1']);
  assert.ok(comparison.obstacleCellsTheStraightRouteCrosses > 0);
  for (const leg of comparison.legs) assert.ok(leg.detourRatio >= 1);
  // Even an unblocked leg pays for the grid: the cell path is not the straight line.
  const clear = comparison.legs.find(leg => leg.obstacleCellsTheStraightLineCrosses === 0);
  assert.ok(clear.detourRatio > 1 && clear.detourRatio < 1.2, `grid overhead ${clear.detourRatio}`);
});

test('with no obstacle drawn, no leg bends and the round costs what the straight route costs, within the grid', () => {
  const { s6 } = round({ hole11: true });
  assert.deepEqual(s6.summary.legsThatHadToBend, []);
  assert.equal(s6.check.balanced, true);
  assert.equal(s6.vsStraight.obstacleCellsTheStraightRouteCrosses, 0);
  assert.ok(s6.vsStraight.routedTotalPx < s6.vsStraight.straightTotalPx * 1.2);
});

test('all three round runs are pyto-run-record@1 records', () => {
  const { lab } = round();
  assert.deepEqual(lab.runRecord('S7.round').record.ticks.map(tick => tick.name), ROUND_CONTRACT.ticks);
  assert.equal(lab.runRecord('S7.round.invariants').record.ticks[1].invocations[0].actual_produces[0], ROUND_ADDRESSES.check);
  assert.equal(lab.runRecord('S7.vs-straight').record.ticks[0].invocations[0].actual_produces[0], ROUND_ADDRESSES.vsStraight);
});
