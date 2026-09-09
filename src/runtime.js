import { createExecBoard, pxFn, readPql, invokePql } from './core/exec.js';
import { freeze, stable, labelHash, partAddress, get, all, currentBattle, materialFor, discoverFields, applyCommand, validateWorld, id } from './domain.js';
import { prepareDiscArt, composeCard, cardSvg, composeOverlay, materializeOverlay } from './presentation.js';
import { constraintDefinitions, bagLimit, oneMold, teamThrows, combineConstraints } from './constraints.js';
import { shelfSheet } from './formats/shelf-sheet.js';

/** Application adapter over the existing ChainSpot runtime. No second execution engine. */
export function createStudioRuntime(initial) {
  const core = createExecBoard(), addresses = new Set();
  const pxc = { ...core, set(address, value) { const key = typeof address === 'string' ? address : address.address; addresses.add(key); core.set(address, freeze(value)); } };
  const calls = [], counters = { calls: 0, computed: 0, reused: 0 }, nextSlot = {};
  let previousObjects = new Set(), listener = () => {};
  const source = (address, value) => { if (!pxc.has(address) || stable(pxc.get(address)) !== stable(value)) pxc.set(address, value); return address; };
  function register(address, calculate, { memo = true, revision = 1 } = {}) {
    pxc.register(pxFn(address), inputs => {
      const signature = stable({ revision, inputs }), tag = address.slice(3), prefix = `px.memo.${tag}.`;
      let hit = null;
      if (memo) for (let n = 0; n < 24; n++) if (pxc.has(prefix + n) && pxc.get(prefix + n).signature === signature) { hit = pxc.get(prefix + n); break; }
      counters.calls++;
      if (hit) { counters.reused++; calls.push({ call: address, reused: true, material: hit.id, revision }); return hit.value; }
      const value = freeze(calculate(inputs)); counters.computed++;
      const material = `${tag}:${labelHash(signature)}`;
      if (memo) { const slot = (nextSlot[tag] ?? 0) % 24; nextSlot[tag] = slot + 1; pxc.set(prefix + slot, { id: material, signature, revision, value }); }
      calls.push({ call: address, reused: false, material, revision }); return value;
    });
  }
  register('fn.studio.applyCommand', applyCommand, { memo: false });
  register('fn.domain.fields', ({ material }) => discoverFields(material));
  register('fn.disc.art', prepareDiscArt);
  register('fn.card.compose', composeCard);
  register('fn.card.svg', cardSvg);
  register('fn.comparison.layout', ({ layout, ...cards }) => composeOverlay({ cards, layout }));
  register('fn.overlay.svg', materializeOverlay);
  register('fn.constraint.bagLimit', bagLimit);
  register('fn.constraint.oneMold', oneMold);
  register('fn.constraint.teamThrows', teamThrows);
  register('fn.constraint.combine', ({ combine, ...results }) => combineConstraints({ results, combine }));
  register('fn.disc.format.shelfSheet', shelfSheet);
  function publishWorld(world) {
    validateWorld(world); pxc.set('px.studio.world', world);
    const present = new Set();
    for (const [type, records] of Object.entries(world.objects)) for (const [key, record] of Object.entries(records)) { const a = partAddress(type, key); present.add(a); source(a, record); }
    for (const a of previousObjects) if (!present.has(a)) pxc.set(a, null); // Tombstones cannot masquerade as live objects.
    previousObjects = present;
    source('px.domain.schemas', world.schemas);
    for (const preset of Object.values(world.presets)) source(`px.presentation.${preset.id}`, preset);
    source('px.comparison.layout', world.layout); source('px.comparison.states', world.battle);
  }
  publishWorld(freeze(validateWorld(initial)));
  const world = () => pxc.get('px.studio.world');
  const step = (name, call, bindings, into, args = {}) => ({ name, Calculations: [{ call, with: bindings, args, into }] });
  function execute(name, ticks) {
    const mark = calls.length;
    const composition = readPql(JSON.stringify({ PrincipleComponentRender: name, Ticks: ticks }), JSON.parse);
    const run = invokePql(composition, { pxc });
    const invoked = calls.slice(mark); if (calls.length > 1000) calls.splice(0, calls.length - 1000);
    const trace = run.Ticks.flatMap(t => t.Calculations.map(c => ({ tick: t.name, call: c.actualCall, inputs: c.with, output: c.into }))).map((r, i) => ({ ...r, ...invoked[i] }));
    const receipt = freeze({ composition, trace, computed: trace.filter(r => !r.reused).length, reused: trace.filter(r => r.reused).length });
    pxc.set(`px.receipt.${name}`, receipt);
    return receipt;
  }
  function dispatch(command) {
    source('px.input.command', { ...command, eventId: id('event'), time: new Date().toISOString() });
    const run = execute('studio-command', [step('ApplyCommand', 'fn.studio.applyCommand', { world: 'px.studio.world', command: 'px.input.command' }, 'px.studio.nextWorld')]);
    publishWorld(pxc.get('px.studio.nextWorld')); listener(world(), command, run); return run;
  }
  function cardSteps(discId, presetId, context, entry, suffix) {
    const w = world(), disc = get(w, 'Disc', discId), preset = w.presets[presetId];
    if (!disc) throw new Error(`Missing physical disc '${discId}'. Nothing was silently dropped.`);
    if (!preset) throw new Error(`Missing presentation '${presetId}'.`);
    const mold = get(w, 'Mold', disc.moldId), maker = mold && get(w, 'Manufacturer', mold.manufacturerId);
    if (!mold || !maker) throw new Error(`The product identity for '${disc.nickname || disc.id}' is unresolved.`);
    const roots = { entry: { type: 'BattleEntry', record: entry }, disc: { type: 'Disc', id: discId }, bag: { type: 'Bag', id: context.bagId }, competition: { type: 'Competition', id: context.competitionId }, round: { type: 'Round', id: context.roundId } };
    if (context.extraType && w.schemas[context.extraType]) roots[context.extraType.toLowerCase()] = { type: context.extraType, id: context.extraId };
    const prefix = `px.render.${suffix}`, mat = source(`${prefix}.inputs`, materialFor(w, roots));
    const ea = source(`${prefix}.entry`, entry);
    return {
      prefix,
      ticks: [
        step(`Fields:${discId}`, 'fn.domain.fields', { material: mat }, `${prefix}.fields`),
        step(`Art:${discId}`, 'fn.disc.art', { disc: partAddress('Disc', discId), mold: partAddress('Mold', mold.id), maker: partAddress('Manufacturer', maker.id) }, `${prefix}.art`),
        step(`Card:${discId}`, 'fn.card.compose', { fields: `${prefix}.fields`, art: `${prefix}.art`, preset: `px.presentation.${presetId}`, entry: ea }, `${prefix}.card`),
        step(`CardSvg:${discId}`, 'fn.card.svg', { card: `${prefix}.card` }, `${prefix}.svg`)
      ]
    };
  }
  function card(discId, presetId, context = {}, entry = null) {
    const { prefix, ticks } = cardSteps(discId, presetId, context, entry, `single.${discId}`);
    const run = execute('display-card', ticks);
    return { ...pxc.get(`${prefix}.svg`), card: pxc.get(`${prefix}.card`), fields: pxc.get(`${prefix}.fields`), part: `${prefix}.svg`, run };
  }
  function scene({ mode = 'battle', discId, bagId, competitionId, roundId, stateId, presetId } = {}) {
    const w = world(), state = stateId ? w.battle.states.find(s => s.id === stateId) : currentBattle(w);
    if (!state) throw new Error('Comparison state is missing.');
    const entries = mode === 'card' ? [{ discId, id: 'single' }] : w.battle.entries;
    const ticks = [], inputs = { layout: 'px.comparison.layout' };
    entries.forEach((entry, i) => {
      const info = mode === 'card' ? null : { ...entry, score: state.scores[entry.id] ?? null, highlighted: state.highlight === entry.id, winner: state.winners.includes(entry.id) };
      const built = cardSteps(entry.discId, presetId || w.layout.presetId, { bagId, competitionId, roundId }, info, `course.${entry.id}`);
      ticks.push(...built.ticks); inputs[`card${i}`] = `${built.prefix}.card`;
    });
    ticks.push(step('ArrangeComparison', 'fn.comparison.layout', inputs, 'px.course.scene'));
    ticks.push(step('MaterializeOverlay', 'fn.overlay.svg', { scene: 'px.course.scene' }, 'px.course.svg'));
    const run = execute('on-the-course', ticks);
    return { ...pxc.get('px.course.svg'), part: 'px.course.svg', run, stateId: state.id, scene: pxc.get('px.course.scene') };
  }
  function constraints(competitionId) {
    const w = world(), comp = get(w, 'Competition', competitionId);
    if (!comp) throw new Error('Competition is missing.');
    const teams = comp.teamIds.map(key => { const team = get(w, 'Team', key); if (!team) throw new Error(`Missing team '${key}'.`); return team; });
    const rounds = comp.roundIds.map(key => { const round = get(w, 'Round', key); if (!round) throw new Error(`Missing round '${key}'.`); return round; });
    const material = { teams, rounds, bags: w.objects.Bag, discs: w.objects.Disc, molds: w.objects.Mold, throws: all(w, 'Throw').filter(t => comp.teamIds.includes(t.teamId) && comp.roundIds.includes(t.roundId)) };
    const ma = source('px.competition.material', material), ticks = [], inputs = {};
    for (const rule of comp.constraints.filter(r => r.enabled)) {
      const definition = constraintDefinitions[rule.kind]; if (!definition) throw new Error(`Unknown reusable constraint '${rule.kind}'.`);
      if (!Number.isInteger(rule.value) || rule.value < 1 || rule.value > 100) throw new Error('Constraint quantities must be integers from 1 to 100.');
      const ra = source(`px.constraint.${rule.id}.definition`, rule), into = `px.constraint.${rule.id}.result`;
      ticks.push(step(rule.id, definition.call, { material: ma, rule: ra }, into)); inputs[rule.id] = into;
    }
    ticks.push(step('ComposeConstraints', 'fn.constraint.combine', inputs, 'px.competition.validation', { combine: comp.combine }));
    const run = execute('competition', ticks);
    return { ...pxc.get('px.competition.validation'), run, part: 'px.competition.validation' };
  }
  return {
    pxc, world, dispatch, card, scene, constraints, counters,
    onChange(fn) { listener = fn; },
    replace(next) { publishWorld(freeze(validateWorld(next))); listener(world(), { type: 'draft.import' }, null); },
    parts() { return [...addresses].sort().map(address => ({ address, value: pxc.get(address) })); },
    /** Read/select Parts without building another state store. */
    select(prefix) { return [...addresses].filter(a => a.startsWith(prefix)).map(a => ({ address: a, value: pxc.get(a) })); }
  };
}
