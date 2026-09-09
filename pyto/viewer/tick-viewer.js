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

import { validate, bareAddress, tickDurationMs, PNG_DATA_URL_PREFIX, fromPytoRecord, fromDiscStudioReceipt, fromChessLabReceipts, fromWumpusRecords } from './adapters.js';

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

export function renderInvocation(doc, invocation) {
  const address = invocation.calculation.address || '(no calculation address recorded)';
  const impl = shortHash(invocation.calculation.implementation_sha256);
  const row = el(doc, 'article', { className: 'inv', attrs: { 'data-invocation': invocation.id } });

  const head = el(doc, 'header', { className: 'inv-head' }, [
    el(doc, 'span', { className: 'inv-id', text: invocation.id }),
    el(doc, 'span', { className: 'inv-call', text: address }),
    impl ? el(doc, 'span', { className: 'impl', attrs: { title: invocation.calculation.implementation_sha256 }, text: `impl ${impl}` }) : null,
    el(doc, 'span', { className: `pill ${invocation.hit ? 'hit' : 'computed'}`, text: invocation.hit ? 'hit' : 'computed' }),
    el(doc, 'span', { className: 'dur', text: ms(invocation.duration_ms) })
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
  const section = el(doc, 'section', { className: 'tick', attrs: { 'data-tick': String(tick.index) } });
  const count = tick.invocations.length;
  const duration = tickDurationMs(tick);
  section.appendChild(el(doc, 'header', { className: 'tick-head' }, [
    el(doc, 'h2', {}, [
      el(doc, 'span', { className: 'tick-index', text: String(tick.index) }),
      el(doc, 'span', { className: 'tick-name', text: tick.name })
    ]),
    el(doc, 'p', { className: 'tick-meta', text: `${count} invocation${count === 1 ? '' : 's'} · ${duration === null ? 'no durations recorded' : ms(duration)}` })
  ]));
  for (const invocation of tick.invocations) section.appendChild(renderInvocation(doc, invocation));
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

/** Wire the page: embedded record, ?src=, file picker, drag and drop. */
export function mount(doc = globalThis.document) {
  const output = doc.getElementById('output');
  const status = doc.getElementById('status');
  const filterBox = doc.getElementById('filter');
  const picker = doc.getElementById('file');
  let current = null;

  const say = (message, isError = false) => {
    status.textContent = message;
    status.className = isError ? 'status error' : 'status';
  };

  const draw = () => {
    while (output.firstChild) output.removeChild(output.firstChild);
    if (!current) return;
    output.appendChild(renderRecord(current, { doc, filter: filterBox ? filterBox.value : '' }));
  };

  const show = (parsed, label) => {
    try {
      current = coerceToRecord(parsed);
      say(`${label}: ${current.pcr} · ${current.source.runtime} · ${current.counters.invocations} invocations`);
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

  const embedded = readEmbeddedRecord(doc);
  if (embedded) {
    current = embedded;
    say(`embedded record: ${embedded.pcr} · ${embedded.source.runtime} · ${embedded.counters.invocations} invocations`);
    draw();
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
      .catch((error) => say(`${src}: ${error.message}`, true));
    return;
  }

  say('Choose a record, or drop one on the page. file:// pages cannot fetch, so ?src= needs a local server.');
}
