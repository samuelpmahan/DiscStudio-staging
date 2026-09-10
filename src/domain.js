import { defaultCards, validateCards, applyCardsSet } from './cards.js';
/** Runtime domain definitions drive both fact editing and presentation discovery. */
export const schema = {
  BattleEntry: { label: 'Current comparison entry', fields: { score: { type: 'number', label: 'Score', optional: true }, highlighted: { type: 'boolean', label: 'Highlighted' }, winner: { type: 'boolean', label: 'Authored winner' } } },
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
  if (!Array.isArray(world.battle.entries) || world.battle.entries.length > 12 || new Set(world.battle.entries.map(e => e.id)).size !== world.battle.entries.length) throw new Error('Invalid comparison lineup (maximum 12).');
  if (!Array.isArray(world.battle.states) || !currentBattle(world)) throw new Error('Comparison state is missing.');
  for (const s of world.battle.states) {
    if (!s.scores || Object.values(s.scores).some(n => n !== null && !Number.isFinite(n))) throw new Error('Scores must be finite numbers or blank.');
    if (s.highlight && !world.battle.entries.some(e => e.id === s.highlight)) throw new Error('Highlight references a missing participant.');
    if (!Array.isArray(s.winners) || s.winners.some(key => !world.battle.entries.some(e => e.id === key))) throw new Error('Winner references a missing participant.');
  }
  const l = world.layout;
  if (!l || !world.presets[l.presetId] || !['row', 'stack', 'grid'].includes(l.arrangement) || !['top-left', 'top-right', 'bottom-left', 'bottom-right', 'center'].includes(l.anchor) || !Number.isFinite(l.scale) || l.scale < .25 || l.scale > 2 || !Number.isFinite(l.gap) || l.gap < 0 || l.gap > 100) throw new Error('Invalid comparison layout.');
  for (const comp of Object.values(world.objects.Competition ?? {})) {
    if (!['all', 'any'].includes(comp.combine) || !Array.isArray(comp.constraints) || !Array.isArray(comp.teamIds) || !Array.isArray(comp.roundIds)) throw new Error('Invalid competition composition.');
    for (const rule of comp.constraints) if (!['bagLimit', 'oneMold', 'teamThrows'].includes(rule.kind) || !safeKey(rule.id) || typeof rule.enabled !== 'boolean' || !Number.isInteger(rule.value) || rule.value < 1 || rule.value > 100) throw new Error('Constraint values must be whole numbers from 1 to 100.');
  }
  for (const preset of Object.values(world.presets)) validatePreset(preset);
  // Old drafts saved before the card cascade existed carry no `cards` at all;
  // fill the defaults here rather than mutate (world may already be frozen --
  // `pop` validates an already-frozen Part) by returning a new object only
  // when one is needed.
  const result = world.cards ? world : { ...world, cards: defaultCards() };
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
  return p;
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
    case 'disc.duplicate': { const d = clone(required('Disc', c.id)); d.id = c.newId; d.nickname = `${d.nickname || 'Disc'} · another specimen`; w.objects.Disc[d.id] = d; break; }
    case 'disc.remove': {
      if (all(w, 'Bag').some(b => b.discIds.includes(c.id)) || w.battle.entries.some(e => e.discId === c.id) || all(w, 'Throw').some(t => t.discId === c.id)) throw new Error('Remove this disc from its bags and comparison first. Discs with recorded throws must be retained.');
      delete w.objects.Disc[c.id]; break;
    }
    case 'bag.membership': { const b = required('Bag', c.bagId); required('Disc', c.discId); b.discIds = c.include ? [...new Set([...b.discIds, c.discId])] : b.discIds.filter(x => x !== c.discId); break; }
    case 'bag.remove': { if (all(w, 'Team').some(t => t.bagId === c.id)) throw new Error('This bag belongs to a competition team. Reassign the team first.'); delete w.objects.Bag[c.id]; break; }
    case 'battle.add': {
      required('Disc', c.discId); if (w.battle.entries.some(e => e.discId === c.discId)) throw new Error('That physical disc is already in the comparison.');
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
    case 'preset.put': w.presets[c.preset.id] = clone(validatePreset(c.preset)); break;
    case 'preset.set': { const p = w.presets[c.id]; if (!p) throw new Error('Presentation is missing.'); if (c.nodeId) { const node = p.nodes.find(n => n.id === c.nodeId); if (!node) throw new Error('Element is missing.'); Object.assign(node, c.patch); } else Object.assign(p, c.patch); break; }
    case 'preset.node.add': w.presets[c.id].nodes.push(clone(c.node)); break;
    case 'preset.node.remove': w.presets[c.id].nodes = w.presets[c.id].nodes.filter(n => n.id !== c.nodeId); break;
    case 'preset.node.move': { const nodes = w.presets[c.id].nodes, i = nodes.findIndex(n => n.id === c.nodeId), j = i + c.offset; if (i >= 0 && j >= 0 && j < nodes.length) [nodes[i], nodes[j]] = [nodes[j], nodes[i]]; break; }
    case 'layout.set': Object.assign(w.layout, c.patch); break;
    case 'cards.set': w.cards = applyCardsSet(w.cards, c); break;
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
