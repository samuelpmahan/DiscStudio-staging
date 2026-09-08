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
