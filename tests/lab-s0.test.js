/** S0 (ChainSpot LAB, ported) running on the studio's PxC core. */
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { createLab } from '../src/lab/lab.js';
import { SOURCE } from '../src/lab/source.js';
import { parseYaml } from '../src/lab/yaml.js';
import { registerS0, runS0, S0_ADDRESSES, toGray, stripChromeProposal } from '../src/lab/s0.js';
import { fixtureCapture, CHROME_TOP, CHROME_BOTTOM, WIDTH, HEIGHT } from '../src/lab/fixtures.js';

const s0 = () => { const lab = createLab(); const cache = registerS0(lab); return { lab, cache, capture: fixtureCapture() }; };

test('S0 runs its compiled document through readPql/invokePql and exits at canonicalPixels', () => {
  const { lab, capture } = s0();
  const run = runS0(lab, { decoded: capture, label: 'fixture' });
  assert.deepEqual(run.run.Ticks.map(tick => tick.name), ['Decode', 'Crop', 'Cache']);
  // S0.stage.yaml: exit_when.S1_can_consume is px.course.canonicalPixels.
  const stage = parseYaml(readFileSync(join(SOURCE, 'S0.stage.yaml'), 'utf8'));
  assert.equal(stage.exit_when.S1_can_consume, 'px.course.canonicalPixels');
  assert.ok(lab.has(S0_ADDRESSES.canonicalPixels));
  assert.equal(run.croppedImage.widthPx, WIDTH);
});

test('the crop receipt carries exactly the fields S0.pcr.yaml names', () => {
  const { lab, capture } = s0();
  const run = runS0(lab, { decoded: capture, label: 'fixture' });
  const pcr = parseYaml(readFileSync(join(SOURCE, 'S0.pcr.yaml'), 'utf8'));
  assert.deepEqual(Object.keys(run.cropReceipt), pcr.receipt.fields);
  assert.equal(run.cropReceipt.cropMethod, 'single-phone-entropy');
});

test('the entropy detector finds the fixture chrome bands and cuts its safety margin past them', () => {
  const { capture } = s0();
  const crop = stripChromeProposal(toGray(capture));
  // The band is CHROME_TOP rows of constant grey; the LAB's detector walks in
  // one row past the first run of content rows and adds a 2px margin.
  assert.equal(crop.insets.top, CHROME_TOP + 2);
  assert.equal(crop.insets.bottom, CHROME_BOTTOM + 2);
  assert.deepEqual([crop.insets.left, crop.insets.right], [0, 0]);
});

test('canonicalPixels is the capture byte for byte inside the crop', () => {
  const { lab, capture } = s0();
  const run = runS0(lab, { decoded: capture, label: 'fixture' });
  const { top, left } = run.crop.insets;
  assert.equal(run.croppedImage.heightPx, HEIGHT - run.crop.insets.top - run.crop.insets.bottom);
  for (const [y, x] of [[0, 0], [10, 17], [400, 300], [run.croppedImage.heightPx - 1, WIDTH - 1]]) {
    const there = ((y + top) * WIDTH + (x + left)) * 4, here = (y * run.croppedImage.widthPx + x) * 4;
    assert.deepEqual(run.croppedImage.rgba.slice(here, here + 4), capture.rgba.slice(there, there + 4), `pixel ${x},${y}`);
  }
});

test('FullImage is cached last, after the CroppedImage has materialized', () => {
  const { lab, cache, capture } = s0();
  runS0(lab, { decoded: capture, label: 'fixture' });
  assert.deepEqual(lab.get(S0_ADDRESSES.cacheReceipt), { cached: capture.imageId, at: 'last', widthPx: WIDTH, heightPx: HEIGHT });
  assert.ok(cache.has(capture.imageId));
});

test('the S0 run is a pyto-run-record@1 the shared adapter validates', () => {
  const { lab, capture } = s0();
  runS0(lab, { decoded: capture, label: 'fixture' });
  const { record } = lab.runRecord('S0');
  assert.equal(record.schema, 'pyto-run-record@1');
  assert.equal(record.pcr, 'S0');
  assert.deepEqual(record.ticks.map(tick => tick.name), ['Decode', 'Crop', 'Cache']);
  assert.deepEqual(record.ticks[1].invocations.map(invocation => invocation.calculation.address), ['fn.lab.s0.findchromebounds', 'fn.lab.s0.applycrop']);
});
