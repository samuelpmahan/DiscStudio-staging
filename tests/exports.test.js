import test from 'node:test';
import assert from 'node:assert/strict';
import { planExports, queueProgress } from '../src/exports.js';
import { createSeed } from '../src/seed.js';
const world = () => { const w = createSeed(); w.battle.states.push({ id: 'state-2', name: 'Hole 2', scores: {}, highlight: null, winners: [] }); return w; };

test('one tap plans one job per state, in order, each naming the canvas it will render', () => {
  const jobs = planExports({ intent: 'all-states', world: world() });
  assert.deepEqual(jobs.map(job => job.stateId), ['state-1', 'state-2']);
  assert.ok(jobs.every(job => job.orientation === 'landscape' && job.status === 'queued' && job.kind === 'png'));
  assert.equal(jobs[0].label, 'Opening · 1920 × 1080 · PNG');
});
test('"this battle, vertical" plans the same states on the 1080 x 1920 canvas and changes nothing in the workspace', () => {
  const w = world(), jobs = planExports({ intent: 'vertical', world: w });
  assert.ok(jobs.every(job => job.orientation === 'portrait'));
  assert.equal(w.layout.orientation, 'landscape', 'planning an export never edits the draft');
  assert.equal(jobs[1].label, 'Hole 2 · vertical 1080 × 1920 · PNG');
});
test('"every disc" plans one single card per disc in the battle, each file named after the disc', () => {
  const jobs = planExports({ intent: 'each-disc', world: world() });
  assert.deepEqual(jobs.map(job => job.discId), ['buzzz-mint', 'zone-peach', 'destroyer-lilac']);
  assert.deepEqual(jobs.map(job => job.name), ['mint-practice-disc', 'peach-approach-disc', 'lilac-bomber']);
  assert.ok(jobs.every(job => job.mode === 'card'));
});
test('an empty battle refuses by name instead of queueing nothing', () => {
  const w = world(); w.battle.entries = [];
  assert.throws(() => planExports({ intent: 'each-disc', world: w }), /add a disc/);
  assert.throws(() => planExports({ intent: 'nonsense', world: w }), /Unknown export intent/);
});
test('the queue reads as a sentence at every stage, and a failure keeps its own', () => {
  const jobs = planExports({ intent: 'all-states', world: world() });
  assert.equal(queueProgress([]).sentence, 'Nothing queued.');
  assert.match(queueProgress(jobs).sentence, /0 of 2 done · 2 waiting/);
  jobs[0].status = 'running';
  assert.match(queueProgress(jobs).sentence, /exporting Opening/);
  assert.equal(queueProgress(jobs).complete, false);
  jobs[0].status = 'done'; jobs[1].status = 'failed';
  const progress = queueProgress(jobs);
  assert.deepEqual([progress.complete, progress.done, progress.failed], [true, 1, 1]);
  assert.match(progress.sentence, /1 failed, and each says why/);
  jobs[1].status = 'done';
  assert.equal(queueProgress(jobs).sentence, 'All 2 exported.');
});
