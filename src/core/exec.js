/**
 * ChainSpot PxC/PQL browser core, transcribed in DiscStudio @ d5e324c
 * source/candidate-pxc/chainspot/exec.js (original ChainSpot @82f8fc9).
 * Only packaging change: no implicit YAML dependency. readPql requires an
 * explicit parser. The studio uses the existing PQL object schema as JSON.
 * Execution order, Part binding and Calculation invocation are unchanged.
 */
export function pxKey(address) { return Object.freeze({ address }); }
export function pxFn(address) { return Object.freeze({ address }); }
function addressOf(slot) { return typeof slot === 'string' ? slot : slot.address; }
export function createExecBoard() { return boardFrom(new Map(), new Map()); }
function boardFrom(slots, calculations) {
  return {
    fork: () => boardFrom(new Map(slots), new Map(calculations)),
    get(slot) { const address = addressOf(slot); if (!slots.has(address)) throw new Error(`exec board: slot '${address}' not produced yet.`); return slots.get(address); },
    has: (slot) => slots.has(addressOf(slot)),
    set: (slot, value) => { slots.set(addressOf(slot), value); },
    register(fn, calculate) { const current = calculations.get(fn.address); if (current && current !== calculate) throw new Error(`PxC: calculation '${fn.address}' is already registered.`); calculations.set(fn.address, calculate); },
    keys: () => [...slots.keys()],
    call(fn, args) { const calculate = calculations.get(fn.address); if (!calculate) throw new Error(`PxC: calculation '${fn.address}' is not registered.`); return calculate(args); }
  };
}
export function trackAccess(board, tick) {
  const consumed = new Set(), produced = new Set(), writes = [], declaredConsumes = new Set(tick.consumes);
  const tracked = {
    fork: () => board.fork(),
    get(slot) { const address = addressOf(slot); consumed.add(address); try { return board.get(slot); } catch (error) { if (!board.has(slot)) throw new Error(`PxC: Tick '${tick.id}' read missing address '${address}'.`, { cause: error }); throw error; } },
    has: (slot) => board.has(slot),
    set(slot, value) { const address = addressOf(slot), existed = board.has(slot); produced.add(address); writes.push({ address, kind: !existed ? 'new-address' : declaredConsumes.has(address) ? 'refinement' : 'replacement' }); board.set(slot, value); },
    register: (fn, calculate) => board.register(fn, calculate),
    keys: () => board.keys(),
    call: (fn, args) => board.call(fn, args)
  };
  return { tracked, consumed, produced, writes };
}
function object(value, where) { if (!value || typeof value !== 'object' || Array.isArray(value)) throw new Error(`PQL ${where}: expected a mapping.`); return value; }
function text(value, where) { if (typeof value !== 'string' || !value.length) throw new Error(`PQL ${where}: expected a nonempty string.`); return value; }
function list(value, where) { if (!Array.isArray(value)) throw new Error(`PQL ${where}: expected a sequence.`); return value; }
/** A `with` value is one Part address, or a `<prefix>.*` prefix query over the board. */
export function isPrefixQuery(address) { return typeof address === 'string' && address.endsWith('.*'); }
function binding(value, where) {
  const address = text(value, where);
  if (address.includes('*') && !isPrefixQuery(address)) throw new Error(`PQL ${where}: '*' is only the last segment of a prefix query, as in 'px.receipt.*'.`);
  return address;
}
/**
 * `into` is one address, or a non-empty array of distinct addresses: one pass,
 * several Parts, one receipt listing all of them ({?} WhatIsATick, decided).
 */
function produces(value, where) {
  if (!Array.isArray(value)) return text(value, where);
  if (!value.length) throw new Error(`PQL ${where}: expected at least one address; a Calculation that publishes nothing has no place in this grammar.`);
  const addresses = value.map((entry, index) => text(entry, `${where}[${index}]`)), seen = new Set();
  addresses.forEach((address, index) => { if (seen.has(address)) throw new Error(`PQL ${where}[${index}]: '${address}' is declared twice; one Calculation publishes each address once.`); seen.add(address); });
  return Object.freeze(addresses);
}
/** Every address one Calculation publishes, in declared order. */
export function produceAddresses(into) { return Array.isArray(into) ? [...into] : [into]; }
/** The values a multi-produce output hands to each declared address, in order. */
function spread(into, output, where) {
  if (Array.isArray(output)) {
    if (output.length !== into.length) throw new Error(`PQL ${where}: 'into' declares ${into.length} addresses and the Calculation returned ${output.length} values.`);
    return output;
  }
  if (!output || typeof output !== 'object') throw new Error(`PQL ${where}: 'into' declares ${into.length} addresses, so the Calculation must return an object keyed by them or an array of ${into.length} values; got ${output === null ? 'null' : typeof output}.`);
  for (const address of into) if (!Object.hasOwn(output, address)) throw new Error(`PQL ${where}: the output has no key '${address}'; every declared produce must be present, and nothing is silently dropped.`);
  return into.map(address => output[address]);
}
/** Read every Part under a prefix, newest position irrelevant: sorted by address, so a query is one value. */
export function queryPrefix(pxc, pattern) {
  if (typeof pxc.keys !== 'function') throw new Error(`PQL: this board cannot answer the prefix query '${pattern}'.`);
  const prefix = pattern.slice(0, -1);
  return Object.freeze(Object.fromEntries(pxc.keys().filter(address => address.startsWith(prefix)).sort().map(address => [address, pxc.get(address)])));
}
export function readPql(source, parseYaml) {
  const root = object(parseYaml(source), 'document');
  return { PrincipleComponentRender: text(root.PrincipleComponentRender, 'PrincipleComponentRender'), Ticks: list(root.Ticks, 'Ticks').map((value, tickIndex) => {
    const tick = object(value, `Ticks[${tickIndex}]`);
    return { name: text(tick.name, `Ticks[${tickIndex}].name`), Calculations: list(tick.Calculations, 'Calculations').map((value, index) => {
      const where = `${tick.name}.Calculations[${index}]`, calculation = object(value, where), call = text(calculation.call, `${where}.call`);
      if (!call.startsWith('fn.')) throw new Error(`PQL ${where}.call: expected a registered fn. address.`);
      const bindings = object(calculation.with ?? {}, `${where}.with`), args = object(calculation.args ?? {}, `${where}.args`);
      for (const [name, address] of Object.entries(bindings)) { binding(address, `${where}.with.${name}`); if (Object.hasOwn(args, name)) throw new Error(`PQL ${where}: '${name}' appears in both with and args.`); }
      return { call, with: bindings, args, into: produces(calculation.into, `${where}.into`) };
    }) };
  }) };
}

/* ------------------------------------------------------------------ */
/* the schedule: parallel Ticks, placement, latency and a budget       */
/* ------------------------------------------------------------------ */

/** Milliseconds, rounded the way the record rounds them (RECORD.md). */
function round3(value) { return Math.round(value * 1000) / 1000; }
/** The default clock is injectable so a budget test never waits on real time. */
const wallClock = () => performance.now();
/** How the options reach here: `invokePql(doc, pxc, opts)` and `invokePql(doc, {pxc, ...opts})` are the same call. */
function options(second, third) { return second && typeof second.call === 'function' ? { pxc: second, ...third } : { ...second }; }
/**
 * The name one Calculation answers to inside its Tick. PQL gives a Calculation
 * no id of its own, so a refusal names it the way a reader can find it: its
 * position, its call and the addresses it declares.
 */
function calculationId(calculation, index) { return `Calculations[${index}] '${calculation.call}' -> ${produceAddresses(calculation.into).join(', ')}`; }
/** Does this binding read `address`? A `.*` prefix query reads every address under it. */
function bindingReads(binding, address) { return isPrefixQuery(binding) ? address.startsWith(binding.slice(0, -1)) : binding === address; }
/**
 * The node law, checked before a parallel Tick runs anything: no Calculation
 * may read what a sibling publishes in the same Tick, and no address may be
 * declared by two siblings. Reads are the document's `with` bindings and their
 * `.*` prefixes, exactly as pyto/experiments/tick-laws/tick_laws.py computes
 * them, so both readers refuse the same Tick. Refusing before the Tick runs is
 * what keeps a parallel Tick all-or-nothing: no Calculation of a refused Tick
 * is invoked and no Part of it is published.
 */
export function refuseUnparallelTick(tick) {
  const declaredBy = new Map();
  tick.Calculations.forEach((calculation, index) => {
    const id = calculationId(calculation, index);
    for (const address of produceAddresses(calculation.into)) {
      const owner = declaredBy.get(address);
      if (owner !== undefined) throw new Error(`PQL ${tick.name}: parallel refused: ${owner} and ${id} both declare into '${address}'; in one Tick an address has one producer.`);
      declaredBy.set(address, id);
    }
  });
  tick.Calculations.forEach((calculation, index) => {
    const id = calculationId(calculation, index);
    for (const binding of Object.values(calculation.with)) {
      for (const [address, owner] of declaredBy) {
        if (owner === id || !bindingReads(binding, address)) continue;
        throw new Error(`PQL ${tick.name}: parallel refused: ${id} reads '${address}', which its sibling ${owner} produces in the same Tick.`);
      }
    }
  });
  return tick;
}

/** Read this Calculation's inputs and invoke it. The output is not published here. */
function invoke(calculation, pxc, overrides) {
  const inputs = Object.fromEntries(Object.entries(calculation.with).map(([name, address]) => [name, isPrefixQuery(address) ? queryPrefix(pxc, address) : pxc.get(address)]));
  const replacement = overrides[calculation.call], actualCall = replacement?.call ?? calculation.call, args = { ...calculation.args, ...replacement?.args };
  for (const name of Object.keys(inputs)) if (Object.hasOwn(args, name)) throw new Error(`Argument '${name}' shadows a named input.`);
  const output = pxc.call(pxFn(actualCall), { ...args, ...inputs });
  return { actualCall, args, inputs, output };
}

/** Publish what one Calculation returned, and hand back its line of testimony. */
function publish(tick, calculation, step, pxc) {
  const addresses = produceAddresses(calculation.into);
  const values = Array.isArray(calculation.into) ? spread(calculation.into, step.output, `${tick.name}.${calculation.call}.into`) : [step.output];
  addresses.forEach((address, index) => pxc.set(address, values[index]));
  return { ...calculation, actualCall: step.actualCall, args: step.args, inputs: step.inputs, output: step.output, produces: addresses };
}

function failed(tick, calculation, cause) { return new Error(`PQL ${tick.name}: ${calculation.call} -> ${produceAddresses(calculation.into).join(', ')} failed.`, { cause }); }

/**
 * The schedule the run reports, in the shape RECORD.md's "Placement and budget"
 * asks for. It is written **only** when the run was parallel, was given a
 * budget, or was stopped by one: absent means serial and unbudgeted, so a plain
 * serial run's testimony and receipt are byte for byte what they were before
 * any of this existed.
 */
function schedule({ parallel, budgetMs, stoppedAfterTick, ticks }) {
  if (!parallel && budgetMs === null && stoppedAfterTick === null) return null;
  return Object.freeze({
    parallel,
    budget: Object.freeze({ limit_ms: budgetMs, stopped_after_tick: stoppedAfterTick, completed: stoppedAfterTick === null }),
    ticks: Object.freeze(ticks.map(tick => Object.freeze({ name: tick.name, latency_ms: tick.latency_ms, placements: Object.freeze(tick.placements) })))
  });
}

/** A budget is read at the Tick boundary and nowhere else: a Tick that started finishes. */
function overBudget(budgetMs, clock, started) { return budgetMs !== null && clock() - started > budgetMs; }

function finish(composition, ticks, scheduled, pxc) {
  const run = { PrincipleComponentRender: composition.PrincipleComponentRender, Ticks: ticks };
  if (scheduled) run.schedule = scheduled;
  pxc.set(`px.pql.${composition.PrincipleComponentRender}`, run);
  return run;
}

/**
 * Run a composition. `invokePql(doc, pxc, { budgetMs, clock })` is the studio's
 * synchronous path and is unchanged for a plain serial run; `parallel: true`
 * needs `invokePqlAsync`, because a Tick whose branches overlap can only be
 * awaited ({?} ParallelIsAsync).
 */
export function invokePql(composition, second, third) {
  const { pxc, overrides = {}, parallel = false, budgetMs = null, clock = wallClock } = options(second, third);
  if (parallel) throw new Error('PQL: a parallel run is awaited; call invokePqlAsync(composition, pxc, { parallel: true }).');
  const started = clock(), ticks = [], measured = [];
  let stoppedAfterTick = null;
  for (const tick of composition.Ticks) {
    if (ticks.length && overBudget(budgetMs, clock, started)) { stoppedAfterTick = ticks[ticks.length - 1].name; break; }
    const tickStarted = clock(), calculations = [];
    for (const calculation of tick.Calculations) {
      try { calculations.push(publish(tick, calculation, invoke(calculation, pxc, overrides), pxc)); }
      catch (cause) { throw failed(tick, calculation, cause); }
    }
    ticks.push({ name: tick.name, Calculations: calculations });
    measured.push({ name: tick.name, latency_ms: round3(clock() - tickStarted), placements: tick.Calculations.map(() => null) });
  }
  return finish(composition, ticks, schedule({ parallel: false, budgetMs, stoppedAfterTick, ticks: measured }), pxc);
}

/**
 * The same run, awaited. With `parallel: true` the Calculations of one Tick are
 * started together (`Promise.all` over async wrappers) and every result is
 * published in declared order **after** the Tick, so the board never holds half
 * a Tick; a Calculation that reads a sibling's produce is refused before the
 * Tick runs. The testimony is byte-identical to the serial run's: placement and
 * latency live in `run.schedule`, outside it.
 */
export async function invokePqlAsync(composition, second, third) {
  const { pxc, overrides = {}, parallel = false, budgetMs = null, clock = wallClock } = options(second, third);
  const started = clock(), ticks = [], measured = [];
  let stoppedAfterTick = null;
  for (const tick of composition.Ticks) {
    if (ticks.length && overBudget(budgetMs, clock, started)) { stoppedAfterTick = ticks[ticks.length - 1].name; break; }
    if (parallel) refuseUnparallelTick(tick);
    const tickStarted = clock(), placements = [];
    let steps;
    if (parallel) {
      // Each wrapper runs to its first await, so a worker index is handed out in
      // the order the branches actually start; a synchronous Calculation simply
      // runs to completion there and its branch is already done.
      steps = await Promise.all(tick.Calculations.map(async (calculation, index) => {
        placements[index] = { worker: index, started_ms: round3(clock() - tickStarted) };
        try { const step = invoke(calculation, pxc, overrides); step.output = await step.output; return step; }
        catch (cause) { throw failed(tick, calculation, cause); }
      }));
    } else {
      steps = [];
      for (const calculation of tick.Calculations) {
        placements.push(null);
        try { const step = invoke(calculation, pxc, overrides); step.output = await step.output; steps.push(step); }
        catch (cause) { throw failed(tick, calculation, cause); }
      }
    }
    const latency = round3(clock() - tickStarted);
    const calculations = tick.Calculations.map((calculation, index) => {
      try { return publish(tick, calculation, steps[index], pxc); }
      catch (cause) { throw failed(tick, calculation, cause); }
    });
    ticks.push({ name: tick.name, Calculations: calculations });
    measured.push({ name: tick.name, latency_ms: latency, placements });
  }
  return finish(composition, ticks, schedule({ parallel, budgetMs, stoppedAfterTick, ticks: measured }), pxc);
}
