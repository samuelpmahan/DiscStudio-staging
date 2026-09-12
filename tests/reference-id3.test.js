import test from 'node:test';
import assert from 'node:assert/strict';
import { createLab } from '../src/lab/lab.js';
import { createId3Session, id3Entropy } from '../src/reference-algorithms/id3.js';
import { createLiveTransport } from '../src/reference-algorithms/live.js';
import { DIGIT_DATASET, DIGIT_TEST_SAMPLES } from '../src/reference-algorithms/digit-data.js';
import { validate } from '../pyto/viewer/adapters.js';

const tiny = samples => ({width: samples[0].pixels.length, height: 1, threshold: 8, samples});
const near = (actual, expected, epsilon = 1e-12) => assert.ok(Math.abs(actual - expected) < epsilon, `${actual} is not near ${expected}`);
const fixture = tiny([{id:'a',label:0,pixels:[0,0]}, {id:'b',label:0,pixels:[0,0]}, {id:'c',label:1,pixels:[16,16]}, {id:'d',label:1,pixels:[16,16]}]);

test('ID3 begins without scores, runs one calculation per Next, and retains real Parts per frame', async () => {
 const lab = createLab(), session = createId3Session(lab, {dataset: fixture});
 assert.equal(session.state.nextTick, 0); assert.equal(session.record, null);
 assert.equal(session.frame().tree.nodes.n0.status, 'pending');
 assert.equal(session.frame().tree.nodes.n0.counts, null); assert.equal(session.frame().candidates, null);
 assert.equal(lab.addresses().some(address => /\.scores\.\d+$/.test(address)), false);
 assert.equal(session.predict([0,0]).result.status, 'unresolved'); assert.equal(session.state.nextTick, 0);
 const initial = JSON.stringify(session.frame());
 const one = session.next(), same = session.next(); assert.equal(one, same); await Promise.all([one,same]);
 assert.equal(session.state.nextTick, 1); assert.equal(session.record.counters.invocations, 1); assert.equal(session.record.ticks.length, 1);
 const scored = session.frame(); assert.equal(scored.phase, 'scored');
 assert.equal(Object.keys(scored.tree.nodes).length, 1); assert.equal(scored.tree.nodes.n0.status, 'pending');
 near(scored.candidates.parentEntropy, 1); near(scored.candidates.candidates[0].gain, 1);
 assert.equal(scored.candidates.recommendedCandidate.pixel, 0); assert.equal(scored.previewCandidate.pixel, 0); assert.equal(scored.selectedCandidate, null);
 assert.deepEqual(scored.candidates, lab.get(scored.candidatesAddress));
 assert.deepEqual(scored.tree, lab.get(scored.treeAddress));
 const oldScore = JSON.stringify(scored), oldRecord = JSON.stringify(session.record);
 await session.next();
 assert.equal(session.state.nextTick, 2); assert.equal(session.frame().phase, 'split');
 assert.equal(session.frame().selectedCandidate.pixel, 0); assert.equal(session.frame().activeNodeId, 'n0');
 assert.equal(session.frame().tree.nodes.n0.pixel, 0); assert.equal(session.frame().tree.nodes['n0.0'].status, 'pending');
 assert.deepEqual(session.frame().tree.queue, ['n0.0','n0.1']);
 assert.deepEqual(session.frame().tree.nodes['n0.0'].availablePixels, [1]);
 assert.equal(JSON.stringify(session.frame(0)), initial); assert.equal(JSON.stringify(session.frame(1)), oldScore);
 assert.equal(JSON.stringify(lab.get(session.state.records[0])), oldRecord);
 assert.equal(session.predict([0,0]).result.status, 'unresolved');
 await session.all(); assert.equal(session.state.status, 'complete');
 assert.equal(session.state.nextTick, 6); assert.equal(session.record.ticks.length, 6); validate(session.record);
 for (const sample of fixture.samples) assert.equal(session.predict(sample.pixels).result.prediction, sample.label);
 assert.equal(session.predict([0,0], {frameIndex: 0}).result.status, 'unresolved');
 assert.equal(session.state.nextTick, 6); assert.equal(session.frame(2).tree.nodes['n0.0'].status, 'pending');
 assert.throws(() => {session.frame().tree.nodes.n0.pixel = 99;}, TypeError);
 assert.throws(() => session.frame(7), /not been calculated/);
});

test('ID3 handles equality at threshold, zero-gain XOR, and deterministic pixel ties', async () => {
 const data = tiny([{id:'00',label:0,pixels:[0,0]}, {id:'01',label:1,pixels:[0,8]}, {id:'10',label:1,pixels:[8,0]}, {id:'11',label:0,pixels:[8,8]}]);
 const session = createId3Session(createLab(), {dataset: data}); await session.next();
 assert.deepEqual(session.frame().candidates.candidates.map(candidate => candidate.gain), [0,0]);
 assert.deepEqual(session.frame().candidates.candidates[0].on.sampleIds, ['10','11']);
 await session.next(); assert.equal(session.frame().selectedCandidate.pixel, 0);
 await session.all(); for (const sample of data.samples) assert.equal(session.predict(sample.pixels).result.prediction, sample.label);
 assert.equal(session.predict([8,0]).result.visited[0].on, true);
});

test('constant questions remain visible but cannot divide samples; ambiguous leaves disclose majority ties', async () => {
 const data = tiny([{id:'a',label:3,pixels:[0,0]}, {id:'b',label:1,pixels:[0,0]}]);
 const session = createId3Session(createLab(), {dataset: data}); await session.next();
 assert.ok(session.frame().candidates.candidates.every(candidate => candidate.eligible === false));
 await session.next(); assert.equal(session.state.status, 'complete');
 assert.equal(session.frame().tree.nodes.n0.reason, 'remaining-pixels-cannot-separate');
 assert.equal(session.frame().tree.nodes.n0.prediction, 1); assert.equal(session.frame().decision.majorityTieRule, 'lowest digit label');
 const result = session.predict([0,0]); assert.equal(result.result.prediction, 1); validate(result.record);
 const pure = createId3Session(createLab(), {dataset: tiny([{id:'a',label:7,pixels:[16]}])});
 await pure.next(); assert.equal(pure.frame().candidates.recommendedCandidate, null); assert.equal(pure.frame().previewCandidate, null);
 await pure.all(); assert.equal(pure.state.nextTick, 2); assert.equal(pure.frame().tree.nodes.n0.reason, 'pure');
});

test('step-all and manual stepping agree, and transport review does not train', async () => {
 const lab = createLab(), first = createId3Session(lab, {dataset: fixture}), second = createId3Session(lab, {dataset: fixture});
 await first.all(); const transport = createLiveTransport(second); await transport.play();
 assert.deepEqual(first.frame().tree, second.frame().tree);
 const state = JSON.stringify(second.state); await transport.review(0); assert.equal(JSON.stringify(second.state), state);
 assert.equal(transport.cursor, 0); assert.equal(second.state.nextTick, 6);
 const old = JSON.stringify(first.frame()); createId3Session(lab, {dataset: tiny([{id:'different',label:9,pixels:[0]}])});
 assert.equal(JSON.stringify(first.frame()), old);
});

test('real 8x8 root agrees with independently calculated entropy and candidate partition', async () => {
 const lab = createLab(), session = createId3Session(lab, {dataset: DIGIT_DATASET}); await session.next();
 const scores = session.frame().candidates; assert.equal(scores.candidates.length, 64);
 near(scores.parentEntropy, 3.3219280948873626);
 const best = scores.candidates[28]; near(best.gain, .826466250649041);
 assert.equal(scores.recommendedCandidate.pixel, 28); assert.equal(session.frame().selectedCandidate, null);
 assert.equal(session.frame().tree.nodes.n0.status, 'pending'); assert.equal(Object.keys(session.frame().tree.nodes).length, 1);
 assert.equal(best.row, 3); assert.equal(best.column, 4); assert.equal(best.off.sampleIds.length, 10); assert.equal(best.on.sampleIds.length, 20);
 assert.deepEqual(best.off.counts, {'0':3,'1':0,'2':0,'3':0,'4':3,'5':1,'6':3,'7':0,'8':0,'9':0});
 await session.next(); assert.equal(session.frame().selectedCandidate.pixel, 28);
 for (const candidate of scores.candidates) {
  const ids = [...candidate.off.sampleIds,...candidate.on.sampleIds];
  assert.equal(new Set(ids).size, 30); assert.deepEqual([...ids].sort(), DIGIT_DATASET.samples.map(sample => sample.id).sort());
 }
 const testIds = new Set(DIGIT_TEST_SAMPLES.map(sample => sample.id));
 assert.ok(DIGIT_DATASET.samples.every(sample => !testIds.has(sample.id)));
});

test('invalid inputs cannot create a session or silently change retained inputs', () => {
 const lab = createLab();
 assert.throws(() => createId3Session(lab, {dataset: {...fixture, threshold: NaN}}), /threshold/);
 assert.throws(() => createId3Session(lab, {dataset: tiny([{id:'a',label:0,pixels:[17]}])}), /pixel/);
 assert.deepEqual(lab.addresses(), []);
 const original = structuredClone(fixture), session = createId3Session(lab, {dataset: original, name: 'fixed'});
 original.samples[0].pixels[0] = 16; assert.equal(session.frame().dataset.samples[0].pixels[0], 0);
 original.width = 200; assert.equal(session.predict([0,0]).result.status, 'unresolved');
 assert.throws(() => createId3Session(lab, {dataset: fixture, name: 'fixed'}), /already exists/);
 assert.throws(() => session.predict([undefined,0]), /pixel/);
 near(id3Entropy({a:0,b:4}), 0); near(id3Entropy({a:1,b:1}), 1);
});
