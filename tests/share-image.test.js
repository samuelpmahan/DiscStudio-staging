import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createSeed } from '../src/seed.js';
import { createStudioRuntime } from '../src/runtime.js';
import { shareImage } from '../src/formats/share-image.js';
import { pxFn, readPql, invokePql } from '../src/core/exec.js';

const fixture = JSON.parse(readFileSync(new URL('./fixtures/share-image.json', import.meta.url)));

test('share image is deterministic and matches final output art fixture', () => {
  const first = shareImage(fixture.input), second = shareImage(fixture.input);
  assert.equal(first.svg, second.svg);
  assert.equal(first.svg, fixture.expectedSvg);
  assert.equal(first.width, 1080);
  assert.equal(first.height, 1080);
  assert.match(first.svg, /data-entry="entry-winner"/);
  assert.match(first.svg, /data:image\/png;base64,AA==/);
  assert.match(first.svg, /Authored winner/);
});

test('share image keeps final composed material and authored state semantics', () => {
  const result = shareImage(structuredClone(fixture.input));
  assert.match(result.svg, />7</);
  assert.match(result.svg, /data-entry="entry-winner"/);
  assert.match(result.svg, /stroke="#b9d789"/);
  assert.match(result.svg, /aria-label="Authored winner"/);
});

test('production PQL can consume the final overlay Part and leave a format record', () => {
  const runtime = createStudioRuntime(createSeed());
  runtime.dispatch({ type: 'battle.score', id: 'entry-1', score: 7 });
  runtime.dispatch({ type: 'battle.highlight', id: 'entry-1' });
  runtime.dispatch({ type: 'battle.winner', id: 'entry-1' });
  const rendered = runtime.scene({ bagId: 'everyday', competitionId: 'putterwarz', roundId: 'hole-1' });
  const input = { rendered: { svg: rendered.svg, width: rendered.width, height: rendered.height }, background: fixture.input.background, label: fixture.input.label };
  runtime.pxc.set('px.input.rendered', input.rendered);
  runtime.pxc.set('px.input.background', input.background);
  runtime.pxc.set('px.input.label', input.label);
  const composition = readPql(JSON.stringify({ PrincipleComponentRender: 'disc-share-image', Ticks: [{ name: 'ShareImage', Calculations: [{ call: 'fn.disc.format.shareImage', with: { rendered: 'px.input.rendered' }, into: 'px.format.shareImage' }] }] }), JSON.parse);
  const run = invokePql(composition, { pxc: runtime.pxc });
  assert.equal(runtime.pxc.get('px.format.shareImage').width, 1080);
  assert.match(runtime.pxc.get('px.format.shareImage').svg, /<svg[^>]+width="1080"/);
  assert.match(runtime.pxc.get('px.format.shareImage').svg, /data-entry="entry-1"/);
  assert.match(runtime.pxc.get('px.format.shareImage').svg, />7</);
  assert.match(runtime.pxc.get('px.format.shareImage').svg, /aria-label="Authored winner"/);
  assert.match(runtime.pxc.get('px.format.shareImage').svg, /data:image|<svg/);
  assert.equal(runtime.pxc.get('px.pql.disc-share-image').PrincipleComponentRender, 'disc-share-image');
  assert.equal(run.Ticks[0].Calculations[0].actualCall, 'fn.disc.format.shareImage');
});

test('single-card and battle scenes both pass through the same share format', () => {
  const runtime = createStudioRuntime(createSeed());
  const context = { bagId: 'everyday', competitionId: 'putterwarz', roundId: 'hole-1' };
  const single = runtime.scene({ ...context, mode: 'card', discId: 'buzzz-mint', presetId: 'showcase' });
  const singleImage = shareImage({ rendered: single });
  assert.equal(singleImage.width, 1080);
  assert.match(singleImage.svg, /Buzzz/);
  runtime.dispatch({ type: 'battle.score', id: 'entry-2', score: 3 });
  runtime.dispatch({ type: 'battle.highlight', id: 'entry-2' });
  runtime.dispatch({ type: 'battle.winner', id: 'entry-2' });
  const battle = runtime.scene(context), battleImage = shareImage({ rendered: battle });
  assert.match(battleImage.svg, />3</);
  assert.match(battleImage.svg, /data-entry="entry-2"/);
  assert.match(battleImage.svg, /aria-label="Authored winner"/);
});

test('malformed rendered SVG is rejected while nested card art is preserved', () => {
  assert.throws(() => shareImage({ svg: '<svg>', width: 100, height: 100 }));
  assert.doesNotThrow(() => shareImage({ svg: '<svg><svg viewBox="0 0 1 1"></svg></svg>', width: 100, height: 100 }));
});
