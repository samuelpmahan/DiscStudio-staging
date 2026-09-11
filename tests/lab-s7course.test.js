/** S7 Pathfinding, the course half: the Course as a graph over the canonical raster, and the obstacle map under it. */
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, readdirSync } from 'node:fs';
import { join } from 'node:path';
import { createLab } from '../src/lab/lab.js';
import { labAddress } from '../src/lab/address.js';
import { structuralDigest } from '../src/lab/mermaid.js';
import { STAGES } from '../src/lab/source.js';
import { STAGE_TEXT, readStageSource } from '../src/lab/stage-sources.js';
import { registerS0, runS0 } from '../src/lab/s0.js';
import { registerS1, runS1, s1YamlDocument } from '../src/lab/s1.js';
import { registerS2, runS2 } from '../src/lab/s2.js';
import { registerS3, runS3 } from '../src/lab/s3.js';
import { registerHolesNearest, runHolesNearest } from '../src/lab/holes-nearest.js';
import { registerCourse, runCourse, courseDocument, compiledCourse, holeGeometry, checkCourse, grid, cellOf, straightIsBlocked, COURSE_ADDRESSES, COURSE_CONTRACT, CLASSES, CELL_PX } from '../src/lab/s7course.js';
import { fixtureCapture, OBSTACLE } from '../src/lab/fixtures.js';

function course(options = { hole11: true, obstacle: true }) {
  const lab = createLab();
  registerS0(lab); registerS1(lab); registerS2(lab); registerS3(lab); registerHolesNearest(lab); registerCourse(lab);
  const s0 = runS0(lab, { decoded: fixtureCapture(20260911, options), label: 'fixture' });
  runS1(lab, { croppedImage: s0.croppedImage, document: s1YamlDocument(lab), seedRaster: true });
  const s2 = runS2(lab), s3 = runS3(lab), s4 = runHolesNearest(lab);
  return { lab, s0, s2, s3, s4, s5: runCourse(lab) };
}

test('the course runs the document its contract declares, over the holes and the Stage masks', () => {
  const { lab, s5 } = course();
  assert.deepEqual(s5.composition.Ticks.map(tick => tick.name), COURSE_CONTRACT.ticks);
  assert.deepEqual(COURSE_CONTRACT.produces, ['px.exp.lab.course.graph', 'px.exp.lab.course.summary']);
  assert.deepEqual(s5.composition.Ticks[1].Calculations[0].with, {
    remaining: labAddress('px.remaining.afterBadges'), fields: labAddress('px.components'),
    baskets: labAddress('px.baskets'), tees: labAddress('px.tees'), raster: labAddress('px.course.canonicalPixels')
  });
  assert.deepEqual(s5.run.Ticks.map(tick => tick.Calculations[0].call), ['fn.lab.course.holegeometry', 'fn.lab.course.obstaclemap', 'fn.lab.course.walkable', 'fn.lab.course.graph', 'fn.lab.course.summary']);
  for (const address of COURSE_CONTRACT.produces) assert.ok(lab.has(address), address);
});

test('S7.course.mmd compiles to the same document the course runs, and the embedded flowcharts are the files', () => {
  const lab = createLab(); registerCourse(lab);
  const { document, local } = compiledCourse();
  assert.deepEqual(local, []);
  assert.equal(structuralDigest(document), structuralDigest(courseDocument(lab)));
  assert.deepEqual(Object.keys(STAGE_TEXT).sort(), readdirSync(STAGES).sort());
  for (const name of Object.keys(STAGE_TEXT)) assert.equal(readStageSource(name), readFileSync(join(STAGES, name), 'utf8'), name);
  assert.throws(() => readStageSource('S9.mmd'), /not an embedded stage document/);
});

test('no invented Stage module reaches for node at import time', () => {
  for (const name of ['holes-nearest.js', 's7course.js', 'stage-sources.js']) {
    const source = readFileSync(join(STAGES, '..', name), 'utf8');
    const statics = [...source.matchAll(/^\s*import\s[^\n]*?from\s*'([^']+)'/gm)].map(match => match[1]);
    assert.deepEqual(statics.filter(specifier => specifier.startsWith('node:')), [], `${name} imports node at module scope`);
  }
});

test('a hole is a tee-to-basket vector and a length in raster px, and the play order is the holes order', () => {
  const { s4, s5 } = course();
  assert.deepEqual(s5.graph.order, [1, 10]);
  assert.deepEqual(s5.graph.order, s4.holes.filter(hole => hole.complete).map(hole => hole.number));
  assert.deepEqual(s5.geometry.incomplete, [{ number: 11, missing: ['basket'] }]);
  for (const hole of s5.graph.holes) {
    const source = s4.holes.find(entry => entry.number === hole.number);
    assert.deepEqual(hole.vector, [Math.round((source.basket.at[0] - source.tee.at[0]) * 1000) / 1000, Math.round((source.basket.at[1] - source.tee.at[1]) * 1000) / 1000]);
    assert.equal(hole.lengthPx, Math.round(Math.hypot(...hole.vector) * 1000) / 1000);
    assert.ok(hole.bearingDeg >= 0 && hole.bearingDeg < 360);
  }
  assert.equal(s5.summary.totalLengthPx, Math.round((s5.graph.holes[0].lengthPx + s5.graph.holes[1].lengthPx) * 1000) / 1000);
});

test('an anchor outside the canonical raster refuses the Stage', () => {
  const holes = [{ number: 1, complete: true, missing: [], badge: { id: 'badge-1' }, confidence: { value: 1 }, tee: { id: 't', at: [1, 1] }, basket: { id: 'b', at: [900, 1] } }];
  assert.throws(() => holeGeometry({ holes, raster: { widthPx: 100, heightPx: 100 } }), /leaves canonical raster/);
});

test('the obstacle map is a partition, and terrain is exactly what no Stage object owns', () => {
  const { s0, s2, s3, s5 } = course();
  const { obstacles } = s5, frame = obstacles.frame;
  assert.deepEqual(obstacles.classes, CLASSES);
  assert.equal(Object.values(obstacles.pixelsByClass).reduce((sum, value) => sum + value, 0), frame.widthPx * frame.heightPx);
  assert.equal(Object.values(obstacles.cellsByClass).reduce((sum, value) => sum + value, 0), frame.cells);
  assert.equal(s5.walkable.count + obstacles.terrain.cells.length, frame.cells);
  // The bar the fixture drew, and nothing else: every basket and tee pixel left through its own door.
  assert.equal(obstacles.pixelsByClass.terrain, OBSTACLE.width * OBSTACLE.height);
  assert.equal(obstacles.pixelsByClass.basket, s2.baskets.reduce((sum, basket) => sum + basket.px.length, 0));
  assert.equal(obstacles.pixelsByClass.tee, s3.tees.reduce((sum, tee) => sum + tee.px.length, 0));
  // The terrain cells are the bar's own cells, in the cropped frame.
  const cropped = grid(frame.widthPx, frame.heightPx, CELL_PX), top = OBSTACLE.y - s0.crop.insets.top;
  const expected = [];
  for (let row = Math.floor(top / CELL_PX); row <= Math.floor((top + OBSTACLE.height - 1) / CELL_PX); row++)
    for (let column = 0; column <= Math.floor((OBSTACLE.width - 1) / CELL_PX); column++) expected.push(row * cropped.cols + column);
  assert.deepEqual(obstacles.terrain.cells, expected);
  assert.equal(obstacles.terrain.cells.length, 34);
});

test('the walkable cells are every class but terrain, and the rule says why', () => {
  const { s5 } = course();
  assert.match(s5.walkable.rule, /every class but terrain/);
  s5.obstacles.cells.forEach((klass, cell) => assert.equal(s5.walkable.walkable[cell], klass === 'terrain' ? 0 : 1, `cell ${cell} is ${klass}`));
  // A leg has to be able to end where it is going: every anchor's own cell is walkable.
  for (const node of s5.graph.nodes) assert.equal(s5.walkable.walkable[node.cell], 1, node.id);
});

test('the course says which straight legs cannot be walked, and does not route around them', () => {
  const { s5 } = course();
  assert.deepEqual(s5.graph.edges.map(edge => `${edge.kind}:${edge.from}->${edge.to}`), ['play:tee-3->basket-2', 'walk:basket-2->tee-2', 'play:tee-2->basket-1']);
  assert.deepEqual(s5.graph.edges.map(edge => edge.straightIsBlocked), [false, true, true]);
  assert.deepEqual(s5.summary.blockedStraightLegs, ['walk:basket-2->tee-2', 'play:tee-2->basket-1']);
  // Nothing in the graph is a route: an edge carries its straight length only.
  for (const edge of s5.graph.edges) assert.equal(typeof edge.straightLengthPx, 'number');
  assert.ok(!Object.keys(s5.graph).includes('legs'));
});

test('with no obstacle drawn, the same course has no terrain and no blocked leg', () => {
  const { s5 } = course({ hole11: true });
  assert.equal(s5.obstacles.pixelsByClass.terrain, 0);
  assert.deepEqual(s5.obstacles.terrain.cells, []);
  assert.equal(s5.walkable.count, s5.obstacles.frame.cells);
  assert.deepEqual(s5.summary.blockedStraightLegs, []);
  assert.equal(s5.check.balanced, true);
});

test('the invariants balance, and a map that is not a partition is refused', () => {
  const { lab, s4, s5 } = course();
  assert.deepEqual(s5.invariants.Ticks.map(tick => tick.name), ['AccountCourse', 'CheckCourse']);
  assert.deepEqual(Object.keys(s5.check.checks), COURSE_CONTRACT.invariants);
  assert.equal(s5.check.balanced, true);
  assert.ok(lab.has(COURSE_ADDRESSES.check));
  const broken = { ...s5.graph, walkable: { ...s5.graph.walkable, cells: s5.graph.walkable.cells.map(() => 1) } };
  assert.equal(checkCourse({ ledger: s5.ledger, graph: broken, holes: s4.holes, obstacles: s5.obstacles }).checks.theMapIsAPartition, false);
  const reordered = { ...s5.graph, order: [10, 1] };
  assert.equal(checkCourse({ ledger: s5.ledger, graph: reordered, holes: s4.holes, obstacles: s5.obstacles }).checks.playOrderIsTheBadgeOrder, false);
});

test('a straight line is blocked when it crosses an obstacle cell, and the sampler catches a thin one', () => {
  const frame = grid(64, 64, 16), walkable = new Array(frame.cells).fill(1);
  walkable[cellOf(frame, 40, 8)] = 0;
  assert.equal(straightIsBlocked(frame, walkable, [8, 8], [56, 8]), true);
  assert.equal(straightIsBlocked(frame, walkable, [8, 40], [56, 40]), false);
});

test('both course runs are pyto-run-record@1 records', () => {
  const { lab } = course();
  assert.deepEqual(lab.runRecord('S7.course').record.ticks.map(tick => tick.name), COURSE_CONTRACT.ticks);
  assert.equal(lab.runRecord('S7.course.invariants').record.ticks[1].invocations[0].actual_produces[0], COURSE_ADDRESSES.check);
});
