import test from 'node:test';
import assert from 'node:assert/strict';
import { createReferenceLab } from '../src/reference-algorithms/index.js';
import { runTransformer } from '../src/reference-algorithms/transformer.js';

const close = (actual, expected, tolerance = 1e-9) => assert.ok(Math.abs(actual - expected) <= tolerance, `${actual} is not within ${tolerance} of ${expected}`);
const everyFinite = value => Array.isArray(value) ? value.every(everyFinite) : Number.isFinite(value);

test('fixed single-head encoder layer exposes projections, attention, post-LN and FFN Parts', () => {
  const result = runTransformer(createReferenceLab());

  assert.deepEqual(result.query.values, [[1, 0], [0, 1]]);
  assert.deepEqual(result.key.values, [[1, 0], [0, 1]]);
  assert.deepEqual(result.value.values, [[1, 0], [0, 1]]);
  assert.deepEqual(result.scores.values, [[1, 0], [0, 1]]);
  close(result.scaledScores.values[0][0], 0.7071067811865475);

  // Hand calculation: softmax([1/sqrt(2), 0]) = [0.6697615493, 0.3302384507].
  close(result.softmax.values[0][0], 0.6697615493266569);
  close(result.softmax.values[0][1], 0.3302384506733431);
  close(result.softmax.values[0].reduce((sum, value) => sum + value, 0), 1);
  close(result.softmax.values[1].reduce((sum, value) => sum + value, 0), 1);
  assert.deepEqual(result.context.values, result.softmax.values);

  close(result.residual1.values[0][0], 1.6697615493266569);
  close(result.norm1.values[0][0], 0.9999888539157693);
  close(result.norm1.values[0][1], -0.9999888539157693);
  assert.deepEqual(result.ffnActivated.values, [[0.9999888539157693, 0], [0, 0.9999888539157693]]);
  close(result.residual2.values[0][0], 1.9999777078315386);
  close(result.output.values[0][0], 0.9999977777356464);
  close(result.output.values[1][1], 0.9999977777356464);
  close(result.output.values[0][1], -0.9999977777356464);
  assert.deepEqual(result.output.shape, [2, 2]);

  const invocationParts = result.record.ticks.flatMap(tick => tick.invocations.flatMap(invocation => invocation.actual_produces));
  assert.deepEqual(result.record.ticks.map(tick => tick.name), ['TransformerProject', 'TransformerAttend', 'TransformerNorm1', 'TransformerFfn', 'TransformerNorm2']);
  assert.equal(result.receipt.computed, 5);
  assert.equal(result.recordAddress, 'px.run.transformer-1');
  assert.ok(invocationParts.includes(result.addresses.softmax(result.run)));
  assert.ok(invocationParts.includes(result.addresses.output(result.run)));
});

test('transformer snapshots editable overrides at fresh addresses and stable softmax stays finite', () => {
  const lab = createReferenceLab();
  const input = [[1000, 0], [0, 1000]];
  const weights = { query: [[1, 0], [0, 1]], key: [[1, 0], [0, 1]] };
  const first = runTransformer(lab, { input, weights, parameters: { epsilon: 1e-5 } });
  input[0][0] = -4;
  weights.query[0][0] = -4;
  const second = runTransformer(lab, { input: [[1, 1], [1, 0]] });

  assert.equal(first.input[0][0], 1000);
  assert.equal(first.weights.query[0][0], 1);
  assert.ok(Object.isFrozen(first.input));
  assert.ok(Object.isFrozen(first.weights));
  assert.ok(Object.isFrozen(first.output));
  assert.notEqual(first.addresses.input(first.run), second.addresses.input(second.run));
  assert.notEqual(first.addresses.output(first.run), second.addresses.output(second.run));
  assert.ok(everyFinite(first.softmax.values));
  assert.ok(everyFinite(first.output.values));
  assert.deepEqual(first.softmax.values, [[1, 0], [0, 1]]);
});

test('transformer rejects incompatible editable weight or normalization overrides', () => {
  const lab = createReferenceLab();
  assert.throws(() => runTransformer(lab, { weights: { query: [[1, 0, 0], [0, 1, 0]] } }), /Q and K must share d_k/);
  assert.throws(() => runTransformer(lab, { parameters: { epsilon: 0 } }), /epsilon must be a positive finite number/);
});

test('transformer keeps fixed gamma=1 beta=0 explicit and handles asymmetric weights', () => {
  const result = runTransformer(createReferenceLab(), {
    input: [[1, 2], [3, 4]],
    weights: {
      query: [[1, 2], [0, 1]], key: [[2, 0], [1, 1]], value: [[0, 1], [2, 1]], output: [[1, 0], [0, 2]],
      ffn1: [[1, 0], [1, 2]], ffn1Bias: [0.25, -0.5], ffn2: [[2, 1], [0, 1]], ffn2Bias: [0.1, 0.2]
    }
  });
  assert.deepEqual(result.query.values, [[1, 4], [3, 10]]);
  assert.deepEqual(result.key.values, [[4, 2], [10, 4]]);
  assert.deepEqual(result.value.values, [[4, 3], [8, 7]]);
  assert.deepEqual(result.scores.values, [[12, 26], [32, 70]]);
  assert.equal(result.norm1.gamma, 1);
  assert.equal(result.norm1.beta, 0);
  assert.equal(result.norm2.gamma, 1);
  assert.equal(result.norm2.beta, 0);
  assert.ok(everyFinite(result.output.values));
});

test('transformer rejects sparse arrays and finite inputs that overflow, without success receipts', () => {
  const sparse = [[1, 2], []]; sparse[1][1] = 3;
  const sparseLab = createReferenceLab();
  assert.throws(() => runTransformer(sparseLab, { input: sparse }), /rectangular and finite|dense array/);
  assert.deepEqual(sparseLab.addresses(), []);

  const lab = createReferenceLab();
  assert.throws(() => runTransformer(lab, { input: [[Number.MAX_VALUE, 0], [0, Number.MAX_VALUE]] }), error => /overflowed|non-finite/.test(error.cause?.message ?? ''));
  assert.equal(lab.has('px.receipt.transformer-1'), false);
  assert.equal(lab.has('px.run.transformer-1'), false);
});

import { createLiveReference } from '../src/reference-algorithms/live.js';
test('transformer advances five Ticks and retains true 3x2 projections and 3x3 attention',async()=>{
 const lab=createReferenceLab(),input=[[1,0],[0,1],[1,1]],session=createLiveReference(lab,'transformer',{input});
 const produced=session.state.composition.Ticks.map(tick=>tick.Calculations.flatMap(calc=>Array.isArray(calc.into)?calc.into:[calc.into]));
 for(let i=0;i<5;i++){
  for(const address of produced.slice(i).flat())assert.equal(lab.has(address),false,address);
  await session.next();assert.equal(session.record.counters.invocations,i+1);
 }
 const whole=runTransformer(lab,{input});
 for(const [key,address] of Object.entries(session.addresses))assert.deepEqual(lab.get(address),lab.get(whole.addresses[key](whole.run)));
 const frame=session.frame(2);assert.deepEqual(frame.attention.shape,[3,3]);
 assert.deepEqual(frame.nodes.find(node=>node.key==='query').value.shape,[3,2]);
 assert.deepEqual(frame.attention.rowLabels,['Query 1','Query 2','Query 3']);
 assert.deepEqual(frame.attention.columnLabels,['Token 1','Token 2','Token 3']);
 assert.equal(frame.nodes.some(node=>node.key==='output'),false);
});
