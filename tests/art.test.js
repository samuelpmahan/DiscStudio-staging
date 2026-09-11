import test from 'node:test';
import assert from 'node:assert/strict';
import { assignArt, goldenIndex, shelfItems } from '../src/art.js';
import { createSeed } from '../src/seed.js';
import { createStudioRuntime } from '../src/runtime.js';
import { FAMILIES } from '../pyto/consumers/discstudio-card/port/painter/painter.mjs';

const context = { bagId: 'everyday', competitionId: 'putterwarz', roundId: 'hole-1' };
const items = (n, key = i => `k${i}`) => Array.from({ length: n }, (_, i) => ({ id: `d${i}`, key: key(i), authored: null }));

/* the four oracles: coverage, spread, grouping, stability */

test('coverage: with the spread budget set to the whole list, every family is used once before any repeats', () => {
  const out = assignArt({ items: items(FAMILIES.length), families: FAMILIES, spread: FAMILIES.length });
  assert.deepEqual(Object.values(out.histogram), FAMILIES.map(() => 1));
  const half = assignArt({ items: items(12), families: FAMILIES });
  assert.equal(half.spread, Math.ceil(FAMILIES.length / 2), 'by default the first half of the list is spread, then like groups with like');
  assert.equal(new Set(items(8).map(i => half.assignment[i.id])).size, 8, 'the first eight are eight different families');
});

test('spread: the golden walk lands a prefix evenly across the list, not clustered at one end', () => {
  const n = FAMILIES.length, picks = Array.from({ length: 4 }, (_, k) => goldenIndex(k, n)).sort((a, b) => a - b);
  const gaps = picks.slice(1).map((v, i) => v - picks[i]);
  assert.ok(Math.max(...gaps) <= Math.ceil(n / 2), `four picks over ${n} slots spread out: ${picks}`);
  const out = assignArt({ items: items(8), families: FAMILIES });
  const ids = items(8).map(i => i.id);
  for (let i = 1; i < ids.length; i++) assert.notEqual(out.assignment[ids[i]], out.assignment[ids[i - 1]], 'no two neighbours share a family while spreading');
});

test('grouping: after coverage, an item takes the family of the earliest item with its key; a new key keeps walking', () => {
  const list = [...items(8), { id: 'x1', key: 'k3', authored: null }, { id: 'x2', key: 'brand-new', authored: null }, { id: 'x3', key: 'k3', authored: null }];
  const out = assignArt({ items: list, families: FAMILIES });
  assert.equal(out.assignment.x1, out.assignment.d3, 'same mold, same family, once the spread phase is over');
  assert.equal(out.assignment.x3, out.assignment.d3);
  assert.equal(out.phase.x1, 'grouped');
  assert.equal(out.phase.x2, 'grouped');
  assert.ok(FAMILIES.includes(out.assignment.x2));
  assert.ok(!items(8).some(i => out.assignment[i.id] === out.assignment.x2), 'a new key after the spread still takes an unused family first');
  const early = assignArt({ items: [{ id: 'a', key: 'same', authored: null }, { id: 'b', key: 'same', authored: null }], families: FAMILIES });
  assert.notEqual(early.assignment.a, early.assignment.b, 'before coverage, likeness does not repeat a family: spread first');
});

test('stability: appending a disc never moves an earlier one, and an authored family always wins', () => {
  const base = items(10), more = [...base, { id: 'later', key: 'k2', authored: null }];
  const a = assignArt({ items: base, families: FAMILIES }), b = assignArt({ items: more, families: FAMILIES });
  for (const item of base) assert.equal(b.assignment[item.id], a.assignment[item.id]);
  const authored = [...items(3), { id: 'p', key: 'k0', authored: 'hot-foil' }];
  const out = assignArt({ items: authored, families: FAMILIES });
  assert.equal(out.assignment.p, 'hot-foil'); assert.equal(out.phase.p, 'authored');
  for (const item of items(3)) assert.notEqual(out.assignment[item.id], 'hot-foil', 'an authored family is taken before the walk starts, wherever the authored disc sits');
  assert.throws(() => assignArt({ items: items(2), families: [] }), /at least one family/);
});

/* the shelf binds it */

test('the runtime assigns the shelf on the record and every card binds px.art.assignment', () => {
  const r = createStudioRuntime(createSeed());
  const part = r.pxc.get('px.art.assignment');
  assert.equal(Object.keys(part.assignment).length, 12);
  const order = Object.keys(r.world().objects.Disc);
  assert.equal(new Set(order.slice(0, 8).map(id => part.assignment[id])).size, 8, 'the first eight discs spread over eight families');
  assert.equal(part.assignment['luna-lilac'], part.assignment['luna-mint'], 'then like groups with like: the Lunas share a family');
  assert.equal(part.assignment['zone-rose'], part.assignment['zone-peach']);
  assert.ok(r.pxc.has('px.receipt.art-assignment'));
  const card = r.card('buzzz-mint', 'discImage', context, null, 'shelf');
  const art = r.pxc.get(card.run.trace.find(t => t.call === 'fn.disc.art').output);
  assert.equal(art.inputs[0], part.assignment['buzzz-mint'], 'the painted family is the assigned one');
  r.dispatch({ type: 'entity.set', entityType: 'Disc', id: 'zone-peach', path: 'artFamily', value: 'hot-foil' });
  assert.equal(r.pxc.get('px.art.assignment').assignment['zone-peach'], 'hot-foil', 'an authored family wins after the re-run');
  const key = `disc-added`;
  r.dispatch({ type: 'entity.add', record: { id: key, type: 'Disc', moldId: 'buzzz', nickname: 'Another buzzz', photo: null, plastic: '', weight: null, color: '', notes: '' } });
  const after = r.pxc.get('px.art.assignment');
  assert.equal(after.assignment[key], after.assignment['buzzz-mint'], 'a thirteenth disc of a known mold groups with it');
  assert.equal(after.assignment['destroyer-lilac'], part.assignment['destroyer-lilac'], 'adding a disc moved nobody');
  assert.deepEqual(shelfItems(r.world())[0], { id: 'buzzz-mint', key: 'buzzz', authored: null });
});
