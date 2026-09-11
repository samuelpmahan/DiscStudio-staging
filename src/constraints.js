/** Reusable domain predicates, not parsed code or a competition-specific validation pipeline. */
export const constraintDefinitions = {
  bagLimit: { label: 'Each bag: maximum discs', description: 'Count physical disc references in every participating team’s bag.', call: 'fn.constraint.bagLimit', defaultValue: 5, unit: 'discs per bag' },
  oneMold: { label: 'Each bag: one mold', description: 'Distinct mold identities, not display-name strings. Empty bags are pending.', call: 'fn.constraint.oneMold', defaultValue: 1, unit: 'distinct mold' },
  teamThrows: { label: 'Each team: throws per round', description: 'Exactly this many recorded throws when a round is complete; too many fails immediately.', call: 'fn.constraint.teamThrows', defaultValue: 3, unit: 'throws / team / round' }
};
const result = (subject, status, message, actual, expected) => ({ subject, status, message, actual, expected });
export function bagLimit({ material, rule }) {
  return material.teams.map(t => {
    const b = material.bags[t.bagId];
    if (!b) return result(t.name, 'fail', 'Referenced bag is missing.', null, rule.value);
    const missing = b.discIds.filter(id => !material.discs[id]);
    return result(b.name, missing.length || b.discIds.length > rule.value ? 'fail' : 'pass', missing.length ? `Missing disc references: ${missing.join(', ')}` : `${b.discIds.length} / ${rule.value} discs`, b.discIds.length, rule.value);
  });
}
export function oneMold({ material, rule }) {
  return material.teams.map(t => {
    const b = material.bags[t.bagId]; if (!b) return result(t.name, 'fail', 'Referenced bag is missing.', null, 1);
    const ds = b.discIds.map(id => material.discs[id]);
    if (ds.some(d => !d || !material.molds[d.moldId])) return result(b.name, 'fail', 'A disc or its mold identity is unresolved.', null, 1);
    const count = new Set(ds.map(d => d.moldId)).size;
    return result(b.name, count === 0 ? 'pending' : count === 1 ? 'pass' : 'fail', `${count} distinct mold${count === 1 ? '' : 's'}`, count, 1);
  });
}
export function teamThrows({ material, rule }) {
  return material.rounds.flatMap(round => material.teams.map(team => {
    const throws = material.throws.filter(t => t.roundId === round.id && t.teamId === team.id), n = throws.length;
    const bag = material.bags[team.bagId];
    const invalid = throws.some(t => !material.discs[t.discId] || !bag?.discIds.includes(t.discId));
    const status = invalid || n > rule.value || round.complete && n !== rule.value ? 'fail' : n === rule.value ? 'pass' : 'pending';
    return result(`${round.name} · ${team.name}`, status, invalid ? 'A recorded throw references a missing or non-bag disc.' : `${n} / ${rule.value} throws${!round.complete && n < rule.value ? ' · round open' : ''}`, n, rule.value);
  }));
}
export function combineConstraints({ results, combine = 'all' }) {
  const rules = Object.entries(results).map(([id, details]) => ({ id, details, status: !details.length ? 'pending' : details.some(d => d.status === 'fail') ? 'fail' : details.some(d => d.status === 'pending') ? 'pending' : 'pass' }));
  const statuses = rules.map(r => r.status);
  const status = !rules.length ? 'unconstrained' : combine === 'any' ? statuses.includes('pass') ? 'pass' : statuses.includes('pending') ? 'pending' : 'fail' : statuses.includes('fail') ? 'fail' : statuses.includes('pending') ? 'pending' : 'pass';
  return { status, combine, rules };
}

/* ------------------------------------------------------------------ */
/* the Constraints a DiscBattle is composed from                        */
/* ------------------------------------------------------------------ */
/**
 * A battle is composed the way a competition is -- Competition[Constraint] --
 * from these three, each with its own parameters. They read one material: the
 * battle's lineup and its states. `discCap` is also read by the domain, so
 * adding a disc past the cap is refused with the same sentence the panel shows.
 */
export const battleConstraintDefinitions = {
  discCap: { label: 'The battle: at most N discs', description: 'Count the discs in the lineup. Adding one past the cap is refused by name, never silently dropped.', call: 'fn.constraint.discCap', defaultValue: 5, unit: 'discs in the battle' },
  placesPoints: { label: 'The places: the top K score P1…PK', description: 'Each state is a hole: the finishing order scores by the scheme, and everyone below the last scoring place takes nothing.', call: 'fn.constraint.placesPoints', defaultValue: 3, unit: 'scoring places' },
  tieRule: { label: 'A tie: what the shared place is worth', description: 'Two discs on one score take the same place. This says what that place pays.', call: 'fn.constraint.tieRule', defaultValue: 1, unit: 'rule' }
};
/** How a tie is paid, and which direction a score runs. Both are parameters of a Constraint, not settings. */
export const TIE_MODES = { share: 'Share the tied places’ points evenly', best: 'Each takes the better place’s points', none: 'Leave it: a tie is not resolved here' };
export const SCORE_MODES = { low: 'Lower score wins (strokes)', high: 'Higher score wins (distance, points)' };
/** The points a places Constraint pays, one per place: as authored, or N, N-1 … 1 when none was authored. */
export const rulePoints = rule => Array.isArray(rule.points) && rule.points.length ? rule.points.slice(0, rule.value) : Array.from({ length: rule.value }, (_, index) => rule.value - index);
/** Every battle Constraint, checked by name before it can enter a world. */
export function validateBattleRule(rule) {
  if (!rule || !Object.hasOwn(battleConstraintDefinitions, rule.kind)) throw new Error(`Unknown battle constraint '${rule?.kind}'.`);
  if (typeof rule.id !== 'string' || !/^[A-Za-z][A-Za-z0-9_-]{0,99}$/.test(rule.id) || typeof rule.enabled !== 'boolean') throw new Error('A battle constraint needs an id and an enabled flag.');
  if (!Number.isInteger(rule.value) || rule.value < 1 || rule.value > 12) throw new Error('A battle constraint counts from 1 to 12: a comparison holds at most twelve discs.');
  if (rule.kind === 'placesPoints') {
    if (!Array.isArray(rule.points) || rule.points.length !== rule.value) throw new Error('The points scheme needs exactly one number per scoring place.');
    if (rule.points.some(points => !Number.isInteger(points) || points < 0 || points > 100)) throw new Error('Points are whole numbers from 0 to 100.');
    if (rule.points.some((points, index) => index && points > rule.points[index - 1])) throw new Error('A later place cannot score more than an earlier one.');
    if (!Object.hasOwn(SCORE_MODES, rule.mode ?? 'low')) throw new Error('A score runs low-wins or high-wins.');
  }
  if (rule.kind === 'tieRule' && !Object.hasOwn(TIE_MODES, rule.mode ?? 'share')) throw new Error('A tie is shared, taken at best, or left.');
  return rule;
}
const plural = (n, word) => `${n} ${word}${n === 1 ? '' : 's'}`;
export function discCap({ material, rule }) {
  const n = material.entries.length;
  return [result('The battle', n > rule.value ? 'fail' : n === rule.value ? 'pass' : 'pending', n > rule.value ? `${n} discs is past the cap of ${rule.value}. Remove ${plural(n - rule.value, 'disc')}.` : `${n} / ${rule.value} discs${n === rule.value ? ' · the cap is full' : ` · room for ${plural(rule.value - n, 'more disc')}`}`, n, rule.value)];
}
export function placesPoints({ material, rule }) {
  const points = rulePoints(rule), short = points.length > material.entries.length;
  const scheme = result('Points scheme', short ? 'pending' : 'pass', short ? `${plural(points.length, 'scoring place')} and only ${plural(material.entries.length, 'disc')} in the battle.` : `${plural(points.length, 'place')} · ${points.join(', ')} pt · ${(SCORE_MODES[rule.mode ?? 'low'])}`, points.length, material.entries.length);
  return [scheme, ...material.states.map(state => {
    const entered = material.entries.filter(entry => Number.isFinite(state.scores?.[entry.id])).length, of = material.entries.length;
    return result(state.name, !of ? 'pending' : entered === of ? 'pass' : 'pending', `${entered} / ${of} results entered${entered === of ? ' · scored' : ''}`, entered, of);
  })];
}
export function tieRule({ material, rule }) {
  const mode = rule.mode ?? 'share';
  return material.states.map(state => {
    const scores = material.entries.map(entry => state.scores?.[entry.id]).filter(Number.isFinite);
    const tied = scores.length - new Set(scores).size;
    return result(state.name, !tied ? 'pass' : mode === 'none' ? 'fail' : 'pass', !tied ? 'No tie' : `${plural(tied, 'tied result')} · ${TIE_MODES[mode]}`, tied, 0);
  });
}
