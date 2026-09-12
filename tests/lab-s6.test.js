/** S6 (invented here): three points make a line -- continue the ray and the basket is there, or it is a dogleg. */
import test from 'node:test';
import assert from 'node:assert/strict';
import { createLab } from '../src/lab/lab.js';
import { labAddress } from '../src/lab/address.js';
import { structuralDigest } from '../src/lab/mermaid.js';
import { registerS0, runS0 } from '../src/lab/s0.js';
import { registerS1, runS1, s1YamlDocument } from '../src/lab/s1.js';
import { registerS2, runS2 } from '../src/lab/s2.js';
import { registerS3, runS3 } from '../src/lab/s3.js';
import { registerS4, runS4 } from '../src/lab/s4.js';
import { registerS5, runS5 } from '../src/lab/s5.js';
import { registerS6, runS6, s6Document, compiledS6, continueRay, straightHoles, checkStraight, residualOf, S6_ADDRESSES, S6_CONTRACT, MAX_RESIDUAL_PX } from '../src/lab/s6.js';
import { fixtureCapture, ALIGNED } from '../src/lab/fixtures.js';

function course(options = { obstacle: true, aligned: true }) {
  const lab = createLab();
  registerS0(lab); registerS1(lab); registerS2(lab); registerS3(lab); registerS4(lab); registerS5(lab); registerS6(lab);
  const s0 = runS0(lab, { decoded: fixtureCapture(20260911, options), label: 'fixture' });
  runS1(lab, { croppedImage: s0.croppedImage, document: s1YamlDocument(lab), seedRaster: true });
  runS2(lab); runS3(lab);
  const s4 = runS4(lab), s5 = runS5(lab);
  return { lab, s0, s4, s5, s6: runS6(lab) };
}

test('S6 runs the document its contract declares, over the rays and the recovered baskets', () => {
  const { lab, s6 } = course();
  assert.deepEqual(s6.composition.Ticks.map(tick => tick.name), S6_CONTRACT.ticks);
  assert.deepEqual(S6_CONTRACT.produces, ['px.exp.lab.holes.straight', 'px.exp.lab.holes.unresolved']);
  assert.deepEqual(s6.composition.Ticks[0].Calculations[0].with, { rays: labAddress('px.teebadge.rays'), baskets: labAddress('px.recovered.baskets') });
  assert.deepEqual(s6.run.Ticks.map(tick => tick.Calculations[0].call), ['fn.lab.hole.continueray', 'fn.lab.hole.straight', 'fn.lab.hole.unresolved']);
  for (const address of S6_CONTRACT.produces) assert.ok(lab.has(address), address);
});

test('S6.mmd compiles to the same document S6 runs', () => {
  const lab = createLab(); registerS6(lab);
  const { document, local } = compiledS6();
  assert.deepEqual(local, []);
  assert.equal(structuralDigest(document), structuralDigest(s6Document(lab)));
});

test('the hole is the three points on one line: tee, badge, basket, with the residual to prove it', () => {
  const { s6 } = course();
  assert.equal(s6.holes.length, 1);
  const [hole] = s6.holes;
  assert.equal(hole.reading, ALIGNED.reading);
  assert.equal(hole.number, 11);
  assert.equal(hole.basis, 'tee-badge-ray-continued');
  assert.ok(hole.residualPx <= MAX_RESIDUAL_PX);
  assert.ok(hole.teeToBasketPx > hole.teeToBadgePx, 'the basket is beyond the badge on the same ray');
  assert.deepEqual(hole.direction, [0, 1]);
  assert.equal(hole.has.continueRay.fn, 'fn.lab.hole.continueray');
});

test('a badge no ray reaches is a dogleg, named and left alone', () => {
  const { s4, s6 } = course();
  assert.equal(s6.unresolved.doglegs.length, 2);
  assert.deepEqual(s6.unresolved.doglegs.map(entry => entry.reading), ['10', '01']);
  for (const dogleg of s6.unresolved.doglegs) assert.match(dogleg.why, /no tee points at this badge/);
  assert.deepEqual(s6.unresolved.counts, { badges: s4.badges.objects.length, straight: 1, doglegs: 2 });
  // The baskets those holes would have used are listed too, not silently dropped.
  assert.equal(s6.unresolved.baskets.length, 2);
  assert.equal(s6.unresolved.tees.length, 2);
});

test('a basket off the line is refused however close it is', () => {
  const rays = { rays: [{ tee: 'tee-1', teeBasis: 'ring-family', origin: [10, 10], direction: [0, 1], axisAngleDeg: 90, lean: { alongAxisPx: 2 }, badge: { id: 'badge-1', bbox: [5, 20, 10, 10], at: [10, 25], reading: '7', basis: 'bright-family' }, distancePx: 15, why: null }], unpointed: [], missed: [] };
  const near = { objects: [{ id: 'basket-1', bbox: [40, 40, 10, 10], basis: 'body-family' }] };
  const hits = continueRay({ rays, baskets: near, maxResidualPx: MAX_RESIDUAL_PX });
  // The ray runs straight down x=10; a basket at x=45 is never entered at all.
  assert.equal(hits.hits[0].basket, null);
  assert.match(hits.hits[0].why, /entered no basket: this hole bends/);
  assert.deepEqual(straightHoles({ hits, rays }), []);
  // And one that IS entered but sits off the line is refused by the residual.
  const wide = { objects: [{ id: 'basket-1', bbox: [5, 60, 40, 10], basis: 'body-family' }] };
  const offLine = continueRay({ rays, baskets: wide, maxResidualPx: 2 });
  assert.equal(offLine.hits[0].basket, 'basket-1');
  assert.equal(offLine.hits[0].straight, false);
  assert.match(offLine.hits[0].why, /off the tee-to-badge line/);
  assert.deepEqual(straightHoles({ hits: offLine, rays }), []);
});

test('the residual is the perpendicular distance to the ray, and it is zero on the line', () => {
  assert.equal(residualOf([0, 0], [0, 1], [0, 50]), 0);
  assert.equal(residualOf([0, 0], [0, 1], [7, 50]), 7);
  assert.equal(residualOf([0, 0], [1, 0], [50, 3]), 3);
});

test('the invariants balance, and a hole whose basket is behind its badge would be refused', () => {
  const { s4, s6 } = course();
  assert.deepEqual(Object.keys(s6.check.checks), S6_CONTRACT.invariants);
  assert.equal(s6.check.balanced, true);
  const behind = s6.holes.map(hole => ({ ...hole, teeToBasketPx: hole.teeToBadgePx - 1 }));
  const args = { unresolved: s6.unresolved, hits: s6.hits, badges: s4.badges, baskets: s4.baskets };
  assert.equal(checkStraight({ holes: behind, ...args }).checks.theBasketIsBeyondTheBadge, false);
  const off = s6.holes.map(hole => ({ ...hole, residualPx: MAX_RESIDUAL_PX + 1 }));
  assert.equal(checkStraight({ holes: off, ...args }).checks.threePointsAreOnALine, false);
});

test('with no pointing tee drawn, nothing is straight and every badge is a dogleg', () => {
  const { s4, s6 } = course({ hole11: true, obstacle: true });
  assert.deepEqual(s6.holes, []);
  assert.equal(s6.unresolved.doglegs.length, s4.badges.objects.length);
  assert.equal(s6.check.balanced, true);
});

test('both S6 runs are pyto-run-record@1 records', () => {
  const { lab } = course();
  assert.deepEqual(lab.runRecord('S6').record.ticks.map(tick => tick.name), S6_CONTRACT.ticks);
  assert.equal(lab.runRecord('S6.invariants').record.ticks[0].invocations[0].actual_produces[0], S6_ADDRESSES.check);
});
