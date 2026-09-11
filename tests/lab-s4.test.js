/** S4 (invented here, in the LAB's stage grammar): Holes, and the invariants that are its oracle. */
import test from 'node:test';
import assert from 'node:assert/strict';
import { createLab } from '../src/lab/lab.js';
import { labAddress } from '../src/lab/address.js';
import { structuralDigest } from '../src/lab/mermaid.js';
import { registerS0, runS0 } from '../src/lab/s0.js';
import { registerS1, runS1, s1YamlDocument } from '../src/lab/s1.js';
import { registerS2, runS2 } from '../src/lab/s2.js';
import { registerS3, runS3 } from '../src/lab/s3.js';
import { registerS4, runS4, s4Document, compiledS4, readNumbers, bindAnchors, assembleHoles, unplaced, checkHoles, accountHoles, S4_ADDRESSES, S4_CONTRACT } from '../src/lab/s4.js';
import { fixtureCapture, fixtureBasis } from '../src/lab/fixtures.js';

/** The course fixture: three badges, three tees, two baskets -- hole 11's basket is not there. */
function course(options = { hole11: true, obstacle: true }) {
  const lab = createLab();
  registerS0(lab); registerS1(lab); registerS2(lab); registerS3(lab); registerS4(lab);
  const capture = fixtureCapture(20260911, options);
  const s0 = runS0(lab, { decoded: capture, label: 'fixture' });
  runS1(lab, { croppedImage: s0.croppedImage, document: s1YamlDocument(lab), seedRaster: true });
  const s2 = runS2(lab), s3 = runS3(lab);
  return { lab, capture, s0, s2, s3, s4: runS4(lab) };
}

test('S4 runs the document its contract declares, over the produce Parts of S1, S2 and S3', () => {
  const { lab, s4 } = course();
  const document = s4Document(lab);
  assert.deepEqual(document.Ticks.map(tick => tick.name), S4_CONTRACT.ticks);
  assert.deepEqual(S4_CONTRACT.consumes, ['px.exp.lab.badges.objects', 'px.exp.lab.tees', 'px.exp.lab.baskets']);
  assert.deepEqual(S4_CONTRACT.produces, ['px.exp.lab.holes.objects', 'px.exp.lab.holes.unplaced']);
  assert.deepEqual(document.Ticks[1].Calculations[0].with, { numbers: S4_ADDRESSES.numbers, tees: labAddress('px.tees'), baskets: labAddress('px.baskets') });
  assert.deepEqual(s4.run.Ticks.map(tick => tick.Calculations[0].call), ['fn.lab.hole.readnumbers', 'fn.lab.hole.bindanchors', 'fn.lab.hole.assemble', 'fn.lab.hole.unplaced']);
  for (const address of S4_CONTRACT.produces) assert.ok(lab.has(address), address);
});

test('S4.mmd compiles to the same document S4 runs', () => {
  const lab = createLab(); registerS4(lab);
  const { document, local } = compiledS4();
  assert.deepEqual(local, [], 'every S4 result is a published Part');
  assert.equal(structuralDigest(document), structuralDigest(s4Document(lab)));
  assert.deepEqual(document.Ticks.map(tick => tick.name), S4_CONTRACT.ticks);
});

test('the holes take their turns in badge order, each on the nearest free tee and basket', () => {
  const { s4 } = course();
  assert.deepEqual(s4.holes.map(hole => hole.number), [1, 10, 11]);
  assert.deepEqual(s4.holes.map(hole => hole.badge.reading), ['01', '10', '11']);
  // Badge "11" is the topmost in the raster and the last to play: the reading orders the holes.
  assert.ok(s4.holes[2].badge.at[1] < s4.holes[0].badge.at[1]);
  assert.deepEqual(s4.holes.map(hole => hole.tee?.id), ['tee-3', 'tee-2', 'tee-1']);
  assert.deepEqual(s4.holes.map(hole => hole.basket && hole.basket.id), ['basket-2', 'basket-1', null]);
  const used = s4.holes.flatMap(hole => [hole.tee?.id, hole.basket?.id]).filter(Boolean);
  assert.equal(new Set(used).size, used.length, 'no anchor is used twice');
});

test('a hole with no basket left is a hole with a missing basket, never a guess', () => {
  const { s4 } = course();
  const eleven = s4.holes.at(-1);
  assert.equal(eleven.basket, null);
  assert.deepEqual(eleven.missing, ['basket']);
  assert.equal(eleven.complete, false);
  assert.equal(eleven.confidence.value, 0.75);
  assert.deepEqual(eleven.confidence.basis, { badgeRead: 0.5, tee: 0.25, basket: 0 });
  assert.deepEqual(s4.unplaced.incomplete.map(entry => entry.number), [11]);
  assert.deepEqual(s4.unplaced.baskets, []);
  assert.deepEqual(s4.unplaced.tees, []);
  assert.deepEqual(s4.unplaced.badges, []);
  for (const hole of s4.holes.slice(0, 2)) { assert.equal(hole.complete, true); assert.equal(hole.confidence.value, 1); }
});

test('an unreadable badge takes no turn and is reported, and an anchor no hole took is free', () => {
  const badges = [
    { reading: { value: '2', status: 'read' }, unaccountedButOwned: { bbox: [0, 0, 4, 4] } },
    { reading: { value: null, status: 'unread' }, unaccountedButOwned: { bbox: [50, 50, 4, 4] } }
  ];
  const numbers = readNumbers({ badges });
  assert.deepEqual(numbers.numbered.map(entry => entry.number), [2]);
  assert.deepEqual(numbers.unreadable.map(entry => entry.id), ['badge-2']);
  const binding = bindAnchors({ numbers, tees: [{ center: [4, 4], bbox: [3, 3, 2, 2] }, { center: [80, 80], bbox: [79, 79, 2, 2] }], baskets: [{ bbox: [8, 8, 2, 2] }] });
  const holes = assembleHoles({ binding });
  const left = unplaced({ binding, holes });
  assert.deepEqual(holes.map(hole => hole.tee.id), ['tee-1']);
  assert.deepEqual(left.tees.map(entry => entry.id), ['tee-2']);
  assert.deepEqual(left.badges.map(entry => entry.id), ['badge-2']);
  assert.equal(left.badges[0].why, 'S1 did not read the digits confidently');
  const ledger = accountHoles({ numbers, binding, holes, unplaced: left });
  assert.equal(checkHoles({ ledger, holes, binding }).balanced, true);
  assert.throws(() => bindAnchors({ numbers, tees: [], baskets: [], rule: 'nearest-anywhere' }), /unknown binding rule/);
});

test('the invariants balance, and each one is a check a reader can name', () => {
  const { lab, s4 } = course();
  assert.deepEqual(s4.invariants.Ticks.map(tick => tick.name), ['AccountHoles', 'CheckHoles']);
  assert.equal(s4.invariants.Ticks[1].Calculations[0].with.ledger, S4_ADDRESSES.ledger);
  const { ledger, summary } = s4;
  assert.deepEqual(ledger, { badgesIn: 3, numbered: 3, unreadable: 0, holes: 3, teesIn: 3, teesBound: 3, teesFree: 0, basketsIn: 2, basketsBound: 2, basketsFree: 0, complete: 2, incomplete: 1 });
  assert.deepEqual(Object.keys(summary.checks), S4_CONTRACT.invariants);
  assert.equal(summary.balanced, true);
  assert.ok(lab.has(S4_ADDRESSES.summary));
  // The oracle refuses what the rule may never do: a basket guessed onto hole 11.
  const guessed = s4.holes.map(hole => hole.number === 11 ? { ...hole, basket: s4.holes[0].basket } : hole);
  assert.equal(checkHoles({ ledger, holes: guessed, binding: s4.binding }).checks.everyBasketOnce, false);
  assert.equal(checkHoles({ ledger, holes: guessed, binding: s4.binding }).checks.missingIsNotGuessed, false);
});

test('both S4 runs are pyto-run-record@1 records', () => {
  const { lab } = course();
  assert.deepEqual(lab.runRecord('S4').record.ticks.map(tick => tick.name), S4_CONTRACT.ticks);
  const invariants = lab.runRecord('S4.invariants').record;
  assert.equal(invariants.pcr, 'S4.invariants');
  assert.equal(invariants.ticks[1].invocations[0].actual_produces[0], S4_ADDRESSES.summary);
});

test('the extended fixture is the same capture plus two stated elements, and its basis says why', () => {
  const plain = fixtureCapture(), extended = fixtureCapture(20260911, { hole11: true, obstacle: true });
  assert.equal(plain.badges.length, 2);
  assert.equal(extended.badges.length, 3);
  assert.equal(extended.tees.length, 3);
  assert.equal(extended.baskets.length, 2, 'no third basket: hole 11 is the hole whose basket is missing');
  assert.equal(plain.obstacle, null);
  assert.deepEqual(extended.obstacle, { x: 0, y: 380, width: 264, height: 16 });
  // The two captures agree everywhere the new elements are not drawn.
  const differing = plain.rgba.reduce((count, value, index) => count + (value === extended.rgba[index] ? 0 : 1), 0);
  assert.ok(differing > 0 && differing < plain.rgba.length / 8, `only the new elements differ (${differing} samples)`);
  const basis = fixtureBasis({ hole11: true, obstacle: true });
  assert.equal(basis.elements.length, 6);
  assert.ok(basis.elements.at(-1).basis.includes('264x16'));
  assert.equal(fixtureBasis().elements.length, 4);
});

test('the Stages still run on the fixture without the new elements, and S4 then has two complete holes', () => {
  const { s4 } = course({});
  assert.deepEqual(s4.holes.map(hole => hole.number), [1, 10]);
  assert.deepEqual(s4.holes.map(hole => hole.complete), [true, true]);
  assert.equal(s4.summary.balanced, true);
  assert.deepEqual(s4.unplaced.incomplete, []);
});
