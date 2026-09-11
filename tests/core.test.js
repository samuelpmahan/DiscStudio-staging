import test from 'node:test';
import assert from 'node:assert/strict';
import { createSeed } from '../src/seed.js';
import { createStudioRuntime } from '../src/runtime.js';
import { classifyTick, createExecBoard, invokePql, invokePqlAsync, pxFn, queryPrefix, readPql } from '../src/core/exec.js';
import { discoverFields, materialFor, currentBattle, clone, validateWorld } from '../src/domain.js';
import { fieldNode, sampleColors } from '../src/presentation.js';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { fromDiscStudioReceipt, validate } from '../pyto/viewer/adapters.js';
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
  assert.deepEqual(art.inputs.slice(2, 4), sampleColors(150), 'an invalid authored colour falls back to the disc\'s own sample colours (buzzz-mint, hue 150)');
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

/* ------------------------------------------------------------------ */
/* several `into` per Calculation, the px.receipt.* prefix query,      */
/* the Inspect receipts list and the UndoStack                         */
/* ------------------------------------------------------------------ */

const board = () => { const pxc = createExecBoard(); pxc.set('px.rows', [1, 2, 3, 4]); return pxc; };
const because = (pattern) => (error) => { let text = ''; for (let e = error; e; e = e.cause) text += `${e.message} | `; assert.match(text, pattern); return true; };
const document = (into, calculate, call = 'fn.multi.stats') => {
  const pxc = board(); pxc.register(pxFn(call), calculate);
  const composition = readPql(JSON.stringify({ PrincipleComponentRender: 'multi', Ticks: [{ name: 'Prepare', Calculations: [{ call, with: { rows: 'px.rows' }, into }] }] }), JSON.parse);
  return { pxc, composition };
};

// Kills: keeping `text(calculation.into, ...)` in readPql (an array `into` is
// refused outright), and `pxc.set(calculation.into, output)` in invokePql (one
// Part addressed by the array, and the second produce silently dropped).
test('a Calculation may declare several into: one pass, several Parts, one receipt listing all of them', () => {
  const produces = ['px.multi.mean', 'px.multi.count'];
  const { pxc, composition } = document(produces, ({ rows }) => ({ 'px.multi.mean': rows.reduce((a, b) => a + b, 0) / rows.length, 'px.multi.count': rows.length }));
  assert.deepEqual(composition.Ticks[0].Calculations[0].into, produces);
  const run = invokePql(composition, { pxc });
  assert.equal(pxc.get('px.multi.mean'), 2.5);
  assert.equal(pxc.get('px.multi.count'), 4);
  assert.deepEqual(run.Ticks[0].Calculations[0].produces, produces);
  // The array is positional too: the same declaration accepts an array of values.
  const array = document(produces, ({ rows }) => [rows.length, rows.length * 2]);
  invokePql(array.composition, { pxc: array.pxc });
  assert.equal(array.pxc.get('px.multi.mean'), 4);
  assert.equal(array.pxc.get('px.multi.count'), 8);
});

// Kills: publishing what the output happens to have (a missing produce written as
// undefined), and publishing the first address before the shape is checked.
test('a multi-produce output that does not carry every declared address publishes nothing', () => {
  const produces = ['px.multi.mean', 'px.multi.count'];
  const { pxc, composition } = document(produces, ({ rows }) => ({ 'px.multi.mean': rows.length }));
  assert.throws(() => invokePql(composition, { pxc }), because(/has no key 'px.multi.count'/));
  assert.equal(pxc.has('px.multi.mean'), false);
  assert.equal(pxc.has('px.multi.count'), false);
  const short = document(produces, () => [1]);
  assert.throws(() => invokePql(short.composition, { pxc: short.pxc }), because(/declares 2 addresses and the Calculation returned 1 values/));
  const scalar = document(produces, () => 7);
  assert.throws(() => invokePql(scalar.composition, { pxc: scalar.pxc }), because(/must return an object keyed by them or an array of 2 values; got number/));
});

test('the grammar refuses an empty into, a repeated produce address and a misplaced prefix star', () => {
  const read = (calculation) => readPql(JSON.stringify({ PrincipleComponentRender: 'p', Ticks: [{ name: 'T', Calculations: [{ call: 'fn.x', with: {}, ...calculation }] }] }), JSON.parse);
  assert.throws(() => read({ into: [] }), /expected at least one address/);
  assert.throws(() => read({ into: ['px.a', 'px.a'] }), /'px.a' is declared twice/);
  assert.throws(() => read({ into: ['px.a', 3] }), /expected a nonempty string/);
  assert.throws(() => read({ into: 'px.a', with: { r: 'px.*.tail' } }), /only the last segment of a prefix query/);
  assert.equal(read({ into: 'px.a', with: { r: 'px.receipt.*' } }).Ticks[0].Calculations[0].with.r, 'px.receipt.*');
});

// Kills: resolving 'px.receipt.*' with pxc.get (the address does not exist), and
// answering the query in address order instead of sorted order.
test('a with binding ending in .* is a prefix query over the board, sorted and read as one value', () => {
  const pxc = createExecBoard();
  for (const address of ['px.receipt.z', 'px.receipt.a', 'px.other.b']) pxc.set(address, { at: address });
  assert.deepEqual(Object.keys(queryPrefix(pxc, 'px.receipt.*')), ['px.receipt.a', 'px.receipt.z']);
  pxc.register(pxFn('fn.count'), ({ seen }) => Object.keys(seen));
  const composition = readPql(JSON.stringify({ PrincipleComponentRender: 'q', Ticks: [{ name: 'Q', Calculations: [{ call: 'fn.count', with: { seen: 'px.receipt.*' }, into: 'px.seen' }] }] }), JSON.parse);
  invokePql(composition, { pxc });
  assert.deepEqual(pxc.get('px.seen'), ['px.receipt.a', 'px.receipt.z']);
  assert.deepEqual(queryPrefix(pxc, 'px.nothing.*'), {});
});

// Kills: building the Receipts list from runtime.parts() or another index instead
// of a PQL Calculation, and writing one Part where the Calculation declares two.
test('the Inspect receipts list is a PQL query over px.receipt.* publishing two Parts', () => {
  const r = seededScene();
  const first = r.receipts();
  // task 131: the shelf's art assignment is a run of its own (art-assignment, one invocation, one Part), listed beside the scene
  assert.deepEqual(first.rows.map(row => row.name), ['art-assignment', 'on-the-course']);
  assert.deepEqual(first.summary, { receipts: 2, invocations: 21, produces: 21, digest: first.summary.digest });
  assert.match(first.summary.digest, /^[0-9a-f]{8}$/);
  assert.deepEqual(r.pxc.get('px.studio.receipts'), first.rows);
  assert.deepEqual(r.pxc.get('px.studio.receipts.summary'), first.summary);
  const scene = first.rows.find(row => row.name === 'on-the-course');
  assert.equal(scene.address, 'px.receipt.on-the-course');
  assert.equal(scene.invocations, 20); // task 78: each of the 3 lineup entries now gains a Cascade Tick of 2 Calculations (14 + 3*2)
  assert.ok(scene.consumes.includes('px.domain.Disc.buzzz-mint') && scene.consumes.includes('px.course.scene'));
  assert.ok(scene.produces.includes('px.course.svg') && scene.produces.includes('px.render.course.entry-1.card'));
  assert.deepEqual(scene.consumes, [...scene.consumes].sort());
  // The query is over the record, so the second reading sees the first one's own receipt.
  const second = r.receipts(), listed = second.rows.find(row => row.name === 'studio-receipts');
  assert.deepEqual(second.rows.map(row => row.name), ['art-assignment', 'on-the-course', 'studio-receipts']);
  assert.deepEqual(listed.consumes, ['px.receipt.*']);
  assert.deepEqual(listed.produces, ['px.studio.receipts', 'px.studio.receipts.summary']);
  assert.equal(listed.invocations, 1);
  assert.equal(seededScene().receipts().rows.find(row => row.name === 'on-the-course').digest, scene.digest, 'the same workspace and composition label the same materials');
});

// Kills: an undo that keeps its own history outside the store, and a pop that
// hands back a rebuilt value instead of the one push recorded.
test('push then pop restores the exact previous value and the stack depth follows', () => {
  const r = make(), before = r.world();
  assert.equal(r.undo.depth(), 0);
  r.dispatch({ type: 'entity.set', entityType: 'Disc', id: 'buzzz-mint', path: 'nickname', value: 'Edited once' });
  assert.equal(r.world().objects.Disc['buzzz-mint'].nickname, 'Edited once');
  assert.equal(r.undo.depth(), 1);
  assert.deepEqual(r.undo.stack().entries.map(entry => [entry.address, entry.depth]), [['px.studio.world', 1]]);
  r.undo.pop('px.studio.world');
  assert.deepEqual(r.world(), before);
  assert.equal(r.pxc.get('px.domain.Disc.buzzz-mint').nickname, before.objects.Disc['buzzz-mint'].nickname);
  assert.equal(r.undo.depth(), 0);
  assert.equal(r.card('buzzz-mint', 'broadcast', context).svg, make().card('buzzz-mint', 'broadcast', context).svg);
});

// Kills: a pop that throws, silently returns, or drops an entry when the stack is
// empty -- the attempt is an ordinary invocation and leaves a receipt either way.
test('pop on an empty stack changes nothing and is still on the record', () => {
  const r = make(), world = r.world();
  const run = r.undo.pop('px.studio.world');
  assert.equal(r.world(), world);
  assert.equal(r.undo.depth(), 0);
  assert.deepEqual(run.trace.map(step => step.call), ['fn.undo.pop', 'fn.undo.settle']);
  assert.deepEqual(run.trace.map(step => step.output), ['px.studio.world', 'px.undo.studio']);
  assert.equal(r.pxc.get('px.receipt.studio-undo'), run);
  assert.deepEqual(r.pxc.get('px.undo.studio'), { scope: 'studio', depth: 0, entries: [] });
});

// Kills: undo written as a runtime side effect instead of Calculations -- a run
// record built from px.pql.studio-undo would then have nothing to carry.
test('the run record lists the undo invocations, push and pop alike', () => {
  const r = make();
  r.dispatch({ type: 'entity.set', entityType: 'Disc', id: 'buzzz-mint', path: 'nickname', value: 'Edited once' });
  const pushed = r.runRecord('studio-undo-push').record;
  assert.deepEqual(pushed.ticks.map(tick => tick.name), ['Push']);
  assert.deepEqual(pushed.ticks[0].invocations.map(i => i.calculation.address), ['fn.undo.push']);
  assert.deepEqual(pushed.ticks[0].invocations[0].actual_consumes, ['px.undo.studio', 'px.studio.world']);
  assert.deepEqual(pushed.ticks[0].invocations[0].into, 'px.undo.studio');
  r.undo.pop('px.studio.world');
  const undone = r.runRecord('studio-undo').record;
  assert.equal(validate(undone), undone);
  assert.deepEqual(undone.ticks.map(tick => tick.name), ['Restore', 'Settle']);
  assert.deepEqual(undone.ticks.flatMap(tick => tick.invocations).map(i => i.calculation.address), ['fn.undo.pop', 'fn.undo.settle']);
  assert.deepEqual(undone.ticks.flatMap(tick => tick.invocations).map(i => i.into), ['px.studio.world', 'px.undo.studio']);
  assert.equal(undone.counters.invocations, 2);
  assert.equal(r.receipts().rows.map(row => row.name).filter(name => name.startsWith('studio-undo')).length, 2);
});

/* ------------------------------------------------------------------ */
/* the schedule: parallel Ticks, placement, latency and a budget       */
/* (src/core/exec.js, pyto/viewer/RECORD.md "Placement and budget")    */
/* ------------------------------------------------------------------ */

// Kills: dropping classifyTick from invokePqlAsync (exec.js `mode`) makes the
// backwards read and the duplicate `into` run instead of being refused, and
// runs a chain at once, so its later Calculation reads a missing address;
// moving a parallel Tick's publish loop inside the Promise.all wrapper lets the
// board hold half a Tick; publishing a chain only after the Tick starves its
// later Calculation of the earlier sibling's value; checking the budget inside
// a Tick instead of at the boundary (`overBudget`) stops mid-Tick and the board
// keeps a Part of the Tick the record says never ran.

const SLEEP_MS = 40;
const parse = document => readPql(JSON.stringify(document), JSON.parse);
const testimony = run => JSON.stringify({ PrincipleComponentRender: run.PrincipleComponentRender, Ticks: run.Ticks });
function timerBoard() {
  const board = createExecBoard();
  board.register(pxFn('fn.seed'), ({ n }) => n);
  board.register(pxFn('fn.slow'), async ({ base, n }) => { await new Promise(resolve => setTimeout(resolve, SLEEP_MS)); return base * 10 + n; });
  board.register(pxFn('fn.join'), inputs => Object.keys(inputs).sort().map(key => inputs[key]).join('+'));
  return board;
}
const fanDocument = {
  PrincipleComponentRender: 'schedule-demo',
  Ticks: [
    { name: 'Seed', Calculations: [{ call: 'fn.seed', args: { n: 3 }, into: 'px.seed' }] },
    { name: 'Fan', Calculations: [0, 1, 2, 3].map(n => ({ call: 'fn.slow', with: { base: 'px.seed' }, args: { n }, into: `px.leg.${n}` })) },
    { name: 'Join', Calculations: [{ call: 'fn.join', with: { a: 'px.leg.0', b: 'px.leg.1', c: 'px.leg.2', d: 'px.leg.3' }, into: 'px.total' }] }
  ]
};

test('a Tick of four timer-awaiting Calculations runs at once: latency under the work, testimony byte-identical to the serial run', async () => {
  const serialBoard = timerBoard(), parallelBoard = timerBoard();
  const serialStarted = Date.now();
  const serial = await invokePqlAsync(parse(fanDocument), serialBoard, { parallel: false });
  const serialElapsed = Date.now() - serialStarted;
  const parallel = await invokePqlAsync(parse(fanDocument), parallelBoard, { parallel: true });

  assert.equal(testimony(serial), testimony(parallel), 'the schedule is not the program: the testimony is the same bytes either way');
  assert.equal(serialBoard.get('px.total'), parallelBoard.get('px.total'));
  assert.equal(serial.schedule, undefined, 'a serial, unbudgeted run reports no schedule at all');

  const fan = parallel.schedule.ticks[1], work = SLEEP_MS * fanDocument.Ticks[1].Calculations.length;
  assert.equal(parallel.schedule.parallel, true);
  assert.deepEqual(parallel.schedule.budget, { limit_ms: null, stopped_after_tick: null, completed: true });
  assert.deepEqual(fan.placements.map(p => p.worker), [0, 1, 2, 3], 'one worker index per branch, in the order the branches start');
  assert.ok(fan.placements.every(p => p.started_ms >= 0 && p.started_ms < SLEEP_MS), fan.placements);
  assert.ok(fan.latency_ms < work * 0.75, `latency ${fan.latency_ms}ms is not under the ${work}ms of work`);
  assert.ok(serialElapsed >= work * 0.75, `the serial run took ${serialElapsed}ms, which is not the work`);
  assert.deepEqual(parallel.schedule.ticks[0].placements.map(p => p.worker), [0], 'the one branch of a one-Calculation Tick is worker 0');
  assert.deepEqual(parallel.schedule.ticks.map(tick => tick.mode), ['parallel', 'parallel', 'parallel'], 'no Tick of this document reads a sibling, so every Tick ran at once');
  assert.deepEqual(serialBoard.get('px.leg.2'), parallelBoard.get('px.leg.2'));
  console.log(`# parallel Fan Tick: work ${work}ms (4 x ${SLEEP_MS}ms), latency ${fan.latency_ms}ms; the same run serially: ${serialElapsed}ms`);
});

// Inside a Tick the Calculations are a sequence in declared order, and a later
// one may read what an earlier sibling produced (the owner, 2026-09-10: the
// ChainSpot program deliberately chains dependent Calculations inside a Tick;
// the Tick boundary is where the sequence becomes inspectable).
const chainDocument = {
  PrincipleComponentRender: 'chain-demo',
  Ticks: [
    { name: 'Seed', Calculations: [{ call: 'fn.seed', args: { n: 1 }, into: 'px.a' }] },
    { name: 'Chain', Calculations: [
      { call: 'fn.seed', args: { n: 2 }, into: 'px.b' },
      { call: 'fn.slow', with: { base: 'px.b' }, args: { n: 3 }, into: 'px.c' },
      { call: 'fn.join', with: { a: 'px.a', b: 'px.b', c: 'px.c' }, into: 'px.d' }
    ] }
  ]
};

test('a Tick whose Calculation reads an earlier sibling is a chain: under parallel: true it runs in declared order and each later Calculation sees the earlier value', async () => {
  const board = timerBoard();
  const run = await invokePqlAsync(parse(chainDocument), board, { parallel: true });
  assert.equal(board.get('px.c'), 23, 'the second Calculation read px.b, which its earlier sibling produced in the same Tick');
  assert.equal(board.get('px.d'), '1+2+23', 'the third read both earlier siblings and the earlier Tick');
  assert.deepEqual(run.Ticks[1].Calculations.map(calculation => calculation.inputs), [{}, { base: 2 }, { a: 1, b: 2, c: 23 }], 'the testimony records the values each Calculation actually read');
  // A prefix query reads every address under it, so it reads an earlier sibling's produce too: a chain as well.
  const query = { PrincipleComponentRender: 'chain-query', Ticks: [{ name: 'Chain', Calculations: [
    { call: 'fn.seed', args: { n: 1 }, into: 'px.leaf.one' },
    { call: 'fn.join', with: { all: 'px.leaf.*' }, into: 'px.q' }
  ] }] };
  const queried = await invokePqlAsync(parse(query), timerBoard(), { parallel: true });
  assert.deepEqual(queried.Ticks[0].Calculations[1].inputs, { all: { 'px.leaf.one': 1 } });
  assert.equal(classifyTick(parse(query).Ticks[0]), 'chain');
});

test('a chain under parallel: true and the same document serially write byte-identical testimony', async () => {
  const serialBoard = timerBoard(), parallelBoard = timerBoard();
  const serial = await invokePqlAsync(parse(chainDocument), serialBoard, { parallel: false });
  const parallel = await invokePqlAsync(parse(chainDocument), parallelBoard, { parallel: true });
  assert.equal(testimony(serial), testimony(parallel), 'the schedule is not the program: a chain testifies exactly as the serial run does');
  assert.deepEqual(serialBoard.keys().sort(), parallelBoard.keys().sort());
  for (const address of serialBoard.keys().filter(address => !address.startsWith('px.pql.'))) assert.deepEqual(serialBoard.get(address), parallelBoard.get(address), address);
  assert.equal(serial.schedule, undefined, 'a serial, unbudgeted run still reports no schedule at all');
});

test('the schedule marks a Tick with sibling reads mode chain, on one worker in sequence, and a Tick without them mode parallel', async () => {
  const run = await invokePqlAsync(parse(chainDocument), timerBoard(), { parallel: true });
  assert.deepEqual(run.schedule.ticks.map(tick => [tick.name, tick.mode]), [['Seed', 'parallel'], ['Chain', 'chain']]);
  assert.deepEqual(classifyTick(parse(chainDocument).Ticks[0]), 'parallel');
  assert.deepEqual(classifyTick(parse(chainDocument).Ticks[1]), 'chain');
  const chain = run.schedule.ticks[1];
  assert.deepEqual(chain.placements.map(placement => placement.worker), [0, 0, 0], 'a chain runs on worker 0 throughout');
  const starts = chain.placements.map(placement => placement.started_ms);
  assert.ok(starts.every((start, index) => index === 0 || start >= starts[index - 1]), `started offsets are in sequence: ${starts}`);
  assert.ok(starts[2] - starts[1] >= SLEEP_MS * 0.75, `the third Calculation started after the slow second one finished: ${starts}`);
  assert.ok(chain.latency_ms >= SLEEP_MS * 0.75, `the chain's latency is its work: ${chain.latency_ms}ms`);
  assert.equal(run.schedule.parallel, true);
  assert.deepEqual(run.schedule.budget, { limit_ms: null, stopped_after_tick: null, completed: true });
  // A serial, budgeted run reports a schedule but no mode: absent means serial, as for placement.
  const budgeted = await invokePqlAsync(parse(chainDocument), timerBoard(), { parallel: false, budgetMs: 10_000 });
  assert.deepEqual(budgeted.schedule.ticks.map(tick => 'mode' in tick), [false, false]);
});

test('a Calculation that reads a LATER sibling produce is a backwards read, refused by name before the Tick runs', async () => {
  const board = timerBoard();
  const document = { PrincipleComponentRender: 'backwards-read', Ticks: [{ name: 'Fan', Calculations: [
    { call: 'fn.join', with: { a: 'px.a' }, into: 'px.b' },
    { call: 'fn.seed', args: { n: 1 }, into: 'px.a' }
  ] }] };
  await assert.rejects(() => invokePqlAsync(parse(document), board, { parallel: true }), error => {
    assert.match(error.message, /parallel refused/);
    assert.match(error.message, /Calculations\[0\] 'fn\.join' -> px\.b reads 'px\.a', which its sibling Calculations\[1\] 'fn\.seed' -> px\.a produces later in the same Tick/);
    return true;
  });
  assert.equal(board.has('px.a'), false, 'a refused Tick publishes nothing at all');
  assert.equal(board.has('px.b'), false);
  // A prefix query over a later sibling's address is the same backwards read.
  const query = { PrincipleComponentRender: 'backwards-query', Ticks: [{ name: 'Fan', Calculations: [
    { call: 'fn.join', with: { all: 'px.leaf.*' }, into: 'px.b' },
    { call: 'fn.seed', args: { n: 1 }, into: 'px.leaf.one' }
  ] }] };
  await assert.rejects(() => invokePqlAsync(parse(query), board, { parallel: true }), /reads 'px\.leaf\.one', which its sibling .* produces later in the same Tick/);
  assert.throws(() => classifyTick(parse(document).Ticks[0]), /produces later in the same Tick/);
});

test('two Calculations of one Tick declaring one into are refused by name', async () => {
  const board = timerBoard();
  const document = { PrincipleComponentRender: 'one-address-two-producers', Ticks: [{ name: 'Fan', Calculations: [
    { call: 'fn.seed', args: { n: 1 }, into: ['px.a', 'px.shared'] },
    { call: 'fn.seed', args: { n: 2 }, into: 'px.shared' }
  ] }] };
  await assert.rejects(() => invokePqlAsync(parse(document), board, { parallel: true }), error => {
    assert.match(error.message, /Calculations\[0\] 'fn\.seed' -> px\.a, px\.shared and Calculations\[1\] 'fn\.seed' -> px\.shared both declare into 'px\.shared'/);
    return true;
  });
  assert.equal(board.has('px.a'), false, 'a refused Tick publishes nothing at all');
});

test('a budget stops the run at a Tick boundary: the board holds whole Ticks and the record says which was the last', () => {
  const board = createExecBoard();
  let now = 0;
  const clock = () => now;
  board.register(pxFn('fn.step'), ({ ms }) => { now += ms; return now; });
  const document = { PrincipleComponentRender: 'budgeted', Ticks: ['Tick1', 'Tick2', 'Tick3', 'Tick4'].map((name, index) => ({
    name, Calculations: [{ call: 'fn.step', args: { ms: 10 }, into: `px.part.${index + 1}` }]
  })) };
  const run = invokePql(parse(document), board, { budgetMs: 15, clock });

  assert.deepEqual(run.Ticks.map(tick => tick.name), ['Tick1', 'Tick2'], 'the Tick that started finished; the next one never began');
  assert.deepEqual([1, 2, 3, 4].map(n => board.has(`px.part.${n}`)), [true, true, false, false]);
  assert.deepEqual(run.schedule.budget, { limit_ms: 15, stopped_after_tick: 'Tick2', completed: false });
  assert.equal(run.schedule.parallel, false);
  assert.deepEqual(run.schedule.ticks.map(tick => tick.latency_ms), [10, 10]);

  const trace = run.Ticks.flatMap(tick => tick.Calculations.map(calculation => ({
    tick: tick.name, call: calculation.actualCall, inputs: calculation.with, output: calculation.into,
    produces: calculation.produces, reused: false, material: null, revision: 1
  })));
  const record = fromDiscStudioReceipt(run, { composition: document, trace, computed: trace.length, reused: 0, schedule: run.schedule });
  assert.deepEqual(record.budget, { limit_ms: 15, stopped_after_tick: 'Tick2', completed: false });
  assert.equal(record.parallel, false);
  assert.deepEqual(record.ticks.map(tick => tick.name), ['Tick1', 'Tick2']);
  assert.deepEqual(record.ticks.map(tick => tick.latency_ms), [10, 10]);
  assert.deepEqual(record.ticks.flatMap(tick => tick.invocations.map(invocation => invocation.placement)), [null, null]);
  assert.ok(validate(record));
  assert.throws(() => validate({ ...record, budget: { ...record.budget, stopped_after_tick: 'Tick9' } }), /names no Tick in this record/);
});

test('a serial, unbudgeted run writes the record it always wrote, byte for byte', () => {
  const r = make();
  r.scene({ ...context });
  const { record } = r.runRecord('on-the-course');
  const fixture = JSON.parse(readFileSync(resolve('tests/fixtures/serial-run-record.json'), 'utf8'));
  assert.equal(JSON.stringify(record, null, 2), JSON.stringify(fixture, null, 2), 'the schedule fields are absent from a serial, unbudgeted record and nothing else moved');
  const text = JSON.stringify(record);
  for (const field of ['parallel', 'budget', 'latency_ms', 'placement']) assert.equal(text.includes(`"${field}"`), false, field);
});

test('fromDiscStudioReceipt takes an array into: the list is the into, and every declared address is a produce', () => {
  const r = make();
  r.receipts();
  const { record } = r.runRecord('studio-receipts');
  const invocation = record.ticks[0].invocations[0];
  assert.deepEqual(invocation.into, ['px.studio.receipts', 'px.studio.receipts.summary']);
  assert.deepEqual(invocation.actual_produces, invocation.into);
  assert.deepEqual(invocation.writes, invocation.into.map(address => ({ address, kind: 'new-address' })));
  assert.equal(invocation.id, 'px.studio.receipts', 'the invocation id is the first address it declares');
  for (const address of invocation.into) assert.equal(record.parts[address].written_by, invocation.id);
  assert.equal(record.counters.invocations, 1);
  assert.ok(validate(record));
});

test('one disc.create makes the maker, the mold, the disc and its bag place, and one undo takes all of it back', () => {
  const r = make(), before = r.world();
  r.dispatch({ type: 'disc.create', id: 'disc-new', manufacturer: 'Kastaplast', mold: 'Berg', category: 'Putter', plastic: 'K1', weight: 174, color: 'Mint', nickname: '', photo: null, bagId: 'everyday' });
  const w = r.world(), made = w.objects.Disc['disc-new'], mold = w.objects.Mold[made.moldId], maker = w.objects.Manufacturer[mold.manufacturerId];
  assert.equal(maker.name, 'Kastaplast');
  assert.equal(mold.name, 'Berg');
  assert.equal(mold.category, 'Putter');
  assert.equal(made.nickname, 'K1 Berg 174 g', 'a blank nickname is written from the facts, never left as a placeholder');
  assert.equal(made.sampleHue, w.objects.Disc['buzzz-mint'].sampleHue, 'a disc the person called Mint paints in the same hue the seeded Mint disc does');
  assert.ok(w.objects.Bag.everyday.discIds.includes('disc-new'));
  r.undo.pop('px.studio.world');
  const after = r.world();
  assert.equal(after.objects.Disc['disc-new'], undefined);
  assert.equal(Object.keys(after.objects.Manufacturer).length, Object.keys(before.objects.Manufacturer).length, 'no stray maker is left behind');
  assert.deepEqual(after.objects.Bag.everyday.discIds, before.objects.Bag.everyday.discIds);
});

test('disc.create reuses the maker and mold that are already on the shelf, and a disc with an unknown colour still gets its own hue', () => {
  const r = make();
  r.dispatch({ type: 'disc.create', id: 'disc-two', manufacturer: 'discraft', mold: 'buzzz', category: 'Midrange', plastic: 'Big Z', weight: null, color: 'Swirly something', nickname: 'The gamer', photo: null, bagId: null });
  const w = r.world(), made = w.objects.Disc['disc-two'];
  assert.equal(made.moldId, 'buzzz', 'the mold is matched case-insensitively rather than duplicated');
  assert.equal(Object.keys(w.objects.Mold).length, 7);
  assert.equal(made.nickname, 'The gamer');
  assert.ok(Number.isFinite(made.sampleHue) && made.sampleHue !== w.objects.Disc['buzzz-mint'].sampleHue);
  const card = r.card('disc-two', 'broadcast', context);
  assert.match(card.svg, /Buzzz/);
});
