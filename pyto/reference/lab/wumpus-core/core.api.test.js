import test from 'node:test';
import assert from 'node:assert/strict';
import * as core from '../src/core/index.js';

test('public core API exposes PxC, tick execution, and math', () => {
  assert.equal(typeof core.createPxC, 'function');
  assert.equal(typeof core.executeTick, 'function');
  assert.equal(typeof core.math?.point, 'function');
  assert.equal(typeof core.createPxC(), 'object');
});

test('executeTick captures unique access testimony and isolates typed arrays', () => {
  const pxc = core.createPxC();
  const input = new Uint8Array([4, 5]);
  pxc.set('input', input);

  const receipt = core.executeTick(pxc, {
    id: 'read-write',
    consumes: ['input'],
    produces: ['output'],
    run: (tx) => {
      const first = tx.get('input');
      const second = tx.get('input');
      first[0] = 9;
      tx.set('output', first);
      return { count: second.length };
    },
  });

  assert.match(receipt.invocationId, /^tick-\d+$/);
  assert.deepEqual(receipt.actualConsumes, ['input']);
  assert.deepEqual(receipt.actualProduces, ['output']);
  assert.deepEqual(receipt.writes, [{ address: 'output', kind: 'new-address' }]);
  assert.deepEqual([...receipt.inputs[0].value], [4, 5]);
  assert.deepEqual([...receipt.outputs[0].value], [9, 5]);
  assert.deepEqual([...pxc.get('input')], [4, 5]);

  const output = pxc.get('output');
  output[0] = 77;
  assert.deepEqual([...pxc.get('output')], [9, 5]);
});

test('executeTick gives each invocation a unique id', () => {
  const pxc = core.createPxC();
  const first = core.executeTick(pxc, { run: () => undefined });
  const second = core.executeTick(pxc, { run: () => undefined });
  assert.notEqual(first.invocationId, second.invocationId);
});

test('executeTick records named calculation calls as isolated testimony', () => {
  const pxc = core.createPxC();
  pxc.register('fn.math.double', ({ value }) => new Uint8Array([value * 2]));

  const receipt = core.executeTick(pxc, {
    id: 'calculate',
    run: (tx) => tx.set('result', tx.call('fn.math.double', { value: 3 })),
  });

  assert.deepEqual(receipt.calculations.map(({ address }) => address), ['fn.math.double']);
  assert.equal(receipt.calculations[0].identityScope, 'registered-address-only');
  assert.deepEqual(receipt.calculations[0].input, { value: 3 });
  assert.deepEqual([...receipt.calculations[0].output], [6]);
  receipt.calculations[0].output[0] = 99;
  assert.deepEqual([...pxc.get('result')], [6]);
  assert.equal(Object.isFrozen(receipt.calculations[0]), true);
});

test('executeTick rolls back slots and registered calculations on failure', () => {
  const pxc = core.createPxC();
  pxc.set('stable', { value: 1 });

  assert.throws(() => core.executeTick(pxc, {
    id: 'failing',
    run: (tx) => {
      tx.set('temporary', { value: 2 });
      tx.register('fn.temporary', () => 42);
      throw new Error('abort');
    },
  }), /abort/);

  assert.equal(pxc.has('temporary'), false);
  assert.deepEqual(pxc.get('stable'), { value: 1 });
  assert.throws(() => pxc.call('fn.temporary', null), /not registered/);
});
