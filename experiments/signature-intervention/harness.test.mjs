import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import { compareOutputs, median, observerSlices, sourceIdentity, timingMedian, withoutReceipt } from './lib.mjs';

test('equivalence excludes only the top-level run receipt', () => {
  const result = { svg: '<svg/>', card: { value: 1 }, run: { computed: 1, trace: [] } };
  assert.deepEqual(withoutReceipt(result), { svg: '<svg/>', card: { value: 1 } });
  assert.throws(() => withoutReceipt({ svg: '<svg/>' }), /top-level run receipt/);
});

test('comparison retains SVG identity and reports case IDs', () => {
  const a = [{ id: 'cold', inputSha256: 'input-a', output: { svg: '<svg>A</svg>' }, svgSha256: 'a' }];
  assert.equal(compareOutputs(a, structuredClone(a)).pass, true);
  assert.deepEqual(compareOutputs(a, [{ ...a[0], output: { svg: '<svg>B</svg>' } }]).mismatches, ['cold']);
  assert.deepEqual(compareOutputs(a, [{ ...a[0], id: 'warm' }]).mismatches, ['cold']);
  assert.deepEqual(compareOutputs(a, [{ ...a[0], inputSha256: 'different-input' }]).mismatches, ['cold']);
});

test('numeric and timing medians distinguish regressions from invalid timing', () => {
  assert.equal(median([3, 1, 2]), 2);
  assert.equal(median([-1, 0, 1]), 0);
  assert.throws(() => median([]), /Invalid/);
  assert.equal(timingMedian([0, 1]), 0.5);
  assert.throws(() => timingMedian([-1, 1]), /Invalid/);
});

test('source identity is deterministic and includes relative file names', () => {
  const root = mkdtempSync(join(tmpdir(), 'signature-harness-')); writeFileSync(join(root, 'a.txt'), 'a');
  const identity = sourceIdentity(root); assert.deepEqual(Object.keys(identity.files), ['a.txt']); assert.equal(identity.fingerprint.length, 64);
});

test('observer boundary slices are grouped by actual render end offsets', () => {
  const events = [{ serialized: true }, { serialized: false }, { serialized: true }, { serialized: false }];
  assert.deepEqual(observerSlices(events, [2, 3, 4]), [[events[0], events[1]], [events[2]], [events[3]]]);
  assert.throws(() => observerSlices(events, [3, 2]), /Invalid observer boundaries/);
});
