/**
 * Card cascade (task 78): the token model, its validation and the three pure
 * Calculations PxC calls through `fn.cards.effective` / `fn.cards.apply` /
 * `fn.cards.query`. Everything here is pure over its inputs -- no board, no
 * addresses -- so runtime.js is the only place that knows how these functions
 * are wired to Parts. See pyto/experiments/cards/CONTRACT.md for the shape
 * this file implements.
 */

/** The four places the existing card chain (Fields -> Art -> Card -> CardSvg) is called from. */
export const PROJECTIONS = ['shelf', 'bag', 'single', 'competition'];

/** The token set, small on purpose. Published verbatim as `px.discstudio.cards.tokens`. */
export const CARD_TOKENS = {
  background: { kind: 'color', label: 'Background' },
  foreground: { kind: 'color', label: 'Foreground' },
  accent: { kind: 'color', label: 'Accent' },
  font: { kind: 'font', label: 'Font', options: ['sans', 'serif', 'mono'] },
  radius: { kind: 'radius', label: 'Corner radius', min: 0, max: 100 },
  sponsor: { kind: 'sponsor', label: 'Sponsor lockup', maxLength: 40 }
};
const TOKEN_NAMES = Object.keys(CARD_TOKENS);

/** The cascade a fresh or old-format draft gets: one root layer, four empty overrides each. */
export function defaultCards() {
  return {
    global: { background: '#203d36', foreground: '#fcfbf5', accent: '#b9d789', font: 'sans', radius: 16, sponsor: '' },
    projections: Object.fromEntries(PROJECTIONS.map(p => [p, {}])),
    instances: Object.fromEntries(PROJECTIONS.map(p => [p, {}]))
  };
}

/** One token's value, checked against its kind. Throws by name -- refusals name the token. */
export function validateToken(token, value) {
  if (!Object.hasOwn(CARD_TOKENS, token)) throw new Error(`Unknown card token '${token}'.`);
  switch (token) {
    case 'background': case 'foreground': case 'accent':
      if (typeof value !== 'string' || !/^#[0-9a-f]{6}$/i.test(value)) throw new Error(`Token '${token}' must be a #rrggbb color.`);
      break;
    case 'font':
      if (!['sans', 'serif', 'mono'].includes(value)) throw new Error(`Token 'font' must be one of sans, serif, mono.`);
      break;
    case 'radius':
      if (!Number.isInteger(value) || value < 0 || value > 100) throw new Error(`Token 'radius' must be an integer from 0 to 100.`);
      break;
    case 'sponsor':
      if (typeof value !== 'string' || value.length > 40) throw new Error(`Token 'sponsor' must be a string of at most 40 characters.`);
      break;
  }
  return value;
}

/** `world.cards` is well-formed: global carries all six tokens, overrides carry only what they declare. */
export function validateCards(cards) {
  if (!cards || typeof cards !== 'object') throw new Error('Invalid card cascade.');
  if (!cards.global || typeof cards.global !== 'object') throw new Error('Card cascade: global layer is missing.');
  for (const token of TOKEN_NAMES) validateToken(token, cards.global[token]);
  if (Object.keys(cards.global).length !== TOKEN_NAMES.length) throw new Error('Card cascade: the global layer must carry exactly the six tokens.');
  if (!cards.projections || typeof cards.projections !== 'object') throw new Error('Card cascade: projections layer is missing.');
  for (const p of Object.keys(cards.projections)) if (!PROJECTIONS.includes(p)) throw new Error(`Card cascade: unknown projection '${p}'.`);
  for (const p of PROJECTIONS) {
    const layer = cards.projections[p];
    if (!layer || typeof layer !== 'object') throw new Error(`Card cascade: projection '${p}' is missing.`);
    for (const [token, value] of Object.entries(layer)) validateToken(token, value);
  }
  if (!cards.instances || typeof cards.instances !== 'object') throw new Error('Card cascade: instances layer is missing.');
  for (const p of Object.keys(cards.instances)) if (!PROJECTIONS.includes(p)) throw new Error(`Card cascade: unknown projection '${p}'.`);
  for (const p of PROJECTIONS) {
    const byDisc = cards.instances[p] ?? {};
    if (typeof byDisc !== 'object') throw new Error(`Card cascade: instance overrides for '${p}' are missing.`);
    for (const [discId, layer] of Object.entries(byDisc)) {
      if (!layer || typeof layer !== 'object' || !Object.keys(layer).length) throw new Error(`Card cascade: instance override '${p}.${discId}' must not be empty.`);
      for (const [token, value] of Object.entries(layer)) validateToken(token, value);
    }
  }
  return cards;
}

/**
 * `{ type: 'cards.set', layer, projection?, discId?, token, value }` applied to
 * `world.cards`, returning a new cards object (the caller owns mutation of the
 * rest of the world). `value: null` clears an override on `projection` /
 * `instance`; on `global` it is refused, because the root of the cascade never
 * inherits.
 */
export function applyCardsSet(cards, c) {
  if (!Object.hasOwn(CARD_TOKENS, c.token)) throw new Error(`Unknown card token '${c.token}'.`);
  if (c.layer !== 'global' && !PROJECTIONS.includes(c.projection)) throw new Error(`Unknown card projection '${c.projection}'.`);
  const next = {
    global: { ...cards.global },
    projections: Object.fromEntries(PROJECTIONS.map(p => [p, { ...(cards.projections[p] ?? {}) }])),
    instances: Object.fromEntries(PROJECTIONS.map(p => [p, Object.fromEntries(Object.entries(cards.instances[p] ?? {}).map(([discId, layer]) => [discId, { ...layer }]))]))
  };
  if (c.layer === 'global') {
    if (c.value === null) throw new Error('The root of the cascade never inherits.');
    next.global[c.token] = validateToken(c.token, c.value);
  } else if (c.layer === 'projection') {
    const layer = next.projections[c.projection];
    if (c.value === null) delete layer[c.token]; else layer[c.token] = validateToken(c.token, c.value);
  } else if (c.layer === 'instance') {
    if (typeof c.discId !== 'string' || !c.discId) throw new Error('An instance override needs a disc id.');
    const byDisc = next.instances[c.projection];
    const layer = { ...(byDisc[c.discId] ?? {}) };
    if (c.value === null) delete layer[c.token]; else layer[c.token] = validateToken(c.token, c.value);
    if (Object.keys(layer).length) byDisc[c.discId] = layer; else delete byDisc[c.discId];
  } else {
    throw new Error(`Unknown card cascade layer '${c.layer}'.`);
  }
  return next;
}

/**
 * `fn.cards.effective`: the three layers folded into one set of tokens plus
 * where each one came from. `instances` is the resolved prefix query
 * `px.discstudio.cards.instance.<projectionName>.*`, so the one entry for this
 * disc (if any) is found by rebuilding its address.
 */
export function cardsEffective({ global, projection = {}, instances = {}, projectionName, discId }) {
  const instanceAddress = `px.discstudio.cards.instance.${projectionName}.${discId}`;
  const instance = instances[instanceAddress] ?? {};
  const tokens = {}, provenance = {};
  for (const token of TOKEN_NAMES) {
    if (Object.hasOwn(instance, token)) { tokens[token] = instance[token]; provenance[token] = 'instance'; }
    else if (Object.hasOwn(projection, token)) { tokens[token] = projection[token]; provenance[token] = 'projection'; }
    else { tokens[token] = global[token]; provenance[token] = 'global'; }
  }
  return { projection: projectionName, discId, tokens, provenance, layers: { global, projection, instance } };
}

/**
 * `fn.cards.apply`: the preset with the effective tokens painted on, plus a
 * sponsor lockup node when `sponsor` is non-empty. `binding: ''` is
 * deliberate -- composeCard (src/presentation.js) reads `n.text` only when a
 * node has no binding, so this is a static text node, not a field reference.
 */
export function cardsApply({ preset, effective }) {
  const tokens = effective.tokens, nodes = preset.nodes.map(n => ({ ...n }));
  if (tokens.sponsor) {
    const w = Math.min(160, Math.max(40, preset.width - 20)), h = 18;
    nodes.push({
      id: 'sponsor', kind: 'text', binding: '', text: tokens.sponsor,
      x: Math.max(4, preset.width - w - 10), y: Math.max(4, preset.height - h - 8), w, h,
      size: 11, bold: true, align: 'right', font: tokens.font, color: tokens.accent,
      showLabel: false, hideEmpty: false, prefix: '', suffix: '', visible: true
    });
  }
  return { ...preset, background: tokens.background, foreground: tokens.foreground, accent: tokens.accent, font: tokens.font, radius: tokens.radius, nodes };
}

/**
 * `fn.cards.query`: the three PQL reads the editor needs, all over prefix
 * queries so a read is on the record instead of a runtime-side index.
 * `projections` is `px.discstudio.cards.projection.*`, `instances` is
 * `px.discstudio.cards.instance.*` and `effective` is
 * `px.discstudio.cards.effective.*` -- every one keyed by full address.
 */
export function cardsQuery({ global, projections = {}, instances = {}, effective = {}, name, token, projection, discId }) {
  if (name === 'overrides') {
    const rows = [];
    for (const p of PROJECTIONS) {
      const layer = projections[`px.discstudio.cards.projection.${p}`] ?? {};
      for (const [tok, value] of Object.entries(layer)) rows.push({ layer: 'projection', projection: p, token: tok, value });
    }
    for (const [address, layer] of Object.entries(instances)) {
      const m = /^px\.discstudio\.cards\.instance\.([^.]+)\.(.+)$/.exec(address);
      if (!m || !layer) continue;
      for (const [tok, value] of Object.entries(layer)) rows.push({ layer: 'instance', projection: m[1], discId: m[2], token: tok, value });
    }
    return rows;
  }
  if (name === 'inherits') {
    const projectionsResult = {};
    for (const p of PROJECTIONS) {
      const layer = projections[`px.discstudio.cards.projection.${p}`] ?? {};
      projectionsResult[p] = !Object.hasOwn(layer, token);
    }
    const instancesResult = [];
    for (const e of Object.values(effective)) {
      if (e && e.provenance && e.provenance[token] === 'global') instancesResult.push({ projection: e.projection, discId: e.discId });
    }
    return { projections: projectionsResult, instances: instancesResult };
  }
  if (name === 'provenance') {
    const e = effective[`px.discstudio.cards.effective.${projection}.${discId}`];
    return e ? e.provenance : null;
  }
  throw new Error(`Unknown card cascade query '${name}'.`);
}
