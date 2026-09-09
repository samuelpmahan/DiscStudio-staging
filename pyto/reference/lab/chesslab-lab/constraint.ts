/** A Constraint relates computational materials through a named predicate.
 * Definitions are reusable; the caller's Tick records evaluations in PxC.
 */
export type Address = string;
export type CalculationAddress = `fn.${string}`;

export interface Measurement {
  readonly name: string;
  readonly value: number;
  readonly unit: string;
}

export interface ConstraintJudgment {
  readonly status: 'satisfied' | 'violated' | 'unknown';
  readonly reason: string;
  readonly measurements?: readonly Measurement[];
  readonly details?: Readonly<Record<string, unknown>>;
}

export interface Constraint {
  readonly kind: 'constraint';
  readonly id: string;
  readonly label: string;
  readonly materials: Readonly<Record<string, Address>>;
  readonly predicate: CalculationAddress;
  readonly basis: ConstraintBasis;
}

export interface ConstraintBasis {
  readonly observations: readonly Address[];
  readonly assumptions: readonly Address[];
}

export interface ConstraintGroup {
  readonly kind: 'constraint-group';
  readonly id: string;
  readonly label: string;
  readonly operator: 'all' | 'any';
  readonly members: readonly ConstraintNode[];
}

export type ConstraintNode = Constraint | ConstraintGroup;

/** The materials a predicate receives after its declared addresses resolve. */
export interface PredicateInputs {
  readonly materials: Readonly<Record<string, unknown>>;
  readonly observations: Readonly<Record<Address, unknown>>;
  readonly assumptions: Readonly<Record<Address, unknown>>;
}

export type ConstraintPredicate = (input: PredicateInputs) => ConstraintJudgment;

/** Structural read-only PxC surface; constraint evaluation never writes. */
export interface PxCReader {
  has(address: Address): boolean;
  get<T>(address: Address): T;
  call<Args, Result>(calculation: { readonly address: CalculationAddress }, args: Args): Result;
}
export type ConstraintReader = PxCReader;
/** Compatibility alias for earlier consumers. */
export type Judgment = ConstraintJudgment;
export type ConstraintPredicateInput = PredicateInputs;

export interface ConstraintEvaluation extends ConstraintJudgment {
  readonly constraint: ConstraintNode;
  /** Addresses actually read. A missing dependency prevents all reads. */
  readonly reads: readonly Address[];
  readonly missing: readonly Address[];
  readonly children?: readonly ConstraintEvaluation[];
}

const unique = (addresses: readonly Address[]): Address[] => [...new Set(addresses)];
const requiredAddresses = (constraint: Constraint): Address[] => unique([
  ...Object.values(constraint.materials),
  ...constraint.basis.observations,
  ...constraint.basis.assumptions
]);

function unknown(reason: string, details?: Readonly<Record<string, unknown>>): ConstraintJudgment {
  return { status: 'unknown', reason, ...(details ? { details } : {}) };
}

function evaluateLeaf(reader: PxCReader, constraint: Constraint): ConstraintEvaluation {
  const required = requiredAddresses(constraint);
  const missing = required.filter(address => !reader.has(address));
  if (missing.length) {
    return { constraint, ...unknown(`Required materials unavailable: ${missing.join(', ')}`), reads: [], missing };
  }

  const values = new Map<Address, unknown>();
  for (const address of required) values.set(address, reader.get(address));
  const byAddress = (addresses: readonly Address[]): Readonly<Record<Address, unknown>> => Object.fromEntries(addresses.map(address => [address, values.get(address)]));
  const materials = Object.fromEntries(Object.entries(constraint.materials).map(([name, address]) => [name, values.get(address)]));
  const judgment = reader.call<PredicateInputs, ConstraintJudgment>({address: constraint.predicate}, {
    materials,
    observations: byAddress(constraint.basis.observations),
    assumptions: byAddress(constraint.basis.assumptions)
  });
  return { constraint, ...judgment, reads: required, missing: [] };
}

function groupJudgment(group: ConstraintGroup, members: readonly ConstraintEvaluation[]): ConstraintJudgment {
  if (!members.length) throw new Error(`Constraint group '${group.id}' has no members.`);
  const statuses = members.map(member => member.status);
  if (group.operator === 'all') {
    if (statuses.includes('violated')) return { status: 'violated', reason: `At least one member of '${group.label}' is violated.` };
    if (statuses.every(status => status === 'satisfied')) return { status: 'satisfied', reason: `All members of '${group.label}' are satisfied.` };
    return { status: 'unknown', reason: `No member of '${group.label}' is violated, but at least one is unknown.` };
  }
  if (statuses.includes('satisfied')) return { status: 'satisfied', reason: `At least one member of '${group.label}' is satisfied.` };
  if (statuses.every(status => status === 'violated')) return { status: 'violated', reason: `All members of '${group.label}' are violated.` };
  return { status: 'unknown', reason: `No member of '${group.label}' is satisfied, but at least one is unknown.` };
}

/** Evaluates declarative constraints only; callers retain ownership of every board write. */
export function evaluateConstraint(reader: PxCReader, constraint: ConstraintNode): ConstraintEvaluation {
  if (constraint.kind === 'constraint') return evaluateLeaf(reader, constraint);
  if (!constraint.members.length) throw new Error(`Constraint group '${constraint.id}' has no members.`);
  const members = constraint.members.map(member => evaluateConstraint(reader, member));
  return {
    constraint,
    ...groupJudgment(constraint, members),
    reads: unique(members.flatMap(member => member.reads)),
    missing: unique(members.flatMap(member => member.missing)),
    children: members
  };
}
