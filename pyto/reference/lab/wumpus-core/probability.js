/**
 * Pure weighted-belief helpers for small material/calculation experiments.
 * Inputs are iterable records with an optional finite non-negative `weight`.
 */

function asItems(items) {
  if (items == null || typeof items[Symbol.iterator] !== 'function') {
    throw new TypeError('items must be iterable');
  }
  return [...items];
}

function priorOf(item, index) {
  if (!item || typeof item !== 'object' || Array.isArray(item)) {
    throw new TypeError(`items[${index}] must be an object`);
  }
  const weight = item.weight === undefined ? 1 : item.weight;
  if (typeof weight !== 'number' || !Number.isFinite(weight) || weight < 0) {
    throw new TypeError(`items[${index}].weight must be a finite non-negative number`);
  }
  return weight;
}

function requireLikelihood(value, index) {
  if (typeof value !== 'number' || !Number.isFinite(value) || value < 0) {
    throw new TypeError(`likelihood for items[${index}] must be a finite non-negative number`);
  }
  return value;
}

/**
 * Apply a non-negative likelihood function and normalize posterior weights.
 * Every input record is shallow-copied, preserving metadata and replacing its
 * optional `weight` with the normalized posterior. Inputs are never mutated.
 */
export function conditionWeights(items, likelihood) {
  const source = asItems(items);
  if (typeof likelihood !== 'function') throw new TypeError('likelihood must be a function');
  const weighted = source.map((item, index) => {
    const prior = priorOf(item, index);
    const value = requireLikelihood(likelihood(item, index), index);
    return { item, mass: prior * value };
  });
  const total = weighted.reduce((sum, entry) => sum + entry.mass, 0);
  if (!(total > 0) || !Number.isFinite(total)) {
    throw new RangeError('conditionWeights requires a positive finite total weight');
  }
  return Object.freeze(weighted.map(({ item, mass }) => Object.freeze({ ...item, weight: mass / total })));
}

/**
 * Return the normalized weighted mass of records accepted by `predicate`.
 * Missing weights default to 1. The input is not changed.
 */
export function marginalProbability(items, predicate) {
  const source = asItems(items);
  if (typeof predicate !== 'function') throw new TypeError('predicate must be a function');
  let total = 0;
  let accepted = 0;
  for (const [index, item] of source.entries()) {
    const weight = priorOf(item, index);
    total += weight;
    if (predicate(item, index)) accepted += weight;
  }
  if (!(total > 0) || !Number.isFinite(total)) {
    throw new RangeError('marginalProbability requires a positive finite total weight');
  }
  return accepted / total;
}
