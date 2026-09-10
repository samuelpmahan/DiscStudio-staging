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

/** RECORD.md, "Placement and budget": the optional fields, and their key sets. */
export const PLACEMENT_KEYS = ['worker', 'started_ms'];
export const BUDGET_KEYS = ['limit_ms', 'stopped_after_tick', 'completed'];

/** RECORD.md:109-110: a `png-data-url` value's data is exactly this shape. */
export const PNG_DATA_URL_PREFIX = 'data:image/png;base64,';

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

/**
 * RECORD.md: `inputs` keeps the testimony spelling `px:<address>`, `fn:<id>`, or
 * `fn:<id>#<address>` when the producer published several Parts. Both halves of
 * the qualified form must be non-empty, so a reader always has a producer to
 * resolve and an address to resolve it to.
 */
function requireBindingSpelling(value, path) {
  requireString(value, path);
  if (!value.startsWith('px:') && !value.startsWith('fn:')) {
    fail(path, `expected a testimony binding spelled "px:<address>", "fn:<id>" or "fn:<id>#<address>", got ${show(value)}`);
  }
  if (value.startsWith('fn:') && value.includes('#')) {
    const body = value.slice(3);
    const cut = body.lastIndexOf('#');
    if (cut === 0 || cut === body.length - 1) {
      fail(path, `expected a produce-qualified result binding "fn:<id>#<address>", got ${show(value)}`);
    }
  }
  return value;
}

/**
 * RECORD.md: `into` is one address, an array of addresses, or null. The array is
 * the multi-produce form -- one invocation publishing several Parts from one
 * pass. An empty array is refused (an invocation that produces nothing writes
 * null, like every other absent field) and so is a repeated address.
 */
function requireInto(value, path) {
  if (value === null || typeof value === 'string') return requireNullableString(value, path);
  if (!Array.isArray(value)) fail(path, `expected an address, an array of addresses, or null, got ${show(value)}`);
  if (value.length === 0) fail(path, 'expected at least one address; an invocation that produces nothing writes null');
  const seen = new Set();
  value.forEach((entry, index) => {
    requireString(entry, `${path}[${index}]`);
    if (seen.has(entry)) fail(`${path}[${index}]`, `duplicate produce address ${JSON.stringify(entry)}; one invocation publishes each address once`);
    seen.add(entry);
  });
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
    // RECORD.md:109-110 states the shape; tick-viewer.js:118 puts this string
    // straight into an <img src>, so an unchecked kind is an outbound request
    // the record chose. Enforce the clause here rather than trusting a producer.
    if (kind === 'png-data-url' && !value.data.startsWith(PNG_DATA_URL_PREFIX)) {
      fail(`${path}.data`, `expected a string beginning ${JSON.stringify(PNG_DATA_URL_PREFIX)} for kind "png-data-url", got ${show(value.data)}`);
    }
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
  requireInto(invocation.into, `${path}.into`);

  // RECORD.md's declared_consumes rule is strict, so it is checked and not
  // assumed: exactly the `px:` bindings of `inputs`, in binding order. An `fn:`
  // entry or an address `inputs` does not carry would add a read edge no
  // binding declares, because derivePartIndex below unions the two fields.
  requireArray(invocation.declared_consumes, `${path}.declared_consumes`);
  const boundValues = new Set(Object.values(inputs));
  invocation.declared_consumes.forEach((entry, i) => {
    const where = `${path}.declared_consumes[${i}]`;
    requireBindingSpelling(entry, where);
    if (!entry.startsWith('px:')) {
      fail(where, `declared_consumes carries Part bindings only, spelled "px:<address>", got ${show(entry)}`);
    }
    if (!boundValues.has(entry)) {
      fail(where, `declared_consumes is a subset of inputs.values(), which does not carry ${show(entry)}`);
    }
  });
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
  validatePlacement(invocation, path);
  return invocation;
}

/**
 * RECORD.md, "Placement and budget": `placement` is optional and null for a
 * serial run -- a Tick that ran on one thread has no placement to report.
 * `worker` is a 0-based index inside its Tick, `started_ms` the offset from the
 * moment that Tick began, so a reader draws the overlap without a wall clock.
 */
function validatePlacement(invocation, path) {
  if (!('placement' in invocation) || invocation.placement === null) return null;
  const where = `${path}.placement`;
  const placement = requireObject(invocation.placement, where);
  const extra = Object.keys(placement).filter((key) => !PLACEMENT_KEYS.includes(key));
  if (extra.length > 0) fail(where, `unknown field(s) ${extra.sort().join(', ')} not in RECORD.md`);
  if (!Number.isInteger(placement.worker) || placement.worker < 0) {
    fail(`${where}.worker`, `expected a non-negative integer, got ${show(placement.worker)}`);
  }
  if (typeof placement.started_ms !== 'number' || !Number.isFinite(placement.started_ms)) {
    fail(`${where}.started_ms`, `expected a finite number, got ${show(placement.started_ms)}`);
  }
  return placement;
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

  // Placement and budget: optional, so absent is a serial unbudgeted run and not
  // a violation; present, they are held to the same rules as everything else.
  ticks.forEach((tick, index) => {
    if ('latency_ms' in tick) requireNullableNumber(tick.latency_ms, `ticks[${index}].latency_ms`);
  });
  if ('parallel' in record) requireBoolean(record.parallel, 'parallel');
  if ('budget' in record) {
    const budget = requireObject(record.budget, 'budget');
    const missing = BUDGET_KEYS.filter((key) => !(key in budget));
    if (missing.length > 0) fail('budget', `missing required field(s) ${missing.join(', ')}; RECORD.md: missing fields are null, never absent`);
    const extra = Object.keys(budget).filter((key) => !BUDGET_KEYS.includes(key));
    if (extra.length > 0) fail('budget', `unknown field(s) ${extra.sort().join(', ')} not in RECORD.md`);
    requireNullableNumber(budget.limit_ms, 'budget.limit_ms');
    requireNullableString(budget.stopped_after_tick, 'budget.stopped_after_tick');
    requireBoolean(budget.completed, 'budget.completed');
    if (budget.completed && budget.stopped_after_tick !== null) {
      fail('budget.stopped_after_tick', `a completed run stopped after no Tick; stopped_after_tick names the last Tick a budget cut the run after, got ${show(budget.stopped_after_tick)}`);
    }
    const names = new Set(ticks.map((tick) => tick.name));
    if (budget.stopped_after_tick !== null && !names.has(budget.stopped_after_tick)) {
      fail('budget.stopped_after_tick', `names no Tick in this record (${[...names].sort().join(', ') || 'none'}), got ${show(budget.stopped_after_tick)}`);
    }
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

/** The addresses an invocation's `into` names: none, one, or several. */
export function produceAddresses(into) {
  if (into === null || into === undefined) return [];
  return typeof into === 'string' ? [into] : [...into];
}

/**
 * The Part addresses one testimony binding reads (RECORD.md, Field rules).
 *
 * `px:<address>` is that address. `fn:<id>` is the whole result of that
 * invocation, which is the one Part it published; `fn:<id>#<address>` names one
 * produce of an invocation that published several. A known id wins over the `#`
 * split, so an invocation id that itself carries a `#` still resolves as the bare
 * reference it is. `producedBy` maps an invocation id to the addresses it
 * published.
 */
export function parseBinding(binding, producedBy) {
  if (typeof binding !== 'string') return [];
  if (binding.startsWith('px:')) return [binding.slice(3)];
  if (!binding.startsWith('fn:')) return [];
  const body = binding.slice(3);
  if (producedBy.has(body)) return [...producedBy.get(body)];
  const cut = body.lastIndexOf('#');
  if (cut > 0 && cut < body.length - 1) {
    const writer = body.slice(0, cut);
    const address = body.slice(cut + 1);
    if (producedBy.has(writer) && producedBy.get(writer).includes(address)) return [address];
  }
  return [];
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
    // Tested on `raw`, not on the trimmed `head`: the classification has to
    // agree with validateValue, which reads the bytes that land in `data`.
    else if (raw.startsWith(PNG_DATA_URL_PREFIX)) kind = 'png-data-url';
    return capped({ kind, data: raw, note }, utf8Length(raw), digest);
  }
  // Serializability is decided on the whole value, before anything is cut, the
  // way ../../src/pyto/materialize.py:229-234 decides it: a cycle or an
  // unserializable entry past the cap must still reach `omitted`, not be sliced
  // out of sight first.
  try {
    if (JSON.stringify(raw) === undefined) {
      return { kind: 'omitted', data: null, note: 'value is not JSON serializable' };
    }
  } catch (error) {
    return { kind: 'omitted', data: null, note: `value is not JSON serializable: ${error.message}` };
  }
  const lengths = [];
  const data = truncateArrays(raw, MAX_ARRAY_ENTRIES, lengths);
  const arrayNote = lengths.length
    ? `${lengths.length} array(s) truncated to the first ${MAX_ARRAY_ENTRIES} entries; `
      + `original lengths: [${lengths.slice().sort((a, b) => b - a).join(', ')}]`
    : note;
  return capped({ kind: 'json', data, note: arrayNote ?? null }, utf8Length(JSON.stringify(data)), digest);
}

/**
 * Copy `value` with every array longer than `cap` cut to its first `cap`
 * entries, appending each original length to `lengths`.
 *
 * Recursive, and deliberately the same traversal as
 * ../../src/pyto/materialize.py:151-164 `_truncate_arrays`: array first (cut,
 * record the length, then recurse into the surviving entries), then dict in key
 * order, then everything else untouched. RECORD.md states the cap without
 * qualifying it by depth ("arrays longer than 200 entries carry the first 200
 * and a note with the full length", RECORD.md:113 as it now stands), so
 * `{"rows": [0..999]}` has to be a 200-row record in both runtimes; truncating only a top-level array made the browser keep all
 * 1000 with note null.
 *
 * `isDictLike` stands in for Python's `isinstance(value, dict)`: a Date or
 * any other object carrying `toJSON` is left whole rather than rebuilt as an
 * empty plain object, so JSON.stringify still sees what it would have seen.
 */
function truncateArrays(value, cap, lengths) {
  if (Array.isArray(value)) {
    let items = value;
    if (items.length > cap) {
      lengths.push(items.length);
      items = items.slice(0, cap);
    }
    return items.map((item) => truncateArrays(item, cap, lengths));
  }
  if (isDictLike(value)) {
    const copy = {};
    for (const key of Object.keys(value)) copy[key] = truncateArrays(value[key], cap, lengths);
    return copy;
  }
  return value;
}

function isDictLike(value) {
  if (value === null || typeof value !== 'object') return false;
  const proto = Object.getPrototypeOf(value);
  return proto === Object.prototype || proto === null;
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
  // A Part address is record data, so it can be `__proto__` or `constructor`.
  // On a `{}` map those names reach Object.prototype instead of an own slot:
  // the index would answer for addresses no run wrote, and mutate the page's
  // prototype chain. A null-prototype map has no inherited names to hit, and
  // hasOwnProperty decides existence rather than truthiness.
  const parts = Object.create(null);
  const entry = (address) => {
    if (!Object.prototype.hasOwnProperty.call(parts, address)) {
      Object.defineProperty(parts, address, {
        value: { written_by: null, read_by: [], preexisting: false },
        enumerable: true, writable: true, configurable: true
      });
    }
    return parts[address];
  };
  // Spread, not assignment, to hand back the shape JSON.parse gives a consumer
  // reading the same index off disk: a plain object carrying `__proto__` as an
  // own data property. `{ ...map }` copies with CreateDataProperty, so the
  // hostile name stays a row here too; `Object.assign` would not.
  const plain = () => ({ ...parts });
  const produced = new Set();
  // A `fn:<id>` binding is a read of the Part that invocation wrote: pcr.py:112-116
  // rewrites a Part binding into the producing invocation's ResultRef, and the
  // value is the same one published at `into`. Counting it keeps the index
  // useful ("who consumes scratch.ablation.model.all") and matches what
  // pyto.materialize emits. It never makes a hit -- only a `px:` binding does.
  const intoById = new Map();
  for (const tick of ticks) {
    for (const invocation of tick.invocations) {
      // `inputs` is the complete binding map and is sufficient on its own:
      // `declared_consumes` is a validated subset of it (validateInvocation
      // above), so unioning the two adds nothing to a conformant record. The
      // union is kept as a defence for a record that reached this reader
      // without passing validate -- a duplicated edge, never a lost one.
      const bindings = [...Object.values(invocation.inputs), ...invocation.declared_consumes];
      for (const binding of bindings) {
        for (const address of parseBinding(binding, intoById)) {
          if (!address) continue;
          const part = entry(address);
          if (!binding.startsWith('fn:') && !produced.has(address)) part.preexisting = true;
          if (!part.read_by.includes(invocation.id)) part.read_by.push(invocation.id);
        }
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
      const produces = produceAddresses(invocation.into);
      if (produces.length) {
        for (const address of produces) {
          const part = entry(address);
          if (part.written_by === null) part.written_by = invocation.id;
          produced.add(address);
        }
        intoById.set(invocation.id, produces);
      }
    }
  }
  return plain();
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

/**
 * One Tick's wall time: `latency_ms` when the record carries it, else the sum of
 * its durations -- the same arithmetic a serial run does, and null when any one
 * duration is null (RECORD.md, "Placement and budget").
 *
 * Qualified `FromRecord` because `tick-viewer.js` exports its own `tickLatencyMs`
 * (task 40) and `embed.mjs` concatenates both files into one module, where two
 * top-level bindings of one name is a SyntaxError. The two are not the same
 * function: with `latency_ms` present they agree, and with it absent this one
 * sums the durations (the serial reading RECORD.md specifies for the fallback)
 * while the viewer's takes the longest branch of a parallel Tick and the sum of a
 * chain (the critical path it draws).
 * See `{?} TwoLatencyFallbacks` in experiments/tasks/39/packet.md.
 */
export function tickLatencyMsFromRecord(tick) {
  if (typeof tick.latency_ms === 'number') return tick.latency_ms;
  if (tick.invocations.length === 0) return null;
  let total = 0;
  for (const invocation of tick.invocations) {
    if (typeof invocation.duration_ms !== 'number') return null;
    total += invocation.duration_ms;
  }
  return round3(total);
}

/** This invocation's placement, or null -- absent and null read the same. */
export function invocationPlacement(invocation) {
  return invocation.placement ?? null;
}

/**
 * How the run was scheduled, with the defaults an absent field means: a record
 * carrying neither `parallel` nor `budget` is a serial, unbudgeted run that ran
 * to the end.
 */
export function runSchedule(record) {
  const budget = record.budget ?? {};
  return {
    parallel: record.parallel === true,
    budget: {
      limit_ms: budget.limit_ms ?? null,
      stopped_after_tick: budget.stopped_after_tick ?? null,
      completed: budget.completed ?? true
    }
  };
}

function assemble({ pcr, source, ticks, wallMs = null, schedule = null }) {
  const record = {
    schema: SCHEMA,
    pcr,
    source,
    ticks,
    parts: derivePartIndex(ticks),
    counters: deriveCounters(ticks, wallMs)
  };
  // RECORD.md, "Placement and budget": the four fields go in together and only
  // when the run was parallel, was given a budget, or was stopped by one, and
  // they go in last, in the order pyto.materialize.run_record writes them.
  if (schedule) {
    record.parallel = schedule.parallel === true;
    record.budget = {
      limit_ms: schedule.budget?.limit_ms ?? null,
      stopped_after_tick: schedule.budget?.stopped_after_tick ?? null,
      completed: schedule.budget?.completed !== false
    };
  }
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
  // The schedule exec.js reported for this run (src/core/exec.js `schedule`),
  // filed on the receipt by runtime.js and on the composition Part by the run
  // itself. Absent on both is a serial, unbudgeted run and stays absent here.
  const scheduled = (receipt && receipt.schedule) || pqlRun.schedule || null;
  const scheduledTick = (index) => (scheduled ? scheduled.ticks?.[index] ?? null : null);

  const produced = new Set();
  const seen = new Set();
  const ticks = [];
  let flat = 0;

  pqlTicks.forEach((tick, index) => {
    const invocations = requireArray(tick.Calculations, `discstudio.pqlRun.Ticks[${index}].Calculations`).map((calculation, order) => {
      const step = trace[flat] ?? null;
      flat += 1;
      const bindings = calculation.with ?? {};
      // Null-prototype for the same reason as derivePartIndex: a binding named
      // `__proto__` on a `{}` would set the prototype and drop the binding.
      const inputs = Object.create(null);   // filled below, spread into a plain object
      const declared = [];
      const actual = [];
      for (const [key, address] of Object.entries(bindings)) {
        inputs[key] = `px:${address}`;
        declared.push(`px:${address}`);
        actual.push(address);
      }
      // `into` is one address or, since task 42, a list of them: one pass, several
      // Parts, one invocation listing all of them ({?} RecordAdapterHasOneIntoPerInvocation).
      const into = calculation.into ?? null;
      const addresses = into === null ? [] : Array.isArray(into) ? [...into] : [into];
      const writes = addresses.map((address) => ({
        address,
        kind: actual.includes(address) ? 'refinement' : produced.has(address) ? 'replacement' : 'new-address'
      }));
      const reused = step ? step.reused === true : false;
      const hit = deriveHit(declared, produced, reused);
      const material = step && typeof step.material === 'string' ? step.material : null;
      const revision = step && step.revision !== undefined ? step.revision : null;
      const invocation = {
        id: uniqueId(addresses[0] ?? `${tick.name}:${calculation.call}`, seen),
        calculation: {
          address: calculation.actualCall ?? calculation.call ?? null,
          // runtime.js keys memo identity on { revision, inputs } (runtime.js:15),
          // never on the function body, so there is no implementation digest here.
          implementation_sha256: null,
          identity_scope: revision === null ? 'registered-address-only' : `registered-address-and-revision:${revision}`
        },
        inputs: { ...inputs },
        args: isPlainObject(calculation.args) ? calculation.args : {},
        into,
        declared_consumes: declared,
        actual_consumes: actual,
        actual_produces: addresses,
        writes,
        // runtime.js records reuse and material identity, never a duration.
        duration_ms: null,
        result_sha256: material,
        hit,
        value: discStudioValue(calculation.output, material, reused)
      };
      // Placement is written for every invocation of a run that reports a
      // schedule and for no invocation of one that does not: a serial Tick has
      // none to report and says so with null.
      if (scheduled) invocation.placement = scheduledTick(index)?.placements?.[order] ?? null;
      for (const address of addresses) produced.add(address);
      return invocation;
    });
    const entry = { index, name: requireString(tick.name, `discstudio.pqlRun.Ticks[${index}].name`), invocations };
    if (scheduled) entry.latency_ms = scheduledTick(index)?.latency_ms ?? null;
    ticks.push(entry);
  });

  return assemble({ pcr: name, source: { runtime: 'discstudio', version, commit }, ticks, schedule: scheduled });
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
