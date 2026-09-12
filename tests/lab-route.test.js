/** Pathfinding on the Stage outputs: the course, not a hex walk. */
import test from 'node:test';
import assert from 'node:assert/strict';
import { createLab } from '../src/lab/lab.js';
import { labAddress } from '../src/lab/address.js';
import { registerS0, runS0 } from '../src/lab/s0.js';
import { registerS1, runS1, s1YamlDocument } from '../src/lab/s1.js';
import { registerS2, runS2 } from '../src/lab/s2.js';
import { registerS3, runS3 } from '../src/lab/s3.js';
import { registerRoute, runRoute, routeDocument, order, route, ROUTE_ADDRESSES } from '../src/lab/route.js';
import { fixtureCapture } from '../src/lab/fixtures.js';

function played() {
  const lab = createLab();
  registerS0(lab); registerS1(lab); registerS2(lab); registerS3(lab); registerRoute(lab);
  const capture = fixtureCapture();
  const s0 = runS0(lab, { decoded: capture, label: 'fixture' });
  runS1(lab, { croppedImage: s0.croppedImage, document: s1YamlDocument(lab), seedRaster: true });
  runS2(lab); runS3(lab);
  return { lab, capture, s0, round: runRoute(lab, { course: 'labfixture' }) };
}

test('the route is a composition over Stage Parts, not over the course manifest', () => {
  const { lab, round } = played();
  const { composition } = routeDocument(lab, { course: 'labfixture' });
  assert.deepEqual(composition.Ticks.map(tick => tick.name), ['Anchors', 'Order', 'Route', 'Settle']);
  assert.deepEqual(composition.Ticks[0].Calculations[0].with, {
    badges: labAddress('px.badges.objects'), baskets: labAddress('px.baskets'), tees: labAddress('px.tees'), raster: labAddress('px.course.canonicalPixels')
  });
  assert.deepEqual(round.path.from, ['px.exp.lab.badges.objects', 'px.exp.lab.baskets', 'px.exp.lab.tees']);
  assert.equal(round.address, 'px.exp.lab.route.labfixture');
});

test('the holes are played in badge order, which is not their order in the raster', () => {
  const { lab, round } = played();
  assert.deepEqual(round.path.holes.map(hole => hole.number), [1, 10]);
  const anchors = lab.get(ROUTE_ADDRESSES.anchors);
  // Badge "10" sits higher in the raster than badge "01"; the reading decides.
  assert.ok(anchors.badges[0].at[1] < anchors.badges[1].at[1]);
  assert.deepEqual(anchors.badges.map(badge => badge.reading), ['10', '01']);
  assert.deepEqual(round.path.holes.map(hole => hole.tee), ['tee-2', 'tee-1']);
  assert.deepEqual(round.path.holes.map(hole => hole.basket), ['basket-2', 'basket-1']);
});

test('each hole takes the nearest free tee and basket, and no anchor is used twice', () => {
  const { lab, round } = played();
  const bound = lab.get(ROUTE_ADDRESSES.order);
  assert.deepEqual(bound.unbound, { tees: [], baskets: [] });
  assert.deepEqual(bound.incomplete, []);
  const used = round.path.holes.flatMap(hole => [hole.tee, hole.basket]);
  assert.equal(new Set(used).size, used.length);
  for (const hole of bound.holes) {
    const others = bound.holes.filter(other => other !== hole);
    for (const other of others) assert.ok(hole.tee.gapFromBadgePx <= Math.hypot(...[0, 1].map(axis => other.tee.at[axis] - hole.at[axis])) + 1e-9, 'a nearer free tee was left unbound');
  }
});

test('the legs chain: tee to basket, basket to the next tee, and the lengths add up', () => {
  const { round } = played();
  const { legs, waypoints } = round.path;
  assert.deepEqual(legs.map(leg => leg.kind), ['play', 'walk', 'play']);
  assert.equal(waypoints.length, legs.length + 1);
  legs.forEach((leg, index) => {
    assert.deepEqual(leg.from.at.map(value => Math.round(value * 1000) / 1000), waypoints[index].at);
    assert.deepEqual(leg.to.at.map(value => Math.round(value * 1000) / 1000), waypoints[index + 1].at);
    assert.ok(leg.lengthPx > 0);
  });
  assert.equal(Math.round((round.path.playLengthPx + round.path.walkLengthPx) * 1000) / 1000, round.path.totalLengthPx);
  // Every leg of a hole named `play` runs between that hole's own anchors.
  const holes = new Map(round.path.holes.map(hole => [hole.number, hole]));
  for (const leg of legs.filter(leg => leg.kind === 'play')) {
    assert.equal(leg.from.id, holes.get(leg.hole).tee);
    assert.equal(leg.to.id, holes.get(leg.hole).basket);
  }
});

test('a badge S1 could not read takes no turn, and is reported rather than guessed', () => {
  const anchors = {
    frame: { width: 100, height: 100 },
    badges: [{ id: 'b1', reading: '2', status: 'read', bbox: [0, 0, 4, 4], at: [2, 2] }, { id: 'b2', reading: null, status: 'unread', bbox: [50, 50, 4, 4], at: [52, 52] }],
    baskets: [{ id: 'basket-1', bbox: [0, 0, 2, 2], at: [10, 10] }],
    tees: [{ id: 'tee-1', bbox: [0, 0, 2, 2], at: [4, 4] }, { id: 'tee-2', bbox: [0, 0, 2, 2], at: [60, 60] }]
  };
  const bound = order({ anchors });
  assert.deepEqual(bound.holes.map(hole => hole.number), [2]);
  assert.deepEqual(bound.unreadable, ['b2']);
  assert.deepEqual(bound.unbound.tees, ['tee-2']);
  assert.deepEqual(bound.incomplete, []);
});

test('an anchor outside the canonical raster refuses the route', () => {
  const anchors = { frame: { width: 100, height: 100 }, badges: [], baskets: [], tees: [] };
  const holes = [{ number: 1, badge: 'b1', at: [1, 1], tee: { id: 't', at: [1, 1] }, basket: { id: 'k', at: [500, 1] } }];
  assert.throws(() => route({ order: { holes, unreadable: [], unbound: { tees: [], baskets: [] }, incomplete: [] }, anchors }), /leaves canonical raster/);
});

test('the path is a produce with a receipt and a run record', () => {
  const { lab, round } = played();
  const settle = round.receipt.trace.at(-1);
  assert.equal(settle.tick, 'Settle');
  assert.ok(settle.produces.includes(round.address));
  const { record } = lab.runRecord(round.composition.PrincipleComponentRender);
  assert.deepEqual(record.ticks.map(tick => tick.name), ['Anchors', 'Order', 'Route', 'Settle']);
  assert.equal(record.ticks[3].invocations[0].actual_produces[0], round.address);
});
