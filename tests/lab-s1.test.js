/** S1 (ChainSpot LAB, ported): the LAB's own PQL document, run on the studio's core. */
import test from 'node:test';
import assert from 'node:assert/strict';
import { createLab } from '../src/lab/lab.js';
import { labAddress } from '../src/lab/address.js';
import { registerS0, runS0 } from '../src/lab/s0.js';
import { registerS1, runS1, s1YamlDocument, s1MermaidDocument, S1_ADDRESSES } from '../src/lab/s1.js';
import { fixtureCapture, shift } from '../src/lab/fixtures.js';

function stage({ mermaid = false } = {}) {
  const lab = createLab();
  registerS0(lab); registerS1(lab);
  const capture = fixtureCapture();
  const s0 = runS0(lab, { decoded: capture, label: 'fixture' });
  const document = mermaid ? s1MermaidDocument(lab) : s1YamlDocument(lab);
  const s1 = runS1(lab, { croppedImage: s0.croppedImage, document, seedRaster: !mermaid });
  return { lab, capture, s0, s1, document };
}

const box = part => part.bbox;

test('S1 runs the LAB PrincipleComponentRender.yaml document through readPql/invokePql', () => {
  const { s1, document } = stage();
  assert.deepEqual(document.Ticks.map(tick => tick.name), ['BlackMask', 'WhiteMask', 'BadgeAssembly', 'WhiteDigitRecognition', 'BadgeOutputs']);
  assert.deepEqual(s1.run.Ticks.map(tick => tick.Calculations.length), [2, 2, 5, 2, 4]);
  assert.equal(s1.receipt.trace.length, 15);
  for (const address of ['px.badges.objects', 'px.badges.px', 'px.badges.muted', 'px.remaining.afterBadges']) assert.ok(s1.outputs[labAddress(address)], address);
});

test('the masks and components are the fixture badges, at the geometry the knobs accept', () => {
  const { lab, capture, s0 } = stage();
  const plates = lab.get(labAddress('px.s1.exp.badgeAssembly.plates'));
  assert.equal(plates.selected.length, 2);
  const { top, left } = s0.crop.insets;
  assert.deepEqual(plates.selected.map(box), capture.badges.map(badge => shift(badge.plate, left, top)));
  const borders = lab.get(labAddress('px.s1.exp.badgeAssembly.plateBorders'));
  assert.deepEqual(borders.rows.map(row => row.matches.map(box)), capture.badges.map(badge => [shift(badge.border, left, top)]));
  const digits = lab.get(labAddress('px.s1.exp.badgeAssembly.plateDigits'));
  assert.deepEqual(digits.rows.map(row => row.matches.length), [2, 2]);
  const loops = lab.get(labAddress('px.s1.exp.badgeAssembly.digitLoops'));
  assert.deepEqual(loops.rows.flatMap(row => row.matches.map(box)), capture.badges.map(badge => shift(badge.loop, left, top)));
});

test('every badge is assembled and read, and the reading keeps the LAB shape', () => {
  const { lab } = stage();
  const candidates = lab.get(labAddress('px.s1.exp.badgeAssembly.badgeCandidates'));
  assert.equal(candidates.candidates.length, 2);
  assert.deepEqual(candidates.incomplete, []);
  const recognized = lab.get(labAddress('px.s1.whiteDigits.recognizedBadges'));
  assert.deepEqual(recognized.candidates.map(badge => badge.reading.status), ['read', 'read']);
  assert.deepEqual(recognized.candidates.map(badge => badge.reading.value), ['10', '10']);
  assert.equal(recognized.candidates[0].reading.digits[0].rankings[0].label, '1');
});

test('owned, muted and remaining partition the raster exactly', () => {
  const { lab, s0 } = stage();
  const owned = lab.get(labAddress('px.badges.px')), muted = lab.get(labAddress('px.badges.muted')), remaining = lab.get(labAddress('px.remaining.afterBadges'));
  const total = s0.croppedImage.widthPx * s0.croppedImage.heightPx;
  const union = new Set([...owned.pixels, ...muted.pixels, ...remaining.pixels]);
  assert.equal(owned.pixels.length + muted.pixels.length + remaining.pixels.length, total, 'the three sets overlap');
  assert.equal(union.size, total, 'the three sets do not cover the raster');
  // Ownership is declared from the outer border bbox; the muted pixels are the
  // ones inside it that no component explains.
  const badges = lab.get(labAddress('px.badges.objects'));
  assert.equal(badges.length, 2);
  const declared = badges.reduce((sum, badge) => sum + badge.unaccountedButOwned.bbox[2] * badge.unaccountedButOwned.bbox[3], 0);
  assert.equal(owned.pixels.length + muted.pixels.length, declared);
  assert.equal(badges[0].unaccountedButOwned.rule, 'outer-border-bbox');
});

test('the compiled Mermaid S1 produces the same Parts as the YAML S1, value for value', () => {
  const baseline = stage(), generated = stage({ mermaid: true });
  const addresses = baseline.document.Ticks.flatMap(tick => tick.Calculations.flatMap(calculation => calculation.into));
  assert.equal(addresses.length, 15);
  for (const address of addresses) assert.deepEqual(generated.lab.get(address), baseline.lab.get(address), address);
  // The Mermaid document computes the warm raster the YAML path seeds.
  assert.deepEqual(generated.lab.get(S1_ADDRESSES.croppedRaster), baseline.lab.get(S1_ADDRESSES.croppedRaster));
});

test('the S1 run is a pyto-run-record@1 with the LAB Tick names', () => {
  const { lab } = stage();
  const { record } = lab.runRecord('S1');
  assert.equal(record.schema, 'pyto-run-record@1');
  assert.deepEqual(record.ticks.map(tick => tick.name), ['BlackMask', 'WhiteMask', 'BadgeAssembly', 'WhiteDigitRecognition', 'BadgeOutputs']);
  assert.equal(record.ticks[2].invocations.length, 5);
});
