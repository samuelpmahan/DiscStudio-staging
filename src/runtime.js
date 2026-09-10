import { createExecBoard, pxFn, readPql, invokePql, invokePqlAsync } from './core/exec.js';
import { freeze, stable, labelHash, partAddress, get, all, currentBattle, materialFor, discoverFields, applyCommand, validateWorld, id } from './domain.js';
import { prepareDiscArt, composeCard, cardSvg, composeOverlay, materializeOverlay } from './presentation.js';
import { constraintDefinitions, bagLimit, oneMold, teamThrows, combineConstraints } from './constraints.js';
import { fromDiscStudioReceipt, validate } from '../pyto/viewer/adapters.js';
import { shelfSheet } from './formats/shelf-sheet.js';
import { receiptList } from './formats/receipt-list.js';
import { emptyStack, undoPush, undoPop, undoSettle } from './formats/undo.js';
import { PROJECTIONS, CARD_TOKENS, cardsEffective, cardsApply, cardsQuery } from './cards.js';
import { findings as cardsFindings } from './cards-findings.js';

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
  register('fn.studio.receipts', receiptList, { memo: false });
  register('fn.undo.push', undoPush, { memo: false });
  register('fn.undo.pop', undoPop, { memo: false });
  register('fn.undo.settle', undoSettle, { memo: false });
  register('fn.cards.effective', cardsEffective);
  register('fn.cards.apply', cardsApply);
  register('fn.cards.query', cardsQuery);
  let previousCardInstances = new Set();
  function publishWorld(world) {
    world = validateWorld(world); pxc.set('px.studio.world', world);
    const present = new Set();
    for (const [type, records] of Object.entries(world.objects)) for (const [key, record] of Object.entries(records)) { const a = partAddress(type, key); present.add(a); source(a, record); }
    for (const a of previousObjects) if (!present.has(a)) pxc.set(a, null); // Tombstones cannot masquerade as live objects.
    previousObjects = present;
    source('px.domain.schemas', world.schemas);
    for (const preset of Object.values(world.presets)) source(`px.presentation.${preset.id}`, preset);
    source('px.comparison.layout', world.layout); source('px.comparison.states', world.battle);
    source('px.discstudio.cards.tokens', CARD_TOKENS);
    source('px.discstudio.cards.global', world.cards.global);
    for (const p of PROJECTIONS) source(`px.discstudio.cards.projection.${p}`, world.cards.projections[p] ?? {});
    const presentInstances = new Set();
    for (const p of PROJECTIONS) for (const [discId, override] of Object.entries(world.cards.instances[p] ?? {})) {
      const a = `px.discstudio.cards.instance.${p}.${discId}`; presentInstances.add(a); source(a, override);
    }
    for (const a of previousCardInstances) if (!presentInstances.has(a)) pxc.set(a, null); // A cleared override tombstones its Part.
    previousCardInstances = presentInstances;
  }
  publishWorld(freeze(validateWorld(initial)));
  for (const finding of cardsFindings) source(finding.address, finding);
  pxc.set('px.undo.studio', emptyStack('studio'));
  const world = () => pxc.get('px.studio.world');
  const calc = (call, bindings, into, args = {}) => ({ call, with: bindings, args, into });
  const tick = (name, calcs) => ({ name, Calculations: calcs });
  const step = (name, call, bindings, into, args = {}) => tick(name, [calc(call, bindings, into, args)]);
  const compose = (name, ticks) => readPql(JSON.stringify({ PrincipleComponentRender: name, Ticks: ticks }), JSON.parse);
  /**
   * One receipt for one run. `run.schedule` is filed on it only when exec.js
   * reported one -- a parallel run, a budgeted run, or a run a budget stopped --
   * so a plain serial receipt is byte for byte the receipt it always was
   * (pyto/viewer/RECORD.md, "Placement and budget").
   */
  function settle(name, composition, run, mark) {
    const invoked = calls.slice(mark); if (calls.length > 1000) calls.splice(0, calls.length - 1000);
    const trace = run.Ticks.flatMap(t => t.Calculations.map(c => ({ tick: t.name, call: c.actualCall, inputs: c.with, output: c.into, produces: c.produces }))).map((r, i) => ({ ...r, ...invoked[i] }));
    const receipt = freeze({ composition, trace, computed: trace.filter(r => !r.reused).length, reused: trace.filter(r => r.reused).length, ...(run.schedule ? { schedule: run.schedule } : {}) });
    pxc.set(`px.receipt.${name}`, receipt);
    return receipt;
  }
  function execute(name, ticks, schedule = {}) {
    const mark = calls.length, composition = compose(name, ticks);
    return settle(name, composition, invokePql(composition, pxc, schedule), mark);
  }
  /** The awaited run: the only way to ask for `parallel: true` ({?} ParallelIsAsync). */
  async function executeAsync(name, ticks, schedule = {}) {
    const mark = calls.length, composition = compose(name, ticks);
    return settle(name, composition, await invokePqlAsync(composition, pxc, schedule), mark);
  }
  /**
   * The pyto-run-record@1 view of one recorded execution (pyto/viewer/RECORD.md),
   * built by the shared adapter (pyto/viewer/adapters.js:508) from the two Parts the
   * run already wrote -- px.pql.<name> (core/exec.js:66) and px.receipt.<name>
   * (runtime.js:58) -- and validated by the shared validator before it is kept.
   * It is kept at the reserved `run` second segment (pyto/BOARD.md:135-136), one
   * address per composition name, so re-exporting replaces it; domain facts under
   * px.domain.* are never written here.
   */
  function runRecord(name) {
    const composition = `px.pql.${name}`, receipt = `px.receipt.${name}`, address = `px.run.${name}`;
    if (!pxc.has(composition) || !pxc.has(receipt)) throw new Error(`No execution named '${name}' has been recorded in this session yet. Render the composition first.`);
    const record = validate(fromDiscStudioReceipt(pxc.get(composition), pxc.get(receipt)));
    pxc.set(address, record);
    return { address, record };
  }
  function dispatch(command) {
    push('px.studio.world');
    source('px.input.command', { ...command, eventId: id('event'), time: new Date().toISOString() });
    const run = execute('studio-command', [step('ApplyCommand', 'fn.studio.applyCommand', { world: 'px.studio.world', command: 'px.input.command' }, 'px.studio.nextWorld')]);
    publishWorld(pxc.get('px.studio.nextWorld')); listener(world(), command, run); return run;
  }
  /**
   * The shared card chain, now with the cascade Tick task 78 asks for:
   * `Cascade:<label>` computes the effective tokens then applies them to the
   * chosen preset (task 57: two Calculations in declared order, one Tick,
   * the second reading the first's produce -- classifyTick calls this a
   * chain), and `Card:<label>` composes from the resulting preset instead of
   * the raw one. `label` names the Ticks (discId ordinarily; recompose()
   * below uses the projection name instead, since it renders one disc four
   * ways in a single composition and needs four distinct Tick names).
   */
  function cardSteps(discId, presetId, context, entry, suffix, projection = 'single', label = discId) {
    const w = world(), disc = get(w, 'Disc', discId), preset = w.presets[presetId];
    if (!disc) throw new Error(`Missing physical disc '${discId}'. Nothing was silently dropped.`);
    if (!preset) throw new Error(`Missing presentation '${presetId}'.`);
    const mold = get(w, 'Mold', disc.moldId), maker = mold && get(w, 'Manufacturer', mold.manufacturerId);
    if (!mold || !maker) throw new Error(`The product identity for '${disc.nickname || disc.id}' is unresolved.`);
    const roots = { entry: { type: 'BattleEntry', record: entry }, disc: { type: 'Disc', id: discId }, bag: { type: 'Bag', id: context.bagId }, competition: { type: 'Competition', id: context.competitionId }, round: { type: 'Round', id: context.roundId } };
    if (context.extraType && w.schemas[context.extraType]) roots[context.extraType.toLowerCase()] = { type: context.extraType, id: context.extraId };
    const prefix = `px.render.${suffix}`, mat = source(`${prefix}.inputs`, materialFor(w, roots));
    const ea = source(`${prefix}.entry`, entry);
    const effectiveAddress = `px.discstudio.cards.effective.${projection}.${discId}`, presetAddress = `px.discstudio.cards.preset.${projection}.${discId}`;
    return {
      prefix,
      ticks: [
        step(`Fields:${label}`, 'fn.domain.fields', { material: mat }, `${prefix}.fields`),
        step(`Art:${label}`, 'fn.disc.art', { disc: partAddress('Disc', discId), mold: partAddress('Mold', mold.id), maker: partAddress('Manufacturer', maker.id) }, `${prefix}.art`),
        tick(`Cascade:${label}`, [
          calc('fn.cards.effective', { global: 'px.discstudio.cards.global', projection: `px.discstudio.cards.projection.${projection}`, instances: `px.discstudio.cards.instance.${projection}.*` }, effectiveAddress, { projectionName: projection, discId }),
          calc('fn.cards.apply', { preset: `px.presentation.${presetId}`, effective: effectiveAddress }, presetAddress)
        ]),
        step(`Card:${label}`, 'fn.card.compose', { fields: `${prefix}.fields`, art: `${prefix}.art`, preset: presetAddress, entry: ea }, `${prefix}.card`),
        step(`CardSvg:${label}`, 'fn.card.svg', { card: `${prefix}.card` }, `${prefix}.svg`)
      ]
    };
  }
  function card(discId, presetId, context = {}, entry = null, projection = 'single') {
    const { prefix, ticks } = cardSteps(discId, presetId, context, entry, `single.${discId}`, projection);
    const run = execute('display-card', ticks);
    return { ...pxc.get(`${prefix}.svg`), card: pxc.get(`${prefix}.card`), fields: pxc.get(`${prefix}.fields`), part: `${prefix}.svg`, run };
  }
  function sceneComposition({ mode = 'battle', discId, bagId, competitionId, roundId, stateId, presetId } = {}) {
    const w = world(), state = stateId ? w.battle.states.find(s => s.id === stateId) : currentBattle(w);
    if (!state) throw new Error('Comparison state is missing.');
    const entries = mode === 'card' ? [{ discId, id: 'single' }] : w.battle.entries;
    const ticks = [], inputs = { layout: 'px.comparison.layout' };
    entries.forEach((entry, i) => {
      const info = mode === 'card' ? null : { ...entry, score: state.scores[entry.id] ?? null, highlighted: state.highlight === entry.id, winner: state.winners.includes(entry.id) };
      const built = cardSteps(entry.discId, presetId || w.layout.presetId, { bagId, competitionId, roundId }, info, `course.${entry.id}`, 'competition');
      ticks.push(...built.ticks); inputs[`card${i}`] = `${built.prefix}.card`;
    });
    ticks.push(step('ArrangeComparison', 'fn.comparison.layout', inputs, 'px.course.scene'));
    ticks.push(step('MaterializeOverlay', 'fn.overlay.svg', { scene: 'px.course.scene' }, 'px.course.svg'));
    return { ticks, state };
  }
  const rendered = state => ({ ...pxc.get('px.course.svg'), part: 'px.course.svg', stateId: state.id, scene: pxc.get('px.course.scene') });
  function scene(options = {}) {
    const { ticks, state } = sceneComposition(options);
    const run = execute('on-the-course', ticks);
    return { ...rendered(state), run };
  }
  /**
   * The same sample composition, one Tick per stage instead of one Tick per
   * card: every card's Fields (then Art, then Card, then CardSvg) is a branch of
   * one Tick, which is what the node law allows to run at once -- no branch
   * reads what a sibling of its own Tick publishes.
   */
  function byStage(ticks) {
    const stages = new Map();
    for (const tick of ticks) {
      const stage = tick.name.includes(':') ? tick.name.slice(0, tick.name.indexOf(':')) : tick.name;
      if (!stages.has(stage)) stages.set(stage, { name: stage, Calculations: [] });
      stages.get(stage).Calculations.push(...tick.Calculations);
    }
    return [...stages.values()];
  }
  async function sceneParallel(options = {}) {
    const { ticks, state } = sceneComposition(options);
    const run = await executeAsync('on-the-course-parallel', byStage(ticks), { parallel: true });
    return { ...rendered(state), run };
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
  /**
   * UndoStack: `fn.undo.push` records the value an address holds now; `fn.undo.pop`
   * writes the recorded value back and `fn.undo.settle` takes it off the stack.
   * Each is an ordinary Calculation invocation, so runRecord() carries all of them.
   */
  const stackAddress = scope => `px.undo.${scope}`;
  function undoStack(scope = 'studio') { const address = stackAddress(scope); if (!pxc.has(address)) pxc.set(address, emptyStack(scope)); return pxc.get(address); }
  function push(address, scope = 'studio') {
    undoStack(scope);
    return execute('studio-undo-push', [step('Push', 'fn.undo.push', { stack: stackAddress(scope), value: address }, stackAddress(scope), { address, scope })]);
  }
  function pop(address, scope = 'studio') {
    undoStack(scope);
    const run = execute('studio-undo', [
      step('Restore', 'fn.undo.pop', { stack: stackAddress(scope), current: address }, address, { address, scope }),
      step('Settle', 'fn.undo.settle', { stack: stackAddress(scope) }, stackAddress(scope), { address, scope })
    ]);
    if (address === 'px.studio.world') { publishWorld(freeze(validateWorld(pxc.get(address)))); listener(world(), { type: 'undo.pop', address, scope }, run); }
    return run;
  }
  /** The studio's own receipts, read back through the PQL prefix query px.receipt.*. */
  function receipts() {
    const run = execute('studio-receipts', [step('Receipts', 'fn.studio.receipts', { receipts: 'px.receipt.*' }, ['px.studio.receipts', 'px.studio.receipts.summary'])]);
    return { rows: pxc.get('px.studio.receipts'), summary: pxc.get('px.studio.receipts.summary'), run };
  }
  /**
   * The card cascade editor's API (task 78). `presetFor` names the preset
   * each projection composes with today (shelf/bag always show the disc
   * itself; single/competition follow the shared comparison design), and is
   * the only place that mapping lives.
   */
  function presetFor(projection) {
    if (projection === 'shelf' || projection === 'bag') return 'discImage';
    if (projection === 'single' || projection === 'competition') return world().layout.presetId;
    throw new Error(`Unknown card projection '${projection}'.`);
  }
  const cardsCascadeTick = (label, projection, discId, presetId) => {
    const effectiveAddress = `px.discstudio.cards.effective.${projection}.${discId}`, presetAddress = `px.discstudio.cards.preset.${projection}.${discId}`;
    return tick(`Cascade:${label}`, [
      calc('fn.cards.effective', { global: 'px.discstudio.cards.global', projection: `px.discstudio.cards.projection.${projection}`, instances: `px.discstudio.cards.instance.${projection}.*` }, effectiveAddress, { projectionName: projection, discId }),
      calc('fn.cards.apply', { preset: `px.presentation.${presetId}`, effective: effectiveAddress }, presetAddress)
    ]);
  };
  /** Runs the Cascade Tick alone -- the effective tokens for one projection/disc pair, on the record. */
  function cardsEffectiveRun(projection, discId, context = {}) {
    if (!PROJECTIONS.includes(projection)) throw new Error(`Unknown card projection '${projection}'.`);
    if (!get(world(), 'Disc', discId)) throw new Error(`Missing physical disc '${discId}'. Nothing was silently dropped.`);
    const effectiveAddress = `px.discstudio.cards.effective.${projection}.${discId}`;
    const run = execute('cards-effective', [cardsCascadeTick(discId, projection, discId, presetFor(projection))]);
    return { ...pxc.get(effectiveAddress), part: effectiveAddress, run };
  }
  /**
   * One composition, `cards-recompose`, that renders one disc through all
   * four projections' chains -- each Tick named by projection (`Cascade:shelf`,
   * `Card:shelf`, ...) rather than by discId, and each addressed under its own
   * `px.render.recompose.<projection>.<discId>` prefix, since the four chains
   * share one discId in one run. `changed` reads the settled receipt: the
   * `fn.card.compose` step for a projection is `!reused` exactly when that
   * projection's effective tokens (and so its applied preset) actually moved.
   */
  function recompose(discId, context = {}) {
    if (!get(world(), 'Disc', discId)) throw new Error(`Missing physical disc '${discId}'. Nothing was silently dropped.`);
    const prefixes = {}, ticks = [];
    for (const projection of PROJECTIONS) {
      const { prefix, ticks: built } = cardSteps(discId, presetFor(projection), context, null, `recompose.${projection}.${discId}`, projection, projection);
      prefixes[projection] = prefix; ticks.push(...built);
    }
    const receipt = execute('cards-recompose', ticks);
    const cards = {};
    for (const projection of PROJECTIONS) {
      const prefix = prefixes[projection], svg = pxc.get(`${prefix}.svg`);
      const row = receipt.trace.find(r => r.tick === `Card:${projection}` && r.call === 'fn.card.compose');
      cards[projection] = { svg: svg.svg, width: svg.width, height: svg.height, part: `${prefix}.svg`, changed: !!row && row.reused === false };
    }
    return { receipt, cards };
  }
  /** Every PQL read the editor needs over the cascade, one Calculation, one Part per name. */
  function cardsQueryRun(name, args = {}) {
    const into = `px.discstudio.cards.query.${name}`;
    const bindings = { global: 'px.discstudio.cards.global', projections: 'px.discstudio.cards.projection.*', instances: 'px.discstudio.cards.instance.*', effective: 'px.discstudio.cards.effective.*' };
    execute('cards-query', [step('Query', 'fn.cards.query', bindings, into, { name, ...args })]);
    return pxc.get(into);
  }
  return {
    pxc, world, dispatch, card, scene, sceneParallel, constraints, counters, runRecord, execute, executeAsync,
    receipts,
    cards: { projections: PROJECTIONS, tokens: CARD_TOKENS, presetFor, effective: cardsEffectiveRun, recompose, query: cardsQueryRun },
    undo: { push, pop, stack: undoStack, depth: (scope = 'studio') => undoStack(scope).depth },
    onChange(fn) { listener = fn; },
    replace(next) { publishWorld(freeze(validateWorld(next))); listener(world(), { type: 'draft.import' }, null); },
    parts() { return [...addresses].sort().map(address => ({ address, value: pxc.get(address) })); },
    /** Read/select Parts without building another state store. */
    select(prefix) { return [...addresses].filter(a => a.startsWith(prefix)).map(a => ({ address: a, value: pxc.get(a) })); }
  };
}
