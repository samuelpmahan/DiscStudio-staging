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

test('grouping chains nest: every order of dimensions is valid and every disc lands in exactly one leaf', () => {
  const r = make();
  const view = r.shelf({ group: ['category', 'maker'] });
  assert.deepEqual(view.groups.map(g => g.label), ['Distance driver', 'Fairway driver', 'Midrange', 'Putt & approach', 'Putter']);
  for (const top of view.groups) {
    assert.ok(top.children.length > 0, `${top.label} splits by maker`);
    assert.ok(top.children.every(c => c.children.length === 0), 'two links nest exactly two deep');
  }
  const leaves = view.groups.flatMap(g => g.children);
  assert.equal(leaves.flatMap(l => l.discIds).length, view.shown, 'every shown disc sits in exactly one leaf');
  assert.equal(new Set(leaves.flatMap(l => l.discIds)).size, view.shown);
  const midrange = view.groups.find(g => g.label === 'Midrange');
  assert.ok(midrange.children.some(c => c.label === 'Discraft'), 'the Buzzzes nest under Discraft inside Midrange');
  const other = r.shelf({ group: ['maker', 'category'] });
  assert.deepEqual(other.groups.map(g => g.label), ['Discraft', 'Innova'], 'the maker-first chain reads the other way');
  assert.equal(other.groups.flatMap(g => g.children.flatMap(c => c.discIds)).length, other.shown);
});

test('speed and stability are grouping dimensions with their own order', () => {
  const r = make();
  const speed = r.shelf({ group: 'speed' });
  const nums = speed.groups.map(g => g.label);
  assert.ok(nums.every(l => /^Speed \d+/.test(l)), nums);
  assert.deepEqual(nums.map(l => Number(l.slice(6))), [...nums.map(l => Number(l.slice(6)))].sort((a, b) => a - b), 'speed sections run slow to fast');
  const stab = r.shelf({ group: ['stability'] });
  const bands = ['Very understable', 'Understable', 'Neutral', 'Stable', 'Overstable', 'Unknown stability'];
  assert.ok(stab.groups.every(g => bands.includes(g.label)), stab.groups.map(g => g.label));
  assert.deepEqual(stab.groups.map(g => bands.indexOf(g.label)), [...stab.groups.map(g => bands.indexOf(g.label))].sort((a, b) => a - b), 'stability reads understable to overstable');
  assert.equal(stab.groups.flatMap(g => g.discIds).length, stab.shown);
});

test('a lone string still groups one level and none is the empty chain', () => {
  const r = make();
  assert.deepEqual(r.shelf({ group: 'maker' }).groups.map(g => g.label), ['Discraft', 'Innova']);
  for (const view of [r.shelf({ group: 'none' }), r.shelf({ group: [] }), r.shelf({})]) {
    assert.deepEqual(view.groups.map(g => g.label), ['All discs']);
    assert.equal(view.groups[0].discIds.length, view.shown);
  }
  assert.deepEqual(r.shelf({ group: ['category', 'maker'] }).rows[0].groupPath.length, 2, 'rows carry their breadcrumb');
});

test('the focus shapes narrow the same read: maker set, category set, stability bands, speed range', () => {
  const r = make(), total = r.shelf({}).shown;
  assert.ok(total > 4, 'enough discs to narrow');
  const makers = r.world().objects.Manufacturer;
  const discraft = Object.values(makers).find(m => m.name === 'Discraft').id;
  const onlyDiscraft = r.shelf({ makerIds: [discraft] });
  assert.ok(onlyDiscraft.shown > 0 && onlyDiscraft.shown < total);
  assert.ok(ids(onlyDiscraft).every(id => r.world().objects.Mold[r.world().objects.Disc[id].moldId].manufacturerId === discraft));
  const putters = r.shelf({ categories: ['Putter', 'Putt & approach'] });
  assert.ok(putters.shown > 0 && putters.shown < total);
  assert.ok(ids(putters).every(id => ['Putter', 'Putt & approach'].includes(r.world().objects.Mold[r.world().objects.Disc[id].moldId].category)));
  const neutral = r.shelf({ stability: ['Neutral'] });
  assert.ok(neutral.shown > 0 && neutral.shown < total, 'some but not all of the seed is neutral');
  const slot = r.shelf({ stability: ['Neutral'], speedRange: [5, 5] });
  assert.ok(slot.shown > 0 && slot.shown <= neutral.shown, 'the speed range narrows the band');
  for (const id of ids(slot)) {
    const mold = r.world().objects.Mold[r.world().objects.Disc[id].moldId];
    assert.equal(mold.flight.speed, 5, id);
  }
  assert.equal(r.shelf({ makerIds: ['no-such-maker'] }).shown, 0, 'a maker set with nothing in it is empty, not an error');
});
