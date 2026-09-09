/** Evaluate readonly, evidence-backed constraints against a PxC store. */

const STATUS = new Set(['satisfied', 'violated', 'unknown']);

function isAddress(value) {
  return typeof value === 'string' && value.length > 0;
}

function assertBasis(basis) {
  if (basis === null || typeof basis !== 'object' || Array.isArray(basis)
      || !Array.isArray(basis.observations) || !Array.isArray(basis.assumptions)
      || !basis.observations.every(isAddress) || !basis.assumptions.every(isAddress)) {
    throw new TypeError('Constraint basis requires observations and assumptions arrays of PxC addresses.');
  }
}

function assertLeaf(node) {
  if (node === null || typeof node !== 'object' || Array.isArray(node)
      || node.kind !== 'constraint' || !isAddress(node.id) || !isAddress(node.label)
      || node.materials === null || typeof node.materials !== 'object' || Array.isArray(node.materials)
      || !isAddress(node.predicate) || !node.predicate.startsWith('fn.')) {
    throw new TypeError('Invalid constraint definition.');
  }
  if (!Object.entries(node.materials).every(([name, address]) => isAddress(name) && isAddress(address))) {
    throw new TypeError('Constraint materials must map semantic names to PxC addresses.');
  }
  assertBasis(node.basis);
}

function assertGroup(node) {
  if (node === null || typeof node !== 'object' || Array.isArray(node)
      || node.kind !== 'constraint-group' || !isAddress(node.id) || !isAddress(node.label)
      || (node.operator !== 'all' && node.operator !== 'any') || !Array.isArray(node.members)) {
    throw new TypeError('Invalid constraint group definition.');
  }
  if (node.members.length === 0) throw new RangeError('Constraint group members must not be empty.');
}

function addRead(reads, address) {
  if (!reads.includes(address)) reads.push(address);
}

function readAddress(pxc, address, reads, missing) {
  if (!pxc.has(address)) {
    if (!missing.includes(address)) missing.push(address);
    return undefined;
  }
  addRead(reads, address);
  return pxc.get(address);
}

function normalizePredicateResult(value, constraint, reads, missing) {
  if (typeof value === 'boolean') {
    return {
      status: value ? 'satisfied' : 'violated',
      reason: value ? 'predicate satisfied' : 'predicate violated',
      constraint, reads, missing,
    };
  }
  if (value === null || typeof value !== 'object' || Array.isArray(value) || !STATUS.has(value.status)) {
    throw new TypeError('Constraint predicate must return a boolean or a judgment with a valid status.');
  }
  const result = {
    status: value.status,
    reason: typeof value.reason === 'string' ? value.reason : `predicate ${value.status}`,
    constraint, reads, missing,
  };
  if (Object.hasOwn(value, 'measurements')) result.measurements = value.measurements;
  if (Object.hasOwn(value, 'details')) result.details = value.details;
  return result;
}

function evaluateLeaf(pxc, node) {
  assertLeaf(node);
  const reads = [], missing = [];
  const materials = Object.fromEntries(Object.entries(node.materials).map(([name,address]) =>
    [name, readAddress(pxc,address,reads,missing)]));
  const observations = Object.fromEntries(node.basis.observations.map(address =>
    [address, readAddress(pxc,address,reads,missing)]));
  const assumptions = Object.fromEntries(node.basis.assumptions.map(address =>
    [address, readAddress(pxc,address,reads,missing)]));
  if (missing.length > 0) {
    return { status: 'unknown', reason: 'missing material or basis', constraint: node.id, reads, missing };
  }

  addRead(reads, node.predicate);
  // Deliberately uncaught: registered-calculation failures are runtime errors.
  return normalizePredicateResult(
    pxc.call(node.predicate, { materials, observations, assumptions }), node.id, reads, missing,
  );
}

function evaluateGroup(pxc, node) {
  assertGroup(node);
  const children = node.members.map((member) => evaluateConstraint(pxc, member));
  const reads = [], missing = [];
  for (const child of children) {
    for (const address of child.reads) addRead(reads, address);
    for (const address of child.missing) if (!missing.includes(address)) missing.push(address);
  }
  const statuses = children.map(({ status }) => status);
  const status = node.operator === 'all'
    ? (statuses.includes('violated') ? 'violated' : statuses.includes('unknown') ? 'unknown' : 'satisfied')
    : (statuses.includes('satisfied') ? 'satisfied' : statuses.includes('unknown') ? 'unknown' : 'violated');
  return { status, reason: `${node.operator} group ${status}`, constraint: node.id, reads, missing, children };
}

/** Evaluate a valid constraint definition without changing PxC state. */
export function evaluateConstraint(pxc, node) {
  if (node?.kind === 'constraint') return evaluateLeaf(pxc, node);
  if (node?.kind === 'constraint-group') return evaluateGroup(pxc, node);
  throw new TypeError('Expected a constraint or constraint-group.');
}

export default evaluateConstraint;
