/**
 * A DiscBattle, composed the way a Competition is: reusable Constraints with
 * parameters (src/constraints.js), plus the one Calculation that scores the
 * states those Constraints describe. Everything here is pure over its inputs --
 * runtime.js is the only place that knows which Part each argument comes from,
 * and every number a card shows was produced by `battleStandings` on the record.
 */
import { TIE_MODES, rulePoints } from './constraints.js';

/**
 * The templates a person picks instead of assembling rules by hand. Applying one
 * is a single command, so undoing it is one sentence.
 */
export const battleTemplates = {
  open: {
    id: 'open', name: 'Open comparison · authored scores only',
    about: 'No cap and no points. Scores, highlight and winner stay exactly what you author.',
    constraints: []
  },
  'cap5-top3': {
    id: 'cap5-top3', name: '5-disc cap · top 3 score 3, 2, 1',
    about: 'Five discs in the battle. On every hole the best three take 3, 2 and 1 points; a tie shares the tied places evenly.',
    constraints: [
      { id: 'disc-cap', kind: 'discCap', value: 5, enabled: true },
      { id: 'places', kind: 'placesPoints', value: 3, points: [3, 2, 1], mode: 'low', enabled: true },
      { id: 'ties', kind: 'tieRule', value: 1, mode: 'share', enabled: true }
    ]
  },
  'cap3-one': {
    id: 'cap3-one', name: '3-disc cap · the hole is worth 1',
    about: 'Three discs; one point to the best on each hole and nothing to the others.',
    constraints: [
      { id: 'disc-cap', kind: 'discCap', value: 3, enabled: true },
      { id: 'places', kind: 'placesPoints', value: 1, points: [1], mode: 'low', enabled: true },
      { id: 'ties', kind: 'tieRule', value: 1, mode: 'share', enabled: true }
    ]
  },
  'cap8-far': {
    id: 'cap8-far', name: '8-disc cap · furthest scores 5, 3, 2, 1',
    about: 'Eight discs, measured rather than counted: the four longest take 5, 3, 2 and 1, so a higher number is better.',
    constraints: [
      { id: 'disc-cap', kind: 'discCap', value: 8, enabled: true },
      { id: 'places', kind: 'placesPoints', value: 4, points: [5, 3, 2, 1], mode: 'high', enabled: true },
      { id: 'ties', kind: 'tieRule', value: 1, mode: 'share', enabled: true }
    ]
  }
};

/** What the enabled Constraints say the scoring is. Derived here, so it is derived on the record. */
export function schemeFrom(rules = []) {
  const places = rules.find(r => r.enabled && r.kind === 'placesPoints') ?? null;
  const ties = rules.find(r => r.enabled && r.kind === 'tieRule') ?? null;
  const cap = rules.find(r => r.enabled && r.kind === 'discCap') ?? null;
  const tie = ties?.mode ?? 'share';
  return {
    ranked: !!places, points: places ? rulePoints(places) : [],
    mode: places?.mode === 'high' ? 'high' : 'low',
    tie: Object.hasOwn(TIE_MODES, tie) ? tie : 'share',
    cap: cap ? cap.value : null
  };
}

/**
 * `fn.battle.standings`: ranks from the scores, points from the places scheme,
 * and a running total across the states in order, up to and including the one
 * being rendered. Nothing is invented: with no places Constraint enabled every
 * points value is null and the table is the lineup, untouched.
 */
export function battleStandings({ material, rules = [] }) {
  const scheme = schemeFrom(rules), entries = material.entries ?? [];
  const totals = Object.fromEntries(entries.map(e => [e.id, 0]));
  const states = (material.states ?? []).map(state => {
    const scored = entries.map(e => ({ entryId: e.id, discId: e.discId, name: e.name, score: state.scores?.[e.id] ?? null })).filter(r => Number.isFinite(r.score));
    const order = [...scored].sort((a, b) => scheme.mode === 'high' ? b.score - a.score : a.score - b.score);
    const rows = [];
    for (let i = 0; i < order.length;) {
      let end = i; while (end + 1 < order.length && order[end + 1].score === order[i].score) end++;
      const size = end - i + 1, slice = scheme.points.slice(i, i + size), sum = slice.reduce((a, b) => a + b, 0);
      const award = !scheme.ranked ? 0 : size === 1 || scheme.tie === 'none' || scheme.tie === 'best' ? (scheme.points[i] ?? 0) : Math.round((sum / size) * 100) / 100;
      for (let k = i; k <= end; k++) rows.push({ ...order[k], place: i + 1, tied: size > 1, points: award });
      i = end + 1;
    }
    for (const row of rows) totals[row.entryId] += row.points;
    return { id: state.id, name: state.name, entered: scored.length, of: entries.length, complete: entries.length > 0 && scored.length === entries.length, unresolvedTie: scheme.tie === 'none' && rows.some(r => r.tied), rows, totals: { ...totals } };
  });
  const current = states.find(s => s.id === material.currentStateId) ?? states.at(-1) ?? null;
  const running = current?.totals ?? totals;
  const table = entries.map(entry => {
    const row = current?.rows.find(r => r.entryId === entry.id) ?? null;
    return { entryId: entry.id, discId: entry.discId, name: entry.name, score: row?.score ?? null, place: row?.place ?? null, tied: row?.tied ?? false, points: scheme.ranked && row ? row.points : null, total: scheme.ranked ? (running[entry.id] ?? 0) : null };
  }).sort((a, b) => (b.total ?? 0) - (a.total ?? 0) || (a.place ?? 99) - (b.place ?? 99));
  let standing = 0, previous = null;
  table.forEach((row, index) => { if (row.total !== previous) { standing = index + 1; previous = row.total; } row.standing = scheme.ranked ? standing : null; });
  return { scheme, states, table, through: current?.id ?? null, sentence: standingsSentence({ scheme, table, current }) };
}

/** One plain line a person can read off the panel, and the same line the receipt carries. */
export function standingsSentence({ scheme, table, current }) {
  if (!scheme.ranked) return 'No points scheme is enabled: the scores and the winner are exactly what you authored.';
  const places = scheme.points.join(', ');
  const how = `top ${scheme.points.length} score ${places}; ${scheme.mode === 'high' ? 'higher' : 'lower'} score wins`;
  if (!current || !current.entered) return `Nothing entered for ${current ? current.name : 'this state'} yet (${how}).`;
  const leaders = table.filter(row => row.standing === 1);
  const who = leaders.length === 1 ? leaders[0].name : `${leaders.length} discs`;
  return `Through ${current.name}: ${who} lead${leaders.length === 1 ? 's' : ''} on ${leaders[0].total} point${leaders[0].total === 1 ? '' : 's'} (${how}).`;
}

/**
 * `fn.battle.entry`: the BattleEntry a card binds, read off the standings rather
 * than assembled beside them, so `entry.points`, `entry.place` and
 * `entry.total` on a card are the same numbers the standings panel shows.
 */
export function battleEntry({ standings, battle, entryId, stateId }) {
  const state = battle.states.find(s => s.id === stateId) ?? battle.states.find(s => s.id === battle.currentStateId);
  if (!state) throw new Error('Comparison state is missing.');
  const row = standings.states.find(s => s.id === state.id)?.rows.find(r => r.entryId === entryId) ?? null;
  const standing = standings.table.find(t => t.entryId === entryId) ?? null;
  return {
    id: entryId, score: state.scores[entryId] ?? null,
    highlighted: state.highlight === entryId, winner: state.winners.includes(entryId),
    place: row?.place ?? null, tied: row?.tied ?? false,
    points: standings.scheme.ranked && row ? row.points : null,
    total: standings.scheme.ranked ? (standing?.total ?? null) : null,
    standing: standings.scheme.ranked ? (standing?.standing ?? null) : null
  };
}

/**
 * Tapping the finishing order. The tapped disc takes the next free place; tapping
 * one that already has a place takes it out and closes the gap behind it. The
 * places ARE the scores (1 = first in), so a hole entered by tapping and a hole
 * typed into the score boxes are the same recorded fact, and undo is one step.
 */
export function placeOrder({ state, entries, entryId }) {
  const ordered = entries.map(e => ({ id: e.id, score: state.scores[e.id] })).filter(r => Number.isFinite(r.score)).sort((a, b) => a.score - b.score);
  const without = ordered.filter(r => r.id !== entryId);
  const next = ordered.some(r => r.id === entryId) ? without : [...without, { id: entryId }];
  const scores = Object.fromEntries(entries.map(e => [e.id, null]));
  next.forEach((row, index) => { scores[row.id] = index + 1; });
  return scores;
}
