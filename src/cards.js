/**
 * Card cascade (task 79): the token model, its validation and the three pure
 * Calculations PxC calls through `fn.cards.effective` / `fn.cards.apply` /
 * `fn.cards.query`. Everything here is pure over its inputs -- no board, no
 * addresses -- so runtime.js is the only place that knows how these functions
 * are wired to Parts. See pyto/experiments/cards/CONTRACT.md for the shape
 * this file implements.
 *
 * The owner's way this task implements: the preset IS the projection layer.
 * `shelf`/`bag` compose with the `discImage` preset; `single`/`competition`
 * compose with whichever preset `world.layout.presetId` names. A preset's own
 * background/foreground/accent/font/radius/sponsor ARE its overrides -- a
 * field set to `null` (or, for sponsor, left absent) inherits from global.
 * There is no separate `px.discstudio.cards.projection.*` Part: the
 * projection layer of a card is simply the preset it composes with.
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

/** The cascade a fresh or old-format draft gets: one global layer, no instance overrides. */
export function defaultCards() {
  return {
    global: { background: '#203d36', foreground: '#fcfbf5', accent: '#b9d789', font: 'sans', radius: 16, sponsor: '' },
    instances: Object.fromEntries(PROJECTIONS.map(p => [p, {}]))
  };
}

/** One token's value, checked against its kind. Throws by name -- refusals name the token. */
export function validateToken(token, value) {
  if (!Object.hasOwn(CARD_TOKENS, token)) throw new Error(`Unknown card token '${token}'.`);
  switch (token) {
    case 'background':
      if (value !== 'transparent' && (typeof value !== 'string' || !/^#[0-9a-f]{6}$/i.test(value))) throw new Error(`Token 'background' must be a #rrggbb color or 'transparent'.`);
      break;
    case 'foreground': case 'accent':
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

/**
 * A preset's own cascade fields: each of the six tokens is either absent/null
 * (inherits from global) or a legal value for its kind. `'transparent'` stays
 * legal for `background`, foreground and accent (task 78 already allowed the
 * card background to be transparent for an overlay-only export).
 */
export function validatePresetCascade(p) {
  for (const token of TOKEN_NAMES) {
    if (!Object.hasOwn(p, token) || p[token] === null || p[token] === undefined) continue;
    validateToken(token, p[token]);
  }
  return p;
}

/** `world.cards` is well-formed: global carries all six tokens, instance overrides carry only what they declare. */
export function validateCards(cards) {
  if (!cards || typeof cards !== 'object') throw new Error('Invalid card cascade.');
  if (!cards.global || typeof cards.global !== 'object') throw new Error('Card cascade: global layer is missing.');
  for (const token of TOKEN_NAMES) validateToken(token, cards.global[token]);
  if (Object.keys(cards.global).length !== TOKEN_NAMES.length) throw new Error('Card cascade: the global layer must carry exactly the six tokens.');
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
 * `{ type: 'cards.set', layer, presetId?, projection?, discId?, token, value }`
 * applied to `{ cards, presets }`, returning a new `{ cards, presets }` (the
 * caller owns mutation of the rest of the world). `value: null` clears an
 * override on `preset` / `instance`; on `global` it is refused, because the
 * root of the cascade never inherits. The `preset` layer is the same
 * mutation `preset.set` with a patch performs -- `w.presets[presetId][token]
 * = value` -- so the Component Editor's existing controls, which dispatch
 * `preset.set` directly, and this command agree on one behaviour.
 */
export function applyCardsSet({ cards, presets }, c) {
  if (!Object.hasOwn(CARD_TOKENS, c.token)) throw new Error(`Unknown card token '${c.token}'.`);
  if (c.layer === 'global') {
    if (c.value === null) throw new Error('The root of the cascade never inherits.');
    return { cards: { ...cards, global: { ...cards.global, [c.token]: validateToken(c.token, c.value) } }, presets };
  }
  if (c.layer === 'preset') {
    const preset = presets[c.presetId];
    if (!preset) throw new Error(`Missing presentation '${c.presetId}'.`);
    const value = c.value === null ? null : validateToken(c.token, c.value);
    return { cards, presets: { ...presets, [c.presetId]: { ...preset, [c.token]: value } } };
  }
  if (c.layer === 'instance') {
    if (!PROJECTIONS.includes(c.projection)) throw new Error(`Unknown card projection '${c.projection}'.`);
    if (typeof c.discId !== 'string' || !c.discId) throw new Error('An instance override needs a disc id.');
    const byDisc = { ...(cards.instances[c.projection] ?? {}) };
    const layer = { ...(byDisc[c.discId] ?? {}) };
    if (c.value === null) delete layer[c.token]; else layer[c.token] = validateToken(c.token, c.value);
    if (Object.keys(layer).length) byDisc[c.discId] = layer; else delete byDisc[c.discId];
    return { cards: { ...cards, instances: { ...cards.instances, [c.projection]: byDisc } }, presets };
  }
  throw new Error(`Unknown card cascade layer '${c.layer}'.`);
}

/**
 * `fn.cards.effective`: the three layers folded into one set of tokens plus
 * where each one came from. `preset` is the live preset Part this projection
 * composes with (`px.presentation.<presetId>`) -- its own six fields ARE the
 * preset layer, `null`/absent meaning it inherits from `global`. `instances`
 * is the resolved prefix query `px.discstudio.cards.instance.<projectionName>.*`,
 * so the one entry for this disc (if any) is found by rebuilding its address.
 */
export function cardsEffective({ global, preset, instances = {}, projectionName, discId }) {
  const instanceAddress = `px.discstudio.cards.instance.${projectionName}.${discId}`;
  const instance = instances[instanceAddress] ?? {};
  const tokens = {}, provenance = {};
  for (const token of TOKEN_NAMES) {
    if (Object.hasOwn(instance, token)) { tokens[token] = instance[token]; provenance[token] = 'instance'; }
    else if (preset[token] !== null && preset[token] !== undefined) { tokens[token] = preset[token]; provenance[token] = 'preset'; }
    else { tokens[token] = global[token]; provenance[token] = 'global'; }
  }
  const presetOverrides = Object.fromEntries(TOKEN_NAMES.filter(t => preset[t] !== null && preset[t] !== undefined).map(t => [t, preset[t]]));
  return { projection: projectionName, discId, presetId: preset.id, tokens, provenance, layers: { global, preset: presetOverrides, instance } };
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

/** The preset a projection composes with today: shelf/bag on the disc image, single/competition on the shared comparison design. */
const presetIdFor = (projection, layout) => (projection === 'shelf' || projection === 'bag') ? 'discImage' : layout.presetId;

/**
 * `fn.cards.query`: the three PQL reads the editor needs, all over prefix
 * queries so a read is on the record instead of a runtime-side index.
 * `presentations` is `px.presentation.*` (every preset, keyed by address),
 * `instances` is `px.discstudio.cards.instance.*` and `effective` is
 * `px.discstudio.cards.effective.*` -- every one keyed by full address.
 */
export function cardsQuery({ global, presentations = {}, layout, instances = {}, effective = {}, name, token, projection, discId }) {
  if (name === 'overrides') {
    const rows = [];
    for (const preset of Object.values(presentations)) {
      for (const tok of TOKEN_NAMES) if (preset[tok] !== null && preset[tok] !== undefined) rows.push({ layer: 'preset', presetId: preset.id, token: tok, value: preset[tok] });
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
      const preset = presentations[`px.presentation.${presetIdFor(p, layout)}`];
      projectionsResult[p] = !preset || preset[token] === null || preset[token] === undefined;
    }
    const presetsResult = {};
    for (const preset of Object.values(presentations)) presetsResult[preset.id] = preset[token] === null || preset[token] === undefined;
    const instancesResult = [];
    for (const e of Object.values(effective)) {
      if (e && e.provenance && e.provenance[token] === 'global') instancesResult.push({ projection: e.projection, discId: e.discId });
    }
    return { projections: projectionsResult, presets: presetsResult, instances: instancesResult };
  }
  if (name === 'provenance') {
    const e = effective[`px.discstudio.cards.effective.${projection}.${discId}`];
    return e ? e.provenance : null;
  }
  throw new Error(`Unknown card cascade query '${name}'.`);
}
