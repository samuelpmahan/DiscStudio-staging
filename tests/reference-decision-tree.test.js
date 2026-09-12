import test from 'node:test';
import assert from 'node:assert/strict';
import { createDecisionTreeLab, runDecisionTree } from '../src/reference-algorithms/decision-tree.js';

test('decision tree produces numeric comparisons, path and a real run record', () => {
  const lab = createDecisionTreeLab();
  const result = runDecisionTree(lab, { value: 3, parameters: { rootThreshold: 5, branchThreshold: 10 } });
  assert.equal(result.root.outcome, 'left');
  assert.equal(result.branch.outcome, 'low');
  assert.deepEqual(result.path.decisions, ['left', 'low']);
  assert.equal(result.leaf.label, 'low');
  assert.deepEqual(result.record.ticks.map(tick => tick.name), ['Root', 'Branch', 'Path', 'Leaf']);
  assert.equal(result.receipt.computed, 4);
  assert.equal(result.record.ticks.at(-1).invocations[0].actual_produces[0], result.addresses.leaf(result.run));
});

test('a second composition takes the other path and keeps the first snapshots', () => {
  const lab = createDecisionTreeLab();
  const first = runDecisionTree(lab, { value: 3, parameters: { rootThreshold: 5, branchThreshold: 10 } });
  const second = runDecisionTree(lab, { value: 12, parameters: { rootThreshold: 5, branchThreshold: 10 } });
  assert.equal(second.root.outcome, 'right');
  assert.equal(second.branch.outcome, 'high');
  assert.equal(first.input.value, 3);
  assert.equal(lab.get(first.addresses.input(first.run)).value, 3);
  assert.notEqual(first.addresses.input(first.run), second.addresses.input(second.run));
  assert.ok(lab.addresses().includes(second.addresses.path(second.run)));
});

test('tree validates explicit runs before writing and records bypassed or middle branches', () => {
  const lab = createDecisionTreeLab();
  assert.throws(() => runDecisionTree(lab, { run: 0, value: 1 }), /positive integer/);
  assert.deepEqual(lab.addresses(), []);

  const left = runDecisionTree(lab, { run: 4, value: 3, parameters: { rootThreshold: 5, branchThreshold: 10 } });
  assert.equal(left.branch.comparison, 'bypassed');
  assert.equal(Object.hasOwn(left.branch, 'operator'), false);
  assert.equal(Object.hasOwn(left.branch, 'threshold'), false);
  assert.match(left.leaf.explanation, /second comparison bypassed/);
  assert.throws(() => runDecisionTree(lab, { run: 4, value: 5 }), /already exists/);
  assert.equal(lab.get(left.addresses.input(4)).value, 3);

  const middle = runDecisionTree(lab, { run: 5, value: 5, parameters: { rootThreshold: 5, branchThreshold: 10 } });
  assert.equal(middle.root.outcome, 'right');
  assert.equal(middle.branch.outcome, 'middle');
  assert.equal(middle.branch.operator, '<');
  assert.equal(middle.branch.threshold, 10);
});

test('tree Parts are deeply frozen and invalid inputs publish nothing', () => {
  const lab = createDecisionTreeLab();
  assert.throws(() => runDecisionTree(lab, { value: Number.POSITIVE_INFINITY }), /finite number/);
  assert.deepEqual(lab.addresses(), []);
  const sparse = []; sparse[1] = 3;
  assert.throws(() => runDecisionTree(lab, { input: { value: 3, metadata: sparse } }), /sparse arrays/);

  const result = runDecisionTree(lab, { value: 3 });
  assert.throws(() => { result.leaf.path[0] = 'changed'; }, TypeError);
  assert.equal(lab.get(result.addresses.leaf(result.run)).path[0], 'left');
});

import { createLiveReference } from '../src/reference-algorithms/live.js';
test('tree live execution retains four real boundaries and agrees with run-all',async()=>{
 const lab=createDecisionTreeLab(),session=createLiveReference(lab,'tree',{value:12});
 const outputs=['root','branch','path','leaf'];
 for(let i=0;i<4;i++){
  for(const key of outputs.slice(i))assert.equal(lab.has(session.addresses[key]),false);
  await session.next();assert.equal(session.state.nextTick,i+1);assert.equal(session.record.counters.invocations,i+1);
 }
 const whole=runDecisionTree(lab,{value:12});
 for(const key of outputs)assert.deepEqual(lab.get(session.addresses[key]),whole[key]);
 assert.equal(session.frame(1).nodes.some(node=>node.key==='leaf'),false);
 const failed=createLiveReference(lab,'tree',{value:3});
 assert.throws(()=>failed.frame(1),/not been calculated/);assert.equal(failed.state.nextTick,0);
});
