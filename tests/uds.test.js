import test from 'node:test';
import assert from 'node:assert/strict';
import { createStudioRuntime } from '../src/runtime.js';
import { createSeed } from '../src/seed.js';
import { queryPrefix, readPql, invokePql } from '../src/core/exec.js';
import { get, validateWorld, validatePaintRecipe } from '../src/domain.js';
import { recipeFor, artInputs, prepareDiscArt } from '../src/presentation.js';
import { render as paintRender, FAMILIES } from '../pyto/consumers/discstudio-card/port/painter/painter.mjs';

const context = { bagId: 'everyday', competitionId: 'putterwarz', roundId: 'hole-1' };
const recipe = { family: 'pressed-fern', seed: 4242, base: '#3f6b4f', accent: '#c9d6a3', target: 96, label: 'Kastaplast · Berg' };
const artOf = (r, id) => { const w = r.world(), disc = get(w, 'Disc', id), mold = get(w, 'Mold', disc.moldId), maker = get(w, 'Manufacturer', mold.manufacturerId); return prepareDiscArt({ disc, mold, maker }); };

test('recipeFor with no retained recipe is the legacy artInputs derivation, byte for byte', () => {
  const r = createStudioRuntime(createSeed());
  const w = r.world(), disc = get(w, 'Disc', 'buzzz-mint'), mold = get(w, 'Mold', disc.moldId), maker = get(w, 'Manufacturer', mold.manufacturerId);
  const assignment = r.pxc.get('px.art.assignment');
  assert.deepEqual(recipeFor(disc, assignment, mold, maker), artInputs({ disc, mold, maker, assignment }));
  assert.equal(paintRender(...recipeFor(disc, assignment, mold, maker)), paintRender(...artInputs({ disc, mold, maker, assignment })));
});

test('a retained paint recipe renders the same SVG on two runtimes and survives unrelated fact edits', () => {
  const make = () => {
    const r = createStudioRuntime(createSeed());
    r.dispatch({ type: 'disc.create', id: 'disc-fern', manufacturer: 'Kastaplast', mold: 'Berg', category: 'Putter', plastic: 'K1', weight: 174, color: 'Green', nickname: '', photo: null, depiction: 'paint', paint: recipe, bagId: 'everyday' });
    return r;
  };
  const a = make(), b = make();
  const svgA = a.card('disc-fern', 'broadcast', context).svg, svgB = b.card('disc-fern', 'broadcast', context).svg;
  assert.equal(svgA, svgB, 'the same recipe is the same artwork on a fresh runtime');
  assert.equal(artOf(a, 'disc-fern').svg, paintRender(recipe.family, recipe.seed, recipe.base, recipe.accent, recipe.target, recipe.label), 'the card paints from the retained recipe');
  const before = a.world().objects.Disc['disc-fern'].paint;
  a.dispatch({ type: 'entity.set', entityType: 'Disc', id: 'disc-fern', path: 'color', value: 'Blue' });
  const after = a.world().objects.Disc['disc-fern'];
  assert.deepEqual(after.paint, before, 'an unrelated fact edit does not touch the retained recipe');
  assert.equal(a.card('disc-fern', 'broadcast', context).svg, svgA, 'and the artwork does not reroll');
});

test('all sixteen bundled painters still render a retained recipe', () => {
  assert.equal(FAMILIES.length, 16);
  for (const family of FAMILIES) {
    const svg = paintRender(family, 7, '#3f6b4f', '#c9d6a3', 96, 'Kastaplast · Berg');
    assert.ok(svg.includes('<svg'), family);
  }
});

test('disc.create defaults the depiction to the photo when one is supplied, paint otherwise', () => {
  const r = createStudioRuntime(createSeed());
  r.dispatch({ type: 'disc.create', id: 'disc-a', manufacturer: 'Discraft', mold: 'Buzzz', photo: null, bagId: null });
  r.dispatch({ type: 'disc.create', id: 'disc-b', manufacturer: 'Discraft', mold: 'Buzzz', photo: 'data:image/png;base64,iVBOR', bagId: null });
  r.dispatch({ type: 'disc.create', id: 'disc-c', manufacturer: 'Discraft', mold: 'Buzzz', photo: null, depiction: 'photo', bagId: null });
  const w = r.world();
  assert.equal(w.objects.Disc['disc-a'].depiction, 'paint');
  assert.equal(w.objects.Disc['disc-a'].paint, null);
  assert.equal(w.objects.Disc['disc-b'].depiction, 'photo');
  assert.equal(w.objects.Disc['disc-c'].depiction, 'photo', 'an explicitly requested depiction is honoured');
  assert.equal(artOf(r, 'disc-b').kind, 'photo');
  assert.equal(artOf(r, 'disc-a').kind, 'painted');
  try {
    r.dispatch({ type: 'disc.create', id: 'disc-d', manufacturer: 'Discraft', mold: 'Buzzz', paint: { family: 'nope', seed: 1, base: '#ffffff', accent: '#000000', target: 96, label: 'x' }, bagId: null });
    assert.fail('a bad recipe should fail the whole creation');
  } catch (error) { assert.match(String(error.cause?.message ?? error.message), /Unknown painter family/, 'a bad recipe fails the whole creation'); }
  assert.equal(r.world().objects.Disc['disc-d'], undefined, 'nothing half-made is left behind');
});

test('one disc.create carries depiction, recipe and bag membership; one undo takes all of it back', () => {
  const r = createStudioRuntime(createSeed()), before = r.world();
  r.dispatch({ type: 'disc.create', id: 'disc-u', manufacturer: 'Mint', mold: 'Lobster', category: 'Midrange', plastic: 'Apex', weight: 175, color: 'Mint', nickname: '', photo: null, depiction: 'paint', paint: recipe, bagId: 'everyday' });
  const made = r.world().objects.Disc['disc-u'];
  assert.equal(made.depiction, 'paint');
  assert.deepEqual(made.paint, recipe);
  assert.ok(r.world().objects.Bag.everyday.discIds.includes('disc-u'));
  assert.ok(r.card('disc-u', 'broadcast', context).svg.length > 100);
  r.undo.pop('px.studio.world');
  assert.equal(r.world().objects.Disc['disc-u'], undefined);
  assert.deepEqual(r.world().objects.Bag.everyday.discIds, before.objects.Bag.everyday.discIds);
  assert.equal(Object.keys(r.world().objects.Manufacturer).length, Object.keys(before.objects.Manufacturer).length, 'no stray maker is left behind');
});

test('switching depiction keeps both the photo and the recipe, and undoes', () => {
  const r = createStudioRuntime(createSeed());
  const photo = 'data:image/png;base64,iVBORw0KGgo=';
  r.dispatch({ type: 'disc.create', id: 'disc-s', manufacturer: 'Discraft', mold: 'Buzzz', photo, depiction: 'photo', paint: recipe, bagId: null });
  assert.equal(artOf(r, 'disc-s').kind, 'photo');
  r.dispatch({ type: 'entity.set', entityType: 'Disc', id: 'disc-s', path: 'depiction', value: 'paint' });
  const disc = r.world().objects.Disc['disc-s'];
  assert.equal(disc.photo, photo, 'the photo is retained');
  assert.deepEqual(disc.paint, recipe, 'the recipe is retained');
  const art = artOf(r, 'disc-s');
  assert.equal(art.kind, 'painted');
  assert.equal(art.svg, paintRender(recipe.family, recipe.seed, recipe.base, recipe.accent, recipe.target, recipe.label));
  r.undo.pop('px.studio.world');
  assert.equal(artOf(r, 'disc-s').kind, 'photo', 'the switch undoes');
});

test('handing a disc a photo chooses the photo depiction, so the bound presentations use it', () => {
  const r = createStudioRuntime(createSeed());
  const photo = 'data:image/webp;base64,UklGRg==';
  assert.equal(r.world().objects.Disc['buzzz-mint'].depiction, 'paint');
  r.dispatch({ type: 'entity.set', entityType: 'Disc', id: 'buzzz-mint', path: 'photo', value: photo });
  const disc = r.world().objects.Disc['buzzz-mint'];
  assert.equal(disc.depiction, 'photo', 'the upload is the deliberate choice of the photo depiction');
  assert.equal(artOf(r, 'buzzz-mint').kind, 'photo');
  assert.equal(artOf(r, 'buzzz-mint').src, photo);
  r.dispatch({ type: 'entity.set', entityType: 'Disc', id: 'buzzz-mint', path: 'photo', value: null });
  assert.equal(r.world().objects.Disc['buzzz-mint'].depiction, 'photo', 'removing the photo keeps the depiction; the painted fallback renders');
  assert.equal(artOf(r, 'buzzz-mint').kind, 'painted');
});

test('a legacy draft without depiction normalises instead of refusing', () => {
  const seed = createSeed();
  for (const disc of Object.values(seed.objects.Disc)) { delete disc.depiction; delete disc.paint; }
  seed.objects.Disc['buzzz-mint'].photo = 'data:image/png;base64,iVBOR';
  seed.objects.Disc['zone-rose'].paint = { family: 'nope' };
  const world = validateWorld(seed);
  assert.equal(world.objects.Disc['buzzz-mint'].depiction, 'photo', 'a photo means the photo depiction');
  assert.equal(world.objects.Disc['buzzz-mint'].paint, null);
  assert.equal(world.objects.Disc['zone-rose'].depiction, 'paint');
  assert.equal(world.objects.Disc['zone-rose'].paint, null, 'a malformed recipe normalises to no recipe');
  for (const disc of Object.values(world.objects.Disc)) assert.ok(['photo', 'paint'].includes(disc.depiction));
});

test('fn.studio.effectiveDefinition merges the base requirements with the variant additional through PQL', () => {
  const r = createStudioRuntime(createSeed());
  const doc = readPql(JSON.stringify({ PrincipleComponentRender: 'effective-definition', Ticks: [{ name: 'Compose', Calculations: [{ call: 'fn.studio.effectiveDefinition', with: { base: 'px.studio.uds.definition', variant: 'px.studio.uds.paint.definition' }, into: 'px.test.effective' }] }] }), JSON.parse);
  invokePql(doc, r.pxc);
  const effective = r.pxc.get('px.test.effective');
  const base = r.pxc.get('px.studio.uds.definition'), variant = r.pxc.get('px.studio.uds.paint.definition');
  assert.deepEqual(effective.shared, base.shared, 'shared requirements come from the base');
  assert.deepEqual(effective.additional, variant.additional, 'additional requirements come from the variant');
  assert.equal(effective.discVizType, 'px.studio.discviztype.paint');
  assert.equal(r.pxc.get(effective.discVizType).value, 'paint', 'the DiscVizType Part resolves');
  assert.equal(effective.parameter, 'px.studio.discviztype');
  assert.ok(effective.continues.includes('px.studio.exploreshelf.definition'));
  const bad = readPql(JSON.stringify({ PrincipleComponentRender: 'bad', Ticks: [{ name: 'Bad', Calculations: [{ call: 'fn.studio.effectiveDefinition', with: { base: 'px.studio.uds.definition' }, into: 'px.test.bad' }] }] }), JSON.parse);
  try { invokePql(bad, r.pxc); assert.fail('a missing variant should fail'); }
  catch (error) { assert.match(String(error.cause?.message ?? error.message), /variant/); }
});

test('the frame discovers six experiences: UDS usable, the other five defined', () => {
  const r = createStudioRuntime(createSeed());
  const list = r.experiences().list();
  assert.deepEqual(list.map(e => e.key), ['uds', 'exploreshelf', 'createbag', 'managebags', 'creategraphics', 'exportgraphics']);
  for (const e of list) {
    assert.equal(e.status, e.key === 'uds' ? 'usable' : 'defined', e.key);
    assert.ok(e.purpose.length > 0, e.key);
    assert.equal(e.address, `px.studio.${e.key}.definition`);
  }
  assert.deepEqual(r.experiences().usable, ['uds']);
});

test('frame context publishes on USE under px.studio.uds.context.*, never at load', () => {
  const r = createStudioRuntime(createSeed());
  assert.deepEqual(queryPrefix(r.pxc, 'px.studio.uds.context.*'), {});
  const selection = r.experiences().select('uds', 'paint');
  assert.equal(selection.experience, 'uds');
  assert.equal(selection.variant, 'px.studio.uds.paint.definition');
  const effective = r.pxc.get('px.studio.uds.context.effective.paint');
  assert.deepEqual(effective.shared, r.pxc.get('px.studio.uds.definition').shared);
  assert.deepEqual(effective.additional, r.pxc.get('px.studio.uds.paint.definition').additional);
  assert.ok(Object.keys(queryPrefix(r.pxc, 'px.studio.uds.context.*')).length >= 2);
  assert.ok(r.pxc.has('px.receipt.experience-effective'), 'the effective-definition run is on the record');
  const draft = r.experiences().draft({ depiction: 'paint', paint: recipe, hasPhoto: false });
  assert.equal(draft.depiction, 'paint');
  assert.deepEqual(draft.recipe, recipe);
  assert.equal(r.pxc.get('px.studio.uds.context.draft').depiction, 'paint');
});

test('a null recipe label is live: the disc\'s current maker and mold name the artwork', () => {
  const r = createStudioRuntime(createSeed());
  const live = { family: 'pressed-fern', seed: 4242, base: '#3f6b4f', accent: '#c9d6a3', target: 96, label: null };
  r.dispatch({ type: 'disc.create', id: 'disc-proto', manufacturer: 'Discraft', mold: 'Prototype X', category: 'Driver', plastic: 'ESP', weight: 175, color: 'Blue', nickname: '', photo: null, depiction: 'paint', paint: live, bagId: null });
  assert.equal(r.world().objects.Disc['disc-proto'].paint.label, null, 'the recipe retains no frozen label');
  assert.equal(artOf(r, 'disc-proto').inputs[5], 'Discraft · Prototype X');
  assert.equal(artOf(r, 'disc-proto').svg, paintRender('pressed-fern', 4242, '#3f6b4f', '#c9d6a3', 96, 'Discraft · Prototype X'));
  // The pre-release gets its name: the card follows without touching the recipe.
  const moldId = get(r.world(), 'Disc', 'disc-proto').moldId;
  r.dispatch({ type: 'entity.set', entityType: 'Mold', id: moldId, path: 'name', value: 'Halo' });
  assert.equal(artOf(r, 'disc-proto').inputs[5], 'Discraft · Halo');
  assert.equal(r.world().objects.Disc['disc-proto'].paint.label, null, 'renaming the mold never rewrites the recipe');
});

test('a fixed recipe label is an override: it survives mold changes', () => {
  const r = createStudioRuntime(createSeed());
  const fixed = { family: 'pressed-fern', seed: 4242, base: '#3f6b4f', accent: '#c9d6a3', target: 96, label: 'my ace disc' };
  r.dispatch({ type: 'disc.create', id: 'disc-ace', manufacturer: 'Discraft', mold: 'Buzzz', depiction: 'paint', paint: fixed, bagId: null });
  const moldId = get(r.world(), 'Disc', 'disc-ace').moldId;
  r.dispatch({ type: 'entity.set', entityType: 'Mold', id: moldId, path: 'name', value: 'Halo' });
  assert.equal(artOf(r, 'disc-ace').inputs[5], 'my ace disc', 'a typed label is the person\'s words, not the disc\'s');
});

test('validatePaintRecipe takes a null live label and refuses a blank one', () => {
  const base = { family: 'pressed-fern', seed: 1, base: '#ffffff', accent: '#000000', target: 96 };
  assert.equal(validatePaintRecipe({ ...base, label: null }).label, null);
  assert.equal(validatePaintRecipe({ ...base, label: ' Hi ' }).label, 'Hi');
  assert.throws(() => validatePaintRecipe({ ...base, label: '' }), /live label/);
  assert.throws(() => validatePaintRecipe({ ...base, label: '   ' }), /live label/);
});
