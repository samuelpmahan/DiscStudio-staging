/**
 * Finding the RIGHT disc, as one Calculation over the whole shelf.
 *
 * A query is read the way a person says it out loud -- "buzzz 177", "midrange -1",
 * "esp mint" -- so every term has to match something about the disc (a word in a
 * text fact, or a number that is its weight or one of its flight numbers) and the
 * results are ranked by how well: the mold you named beats the nickname that merely
 * contains the same letters. Every field is searched, including the ones that live
 * on the mold (flight numbers, disc type) rather than on the specimen.
 *
 * The same Calculation also does the organising a shelf needs -- the quick filters,
 * the sort and the grouping -- because they are one read over one set: filter, then
 * rank, then order, then group, in that order, with the rows carrying what matched.
 */
export const SORTS = [
  ['recent', 'Recently added'], ['maker', 'Maker'], ['mold', 'Mold'],
  ['category', 'Disc type'], ['speed', 'Speed'], ['weight', 'Weight']
];
export const GROUPS = [['none', 'No grouping'], ['maker', 'By maker'], ['category', 'By disc type']];
export const FILTERS = [['inBag', 'In this bag'], ['unbagged', 'In no bag'], ['photo', 'Has photo']];
const FLIGHT = ['speed', 'glide', 'turn', 'fade'];
const norm = value => String(value ?? '').toLowerCase().trim();
const words = value => norm(value).split(/[^a-z0-9+.'-]+/).filter(Boolean);
/** Text facts, with what each is worth when a term hits it: the mold you named beats a nickname that merely contains it. */
const textFacts = ({ disc, mold, maker }) => [
  { label: mold?.name, text: mold?.name, weight: 10, kind: 'mold' },
  { label: maker?.name, text: maker?.name, weight: 7, kind: 'maker' },
  { label: mold?.category, text: mold?.category, weight: 7, kind: 'category' },
  { label: disc.plastic, text: disc.plastic, weight: 6, kind: 'plastic' },
  { label: disc.color, text: disc.color, weight: 5, kind: 'colour' },
  { label: disc.nickname, text: disc.nickname, weight: 4, kind: 'nickname' },
  { label: disc.notes, text: disc.notes, weight: 2, kind: 'notes' }
].filter(fact => norm(fact.text));
/** One term against one disc: its best score, and the fact it matched, or null when nothing did. */
function scoreTerm(term, row) {
  let best = null;
  const take = (score, label) => { if (score > 0 && (!best || score > best.score)) best = { score, label }; };
  for (const fact of textFacts(row)) {
    const text = norm(fact.text);
    if (words(text).includes(term)) take(fact.weight * 3, fact.label);
    else if (text.startsWith(term)) take(fact.weight * 2, fact.label);
    else if (words(text).some(word => word.startsWith(term))) take(Math.round(fact.weight * 1.5), fact.label);
    else if (text.includes(term)) take(fact.weight, fact.label);
  }
  const value = /^-?\d+(\.\d+)?$/.test(term) ? Number(term) : null;
  if (value !== null) {
    if (row.disc.weight === value) take(30, `${value} g`);
    else if (Number.isFinite(row.disc.weight) && Math.abs(row.disc.weight - value) <= 2) take(9, `${row.disc.weight} g`);
    for (const key of FLIGHT) if (row.mold?.flight?.[key] === value) take(24, `${key} ${String(value).replace('-', '−')}`);
  }
  return best;
}
const compare = (a, b) => a < b ? -1 : a > b ? 1 : 0;
const last = (value, direction) => value === null || value === undefined || value === '' ? direction : 0;
function order(sort, rows) {
  const by = {
    recent: (a, b) => b.index - a.index,
    maker: (a, b) => compare(norm(a.maker?.name), norm(b.maker?.name)) || compare(norm(a.mold?.name), norm(b.mold?.name)),
    mold: (a, b) => compare(norm(a.mold?.name), norm(b.mold?.name)) || compare(b.disc.weight ?? 0, a.disc.weight ?? 0),
    category: (a, b) => last(a.mold?.category, 1) - last(b.mold?.category, 1) || compare(norm(a.mold?.category), norm(b.mold?.category)) || compare(norm(a.mold?.name), norm(b.mold?.name)),
    speed: (a, b) => last(a.mold?.flight?.speed, 1) - last(b.mold?.flight?.speed, 1) || compare(b.mold?.flight?.speed ?? 0, a.mold?.flight?.speed ?? 0) || compare(norm(a.mold?.name), norm(b.mold?.name)),
    weight: (a, b) => last(a.disc.weight, 1) - last(b.disc.weight, 1) || compare(b.disc.weight ?? 0, a.disc.weight ?? 0) || compare(norm(a.mold?.name), norm(b.mold?.name))
  }[sort] ?? ((a, b) => b.index - a.index);
  return [...rows].sort((a, b) => by(a, b) || compare(a.disc.id, b.disc.id));
}
const groupOf = (row, group) => group === 'maker' ? (row.maker?.name || 'Unknown maker') : group === 'category' ? (row.mold?.category || 'Unsorted') : 'All discs';
/**
 * The shelf as a person asked for it. `discs` arrives in the order the shelf holds
 * them, which is the order they were added, so "recently added" is that order read
 * backwards rather than a timestamp nobody wrote down.
 */
export function shelfQuery({ discs = [], molds = {}, makers = {}, bags = [], query = '', sort = 'recent', group = 'none', filters = [], bagId = null } = {}) {
  const terms = norm(query).split(/\s+/).filter(Boolean);
  const active = FILTERS.map(([key]) => key).filter(key => filters.includes(key));
  const rows = discs.map((disc, index) => {
    const mold = molds[disc.moldId] ?? null;
    return { index, disc, mold, maker: (mold && makers[mold.manufacturerId]) || null, bagIds: bags.filter(bag => bag.discIds.includes(disc.id)).map(bag => bag.id) };
  });
  const kept = rows.filter(row => {
    if (active.includes('inBag') && !(bagId && row.bagIds.includes(bagId))) return false;
    if (active.includes('unbagged') && row.bagIds.length) return false;
    if (active.includes('photo') && !row.disc.photo) return false;
    return true;
  });
  const ranked = [];
  for (const row of kept) {
    if (!terms.length) { ranked.push({ ...row, score: 0, matched: [] }); continue; }
    const hits = terms.map(term => scoreTerm(term, row));
    if (hits.some(hit => !hit)) continue;
    ranked.push({ ...row, score: hits.reduce((sum, hit) => sum + hit.score, 0), matched: [...new Set(hits.map(hit => hit.label))] });
  }
  const ordered = terms.length
    ? order(sort, ranked).sort((a, b) => b.score - a.score || 0)
    : order(sort, ranked);
  const groups = [];
  for (const row of ordered) {
    const label = groupOf(row, group);
    (groups.find(g => g.label === label) ?? (groups.push({ label, discIds: [] }), groups.at(-1))).discIds.push(row.disc.id);
  }
  // The sections read A to Z whatever the sort inside them is; without grouping there is one.
  if (group !== 'none') groups.sort((a, b) => compare(norm(a.label), norm(b.label)));
  return {
    query, terms, sort, group, filters: active, bagId,
    total: discs.length, shown: ordered.length,
    rows: ordered.map(row => ({ id: row.disc.id, score: row.score, matched: row.matched, bagIds: row.bagIds, group: groupOf(row, group) })),
    groups
  };
}
