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
export function invokePql(composition, { pxc, overrides = {} }) {
  const ticks = [];
  for (const tick of composition.Ticks) {
    const calculations = [];
    for (const calculation of tick.Calculations) {
      try {
        const inputs = Object.fromEntries(Object.entries(calculation.with).map(([name, address]) => [name, isPrefixQuery(address) ? queryPrefix(pxc, address) : pxc.get(address)]));
        const replacement = overrides[calculation.call], actualCall = replacement?.call ?? calculation.call, args = { ...calculation.args, ...replacement?.args };
        for (const name of Object.keys(inputs)) if (Object.hasOwn(args, name)) throw new Error(`Argument '${name}' shadows a named input.`);
        const addresses = produceAddresses(calculation.into);
        const output = pxc.call(pxFn(actualCall), { ...args, ...inputs });
        const values = Array.isArray(calculation.into) ? spread(calculation.into, output, `${tick.name}.${calculation.call}.into`) : [output];
        addresses.forEach((address, index) => pxc.set(address, values[index]));
        calculations.push({ ...calculation, actualCall, args, inputs, output, produces: addresses });
      } catch (cause) { throw new Error(`PQL ${tick.name}: ${calculation.call} -> ${produceAddresses(calculation.into).join(', ')} failed.`, { cause }); }
    }
    ticks.push({ name: tick.name, Calculations: calculations });
  }
  const run = { PrincipleComponentRender: composition.PrincipleComponentRender, Ticks: ticks };
  pxc.set(`px.pql.${composition.PrincipleComponentRender}`, run);
  return run;
}
