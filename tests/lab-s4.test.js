/** S4 (invented here, in the LAB's own recovery shape): the objects an overlap hides, found again. */
import test from 'node:test';
import assert from 'node:assert/strict';
import { createLab } from '../src/lab/lab.js';
import { labAddress } from '../src/lab/address.js';
import { structuralDigest } from '../src/lab/mermaid.js';
import { registerS0, runS0 } from '../src/lab/s0.js';
import { registerS1, runS1, s1YamlDocument } from '../src/lab/s1.js';
import { registerS2, runS2 } from '../src/lab/s2.js';
import { registerS3, runS3 } from '../src/lab/s3.js';
import { registerS4, runS4, s4Document, compiledS4, checkRecovery, glyphFraction, S4_ADDRESSES, S4_CONTRACT, PLATE_KNOBS } from '../src/lab/s4.js';
import { fixtureCapture, fixtureBasis, OVERLAPS } from '../src/lab/fixtures.js';

const OVERLAPPED = { hole11: true, obstacle: true, overlaps: true };

function stages(options = OVERLAPPED) {
  const lab = createLab();
  registerS0(lab); registerS1(lab); registerS2(lab); registerS3(lab); registerS4(lab);
  const capture = fixtureCapture(20260911, options);
  const s0 = runS0(lab, { decoded: capture, label: 'fixture' });
  const s1 = runS1(lab, { croppedImage: s0.croppedImage, document: s1YamlDocument(lab), seedRaster: true });
  const s2 = runS2(lab), s3 = runS3(lab);
  return { lab, capture, s0, s1, s2, s3, s4: runS4(lab) };
}

test('S4 runs the document its contract declares, over the clean produce and the substrate', () => {
  const { lab, s4 } = stages();
  assert.deepEqual(s4.composition.Ticks.map(tick => tick.name), S4_CONTRACT.ticks);
  assert.deepEqual(S4_CONTRACT.produces, ['px.exp.lab.recovered.badges', 'px.exp.lab.recovered.baskets', 'px.exp.lab.recovered.tees', 'px.exp.lab.recovered.ledger']);
  assert.deepEqual(s4.run.Ticks.map(tick => tick.Calculations[0].call), ['fn.lab.recover.unclaimed', 'fn.lab.recover.badges', 'fn.lab.recover.baskets', 'fn.lab.recover.tees', 'fn.lab.recover.ledger']);
  for (const address of S4_CONTRACT.produces) assert.ok(lab.has(address), address);
});

test('S4.mmd compiles to the same document S4 runs', () => {
  const lab = createLab(); registerS4(lab);
  const { document, local } = compiledS4();
  assert.deepEqual(local, []);
  assert.equal(structuralDigest(document), structuralDigest(s4Document(lab)));
});

test('the overlap is what the clean detectors cannot survive: one object lost per Stage', () => {
  const clean = stages({ hole11: true, obstacle: true }), overlapped = stages();
  assert.deepEqual(clean.s1.badges.map(badge => badge.reading.value), ['11', '10', '01']);
  assert.equal(clean.s2.baskets.length, 2);
  assert.equal(clean.s3.tees.length, 3);
  // The same capture with the three overlaps drawn: S1 loses the badge whose
  // border was cut, S2 the basket whose body was fused, S3 the tee whose hole leaked.
  assert.deepEqual(overlapped.s1.badges.map(badge => badge.reading.value), ['10', '01']);
  assert.equal(overlapped.s2.baskets.length, 1);
  assert.equal(overlapped.s3.tees.length, 2);
  assert.equal(overlapped.capture.occluded.length, 3);
  assert.deepEqual(overlapped.capture.occluded.map(entry => entry.kind), ['badge', 'basket', 'tee']);
  for (const entry of overlapped.capture.occluded) assert.ok(entry.how.length > 20, entry.kind);
});

test('recovery puts each one back, by a named rule, with the evidence it stood on', () => {
  const { s4 } = stages();
  assert.deepEqual(s4.ledger.counts, {
    badge: { clean: 2, recovered: 1, total: 3, rejected: 5 },
    basket: { clean: 1, recovered: 1, total: 2, rejected: 5 },
    tee: { clean: 2, recovered: 1, total: 3, rejected: 5 }
  });
  assert.deepEqual(s4.ledger.recovered.map(entry => `${entry.kind}:${entry.basis}`), ['badge:dark-plate-recovery', 'basket:shell-recovery', 'tee:component-fallback']);
  for (const entry of s4.ledger.recovered) {
    assert.ok(entry.evidence.rule.length > 10, entry.kind);
    assert.ok(entry.overlappedBy.length > 0, `${entry.kind} names the structure it overlaps`);
  }
  assert.deepEqual(s4.ledger.bases, { badge: ['bright-family', 'dark-plate-recovery'], basket: ['body-family', 'shell-recovery'], tee: ['ring-family', 'component-fallback'] });
});

test('a badge recovered from its dark plate arrives read, not merely found', () => {
  const { s4 } = stages();
  const recovered = s4.badges.recovered[0];
  assert.equal(recovered.basis, 'dark-plate-recovery');
  assert.equal(recovered.reading.value, '11');
  assert.equal(recovered.reading.status, 'read');
  // The LAB's own knob is what accepted it: the plate interior carries glyph.
  assert.ok(recovered.evidence.glyphFraction >= PLATE_KNOBS.plateGlyphFractionMin);
  assert.ok(recovered.evidence.glyphFraction <= PLATE_KNOBS.plateGlyphFractionMax);
  assert.equal(recovered.evidence.digits, 2);
  assert.deepEqual(s4.badges.objects.map(badge => badge.reading.value), ['10', '01', '11']);
});

test('a basket is recovered from the shell S2 already measured, and a tee from its frame', () => {
  const { s2, s3, s4 } = stages();
  const basket = s4.baskets.recovered[0];
  assert.equal(basket.basis, 'shell-recovery');
  assert.deepEqual(basket.evidence.margins, [4, 4, 4, 4]);
  assert.ok(basket.evidence.brightInsidePx > 0, 'the occluded body is still bright material inside the shell');
  assert.deepEqual(basket.bbox.slice(2), s2.baskets[0].bbox.slice(2), "the recovered shell is the clean family's geometry exactly");
  const tee = s4.tees.recovered[0];
  assert.equal(tee.basis, 'component-fallback');
  assert.equal(tee.evidence.ring, null);
  assert.deepEqual(tee.bbox.slice(2), s3.tees[0].bbox.slice(2));
  assert.ok(Math.abs(tee.evidence.fill - tee.evidence.familyFill) <= 0.15);
});

test('recovery searches only what the clean path left, and says why it refused the rest', () => {
  const { s4 } = stages();
  assert.ok(s4.unclaimed.bright.length > 0 && s4.unclaimed.dark.length > 0);
  for (const group of [s4.badges, s4.baskets, s4.tees]) {
    for (const entry of group.rejected) assert.ok(entry.why.length > 0, JSON.stringify(entry.bbox));
    // Nothing is rejected for a reason the reader cannot read.
    for (const entry of group.rejected) for (const why of entry.why) assert.equal(typeof why, 'string');
  }
  // The obstacle bar is unclaimed dark structure, and it is refused as every kind.
  const bar = s4.unclaimed.dark.find(entry => entry.bbox[2] > 200);
  assert.ok(bar, 'the obstacle bar is unclaimed');
  assert.ok(s4.badges.rejected.some(entry => entry.bbox.join() === bar.bbox.join()));
  assert.ok(s4.baskets.rejected.some(entry => entry.bbox.join() === bar.bbox.join()));
});

test('the invariants balance, and recovery that replaced a clean object would be refused', () => {
  const { s4, s1 } = stages();
  assert.deepEqual(Object.keys(s4.check.checks), S4_CONTRACT.invariants);
  assert.equal(s4.check.balanced, true);
  const clean = { cleanBadges: s1.badges, cleanBaskets: [], cleanTees: [] };
  const moved = { ...s4.badges, objects: [{ ...s4.badges.objects[0], bbox: [0, 0, 1, 1] }, ...s4.badges.objects.slice(1)] };
  assert.equal(checkRecovery({ ledger: s4.ledger, badges: moved, baskets: s4.baskets, tees: s4.tees, ...clean, cleanBaskets: [], cleanTees: [] }).checks.everyCleanObjectSurvivesUnchanged, false);
  const onTop = { ...s4.tees, recovered: [{ ...s4.tees.recovered[0], bbox: s4.tees.clean[0].bbox }] };
  assert.equal(checkRecovery({ ledger: s4.ledger, badges: s4.badges, baskets: s4.baskets, tees: onTop, cleanBadges: s1.badges, cleanBaskets: [], cleanTees: [] }).checks.noRecoveredObjectSitsOnACleanOne, false);
});

test('with no overlap drawn, recovery recovers nothing and takes nothing away', () => {
  const { s4 } = stages({ hole11: true, obstacle: true });
  assert.deepEqual(s4.ledger.counts.badge, { clean: 3, recovered: 0, total: 3, rejected: 1 });
  // With nothing occluded the only unclaimed dark structure left is the obstacle bar.
  assert.equal(s4.unclaimed.dark.length, 1);
  assert.equal(s4.baskets.recovered.length, 0);
  assert.equal(s4.tees.recovered.length, 0);
  assert.equal(s4.check.balanced, true);
  assert.deepEqual(s4.ledger.bases, { badge: ['bright-family'], basket: ['body-family'], tee: ['ring-family'] });
});

test('the glyph fraction is the LAB measurement, over the plate interior only', () => {
  const mask = { data: new Uint8Array(100), width: 10, height: 10 };
  for (let index = 0; index < 100; index++) mask.data[index] = 1;
  const component = { bboxX: 0, bboxY: 0, bboxW: 10, bboxH: 10 };
  assert.deepEqual(glyphFraction(component, mask, 10, 10, 4), { interior: 4, glyph: 4, fraction: 1 });
  assert.equal(glyphFraction(component, { ...mask, data: new Uint8Array(100) }, 10, 10, 4).fraction, 0);
});

test('the fixture records the overlaps in its basis, and both S4 runs are records', () => {
  const basis = fixtureBasis({ hole11: true, obstacle: true, overlaps: true });
  assert.equal(basis.elements.length, 7);
  assert.ok(basis.elements.some(element => element.what === 'the three overlaps'));
  assert.equal(OVERLAPS.teeNotch.width, 10, 'wider than S3 can dilate closed');
  const { lab } = stages();
  assert.deepEqual(lab.runRecord('S4').record.ticks.map(tick => tick.name), S4_CONTRACT.ticks);
  assert.equal(lab.runRecord('S4.invariants').record.ticks[0].invocations[0].actual_produces[0], S4_ADDRESSES.check);
});
