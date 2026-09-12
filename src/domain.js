import { defaultCards, validateCards, applyCardsSet, validatePresetCascade } from './cards.js';
import { validateBattleRule } from './constraints.js';
import { battleTemplates, placeOrder } from './battle.js';
import { framePresets, orientations } from './frames.js';
/** Runtime domain definitions drive both fact editing and presentation discovery. */
export const schema = {
  // `place`, `points`, `total` and `standing` are produced by fn.battle.standings
  // (src/battle.js) and nowhere else, so a preset can bind the standings the same
  // way it binds a score, and the number on the card is the number in the panel.
  BattleEntry: { label: 'Current comparison entry', fields: { score: { type: 'number', label: 'Score', optional: true }, place: { type: 'number', label: 'Place', optional: true }, points: { type: 'number', label: 'Points', optional: true }, total: { type: 'number', label: 'Running total', optional: true }, standing: { type: 'number', label: 'Standing', optional: true }, highlighted: { type: 'boolean', label: 'Highlighted' }, winner: { type: 'boolean', label: 'Authored winner' } } },
  Manufacturer: { label: 'Manufacturer', fields: { name: { type: 'text', label: 'Manufacturer', group: 'Disc identity', order: 1 }, website: { type: 'text', label: 'Website' } } },
  Mold: { label: 'Mold', fields: {
    name: { type: 'text', label: 'Mold name', group: 'Disc identity', order: 0 }, manufacturer: { type: 'ref', target: 'Manufacturer', key: 'manufacturerId', label: 'Manufacturer' },
    category: { type: 'text', label: 'Disc type' }, flight: { type: 'object', label: 'Flight numbers', fields: Object.fromEntries(['speed', 'glide', 'turn', 'fade'].map(k => [k, { type: 'number', label: k[0].toUpperCase() + k.slice(1), optional: true, group: 'Flight numbers', order: 10 }])) }
  } },
  Disc: { label: 'Physical disc', fields: {
    photo: { type: 'image', label: 'Exact disc photo', optional: true, group: 'Disc identity', order: 2 }, mold: { type: 'ref', target: 'Mold', key: 'moldId', label: 'Mold' },
    nickname: { type: 'text', label: 'Nickname', group: 'Disc identity', order: 3 }, plastic: { type: 'text', label: 'Plastic', optional: true }, weight: { type: 'number', label: 'Weight', unit: 'g', optional: true },
    color: { type: 'text', label: 'Color', optional: true }, notes: { type: 'text', label: 'Specimen notes', optional: true }
  } },
  Bag: { label: 'Bag', fields: { name: { type: 'text', label: 'Bag name' }, discIds: { type: 'array', target: 'Disc', label: 'Physical discs' }, notes: { type: 'text', label: 'Bag notes', optional: true } } },
  Team: { label: 'Team', fields: { name: { type: 'text', label: 'Team name' }, bag: { type: 'ref', target: 'Bag', key: 'bagId', label: 'Bag' } } },
  Round: { label: 'Round / hole', fields: { name: { type: 'text', label: 'Round / hole name' }, complete: { type: 'boolean', label: 'Round complete' } } },
  Throw: { label: 'Recorded throw', fields: { team: { type: 'ref', key: 'teamId', target: 'Team', label: 'Team' }, round: { type: 'ref', key: 'roundId', target: 'Round', label: 'Round' }, disc: { type: 'ref', key: 'discId', target: 'Disc', label: 'Disc' } } },
  Competition: { label: 'Competition', fields: { name: { type: 'text', label: 'Competition name' }, teamIds: { type: 'array', target: 'Team', label: 'Teams' }, roundIds: { type: 'array', target: 'Round', label: 'Rounds / holes' }, combine: { type: 'text', label: 'Constraint composition' } } }
};
export const id = prefix => {
  const bytes = crypto.getRandomValues(new Uint8Array(16)); bytes[6] = (bytes[6] & 15) | 64; bytes[8] = (bytes[8] & 63) | 128;
  return `${prefix}-${Array.from(bytes, b => b.toString(16).padStart(2, '0')).join('')}`;
};
export const clone = value => structuredClone(value);
export function freeze(value) { if (value && typeof value === 'object' && !Object.isFrozen(value)) { Object.freeze(value); Object.values(value).forEach(freeze); } return value; }
export function stable(value) { if (value === undefined) return 'null'; if (Array.isArray(value)) return `[${value.map(stable).join(',')}]`; if (value && typeof value === 'object') return `{${Object.keys(value).sort().map(k => `${JSON.stringify(k)}:${stable(value[k])}`).join(',')}}`; return JSON.stringify(value); }
/** Display label only; memoization compares full signatures and never trusts this hash. */
export function labelHash(value) { let h = 2166136261; for (const c of stable(value)) h = Math.imul(h ^ c.charCodeAt(0), 16777619); return (h >>> 0).toString(16).padStart(8, '0'); }
export const partAddress = (type, key) => `px.domain.${type}.${key}`;
export const get = (world, type, key) => world.objects[type]?.[key] ?? null;
export const all = (world, type) => Object.values(world.objects[type] ?? {});
export const currentBattle = world => world.battle.states.find(s => s.id === world.battle.currentStateId);
const safeKey = key => typeof key === 'string' && /^[A-Za-z][A-Za-z0-9_-]{0,99}$/.test(key) && !['__proto__', 'constructor', 'prototype'].includes(key);
export const safeImage = src => typeof src === 'string' && /^data:image\/(png|jpeg|webp);base64,[A-Za-z0-9+/]+=*$/.test(src);
const primitive = value => typeof value === 'number' ? 'number' : typeof value === 'boolean' ? 'boolean' : Array.isArray(value) ? 'array' : value && typeof value === 'object' ? 'object' : 'text';

/** Include defined-but-missing fields AND unregistered data fields. Never a UI whitelist. */
export function discoverFields({ objects, schemas, roots }) {
  const result = [];
  function visit(record, fields, prefix, group, source, trail = [], depth = 0) {
    if (depth > 5) return;
    const definitions = { ...fields };
    const storageKeys = new Set(Object.values(fields).map(d => d.key).filter(Boolean));
    for (const k of Object.keys(record ?? {})) if (safeKey(k) && k !== 'type' && k !== 'id' && !storageKeys.has(k) && !definitions[k]) definitions[k] = { type: primitive(record[k]), label: k, discovered: true };
    for (const [key, def] of Object.entries(definitions)) {
      if (!safeKey(key) || def.private) continue;
      const path = `${prefix}.${key}`, value = record?.[def.key ?? key];
      if (def.type === 'ref') {
        const next = objects[def.target]?.[value] ?? null;
        const marker = `${def.target}:${value}`;
        if (!trail.includes(marker)) visit(next, schemas[def.target]?.fields ?? {}, path, `${group} / ${def.label}`, value ? partAddress(def.target, value) : source, [...trail, marker], depth + 1);
      } else if (def.type === 'object') {
        visit(value, def.fields ?? {}, path, `${group} / ${def.label}`, source, trail, depth + 1);
      } else {
        result.push({ path, label: def.label ?? key, group: def.group ?? group, order: def.order ?? 100, type: def.type, unit: def.unit ?? '', optional: !!def.optional, discovered: !!def.discovered, source, value: value ?? null, available: value !== null && value !== undefined && value !== '' });
        if (def.type === 'array') result.push({ path: `${path}.count`, label: `${def.label} · count`, group, type: 'number', unit: '', source, value: Array.isArray(value) ? value.length : null, available: Array.isArray(value) });
      }
    }
  }
  for (const [alias, root] of Object.entries(roots)) {
    const record = root.record ?? objects[root.type]?.[root.id] ?? null;
    visit(record, schemas[root.type]?.fields ?? root.fields ?? {}, alias, schemas[root.type]?.label ?? root.type, root.id ? partAddress(root.type, root.id) : `px.context.${alias}`);
  }
  return result.sort((a, b) => (a.order ?? 100) - (b.order ?? 100));
}

/** Only the referenced entity closure enters a card's field calculation/cache key. */
export function materialFor(world, roots) {
  const objects = {}, schemas = world.schemas;
  function add(type, key, seen = new Set()) {
    const tag = `${type}:${key}`; if (seen.has(tag)) return; seen.add(tag);
    const record = get(world, type, key); if (!record) return;
    (objects[type] ??= {})[key] = record;
    for (const def of Object.values(schemas[type]?.fields ?? {})) if (def.type === 'ref') add(def.target, record[def.key], seen);
  }
  Object.values(roots).forEach(r => { if (r.id) add(r.type, r.id); });
  return { objects, schemas, roots };
}

export function setPath(record, path, value) {
  const keys = path.split('.'); if (keys.some(k => !safeKey(k))) throw new Error('Invalid field path.');
  let target = record; for (const k of keys.slice(0, -1)) target = target[k] ??= {};
  target[keys.at(-1)] = value;
}

/** Validate every imported/command-produced world before it can replace the current Part. */
export function validateWorld(world) {
  if (!world || world.version !== 2 || !world.objects || !world.schemas || !world.presets || !world.battle) throw new Error('This is not a DiscStudio v2 draft.');
  if (JSON.stringify(world).length > 12_000_000) throw new Error('Draft is too large (12 MB maximum).');
  for (const [type, records] of Object.entries(world.objects)) {
    if (!safeKey(type) || !records || typeof records !== 'object' || Array.isArray(records)) throw new Error('Invalid domain collection.');
    if (Object.keys(records).length > 500) throw new Error('A domain collection exceeds 500 records.');
    for (const [key, record] of Object.entries(records)) {
      if (!safeKey(key) || record.id !== key || record.type !== type) throw new Error('Invalid domain identity.');
      if (type === 'Disc' && record.photo && !safeImage(record.photo)) throw new Error('Disc photos must be embedded PNG, JPEG or WebP images.');
      if (type === 'Bag' && (!Array.isArray(record.discIds) || new Set(record.discIds).size !== record.discIds.length)) throw new Error('A bag must contain unique physical-disc references.');
    }
  }
  // A draft saved before a battle was composed of Constraints carries none, and
  // opens as the open battle -- authored scores, no cap, no points -- rather than
  // being refused. Same rule as the layout's canvas above: normalise, never guess.
  let battle = world.battle;
  if (!Array.isArray(battle.constraints) || typeof battle.combine !== 'string' || typeof battle.templateId !== 'string')
    battle = { ...battle, constraints: Array.isArray(battle.constraints) ? battle.constraints : [], combine: typeof battle.combine === 'string' ? battle.combine : 'all', templateId: typeof battle.templateId === 'string' ? battle.templateId : 'open' };
  if (!['all', 'any'].includes(battle.combine)) throw new Error('A battle composes its constraints with all or any.');
  if (battle.templateId !== 'custom' && !battleTemplates[battle.templateId]) throw new Error(`Unknown battle template '${battle.templateId}'.`);
  if (battle.constraints.length > 12 || new Set(battle.constraints.map(rule => rule.id)).size !== battle.constraints.length) throw new Error('Battle constraints must be distinct.');
  for (const rule of battle.constraints) validateBattleRule(rule);
  if (!Array.isArray(world.battle.entries) || world.battle.entries.length > 12 || new Set(world.battle.entries.map(e => e.id)).size !== world.battle.entries.length) throw new Error('Invalid comparison lineup (maximum 12).');
  if (!Array.isArray(world.battle.states) || !currentBattle(world)) throw new Error('Comparison state is missing.');
  for (const s of world.battle.states) {
    if (!s.scores || Object.values(s.scores).some(n => n !== null && !Number.isFinite(n))) throw new Error('Scores must be finite numbers or blank.');
    if (s.highlight && !world.battle.entries.some(e => e.id === s.highlight)) throw new Error('Highlight references a missing participant.');
    if (!Array.isArray(s.winners) || s.winners.some(key => !world.battle.entries.some(e => e.id === key))) throw new Error('Winner references a missing participant.');
  }
  // A draft saved before the vertical canvas existed carries no orientation and
  // no frame. Both are normalised to what that draft always rendered -- the
  // 1920x1080 canvas, no frame -- rather than refused, and a new object is made
  // only when one is actually missing (validateWorld also runs over frozen Parts).
  let layout = world.layout;
  if (layout && (typeof layout.orientation !== 'string' || !layout.frame || typeof layout.singlePresetId !== 'string')) layout = { ...layout, orientation: typeof layout.orientation === 'string' ? layout.orientation : 'landscape', frame: layout.frame ?? { presetId: 'none', title: '' }, singlePresetId: typeof layout.singlePresetId === 'string' ? layout.singlePresetId : (world.presets.spotlight ? 'spotlight' : layout.presetId) };
  const l = layout;
  if (!l || !world.presets[l.presetId] || !['row', 'stack', 'grid', 'course'].includes(l.arrangement) || !['top-left', 'top-right', 'bottom-left', 'bottom-right', 'center'].includes(l.anchor) || !Number.isFinite(l.scale) || l.scale < .25 || l.scale > 2 || !Number.isFinite(l.gap) || l.gap < 0 || l.gap > 100) throw new Error('Invalid comparison layout.');
  if (!orientations.includes(l.orientation)) throw new Error('A comparison is composed on the landscape or the vertical canvas.');
  if (!world.presets[l.singlePresetId] || world.presets[l.singlePresetId].kind !== 'DisplayCard') throw new Error('Single Disc mode composes with a saved DisplayCard design.');
  if (!l.frame || !framePresets[l.frame.presetId] || typeof l.frame.title !== 'string' || l.frame.title.length > 80) throw new Error('Invalid overlay frame: pick a frame preset and a title of at most 80 characters.');
  for (const comp of Object.values(world.objects.Competition ?? {})) {
    if (!['all', 'any'].includes(comp.combine) || !Array.isArray(comp.constraints) || !Array.isArray(comp.teamIds) || !Array.isArray(comp.roundIds)) throw new Error('Invalid competition composition.');
    for (const rule of comp.constraints) if (!['bagLimit', 'oneMold', 'teamThrows'].includes(rule.kind) || !safeKey(rule.id) || typeof rule.enabled !== 'boolean' || !Number.isInteger(rule.value) || rule.value < 1 || rule.value > 100) throw new Error('Constraint values must be whole numbers from 1 to 100.');
  }
  for (const preset of Object.values(world.presets)) validatePreset(preset);
  // Old drafts saved before the card cascade existed carry no `cards` at all;
  // a task-78 draft carries a `projections` layer whose values were never the
  // presets' own overrides (the preset IS the projection layer now, task 79),
  // so it is dropped rather than kept. Both are normalised here rather than
  // mutated (world may already be frozen -- `pop` validates an already-frozen
  // Part) by returning a new object only when one is needed.
  let cards = world.cards;
  if (!cards) cards = defaultCards();
  else if (Object.hasOwn(cards, 'projections')) { const { projections, ...rest } = cards; cards = rest; }
  const result = cards === world.cards && layout === world.layout && battle === world.battle ? world : { ...world, cards, layout, battle };
  validateCards(result.cards);
  return result;
}
export function validatePreset(p) {
  if (!p || !safeKey(p.id) || typeof p.name !== 'string' || !['DisplayCard', 'DiscImage'].includes(p.kind)) throw new Error('Invalid presentation preset.');
  if (![p.width, p.height].every(n => Number.isFinite(n) && n >= 100 && n <= 2000)) throw new Error('Presentation size must be 100–2000 px.');
  if (!Array.isArray(p.nodes) || p.nodes.length > 100 || new Set(p.nodes.map(n => n.id)).size !== p.nodes.length) throw new Error('Invalid presentation elements.');
  for (const n of p.nodes) {
    if (!safeKey(n.id) || !['text', 'image'].includes(n.kind) || typeof n.binding !== 'string' || ![n.x, n.y, n.w, n.h, n.size].every(Number.isFinite)) throw new Error('Invalid presentation element.');
    if (n.w <= 0 || n.h <= 0 || n.size < 4 || n.size > 200 || Math.abs(n.x) > 4000 || Math.abs(n.y) > 4000) throw new Error('Element dimensions are out of range.');
  }
  // The preset IS the projection layer (task 79): background, foreground, accent,
  // font, radius and sponsor are its own cascade overrides, each null (or, for
  // sponsor, absent) meaning it inherits from `world.cards.global` instead.
  validatePresetCascade(p);
  return p;
}

/**
 * A new disc paints in its own hue, like every seeded one: the colour a person
 * actually typed when it names a hue the sample palette knows (the seed's own
 * Mint is 150, Peach 22, Lilac 268, Gold 45, Blue 204, Sand 41, Rose 330), and
 * otherwise a hue derived from the disc's key, so two discs added in a row are
 * never the same colour. Authored artBase/artAccent still win in the painter.
 */
const COLOUR_HUES = { red: 4, copper: 18, peach: 22, orange: 26, bronze: 32, sand: 41, gold: 45, amber: 44, yellow: 54, cream: 56, white: 60, glow: 72, lime: 88, green: 124, mint: 150, teal: 172, cyan: 188, sky: 198, silver: 200, blue: 204, navy: 224, indigo: 246, lilac: 268, purple: 278, violet: 286, magenta: 308, pink: 326, rose: 330, black: 214, grey: 210, gray: 210, clear: 190 };
export function sampleHueFor(colour, key) {
  for (const word of String(colour ?? '').toLowerCase().match(/[a-z]+/g) ?? []) if (COLOUR_HUES[word] != null) return COLOUR_HUES[word];
  let h = 7; for (const ch of String(key ?? '')) h = (h * 31 + ch.charCodeAt(0)) >>> 0;
  return h % 360;
}
/** Product identifiers are linked; this operation rebinds one disc instead of renaming a shared mold. */
function reidentify(world, disc, manufacturer, mold) {
  const name = manufacturer.trim() || 'Unknown manufacturer', moldName = mold.trim() || 'Unnamed mold';
  let org = all(world, 'Manufacturer').find(x => x.name.toLowerCase() === name.toLowerCase());
  if (!org) { org = { id: id('maker'), type: 'Manufacturer', name, website: '' }; world.objects.Manufacturer[org.id] = org; }
  let product = all(world, 'Mold').find(x => x.manufacturerId === org.id && x.name.toLowerCase() === moldName.toLowerCase());
  if (!product) { product = { id: id('mold'), type: 'Mold', name: moldName, manufacturerId: org.id, category: '', flight: {} }; world.objects.Mold[product.id] = product; }
  disc.moldId = product.id;
}

export function applyCommand({ world: previous, command }) {
  const w = clone(previous), c = command, state = currentBattle(w);
  const required = (type, key) => { const value = get(w, type, key); if (!value) throw new Error(`${type} '${key}' is missing.`); return value; };
  switch (c.type) {
    case 'entity.set': setPath(required(c.entityType, c.id), c.path, c.value); break;
    case 'entity.add': {
      if (!safeKey(c.record.type) || !safeKey(c.record.id)) throw new Error('Invalid new object.');
      (w.objects[c.record.type] ??= {})[c.record.id] = clone(c.record); break;
    }
    case 'schema.addField': {
      if (!safeKey(c.name) || !w.schemas[c.entityType]) throw new Error('Invalid field definition.');
      if (!['text', 'number', 'boolean'].includes(c.fieldType)) throw new Error('Unsupported new field type.');
      w.schemas[c.entityType].fields[c.name] = { type: c.fieldType, label: c.label || c.name, optional: true }; break;
    }
    case 'disc.identity': reidentify(w, required('Disc', c.id), c.manufacturer, c.mold); break;
    case 'disc.create': {
      // One gesture, one command: the maker, the mold and the disc are made together,
      // so a single undo takes the whole new disc back out and never leaves a stray
      // 'Unknown manufacturer' behind. The facts a person actually has in hand come in
      // with it; a blank nickname is written from them rather than left as a placeholder.
      if (!safeKey(c.id) || get(w, 'Disc', c.id)) throw new Error('Invalid new disc.');
      const disc = { id: c.id, type: 'Disc', moldId: null, nickname: '', photo: c.photo ?? null, plastic: String(c.plastic ?? '').trim(), weight: c.weight ?? null, color: String(c.color ?? '').trim(), notes: '', sampleHue: sampleHueFor(c.color, c.id) };
      w.objects.Disc[c.id] = disc;
      reidentify(w, disc, String(c.manufacturer ?? ''), String(c.mold ?? ''));
      const product = get(w, 'Mold', disc.moldId), category = String(c.category ?? '').trim();
      if (category && !product.category) product.category = category;
      disc.nickname = String(c.nickname ?? '').trim() || [disc.plastic, product.name, disc.weight == null ? '' : `${disc.weight} g`].filter(Boolean).join(' ') || 'Your disc';
      if (c.bagId) required('Bag', c.bagId).discIds = [...get(w, 'Bag', c.bagId).discIds, c.id];
      break;
    }
    case 'disc.duplicate': { const d = clone(required('Disc', c.id)); d.id = c.newId; d.nickname = `${d.nickname || 'Disc'} · another specimen`; w.objects.Disc[d.id] = d; break; }
    case 'disc.remove': {
      if (all(w, 'Bag').some(b => b.discIds.includes(c.id)) || w.battle.entries.some(e => e.discId === c.id) || all(w, 'Throw').some(t => t.discId === c.id)) throw new Error('Remove this disc from its bags and comparison first. Discs with recorded throws must be retained.');
      delete w.objects.Disc[c.id]; break;
    }
    case 'bag.membership': { const b = required('Bag', c.bagId); required('Disc', c.discId); b.discIds = c.include ? [...new Set([...b.discIds, c.discId])] : b.discIds.filter(x => x !== c.discId); break; }
    case 'bag.reorder': {
      // A bag is an order as well as a set: the order a person packed it in, which is
      // the order the cards stand in. Nothing about size is checked here; a cap is a
      // competition's constraint (src/constraints.js), never the bag's own business.
      const b = required('Bag', c.bagId), from = b.discIds.indexOf(c.discId);
      if (from < 0) throw new Error('That disc is not in this bag.');
      const to = Math.max(0, Math.min(b.discIds.length - 1, Math.trunc(c.toIndex)));
      const next = [...b.discIds]; next.splice(from, 1); next.splice(to, 0, c.discId); b.discIds = next; break;
    }
    case 'bag.duplicate': { const b = required('Bag', c.id); if (!safeKey(c.newId) || get(w, 'Bag', c.newId)) throw new Error('Invalid new bag.'); w.objects.Bag[c.newId] = { ...clone(b), id: c.newId, name: String(c.name ?? '').trim() || `${b.name} · copy` }; break; }
    case 'bag.remove': { if (all(w, 'Team').some(t => t.bagId === c.id)) throw new Error('This bag belongs to a competition team. Reassign the team first.'); delete w.objects.Bag[c.id]; break; }
    case 'battle.add': {
      required('Disc', c.discId); if (w.battle.entries.some(e => e.discId === c.discId)) throw new Error('That physical disc is already in the comparison.');
      // The cap is a Constraint of this battle, refused here by the same sentence
      // the rules panel shows. Nothing is silently dropped to fit.
      const cap = w.battle.constraints.find(rule => rule.enabled && rule.kind === 'discCap');
      if (cap && w.battle.entries.length >= cap.value) throw new Error(`This battle caps the lineup at ${cap.value} discs and it is full. Remove one before adding another, or raise the cap.`);
      w.battle.entries.push({ id: c.id, discId: c.discId }); w.battle.states.forEach(s => { s.scores[c.id] = null; }); break;
    }
    case 'battle.remove': w.battle.entries = w.battle.entries.filter(e => e.id !== c.id); w.battle.states.forEach(s => { delete s.scores[c.id]; if (s.highlight === c.id) s.highlight = null; s.winners = s.winners.filter(x => x !== c.id); }); break;
    case 'battle.move': { const i = w.battle.entries.findIndex(e => e.id === c.id), j = i + c.offset; if (i >= 0 && j >= 0 && j < w.battle.entries.length) [w.battle.entries[i], w.battle.entries[j]] = [w.battle.entries[j], w.battle.entries[i]]; break; }
    case 'battle.score': if (!w.battle.entries.some(e => e.id === c.id)) throw new Error('Participant is missing.'); state.scores[c.id] = c.score; break;
    case 'battle.highlight': state.highlight = c.id || null; break;
    case 'battle.winner': state.winners = state.winners.includes(c.id) ? state.winners.filter(x => x !== c.id) : [...state.winners, c.id]; break;
    case 'battle.state.save': { if (w.battle.states.length >= 100) throw new Error('Maximum 100 comparison states.'); const next = { ...clone(state), id: c.id, name: c.name || `State ${w.battle.states.length + 1}` }; w.battle.states.push(next); w.battle.currentStateId = next.id; break; }
    case 'battle.state.select': if (!w.battle.states.some(s => s.id === c.id)) throw new Error('State is missing.'); w.battle.currentStateId = c.id; break;
    case 'battle.state.rename': state.name = c.name; break;
    case 'battle.state.remove': if (w.battle.states.length === 1) throw new Error('Keep at least one state.'); w.battle.states = w.battle.states.filter(s => s.id !== c.id); if (!w.battle.states.some(s => s.id === w.battle.currentStateId)) w.battle.currentStateId = w.battle.states[0].id; break;
    case 'battle.template': { const template = battleTemplates[c.id]; if (!template) throw new Error(`Unknown battle template '${c.id}'.`); w.battle.templateId = template.id; w.battle.constraints = clone(template.constraints); break; }
    case 'battle.rule.add': { if (w.battle.constraints.some(rule => rule.id === c.rule.id)) throw new Error('That constraint is already composed into this battle.'); w.battle.constraints.push(clone(c.rule)); w.battle.templateId = 'custom'; break; }
    case 'battle.rule.set': { const rule = w.battle.constraints.find(r => r.id === c.ruleId); if (!rule) throw new Error('That battle constraint is missing.'); Object.assign(rule, c.patch); w.battle.templateId = 'custom'; break; }
    case 'battle.rule.remove': w.battle.constraints = w.battle.constraints.filter(rule => rule.id !== c.ruleId); w.battle.templateId = 'custom'; break;
    // Tapping the finishing order IS entering the scores: one command, one undo.
    case 'battle.order': { if (!w.battle.entries.some(e => e.id === c.id)) throw new Error('Participant is missing.'); state.scores = placeOrder({ state, entries: w.battle.entries, entryId: c.id }); break; }
    case 'battle.order.clear': for (const entry of w.battle.entries) state.scores[entry.id] = null; break;
    case 'preset.put': w.presets[c.preset.id] = clone(validatePreset(c.preset)); break;
    case 'preset.set': { const p = w.presets[c.id]; if (!p) throw new Error('Presentation is missing.'); if (c.nodeId) { const node = p.nodes.find(n => n.id === c.nodeId); if (!node) throw new Error('Element is missing.'); Object.assign(node, c.patch); } else Object.assign(p, c.patch); break; }
    case 'preset.node.add': w.presets[c.id].nodes.push(clone(c.node)); break;
    case 'preset.node.remove': w.presets[c.id].nodes = w.presets[c.id].nodes.filter(n => n.id !== c.nodeId); break;
    case 'preset.node.move': { const nodes = w.presets[c.id].nodes, i = nodes.findIndex(n => n.id === c.nodeId), j = i + c.offset; if (i >= 0 && j >= 0 && j < nodes.length) [nodes[i], nodes[j]] = [nodes[j], nodes[i]]; break; }
    case 'layout.set': Object.assign(w.layout, c.patch); break;
    case 'cards.set': { const next = applyCardsSet({ cards: w.cards, presets: w.presets }, c); w.cards = next.cards; w.presets = next.presets; break; }
    case 'competition.rule.set': { const comp = required('Competition', c.id); const rule = comp.constraints.find(r => r.id === c.ruleId); if (!rule) throw new Error('Constraint is missing.'); Object.assign(rule, c.patch); break; }
    case 'competition.rule.add': required('Competition', c.id).constraints.push(clone(c.rule)); break;
    case 'competition.rule.remove': { const comp = required('Competition', c.id); comp.constraints = comp.constraints.filter(r => r.id !== c.ruleId); break; }
    case 'throw.record': {
      const team = required('Team', c.teamId), bag = required('Bag', team.bagId); required('Round', c.roundId); required('Disc', c.discId);
      if (!bag.discIds.includes(c.discId)) throw new Error('This disc is not in that team’s bag.');
      w.objects.Throw[c.id] = { id: c.id, type: 'Throw', teamId: c.teamId, roundId: c.roundId, discId: c.discId }; break;
    }
    case 'throw.remove': delete w.objects.Throw[c.id]; break;
    case 'export.record': w.exports.push(clone(c.record)); w.exports = w.exports.slice(-100); break;
    default: throw new Error(`Unknown command '${c.type}'.`);
  }
  w.events = [...(w.events ?? []), { id: c.eventId ?? id('event'), type: c.type, time: c.time ?? new Date().toISOString(), subject: c.id ?? c.discId ?? c.teamId ?? null }].slice(-200);
  return freeze(validateWorld(w));
}
