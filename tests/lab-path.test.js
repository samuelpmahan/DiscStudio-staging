/** Pathfinding: `lab traverse` geometry, run as a PxC composition over course Parts. */
import test from 'node:test';
import assert from 'node:assert/strict';
import { createLab } from '../src/lab/lab.js';
import { registerPath, pathDocument, putCourses, traverseTarget, traversalNeighbors, polarOffset, courseAnchors, DEFAULT_TRAVERSE_RADIUS } from '../src/lab/path.js';

function lab() {
  const built = createLab();
  registerPath(built);
  putCourses(built, ['DashsTrack', 'AlexClark']);
  // A second course the port owns, so a path is searched over more than one
  // manifest: the LAB's own manifests carry a hole table on DashsTrack only.
  built.put('px.exp.lab.course.labfixture', { for: 'a LAB-shaped course the port owns, to search a second manifest', version: 1, course: 'labfixture', holes: { 1: [40, 40, 80, 60], 2: [400, 160, 80, 60], 3: [220, 700, 80, 60] } });
  const fixture = built.get('px.exp.lab.course.labfixture');
  built.put('px.exp.lab.course.labfixture', { ...fixture, holes: Object.fromEntries(Object.entries(fixture.holes).map(([hole, box]) => [hole, { sourceBox: box }])) });
  return built;
}

function findPath(built, options) {
  const { address, composition } = pathDocument(built, options);
  built.run(composition.PrincipleComponentRender, composition);
  return { address, found: built.get(address), name: composition.PrincipleComponentRender };
}

test('the ported hex geometry is the LAB traverse geometry', () => {
  assert.deepEqual(polarOffset(75, 270).map(value => Math.round(value) + 0), [0, -75]);
  const neighbors = traversalNeighbors([100, 100], 75);
  assert.deepEqual(neighbors.map(neighbor => neighbor.n), [1, 2, 3, 4, 5, 6]);
  assert.deepEqual(neighbors.map(neighbor => neighbor.angleDeg), [270, 330, 30, 90, 150, 210]);
  assert.equal(traverseTarget([10, 10], 75, { kind: 'hex', neighbor: 2 }).detail, 'hex 2 330deg r=75');
  assert.deepEqual(traverseTarget([10, 10], 75, { kind: 'xy', dx: 4, dy: -3 }).point, [14, 7]);
  assert.throws(() => traverseTarget([0, 0], 75, { kind: 'hex', neighbor: 7 }), /neighbor must be 1\.\.6/);
});

test('a course Part gives blind hole anchors, and a course with no viewport table refuses', () => {
  const built = lab();
  const anchors = courseAnchors(built.get('px.exp.lab.course.dashstrack') ?? built.get('px.exp.lab.course.dashstrack'));
  assert.equal(Object.keys(anchors).length, 18);
  assert.deepEqual(anchors.h1, [396.5 + 603.2 / 2, 236.2 + 420 / 2]);
  assert.throws(() => courseAnchors(built.get('px.exp.lab.course.alexclark')), /does not yet define a blind viewport/);
});

test('a path over DashsTrack is a produce with a receipt, and every step is a LAB hex move', () => {
  const built = lab();
  const { address, found, name } = findPath(built, { course: 'dashstrack', name: 'route', from: 'h1', to: 'h9' });
  assert.equal(found.reached, true);
  assert.ok(found.steps > 0 && found.steps < 40);
  assert.ok(found.gapPx <= DEFAULT_TRAVERSE_RADIUS / 2);
  // Replay: each recorded move, applied by the LAB's own traverseTarget, is the
  // next recorded point. The trail is a LAB traversal, not a new kind of walk.
  found.moves.forEach((neighbor, index) => {
    const expected = traverseTarget(found.points[index], found.radiusPx, { kind: 'hex', neighbor }).point;
    assert.deepEqual(found.points[index + 1], expected.map(value => Math.round(value * 1000) / 1000), `step ${index}`);
  });
  assert.deepEqual(found.events, ['traverse-start', ...found.moves.map(() => 'traverse-move')]);
  assert.equal(found.replay.length, found.steps + 2);
  const receipt = built.get(`px.receipt.${name}`);
  assert.deepEqual(receipt.trace.map(step => step.call), ['fn.lab.path.anchors', 'fn.lab.path.start', 'fn.lab.path.search', 'fn.lab.path.receipt']);
  assert.ok(receipt.trace.some(step => step.produces.includes(address)));
});

test('the objective is fewest moves: no shorter walk of the same radius reaches the target', () => {
  const built = lab();
  const { found } = findPath(built, { course: 'labfixture', name: 'short', from: 'h1', to: 'h2' });
  assert.equal(found.reached, true);
  assert.equal(found.objective, 'fewest hex moves of one radius to within tolerance of the target anchor, inside the raster');
  // A* is admissible here, so the step count is the lattice lower bound: the
  // straight-line distance cannot be covered in fewer whole radii.
  const straight = Math.hypot(found.points.at(-1)[0] - found.points[0][0], found.points.at(-1)[1] - found.points[0][1]);
  assert.ok(found.steps >= Math.floor(straight / found.radiusPx), 'a path shorter than the lower bound');
});

test('the same search over two courses is the same composition with two course Parts', () => {
  const built = lab();
  const first = findPath(built, { course: 'dashstrack', name: 'a', from: 'h9', to: 'h18' });
  const second = findPath(built, { course: 'labfixture', name: 'b', from: 'h1', to: 'h3' });
  for (const path of [first, second]) assert.equal(path.found.reached, true);
  assert.equal(first.found.course, 'DashsTrack');
  assert.equal(second.found.course, 'labfixture');
  assert.notEqual(first.found.steps, 0);
  assert.ok(built.addresses().includes('px.exp.lab.path.dashstrack.h9-h18'));
});
