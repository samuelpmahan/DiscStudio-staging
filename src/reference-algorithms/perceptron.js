/**
 * A deliberately small, teaching/reference perceptron.  The values written by
 * this module are ordinary PxC Parts; the only computation happens in the two
 * registered Calculations and their PQL composition.
 */

const runs = new WeakMap();
const compositionNames = new WeakMap();

function freeze(value) {
  if (value && typeof value === 'object' && !Object.isFrozen(value)) {
    Object.values(value).forEach(freeze);
    Object.freeze(value);
  }
  return value;
}

function dense(values, label) {
  if (!Array.isArray(values) || Array.from({ length: values.length }, (_, index) => Object.hasOwn(values, index)).some(present => !present)) {
    throw new Error(`perceptron: ${label} must be a dense array.`);
  }
  return values;
}

function finitePart(value, label = 'part') {
  if (Array.isArray(value)) {
    dense(value, label);
    value.forEach(entry => finitePart(entry, label));
  } else if (value && typeof value === 'object') {
    Object.values(value).forEach(entry => finitePart(entry, label));
  } else if (typeof value === 'number' && !Number.isFinite(value)) {
    throw new Error(`perceptron: ${label} contains a non-finite number.`);
  }
  return freeze(value);
}

function calculationContributions({ features, weights, bias }) {
  if (!Array.isArray(features) || !Array.isArray(weights) || features.length !== weights.length) {
    throw new Error('perceptron: features and weights must be equal-length arrays.');
  }
  dense(features, 'features'); dense(weights, 'weights');
  if (!bias || !Number.isFinite(bias.value)) throw new Error('perceptron: numeric inputs are required.');
  if (![...features, ...weights].every(Number.isFinite)) throw new Error('perceptron: numeric inputs are required.');
  const contributions = features.map((input, index) => {
    const product = input * weights[index];
    if (!Number.isFinite(product)) throw new Error('perceptron: contribution overflowed to a non-finite number.');
    return { index, input, weight: weights[index], product };
  });
  let value = bias.value;
  for (const contribution of contributions) {
    value += contribution.product;
    if (!Number.isFinite(value)) throw new Error('perceptron: weighted sum overflowed to a non-finite number.');
  }
  return [finitePart(contributions, 'contributions'), finitePart({ bias: bias.value, contributions, value }, 'weighted sum')];
}

function calculationActivate({ weightedSum, threshold }) {
  if (!weightedSum || !Number.isFinite(weightedSum.value) || !Number.isFinite(threshold?.value)) throw new Error('perceptron: weighted sum and threshold must be numeric.');
  const value = weightedSum.value >= threshold.value ? 1 : 0;
  return [finitePart({ threshold: threshold.value, weightedSum: weightedSum.value, value }, 'activation'), finitePart({ value, class: value ? 'positive' : 'negative' }, 'output')];
}

/** Register the two reference Calculations on an existing LAB board. */
export function registerPerceptron(lab) {
  lab.register('fn.lab.reference.perceptron.contributions', calculationContributions);
  lab.register('fn.lab.reference.perceptron.activate', calculationActivate);
  return lab;
}

/**
 * Snapshot inputs, compose the reference through PQL, and settle its real
 * receipt/runRecord.  Call registerPerceptron(lab) once before running.
 */
export function preparePerceptron(lab, { features, weights, bias = 0, threshold = 0, name, run = null } = {}) {
  if (!Array.isArray(features) || !Array.isArray(weights) || features.length !== weights.length) throw new Error('perceptron: features and weights must be equal-length arrays.');
  dense(features, 'features'); dense(weights, 'weights');
  if (![...features, ...weights, bias, threshold].every(Number.isFinite)) throw new Error('perceptron: numeric inputs are required.');
  const next = runs.get(lab) || 0;
  const runNumber = run ?? next + 1;
  if (!Number.isInteger(runNumber) || runNumber < 1) throw new Error('perceptron: run must be a positive integer.');
  const runName = name ?? `perceptron-${runNumber}`;
  if (typeof runName !== 'string' || !runName.length) throw new Error('perceptron: name must be a non-empty string.');
  const prefix = `px.reference.perceptron.run-${runNumber}`;
  const runAddresses = ['input.features', 'weights.features', 'bias', 'threshold', 'contributions', 'weighted-sum', 'activation', 'output'];
  if (runAddresses.some(suffix => lab.has(`${prefix}.${suffix}`))) throw new Error(`perceptron: run ${runNumber} already exists on this lab.`);
  const usedNames = compositionNames.get(lab) ?? new Set();
  if (usedNames.has(runName) || lab.has(`px.receipt.${runName}`) || lab.has(`px.run.${runName}`)) throw new Error(`perceptron: composition '${runName}' already exists on this lab.`);
  const featureSnapshot = freeze([...features]), weightSnapshot = freeze([...weights]);
  const biasSnapshot = freeze({ value: bias }), thresholdSnapshot = freeze({ value: threshold });
  const addresses = {
    features: `${prefix}.input.features`,
    weights: `${prefix}.weights.features`,
    bias: `${prefix}.bias`,
    threshold: `${prefix}.threshold`,
    contributions: `${prefix}.contributions`,
    weightedSum: `${prefix}.weighted-sum`,
    activation: `${prefix}.activation`,
    output: `${prefix}.output`
  };
  // Each is a distinct frozen snapshot, so subsequent caller mutation cannot
  // change a completed run.
  runs.set(lab, Math.max(next, runNumber));
  lab.put(addresses.features, featureSnapshot);
  lab.put(addresses.weights, weightSnapshot);
  lab.put(addresses.bias, biasSnapshot);
  lab.put(addresses.threshold, thresholdSnapshot);

  const composition = lab.document(runName, [
    { name: 'PerceptronContributions', Calculations: [{
      call: 'fn.lab.reference.perceptron.contributions',
      with: { features: addresses.features, weights: addresses.weights, bias: addresses.bias },
      into: [addresses.contributions, addresses.weightedSum]
    }] },
    { name: 'PerceptronActivation', Calculations: [{
      call: 'fn.lab.reference.perceptron.activate',
      with: { weightedSum: addresses.weightedSum, threshold: addresses.threshold },
      into: [addresses.activation, addresses.output]
    }] }
  ]);
  usedNames.add(runName); compositionNames.set(lab, usedNames);
  return { name: runName, runNumber, addresses, composition };
}

export function runPerceptron(lab, options = {}) {
  const prepared = preparePerceptron(lab, options);
  const { name: runName, addresses, composition } = prepared;
  const { run: executed, receipt } = lab.run(runName, composition);
  const { address, record } = lab.runRecord(runName);
  return { ...prepared, name: runName, addresses, composition, run: executed, receipt, record, recordAddress: address };
}
