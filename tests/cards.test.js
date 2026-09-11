import test from 'node:test';
import assert from 'node:assert/strict';
import { createSeed } from '../src/seed.js';
import { createStudioRuntime } from '../src/runtime.js';
import { classifyTick } from '../src/core/exec.js';
import { validateWorld, validatePreset } from '../src/domain.js';
import { defaultCards, PROJECTIONS } from '../src/cards.js';
import { validate } from '../pyto/viewer/adapters.js';

const make = () => createStudioRuntime(createSeed());
const context = { bagId: 'everyday', competitionId: 'putterwarz', roundId: 'hole-1' };
// dispatch wraps every applyCommand failure in a PQL error; the real message is on its .cause chain.
const because = pattern => error => { let text = ''; for (let e = error; e; e = e.cause) text += `${e.message} | `; assert.match(text, pattern); return true; };

/* ------------------------------------------------------------------ */
/* the model: the preset IS the projection layer                       */
/* ------------------------------------------------------------------ */

test('createSeed: broadcast inherits background and overrides sponsor; discImage overrides its own background; the instance override exists', () => {
  const w = createSeed();
  assert.equal(w.presets.broadcast.background, null, 'broadcast inherits background from global');
  assert.equal(w.presets.broadcast.sponsor, 'CHAINSPOT', 'broadcast is the only preset that overrides sponsor');
  assert.equal(w.presets.showcase.sponsor ?? null, null, 'showcase inherits sponsor');
  assert.equal(w.presets.discImage.background, '#e6ebde', 'discImage keeps its own background');
  assert.equal(w.presets.discImage.font ?? null, null, 'discImage inherits font');
  assert.equal(w.cards.instances.shelf['buzzz-mint'].accent, '#d47d54');
  assert.deepEqual(Object.keys(w.cards.global).sort(), ['accent', 'background', 'font', 'foreground', 'radius', 'sponsor']);
  assert.equal(w.cards.projections, undefined, 'there is no separate projection layer: the preset IS the projection layer');
});

// Kills: validateWorld silently leaving old drafts without `cards`, keeping a
// task-78 `projections` key around, or mutating a frozen world instead of
// returning a new one.
test('validateWorld fills the card cascade defaults for a draft that lacks them, drops a task-78 projections key, and never mutates a frozen world', () => {
  const w = createSeed(); delete w.cards;
  const frozen = Object.freeze(w);
  const filled = validateWorld(frozen);
  assert.deepEqual(filled.cards, defaultCards());
  assert.notEqual(filled, frozen, 'a new world is returned rather than the frozen one mutated');
  assert.equal(frozen.cards, undefined, 'the frozen draft itself is untouched');

  const old = createSeed();
  old.cards = { ...old.cards, projections: { shelf: {}, bag: {}, single: {}, competition: { sponsor: 'X' } } };
  const frozenOld = Object.freeze(old);
  const normalized = validateWorld(frozenOld);
  assert.equal(normalized.cards.projections, undefined, 'the task-78 projections layer is dropped: its values were never the presets\' own');
  assert.deepEqual(Object.keys(normalized.cards).sort(), ['global', 'instances']);
  assert.ok('projections' in frozenOld.cards, 'the frozen draft itself is untouched');
});

/* ------------------------------------------------------------------ */
/* effective tokens and provenance over global -> preset -> instance    */
/* ------------------------------------------------------------------ */

test('effective tokens cascade global -> preset -> instance; a preset field set to null inherits again; null on global is refused; preset.set changes provenance to preset', () => {
  const r = make();
  let eff = r.cards.effective('shelf', 'buzzz-mint', context);
  assert.equal(eff.tokens.accent, '#d47d54', 'the seeded instance override wins');
  assert.equal(eff.provenance.accent, 'instance');
  assert.equal(eff.tokens.background, r.world().presets.discImage.background, 'shelf composes with discImage, which overrides background');
  assert.equal(eff.provenance.background, 'preset');
  assert.equal(eff.presetId, 'discImage');

  r.dispatch({ type: 'preset.set', id: 'discImage', patch: { background: null } });
  eff = r.cards.effective('shelf', 'buzzz-mint', context);
  assert.equal(eff.provenance.background, 'global', 'clearing the preset override inherits again');
  assert.equal(eff.tokens.background, r.world().cards.global.background);

  r.dispatch({ type: 'preset.set', id: 'discImage', patch: { accent: '#222222' } });
  eff = r.cards.effective('bag', 'zone-peach', context);
  assert.equal(eff.provenance.accent, 'preset', 'a preset.set edit is visible as a preset-layer override');
  assert.equal(eff.tokens.accent, '#222222');

  assert.throws(() => r.dispatch({ type: 'cards.set', layer: 'global', token: 'background', value: null }), because(/never inherits/));
  assert.throws(() => r.dispatch({ type: 'cards.set', layer: 'global', token: 'bogus', value: '#000000' }), because(/Unknown card token/));
  assert.throws(() => r.dispatch({ type: 'cards.set', layer: 'instance', projection: 'nowhere', discId: 'buzzz-mint', token: 'radius', value: 5 }), because(/Unknown card projection/));
  assert.throws(() => r.dispatch({ type: 'cards.set', layer: 'preset', presetId: 'nowhere', token: 'radius', value: 5 }), because(/Missing presentation/));
});

/* ------------------------------------------------------------------ */
/* recompose: changed reaches only the projections an edit changes     */
/* ------------------------------------------------------------------ */

test('recompose: a global radius edit changes all four projections; a global background edit changes exactly single and competition; a preset.set on discImage.accent changes exactly shelf and bag; an instance edit changes exactly one', () => {
  const r = make(), discId = 'zone-peach'; // no seeded instance override
  // `changed` is per address (runtime.js recompose): the material each projection's card
  // was composed from, against the previous recompose of the same address.
  r.cards.recompose(discId, context); // the first recompose of a session changes nothing
  const baseline = r.cards.recompose(discId, context);
  assert.deepEqual(Object.values(baseline.cards).map(c => c.changed), [false, false, false, false]);
  assert.deepEqual(Object.keys(baseline.cards), PROJECTIONS);

  r.dispatch({ type: 'cards.set', layer: 'global', token: 'radius', value: 30 });
  const radiusEdit = r.cards.recompose(discId, context);
  assert.deepEqual(Object.values(radiusEdit.cards).map(c => c.changed), [true, true, true, true], 'both discImage and broadcast inherit radius, so all four projections move');
  r.cards.recompose(discId, context); // settle back to reused

  r.dispatch({ type: 'cards.set', layer: 'global', token: 'background', value: '#0a0a0a' });
  const backgroundEdit = r.cards.recompose(discId, context);
  assert.deepEqual(Object.entries(backgroundEdit.cards).filter(([, c]) => c.changed).map(([p]) => p), ['single', 'competition'], 'discImage overrides its own background, so shelf/bag do not inherit a global background edit');
  r.cards.recompose(discId, context);

  r.dispatch({ type: 'preset.set', id: 'discImage', patch: { accent: '#654321' } });
  const presetEdit = r.cards.recompose(discId, context);
  assert.deepEqual(Object.entries(presetEdit.cards).filter(([, c]) => c.changed).map(([p]) => p), ['shelf', 'bag'], 'only the projections that compose with discImage move');
  r.cards.recompose(discId, context);

  r.dispatch({ type: 'cards.set', layer: 'instance', projection: 'single', discId, token: 'radius', value: 50 });
  const instanceEdit = r.cards.recompose(discId, context);
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

test('the existing surfaces carry the cascade: OnTheCourse carries the broadcast sponsor lockup, clearing it removes it from the single card too, and the minimal preset still renders its own paper background', () => {
  const r = make();
  const scene = r.scene(context);
  assert.match(scene.svg, /CHAINSPOT/, 'competition composes with broadcast, whose sponsor override reaches the OnTheCourse overlay');
  const single = r.card('buzzz-mint', 'broadcast', context, null, 'single');
  assert.match(single.svg, /CHAINSPOT/, 'single also composes with broadcast, so it carries the same lockup');

  r.dispatch({ type: 'preset.set', id: 'broadcast', patch: { sponsor: null } });
  const clearedSingle = r.card('buzzz-mint', 'broadcast', context, null, 'single');
  assert.doesNotMatch(clearedSingle.svg, /CHAINSPOT/, 'a null sponsor inherits the empty global sponsor: no lockup at all when broadcast\'s sponsor is set to null');

  const minimal = r.card('buzzz-mint', 'minimal', context, null, 'single');
  assert.match(minimal.svg, /#f9f7ef/i, 'minimal keeps its own paper background after the preset-is-the-projection-layer retrofit');
});

test('the Component Editor\'s preset controls are live: after preset.set on a preset\'s background, the composed card carries the value', () => {
  const r = make();
  r.dispatch({ type: 'preset.set', id: 'broadcast', patch: { background: '#123456' } });
  const rendered = r.card('buzzz-mint', 'broadcast', context);
  assert.match(rendered.svg, /#123456/i);
});

/* ------------------------------------------------------------------ */
/* PQL: overrides and inherits                                         */
/* ------------------------------------------------------------------ */

test('query(\'overrides\') lists the seed\'s preset and instance overrides', () => {
  const r = make();
  const rows = r.cards.query('overrides');
  assert.ok(rows.some(row => row.layer === 'preset' && row.presetId === 'broadcast' && row.token === 'sponsor' && row.value === 'CHAINSPOT'));
  assert.ok(rows.some(row => row.layer === 'preset' && row.presetId === 'discImage' && row.token === 'background' && row.value === '#e6ebde'));
  assert.ok(rows.some(row => row.layer === 'instance' && row.projection === 'shelf' && row.discId === 'buzzz-mint' && row.token === 'accent' && row.value === '#d47d54'));
});

test('query(\'inherits\', { token }) matches the world', () => {
  const r = make();
  const sponsor = r.cards.query('inherits', { token: 'sponsor' });
  assert.equal(sponsor.presets.broadcast, false, 'broadcast overrides sponsor');
  assert.equal(sponsor.presets.showcase, true);
  assert.equal(sponsor.presets.minimal, true);
  assert.equal(sponsor.presets.discImage, true);
  assert.equal(sponsor.projections.single, false, 'single composes with broadcast');
  assert.equal(sponsor.projections.competition, false, 'competition also composes with broadcast');
  assert.equal(sponsor.projections.shelf, true, 'shelf composes with discImage, which inherits sponsor');
  assert.equal(sponsor.projections.bag, true);

  const accent = r.cards.query('inherits', { token: 'accent' });
  assert.equal(accent.presets.discImage, true, 'discImage inherits accent at the preset layer');
  assert.equal(accent.projections.shelf, true, 'no preset-level accent override for shelf/bag either');

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
  assert.equal(provenance.background, 'global', 'broadcast inherits background, so single does too');
});

/* ------------------------------------------------------------------ */
/* the sponsor lockup node                                             */
/* ------------------------------------------------------------------ */

test('a non-empty sponsor token appends a static, validatable text node', () => {
  const r = make();
  const rendered = r.card('buzzz-mint', 'broadcast', context, null, 'competition');
  const sponsorNode = rendered.card.preset.nodes.find(n => n.id === 'sponsor');
  assert.ok(sponsorNode, 'competition composes with broadcast, whose own sponsor override applies');
  assert.equal(sponsorNode.binding, '');
  assert.equal(sponsorNode.text, 'CHAINSPOT');
  assert.equal(sponsorNode.size, 11);
  assert.equal(sponsorNode.bold, true);
  assert.equal(sponsorNode.align, 'right');
  assert.equal(sponsorNode.color, rendered.card.preset.accent);
  assert.match(rendered.svg, /CHAINSPOT/);
  assert.equal(validatePreset(rendered.card.preset), rendered.card.preset, 'the preset with the sponsor node appended must still pass validatePreset');

  r.dispatch({ type: 'preset.set', id: 'broadcast', patch: { sponsor: null } });
  const cleared = r.card('buzzz-mint', 'broadcast', context, null, 'competition');
  assert.ok(!cleared.card.preset.nodes.some(n => n.id === 'sponsor'), 'clearing broadcast\'s sponsor removes the lockup: global.sponsor is empty');
});
