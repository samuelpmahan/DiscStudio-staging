import test from 'node:test';
import assert from 'node:assert/strict';
import { createSeed } from '../src/seed.js';
import { createStudioRuntime } from '../src/runtime.js';
import { currentBattle } from '../src/domain.js';
import { battleStandings, battleTemplates, schemeFrom } from '../src/battle.js';
const context = { bagId: 'everyday', competitionId: 'putterwarz', roundId: 'hole-1' };
const make = () => createStudioRuntime(createSeed());
const scores = r => currentBattle(r.world()).scores;
const free = r => Object.values(r.world().objects.Disc).filter(d => !r.world().battle.entries.some(e => e.discId === d.id));

// The owner's sentence, as one test: "a 5 disc cap battle where the top 3 each get 3,2,1 pt".
test('the 5-disc cap template composes three Constraints, and the cap refuses the sixth disc by name', () => {
  const r = make();
  r.dispatch({ type: 'battle.template', id: 'cap5-top3' });
  assert.deepEqual(r.world().battle.constraints.map(rule => rule.kind), ['discCap', 'placesPoints', 'tieRule']);
  assert.equal(r.battle().rules.find(rule => rule.id === 'disc-cap').status, 'pending', 'three of five is room for more');
  const spare = free(r);
  r.dispatch({ type: 'battle.add', discId: spare[0].id, id: 'entry-4' });
  r.dispatch({ type: 'battle.add', discId: spare[1].id, id: 'entry-5' });
  const full = r.battle();
  assert.equal(full.rules.find(rule => rule.id === 'disc-cap').status, 'pass');
  assert.match(full.rules.find(rule => rule.id === 'disc-cap').details[0].message, /the cap is full/);
  const before = r.world();
  assert.throws(() => r.dispatch({ type: 'battle.add', discId: spare[2].id, id: 'entry-6' }), error => /caps the lineup at 5 discs/.test(error.cause?.message ?? error.message));
  assert.equal(r.world(), before, 'a refused add changed nothing');
  assert.equal(r.world().battle.entries.length, 5);
});

test('one command is one undo: the template, and taking it back', () => {
  const r = make(), before = r.world();
  r.dispatch({ type: 'battle.template', id: 'cap5-top3' });
  assert.equal(r.world().battle.constraints.length, 3);
  r.undo.pop('px.studio.world');
  assert.deepEqual(r.world().battle.constraints, before.battle.constraints);
  assert.equal(r.world().battle.templateId, 'open');
});

test('tapping the finishing order IS entering the scores, and tapping again takes it back out', () => {
  const r = make(), [a, b, c] = r.world().battle.entries;
  r.dispatch({ type: 'battle.order', id: b.id });
  r.dispatch({ type: 'battle.order', id: a.id });
  r.dispatch({ type: 'battle.order', id: c.id });
  assert.deepEqual([scores(r)[b.id], scores(r)[a.id], scores(r)[c.id]], [1, 2, 3]);
  r.dispatch({ type: 'battle.order', id: a.id });          // out of the order: the gap closes
  assert.deepEqual([scores(r)[b.id], scores(r)[a.id], scores(r)[c.id]], [1, null, 2]);
  r.dispatch({ type: 'battle.order.clear' });
  assert.deepEqual(Object.values(scores(r)), [null, null, null]);
});

test('scoring is a Calculation over the states: ranks from scores, points from the scheme, a running total', () => {
  const r = make();
  r.dispatch({ type: 'battle.template', id: 'cap5-top3' });
  const [a, b, c] = r.world().battle.entries;
  for (const entry of [b, a, c]) r.dispatch({ type: 'battle.order', id: entry.id });
  const first = r.scene(context);
  assert.deepEqual(first.standings.table.map(row => [row.entryId, row.place, row.points, row.total]), [[b.id, 1, 3, 3], [a.id, 2, 2, 2], [c.id, 3, 1, 1]]);
  assert.deepEqual(first.standings.table.map(row => row.standing), [1, 2, 3]);
  // the run carries the standings and every card's entry, so the numbers have a receipt
  assert.ok(first.run.trace.some(step => step.call === 'fn.battle.standings' && step.output === 'px.battle.standings'));
  assert.equal(first.run.trace.filter(step => step.call === 'fn.battle.entry').length, 3);
  assert.equal(r.pxc.get(`px.render.course.${b.id}.entry`).points, 3);
  assert.match(first.svg, />3</, 'the points the preset binds are on the card');
  // a second state, scored differently: the total is across both, through the state being rendered
  r.dispatch({ type: 'battle.state.save', id: 'state-2', name: 'Hole 2' });
  r.dispatch({ type: 'battle.order.clear' });
  for (const entry of [a, c, b]) r.dispatch({ type: 'battle.order', id: entry.id });
  const second = r.scene(context);
  assert.deepEqual(second.standings.table.map(row => [row.entryId, row.total]), [[a.id, 5], [b.id, 4], [c.id, 3]]);
  r.dispatch({ type: 'battle.state.select', id: 'state-1' });
  assert.deepEqual(r.scene(context).standings.table.map(row => [row.entryId, row.total]), [[b.id, 3], [a.id, 2], [c.id, 1]], 'the running total is through the state on screen, not the last one');
});

test('a tie is a parameter of the tie Constraint, not a rounding accident', () => {
  const material = { entries: [{ id: 'a', discId: 'a', name: 'A' }, { id: 'b', discId: 'b', name: 'B' }, { id: 'c', discId: 'c', name: 'C' }], states: [{ id: 's', name: 'Hole', scores: { a: 1, b: 1, c: 2 } }], currentStateId: 's' };
  const rules = mode => [{ id: 'places', kind: 'placesPoints', value: 3, points: [3, 2, 1], mode: 'low', enabled: true }, { id: 'ties', kind: 'tieRule', value: 1, mode, enabled: true }];
  const shared = battleStandings({ material, rules: rules('share') });
  assert.deepEqual(shared.table.map(row => [row.entryId, row.place, row.points]), [['a', 1, 2.5], ['b', 1, 2.5], ['c', 3, 1]]);
  const best = battleStandings({ material, rules: rules('best') });
  assert.deepEqual(best.table.map(row => row.points), [3, 3, 1]);
  assert.equal(schemeFrom(rules('share')).tie, 'share');
});

test('with no points Constraint nothing is invented: no points, no total, no standing', () => {
  const r = make(), [a] = r.world().battle.entries;
  r.dispatch({ type: 'battle.score', id: a.id, score: 3 });
  const rendered = r.scene(context);
  assert.equal(rendered.standings.scheme.ranked, false);
  assert.deepEqual(rendered.standings.table.map(row => [row.points, row.total, row.standing]), [[null, null, null], [null, null, null], [null, null, null]]);
  assert.match(rendered.standings.sentence, /exactly what you authored/);
  assert.equal(r.pxc.get(`px.render.course.${a.id}.entry`).points, null);
});

test('a draft saved before a battle had rules opens as the open battle', () => {
  const seed = createSeed(); delete seed.battle.constraints; delete seed.battle.templateId; delete seed.battle.combine;
  const r = createStudioRuntime(seed);
  assert.deepEqual(r.world().battle.constraints, []);
  assert.equal(r.world().battle.templateId, 'open');
  assert.equal(r.battle().status, 'unconstrained');
  assert.ok(Object.keys(battleTemplates).includes('cap5-top3'));
});
