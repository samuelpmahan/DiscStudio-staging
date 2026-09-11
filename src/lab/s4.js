/**
 * S4, invented: Holes. The first Stage of this port that ChainSpot does not
 * have -- S0..S3 were read out of the LAB and ported; S4 is written in the
 * LAB's own stage grammar (a contract naming consumes and produces, a PQL
 * document of Ticks, `fn.lab.*` Calculations, a `has` provenance block on every
 * object it constructs, and, where no reference run exists, invariants as the
 * oracle) on top of what the ported Stages publish.
 *
 *   consumes  px.badges.objects   (S1: the number, and whether it was read)
 *             px.tees             (S3: the visible tees)
 *             px.baskets          (S2: the baskets)
 *   produces  px.holes.objects    one assembled hole per read badge
 *             px.holes.unplaced   every anchor and badge no hole could use
 *
 * The binding rule is the one the straight route (route.js, task 114) carries
 * today, lifted out of pathfinding and into a Stage: the holes take their turns
 * in badge order, and each takes the nearest tee and the nearest basket not
 * already taken. Lifting it is what makes it checkable. The rule alone can bind
 * a hole to any anchor at any distance; the invariants say what the rule may
 * never do:
 *
 *   1. a badge is used by at most one hole, and every badge is either a hole or
 *      reported unreadable;
 *   2. a tee is used by at most one hole, a basket by at most one hole, and
 *      every anchor is either bound or reported free;
 *   3. a hole with no basket left to take is a hole whose basket is MISSING --
 *      `basket: null`, `missing: ['basket']` -- never the basket of another
 *      hole and never an invented point;
 *   4. confidence is a stated sum over what is present, not a score: 0.5 for a
 *      badge the Stage read, 0.25 for a tee, 0.25 for a basket.
 *
 * Those five accounts are a Part of their own (`S4.invariants`, the two-Tick
 * shape S3's Python analogue uses: AccountHoles publishes a ledger, CheckHoles
 * reads it back and says whether it balances).
 */
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { labAddress, labDocument } from './address.js';
import { STAGES } from './source.js';
import { compileMermaidPcr, lowerToPql } from './mermaid.js';

export const S4_ADDRESSES = {
  numbers: labAddress('px.holes.numbers'),
  binding: labAddress('px.holes.binding'),
  objects: labAddress('px.holes.objects'),
  unplaced: labAddress('px.holes.unplaced'),
  ledger: 'px.exp.lab.s4.holeledger',
  summary: 'px.exp.lab.s4.holesummary'
};

export const BIND_RULE = 'nearest-free-in-badge-order';

export const centerOf = ([x, y, width, height]) => [x + width / 2, y + height / 2];
export const distance = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1]);
export const round3 = value => Math.round(value * 1000) / 1000;

/**
 * Tick 1. The badges, as numbers. A badge S1 marked `unread` has no number and
 * cannot take a turn; it leaves here, named, and never reaches the binding.
 * Ordering is the reading, then position, so two badges reading the same number
 * still order deterministically.
 */
export function readNumbers({ badges }) {
  const read = [], unreadable = [];
  badges.forEach((badge, index) => {
    const id = `badge-${index + 1}`, bbox = badge.unaccountedButOwned.bbox;
    const entry = { id, bbox, at: centerOf(bbox), reading: badge.reading?.value ?? null, status: badge.reading?.status ?? 'unread' };
    if (entry.status === 'read' && entry.reading !== null && /^[0-9]+$/.test(entry.reading)) read.push({ ...entry, number: Number(entry.reading) });
    else unreadable.push({ ...entry, why: entry.status !== 'read' ? 'S1 did not read the digits confidently' : 'the reading is not a hole number' });
  });
  return {
    rule: 'badge order is the reading, not the position in the raster',
    numbered: read.sort((left, right) => left.number - right.number || left.at[1] - right.at[1] || left.at[0] - right.at[0]),
    unreadable
  };
}

/** The anchors get their ids here, from the order their Stage published them: S2's baskets and S3's tees carry none. */
const anchorsOf = (objects, prefix, at) => objects.map((object, index) => ({ id: `${prefix}-${index + 1}`, bbox: object.bbox, at: at(object), taken: null }));

/**
 * Tick 2. The binding: hole by hole in badge order, nearest free anchor first.
 * An exhausted pool binds nothing -- it does not reach further, and it does not
 * take an anchor back off another hole.
 */
export function bindAnchors({ numbers, tees, baskets, rule = BIND_RULE }) {
  if (rule !== BIND_RULE) throw new Error(`lab s4: unknown binding rule: ${rule}`);
  const teePool = anchorsOf(tees, 'tee', tee => tee.center), basketPool = anchorsOf(baskets, 'basket', basket => centerOf(basket.bbox));
  const claim = (pool, hole) => {
    const free = pool.filter(candidate => candidate.taken === null);
    if (!free.length) return null;
    const best = free.map(candidate => ({ candidate, gap: distance(candidate.at, hole.at) }))
      .sort((left, right) => left.gap - right.gap || left.candidate.id.localeCompare(right.candidate.id))[0];
    best.candidate.taken = hole.number;
    return { id: best.candidate.id, at: best.candidate.at, bbox: best.candidate.bbox, gapFromBadgePx: round3(best.gap) };
  };
  const bound = numbers.numbered.map(hole => ({ badge: hole, tee: claim(teePool, hole), basket: claim(basketPool, hole) }));
  return {
    rule, bound, unreadable: numbers.unreadable,
    pools: { tees: teePool.map(({ taken, ...anchor }) => ({ ...anchor, boundTo: taken })), baskets: basketPool.map(({ taken, ...anchor }) => ({ ...anchor, boundTo: taken })) }
  };
}

/** What a hole is missing, and how sure the Stage is of it: a stated sum, not a score. */
export function confidenceOf(entry) {
  const parts = { badgeRead: 0.5, tee: entry.tee ? 0.25 : 0, basket: entry.basket ? 0.25 : 0 };
  return { value: round3(parts.badgeRead + parts.tee + parts.basket), basis: parts, of: 'badge read 0.5 + tee 0.25 + basket 0.25' };
}

/** Tick 3. One Hole object per bound badge, with the `has` block the LAB's objects carry. */
export function assembleHoles({ binding }) {
  return binding.bound.map(entry => {
    const missing = [...(entry.tee ? [] : ['tee']), ...(entry.basket ? [] : ['basket'])];
    return {
      number: entry.badge.number,
      badge: { id: entry.badge.id, reading: entry.badge.reading, bbox: entry.badge.bbox, at: entry.badge.at },
      tee: entry.tee, basket: entry.basket,
      confidence: confidenceOf(entry), missing,
      complete: missing.length === 0,
      has: {
        readNumbers: { fn: labAddress('fn.Hole.readNumbers'), reading: entry.badge.reading, status: entry.badge.status },
        bindAnchors: { fn: labAddress('fn.Hole.bindAnchors'), rule: binding.rule, tee: entry.tee?.id ?? null, basket: entry.basket?.id ?? null },
        assemble: { fn: labAddress('fn.Hole.assemble'), missing }
      }
    };
  });
}

/** Tick 4. Everything no hole could use, each with the reason it is here. */
export function unplaced({ binding, holes }) {
  const free = pool => binding.pools[pool].filter(anchor => anchor.boundTo === null);
  return {
    for: 'what S4 could not put in a hole, so that nothing is silently dropped between the Stages and the course',
    badges: binding.unreadable.map(badge => ({ id: badge.id, bbox: badge.bbox, why: badge.why })),
    tees: free('tees').map(anchor => ({ id: anchor.id, at: anchor.at, why: 'no hole was left to take it' })),
    baskets: free('baskets').map(anchor => ({ id: anchor.id, at: anchor.at, why: 'no hole was left to take it' })),
    incomplete: holes.filter(hole => hole.missing.length).map(hole => ({ number: hole.number, missing: hole.missing, why: `the ${hole.missing.join(' and ')} pool was empty when hole ${hole.number} took its turn` }))
  };
}

/* ------------------------------------------- the invariants, as the oracle */

/** Every badge and every anchor, counted once on each side of the Stage. */
export function accountHoles({ numbers, binding, holes, unplaced }) {
  return {
    badgesIn: numbers.numbered.length + numbers.unreadable.length,
    numbered: numbers.numbered.length, unreadable: numbers.unreadable.length,
    holes: holes.length,
    teesIn: binding.pools.tees.length, teesBound: binding.pools.tees.filter(anchor => anchor.boundTo !== null).length, teesFree: unplaced.tees.length,
    basketsIn: binding.pools.baskets.length, basketsBound: binding.pools.baskets.filter(anchor => anchor.boundTo !== null).length, basketsFree: unplaced.baskets.length,
    complete: holes.filter(hole => hole.complete).length, incomplete: unplaced.incomplete.length
  };
}

/** The five things the binding rule may never do. A `false` here is a refusal, not a warning. */
export function checkHoles({ ledger, holes, binding }) {
  const used = key => holes.map(hole => hole[key]?.id).filter(Boolean);
  const once = ids => new Set(ids).size === ids.length;
  const checks = {
    everyBadgeOnce: ledger.badgesIn === ledger.holes + ledger.unreadable && once(holes.map(hole => hole.badge.id)),
    everyTeeOnce: once(used('tee')) && ledger.teesIn === ledger.teesBound + ledger.teesFree && ledger.teesBound === used('tee').length,
    everyBasketOnce: once(used('basket')) && ledger.basketsIn === ledger.basketsBound + ledger.basketsFree && ledger.basketsBound === used('basket').length,
    missingIsNotGuessed: holes.every(hole => (hole.basket === null) === hole.missing.includes('basket') && (hole.tee === null) === hole.missing.includes('tee')),
    confidenceIsStated: holes.every(hole => hole.confidence.value === confidenceOf(hole).value),
    orderIsTheReading: holes.every((hole, index) => index === 0 || holes[index - 1].number < hole.number)
  };
  return { ...ledger, rule: binding.rule, checks, balanced: Object.values(checks).every(Boolean) };
}

export function registerS4(lab) {
  lab.register(labAddress('fn.Hole.readNumbers'), readNumbers);
  lab.register(labAddress('fn.Hole.bindAnchors'), bindAnchors);
  lab.register(labAddress('fn.Hole.assemble'), assembleHoles);
  lab.register(labAddress('fn.Hole.unplaced'), unplaced);
  lab.register('fn.lab.s4.accountholes', accountHoles);
  lab.register('fn.lab.s4.checkholes', checkHoles);
}

/** The contract, as a Part: what S4 consumes and what it produces, in one place a reader can check against the document. */
export const S4_CONTRACT = {
  stage: 'S4', name: 'Holes',
  for: 'one hole object per badge the Stages read, anchored on the tees and baskets they found, with what is missing named rather than guessed',
  consumes: ['px.badges.objects', 'px.tees', 'px.baskets'].map(labAddress),
  produces: [S4_ADDRESSES.objects, S4_ADDRESSES.unplaced],
  ticks: ['Hole.readNumbers', 'Hole.bindAnchors', 'Hole.assemble', 'Hole.unplaced'],
  invariants: ['everyBadgeOnce', 'everyTeeOnce', 'everyBasketOnce', 'missingIsNotGuessed', 'confidenceIsStated', 'orderIsTheReading']
};

/** The document S4's contract declares. */
export function s4Document(lab) {
  return lab.document('S4', [
    { name: 'Hole.readNumbers', Calculations: [{ call: labAddress('fn.Hole.readNumbers'), with: { badges: labAddress('px.badges.objects') }, args: {}, into: S4_ADDRESSES.numbers }] },
    { name: 'Hole.bindAnchors', Calculations: [{ call: labAddress('fn.Hole.bindAnchors'), with: { numbers: S4_ADDRESSES.numbers, tees: labAddress('px.tees'), baskets: labAddress('px.baskets') }, args: { rule: BIND_RULE }, into: S4_ADDRESSES.binding }] },
    { name: 'Hole.assemble', Calculations: [{ call: labAddress('fn.Hole.assemble'), with: { binding: S4_ADDRESSES.binding }, args: {}, into: S4_ADDRESSES.objects }] },
    { name: 'Hole.unplaced', Calculations: [{ call: labAddress('fn.Hole.unplaced'), with: { binding: S4_ADDRESSES.binding, holes: S4_ADDRESSES.objects }, args: {}, into: S4_ADDRESSES.unplaced }] }
  ]);
}

/**
 * The Mermaid path, the way the LAB has one for S0 and S1: `stages/S4.mmd` is
 * the same composition drawn as a flowchart, and the ported compiler turns it
 * into the document `s4Document` builds -- the same Calculations over the same
 * addresses in the same order (structural digest equal).
 */
export function compiledS4() {
  const compiled = compileMermaidPcr(readFileSync(join(STAGES, 'S4.mmd'), 'utf8'), JSON.parse(readFileSync(join(STAGES, 'S4.args.json'), 'utf8')));
  const { document, local } = lowerToPql(compiled);
  return { compiled, local, document: labDocument(document) };
}

/** The invariants, as their own two-Tick composition: the shape S3's Python analogue uses. */
export function s4InvariantDocument(lab) {
  return lab.document('S4.invariants', [
    { name: 'AccountHoles', Calculations: [{ call: 'fn.lab.s4.accountholes', with: { numbers: S4_ADDRESSES.numbers, binding: S4_ADDRESSES.binding, holes: S4_ADDRESSES.objects, unplaced: S4_ADDRESSES.unplaced }, args: {}, into: S4_ADDRESSES.ledger }] },
    { name: 'CheckHoles', Calculations: [{ call: 'fn.lab.s4.checkholes', with: { ledger: S4_ADDRESSES.ledger, holes: S4_ADDRESSES.objects, binding: S4_ADDRESSES.binding }, args: {}, into: S4_ADDRESSES.summary }] }
  ]);
}

export function runS4(lab) {
  const composition = s4Document(lab), { run, receipt } = lab.run('S4', composition);
  const invariants = s4InvariantDocument(lab);
  lab.run('S4.invariants', invariants);
  return {
    run, receipt, composition, invariants,
    numbers: lab.get(S4_ADDRESSES.numbers), binding: lab.get(S4_ADDRESSES.binding),
    holes: lab.get(S4_ADDRESSES.objects), unplaced: lab.get(S4_ADDRESSES.unplaced),
    ledger: lab.get(S4_ADDRESSES.ledger), summary: lab.get(S4_ADDRESSES.summary)
  };
}
