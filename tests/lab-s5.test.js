/** S5 (invented here): the tee points at its badge, and the pointing end is read off the pad. */
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
import { registerS5, runS5, s5Document, compiledS5, teePointing, castRays, teeBadgeRays, brightCentroid, S5_ADDRESSES, S5_CONTRACT, MIN_LEAN_PX } from '../src/lab/s5.js';
import { fixtureCapture, ALIGNED, TEE_NOSE } from '../src/lab/fixtures.js';

export const COURSE = { obstacle: true, aligned: true };

export function stages(options = COURSE) {
  const lab = createLab();
  registerS0(lab); registerS1(lab); registerS2(lab); registerS3(lab); registerS4(lab); registerS5(lab);
  const s0 = runS0(lab, { decoded: fixtureCapture(20260911, options), label: 'fixture' });
  runS1(lab, { croppedImage: s0.croppedImage, document: s1YamlDocument(lab), seedRaster: true });
  runS2(lab); runS3(lab);
  const s4 = runS4(lab);
  return { lab, s0, s4, s5: runS5(lab) };
}

test('S5 runs the document its contract declares, over the recovered Parts and not the raw ones', () => {
  const { lab, s5 } = stages();
  assert.deepEqual(s5.composition.Ticks.map(tick => tick.name), S5_CONTRACT.ticks);
  assert.deepEqual(S5_CONTRACT.produces, ['px.exp.lab.teebadge.rays']);
  assert.deepEqual(s5.composition.Ticks[0].Calculations[0].with, { tees: labAddress('px.recovered.tees'), fields: labAddress('px.components') });
  assert.equal(s5.composition.Ticks[1].Calculations[0].with.badges, labAddress('px.recovered.badges'));
  assert.deepEqual(s5.run.Ticks.map(tick => tick.Calculations[0].call), ['fn.lab.tee.pointing', 'fn.lab.tee.castray', 'fn.lab.teebadge.pair']);
  assert.ok(lab.has(S5_ADDRESSES.rays));
});

test('S5.mmd compiles to the same document S5 runs', () => {
  const lab = createLab(); registerS5(lab);
  const { document, local } = compiledS5();
  assert.deepEqual(local, []);
  assert.equal(structuralDigest(document), structuralDigest(s5Document(lab)));
});

test('the pointing end is measured, not assumed: the pad leans toward its nose', () => {
  const { s5 } = stages();
  const [pointing, ...symmetric] = s5.pointing.tees;
  assert.deepEqual(pointing.pointing, [0, 1], 'the nose is on the bottom end, so the tee points down');
  assert.ok(pointing.lean.alongAxisPx >= MIN_LEAN_PX, `lean ${pointing.lean.alongAxisPx}`);
  // The lean is the nose's own material pulling the centroid off the ring centre.
  assert.equal(pointing.bbox[3], 26 + TEE_NOSE.height);
  for (const tee of symmetric) {
    assert.equal(tee.pointing, null);
    assert.equal(tee.lean.alongAxisPx, 0);
    assert.match(tee.why, /symmetric and no end of it is the front/);
  }
});

test('the ray finds the badge the tee points at, and its distance is the distance down the line', () => {
  const { s5 } = stages();
  const ray = s5.rays.rays[0];
  assert.equal(ray.badge.reading, ALIGNED.reading);
  assert.ok(ray.distancePx > 0);
  // The badge is straight down the tee's own axis: the entry point keeps the tee's x.
  assert.ok(Math.abs(ray.entryAt[0] - ray.origin[0]) < 1e-9);
  assert.ok(ray.entryAt[1] > ray.origin[1]);
  assert.equal(s5.rays.paired, 1);
  assert.deepEqual(s5.rays.contested, []);
});

test('a symmetric pad is refused, not paired by proximity', () => {
  const { s5 } = stages();
  assert.equal(s5.rays.unpointed.length, 2);
  for (const entry of s5.rays.unpointed) assert.equal(s5.rays.rays.find(ray => ray.tee === entry.tee).badge, null);
  // Two badges are left with no ray at all: they are S6's business, not S5's.
  assert.deepEqual(s5.rays.badgesWithNoRay.map(badge => badge.reading), ['10', '01']);
});

test('a ray that leaves the raster says so, and two rays on one badge contest it', () => {
  const pointing = {
    rule: 'test', minLeanPx: 0.5,
    tees: [
      { id: 'tee-1', basis: 'ring-family', bbox: [0, 0, 4, 4], at: [10, 10], centroid: [10, 12], axisAngleDeg: 90, lean: { alongAxisPx: 2 }, pointing: [0, 1], why: null },
      { id: 'tee-2', basis: 'ring-family', bbox: [0, 0, 4, 4], at: [10, 60], centroid: [10, 58], axisAngleDeg: 270, lean: { alongAxisPx: 2 }, pointing: [0, -1], why: null },
      { id: 'tee-3', basis: 'ring-family', bbox: [0, 0, 4, 4], at: [90, 10], centroid: [92, 10], axisAngleDeg: 0, lean: { alongAxisPx: 2 }, pointing: [1, 0], why: null }
    ]
  };
  const badges = { objects: [{ id: 'badge-1', bbox: [5, 30, 10, 10], reading: { value: '3' }, basis: 'bright-family' }] };
  const hits = castRays({ pointing, badges, raster: { widthPx: 100, heightPx: 100 } });
  assert.deepEqual(hits.hits.map(hit => hit.badge), ['badge-1', 'badge-1', null]);
  assert.match(hits.hits[2].why, /left the 100x100 raster/);
  const rays = teeBadgeRays({ pointing, hits, badges });
  assert.deepEqual(rays.contested, [{ badge: 'badge-1', tees: ['tee-1', 'tee-2'] }]);
  assert.equal(rays.paired, 0, 'a contested badge is reported, never split');
  for (const ray of rays.rays.slice(0, 2)) assert.match(ray.why, /two tees point at badge-1/);
});

test('the invariants balance, and the empty course is empty rather than wrong', () => {
  const { s5 } = stages();
  assert.deepEqual(Object.keys(s5.check.checks), S5_CONTRACT.invariants);
  assert.equal(s5.check.balanced, true);
  const empty = teePointing({ tees: { objects: [] }, fields: { bright: { mask: { data: new Uint8Array(4), width: 2, height: 2 } } } });
  assert.deepEqual(empty.tees, []);
  assert.deepEqual(brightCentroid([0, 0, 2, 2], { data: new Uint8Array(4), width: 2, height: 2 }), { at: null, count: 0 });
});

test('both S5 runs are pyto-run-record@1 records', () => {
  const { lab } = stages();
  assert.deepEqual(lab.runRecord('S5').record.ticks.map(tick => tick.name), S5_CONTRACT.ticks);
  assert.equal(lab.runRecord('S5.invariants').record.ticks[0].invocations[0].actual_produces[0], S5_ADDRESSES.check);
});
