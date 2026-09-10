/**
 * Kibana for Ticks: render one pyto-run-record@1 document as one section per
 * Tick, one row per invocation, with the Part value shown as material.
 *
 * Dependency-free ES module. Every node is built with createElement and
 * textContent -- no innerHTML with record data, ever -- and an `svg` value is
 * rendered through an <img src="data:image/svg+xml;base64,...">, never inlined
 * as markup, so a value that contains <script> cannot become a script element.
 *
 * The DOM is reached only through the `doc` argument, so the render functions
 * run under a minimal document shim in `node --test` with no jsdom.
 */

import { validate, bareAddress, produceAddresses, parseBinding, PNG_DATA_URL_PREFIX, fromPytoRecord, fromDiscStudioReceipt, fromChessLabReceipts, fromWumpusRecords, deriveCounters, derivePartIndex } from './adapters.js';

/* ------------------------------------------------------------------ */
/* small DOM helpers (doc is always explicit)                          */
/* ------------------------------------------------------------------ */

export function el(doc, tag, { className = null, text = null, attrs = null } = {}, children = []) {
  const node = doc.createElement(tag);
  if (className !== null) node.className = className;
  if (text !== null) node.textContent = String(text);
  if (attrs) for (const [name, value] of Object.entries(attrs)) node.setAttribute(name, String(value));
  for (const child of children) if (child) node.appendChild(child);
  return node;
}

// Named apart from adapters.js's own encoder: embed.mjs concatenates both
// modules into one script, where two top-level `encoder` bindings would clash.
const base64Encoder = new TextEncoder();

/** UTF-8 safe base64 for data: URLs; btoa alone throws above U+00FF. */
export function toBase64(text) {
  const bytes = base64Encoder.encode(text);
  let binary = '';
  for (let i = 0; i < bytes.length; i += 0x8000) binary += String.fromCharCode.apply(null, bytes.subarray(i, i + 0x8000));
  return btoa(binary);
}

export function svgDataUrl(svgText) {
  return `data:image/svg+xml;base64,${toBase64(svgText)}`;
}

function shortHash(hex, keep = 12) {
  if (typeof hex !== 'string' || !hex.length) return null;
  return hex.length <= keep ? hex : `${hex.slice(0, keep)}…`;
}

function ms(value) {
  if (typeof value !== 'number') return '—';
  return `${value.toFixed(value < 10 ? 3 : 1)} ms`;
}

/* ------------------------------------------------------------------ */
/* parallel branches: work, latency, placement, budget                 */
/* ------------------------------------------------------------------ */

/**
 * The contract this section renders when a record carries it, and never
 * requires (a record without any of it renders exactly as it did before):
 * per invocation `placement: {worker, started_ms} | null`, per tick
 * `latency_ms: number | null`, and at run level `parallel: bool` and
 * `budget: {limit_ms, stopped_after_tick, completed}`.
 */

/** Every Part address one invocation publishes: `into` (one or several) and actual_produces. */
export function invocationProduces(invocation) {
  const produced = new Set(produceAddresses(invocation.into));
  for (const address of invocation.actual_produces || []) produced.add(address);
  return produced;
}

/**
 * Every Part address one invocation reads, resolved the way
 * experiments/tick-laws/tick_laws.py resolves it: `px:` bindings are store
 * reads, `fn:` bindings are result reads resolved through the producer's
 * `into` (one address or a list), unioned with actual_consumes.
 */
export function invocationReads(invocation, producedBy) {
  const reads = new Set(invocation.actual_consumes || []);
  for (const binding of Object.values(invocation.inputs || {})) {
    for (const address of parseBinding(binding, producedBy)) reads.add(address);
  }
  return reads;
}

/**
 * A Tick is parallel when it holds more than one Calculation and no Calculation
 * reads what a sibling produced: its branches can run at once. Inside a Tick the
 * Calculations are a sequence in declared order, so a Tick where one reads a
 * sibling's produce is a chain instead (`isChainTick`): it runs in order, and the
 * Tick boundary is where that sequence becomes inspectable. The classification is
 * experiments/tick-laws/tick_laws.py's (the owner, 2026-09-10: "'Calculations
 * inside a Tick must be independent' was added as a rule, while your existing
 * ChainSpot program deliberately chains dependent Calculations inside a Tick.
 * Your definition was the moment that sequence becomes inspectable"). Siblings
 * are the only producers that matter here, so the resolver map is built from
 * this Tick alone: an `fn:` reference to an earlier Tick resolves to nothing and
 * is not a branch dependency.
 */
export function isParallelTick(tick) {
  const invocations = tick.invocations || [];
  if (invocations.length < 2) return false;
  const produces = new Map();
  const producedBy = new Map();
  for (const invocation of invocations) {
    const addresses = invocationProduces(invocation);
    produces.set(invocation.id, addresses);
    producedBy.set(invocation.id, [...addresses]);
  }
  for (const invocation of invocations) {
    const reads = invocationReads(invocation, producedBy);
    for (const sibling of invocations) {
      if (sibling.id === invocation.id) continue;
      for (const address of produces.get(sibling.id)) if (reads.has(address)) return false;
    }
  }
  return true;
}

/**
 * A Tick is a chain when it holds more than one Calculation and one of them
 * reads what a sibling produced: the Calculations run in declared order, one
 * after another, and the Tick takes the sum of their durations. The page draws
 * a chain as the sequence it is, one card under the other, and says so.
 */
export function isChainTick(tick) {
  return (tick.invocations || []).length >= 2 && !isParallelTick(tick);
}

/**
 * A Tick's work: the sum of its branches' durations, or null when the runtime
 * recorded none. Unrounded, unlike adapters.js `tickDurationMs`, so that adding
 * Ticks up gives the run total tick_laws.py reports and not a rounded-per-Tick one.
 */
export function tickWorkMs(tick) {
  let total = 0;
  let saw = false;
  for (const invocation of tick.invocations) {
    if (typeof invocation.duration_ms === 'number' && Number.isFinite(invocation.duration_ms)) {
      total += invocation.duration_ms;
      saw = true;
    }
  }
  return saw ? total : null;
}

/**
 * A Tick's latency: `latency_ms` when the record carries it, else the longest
 * branch of a parallel Tick -- the time the Tick takes when its branches run at
 * once -- or the sum through a chain, which runs in order. Either way it is what
 * tick_laws.py reports and what the run's critical path adds up.
 */
export function tickLatencyMs(tick) {
  if (typeof tick.latency_ms === 'number' && Number.isFinite(tick.latency_ms)) return tick.latency_ms;
  if (isChainTick(tick)) return tickWorkMs(tick);
  let longest = null;
  for (const invocation of tick.invocations) {
    if (typeof invocation.duration_ms === 'number' && Number.isFinite(invocation.duration_ms)) {
      longest = longest === null ? invocation.duration_ms : Math.max(longest, invocation.duration_ms);
    }
  }
  return longest;
}

/**
 * Add one number per Tick over the whole run, rounding only at the end -- the
 * run total then agrees to the microsecond with the one tick_laws.py prints,
 * instead of carrying a rounding error per Tick. A Tick with no Calculations
 * costs nothing; a Tick whose number is unknown makes the run's unknown.
 */
function sumOverTicks(record, per) {
  let total = 0;
  for (const tick of record.ticks) {
    if (!tick.invocations.length) continue;
    const value = per(tick);
    if (value === null) return null;
    total += value;
  }
  return scheduleRound3(total);
}

/** The run's total work: every branch's duration added up. */
export function runWorkMs(record) {
  return sumOverTicks(record, tickWorkMs);
}

/** The run's critical path: the Tick latencies added up, Ticks being in series. */
export function runCriticalPathMs(record) {
  return sumOverTicks(record, tickLatencyMs);
}

/** `placement.worker` when the record carries it, else null. */
export function placementWorker(invocation) {
  const placement = invocation.placement;
  if (!placement || typeof placement !== 'object') return null;
  return typeof placement.worker === 'number' && Number.isFinite(placement.worker) ? placement.worker : null;
}

/* ------------------------------------------------------------------ */
/* filter: PQL-like, address substring or prefix                       */
/* ------------------------------------------------------------------ */

/** Every address-ish string an invocation can be found by. */
export function searchTerms(invocation, tickName = '') {
  const terms = [invocation.id, tickName];
  if (invocation.calculation && invocation.calculation.address) terms.push(invocation.calculation.address);
  if (invocation.into) terms.push(invocation.into);
  for (const binding of [...Object.values(invocation.inputs), ...invocation.declared_consumes]) terms.push(bareAddress(binding), binding);
  for (const address of invocation.actual_consumes) terms.push(address);
  for (const address of invocation.actual_produces) terms.push(address);
  for (const write of invocation.writes) terms.push(write.address);
  return terms.filter((term) => typeof term === 'string' && term.length);
}

/**
 * PQL's own two selectors (pyto/src/pyto/pql.py:26-45): an exact address, and
 * a prefix written the way PQL.prefix describes itself, `scratch.ablation.*`.
 * Anything else is an ordinary case-insensitive substring.
 */
export function matchesFilter(invocation, query, tickName = '') {
  const trimmed = (query || '').trim();
  if (!trimmed) return true;
  const terms = searchTerms(invocation, tickName);
  if (trimmed.endsWith('*')) {
    const prefix = trimmed.slice(0, -1).toLowerCase();
    return terms.some((term) => term.toLowerCase().startsWith(prefix));
  }
  const needle = trimmed.toLowerCase();
  return terms.some((term) => term.toLowerCase().includes(needle));
}

/** Ticks with their non-matching invocations removed; empty Ticks dropped. */
export function filterTicks(ticks, query) {
  const kept = [];
  for (const tick of ticks) {
    const invocations = tick.invocations.filter((invocation) => matchesFilter(invocation, query, tick.name));
    if (invocations.length) kept.push({ ...tick, invocations });
  }
  return kept;
}

/* ------------------------------------------------------------------ */
/* value as material                                                   */
/* ------------------------------------------------------------------ */

export function renderValue(doc, value) {
  const box = el(doc, 'div', { className: 'value' });
  if (value.kind === 'omitted') {
    box.appendChild(el(doc, 'p', { className: 'note omitted', text: value.note || 'value omitted' }));
    return box;
  }
  if (value.kind === 'svg') {
    // Never inline the markup: the value becomes the src of an <img>, where a
    // <script> inside it is inert and no script element is created.
    const figure = el(doc, 'figure', { className: 'material' }, [
      el(doc, 'img', { className: 'svg', attrs: { src: svgDataUrl(value.data), alt: 'SVG Part value', loading: 'lazy' } }),
      el(doc, 'figcaption', { text: `svg · ${value.data.length} chars` })
    ]);
    box.appendChild(figure);
  } else if (value.kind === 'png-data-url') {
    // adapters.js validateValue already refuses any other shape; re-check at the
    // render site so a record that reached the DOM by another path still cannot
    // turn an <img src> into an outbound request from a page with no network.
    if (typeof value.data !== 'string' || !value.data.startsWith(PNG_DATA_URL_PREFIX)) {
      box.appendChild(el(doc, 'p', {
        className: 'note omitted',
        text: `value not rendered: kind "png-data-url" must be a ${PNG_DATA_URL_PREFIX}... string (RECORD.md:109-110)`
      }));
    } else {
      box.appendChild(el(doc, 'figure', { className: 'material' }, [
        el(doc, 'img', { className: 'png', attrs: { src: value.data, alt: 'PNG Part value', loading: 'lazy' } }),
        el(doc, 'figcaption', { text: `png-data-url · ${value.data.length} chars` })
      ]));
    }
  } else if (value.kind === 'text') {
    box.appendChild(el(doc, 'pre', { className: 'text', text: value.data }));
  } else {
    const details = el(doc, 'details', { className: 'json' });
    const text = JSON.stringify(value.data, null, 2);
    const lines = text.split('\n').length;
    details.appendChild(el(doc, 'summary', { text: `json · ${lines} line${lines === 1 ? '' : 's'}` }));
    details.appendChild(el(doc, 'pre', { text }));
    box.appendChild(details);
  }
  if (value.note) box.appendChild(el(doc, 'p', { className: 'note', text: value.note }));
  return box;
}

/* ------------------------------------------------------------------ */
/* reads, writes, one invocation                                       */
/* ------------------------------------------------------------------ */

export function renderReads(doc, invocation) {
  const declaredBare = invocation.declared_consumes.map(bareAddress);
  const actual = invocation.actual_consumes;
  const addresses = [];
  for (const address of [...declaredBare, ...actual]) if (!addresses.includes(address)) addresses.push(address);

  const wrap = el(doc, 'div', { className: 'reads' });
  if (!addresses.length && !Object.keys(invocation.inputs).length) {
    wrap.appendChild(el(doc, 'p', { className: 'none', text: 'reads nothing off the store' }));
    return wrap;
  }
  const table = el(doc, 'table', { className: 'reads-table' });
  const head = el(doc, 'tr', {}, [
    el(doc, 'th', { text: 'binding' }), el(doc, 'th', { text: 'declared' }),
    el(doc, 'th', { text: 'actual' }), el(doc, 'th', { text: '' })
  ]);
  table.appendChild(el(doc, 'thead', {}, [head]));
  const body = el(doc, 'tbody');
  const nameFor = (address) => {
    for (const [name, binding] of Object.entries(invocation.inputs)) if (bareAddress(binding) === address) return name;
    return '';
  };
  for (const address of addresses) {
    const declared = declaredBare.includes(address);
    const observed = actual.includes(address);
    const diverges = declared !== observed;
    const binding = Object.entries(invocation.inputs).find(([, value]) => bareAddress(value) === address);
    const spelling = binding ? binding[1] : (declared ? invocation.declared_consumes[declaredBare.indexOf(address)] : `px:${address}`);
    const row = el(doc, 'tr', { className: diverges ? 'diverges' : '' }, [
      el(doc, 'td', { className: 'bindname', text: nameFor(address) || '—' }),
      el(doc, 'td', { className: 'addr', text: declared ? spelling : '—' }),
      el(doc, 'td', { className: 'addr', text: observed ? address : '—' }),
      el(doc, 'td', { className: 'flag', text: diverges ? (declared ? 'declared, never read' : 'read, never declared') : '' })
    ]);
    body.appendChild(row);
  }
  // fn: bindings resolve to an earlier invocation's result, never to the store.
  for (const [name, spelling] of Object.entries(invocation.inputs)) {
    if (!spelling.startsWith('fn:')) continue;
    body.appendChild(el(doc, 'tr', { className: 'resultref' }, [
      el(doc, 'td', { className: 'bindname', text: name }),
      el(doc, 'td', { className: 'addr', text: spelling }),
      el(doc, 'td', { className: 'addr', text: 'result of ' + bareAddress(spelling) }),
      el(doc, 'td', { className: 'flag', text: '' })
    ]));
  }
  table.appendChild(body);
  wrap.appendChild(table);
  return wrap;
}

export function renderWrites(doc, invocation) {
  const wrap = el(doc, 'div', { className: 'writes' });
  if (!invocation.writes.length) {
    wrap.appendChild(el(doc, 'p', { className: 'none', text: 'wrote nothing' }));
    return wrap;
  }
  const list = el(doc, 'ul', { className: 'write-list' });
  for (const write of invocation.writes) {
    list.appendChild(el(doc, 'li', {}, [
      el(doc, 'span', { className: 'addr', text: write.address }),
      el(doc, 'span', { className: `kind kind-${write.kind || 'unknown'}`, text: write.kind || 'kind not recorded' })
    ]));
  }
  wrap.appendChild(list);
  return wrap;
}

/* ------------------------------------------------------------------ */
/* effects: what an OperationalCalculation did outside the store       */
/* ------------------------------------------------------------------ */

/**
 * The contract this section renders when a record carries it, and never
 * requires (a record written before effects existed carries no `effects` key
 * at all and renders exactly as it did before -- no heading, no rows, no
 * chip): per invocation
 * `effects: [{kind, args, result_sha256, ...}]`, one entry per effect in the
 * order they happened, `kind` one of write_text, read_text, now_ms, random,
 * env, and an empty list for a pure `fn.` Calculation. An invocation whose
 * calculation address starts with `oc.` is an OperationalCalculation -- the
 * only kind that may perform an effect at all -- and its card is drawn
 * distinctly whether or not it performed one.
 */

/** The effect kinds the contract names; anything else is shown unstyled. */
export const EFFECT_KINDS = ['write_text', 'read_text', 'now_ms', 'random', 'env'];

/** True when this invocation's calculation address names an OperationalCalculation. */
export function isOperationalCalculation(invocation) {
  const address = invocation.calculation ? invocation.calculation.address : null;
  return typeof address === 'string' && address.startsWith('oc.');
}

/** The recorded effects, and [] for a record that carries none. */
export function invocationEffects(invocation) {
  const effects = invocation.effects;
  if (!Array.isArray(effects)) return [];
  return effects.filter((effect) => effect && typeof effect === 'object');
}

/**
 * The row's middle column, always one line: the path when the effect names one
 * (`read_text`, `write_text`), otherwise `name=value` over the args with the
 * value spelled as JSON, so a string is quoted and a newline inside one can
 * never break the row. Long summaries are cut, never wrapped.
 */
export function effectSummary(effect) {
  const args = effect.args;
  if (!args || typeof args !== 'object') return '\u2014';
  if (typeof args.path === 'string' && args.path.length) return args.path;
  const entries = Object.entries(args);
  if (!entries.length) return '\u2014';
  const line = entries.map(([name, value]) => `${name}=${JSON.stringify(value)}`).join(' \u00b7 ');
  return line.length <= 80 ? line : `${line.slice(0, 80)}\u2026`;
}

/** One row per effect -- index, kind, path or arg summary, digest -- or null for none. */
export function renderEffects(doc, invocation) {
  const effects = invocationEffects(invocation);
  if (!effects.length) return null;
  const wrap = el(doc, 'div', { className: 'effects' });
  wrap.appendChild(el(doc, 'h4', { className: 'effects-head', text: 'effects' }));
  const list = el(doc, 'ol', { className: 'effect-list', attrs: { 'data-effects': String(effects.length) } });
  effects.forEach((effect, index) => {
    const kind = typeof effect.kind === 'string' && effect.kind.length ? effect.kind : 'kind not recorded';
    const known = EFFECT_KINDS.includes(kind) ? ` kind-${kind}` : '';
    const digest = typeof effect.result_sha256 === 'string' && effect.result_sha256.length ? effect.result_sha256 : null;
    list.appendChild(el(doc, 'li', { className: 'effect', attrs: { 'data-effect': String(index) } }, [
      el(doc, 'span', { className: 'effect-index', text: String(index) }),
      el(doc, 'span', { className: `kind effect-kind${known}`, text: kind }),
      el(doc, 'span', { className: 'effect-arg', text: effectSummary(effect) }),
      el(doc, 'span', {
        className: 'digest effect-digest',
        attrs: digest ? { title: digest } : {},
        text: shortHash(digest, 12) || '\u2014'
      })
    ]));
  });
  wrap.appendChild(list);
  return wrap;
}

export function renderInvocation(doc, invocation) {
  const address = invocation.calculation.address || '(no calculation address recorded)';
  const impl = shortHash(invocation.calculation.implementation_sha256);
  const worker = placementWorker(invocation);
  const started = worker !== null && typeof invocation.placement.started_ms === 'number' ? invocation.placement.started_ms : null;
  const operational = isOperationalCalculation(invocation);
  const row = el(doc, 'article', { className: operational ? 'inv oc' : 'inv', attrs: { 'data-invocation': invocation.id } });

  const head = el(doc, 'header', { className: 'inv-head' }, [
    el(doc, 'span', { className: 'inv-id', text: invocation.id }),
    el(doc, 'span', { className: 'inv-call', text: address }),
    operational ? el(doc, 'span', { className: 'pill oc', text: 'oc' }) : null,
    impl ? el(doc, 'span', { className: 'impl', attrs: { title: invocation.calculation.implementation_sha256 }, text: `impl ${impl}` }) : null,
    el(doc, 'span', { className: `pill ${invocation.hit ? 'hit' : 'computed'}`, text: invocation.hit ? 'hit' : 'computed' }),
    el(doc, 'span', { className: 'dur', text: ms(invocation.duration_ms) }),
    worker === null ? null : el(doc, 'span', {
      className: 'placement',
      text: `worker ${worker}`,
      attrs: started === null ? {} : { title: `started ${ms(started)}` }
    })
  ]);
  row.appendChild(head);

  const meta = el(doc, 'dl', { className: 'inv-meta' }, [
    el(doc, 'dt', { text: 'into' }),
    el(doc, 'dd', { className: 'addr', text: invocation.into || '—' }),
    el(doc, 'dt', { text: 'digest' }),
    el(doc, 'dd', { className: 'digest', attrs: invocation.result_sha256 ? { title: invocation.result_sha256 } : {}, text: shortHash(invocation.result_sha256, 16) || '—' }),
    el(doc, 'dt', { text: 'identity scope' }),
    el(doc, 'dd', { text: invocation.calculation.identity_scope })
  ]);
  row.appendChild(meta);

  row.appendChild(renderReads(doc, invocation));
  row.appendChild(renderWrites(doc, invocation));

  const effects = renderEffects(doc, invocation);
  if (effects) row.appendChild(effects);

  if (Object.keys(invocation.args).length) {
    const details = el(doc, 'details', { className: 'args' });
    details.appendChild(el(doc, 'summary', { text: `args · ${Object.keys(invocation.args).join(', ')}` }));
    details.appendChild(el(doc, 'pre', { text: JSON.stringify(invocation.args, null, 2) }));
    row.appendChild(details);
  }

  row.appendChild(renderValue(doc, invocation.value));
  return row;
}

/* ------------------------------------------------------------------ */
/* ticks and part index                                                */
/* ------------------------------------------------------------------ */

export function renderTick(doc, tick) {
  const parallel = isParallelTick(tick);
  const chain = isChainTick(tick);
  // `data-chain` is set only on a chain, so a record with no chain renders byte
  // for byte what it rendered before chains were read (the golden card tree).
  const attrs = { 'data-tick': String(tick.index), 'data-parallel': parallel ? 'yes' : 'no' };
  if (chain) attrs['data-chain'] = 'yes';
  const section = el(doc, 'section', {
    className: parallel ? 'tick parallel' : chain ? 'tick chain' : 'tick',
    attrs
  });
  const count = tick.invocations.length;
  const work = tickWorkMs(tick);
  const latency = tickLatencyMs(tick);
  const timing = work === null && latency === null ? 'no durations recorded' : `work ${ms(work)} · latency ${ms(latency)}`;
  section.appendChild(el(doc, 'header', { className: 'tick-head' }, [
    el(doc, 'h2', {}, [
      el(doc, 'span', { className: 'tick-index', text: String(tick.index) }),
      el(doc, 'span', { className: 'tick-name', text: tick.name }),
      parallel ? el(doc, 'span', { className: 'tick-mode', text: `parallel · ${count} branches` })
        : chain ? el(doc, 'span', { className: 'tick-mode', text: `chain · ${count} in order` }) : null
    ]),
    el(doc, 'p', { className: 'tick-meta', text: `${count} invocation${count === 1 ? '' : 's'} · ${timing}` })
  ]));
  if (parallel) {
    // A row of columns: one branch per Calculation, none of them reading another.
    const branches = el(doc, 'div', { className: 'branches', attrs: { 'data-branches': String(count) } });
    for (const invocation of tick.invocations) {
      branches.appendChild(el(doc, 'div', { className: 'branch' }, [renderInvocation(doc, invocation)]));
    }
    section.appendChild(branches);
  } else {
    // One card under the other: a chain in the order it ran, or a single Calculation.
    for (const invocation of tick.invocations) section.appendChild(renderInvocation(doc, invocation));
  }
  return section;
}

export function renderPartIndex(doc, parts) {
  const section = el(doc, 'section', { className: 'parts' });
  section.appendChild(el(doc, 'h2', { text: 'Part index' }));
  const addresses = Object.keys(parts).sort();
  if (!addresses.length) {
    section.appendChild(el(doc, 'p', { className: 'none', text: 'no Parts recorded' }));
    return section;
  }
  const table = el(doc, 'table', { className: 'part-table' });
  table.appendChild(el(doc, 'thead', {}, [el(doc, 'tr', {}, [
    el(doc, 'th', { text: 'address' }), el(doc, 'th', { text: 'written by' }),
    el(doc, 'th', { text: 'read by' }), el(doc, 'th', { text: 'preexisting' })
  ])]));
  const body = el(doc, 'tbody');
  for (const address of addresses) {
    const part = parts[address];
    body.appendChild(el(doc, 'tr', { className: part.preexisting ? 'preexisting' : '' }, [
      el(doc, 'td', { className: 'addr', text: address }),
      el(doc, 'td', { text: part.written_by || '—' }),
      el(doc, 'td', { text: part.read_by.length ? part.read_by.join(', ') : '—' }),
      el(doc, 'td', { text: part.preexisting ? 'yes' : 'no' })
    ]));
  }
  table.appendChild(body);
  section.appendChild(el(doc, 'div', { className: 'scroll' }, [table]));
  return section;
}

/* ------------------------------------------------------------------ */
/* the whole record                                                    */
/* ------------------------------------------------------------------ */

export function renderRecord(record, { doc = globalThis.document, filter = '' } = {}) {
  validate(record);
  const root = el(doc, 'main', { className: 'record' });

  const total = record.counters.invocations;
  const ticks = filterTicks(record.ticks, filter);
  const shown = ticks.reduce((sum, tick) => sum + tick.invocations.length, 0);

  const source = record.source;
  const header = el(doc, 'header', { className: 'record-head' }, [
    el(doc, 'h1', { text: record.pcr }),
    el(doc, 'p', { className: 'source', text: `${source.runtime}${source.version ? ` ${source.version}` : ''}${source.commit ? ` · ${source.commit}` : ''}` }),
    el(doc, 'ul', { className: 'counters' }, [
      el(doc, 'li', {}, [el(doc, 'span', { className: 'n', text: String(record.counters.invocations) }), el(doc, 'span', { className: 'k', text: 'invocations' })]),
      el(doc, 'li', {}, [el(doc, 'span', { className: 'n', text: String(record.counters.hits) }), el(doc, 'span', { className: 'k', text: 'hits' })]),
      el(doc, 'li', {}, [el(doc, 'span', { className: 'n', text: String(record.counters.computed) }), el(doc, 'span', { className: 'k', text: 'computed' })]),
      el(doc, 'li', {}, [el(doc, 'span', { className: 'n', text: record.counters.wall_ms === null ? '—' : ms(record.counters.wall_ms) }), el(doc, 'span', { className: 'k', text: 'wall' })]),
      el(doc, 'li', {}, [el(doc, 'span', { className: 'n', text: String(record.ticks.length) }), el(doc, 'span', { className: 'k', text: 'ticks' })])
    ])
  ]);
  header.appendChild(el(doc, 'p', {
    className: 'run-timing',
    text: `work ${ms(runWorkMs(record))} · critical path ${ms(runCriticalPathMs(record))}`
  }));
  if (record.parallel === true) {
    header.appendChild(el(doc, 'p', { className: 'run-mode', text: 'parallel: the branches inside a Tick ran at once' }));
  } else if (record.parallel === false) {
    header.appendChild(el(doc, 'p', { className: 'run-mode', text: 'serial: the branches inside a Tick ran one after another; the critical path is what parallel would buy' }));
  }
  const budget = record.budget;
  if (budget && typeof budget === 'object' && budget.completed === false) {
    const limit = typeof budget.limit_ms === 'number' ? `limit ${ms(budget.limit_ms)}` : 'no limit recorded';
    const where = typeof budget.stopped_after_tick === 'string' && budget.stopped_after_tick.length
      ? `stopped after tick ${JSON.stringify(budget.stopped_after_tick)}`
      : 'stopped before the run completed';
    header.appendChild(el(doc, 'p', { className: 'budget-banner', text: `budget: ${where} · ${limit}` }));
  }
  if (filter && filter.trim()) {
    header.appendChild(el(doc, 'p', { className: 'filtered', text: `filter ${JSON.stringify(filter.trim())}: ${shown} of ${total} invocations, ${ticks.length} of ${record.ticks.length} ticks` }));
  }
  root.appendChild(header);

  if (!ticks.length) {
    root.appendChild(el(doc, 'p', { className: 'none', text: `no invocation matches ${JSON.stringify((filter || '').trim())}` }));
  }
  for (const tick of ticks) root.appendChild(renderTick(doc, tick));
  root.appendChild(renderPartIndex(doc, record.parts));
  return root;
}

/* ------------------------------------------------------------------ */
/* watch it think: playback scheduling (pure -- no DOM, no timers)     */
/* ------------------------------------------------------------------ */

// A run with no recorded durations plays at this fixed pace, unscaled by speed.
const FIXED_STEP_MS = 400;

function scheduleRound3(value) {
  return Math.round(value * 1000) / 1000;
}

/**
 * Ordered {tick, invocation, at_ms} events: a serial Calculation "finishes" at
 * the cumulative sum of the durations recorded before it, in record order,
 * scaled by speedFactor (1 = real time, 10/100 = that many times slower).
 *
 * A parallel Tick's branches share one timestamp -- the Tick's latency, not the
 * sum of its branches -- so the page shows that row of cards at once instead of
 * one after another, and the last event lands on the run's critical path.
 */
export function computeSchedule(record, speedFactor = 1) {
  const hasDurations = record.ticks.some((tick) => tick.invocations.some((invocation) => typeof invocation.duration_ms === 'number'));
  const events = [];
  let cumulative = 0;
  for (const tick of record.ticks) {
    if (isParallelTick(tick)) {
      const latency = hasDurations ? tickLatencyMs(tick) : FIXED_STEP_MS;
      cumulative += typeof latency === 'number' ? latency : 0;
      const at = hasDurations ? scheduleRound3(cumulative * speedFactor) : cumulative;
      for (const invocation of tick.invocations) events.push({ tick: tick.index, invocation: invocation.id, at_ms: at });
      continue;
    }
    for (const invocation of tick.invocations) {
      if (hasDurations) cumulative += typeof invocation.duration_ms === 'number' ? invocation.duration_ms : 0;
      else cumulative += FIXED_STEP_MS;
      events.push({ tick: tick.index, invocation: invocation.id, at_ms: hasDurations ? scheduleRound3(cumulative * speedFactor) : cumulative });
    }
  }
  return events;
}

/** The record as it stood at atMs, with parts/counters re-derived so it still validates, and the event currently completing. */
export function scheduleFrame(record, schedule, atMs) {
  const shown = new Set();
  let now = null;
  for (const event of schedule) {
    if (event.at_ms > atMs) break;
    shown.add(event.invocation);
    now = event;
  }
  const ticks = [];
  for (const tick of record.ticks) {
    const invocations = tick.invocations.filter((invocation) => shown.has(invocation.id));
    if (invocations.length) ticks.push({ ...tick, invocations });
  }
  return { record: { ...record, ticks, parts: derivePartIndex(ticks), counters: deriveCounters(ticks) }, now };
}

/* ------------------------------------------------------------------ */
/* loading a record: embedded block, file, drop, ?src=                 */
/* ------------------------------------------------------------------ */

/** A record embedded by embed.mjs as <script type="application/json" id="record">. */
export function readEmbeddedRecord(doc) {
  const node = doc.getElementById ? doc.getElementById('record') : null;
  if (!node) return null;
  const text = (node.textContent || '').trim();
  if (!text) return null;
  return fromPytoRecord(JSON.parse(text));
}

/**
 * "Four worlds, one terminal": records baked by `embed.mjs --out worlds.html`
 * (two-or-more inputs, or `--worlds`), as <script id="records">[{label,
 * record, error, empty, note}]</script>. `record` is already a validated
 * pyto-run-record@1; `error` names why a world's input never became one.
 */
export function readEmbeddedWorlds(doc) {
  const node = doc.getElementById ? doc.getElementById('records') : null;
  if (!node) return null;
  const text = (node.textContent || '').trim();
  if (!text) return null;
  const parsed = JSON.parse(text);
  return Array.isArray(parsed) && parsed.length ? parsed : null;
}

/** A world whose input failed validation: loud, naming the reason, never a blank panel. */
export function renderUnknown(doc, label, reason) {
  return el(doc, 'div', { className: 'status error unknown-panel' }, [
    el(doc, 'p', { className: 'unknown-title', text: `UNKNOWN — ${label}` }),
    el(doc, 'p', { className: 'unknown-reason', text: reason })
  ]);
}

/** A world with no input at all (ChainSpot): a labelled empty slot, not a fake record. */
export function renderEmptySlot(doc, label, note) {
  return el(doc, 'p', { className: 'none', text: `${label}: ${note}` });
}

/**
 * Accept either a record or a raw runtime document and return a record.
 * The wrappers are the fixture shapes in ./fixtures: DiscStudio `{first,second}`
 * or `{pql, receipt}`, ChessLab `{receipts}`, Wumpus `{records}`.
 */
export function coerceToRecord(parsed) {
  if (parsed && parsed.schema) return fromPytoRecord(parsed);
  if (parsed && parsed.pql && parsed.receipt) return fromDiscStudioReceipt(parsed.pql, parsed.receipt);
  if (parsed && parsed.first && parsed.first.pql) return fromDiscStudioReceipt(parsed.first.pql, parsed.first.receipt);
  if (parsed && Array.isArray(parsed.receipts)) return fromChessLabReceipts(parsed.receipts);
  if (parsed && Array.isArray(parsed.records)) return fromWumpusRecords(parsed.records);
  if (parsed && parsed.PrincipleComponentRender) return fromDiscStudioReceipt(parsed, null);
  throw new Error('Unrecognized document: expected a pyto-run-record@1, or {pql, receipt} / {receipts} / {records} from a LAB runtime.');
}

/** Playback controller: Play, Pause, Step, Speed, and the now/clock markers. */
function createPlayback(doc, output, filterBox, getRecord) {
  const toggle = doc.getElementById('playback-toggle');
  const bar = doc.getElementById('playback-bar');
  if (!toggle || !bar) return { isActive: () => false, render() {}, onRecordChanged() {}, forceOff() {}, autostart() {} };

  const speedSel = doc.getElementById('speed');
  const nowEl = doc.getElementById('playback-now');
  const clockEl = doc.getElementById('playback-clock');
  let active = false;
  let schedule = [];
  let shown = 0;
  let timer = null;

  const clearTimer = () => { if (timer !== null) { clearTimeout(timer); timer = null; } };
  const speedFactor = () => Number(speedSel ? speedSel.value : 1) || 1;

  const render = () => {
    while (output.firstChild) output.removeChild(output.firstChild);
    const record = getRecord();
    if (!record) return;
    const atMs = shown ? schedule[shown - 1].at_ms : -1;
    const { record: partial, now } = scheduleFrame(record, schedule, atMs);
    output.appendChild(partial.ticks.length
      ? renderRecord(partial, { doc, filter: filterBox ? filterBox.value : '' })
      : el(doc, 'p', { className: 'none', text: 'watching for the first Calculation…' }));
    if (nowEl) nowEl.textContent = now ? `tick ${now.tick} · ${now.invocation}` : 'not started';
    if (clockEl) clockEl.textContent = `${now ? now.at_ms.toFixed(0) : '0'} ms`;
  };

  const revealOne = () => {
    if (shown >= schedule.length) return;
    // A parallel Tick's branches share one timestamp: Step reveals the row, not one card of it.
    const at = schedule[shown].at_ms;
    do { shown += 1; } while (shown < schedule.length && schedule[shown].at_ms === at);
    render();
  };
  const scheduleNext = () => {
    clearTimer();
    if (shown >= schedule.length) return;
    const from = shown ? schedule[shown - 1].at_ms : 0;
    timer = setTimeout(() => { revealOne(); scheduleNext(); }, Math.max(0, schedule[shown].at_ms - from));
  };
  const reset = () => {
    clearTimer();
    const record = getRecord();
    schedule = record ? computeSchedule(record, speedFactor()) : [];
    shown = 0;
  };

  toggle.addEventListener('click', () => {
    active = !active;
    toggle.setAttribute('aria-pressed', String(active));
    bar.hidden = !active;
    if (active) reset(); else clearTimer();
    render();
  });
  const on = (id, fn) => { const node = doc.getElementById(id); if (node) node.addEventListener('click', fn); };
  on('play-btn', () => { if (active) scheduleNext(); });
  on('pause-btn', clearTimer);
  on('step-btn', () => { if (active) { clearTimer(); revealOne(); } });
  if (speedSel) speedSel.addEventListener('change', () => { if (active) { reset(); render(); } });

  return {
    isActive: () => active,
    render,
    onRecordChanged: () => { if (active) { reset(); render(); } },
    // A world-picker switch onto a slot with no record: stop and rewind.
    forceOff: () => {
      clearTimer();
      schedule = [];
      shown = 0;
      if (active) { active = false; toggle.setAttribute('aria-pressed', 'false'); bar.hidden = true; }
    },
    autostart: () => {
      const params = new URLSearchParams(globalThis.location ? globalThis.location.search : '');
      const flagged = params.get('play') === '1' || (doc.body && doc.body.getAttribute && doc.body.getAttribute('data-play') === '1');
      if (!flagged) return;
      active = true;
      toggle.setAttribute('aria-pressed', 'true');
      bar.hidden = false;
      reset();
      render();
      scheduleNext();
    }
  };
}

/** Wire the page: embedded record, ?src=, file picker, drag and drop. */
export function mount(doc = globalThis.document) {
  const output = doc.getElementById('output');
  const status = doc.getElementById('status');
  const filterBox = doc.getElementById('filter');
  const picker = doc.getElementById('file');
  const worldWrap = doc.getElementById('world-wrap');
  const worldSelect = doc.getElementById('world');
  let current = null;
  let currentEntry = null; // world-picker mode only: the selected {label, record, error, empty, note}

  const playback = createPlayback(doc, output, filterBox, () => current);

  const say = (message, isError = false) => {
    status.textContent = message;
    status.className = isError ? 'status error' : 'status';
  };

  const draw = () => {
    if (playback.isActive()) { playback.render(); return; }
    while (output.firstChild) output.removeChild(output.firstChild);
    if (currentEntry && !currentEntry.record) {
      output.appendChild(currentEntry.error != null
        ? renderUnknown(doc, currentEntry.label, currentEntry.error)
        : renderEmptySlot(doc, currentEntry.label, currentEntry.note || 'no record on file yet'));
      return;
    }
    if (!current) return;
    output.appendChild(renderRecord(current, { doc, filter: filterBox ? filterBox.value : '' }));
  };

  const show = (parsed, label) => {
    try {
      current = coerceToRecord(parsed);
      say(`${label}: ${current.pcr} · ${current.source.runtime} · ${current.counters.invocations} invocations`);
      playback.onRecordChanged();
      draw();
    } catch (error) {
      current = null;
      draw();
      say(`${label}: ${error.message}`, true);
    }
  };

  const loadText = (text, label) => {
    try {
      show(JSON.parse(text), label);
    } catch (error) {
      current = null;
      draw();
      say(`${label}: ${error.message}`, true);
    }
  };

  if (filterBox) filterBox.addEventListener('input', draw);
  if (picker) {
    picker.addEventListener('change', () => {
      const file = picker.files && picker.files[0];
      if (file) file.text().then((text) => loadText(text, file.name));
    });
  }

  const body = doc.body;
  for (const type of ['dragover', 'dragenter']) {
    body.addEventListener(type, (event) => { event.preventDefault(); body.setAttribute('data-drop', 'over'); });
  }
  for (const type of ['dragleave', 'drop']) {
    body.addEventListener(type, () => body.removeAttribute('data-drop'));
  }
  body.addEventListener('drop', (event) => {
    event.preventDefault();
    const file = event.dataTransfer && event.dataTransfer.files && event.dataTransfer.files[0];
    if (file) file.text().then((text) => loadText(text, file.name));
  });

  // Four worlds, one terminal: a picker switch swaps current/currentEntry and
  // redraws -- never a reload -- and always resets playback state.
  const worlds = readEmbeddedWorlds(doc);
  if (worlds && worldSelect) {
    worlds.forEach((entry, index) => {
      worldSelect.appendChild(el(doc, 'option', { text: entry.label, attrs: { value: String(index) } }));
    });
    const selectWorld = (index) => {
      const entry = worlds[index];
      currentEntry = entry;
      current = entry.record || null;
      if (current) {
        playback.onRecordChanged();
        say(`${entry.label}: ${current.pcr} · ${current.source.runtime} · ${current.counters.invocations} invocations`);
      } else {
        playback.forceOff();
        say(`${entry.label}: ${entry.error || entry.note || 'no record'}`, entry.error != null);
      }
      draw();
    };
    worldSelect.addEventListener('change', () => selectWorld(Number(worldSelect.value)));
    if (worldWrap) worldWrap.hidden = false;
    selectWorld(0);
    return;
  }

  const embedded = readEmbeddedRecord(doc);
  if (embedded) {
    current = embedded;
    say(`embedded record: ${embedded.pcr} · ${embedded.source.runtime} · ${embedded.counters.invocations} invocations`);
    draw();
    playback.autostart();
    return;
  }

  const src = new URLSearchParams(globalThis.location ? globalThis.location.search : '').get('src');
  if (src) {
    // Same-origin only: an absolute URL is refused rather than fetched.
    if (/^[a-zA-Z][a-zA-Z0-9+.-]*:/.test(src) || src.startsWith('//')) {
      say(`?src= is same-origin only; refused ${JSON.stringify(src)}`, true);
      return;
    }
    say(`loading ${src}…`);
    fetch(src)
      .then((response) => (response.ok ? response.text() : Promise.reject(new Error(`${response.status} ${response.statusText}`))))
      .then((text) => loadText(text, src))
      .then(() => playback.autostart())
      .catch((error) => say(`${src}: ${error.message}`, true));
    return;
  }

  say('Choose a record, or drop one on the page. file:// pages cannot fetch, so ?src= needs a local server.');
}
