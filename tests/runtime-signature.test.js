import test from 'node:test';
import assert from 'node:assert/strict';
import { createStudioRuntime } from '../src/runtime.js';
import { createSeed } from '../src/seed.js';
import { freeze } from '../src/domain.js';
import { cardSvg } from '../src/presentation.js';

const fixture = () => {
  const runtime = createStudioRuntime(createSeed());
  const card = structuredClone(runtime.card('buzzz-mint', 'broadcast').card);
  return { runtime, card, render: value => runtime.pxc.call({ address: 'fn.card.svg' }, { card: value }) };
};

test('repeated deeply frozen inputs keep output identity and the existing memo Part shape', () => {
  const { runtime, card, render } = fixture();
  freeze(card);
  assert.strictEqual(render(card), render(card));
  for (const { value } of runtime.select('px.memo.card.svg.')) assert.deepEqual(Object.keys(value).sort(), ['id', 'revision', 'signature', 'value']);
});

test('mutable input identity never substitutes for content equality', () => {
  const { card, render } = fixture(), before = render(card).svg;
  card.nodes.find(n => n.id === 'mold').content = 'A different mold';
  assert.equal(render(card).svg, cardSvg({ card }).svg);
  assert.notEqual(render(card).svg, before);
});

test('a shallow-frozen input with mutable descendants is reserialized', () => {
  const { card, render } = fixture(); Object.freeze(card);
  const before = render(card).svg;
  card.nodes.find(n => n.id === 'mold').content = 'Changed inside the shallow freeze';
  assert.equal(render(card).svg, cardSvg({ card }).svg);
  assert.notEqual(render(card).svg, before);
});

test('mutating then deeply freezing the same input does not reuse its pre-freeze signature', () => {
  const { card, render } = fixture(), before = render(card).svg;
  card.nodes.find(n => n.id === 'mold').content = 'Changed before certification';
  freeze(card);
  const after = render(card).svg;
  assert.notEqual(after, before); assert.equal(after, cardSvg({ card }).svg);
  assert.equal(render(card).svg, after);
});

test('frozen accessor-backed inputs do not acquire an immutable signature', () => {
  const { card, render } = fixture(); let title = 'First';
  const mold = card.nodes.find(n => n.id === 'mold');
  Object.defineProperty(mold, 'content', { enumerable: true, get: () => title });
  freeze(card);
  const before = render(card).svg; title = 'Second';
  assert.equal(render(card).svg, cardSvg({ card }).svg);
  assert.notEqual(render(card).svg, before);
});

test('a reused signature still looks up the live 24-slot memo ring', () => {
  const { runtime, card, render } = fixture();
  for (let i = 0; i < 30; i++) {
    const next = structuredClone(card); next.nodes.find(n => n.id === 'mold').content = `Candidate ${i}`;
    freeze(next); assert.equal(render(next).svg, cardSvg({ card: next }).svg);
  }
  freeze(card);
  assert.equal(render(card).svg, cardSvg({ card }).svg);
  assert.equal(runtime.select('px.memo.card.svg.').length, 24);
});

test('preset edits invalidate the shared rendering chain and unchanged repeats still reuse', () => {
  const runtime = createStudioRuntime(createSeed()), before = runtime.card('buzzz-mint', 'broadcast');
  runtime.dispatch({ type: 'preset.set', id: 'broadcast', nodeId: 'maker', patch: { x: 41 } });
  const after = runtime.card('buzzz-mint', 'broadcast'), repeat = runtime.card('buzzz-mint', 'broadcast');
  assert.notEqual(after.svg, before.svg); assert.equal(repeat.svg, after.svg);
  assert.equal(repeat.run.computed, 0); assert.ok(repeat.run.reused > 0);
});
