/** S2 (ChainSpot LAB, ported): basket detection, consuming S1's component substrate. */
import test from 'node:test';
import assert from 'node:assert/strict';
import { createLab } from '../src/lab/lab.js';
import { labAddress } from '../src/lab/address.js';
import { registerS0, runS0 } from '../src/lab/s0.js';
import { registerS1, runS1, s1YamlDocument } from '../src/lab/s1.js';
import { registerS2, runS2, s2Document, learnShellMargins, SPRITE, S2_ADDRESSES } from '../src/lab/s2.js';
import { fixtureCapture, shift, BASKET_MARGIN } from '../src/lab/fixtures.js';

function stages() {
  const lab = createLab();
  registerS0(lab); registerS1(lab); registerS2(lab);
  const capture = fixtureCapture();
  const s0 = runS0(lab, { decoded: capture, label: 'fixture' });
  runS1(lab, { croppedImage: s0.croppedImage, document: s1YamlDocument(lab), seedRaster: true });
  return { lab, capture, s0, s2: runS2(lab) };
}

const spriteWhite = SPRITE.rows.reduce((sum, row) => sum + [...row].filter(value => value === '1').length, 0);

test('S2 runs the document its OperationSpec composition declares, on S1 produce', () => {
  const { lab, s2 } = stages();
  const document = s2Document(lab);
  assert.deepEqual(document.Ticks.map(tick => tick.name), ['components.publish', 'Basket.detectFamily', 'Basket.findShellFamily', 'Basket.findPx']);
  // The substrate Tick consumes exactly what S1 published, and nothing else.
  assert.deepEqual(Object.values(document.Ticks[0].Calculations[0].with).sort(), ['blackMask', 'blackComponents', 'whiteMask', 'whiteComponents'].map(part => labAddress(`px.s1.exp.maskComponents.part.${part}`)).sort());
  assert.deepEqual(s2.run.Ticks.map(tick => tick.Calculations[0].call), ['fn.lab.components.publish', 'fn.lab.basket.detectfamily', 'fn.lab.basket.findshellfamily', 'fn.lab.basket.findpx']);
  for (const address of ['px.components', 'px.baskets.family', 'px.baskets.shellFamily', 'px.baskets']) assert.ok(lab.has(labAddress(address)), address);
});

test('the family is the sprite family: exact bbox, area ratio and coverage', () => {
  const { capture, s0, s2 } = stages();
  assert.deepEqual(s2.family.templateSize, [SPRITE.width, SPRITE.height]);
  assert.equal(s2.family.members.length, 2);
  const { top, left } = s0.crop.insets;
  assert.deepEqual(s2.family.members.map(member => [member.body.bboxX, member.body.bboxY, member.body.bboxW, member.body.bboxH]), capture.baskets.map(basket => shift(basket.body, left, top)));
  for (const member of s2.family.members) {
    assert.equal(member.whiteCoverage, 1);
    assert.equal(member.areaRatio, 1);
    assert.equal(member.body.area, spriteWhite);
  }
});

test('the shell family is the modal margin, learned with no tolerance', () => {
  const { s2 } = stages();
  assert.deepEqual(s2.shellFamily.margins, [BASKET_MARGIN, BASKET_MARGIN, BASKET_MARGIN, BASKET_MARGIN]);
  assert.equal(s2.shellFamily.members.length, 2);
  // The 75% consensus window: every cell of the shell bbox agreed on by both baskets.
  const window = (SPRITE.width + BASKET_MARGIN * 2) * (SPRITE.height + BASKET_MARGIN * 2);
  assert.equal(s2.shellFamily.shellOffsets.length, window - spriteWhite);
});

test('a tie between margins refuses the family rather than guessing', () => {
  const body = (label, x, y) => ({ label, area: 10, cx: x, cy: y, bboxX: x, bboxY: y, bboxW: 42, bboxH: 66 });
  const dark = (label, x, y, w, h) => ({ label, area: w * h, cx: x, cy: y, bboxX: x, bboxY: y, bboxW: w, bboxH: h });
  // Two bodies, two different shells: 1 vs 1, no modal margin.
  assert.equal(learnShellMargins([body(1, 10, 10), body(2, 200, 10)], [dark(3, 6, 6, 50, 74), dark(4, 198, 8, 46, 70)]), null);
  // The same margin twice is modal.
  assert.deepEqual(learnShellMargins([body(1, 10, 10), body(2, 200, 10)], [dark(3, 6, 6, 50, 74), dark(4, 196, 6, 50, 74)]), [4, 4, 4, 4]);
  assert.equal(learnShellMargins([body(1, 10, 10)], []), null);
});

test('a Basket is its bright body and its agreed dark shell, exactly', () => {
  const { s0, s2 } = stages();
  assert.equal(s2.baskets.length, 2);
  const window = (SPRITE.width + BASKET_MARGIN * 2) * (SPRITE.height + BASKET_MARGIN * 2);
  for (const basket of s2.baskets) {
    assert.deepEqual(basket.bbox.slice(2), [SPRITE.width + BASKET_MARGIN * 2, SPRITE.height + BASKET_MARGIN * 2]);
    assert.equal(basket.whitePx, spriteWhite);
    assert.equal(basket.whitePx + basket.blackPx, basket.px.length);
    // Every pixel of the shell bbox is accounted for: the sprite is white, the rest is shell.
    assert.equal(basket.px.length, window);
    assert.equal(new Set(basket.px).size, basket.px.length, 'a pixel is claimed twice');
    const [x, y, width, height] = basket.bbox;
    for (const pixel of basket.px) {
      const px = pixel % s0.croppedImage.widthPx, py = Math.floor(pixel / s0.croppedImage.widthPx);
      assert.ok(px >= x && px < x + width && py >= y && py < y + height, 'a basket pixel outside its bbox');
    }
    assert.equal(basket.has.detectFamily.fn, 'fn.lab.basket.detectfamily');
  }
  // Two baskets never claim the same pixel.
  assert.equal(new Set([...s2.baskets[0].px, ...s2.baskets[1].px]).size, s2.baskets[0].px.length * 2);
});

test('the S2 run is a pyto-run-record@1 with the LAB operation ids as Tick names', () => {
  const { lab } = stages();
  const { record } = lab.runRecord('S2');
  assert.equal(record.pcr, 'S2');
  assert.deepEqual(record.ticks.map(tick => tick.name), ['components.publish', 'Basket.detectFamily', 'Basket.findShellFamily', 'Basket.findPx']);
  assert.deepEqual(record.ticks[3].invocations[0].actual_produces, [S2_ADDRESSES.objects]);
});
