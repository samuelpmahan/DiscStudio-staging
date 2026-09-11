/**
 * fn.art.assign: which of the painter's families each disc is painted in, decided
 * over the whole shelf at once instead of by a hash per disc (the owner,
 * 2026-09-11: "spread the bitch out for the first half and then the second half
 * grouping the common items ... distributional, representational, and just look
 * good").
 *
 * Two phases over the items in the order the shelf holds them:
 *
 *   spread   the first `spread` unauthored items (half the family list by
 *            default, so the phase does not move with the size of the shelf) each
 *            take the family a golden-ratio walk lands on (frac((k + 1) * phi) * n),
 *            the next unused one when that is taken: every prefix of the walk is
 *            as evenly spread over the family list as a deterministic sequence can
 *            be, and no family repeats while spreading;
 *   grouped  after that, an item takes the family of the earliest item that
 *            shares its key (its mold), so like things look alike; an item whose
 *            key is new keeps walking, unused families first.
 *
 * An authored family always wins and is never handed to anyone else's key.
 * Pure over its inputs: no clock, no random; the same shelf gives the same
 * assignment, and appending a disc never moves an earlier one.
 */
const PHI = (1 + Math.sqrt(5)) / 2;

/** The golden-ratio walk over `n` slots: the k-th index, k from 0. */
export function goldenIndex(k, n) { const x = ((k + 1) * PHI) % 1; return Math.floor(x * n) % n; }

/**
 * `items`: [{ id, key, authored }] in shelf order; `families`: the painter's list.
 * Returns { assignment: { id: family }, phase: { id: 'authored'|'spread'|'grouped' }, histogram, families }.
 */
export function assignArt({ items = [], families = [], key = 'key', spread = null } = {}) {
  if (!Array.isArray(families) || !families.length) throw new Error('fn.art.assign needs at least one family.');
  const budget = spread == null ? Math.ceil(families.length / 2) : Math.max(0, Math.min(families.length, spread));
  const assignment = {}, phase = {}, used = new Set(), byKey = new Map();
  for (const item of items) if (item.authored && families.includes(item.authored)) { assignment[item.id] = item.authored; phase[item.id] = 'authored'; used.add(item.authored); }
  let walk = 0;
  const nextFree = () => {
    for (let tries = 0; tries < families.length; tries++, walk++) {
      const family = families[goldenIndex(walk, families.length)];
      if (!used.has(family)) { walk++; return family; }
    }
    return families[goldenIndex(walk++, families.length)]; // everything used: keep walking, repeats are now allowed
  };
  let placed = 0;
  for (const item of items) {
    const k = item[key] ?? item.key;
    if (phase[item.id] === 'authored') { if (k != null && !byKey.has(k)) byKey.set(k, assignment[item.id]); continue; }
    const spreading = placed < budget && used.size < families.length;
    let family;
    if (!spreading && k != null && byKey.has(k)) { family = byKey.get(k); phase[item.id] = 'grouped'; }
    else { family = nextFree(); phase[item.id] = spreading ? 'spread' : 'grouped'; }
    placed++;
    used.add(family); assignment[item.id] = family;
    if (k != null && !byKey.has(k)) byKey.set(k, family);
  }
  const histogram = Object.fromEntries(families.map(f => [f, 0]));
  for (const family of Object.values(assignment)) histogram[family] = (histogram[family] ?? 0) + 1;
  return { families: [...families], key, spread: budget, assignment, phase, histogram };
}

/** The shelf's items from the world: discs in the order the shelf holds them, keyed by mold. */
export function shelfItems(world, key = 'moldId') {
  return Object.values(world.objects.Disc ?? {}).map(disc => ({ id: disc.id, key: disc[key] ?? null, authored: disc.artFamily || null }));
}
