/**
 * pyto-run-record@1 adapters and validator.
 *
 * One record format, four producers. The schema and every field rule live in
 * ./RECORD.md; this file is its executable form. Dependency-free ES module:
 * it runs unchanged in a browser <script type="module"> and under `node --test`.
 *
 * Reference semantics are the JS runtime's (ULTRACODE-WEEK.md "Reframing 4",
 * "JS is first class"): where the JS and Python records could differ, the
 * shapes in ../../src/core/exec.js and ../../src/runtime.js decide.
 */

export const SCHEMA = 'pyto-run-record@1';

/** RECORD.md: values over 256 KB are replaced by `omitted` with a note. */
export const MAX_VALUE_BYTES = 262144;

/** RECORD.md: arrays longer than 200 entries carry the first 200 and a note. */
export const MAX_ARRAY_ENTRIES = 200;

export const RUNTIMES = ['pyto', 'discstudio', 'chesslab', 'wumpus'];
export const VALUE_KINDS = ['json', 'text', 'svg', 'png-data-url', 'omitted'];
export const WRITE_KINDS = ['new-address', 'refinement', 'replacement'];

const encoder = new TextEncoder();

function utf8Length(text) {
  return encoder.encode(text).length;
}

/* ------------------------------------------------------------------ */
/* validate                                                            */
/* ------------------------------------------------------------------ */

export class RecordSchemaError extends Error {
  constructor(path, message) {
    super(`${SCHEMA} ${path}: ${message}`);
    this.name = 'RecordSchemaError';
    this.path = path;
  }
}

function fail(path, message) {
  throw new RecordSchemaError(path, message);
}

function show(value) {
  if (value === undefined) return 'undefined';
  if (typeof value === 'string') return JSON.stringify(value.length > 60 ? `${value.slice(0, 57)}...` : value);
  if (value === null || typeof value !== 'object') return String(value);
  if (Array.isArray(value)) return `an array of ${value.length}`;
  return 'an object';
}

function isPlainObject(value) {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}

function requireObject(value, path) {
  if (!isPlainObject(value)) fail(path, `expected an object, got ${show(value)}`);
  return value;
}

function requireArray(value, path) {
  if (!Array.isArray(value)) fail(path, `expected an array, got ${show(value)}`);
  return value;
}

function requireString(value, path, { nonEmpty = true } = {}) {
  if (typeof value !== 'string') fail(path, `expected a string, got ${show(value)}`);
  if (nonEmpty && value.length === 0) fail(path, 'expected a non-empty string');
  return value;
}

function requireNullableString(value, path) {
  if (value === null) return null;
  return requireString(value, path);
}

function requireNullableNumber(value, path) {
  if (value === null) return null;
  if (typeof value !== 'number' || !Number.isFinite(value)) fail(path, `expected a finite number or null, got ${show(value)}`);
  return value;
}

function requireBoolean(value, path) {
  if (typeof value !== 'boolean') fail(path, `expected a boolean, got ${show(value)}`);
  return value;
}

function requireEnum(value, allowed, path) {
  if (!allowed.includes(value)) fail(path, `expected one of ${allowed.map((v) => JSON.stringify(v)).join(', ')}, got ${show(value)}`);
  return value;
}

function requireStringArray(value, path) {
  requireArray(value, path);
  value.forEach((entry, index) => requireString(entry, `${path}[${index}]`));
  return value;
}

/** RECORD.md: `inputs` keeps the testimony spelling `px:<address>` / `fn:<id>`. */
function requireBindingSpelling(value, path) {
  requireString(value, path);
  if (!value.startsWith('px:') && !value.startsWith('fn:')) {
    fail(path, `expected a testimony binding spelled "px:<address>" or "fn:<id>", got ${show(value)}`);
  }
  return value;
}

function validateValue(value, path) {
  requireObject(value, path);
  const kind = requireEnum(value.kind, VALUE_KINDS, `${path}.kind`);
  if (!('data' in value)) fail(`${path}.data`, 'is required (null when the kind is "omitted")');
  if (!('note' in value)) fail(`${path}.note`, 'is required (null when there is nothing to say)');
  requireNullableString(value.note, `${path}.note`);
  if (kind === 'omitted') {
    if (value.data !== null) fail(`${path}.data`, `expected null for kind "omitted", got ${show(value.data)}`);
    if (typeof value.note !== 'string' || !value.note.length) fail(`${path}.note`, 'kind "omitted" must say why in note');
  } else if (kind !== 'json') {
    requireString(value.data, `${path}.data`, { nonEmpty: false });
  } else if (value.data === undefined) {
    fail(`${path}.data`, 'expected a JSON value, got undefined');
  }
  return value;
}

function validateInvocation(invocation, path, seenIds) {
  requireObject(invocation, path);
  const id = requireString(invocation.id, `${path}.id`);
  if (seenIds.has(id)) fail(`${path}.id`, `duplicate invocation id ${JSON.stringify(id)}; ids anchor annotations and must be unique in a record`);
  seenIds.add(id);

  const calculation = requireObject(invocation.calculation, `${path}.calculation`);
  requireNullableString(calculation.address, `${path}.calculation.address`);
  requireNullableString(calculation.implementation_sha256, `${path}.calculation.implementation_sha256`);
  requireString(calculation.identity_scope, `${path}.calculation.identity_scope`);

  const inputs = requireObject(invocation.inputs, `${path}.inputs`);
  for (const [name, binding] of Object.entries(inputs)) requireBindingSpelling(binding, `${path}.inputs.${name}`);
  requireObject(invocation.args, `${path}.args`);
  requireNullableString(invocation.into, `${path}.into`);

  requireArray(invocation.declared_consumes, `${path}.declared_consumes`);
  invocation.declared_consumes.forEach((entry, i) => requireBindingSpelling(entry, `${path}.declared_consumes[${i}]`));
  requireStringArray(invocation.actual_consumes, `${path}.actual_consumes`);
  requireStringArray(invocation.actual_produces, `${path}.actual_produces`);

  requireArray(invocation.writes, `${path}.writes`);
  invocation.writes.forEach((write, i) => {
    requireObject(write, `${path}.writes[${i}]`);
    requireString(write.address, `${path}.writes[${i}].address`);
    if (!('kind' in write)) fail(`${path}.writes[${i}].kind`, 'is required (null when the runtime does not record it)');
    if (write.kind !== null) requireEnum(write.kind, WRITE_KINDS, `${path}.writes[${i}].kind`);
  });

  requireNullableNumber(invocation.duration_ms, `${path}.duration_ms`);
  requireNullableString(invocation.result_sha256, `${path}.result_sha256`);
  requireBoolean(invocation.hit, `${path}.hit`);
  validateValue(invocation.value, `${path}.value`);
  return invocation;
}

/**
 * Throw a RecordSchemaError naming the offending path on any violation of
 * RECORD.md; return the record unchanged when it conforms.
 */
export function validate(record) {
  requireObject(record, 'document');
  if (record.schema !== SCHEMA) fail('schema', `expected ${JSON.stringify(SCHEMA)}, got ${show(record.schema)}`);
  requireString(record.pcr, 'pcr');

  const source = requireObject(record.source, 'source');
  requireEnum(source.runtime, RUNTIMES, 'source.runtime');
  requireNullableString(source.version, 'source.version');
  requireNullableString(source.commit, 'source.commit');

  const ticks = requireArray(record.ticks, 'ticks');
  const seenIds = new Set();
  let invocationCount = 0;
  let hitCount = 0;
  ticks.forEach((tick, index) => {
    const path = `ticks[${index}]`;
    requireObject(tick, path);
    if (tick.index !== index) fail(`${path}.index`, `expected ${index} (position in ticks), got ${show(tick.index)}`);
    requireString(tick.name, `${path}.name`);
    const invocations = requireArray(tick.invocations, `${path}.invocations`);
    invocations.forEach((invocation, i) => {
      validateInvocation(invocation, `${path}.invocations[${i}]`, seenIds);
      invocationCount += 1;
      if (invocation.hit) hitCount += 1;
    });
  });

  const parts = requireObject(record.parts, 'parts');
  for (const [address, part] of Object.entries(parts)) {
    const path = `parts[${JSON.stringify(address)}]`;
    requireObject(part, path);
    requireNullableString(part.written_by, `${path}.written_by`);
    requireStringArray(part.read_by, `${path}.read_by`);
    requireBoolean(part.preexisting, `${path}.preexisting`);
  }

  const counters = requireObject(record.counters, 'counters');
  for (const key of ['invocations', 'hits', 'computed']) {
    const value = counters[key];
    if (!Number.isInteger(value) || value < 0) fail(`counters.${key}`, `expected a non-negative integer, got ${show(value)}`);
  }
  requireNullableNumber(counters.wall_ms, 'counters.wall_ms');
  if (counters.invocations !== invocationCount) fail('counters.invocations', `expected ${invocationCount} (invocations in ticks), got ${counters.invocations}`);
  if (counters.hits !== hitCount) fail('counters.hits', `expected ${hitCount} (invocations with hit=true), got ${counters.hits}`);
  if (counters.hits + counters.computed !== counters.invocations) {
    fail('counters.computed', `expected ${counters.invocations - counters.hits} so hits + computed === invocations, got ${counters.computed}`);
  }
  return record;
}

/* ------------------------------------------------------------------ */
/* shared derivations                                                  */
/* ------------------------------------------------------------------ */

/** Strip the testimony marker: "px:a.b" -> "a.b", "fn:split" -> "split". */
export function bareAddress(binding) {
  if (typeof binding !== 'string') return '';
  return binding.startsWith('px:') || binding.startsWith('fn:') ? binding.slice(3) : binding;
}

/**
 * RECORD.md: hit is true when the invocation read a Part that existed before
 * this run (a `px:` binding whose address was not produced by an earlier
 * invocation of the same run), or when the runtime reports reuse. The owner's
 * definition (ULTRACODE-WEEK.md "Reframing 4"): any Part or Calculation being
 * used is a hit; do not over-define it.
 */
export function deriveHit(declaredConsumes, producedSoFar, reused = false) {
  if (reused === true) return true;
  for (const binding of declaredConsumes) {
    if (!binding.startsWith('px:')) continue;
    if (!producedSoFar.has(bareAddress(binding))) return true;
  }
  return false;
}

/** Classify a raw runtime value into a RECORD.md `value` block. */
export function materialize(raw, { digest = null, note = null } = {}) {
  if (raw === undefined) {
    return { kind: 'omitted', data: null, note: note || 'the runtime did not retain a value for this invocation' };
  }
  if (typeof raw === 'string') {
    const head = raw.slice(0, 400).trimStart();
    let kind = 'text';
    if (head.startsWith('<svg') || (head.startsWith('<?xml') && head.includes('<svg'))) kind = 'svg';
    else if (head.startsWith('data:image/png;base64,')) kind = 'png-data-url';
    return capped({ kind, data: raw, note }, utf8Length(raw), digest);
  }
  let data = raw;
  let arrayNote = note;
  if (Array.isArray(raw) && raw.length > MAX_ARRAY_ENTRIES) {
    data = raw.slice(0, MAX_ARRAY_ENTRIES);
    arrayNote = `array truncated: showing the first ${MAX_ARRAY_ENTRIES} of ${raw.length} entries`;
  }
  let text;
  try {
    text = JSON.stringify(data);
  } catch (error) {
    return { kind: 'omitted', data: null, note: `value is not JSON serializable: ${error.message}` };
  }
  if (text === undefined) return { kind: 'omitted', data: null, note: 'value is not JSON serializable' };
  return capped({ kind: 'json', data, note: arrayNote ?? null }, utf8Length(text), digest);
}

function capped(block, bytes, digest) {
  if (bytes > MAX_VALUE_BYTES) {
    const tail = digest ? `; digest ${digest}` : '; digest unavailable';
    return { kind: 'omitted', data: null, note: `value omitted: ${bytes} bytes over the ${MAX_VALUE_BYTES}-byte cap${tail}` };
  }
  return { ...block, note: block.note ?? null };
}

/**
 * Derive `parts` from the invocations, in RECORD.md's terms: written_by is the
 * first invocation that produced the address, read_by is every invocation whose
 * bindings resolved it, preexisting is true when it was read before any
 * invocation in this record produced it.
 */
export function derivePartIndex(ticks) {
  const parts = {};
  const entry = (address) => (parts[address] ??= { written_by: null, read_by: [], preexisting: false });
  const produced = new Set();
  for (const tick of ticks) {
    for (const invocation of tick.invocations) {
      for (const binding of invocation.declared_consumes) {
        if (!binding.startsWith('px:')) continue;
        const address = bareAddress(binding);
        const part = entry(address);
        if (!produced.has(address)) part.preexisting = true;
        if (!part.read_by.includes(invocation.id)) part.read_by.push(invocation.id);
      }
      for (const address of invocation.actual_consumes) {
        const part = entry(address);
        if (!produced.has(address)) part.preexisting = true;
        if (!part.read_by.includes(invocation.id)) part.read_by.push(invocation.id);
      }
      for (const write of invocation.writes) {
        const part = entry(write.address);
        if (part.written_by === null) part.written_by = invocation.id;
        produced.add(write.address);
      }
      if (invocation.into) {
        const part = entry(invocation.into);
        if (part.written_by === null) part.written_by = invocation.id;
        produced.add(invocation.into);
      }
    }
  }
  return parts;
}

export function deriveCounters(ticks, wallMs = null) {
  let invocations = 0;
  let hits = 0;
  let measured = 0;
  let sawDuration = false;
  for (const tick of ticks) {
    for (const invocation of tick.invocations) {
      invocations += 1;
      if (invocation.hit) hits += 1;
      if (typeof invocation.duration_ms === 'number') {
        measured += invocation.duration_ms;
        sawDuration = true;
      }
    }
  }
  const wall = wallMs === null || wallMs === undefined ? (sawDuration ? round3(measured) : null) : wallMs;
  return { invocations, hits, computed: invocations - hits, wall_ms: wall };
}

function round3(value) {
  return Math.round(value * 1000) / 1000;
}

/** Tick wall time: the sum of the durations the runtime recorded, or null. */
export function tickDurationMs(tick) {
  let total = 0;
  let saw = false;
  for (const invocation of tick.invocations) {
    if (typeof invocation.duration_ms === 'number') {
      total += invocation.duration_ms;
      saw = true;
    }
  }
  return saw ? round3(total) : null;
}

function assemble({ pcr, source, ticks, wallMs = null }) {
  const record = {
    schema: SCHEMA,
    pcr,
    source,
    ticks,
    parts: derivePartIndex(ticks),
    counters: deriveCounters(ticks, wallMs)
  };
  return validate(record);
}

function uniqueId(base, seen) {
  let id = base;
  let n = 2;
  while (seen.has(id)) id = `${base}#${n++}`;
  seen.add(id);
  return id;
}

/* ------------------------------------------------------------------ */
/* pyto                                                                */
/* ------------------------------------------------------------------ */

/**
 * pyto's own materializer (pyto.materialize.run_record) already emits this
 * format, so the adapter is a validating pass-through: the viewer never
 * repairs a producer's record silently.
 */
export function fromPytoRecord(document) {
  const parsed = typeof document === 'string' ? JSON.parse(document) : document;
  return validate(parsed);
}

/* ------------------------------------------------------------------ */
/* DiscStudio (src/runtime.js)                                         */
/* ------------------------------------------------------------------ */

/**
 * Map one DiscStudio execution to a record.
 *
 * `pqlRun` is `px.pql.<name>` as invokePql wrote it (../../src/core/exec.js:60-66):
 * Ticks[].Calculations[] with `call`, `with` (name -> address), `args`,
 * `into`, `actualCall`, `inputs` (name -> resolved value) and `output` (value).
 * `receipt` is `px.receipt.<name>` (../../src/runtime.js:55-57): a flat `trace`
 * in Tick/Calculation order carrying `reused`, `material` and `revision`.
 *
 * Access is recorded per binding, not by a tracked board -- runtime.js does not
 * use trackAccess -- so `writes[].kind` is derived with exec.js:28's rule over
 * what this record can see: refinement when the invocation also reads the
 * address, replacement when an earlier invocation of the same run wrote it,
 * new-address otherwise. README.md states that limit.
 */
export function fromDiscStudioReceipt(pqlRun, receipt, { version = null, commit = null } = {}) {
  requireObject(pqlRun, 'discstudio.pqlRun');
  const name = requireString(pqlRun.PrincipleComponentRender, 'discstudio.pqlRun.PrincipleComponentRender');
  const pqlTicks = requireArray(pqlRun.Ticks, 'discstudio.pqlRun.Ticks');
  const trace = receipt ? requireArray(receipt.trace, 'discstudio.receipt.trace') : [];

  const produced = new Set();
  const seen = new Set();
  const ticks = [];
  let flat = 0;

  pqlTicks.forEach((tick, index) => {
    const invocations = requireArray(tick.Calculations, `discstudio.pqlRun.Ticks[${index}].Calculations`).map((calculation) => {
      const step = trace[flat] ?? null;
      flat += 1;
      const bindings = calculation.with ?? {};
      const inputs = {};
      const declared = [];
      const actual = [];
      for (const [key, address] of Object.entries(bindings)) {
        inputs[key] = `px:${address}`;
        declared.push(`px:${address}`);
        actual.push(address);
      }
      const into = calculation.into ?? null;
      const kind = into === null ? null : actual.includes(into) ? 'refinement' : produced.has(into) ? 'replacement' : 'new-address';
      const reused = step ? step.reused === true : false;
      const hit = deriveHit(declared, produced, reused);
      const material = step && typeof step.material === 'string' ? step.material : null;
      const revision = step && step.revision !== undefined ? step.revision : null;
      const invocation = {
        id: uniqueId(into ?? `${tick.name}:${calculation.call}`, seen),
        calculation: {
          address: calculation.actualCall ?? calculation.call ?? null,
          // runtime.js keys memo identity on { revision, inputs } (runtime.js:15),
          // never on the function body, so there is no implementation digest here.
          implementation_sha256: null,
          identity_scope: revision === null ? 'registered-address-only' : `registered-address-and-revision:${revision}`
        },
        inputs,
        args: isPlainObject(calculation.args) ? calculation.args : {},
        into,
        declared_consumes: declared,
        actual_consumes: actual,
        actual_produces: into === null ? [] : [into],
        writes: into === null ? [] : [{ address: into, kind }],
        // runtime.js records reuse and material identity, never a duration.
        duration_ms: null,
        result_sha256: material,
        hit,
        value: discStudioValue(calculation.output, material, reused)
      };
      if (into !== null) produced.add(into);
      return invocation;
    });
    ticks.push({ index, name: requireString(tick.name, `discstudio.pqlRun.Ticks[${index}].name`), invocations });
  });

  return assemble({ pcr: name, source: { runtime: 'discstudio', version, commit }, ticks });
}

function discStudioValue(output, material, reused) {
  // presentation.js:69 cardSvg returns { svg, width, height }; the record shows
  // the material, so that wrapper renders as an image rather than as JSON.
  if (isPlainObject(output) && typeof output.svg === 'string' && output.svg.trimStart().startsWith('<svg')) {
    const block = materialize(output.svg, { digest: material });
    if (block.kind !== 'omitted') block.note = `DiscStudio card wrapper { svg, width: ${output.width}, height: ${output.height} }`;
    return block;
  }
  const block = materialize(output, { digest: material });
  if (reused && block.kind !== 'omitted' && block.note === null) block.note = 'reused from the memo ring (runtime.js:17-19)';
  return block;
}

/* ------------------------------------------------------------------ */
/* ChessLab (reference/lab/chesslab-lab/contract.ts)                   */
/* ------------------------------------------------------------------ */

/**
 * Map ChessLab `Receipt`s (contract.ts:127-141, `TickTestimony = Receipt`).
 * One Tick per receipt, one invocation per entry in `frozenCalculations`;
 * access is declared at Tick granularity there, so every invocation of a Tick
 * repeats that Tick's reads and writes (README.md states this).
 * Receipt has no value field, so every value is `omitted`.
 */
export function fromChessLabReceipts(receipts, { pcr = 'chesslab', version = null, commit = null } = {}) {
  requireArray(receipts, 'chesslab.receipts');
  const produced = new Set();
  const seen = new Set();
  const ticks = receipts.map((receipt, index) => {
    const path = `chesslab.receipts[${index}]`;
    requireObject(receipt, path);
    const opId = requireString(receipt.opId, `${path}.opId`);
    const declared = requireStringArray(receipt.declaredConsumes ?? [], `${path}.declaredConsumes`).map((slot) => `px:${slot}`);
    const actual = requireStringArray(receipt.actualConsumes ?? [], `${path}.actualConsumes`);
    const produces = requireStringArray(receipt.declaredProduces ?? [], `${path}.declaredProduces`);
    const actualProduces = requireStringArray(receipt.actualProduces ?? [], `${path}.actualProduces`);
    const writes = requireArray(receipt.writes ?? [], `${path}.writes`).map((write, i) => ({
      address: requireString(write.address, `${path}.writes[${i}].address`),
      kind: write.kind === undefined || write.kind === null ? null : requireEnum(write.kind, WRITE_KINDS, `${path}.writes[${i}].kind`)
    }));
    const frozen = requireArray(receipt.frozenCalculations ?? [], `${path}.frozenCalculations`);
    const bound = frozen.length ? frozen : [null];
    const hit = deriveHit(declared, produced);
    const inputs = Object.fromEntries(declared.map((binding) => [bareAddress(binding), binding]));
    const invocations = bound.map((calculation, i) => ({
      id: uniqueId(bound.length === 1 ? opId : `${opId}#${i}`, seen),
      calculation: {
        address: calculation ? requireString(calculation.address, `${path}.frozenCalculations[${i}].address`) : null,
        implementation_sha256: calculation && typeof calculation.implementationHash === 'string' ? calculation.implementationHash : null,
        identity_scope: (calculation && calculation.identityScope) || 'runtime-function-body'
      },
      inputs,
      args: {},
      into: produces[0] ?? null,
      declared_consumes: declared,
      actual_consumes: actual,
      actual_produces: actualProduces,
      writes,
      duration_ms: typeof receipt.durationMs === 'number' ? receipt.durationMs : null,
      result_sha256: null,
      hit,
      value: { kind: 'omitted', data: null, note: 'ChessLab receipts retain no Part values (contract.ts:127-141 has no value field); artifacts are content-addressed elsewhere' }
    }));
    for (const address of [...produces, ...actualProduces, ...writes.map((w) => w.address)]) produced.add(address);
    return { index, name: opId, invocations };
  });
  return assemble({ pcr, source: { runtime: 'chesslab', version, commit }, ticks });
}

/* ------------------------------------------------------------------ */
/* Wumpus (reference/lab/wumpus-core/execute.js)                       */
/* ------------------------------------------------------------------ */

/**
 * Map `executeTick` records (execute.js:19-37). One Tick per record; one
 * invocation per entry in `calculations` (execute.js:29-35, each with its own
 * input args and output value), or one invocation carrying `result` when the
 * Tick called no registered Calculation. Access is recorded per Tick, so an
 * invocation repeats its Tick's reads and writes.
 */
export function fromWumpusRecords(records, { pcr = 'wumpus', version = null, commit = null } = {}) {
  requireArray(records, 'wumpus.records');
  const produced = new Set();
  const seen = new Set();
  const ticks = records.map((record, index) => {
    const path = `wumpus.records[${index}]`;
    requireObject(record, path);
    const id = requireString(record.id, `${path}.id`);
    const invocationId = typeof record.invocationId === 'string' ? record.invocationId : id;
    const declared = requireStringArray(record.consumes ?? [], `${path}.consumes`).map((slot) => `px:${slot}`);
    const actual = requireStringArray(record.actualConsumes ?? [], `${path}.actualConsumes`);
    const actualProduces = requireStringArray(record.actualProduces ?? [], `${path}.actualProduces`);
    const produces = requireStringArray(record.produces ?? [], `${path}.produces`);
    const writes = requireArray(record.writes ?? [], `${path}.writes`).map((write, i) => ({
      address: requireString(write.address, `${path}.writes[${i}].address`),
      kind: write.kind === undefined || write.kind === null ? null : requireEnum(write.kind, WRITE_KINDS, `${path}.writes[${i}].kind`)
    }));
    const calculations = requireArray(record.calculations ?? [], `${path}.calculations`);
    const hit = deriveHit(declared, produced);
    const inputs = Object.fromEntries(declared.map((binding) => [bareAddress(binding), binding]));
    const duration = typeof record.durationMs === 'number' ? record.durationMs : null;
    const bound = calculations.length ? calculations : [null];
    const invocations = bound.map((calculation, i) => ({
      id: uniqueId(bound.length === 1 ? invocationId : `${invocationId}#${i}`, seen),
      calculation: {
        address: calculation ? requireString(calculation.address, `${path}.calculations[${i}].address`) : null,
        // execute.js:33-34: the address is the identity; no body is hashed.
        implementation_sha256: null,
        identity_scope: (calculation && calculation.identityScope) || 'registered-address-only'
      },
      inputs,
      args: calculation && isPlainObject(calculation.input) ? calculation.input : {},
      into: produces[0] ?? actualProduces[0] ?? null,
      declared_consumes: declared,
      actual_consumes: actual,
      actual_produces: actualProduces,
      writes,
      duration_ms: duration,
      result_sha256: null,
      hit,
      value: materialize(calculation ? calculation.output : record.result)
    }));
    for (const address of [...produces, ...actualProduces, ...writes.map((w) => w.address)]) produced.add(address);
    return { index, name: id, invocations };
  });
  return assemble({ pcr, source: { runtime: 'wumpus', version, commit }, ticks });
}
