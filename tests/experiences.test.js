import test from 'node:test';
import assert from 'node:assert/strict';
import { createStudioRuntime } from '../src/runtime.js';
import { createSeed } from '../src/seed.js';
import { queryPrefix, readPql, invokePql, pxFn } from '../src/core/exec.js';
import { FAMILIES } from '../pyto/consumers/discstudio-card/port/painter/painter.mjs';

test('Studio loads general UDS and referenced photo/paint specializations without creating a specimen or context', () => {
  const initial = createSeed(), before = structuredClone(initial), runtime = createStudioRuntime(initial);
  const parts = queryPrefix(runtime.pxc, 'px.studio.uds.*');
  for (const type of ['photo', 'paint']) {
    const variant = parts[`px.studio.uds.${type}.definition`];
    assert.equal(variant.specializes, 'px.studio.uds.definition');
    assert.equal(runtime.pxc.get(variant.discVizType).value, type);
    assert.equal(variant.shared, undefined, 'common requirements are referenced, not copied');
  }
  assert.deepEqual(parts['px.studio.uds.paint.families'].values, FAMILIES);
  const starters = parts['px.studio.uds.paint.starterfamilies'].values;
  assert.equal(starters.length, 3);
  assert.ok(starters.every(family => FAMILIES.includes(family)));
  assert.deepEqual(runtime.world(), before);
  assert.deepEqual(queryPrefix(runtime.pxc, 'px.studio.uds.context.*'), {});
  for (const address of runtime.pxc.get('px.studio.experiences').definitions) assert.ok(runtime.pxc.has(address));
});

test('an ordinary PQL prefix binding can consume the loaded Experience Parts and record their use', () => {
  const runtime = createStudioRuntime(createSeed());
  runtime.pxc.register(pxFn('fn.test.experience'), ({ definitions }) => Object.keys(definitions).sort());
  const doc = readPql(JSON.stringify({ PrincipleComponentRender: 'experience-discovery', Ticks: [{ name: 'Discover', Calculations: [{ call: 'fn.test.experience', with: { definitions: 'px.studio.uds.*' }, into: 'px.test.experience.names' }] }] }), JSON.parse);
  const run = invokePql(doc, runtime.pxc);
  const names = runtime.pxc.get('px.test.experience.names');
  assert.ok(names.includes('px.studio.uds.paint.definition'));
  assert.ok(names.includes('px.studio.uds.photo.definition'));
  const invocation = run.Ticks[0].Calculations[0];
  assert.equal(invocation.with.definitions, 'px.studio.uds.*');
  assert.deepEqual(Object.keys(invocation.inputs.definitions).sort(), names);
  assert.deepEqual(invocation.produces, ['px.test.experience.names']);
  assert.deepEqual(runtime.pxc.get('px.pql.experience-discovery'), run);
});

test('existing creation without a photo produces repeatable painted art through the shared render chain', () => {
  const runtime = createStudioRuntime(createSeed());
  runtime.dispatch({ type: 'disc.create', id: 'uds-painted', manufacturer: 'Study', mold: 'Repeatable', color: 'Mint', photo: null });
  const card = runtime.card('uds-painted', 'discImage', {}, null, 'shelf');
  const art = runtime.pxc.get(card.run.trace.find(row => row.call === 'fn.disc.art').output);
  assert.equal(runtime.world().objects.Disc['uds-painted'].photo, null);
  assert.equal(art.kind, 'painted');
  assert.ok(FAMILIES.includes(art.inputs[0]));
  assert.equal(runtime.card('uds-painted', 'discImage', {}, null, 'shelf').svg, card.svg);
  assert.ok(runtime.pxc.has('px.receipt.display-card'));
});
