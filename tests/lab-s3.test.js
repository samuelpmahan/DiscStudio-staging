/** S3 (ChainSpot LAB, ported): visible Tee detection, and the Python analogue's balance. */
import test from 'node:test';
import assert from 'node:assert/strict';
import { createLab } from '../src/lab/lab.js';
import { labAddress } from '../src/lab/address.js';
import { registerS0, runS0 } from '../src/lab/s0.js';
import { registerS1, runS1, s1YamlDocument } from '../src/lab/s1.js';
import { registerS2, runS2 } from '../src/lab/s2.js';
import { registerS3, runS3, s3Document, detectTeeRings, selectTeeFamily, S3_ADDRESSES } from '../src/lab/s3.js';
import { fixtureCapture, shift, TEE_W, TEE_H, TEE_WALL } from '../src/lab/fixtures.js';

function stages() {
  const lab = createLab();
  registerS0(lab); registerS1(lab); registerS2(lab); registerS3(lab);
  const capture = fixtureCapture();
  const s0 = runS0(lab, { decoded: capture, label: 'fixture' });
  runS1(lab, { croppedImage: s0.croppedImage, document: s1YamlDocument(lab), seedRaster: true });
  runS2(lab);
  return { lab, capture, s0, s3: runS3(lab) };
}

test('S3 runs the document its OperationSpecs declare, consuming S2 substrate and S1 badges', () => {
  const { lab, s3 } = stages();
  const document = s3Document(lab);
  assert.deepEqual(document.Ticks.map(tick => tick.name), ['Tee.detectRings', 'Tee.findFamily', 'Tee.findPx']);
  assert.deepEqual(document.Ticks[0].Calculations[0].with, { fields: labAddress('px.components'), badges: labAddress('px.badges.objects') });
  assert.deepEqual(s3.run.Ticks.map(tick => tick.Calculations[0].call), ['fn.lab.tee.detectrings', 'fn.lab.tee.findfamily', 'fn.lab.tee.findpx']);
  for (const address of ['px.tees.rings', 'px.tees.family', 'px.tees']) assert.ok(lab.has(labAddress(address)), address);
});

test('every enclosed hole of the fixture is found, and the badge digit holes are the ones muted', () => {
  const { capture, s0, s3 } = stages();
  const { top, left } = s0.crop.insets;
  assert.equal(s3.rings.enclosed.length, 4);
  assert.equal(s3.rings.elongated.length, 4);
  // Two tee holes, and two badge digit "0" loops: the loops sit inside a Badge's
  // declared footprint, which is exactly what excludedByBadge is for.
  assert.equal(s3.rings.excludedByBadge.length, 2);
  assert.equal(s3.rings.candidates.length, 2);
  const holes = capture.tees.map(fixture => shift(fixture.hole, left, top));
  assert.deepEqual(s3.rings.candidates.map(ring => [ring.bboxX, ring.bboxY, ring.bboxW, ring.bboxH]), holes);
  for (const ring of s3.rings.candidates) {
    assert.equal(ring.kind, 'tee-rect');
    assert.ok(ring.elongation >= 1.18, 'an elongated hole');
    assert.equal(ring.holeArea, (TEE_W - TEE_WALL * 2) * (TEE_H - TEE_WALL * 2));
  }
});

test('a Tee is its enclosing bright frame, exactly', () => {
  const { capture, s0, s3 } = stages();
  const { top, left } = s0.crop.insets;
  assert.equal(s3.tees.length, 2);
  assert.deepEqual(s3.tees.map(tee => tee.bbox), capture.tees.map(fixture => shift(fixture.frame, left, top)));
  for (const tee of s3.tees) {
    // The frame outline: the bbox minus the hole it encloses.
    assert.equal(tee.px.length, TEE_W * TEE_H - (TEE_W - TEE_WALL * 2) * (TEE_H - TEE_WALL * 2));
    assert.equal(new Set(tee.px).size, tee.px.length);
    assert.equal(tee.has.detectRings.fn, 'fn.lab.tee.detectrings');
  }
  // The family is ordered by ring position, top to bottom.
  assert.ok(s3.tees[0].center[1] < s3.tees[1].center[1]);
});

test('the family vote keeps the frames that agree and drops the one that does not', () => {
  const frame = (label, major, minor, area) => ({ ring: { cx: label, cy: label }, frame: { label, major, minor, area, angle: 0 } });
  const measured = [frame(1, 20, 12, 150), frame(2, 21, 12, 155), frame(3, 60, 40, 900)];
  const selected = selectTeeFamily(measured);
  assert.deepEqual(selected.members.map(member => member.frame.label), [1, 2]);
  assert.ok(selected.anchor);
  assert.deepEqual(selectTeeFamily([]).members, []);
});

test('the Python analogue balances: every enclosed ring leaves through one named door', () => {
  const { lab, s3 } = stages();
  assert.deepEqual(s3.accounting.Ticks.map(tick => tick.name), ['AccountRings', 'CheckBalance']);
  // The second Tick consumes the first's published Part (S3_CHECKPOINT.md).
  assert.equal(s3.accounting.Ticks[1].Calculations[0].with.ledger, S3_ADDRESSES.ledger);
  const { ledger, summary } = s3;
  assert.equal(ledger.enclosed, ledger.elongated + ledger.diamondDropped);
  assert.equal(ledger.elongated, ledger.candidates + ledger.excludedByBadge);
  assert.equal(ledger.candidates, ledger.measured + ledger.unframed);
  assert.equal(ledger.measured, ledger.familyMembers + ledger.votedOutOfFamily);
  assert.equal(ledger.familyMembers, s3.tees.length);
  assert.equal(summary.balanced, true);
  assert.equal(summary.teePx, s3.tees.reduce((sum, tee) => sum + tee.px.length, 0));
  assert.ok(lab.has(S3_ADDRESSES.summary));
});

test('both S3 runs are pyto-run-record@1 records', () => {
  const { lab } = stages();
  assert.deepEqual(lab.runRecord('S3').record.ticks.map(tick => tick.name), ['Tee.detectRings', 'Tee.findFamily', 'Tee.findPx']);
  const accounting = lab.runRecord('S3.quick-anno').record;
  assert.equal(accounting.pcr, 'S3.quick-anno');
  assert.deepEqual(accounting.ticks.map(tick => tick.name), ['AccountRings', 'CheckBalance']);
});
