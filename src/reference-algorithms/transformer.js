/**
 * A fixed-weight, single-head encoder-layer teaching fixture. It implements the
 * equations in Vaswani et al., sections 3.1--3.3: scaled dot-product
 * self-attention, post-residual layer normalization, and a position-wise ReLU
 * feed-forward network. LayerNorm uses the fixed teaching simplification
 * gamma=1 and beta=0. This is deliberately not a trainable model or framework.
 */
import { createLab } from '../lab/lab.js';

const runs = new WeakMap();
const compositionNames = new WeakMap();

function dense(values, label) {
  if (!Array.isArray(values) || Array.from({ length: values.length }, (_, index) => Object.hasOwn(values, index)).some(present => !present)) {
    throw new Error(`transformer: ${label} must be a dense array.`);
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
    throw new Error(`transformer: ${label} contains a non-finite number.`);
  }
  return value;
}

function snapshot(value) {
  if (Array.isArray(value)) return Object.freeze(value.map(snapshot));
  if (value && typeof value === 'object') return Object.freeze(Object.fromEntries(Object.entries(value).map(([key, entry]) => [key, snapshot(entry)])));
  return value;
}

const matrix = (rows, label) => {
  if (!Array.isArray(rows) || !rows.length || !dense(rows, label).every(Array.isArray) || !dense(rows[0], label).length) throw new Error(`transformer: ${label} must be a non-empty matrix.`);
  const columns = rows[0].length;
  if (!rows.every(row => dense(row, label).length === columns && row.every(Number.isFinite))) throw new Error(`transformer: ${label} must be rectangular and finite.`);
  return rows;
};

const vector = (values, length, label) => {
  if (!Array.isArray(values) || dense(values, label).length !== length || !values.every(Number.isFinite)) throw new Error(`transformer: ${label} must be ${length} finite numbers.`);
  return values;
};

const shapeOf = values => [values.length, values[0].length];
const transpose = values => values[0].map((_, column) => values.map(row => row[column]));
function multiply(left, right, label) {
  matrix(left, `${label} left`); matrix(right, `${label} right`);
  if (left[0].length !== right.length) throw new Error(`transformer: ${label} has incompatible matrix dimensions.`);
  return finitePart(left.map(row => right[0].map((_, column) => {
    let sum = 0;
    for (let index = 0; index < row.length; index += 1) {
      const product = row[index] * right[index][column];
      if (!Number.isFinite(product)) throw new Error(`transformer: ${label} multiplication overflowed to a non-finite number.`);
      sum += product;
      if (!Number.isFinite(sum)) throw new Error(`transformer: ${label} accumulation overflowed to a non-finite number.`);
    }
    return sum;
  })), label);
}
const add = (left, right, label = 'addition') => {
  matrix(left, `${label} left`); matrix(right, `${label} right`);
  if (shapeOf(left).join(',') !== shapeOf(right).join(',')) throw new Error(`transformer: ${label} has incompatible matrix dimensions.`);
  return finitePart(left.map((row, rowIndex) => row.map((value, column) => {
    const sum = value + right[rowIndex][column];
    if (!Number.isFinite(sum)) throw new Error(`transformer: ${label} overflowed to a non-finite number.`);
    return sum;
  })), label);
};
const addBias = (values, bias, label = 'bias addition') => {
  matrix(values, `${label} values`); vector(bias, values[0].length, `${label} bias`);
  return finitePart(values.map(row => row.map((value, column) => {
    const sum = value + bias[column];
    if (!Number.isFinite(sum)) throw new Error(`transformer: ${label} overflowed to a non-finite number.`);
    return sum;
  })), label);
};
const relu = values => finitePart(values.map(row => row.map(value => Math.max(0, value))), 'ReLU output');
const part = (values, extra = {}) => {
  matrix(values, 'produced values');
  finitePart({ values, ...extra }, 'produced part');
  return snapshot({ values, shape: shapeOf(values), ...extra });
};

/** Stable per-row softmax: subtracting the row maximum does not change weights. */
function rowSoftmax(values) {
  matrix(values, 'softmax input');
  return values.map(row => {
    const maximum = Math.max(...row);
    const exponents = row.map(value => {
      const delta = value - maximum;
      if (!Number.isFinite(delta)) throw new Error('transformer: softmax subtraction produced a non-finite number.');
      const exponent = Math.exp(delta);
      if (!Number.isFinite(exponent)) throw new Error('transformer: softmax exponential produced a non-finite number.');
      return exponent;
    });
    let denominator = 0;
    for (const exponent of exponents) {
      denominator += exponent;
      if (!Number.isFinite(denominator)) throw new Error('transformer: softmax denominator is non-finite.');
    }
    if (denominator <= 0) throw new Error('transformer: softmax denominator is non-finite.');
    return exponents.map(value => {
      const probability = value / denominator;
      if (!Number.isFinite(probability)) throw new Error('transformer: softmax output is non-finite.');
      return probability;
    });
  });
}

function normalized(values, epsilon) {
  matrix(values, 'normalization input');
  return values.map(row => {
    let total = 0;
    for (const value of row) {
      total += value;
      if (!Number.isFinite(total)) throw new Error('transformer: normalization mean overflowed to a non-finite number.');
    }
    const mean = total / row.length;
    if (!Number.isFinite(mean)) throw new Error('transformer: normalization mean is non-finite.');
    let squared = 0;
    for (const value of row) {
      const difference = value - mean;
      if (!Number.isFinite(difference)) throw new Error('transformer: normalization difference is non-finite.');
      const square = difference ** 2;
      if (!Number.isFinite(square)) throw new Error('transformer: normalization square overflowed to a non-finite number.');
      squared += square;
      if (!Number.isFinite(squared)) throw new Error('transformer: normalization variance overflowed to a non-finite number.');
    }
    const variance = squared / row.length, scale = Math.sqrt(variance + epsilon);
    if (!Number.isFinite(variance) || !Number.isFinite(scale) || scale <= 0) throw new Error('transformer: normalization scale is non-finite.');
    const output = row.map(value => {
      const normalizedValue = (value - mean) / scale;
      if (!Number.isFinite(normalizedValue)) throw new Error('transformer: normalized output is non-finite.');
      return normalizedValue;
    });
    return { mean, variance, values: output };
  });
}

export const TRANSFORMER_DEFAULT_INPUT = snapshot([
  [1, 0],
  [0, 1]
]);

/** Small identity weights make the attention and residual arithmetic inspectable. */
export const TRANSFORMER_DEFAULT_WEIGHTS = snapshot({
  query: [[1, 0], [0, 1]],
  key: [[1, 0], [0, 1]],
  value: [[1, 0], [0, 1]],
  output: [[1, 0], [0, 1]],
  ffn1: [[1, 0], [0, 1]],
  ffn1Bias: [0, 0],
  ffn2: [[1, 0], [0, 1]],
  ffn2Bias: [0, 0]
});

export const TRANSFORMER_DEFAULT_PARAMETERS = snapshot({ epsilon: 1e-5, gamma: 1, beta: 0 });

export const TRANSFORMER_ADDRESSES = Object.freeze({
  input: run => `px.reference.transformer.run-${run}.input`,
  weights: run => `px.reference.transformer.run-${run}.weights`,
  parameters: run => `px.reference.transformer.run-${run}.parameters`,
  query: run => `px.reference.transformer.run-${run}.attention.query`,
  key: run => `px.reference.transformer.run-${run}.attention.key`,
  value: run => `px.reference.transformer.run-${run}.attention.value`,
  scores: run => `px.reference.transformer.run-${run}.attention.scores`,
  scaledScores: run => `px.reference.transformer.run-${run}.attention.scaled-scores`,
  softmax: run => `px.reference.transformer.run-${run}.attention.softmax`,
  context: run => `px.reference.transformer.run-${run}.attention.context`,
  attentionOutput: run => `px.reference.transformer.run-${run}.attention.output`,
  residual1: run => `px.reference.transformer.run-${run}.norm1.residual`,
  norm1: run => `px.reference.transformer.run-${run}.norm1.normalized`,
  ffnHidden: run => `px.reference.transformer.run-${run}.ffn.hidden`,
  ffnActivated: run => `px.reference.transformer.run-${run}.ffn.activated`,
  ffnOutput: run => `px.reference.transformer.run-${run}.ffn.output`,
  residual2: run => `px.reference.transformer.run-${run}.norm2.residual`,
  norm2: run => `px.reference.transformer.run-${run}.norm2.normalized`,
  output: run => `px.reference.transformer.run-${run}.output`
});

function checked(input, weights, parameters) {
  matrix(input, 'input');
  const [, dModel] = shapeOf(input);
  for (const name of ['query', 'key', 'value', 'output', 'ffn1', 'ffn2']) matrix(weights?.[name], `weights.${name}`);
  const dKey = weights.query[0].length, dValue = weights.value[0].length, dFfn = weights.ffn1[0].length;
  if (weights.query.length !== dModel || weights.key.length !== dModel || weights.value.length !== dModel) throw new Error('transformer: Q, K, and V weights must start at d_model.');
  if (weights.key[0].length !== dKey) throw new Error('transformer: Q and K must share d_k.');
  if (weights.output.length !== dValue || weights.output[0].length !== dModel) throw new Error('transformer: output weight must map d_v to d_model.');
  if (weights.ffn1.length !== dModel || weights.ffn2.length !== dFfn || weights.ffn2[0].length !== dModel) throw new Error('transformer: FFN weights must map d_model → d_ff → d_model.');
  vector(weights.ffn1Bias, dFfn, 'weights.ffn1Bias');
  vector(weights.ffn2Bias, dModel, 'weights.ffn2Bias');
  checkNormalizationParameters(parameters);
  return { dKey };
}

function checkNormalizationParameters(parameters) {
  if (!Number.isFinite(parameters?.epsilon) || parameters.epsilon <= 0) throw new Error('transformer: parameters.epsilon must be a positive finite number.');
  if ((parameters?.gamma ?? 1) !== 1 || (parameters?.beta ?? 0) !== 0) throw new Error('transformer: layer normalization is fixed with gamma=1 and beta=0.');
}

function weightSnapshot(overrides) {
  if (overrides !== undefined && (!overrides || typeof overrides !== 'object' || Array.isArray(overrides))) throw new Error('transformer: weights must be an object of matrix/vector overrides.');
  return snapshot({ ...TRANSFORMER_DEFAULT_WEIGHTS, ...(overrides ?? {}) });
}

function parameterSnapshot(overrides) {
  if (overrides !== undefined && (!overrides || typeof overrides !== 'object' || Array.isArray(overrides))) throw new Error('transformer: parameters must be an object.');
  return snapshot({ ...TRANSFORMER_DEFAULT_PARAMETERS, ...(overrides ?? {}) });
}

export function transformerProject({ input, weights }) {
  checked(input, weights, TRANSFORMER_DEFAULT_PARAMETERS);
  return [
    part(multiply(input, weights.query, 'Q projection'), { projection: 'Q' }),
    part(multiply(input, weights.key, 'K projection'), { projection: 'K' }),
    part(multiply(input, weights.value, 'V projection'), { projection: 'V' })
  ];
}

export function transformerAttend({ query, key, value, weights }) {
  matrix(query?.values, 'query.values'); matrix(key?.values, 'key.values'); matrix(value?.values, 'value.values');
  const dKey = query.values[0].length;
  if (key.values[0].length !== dKey) throw new Error('transformer: Q and K Parts must share d_k.');
  if (key.values.length !== query.values.length || value.values.length !== query.values.length) throw new Error('transformer: Q, K, and V must have the same token-row count.');
  matrix(weights?.output, 'weights.output');
  if (weights.output.length !== value.values[0].length) throw new Error('transformer: output weight must start at d_v.');
  const scores = multiply(query.values, transpose(key.values), 'attention scores');
  const scaledScores = finitePart(scores.map(row => row.map(value => value / Math.sqrt(dKey))), 'scaled attention scores');
  const softmax = rowSoftmax(scaledScores);
  const context = multiply(softmax, value.values, 'attention context');
  const output = multiply(context, weights.output, 'attention output projection');
  return [
    part(scores, { operation: 'QK^T' }),
    part(scaledScores, { operation: 'QK^T / sqrt(d_k)', dKey }),
    part(softmax, { operation: 'stable row softmax' }),
    part(context, { operation: 'softmax(scores) V' }),
    part(output, { operation: 'context W^O' })
  ];
}

export function transformerNorm1({ input, attentionOutput, parameters }) {
  matrix(input, 'input'); matrix(attentionOutput?.values, 'attentionOutput.values');
  if (shapeOf(input).join(',') !== shapeOf(attentionOutput.values).join(',')) throw new Error('transformer: attention output must match input d_model shape.');
  checkNormalizationParameters(parameters);
  const residual = add(input, attentionOutput.values, 'input + attention output'), details = normalized(residual, parameters.epsilon);
  return [
    part(residual, { operation: 'input + attention output' }),
    snapshot({ values: details.map(row => row.values), shape: shapeOf(residual), mean: details.map(row => row.mean), variance: details.map(row => row.variance), epsilon: parameters.epsilon, gamma: 1, beta: 0, operation: 'LayerNorm(residual)' })
  ];
}

export function transformerFfn({ norm1, weights }) {
  matrix(norm1?.values, 'norm1.values');
  const dModel = norm1.values[0].length;
  matrix(weights?.ffn1, 'weights.ffn1'); matrix(weights?.ffn2, 'weights.ffn2');
  const dFfn = weights.ffn1[0].length;
  if (weights.ffn1.length !== dModel || weights.ffn2.length !== dFfn || weights.ffn2[0].length !== dModel) throw new Error('transformer: FFN weights must map normalized d_model values through d_ff and back.');
  vector(weights.ffn1Bias, dFfn, 'weights.ffn1Bias'); vector(weights.ffn2Bias, dModel, 'weights.ffn2Bias');
  const hidden = addBias(multiply(norm1.values, weights.ffn1, 'FFN first projection'), weights.ffn1Bias, 'FFN first bias');
  const activated = relu(hidden), output = addBias(multiply(activated, weights.ffn2, 'FFN second projection'), weights.ffn2Bias, 'FFN second bias');
  return [part(hidden, { operation: 'x W1 + b1' }), part(activated, { operation: 'ReLU(hidden)' }), part(output, { operation: 'ReLU(hidden) W2 + b2' })];
}

export function transformerNorm2({ norm1, ffnOutput, parameters }) {
  matrix(norm1?.values, 'norm1.values'); matrix(ffnOutput?.values, 'ffnOutput.values');
  if (shapeOf(norm1.values).join(',') !== shapeOf(ffnOutput.values).join(',')) throw new Error('transformer: FFN output must match normalized d_model shape.');
  checkNormalizationParameters(parameters);
  const residual = add(norm1.values, ffnOutput.values, 'norm1 + FFN output'), details = normalized(residual, parameters.epsilon);
  const norm = snapshot({ values: details.map(row => row.values), shape: shapeOf(residual), mean: details.map(row => row.mean), variance: details.map(row => row.variance), epsilon: parameters.epsilon, gamma: 1, beta: 0, operation: 'LayerNorm(residual)' });
  return [part(residual, { operation: 'norm1 + FFN output' }), norm, snapshot({ values: norm.values, shape: norm.shape, source: 'norm2.normalized', explanation: 'fixed-weight single-head post-LN encoder-layer output' })];
}

/** Register the five, intentionally small PxC Calculations on an existing board. */
export function registerTransformer(lab) {
  lab.register('fn.lab.reference.transformer.project', transformerProject);
  lab.register('fn.lab.reference.transformer.attend', transformerAttend);
  lab.register('fn.lab.reference.transformer.norm1', transformerNorm1);
  lab.register('fn.lab.reference.transformer.ffn', transformerFfn);
  lab.register('fn.lab.reference.transformer.norm2', transformerNorm2);
  return lab;
}

export function transformerDocument(run, name = `transformer-${run}`) {
  const at = TRANSFORMER_ADDRESSES;
  return {
    composition: name,
    Ticks: [
      { name: 'TransformerProject', Calculations: [{ call: 'fn.lab.reference.transformer.project', with: { input: at.input(run), weights: at.weights(run) }, args: {}, into: [at.query(run), at.key(run), at.value(run)] }] },
      { name: 'TransformerAttend', Calculations: [{ call: 'fn.lab.reference.transformer.attend', with: { query: at.query(run), key: at.key(run), value: at.value(run), weights: at.weights(run) }, args: {}, into: [at.scores(run), at.scaledScores(run), at.softmax(run), at.context(run), at.attentionOutput(run)] }] },
      { name: 'TransformerNorm1', Calculations: [{ call: 'fn.lab.reference.transformer.norm1', with: { input: at.input(run), attentionOutput: at.attentionOutput(run), parameters: at.parameters(run) }, args: {}, into: [at.residual1(run), at.norm1(run)] }] },
      { name: 'TransformerFfn', Calculations: [{ call: 'fn.lab.reference.transformer.ffn', with: { norm1: at.norm1(run), weights: at.weights(run) }, args: {}, into: [at.ffnHidden(run), at.ffnActivated(run), at.ffnOutput(run)] }] },
      { name: 'TransformerNorm2', Calculations: [{ call: 'fn.lab.reference.transformer.norm2', with: { norm1: at.norm1(run), ffnOutput: at.ffnOutput(run), parameters: at.parameters(run) }, args: {}, into: [at.residual2(run), at.norm2(run), at.output(run)] }] }
    ]
  };
}

/** Validate and reserve input/parameter snapshots and PQL, without executing it. */
export function prepareTransformer(lab, { input = TRANSFORMER_DEFAULT_INPUT, weights, parameters, run = null, name = null } = {}) {
  const next = runs.get(lab) ?? 0;
  const runNumber = run ?? next + 1;
  if (!Number.isInteger(runNumber) || runNumber < 1) throw new Error('transformer: run must be a positive integer.');
  if (Object.values(TRANSFORMER_ADDRESSES).some(address => lab.has(address(runNumber)))) throw new Error(`transformer: run ${runNumber} already exists on this lab.`);
  const inputSnapshot = snapshot(input), weightValues = weightSnapshot(weights), parameterValues = parameterSnapshot(parameters);
  finitePart(inputSnapshot, 'input'); finitePart(weightValues, 'weights'); finitePart(parameterValues, 'parameters');
  checked(inputSnapshot, weightValues, parameterValues);
  const runName = name ?? `transformer-${runNumber}`;
  if (typeof runName !== 'string' || !runName.length) throw new Error('transformer: name must be a non-empty string.');
  const usedNames = compositionNames.get(lab) ?? new Set();
  if (usedNames.has(runName) || lab.has(`px.receipt.${runName}`)) throw new Error(`transformer: composition '${runName}' already exists on this lab.`);
  runs.set(lab, Math.max(next, runNumber)); usedNames.add(runName); compositionNames.set(lab, usedNames);
  const at = TRANSFORMER_ADDRESSES;
  lab.put(at.input(runNumber), inputSnapshot);
  lab.put(at.weights(runNumber), weightValues);
  lab.put(at.parameters(runNumber), parameterValues);
  const document = transformerDocument(runNumber, runName);
  const composition = lab.document(document.composition, document.Ticks);
  return { run: runNumber, name: runName, addresses: at, composition, input: inputSnapshot, weights: weightValues, parameters: parameterValues };
}

export function runTransformer(lab, options = {}) {
  const prepared = prepareTransformer(lab, options);
  const { run: runNumber, name: runName, composition, addresses: at, input: inputSnapshot, weights: weightValues, parameters: parameterValues } = prepared;
  const { run: executed, receipt } = lab.run(runName, composition);
  const { address: recordAddress, record } = lab.runRecord(runName);
  return {
    run: runNumber, name: runName, addresses: at, composition, executed, receipt, record, recordAddress,
    input: inputSnapshot, weights: weightValues, parameters: parameterValues,
    query: lab.get(at.query(runNumber)), key: lab.get(at.key(runNumber)), value: lab.get(at.value(runNumber)),
    scores: lab.get(at.scores(runNumber)), scaledScores: lab.get(at.scaledScores(runNumber)), softmax: lab.get(at.softmax(runNumber)), context: lab.get(at.context(runNumber)), attentionOutput: lab.get(at.attentionOutput(runNumber)),
    residual1: lab.get(at.residual1(runNumber)), norm1: lab.get(at.norm1(runNumber)), ffnHidden: lab.get(at.ffnHidden(runNumber)), ffnActivated: lab.get(at.ffnActivated(runNumber)), ffnOutput: lab.get(at.ffnOutput(runNumber)), residual2: lab.get(at.residual2(runNumber)), norm2: lab.get(at.norm2(runNumber)), output: lab.get(at.output(runNumber))
  };
}

export function createTransformerLab() {
  return registerTransformer(createLab());
}
