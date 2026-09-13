import test from 'node:test';
import assert from 'node:assert/strict';
import { createStudioRuntime } from '../src/runtime.js';
import { createSeed } from '../src/seed.js';
import { queryPrefix } from '../src/core/exec.js';
import { get, clone } from '../src/domain.js';

const make = () => createStudioRuntime(createSeed());
const use = (r, key, args) => r.experiences().use(key, args);

test('ExploreShelf fires on a requested shelf view: fn.shelf.query projects px.shelf.view', () => {
  const r = make();
  const result = use(r, 'exploreshelf', { query: 'buzzz' });
  assert.equal(result.fired, true);
  assert.equal(result.projection, 'px.shelf.view');
  assert.ok(result.total > 0 && result.shown <= result.total);
  assert.ok(r.pxc.has('px.shelf.view'), 'the projection Part exists');
  assert.equal(r.pxc.get('px.studio.exploreshelf.context.view'), 'px.shelf.view');
  assert.equal(r.pxc.get('px.studio.exploreshelf.context.selection').experience, 'exploreshelf');
  assert.deepEqual(result.unsealed, ['px.studio.createbag.definition', 'px.studio.creategraphics.definition']);
});

test('ExploreShelf refuses when the shelf is empty, and says why', () => {
  const empty = createSeed(); empty.objects.Disc = {};
  const r = createStudioRuntime(empty);
  const result = use(r, 'exploreshelf', {});
  assert.equal(result.fired, false);
  assert.match(result.reason, /empty/);
  assert.ok(!r.pxc.has('px.studio.exploreshelf.context.selection'), 'a refusal publishes no context');
});

test('CreateBag fires on a name plus specimens: the Bag Part holds shared references, never copies', () => {
  const r = make();
  const before = clone(r.world().objects.Disc['buzzz-mint']);
  const result = use(r, 'createbag', { name: 'Sunday singles', discIds: ['buzzz-mint'] });
  assert.equal(result.fired, true);
  const bag = get(r.world(), 'Bag', result.bagId);
  assert.equal(bag.name, 'Sunday singles');
  assert.deepEqual(bag.discIds, ['buzzz-mint']);
  assert.deepEqual(r.world().objects.Disc['buzzz-mint'], before, 'the specimen Part is untouched');
  assert.equal(result.projection, `px.domain.Bag.${result.bagId}`);
  assert.equal(r.pxc.get('px.studio.createbag.context.bag'), result.projection);
  assert.deepEqual(result.unsealed, ['px.studio.managebags.definition', 'px.studio.creategraphics.definition']);
});

test('CreateBag refuses a blank name or no specimens', () => {
  const r = make();
  for (const args of [{ name: '   ', discIds: ['buzzz-mint'] }, { name: 'Bag', discIds: [] }, { name: 'Bag', discIds: ['nope'] }]) {
    const result = use(r, 'createbag', args);
    assert.equal(result.fired, false, JSON.stringify(args));
    assert.match(result.reason, /Name the bag/);
  }
  assert.ok(!r.pxc.has('px.studio.createbag.context.selection'), 'a refusal publishes no context');
});

test('ManageBags adapts bags through all five commands; Disc Parts stay untouched', () => {
  const r = make();
  const discsBefore = clone(r.world().objects.Disc);
  const created = use(r, 'createbag', { name: 'Adapt me', discIds: ['buzzz-mint'] });
  const bagId = created.bagId;

  const renamed = use(r, 'managebags', { bagId, adaptation: { kind: 'rename', name: 'Adapted' } });
  assert.equal(renamed.fired, true);
  assert.equal(renamed.bag.name, 'Adapted');

  const packed = use(r, 'managebags', { bagId, adaptation: { kind: 'membership', discId: 'luna-mint', include: true } });
  assert.deepEqual(packed.bag.discIds, ['buzzz-mint', 'luna-mint']);

  const reordered = use(r, 'managebags', { bagId, adaptation: { kind: 'reorder', discId: 'luna-mint', toIndex: 0 } });
  assert.deepEqual(reordered.bag.discIds, ['luna-mint', 'buzzz-mint']);

  const unpacked = use(r, 'managebags', { bagId, adaptation: { kind: 'membership', discId: 'buzzz-mint', include: false } });
  assert.deepEqual(unpacked.bag.discIds, ['luna-mint']);
  assert.ok(r.world().objects.Disc['buzzz-mint'], 'out of the bag is not off the shelf');

  const duplicated = use(r, 'managebags', { bagId, adaptation: { kind: 'duplicate', name: 'Adapted copy' } });
  assert.equal(duplicated.fired, true);
  assert.notEqual(duplicated.bag.id, bagId);
  assert.deepEqual(duplicated.bag.discIds, ['luna-mint']);
  assert.equal(duplicated.projection, `px.domain.Bag.${duplicated.bag.id}`);

  const removed = use(r, 'managebags', { bagId: duplicated.bag.id, adaptation: { kind: 'remove' } });
  assert.equal(removed.removed, true);
  assert.equal(removed.projection, null);
  assert.ok(!get(r.world(), 'Bag', duplicated.bag.id), 'the bag is gone');
  assert.ok(r.world().objects.Disc['luna-mint'], 'its discs remain on the shelf');

  assert.deepEqual(r.world().objects.Disc, discsBefore, 'no adaptation touched a Disc Part');
  assert.deepEqual(renamed.unsealed, ['px.studio.creategraphics.definition']);
});

test('ManageBags refuses without a bag or without an adaptation', () => {
  const r = make();
  assert.equal(use(r, 'managebags', { bagId: 'nope', adaptation: { kind: 'rename', name: 'x' } }).fired, false);
  const created = use(r, 'createbag', { name: 'Bag', discIds: ['buzzz-mint'] });
  const result = use(r, 'managebags', { bagId: created.bagId, adaptation: { kind: 'bogus' } });
  assert.equal(result.fired, false);
  assert.match(result.reason, /adaptation/);
});

test('CreateGraphics-spotlight fires on a bound specimen: the spotlight card, 620x760', () => {
  const r = make();
  const result = use(r, 'creategraphics', { discId: 'buzzz-mint' });
  assert.equal(result.fired, true);
  assert.equal(result.projection, 'px.render.single.buzzz-mint.svg');
  assert.equal(result.width, 620);
  assert.equal(result.height, 760);
  assert.match(result.svg, /<svg/, 'an actual card composition');
  assert.equal(r.pxc.get('px.studio.creategraphics.context.card'), result.projection);
  assert.deepEqual(result.unsealed, ['px.studio.exportgraphics.definition']);
});

test('CreateGraphics refuses a specimen that does not resolve', () => {
  const r = make();
  const result = use(r, 'creategraphics', { discId: 'nope' });
  assert.equal(result.fired, false);
  assert.match(result.reason, /resolves/);
});

test('the spotlight card through the Experience path derives a null recipe label live', () => {
  const r = make();
  r.dispatch({ type: 'disc.create', id: 'disc-live', manufacturer: 'Live Moldworks', mold: 'Livewire', category: '', plastic: '', weight: null, color: '', nickname: '', photo: null, depiction: 'paint', paint: { family: 'pressed-fern', seed: 4242, base: '#3f6b4f', accent: '#c9d6a3', target: 96, label: null }, flight: {}, bagId: null });
  const first = use(r, 'creategraphics', { discId: 'disc-live' });
  assert.ok(first.svg.includes('Live Moldworks') && first.svg.includes('Livewire'), 'the blank label derives maker and mold at render time');
  r.dispatch({ type: 'disc.identity', id: 'disc-live', manufacturer: 'Renamed Moldworks', mold: 'Livewire' });
  const second = use(r, 'creategraphics', { discId: 'disc-live' });
  assert.ok(second.svg.includes('Renamed Moldworks'), 'renaming the maker renames the card: nothing was frozen');
  assert.ok(!second.svg.includes('Live Moldworks'));
});

test('ExportGraphics-spotlight fires on the inspected card: scene plus provenance', () => {
  const r = make();
  const battleBefore = clone(r.world().battle);
  const result = use(r, 'exportgraphics', { discId: 'buzzz-mint' });
  assert.equal(result.fired, true);
  assert.equal(result.projection, 'px.course.svg');
  assert.match(result.svg, /<svg/);
  assert.deepEqual(result.provenance, { disc: 'px.domain.Disc.buzzz-mint', recipe: 'px.presets.spotlight', renderer: 'card' });
  assert.equal(r.pxc.get('px.studio.exportgraphics.context.scene'), 'px.course.svg');
  assert.deepEqual(result.unsealed, []);
  assert.deepEqual(r.world().battle, battleBefore, 'the export never touches the competition');
});

test('ExportGraphics refuses without a bound specimen', () => {
  const r = make();
  const result = use(r, 'exportgraphics', { discId: 'nope' });
  assert.equal(result.fired, false);
  assert.match(result.reason, /CreateGraphics/);
});

test('the full chain fires in order: shelf, bag, adaptation, card, export', () => {
  const r = make();
  assert.equal(use(r, 'exploreshelf', {}).fired, true);
  const bag = use(r, 'createbag', { name: 'Chain bag', discIds: ['buzzz-mint'] });
  assert.equal(bag.fired, true);
  const adapted = use(r, 'managebags', { bagId: bag.bagId, adaptation: { kind: 'membership', discId: 'luna-mint', include: true } });
  assert.equal(adapted.fired, true);
  assert.equal(use(r, 'creategraphics', { discId: 'luna-mint' }).fired, true);
  const exported = use(r, 'exportgraphics', { discId: 'luna-mint' });
  assert.equal(exported.fired, true);
  assert.equal(exported.provenance.disc, 'px.domain.Disc.luna-mint');
  // Each Experience published under its own prefix; UDS was never selected.
  for (const key of ['exploreshelf', 'createbag', 'managebags', 'creategraphics', 'exportgraphics']) {
    assert.equal(r.pxc.get(`px.studio.${key}.context.selection`).experience, key);
  }
  assert.deepEqual(queryPrefix(r.pxc, 'px.studio.uds.context.*'), {}, 'UDS context stays empty when UDS is never used');
});

test('UDS keeps its own context prefix; selecting another Experience does not move it', () => {
  const r = make();
  r.experiences().select('uds');
  r.experiences().select('exploreshelf');
  assert.equal(r.pxc.get('px.studio.uds.context.selection').experience, 'uds');
  assert.equal(r.pxc.get('px.studio.exploreshelf.context.selection').experience, 'exploreshelf');
});
