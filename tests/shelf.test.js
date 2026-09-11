import test from 'node:test';
import assert from 'node:assert/strict';
import { createSeed } from '../src/seed.js';
import { createStudioRuntime } from '../src/runtime.js';
import { shelfQuery, SORTS, GROUPS, FILTERS } from '../src/shelf.js';
const make = () => createStudioRuntime(createSeed());
const ids = view => view.rows.map(row => row.id);

test('a query is read the way a person says it: every term has to match, and the mold beats the nickname', () => {
  const r = make(), view = r.shelf({ query: 'buzzz 177' });
  assert.deepEqual(ids(view), ['buzzz-mint'].concat(ids(view).slice(1)));
  assert.equal(view.rows[0].id, 'buzzz-mint', 'the Buzzz that weighs exactly 177 g is the first result');
  assert.ok(view.rows[0].matched.includes('Buzzz') && view.rows[0].matched.includes('177 g'), view.rows[0].matched);
  assert.ok(view.rows[0].score > view.rows[1].score, 'an exact weight outranks a weight two grams away');
  assert.ok(ids(view).every(id => id.startsWith('buzzz')), ids(view));
});

test('flight numbers and disc type are searched like any other field', () => {
  const r = make(), view = r.shelf({ query: 'midrange -1' });
  assert.deepEqual(ids(view).sort(), ['buzzz-mint', 'buzzz-rose'], 'the Mako3 is a midrange but its turn is 0');
  assert.ok(view.rows[0].matched.some(label => label.includes('turn')), view.rows[0].matched);
  assert.deepEqual(ids(r.shelf({ query: 'esp' })).sort(), ['buzzz-mint', 'buzzz-rose'], 'plastic is searched');
  assert.deepEqual(ids(r.shelf({ query: 'peach' })), ['zone-peach'], 'colour is searched');
  assert.equal(r.shelf({ query: 'zzzz' }).shown, 0);
});

test('the quick filters are over the same read: in this bag, in no bag, has photo', () => {
  const r = make();
  assert.deepEqual(ids(r.shelf({ filters: ['inBag'], bagId: 'luna-bag' })).sort(), ['luna-blue', 'luna-lilac', 'luna-mint']);
  assert.deepEqual(ids(r.shelf({ filters: ['unbagged'] })), ['buzzz-rose'], 'one seeded disc is in no bag at all');
  assert.equal(r.shelf({ filters: ['photo'] }).shown, 0);
  r.dispatch({ type: 'entity.set', entityType: 'Disc', id: 'zone-gold', path: 'photo', value: 'data:image/png;base64,iVBORw0KGgo=' });
  assert.deepEqual(ids(r.shelf({ filters: ['photo'] })), ['zone-gold']);
  assert.equal(r.shelf({ filters: ['photo', 'unbagged'] }).shown, 0, 'filters compose');
});

test('every sort is offered and orders the whole shelf, and recently added is the shelf read backwards', () => {
  const r = make(), shelf = Object.keys(r.world().objects.Disc);
  assert.deepEqual(SORTS.map(([key]) => key), ['recent', 'maker', 'mold', 'category', 'speed', 'weight']);
  for (const [key] of SORTS) assert.equal(r.shelf({ sort: key }).shown, shelf.length, key);
  assert.deepEqual(ids(r.shelf({ sort: 'recent' })), [...shelf].reverse());
  const speeds = ids(r.shelf({ sort: 'speed' })).map(id => r.world().objects.Mold[r.world().objects.Disc[id].moldId].flight.speed);
  assert.deepEqual(speeds, [...speeds].sort((a, b) => b - a), 'fastest first');
  const weights = ids(r.shelf({ sort: 'weight' })).map(id => r.world().objects.Disc[id].weight);
  assert.deepEqual(weights, [...weights].sort((a, b) => b - a), 'heaviest first');
  const makers = ids(r.shelf({ sort: 'maker' })).map(id => r.world().objects.Manufacturer[r.world().objects.Mold[r.world().objects.Disc[id].moldId].manufacturerId].name);
  assert.deepEqual(makers, [...makers].sort());
});

test('grouping puts every shown disc in exactly one group, by maker or by disc type', () => {
  const r = make();
  assert.deepEqual(GROUPS.map(([key]) => key), ['none', 'maker', 'category']);
  const maker = r.shelf({ group: 'maker', sort: 'weight' });
  assert.deepEqual(maker.groups.map(g => g.label), ['Discraft', 'Innova'], 'the sections read A to Z whatever the sort inside them is');
  assert.equal(maker.groups.flatMap(g => g.discIds).length, maker.shown);
  const category = r.shelf({ group: 'category', sort: 'category' });
  assert.deepEqual(category.groups.map(g => g.label), ['Distance driver', 'Fairway driver', 'Midrange', 'Putt & approach', 'Putter']);
  assert.deepEqual(r.shelf({ group: 'none' }).groups.map(g => g.label), ['All discs']);
  assert.deepEqual(FILTERS.map(([key]) => key), ['inBag', 'unbagged', 'photo']);
});

test('the shelf read is a composition on the record, with the query as its own Part', () => {
  const r = make(), view = r.shelf({ query: 'luna', sort: 'weight' });
  assert.equal(view.part, 'px.shelf.view');
  assert.equal(view.run.composition.PrincipleComponentRender, 'shelf-view');
  assert.deepEqual(view.run.trace.map(step => step.call), ['fn.shelf.query']);
  assert.equal(r.pxc.get('px.shelf.request').query, 'luna');
  assert.deepEqual(r.pxc.get('px.shelf.view').rows.map(row => row.id), ids(view));
  assert.ok(r.pxc.has('px.receipt.shelf-view'));
  const again = r.shelf({ query: 'luna', sort: 'weight' });
  assert.ok(again.run.trace[0].reused, 'the same question over the same shelf is answered from the memo');
});

test('a disc added by the composer is findable by every fact it was added with', () => {
  const r = make();
  r.dispatch({ type: 'disc.create', id: 'disc-berg', manufacturer: 'Kastaplast', mold: 'Berg', category: 'Putter', plastic: 'K1', weight: 174, color: 'Mint', nickname: '', photo: null, bagId: 'everyday' });
  for (const query of ['berg', 'kastaplast', 'k1', '174', 'putter mint', 'berg 174']) assert.ok(ids(r.shelf({ query })).includes('disc-berg'), query);
  assert.equal(r.shelf({ sort: 'recent' }).rows[0].id, 'disc-berg', 'the disc just added is at the top of recently added');
  assert.deepEqual(r.shelf({ query: 'berg' }).rows[0].bagIds, ['everyday'], 'the row carries the bags the disc is in');
});

test('shelfQuery is pure over what it is given and never invents a disc', () => {
  const empty = shelfQuery({ discs: [], molds: {}, makers: {}, bags: [] });
  assert.deepEqual(empty.rows, []);
  assert.equal(empty.total, 0);
  const one = { id: 'd1', moldId: 'm1', nickname: 'Nameless', plastic: '', weight: null, color: '', photo: null };
  const view = shelfQuery({ discs: [one], molds: {}, makers: {}, bags: [], query: 'nameless' });
  assert.deepEqual(view.rows.map(r => r.id), ['d1'], 'a disc whose mold is missing is still findable by what it does have');
  assert.equal(shelfQuery({ discs: [one], molds: {}, makers: {}, bags: [], query: 'buzzz' }).shown, 0);
});
