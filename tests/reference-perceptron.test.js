import test from 'node:test';
import assert from 'node:assert/strict';
import { createLab } from '../src/lab/lab.js';
import { registerPerceptron, runPerceptron } from '../src/reference-algorithms/perceptron.js';

test('perceptron produces numeric Parts and a real run record', () => {
  const lab = createLab();
  registerPerceptron(lab);
  const result = runPerceptron(lab, { features: [2, -1], weights: [0.5, 3], bias: 1, threshold: 0 });
  assert.equal(lab.get(result.addresses.weightedSum).value, -1);
  assert.deepEqual(lab.get(result.addresses.contributions).map(part => part.product), [1, -3]);
  assert.equal(lab.get(result.addresses.activation).value, 0);
  assert.deepEqual(lab.get(result.addresses.output), { value: 0, class: 'negative' });
  assert.equal(result.recordAddress, 'px.run.perceptron-1');
  assert.equal(result.record.ticks.length, 2);
  assert.equal(result.record.ticks.flatMap(tick => tick.invocations).length, 2);
});

test('each run snapshots changed inputs and weights at fresh addresses', () => {
  const lab = createLab();
  registerPerceptron(lab);
  const first = runPerceptron(lab, { features: [1, 1], weights: [1, 1], bias: 0, threshold: 3 });
  const second = runPerceptron(lab, { features: [2, 1], weights: [2, 1], bias: 0, threshold: 3 });
  assert.notEqual(first.addresses.features, second.addresses.features);
  assert.notEqual(first.addresses.output, second.addresses.output);
  assert.equal(lab.get(first.addresses.weightedSum).value, 2);
  assert.equal(lab.get(second.addresses.weightedSum).value, 5);
  assert.equal(lab.get(first.addresses.output).value, 0);
  assert.equal(lab.get(second.addresses.output).value, 1);
  assert.ok(Object.isFrozen(lab.get(first.addresses.features)));
  assert.ok(Object.isFrozen(lab.get(first.addresses.weights)));
  assert.equal(first.record.ticks[0].invocations[0].actual_produces[0], first.addresses.contributions);
  assert.equal(second.record.ticks[1].invocations[0].actual_produces[1], second.addresses.output);
});

test('perceptron supports explicit runs, threshold equality and refuses name/run collisions', () => {
  const lab = createLab();
  registerPerceptron(lab);
  const first = runPerceptron(lab, { run: 3, name: 'named-perceptron', features: [2], weights: [1], bias: 0, threshold: 2 });
  assert.equal(lab.get(first.addresses.activation).value, 1);
  assert.throws(() => runPerceptron(lab, { run: 3, name: 'other', features: [9], weights: [9] }), /already exists/);
  assert.throws(() => runPerceptron(lab, { run: 4, name: 'named-perceptron', features: [9], weights: [9] }), /already exists/);
  assert.equal(lab.get(first.addresses.features)[0], 2);
});

test('perceptron rejects sparse input and overflow without a successful receipt', () => {
  const lab = createLab();
  registerPerceptron(lab);
  const sparse = []; sparse[1] = 1;
  assert.throws(() => runPerceptron(lab, { features: sparse, weights: [1, 1] }), /dense array/);
  assert.deepEqual(lab.addresses(), []);

  assert.throws(() => runPerceptron(lab, { features: [Number.MAX_VALUE], weights: [2], name: 'overflow' }), error => /overflowed/.test(error.cause?.message ?? ''));
  assert.equal(lab.has('px.receipt.overflow'), false);
  assert.equal(lab.has('px.run.overflow'), false);
  const result = runPerceptron(lab, { features: [1], weights: [1], name: 'valid' });
  assert.throws(() => { lab.get(result.addresses.contributions)[0].product = 99; }, TypeError);
  assert.equal(lab.get(result.addresses.contributions)[0].product, 1);
});

import { createReferenceLab, createLiveReference, createLiveTransport } from '../src/reference-algorithms/index.js';
import { validate } from '../pyto/viewer/adapters.js';
const firstInputs={features:[2,1],weights:[.5,-1],bias:.25,threshold:0};
test('live perceptron computes one Tick on Next and cannot leak activation early',async()=>{
 const lab=createReferenceLab(),session=createLiveReference(lab,'perceptron',firstInputs),a=session.addresses;
 for(const key of ['contributions','weightedSum','activation','output'])assert.equal(lab.has(a[key]),false,key);
 assert.equal(session.state.nextTick,0);assert.equal(session.record,null);
 const before=JSON.stringify(session.frame(0));
 const requests=[session.next(),session.next(),session.next()];assert.equal(requests[0],requests[1]);
 await Promise.all(requests);
 assert.equal(session.state.nextTick,1);assert.equal(session.record.ticks.length,1);
 assert.deepEqual(lab.get(a.contributions).map(v=>v.product),[1,-1]);assert.equal(lab.get(a.weightedSum).value,.25);
 assert.equal(lab.has(a.activation),false);assert.equal(lab.has(a.output),false);
 assert.equal(JSON.stringify(session.frame(0)),before);
 const firstRecord=JSON.stringify(session.record),firstFrame=JSON.stringify(session.frame(1));
 await session.next();assert.equal(lab.get(a.output).value,1);assert.equal(lab.get(a.activation).threshold,0);
 assert.equal(session.state.status,'complete');assert.equal(session.record.counters.invocations,2);validate(session.record);
 assert.equal(JSON.stringify(lab.get(session.state.records[0])),firstRecord);assert.equal(JSON.stringify(session.frame(1)),firstFrame);
 const frozen=JSON.stringify(session.state);const fork=createLiveReference(lab,'perceptron',{...firstInputs,bias:-1},{parent:session.sessionAddress});await fork.all();
 assert.equal(JSON.stringify(session.state),frozen);assert.equal(lab.get(a.output).value,1);assert.equal(lab.get(fork.addresses.output).value,0);
 const run=runPerceptron(lab,firstInputs);for(const key of Object.keys(a))assert.deepEqual(lab.get(a[key]),lab.get(run.addresses[key]));
 for(const node of session.frame().nodes)assert.deepEqual(node.value,lab.get(node.address));
});

test('Play and click share Next; reviewing does not execute or change the execution cursor',async()=>{
 const lab=createReferenceLab(),session=createLiveReference(lab,'perceptron',firstInputs);let release;
 const transport=createLiveTransport(session,{present:()=>new Promise(resolve=>{release=resolve;})});
 const a=transport.next(),b=transport.next();assert.equal(a,b);
 await new Promise(resolve=>setImmediate(resolve));assert.equal(session.state.nextTick,1);assert.equal(transport.busy,true);
 release();await a;
 const review=transport.review(0);release();await review;assert.equal(session.state.nextTick,1);assert.equal(lab.has(session.addresses.output),false);
 const next=transport.next();await new Promise(resolve=>setImmediate(resolve));release();await next;
 assert.equal(session.state.nextTick,2);assert.equal(transport.cursor,2);
 const other=createLiveReference(lab,'perceptron',firstInputs);let shown=0;
 await createLiveTransport(other,{present:async()=>{shown++;}}).play();assert.equal(shown,2);assert.equal(other.state.nextTick,2);
});
