import test from 'node:test';
import assert from 'node:assert/strict';
import { traceAddress } from '../src/core/provenance.js';

test('traces latest preceding producers and calculation addresses', () => {
  const records = [
    { id: 'seed', invocationId: 'tick-1', inputs: [{ address: 'source', value: 2 }], outputs: [{ address: 'a', value: 2 }], calculations: [] },
    { id: 'derive', invocationId: 'tick-2', inputs: [{ address: 'a', value: 2 }], outputs: [{ address: 'b', value: 4 }], calculations: [{ address: 'fn.double' }] },
  ];
  assert.deepEqual(traceAddress(records, 'b'), {
    address: 'b', value: 4,
    producer: { id: 'derive', invocationId: 'tick-2', index: 1 },
    inputs: [{
      address: 'a', value: 2,
      producer: { id: 'seed', invocationId: 'tick-1', index: 0 },
      inputs: [{ address: 'source', value: 2, producer: null, inputs: [], calculations: [] }],
      calculations: [],
    }],
    calculations: ['fn.double'],
  });
});

test('does not bind a read to a same-tick or future output', () => {
  const records = [
    { id: 'later', invocationId: 'tick-2', inputs: [{ address: 'x', value: 'initial' }], outputs: [{ address: 'x', value: 'later' }], calculations: [] },
  ];
  assert.deepEqual(traceAddress(records, 'x'), {
    address: 'x', value: 'later', producer: { id: 'later', invocationId: 'tick-2', index: 0 }, inputs: [{ address: 'x', value: 'initial', producer: null, inputs: [], calculations: [] }], calculations: [],
  });
  assert.deepEqual(traceAddress(records, 'x', { beforeIndex: 0 }), {
    address: 'x', producer: null, inputs: [], calculations: [],
  });
});

test('uses receipt input values for unproduced leaves and remains cycle safe', () => {
  const records = [{
    id: 'cycle', invocationId: 'tick-1',
    inputs: [{ address: 'a', value: 1 }, { address: 'b', value: 2 }],
    outputs: [{ address: 'a', value: 3 }, { address: 'b', value: 4 }], calculations: [],
  }];
  const trace = traceAddress(records, 'a');
  assert.equal(trace.inputs[0].producer, null);
  assert.equal(trace.inputs[0].value, 1);
});

test('preserves the consuming receipt input over older unrelated reads', () => {
  const records = [
    { id: 'old-read', inputs: [{ address: 'a', value: 1 }], outputs: [], calculations: [] },
    { id: 'produce', inputs: [{ address: 'a', value: 2 }], outputs: [{ address: 'b', value: 4 }], calculations: [] },
  ];
  assert.equal(traceAddress(records, 'b').inputs[0].value, 2);
});
