import test from 'node:test';
import assert from 'node:assert/strict';
import { createSeed } from '../src/seed.js';
import { createStudioRuntime } from '../src/runtime.js';
import { discoverFields, materialFor, currentBattle, clone, validateWorld } from '../src/domain.js';
import { fieldNode } from '../src/presentation.js';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { validate } from '../pyto/viewer/adapters.js';
import { renderRecord } from '../pyto/viewer/tick-viewer.js';
import { buildPage, composePage } from '../pyto/viewer/embed.mjs';
import { render as painterRender } from '../pyto/consumers/discstudio-card/port/painter/painter.mjs';
const make = () => createStudioRuntime(createSeed());
const context = { bagId: 'everyday', competitionId: 'putterwarz', roundId: 'hole-1' };

test('studio art and single card Parts are byte-identical to the ported painter', () => {
  const r = make(), rendered = r.card('buzzz-mint', 'broadcast', context);
  const artTrace = rendered.run.trace.find(step => step.call === 'fn.disc.art');
  const art = r.pxc.get(artTrace.output);
  assert.equal(art.svg, painterRender(...art.inputs));
});

test('ported painter inputs use sanitized authored colors', () => {
  const r = make();
  r.dispatch({ type: 'entity.set', entityType: 'Disc', id: 'buzzz-mint', path: 'artBase', value: 'url(#bad)' });
  r.dispatch({ type: 'entity.set', entityType: 'Disc', id: 'buzzz-mint', path: 'artAccent', value: '#abc' });
  const rendered = r.card('buzzz-mint', 'broadcast', context);
  const art = r.pxc.get(rendered.run.trace.find(step => step.call === 'fn.disc.art').output);
  assert.deepEqual(art.inputs.slice(2, 4), ['#e6ebde', '#456157']);
  assert.equal(art.svg, painterRender(...art.inputs));
});

test('manufacturer, mold, optional values and every registered field are discoverable', () => {
  const r = make(), c = r.card('buzzz-mint', 'broadcast', context), paths = c.fields.map(f => f.path);
  for (const p of ['disc.mold.name', 'disc.mold.manufacturer.name', 'disc.photo', 'disc.mold.flight.speed', 'disc.weight', 'bag.name', 'competition.name']) assert.ok(paths.includes(p), p);
  assert.match(c.svg, /Discraft/); assert.match(c.svg, /Buzzz/);
  r.dispatch({ type: 'entity.set', entityType: 'Mold', id: 'buzzz', path: 'flight', value: {} });
  const next = r.card('buzzz-mint', 'broadcast', context);
  assert.equal(next.fields.find(f => f.path === 'disc.mold.flight.speed').available, false);
  assert.match(next.svg, /Buzzz/);
});
test('new schema fields automatically resolve, compose, serialize and rehydrate', () => {
  const r = make();
  r.dispatch({ type: 'schema.addField', entityType: 'Disc', name: 'retailValue', fieldType: 'number', label: 'Retail value' });
  r.dispatch({ type: 'entity.set', entityType: 'Disc', id: 'buzzz-mint', path: 'retailValue', value: 24 });
  const field = r.card('buzzz-mint', 'broadcast', context).fields.find(f => f.path === 'disc.retailValue');
  r.dispatch({ type: 'preset.node.add', id: 'broadcast', node: { ...fieldNode(field), x: 138, y: 145, h: 20, size: 14 } });
  const restored = createStudioRuntime(JSON.parse(JSON.stringify(r.world())));
  assert.match(restored.card('buzzz-mint', 'broadcast', context).svg, />24</);
});
test('unregistered fields and new related domain objects are surfaced, not silently discarded', () => {
  const w = createSeed(); w.schemas.Sponsor = { label: 'Sponsor', fields: { name: { type: 'text', label: 'Sponsor name' } } };
  w.schemas.Disc.fields.sponsor = { type: 'ref', target: 'Sponsor', key: 'sponsorId', label: 'Sponsor' };
  w.objects.Sponsor = { club: { id: 'club', type: 'Sponsor', name: 'Local Club' } }; w.objects.Disc['buzzz-mint'].sponsorId = 'club';
  w.objects.Disc['buzzz-mint'].customNote = 'Useful fact';
  const fields = discoverFields(materialFor(w, { disc: { type: 'Disc', id: 'buzzz-mint' } }));
  assert.equal(fields.find(f => f.path === 'disc.sponsor.name').value, 'Local Club');
  assert.equal(fields.find(f => f.path === 'disc.customNote').value, 'Useful fact');
});
test('shelf and comparison share physical references; bags do not duplicate discs', () => {
  const r = make(); r.dispatch({ type: 'bag.membership', bagId: 'luna-bag', discId: 'buzzz-mint', include: true });
  r.dispatch({ type: 'entity.set', entityType: 'Disc', id: 'buzzz-mint', path: 'nickname', value: 'Edited once' });
  assert.match(r.scene({ ...context }).svg, /Edited once/);
  r.dispatch({ type: 'bag.membership', bagId: 'luna-bag', discId: 'buzzz-mint', include: false });
  assert.ok(r.world().objects.Disc['buzzz-mint']);
});
test('actual PQL consumes rendered Parts, and repeat rendering reuses actual memoized values', () => {
  const r = make(), first = r.scene(context), again = r.scene(context);
  assert.equal(first.svg, again.svg); assert.equal(again.run.computed, 0); assert.ok(again.run.reused > 0);
  const step = again.run.trace.at(-1); assert.equal(step.call, 'fn.overlay.svg'); assert.equal(step.inputs.scene, 'px.course.scene');
  assert.ok(r.select('px.memo.card.compose.').length);
  assert.equal(r.pxc.get('px.course.svg').svg, again.svg);
});
test('layout and score changes reuse upstream disc art; selected-state changes remain separate from domain', () => {
  const r = make(); r.scene(context);
  r.dispatch({ type: 'layout.set', patch: { anchor: 'top-right' } });
  const moved = r.scene(context); assert.ok(moved.run.trace.filter(t => t.call === 'fn.disc.art').every(t => t.reused));
  r.dispatch({ type: 'battle.score', id: 'entry-1', score: 0 });
  const scored = r.scene(context); assert.ok(scored.run.trace.filter(t => t.call === 'fn.disc.art').every(t => t.reused));
  assert.match(scored.svg, />0</); assert.equal(r.world().objects.Disc['buzzz-mint'].score, undefined);
});
test('presentation edits change real scene and apply to other discs without a second renderer', () => {
  const r = make(); r.dispatch({ type: 'preset.set', id: 'broadcast', nodeId: 'maker', patch: { x: 40, size: 17 } });
  const scene = r.scene(context); assert.match(scene.svg, /x="40"/); assert.match(scene.svg, /Innova/);
  assert.equal(r.world().presets.broadcast.nodes.find(n => n.id === 'maker').x, 40);
});
test('three reusable PutterWarz constraints evaluate pass, pending and fail honestly', () => {
  const r = make(); let checked = r.constraints('putterwarz'); assert.equal(checked.status, 'pending');
  assert.deepEqual(checked.rules.map(x => x.status), ['pass', 'pass', 'pending']);
  r.dispatch({ type: 'bag.membership', bagId: 'luna-bag', discId: 'buzzz-mint', include: true });
  checked = r.constraints('putterwarz'); assert.equal(checked.rules.find(x => x.id === 'single-mold').status, 'fail');
  r.dispatch({ type: 'bag.membership', bagId: 'luna-bag', discId: 'buzzz-mint', include: false });
  for (const team of ['luna', 'zone']) for (let i = 0; i < 3; i++) r.dispatch({ type: 'throw.record', id: `throw-${team}-${i}`, teamId: `team-${team}`, roundId: 'hole-1', discId: team === 'luna' ? 'luna-mint' : 'zone-peach' });
  assert.equal(r.constraints('putterwarz').status, 'pass');
  r.dispatch({ type: 'throw.record', id: 'throw-too-many', teamId: 'team-luna', roundId: 'hole-1', discId: 'luna-mint' });
  assert.equal(r.constraints('putterwarz').status, 'fail');
});
test('constraint group any composition is not the same as all; empty rules do not pretend validation', () => {
  const r = make(); r.dispatch({ type: 'entity.set', entityType: 'Competition', id: 'putterwarz', path: 'combine', value: 'any' });
  assert.equal(r.constraints('putterwarz').status, 'pass');
  for (const id of ['bag-size', 'single-mold', 'round-throws']) r.dispatch({ type: 'competition.rule.set', id: 'putterwarz', ruleId: id, patch: { enabled: false } });
  assert.equal(r.constraints('putterwarz').status, 'unconstrained');
});
test('closing a short round fails exact-count rule; missing references fail visibly', () => {
  const r = make(); r.dispatch({ type: 'entity.set', entityType: 'Round', id: 'hole-1', path: 'complete', value: true });
  assert.equal(r.constraints('putterwarz').status, 'fail');
  const w = clone(r.world()); delete w.objects.Disc['buzzz-mint']; r.replace(w);
  assert.throws(() => r.scene(context), /Missing physical disc/);
});
test('states retain independent scores, highlights and winner tags; lineup removal cleans references', () => {
  const r = make(); r.dispatch({ type: 'battle.state.save', id: 'state-2', name: 'Hole one' });
  r.dispatch({ type: 'battle.score', id: 'entry-1', score: 3 }); r.dispatch({ type: 'battle.highlight', id: 'entry-1' }); r.dispatch({ type: 'battle.winner', id: 'entry-1' });
  r.dispatch({ type: 'battle.state.select', id: 'state-1' }); assert.equal(currentBattle(r.world()).scores['entry-1'], null);
  r.dispatch({ type: 'battle.remove', id: 'entry-1' }); validateWorld(r.world());
  assert.ok(r.world().battle.states.every(s => !s.highlight && s.winners.length === 0));
});
test('all placement/layout combinations stay inside the 1920×1080 export frame', () => {
  const r = make();
  for (const arrangement of ['row', 'stack', 'grid']) for (const anchor of ['top-left', 'top-right', 'bottom-left', 'bottom-right', 'center']) {
    r.dispatch({ type: 'layout.set', patch: { arrangement, anchor, scale: 2 } });
    const { bounds: b } = r.scene(context); assert.ok(b.x >= 0 && b.y >= 0 && b.x + b.width <= 1920 && b.y + b.height <= 1080);
  }
});
test('untrusted SVG/text never becomes executable and malformed data cannot replace a valid world', () => {
  const r = make(); r.dispatch({ type: 'entity.set', entityType: 'Disc', id: 'buzzz-mint', path: 'nickname', value: '<script>alert(1)</script>' });
  const rendered = r.scene(context); assert.ok(!rendered.svg.includes('<script>')); assert.ok(rendered.svg.includes('&lt;script&gt;'));
  assert.throws(() => r.dispatch({ type: 'entity.set', entityType: 'Disc', id: 'buzzz-mint', path: '__proto__.evil', value: 'yes' }));
  const previous = r.world(); assert.throws(() => r.dispatch({ type: 'battle.score', id: 'entry-1', score: NaN })); assert.equal(r.world(), previous);
  assert.throws(() => r.dispatch({ type: 'entity.set', entityType: 'Disc', id: 'buzzz-mint', path: 'photo', value: 'javascript:alert(1)' }));
});
test('no synthetic usage is represented as recorded events or exports', () => {
  const r = make(); r.scene(context); r.constraints('putterwarz'); assert.equal(r.world().events.length, 0); assert.equal(r.world().exports.length, 0); assert.equal(Object.keys(r.world().objects.Throw).length, 0);
});

test('identity fields appear first by domain metadata, not a second customizer whitelist', () => {
  const fields = make().card('buzzz-mint', 'broadcast', context).fields;
  assert.deepEqual(fields.slice(0, 4).map(f => f.path), ['disc.mold.name', 'disc.mold.manufacturer.name', 'disc.photo', 'disc.nickname']);
});
test('malformed layouts and negative constraint quantities fail before changing the world', () => {
  const r = make(), original = r.world();
  assert.throws(() => r.dispatch({ type: 'layout.set', patch: { scale: NaN } }));
  assert.throws(() => r.dispatch({ type: 'competition.rule.set', id: 'putterwarz', ruleId: 'bag-size', patch: { value: -1 } }));
  assert.equal(r.world(), original);
});
test('large authored cards and a twelve-disc row still fit the export frame', () => {
  const r = make();
  for (const d of Object.values(r.world().objects.Disc)) if (!r.world().battle.entries.some(e => e.discId === d.id)) r.dispatch({ type: 'battle.add', discId: d.id, id: `extra-${d.id}` });
  r.dispatch({ type: 'preset.set', id: 'broadcast', patch: { width: 2000, height: 2000 } });
  const scene = r.scene(context), b = scene.bounds;
  assert.equal(scene.cardCount, 12);
  assert.ok(b.x >= 0 && b.y >= 0 && b.x + b.width <= 1920 && b.y + b.height <= 1080);
});

/* ------------------------------------------------------------------ */
/* the run record and its standalone Tick render page                  */
/* ------------------------------------------------------------------ */

const RECORD_OPEN = '<script type="application/json" id="record">';
const viewerSource = name => readFileSync(resolve(import.meta.dirname, '../pyto/viewer', name), 'utf8');
const pageSources = () => ({ html: viewerSource('tick-viewer.html'), adapters: viewerSource('adapters.js'), viewer: viewerSource('tick-viewer.js') });
const embeddedRecordOf = page => { const start = page.indexOf(RECORD_OPEN) + RECORD_OPEN.length; return JSON.parse(page.slice(start, page.indexOf('</script>', start))); };
// The viewer's own DOM shim: plain objects, so the assertions walk its output tree.
const stubDoc = () => ({ createElement(tagName) { return { tagName: String(tagName).toLowerCase(), className: '', textContent: '', attributes: Object.create(null), children: [], appendChild(child) { this.children.push(child); return child; }, setAttribute(name, value) { this.attributes[name] = String(value); }, getAttribute(name) { return name in this.attributes ? this.attributes[name] : null; } }; } });
function* walk(node) { yield node; for (const child of node.children) yield* walk(child); }
const withClass = (root, className) => [...walk(root)].filter(n => String(n.className).split(/\s+/).includes(className));
const seededScene = () => { const r = make(); r.scene({ mode: 'battle', ...context }); return r; };

// Kills: writing the record under px.domain.<name> (a fact address) instead of the
// reserved `run` second segment of pyto/BOARD.md:135-136.
test('a seeded composition exports a validated pyto-run-record@1 kept as a Part outside the facts', () => {
  const r = seededScene(), { address, record } = r.runRecord('on-the-course');
  assert.equal(address, 'px.run.on-the-course');
  assert.equal(validate(record), record);
  assert.equal(record.schema, 'pyto-run-record@1');
  assert.equal(record.source.runtime, 'discstudio');
  const composition = r.pxc.get('px.receipt.on-the-course').composition;
  assert.equal(record.ticks.length, composition.Ticks.length);
  assert.deepEqual(record.ticks.map(t => t.name), composition.Ticks.map(t => t.name));
  assert.deepEqual(record.ticks.map(t => t.invocations.length), composition.Ticks.map(t => t.Calculations.length));
  const parts = r.parts().map(p => p.address);
  assert.ok(parts.includes(address), 'the review panel can read it as a Part');
  assert.deepEqual(parts.filter(a => a.startsWith('px.domain.') && r.pxc.get(a)?.schema), [], 'no run record was written into a domain fact');
  assert.deepEqual(r.pxc.get('px.domain.Disc.buzzz-mint'), r.world().objects.Disc['buzzz-mint']);
});

// Kills: building the record from the PQL run alone (passing null for
// px.receipt.<name>), which silently drops every material digest and reuse flag.
test('the execution receipt reaches the run record: material digests and reuse are carried', () => {
  const r = seededScene(), first = r.runRecord('on-the-course').record;
  const digests = first.ticks.flatMap(t => t.invocations).map(i => i.result_sha256);
  assert.equal(digests.filter(d => typeof d === 'string' && d.includes(':')).length, digests.length);
  assert.match(first.ticks[0].invocations[0].result_sha256, /^domain\.fields:/);
  r.scene({ mode: 'battle', ...context });
  const again = r.runRecord('on-the-course').record.ticks.flatMap(t => t.invocations);
  assert.ok(again.every(i => i.hit), 'a repeated render reads only material that already existed');
  assert.ok(again.some(i => i.value.note === 'reused from the memo ring (runtime.js:17-19)'));
});

// Kills: composePage dropping the inlined adapters.js from the bundle, which
// leaves a page whose viewer cannot validate or render the record it carries.
test('composePage builds the same standalone page as buildPage, one section per Tick', () => {
  const record = seededScene().runRecord('on-the-course').record;
  const page = composePage({ ...pageSources(), record });
  assert.equal(page, buildPage(record), 'the browser and the CLI build the same page from the same builder');
  assert.deepEqual(embeddedRecordOf(page), JSON.parse(JSON.stringify(record)));
  assert.equal(page.match(/^\s*(import|export)\s/gm), null, 'no module statement survives inlining');
  assert.ok(page.includes('function validate') && page.includes('function renderRecord'), 'adapters and viewer are inlined');
  assert.ok(!/<script[^>]+src=/.test(page) && !/https?:\/\/(?!www\.w3\.org)/.test(page.replace(/xmlns="[^"]*"/g, '')), 'nothing is fetched');
  const root = renderRecord(embeddedRecordOf(page), { doc: stubDoc() });
  assert.equal(withClass(root, 'tick').length, record.ticks.length);
  assert.deepEqual(withClass(root, 'tick').map(s => withClass(s, 'tick-name')[0].textContent), record.ticks.map(t => t.name));
});

test('a disc without a photo shows painted art inside the generic card, never the Add image placeholder', () => {
  const r = make(), rendered = r.card('buzzz-mint', 'broadcast', context);
  const svg = typeof rendered.svg === 'string' ? rendered.svg : rendered.markup;
  const art = r.pxc.get(rendered.run.trace.find(step => step.call === 'fn.disc.art').output);
  assert.equal(art.kind, 'painted');
  assert.doesNotMatch(svg, /Add image/);
  assert.match(svg, /viewBox="0 0 512 512"/);
  assert.ok(svg.includes(painterRender(...art.inputs).split('\n')[1].slice(0, 40)), 'the card embeds the painter markup');
});
