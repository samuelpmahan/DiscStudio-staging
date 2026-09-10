import test from 'node:test';
import assert from 'node:assert/strict';
import { createSeed } from '../src/seed.js';
import { createStudioRuntime } from '../src/runtime.js';
import { classifyTick, queryPrefix } from '../src/core/exec.js';
import { validateWorld, validatePreset } from '../src/domain.js';
import { defaultCards, PROJECTIONS } from '../src/cards.js';
import { validate } from '../pyto/viewer/adapters.js';

const make = () => createStudioRuntime(createSeed());
const context = { bagId: 'everyday', competitionId: 'putterwarz', roundId: 'hole-1' };
// dispatch wraps every applyCommand failure in a PQL error; the real message is on its .cause chain.
const because = pattern => error => { let text = ''; for (let e = error; e; e = e.cause) text += `${e.message} | `; assert.match(text, pattern); return true; };

/* ------------------------------------------------------------------ */
/* the model: defaults, validateWorld filling old drafts               */
/* ------------------------------------------------------------------ */

test('createSeed ships one projection override and one instance override', () => {
  const w = createSeed();
  assert.equal(w.cards.projections.competition.sponsor, 'CHAINSPOT');
  assert.equal(w.cards.instances.shelf['buzzz-mint'].accent, '#d47d54');
  assert.deepEqual(Object.keys(w.cards.global).sort(), ['accent', 'background', 'font', 'foreground', 'radius', 'sponsor']);
});

// Kills: validateWorld silently leaving old drafts without `cards`, or
// mutating a frozen world instead of returning a new one.
test('validateWorld fills the card cascade defaults for a draft that lacks them, without mutating a frozen world', () => {
  const w = createSeed(); delete w.cards;
  const frozen = Object.freeze(w);
  const filled = validateWorld(frozen);
  assert.deepEqual(filled.cards, defaultCards());
  assert.notEqual(filled, frozen, 'a new world is returned rather than the frozen one mutated');
  assert.equal(frozen.cards, undefined, 'the frozen draft itself is untouched');
});

/* ------------------------------------------------------------------ */
/* effective tokens and provenance over three layers                   */
/* ------------------------------------------------------------------ */

test('effective tokens cascade global -> projection -> instance; clearing an override inherits again; null on global is refused', () => {
  const r = make();
  let eff = r.cards.effective('shelf', 'buzzz-mint', context);
  assert.equal(eff.tokens.accent, '#d47d54', 'the seeded instance override wins');
  assert.equal(eff.provenance.accent, 'instance');
  assert.equal(eff.tokens.background, r.world().cards.global.background, 'no override at all: falls through to global');
  assert.equal(eff.provenance.background, 'global');

  r.dispatch({ type: 'cards.set', layer: 'projection', projection: 'shelf', token: 'background', value: '#111111' });
  eff = r.cards.effective('shelf', 'buzzz-mint', context);
  assert.equal(eff.tokens.background, '#111111');
  assert.equal(eff.provenance.background, 'projection');

  r.dispatch({ type: 'cards.set', layer: 'instance', projection: 'shelf', discId: 'buzzz-mint', token: 'accent', value: null });
  eff = r.cards.effective('shelf', 'buzzz-mint', context);
  assert.equal(eff.provenance.accent, 'global', 'clearing the instance override inherits again (no projection override for accent either)');
  assert.equal(eff.tokens.accent, r.world().cards.global.accent);

  assert.throws(() => r.dispatch({ type: 'cards.set', layer: 'global', token: 'background', value: null }), because(/never inherits/));
  assert.throws(() => r.dispatch({ type: 'cards.set', layer: 'global', token: 'bogus', value: '#000000' }), because(/Unknown card token/));
  assert.throws(() => r.dispatch({ type: 'cards.set', layer: 'projection', projection: 'nowhere', token: 'radius', value: 5 }), because(/Unknown card projection/));
});

/* ------------------------------------------------------------------ */
/* recompose: changed reaches only the projections an edit changes     */
/* ------------------------------------------------------------------ */

test('recompose: a global edit changes all four projections; a projection or instance edit changes exactly one', () => {
  const r = make();
  r.cards.recompose('buzzz-mint', context); // warm the memo ring
  const baseline = r.cards.recompose('buzzz-mint', context);
  assert.deepEqual(Object.values(baseline.cards).map(c => c.changed), [false, false, false, false]);
  assert.deepEqual(Object.keys(baseline.cards), PROJECTIONS);

  r.dispatch({ type: 'cards.set', layer: 'global', token: 'radius', value: 30 });
  const globalEdit = r.cards.recompose('buzzz-mint', context);
  assert.deepEqual(Object.values(globalEdit.cards).map(c => c.changed), [true, true, true, true]);
  r.cards.recompose('buzzz-mint', context); // settle back to reused

  r.dispatch({ type: 'cards.set', layer: 'projection', projection: 'bag', token: 'radius', value: 5 });
  const projectionEdit = r.cards.recompose('buzzz-mint', context);
  assert.deepEqual(Object.entries(projectionEdit.cards).filter(([, c]) => c.changed).map(([p]) => p), ['bag']);
  r.cards.recompose('buzzz-mint', context);

  r.dispatch({ type: 'cards.set', layer: 'instance', projection: 'single', discId: 'buzzz-mint', token: 'radius', value: 50 });
  const instanceEdit = r.cards.recompose('buzzz-mint', context);
  assert.deepEqual(Object.entries(instanceEdit.cards).filter(([, c]) => c.changed).map(([p]) => p), ['single']);
});

test('the recompose receipt names the four projections\' Ticks, and runRecord validates it', () => {
  const r = make();
  const { receipt } = r.cards.recompose('buzzz-mint', context);
  const cardTicks = receipt.trace.filter(row => row.call === 'fn.card.compose').map(row => row.tick);
  assert.deepEqual(cardTicks, ['Card:shelf', 'Card:bag', 'Card:single', 'Card:competition']);
  const cascadeTicks = receipt.trace.filter(row => row.call === 'fn.cards.effective').map(row => row.tick);
  assert.deepEqual(cascadeTicks, ['Cascade:shelf', 'Cascade:bag', 'Cascade:single', 'Cascade:competition']);

  const { record } = r.runRecord('cards-recompose');
  assert.equal(validate(record), record);
  assert.equal(record.source.runtime, 'discstudio');
});

// Task 57: inside a Tick the Calculations are a sequence in declared order;
// fn.cards.apply reads what fn.cards.effective produced earlier in the same
// Cascade Tick, so classifyTick calls it a chain, not a parallel Tick.
test('the Cascade Tick is classified a chain by classifyTick', () => {
  const r = make();
  r.cards.effective('single', 'buzzz-mint', context);
  const composition = r.pxc.get('px.pql.cards-effective');
  assert.equal(composition.Ticks.length, 1);
  assert.match(composition.Ticks[0].name, /^Cascade:/);
  assert.equal(classifyTick(composition.Ticks[0]), 'chain');
});

/* ------------------------------------------------------------------ */
/* the existing surfaces carry the cascade                             */
/* ------------------------------------------------------------------ */

test('the existing surfaces carry the cascade: single/shelf/bag/competition all read from world.cards', () => {
  const r = make();
  r.dispatch({ type: 'cards.set', layer: 'global', token: 'background', value: '#0a0a0a' });
  const single = r.card('buzzz-mint', 'broadcast', context);
  assert.match(single.svg, /#0a0a0a/i, 'the single-card surface (default projection) carries a global edit');

  const scene = r.scene(context);
  assert.match(scene.svg, /CHAINSPOT/, 'the seeded competition.sponsor override reaches the OnTheCourse overlay');
  assert.doesNotMatch(single.svg, /CHAINSPOT/, 'single never inherits a competition-projection override');
});

/* ------------------------------------------------------------------ */
/* PQL: overrides and inherits                                         */
/* ------------------------------------------------------------------ */

test('query(\'overrides\') lists the seed\'s projection and instance overrides', () => {
  const r = make();
  const rows = r.cards.query('overrides');
  assert.ok(rows.some(row => row.layer === 'projection' && row.projection === 'competition' && row.token === 'sponsor' && row.value === 'CHAINSPOT'));
  assert.ok(rows.some(row => row.layer === 'instance' && row.projection === 'shelf' && row.discId === 'buzzz-mint' && row.token === 'accent' && row.value === '#d47d54'));
});

test('query(\'inherits\', { token }) matches the world', () => {
  const r = make();
  const sponsor = r.cards.query('inherits', { token: 'sponsor' });
  assert.equal(sponsor.projections.competition, false, 'competition overrides sponsor at the projection layer');
  assert.equal(sponsor.projections.shelf, true, 'shelf has no projection-level sponsor override');
  assert.equal(sponsor.projections.bag, true);
  assert.equal(sponsor.projections.single, true);

  const accent = r.cards.query('inherits', { token: 'accent' });
  assert.equal(accent.projections.shelf, true, 'shelf has no PROJECTION-level accent override (only an instance one)');

  r.cards.effective('shelf', 'buzzz-mint', context);
  const afterCompose = r.cards.query('inherits', { token: 'accent' });
  assert.equal(afterCompose.instances.some(x => x.projection === 'shelf' && x.discId === 'buzzz-mint'), false, 'buzzz-mint overrides accent at the instance layer, so it does not inherit it');

  r.cards.effective('bag', 'zone-peach', context);
  const withUninherited = r.cards.query('inherits', { token: 'accent' });
  assert.ok(withUninherited.instances.some(x => x.projection === 'bag' && x.discId === 'zone-peach'), 'zone-peach has no override anywhere, so it inherits accent from global');
});

test('query(\'provenance\') returns null before a projection/disc pair has ever been composed', () => {
  const r = make();
  assert.equal(r.cards.query('provenance', { projection: 'single', discId: 'buzzz-mint' }), null);
  r.cards.effective('single', 'buzzz-mint', context);
  const provenance = r.cards.query('provenance', { projection: 'single', discId: 'buzzz-mint' });
  assert.equal(provenance.background, 'global');
});

/* ------------------------------------------------------------------ */
/* the sponsor lockup node                                             */
/* ------------------------------------------------------------------ */

test('a non-empty sponsor token appends a static, validatable text node', () => {
  const r = make();
  const rendered = r.card('buzzz-mint', 'broadcast', context, null, 'competition');
  const sponsorNode = rendered.card.preset.nodes.find(n => n.id === 'sponsor');
  assert.ok(sponsorNode, 'competition inherits the seeded sponsor lockup');
  assert.equal(sponsorNode.binding, '');
  assert.equal(sponsorNode.text, 'CHAINSPOT');
  assert.equal(sponsorNode.size, 11);
  assert.equal(sponsorNode.bold, true);
  assert.equal(sponsorNode.align, 'right');
  assert.equal(sponsorNode.color, rendered.card.preset.accent);
  assert.match(rendered.svg, /CHAINSPOT/);
  assert.equal(validatePreset(rendered.card.preset), rendered.card.preset, 'the preset with the sponsor node appended must still pass validatePreset');

  const single = r.card('buzzz-mint', 'broadcast', context, null, 'single');
  assert.ok(!single.card.preset.nodes.some(n => n.id === 'sponsor'), 'single has no sponsor override, so no lockup node is added');
});

/* ------------------------------------------------------------------ */
/* the findings are Parts: one prefix query reads them                 */
/* ------------------------------------------------------------------ */

test('the findings are published as proposal.cards.* Parts and every friction carries its for', () => {
  const r = make();
  const rows = Object.values(queryPrefix(r.pxc, 'proposal.cards.*'));
  assert.ok(rows.length >= 6, 'strengths and frictions both ship');
  for (const row of rows) {
    assert.ok(['strength', 'friction'].includes(row.kind), row.address);
    if (row.kind === 'friction') { assert.ok(row.for && row.workaround && row.proposal, `${row.address} carries for, workaround and proposal`); }
  }
  assert.deepEqual(new Set(r.select('proposal.cards.').map(x => x.address)), new Set(rows.map(x => x.address)));
});
