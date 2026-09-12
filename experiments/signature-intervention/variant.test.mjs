import test from 'node:test';
import assert from 'node:assert/strict';
import { createSeed } from '../../src/seed.js';
import { cardSvg } from '../../src/presentation.js';
import { freeze } from '../../src/domain.js';
import { createStudioRuntime as createLazy } from './instrumented/lazy/src/runtime.js';
import { createStudioRuntime as createEager } from './instrumented/eager/src/runtime.js';
import { createStudioRuntime as createPlainLazy } from './variants/lazy/src/runtime.js';
import { createStudioRuntime as createPlainEager } from './variants/eager/src/runtime.js';

const arms = [['lazy', createLazy], ['eager', createEager]];
const fixture = (create, events = []) => {
  const runtime = create(createSeed(), { signatureObserver: event => events.push(event) });
  const card = structuredClone(runtime.card('buzzz-mint', 'broadcast').card);
  const render = value => runtime.pxc.call({ address: 'fn.card.svg' }, { card: value });
  return { runtime, card, render };
};

for (const [name, create] of arms) {
  test(`${name}: stable output, reuse, and modified-input correctness`, () => {
    const events = [], { runtime, card, render } = fixture(create, events);
    freeze(card);
    const first = render(card), second = render(card), third = render(card);
    assert.deepEqual(third, first);
    assert.strictEqual(third, second);
    const changed = structuredClone(card);
    changed.nodes.find(node => node.id === 'mold').content = 'controlled variant';
    freeze(changed);
    const altered = render(changed);
    assert.deepEqual(altered, cardSvg({ card: changed }));
    assert.notEqual(altered.svg, first.svg);
    assert.strictEqual(render(changed), altered);
    assert.ok(events.some(event => event.address === 'fn.card.svg' && event.serializedBytes > 0));
    assert.ok(events.every(event => event.serializationMs >= 0));
    assert.equal(runtime.instrumentation.enabled, true);
  });

  test(`${name}: certification boundary and 24-slot eviction`, () => {
    const events = [], { runtime, card, render } = fixture(create, events);
    freeze(card);
    render(card); render(card); render(card);
    const flags = events.filter(event => event.address === 'fn.card.svg').slice(-3).map(event => event.serialized);
    assert.deepEqual(flags, name === 'lazy' ? [true, true, false] : [true, true, true]);
    const beforeBoundary = events.filter(event => event.address === 'fn.card.svg').length;
    render(card);
    const afterBoundary = events.filter(event => event.address === 'fn.card.svg').length;
    assert.equal(afterBoundary, beforeBoundary + 1);
    const computedBefore = runtime.counters.computed;
    for (let i = 0; i < 24; i++) {
      const candidate = structuredClone(card);
      candidate.nodes.find(node => node.id === 'mold').content = `eviction-${i}`;
      freeze(candidate);
      render(candidate);
    }
    render(card);
    assert.ok(runtime.counters.computed > computedBefore);
  });
}

test('lazy and eager arms produce equivalent card output', () => {
  const lazy = fixture(createLazy), eager = fixture(createEager);
  freeze(lazy.card); freeze(eager.card);
  assert.deepEqual(lazy.render(lazy.card), eager.render(eager.card));
});

test('timed variants are observer-free', () => {
  assert.equal('instrumentation' in createPlainLazy(createSeed()), false);
  assert.equal('instrumentation' in createPlainEager(createSeed()), false);
});

test('timed eager arm differs from lazy only at signature selection', async () => {
  const [lazy, eager] = await Promise.all(['lazy', 'eager'].map(name => import(`node:fs/promises`).then(({ readFile }) => readFile(new URL(`./variants/${name}/src/runtime.js`, import.meta.url), 'utf8'))));
  const normalize = source => source.replace(/unchanged && previousVerified \? previousSignature : stable\(\{ revision, inputs \}\)|stable\(\{ revision, inputs \}\)/, '<SIGNATURE>').replace(/const signature = <SIGNATURE>;/, 'const signature = <SIGNATURE>;');
  assert.equal(normalize(lazy), normalize(eager));
});

test('timed lazy arm is the current runtime snapshot modulo relocation', async () => {
  const { readFile } = await import('node:fs/promises');
  const [lazy, current] = await Promise.all([
    readFile(new URL('./variants/lazy/src/runtime.js', import.meta.url), 'utf8'),
    readFile(new URL('../../src/runtime.js', import.meta.url), 'utf8')
  ]);
  const relocate = source => source.replaceAll('../../../../../src/', './').replaceAll('../../../../../pyto/', '../pyto/');
  assert.equal(relocate(lazy), current);
});

for (const [name, createObserved, createPlain] of [['lazy', createLazy, createPlainLazy], ['eager', createEager, createPlainEager]]) {
  test(`${name}: instrumentation is output-neutral`, () => {
    const seed = createSeed();
    const plain = createPlain(seed);
    const observed = createObserved(structuredClone(seed), { signatureObserver() {} });
    const plainCard = plain.card('buzzz-mint', 'broadcast');
    const observedCard = observed.card('buzzz-mint', 'broadcast');
    assert.deepEqual({ card: observedCard.card, fields: observedCard.fields, svg: observedCard.svg }, { card: plainCard.card, fields: plainCard.fields, svg: plainCard.svg });
    assert.equal(observedCard.svg, plainCard.svg);
  });
}
