/**
 * A deliberately small, hand-authored decision tree.  The tree is a normal
 * PxC composition: callers can inspect the snapshots, comparisons, path and
 * leaf on the board, as well as the receipt made by createLab().
 */
import { createLab } from '../lab/lab.js';

export const DECISION_TREE_ADDRESSES = Object.freeze({
  input: run => `px.reference.decision-tree.run-${run}.input`,
  parameters: run => `px.reference.decision-tree.run-${run}.parameters`,
  root: run => `px.reference.decision-tree.run-${run}.tree.root`,
  branch: run => `px.reference.decision-tree.run-${run}.tree.branch`,
  path: run => `px.reference.decision-tree.run-${run}.tree.path`,
  leaf: run => `px.reference.decision-tree.run-${run}.tree.leaf`
});

const copy = value => {
  if (Array.isArray(value)) return Object.freeze(value.map(copy));
  if (value && typeof value === 'object') return Object.freeze(Object.fromEntries(Object.entries(value).map(([key, entry]) => [key, copy(entry)])));
  return value;
};

function finitePart(value, label = 'part') {
  if (Array.isArray(value)) {
    for (let index = 0; index < value.length; index += 1) {
      if (!Object.hasOwn(value, index)) throw new Error(`decision tree: ${label} must not contain sparse arrays.`);
      finitePart(value[index], label);
    }
  } else if (value && typeof value === 'object') {
    Object.values(value).forEach(entry => finitePart(entry, label));
  } else if (typeof value === 'number' && !Number.isFinite(value)) {
    throw new Error(`decision tree: ${label} contains a non-finite number.`);
  }
  return copy(value);
}

function inputValue(input) {
  const value = typeof input === 'number' ? input : input?.value;
  if (!Number.isFinite(value)) throw new Error('decision tree: input.value must be a finite number.');
  return value;
}

function thresholds(parameters) {
  const root = parameters?.rootThreshold ?? parameters?.root ?? 5;
  const branch = parameters?.branchThreshold ?? parameters?.branch ?? 10;
  if (!Number.isFinite(root) || !Number.isFinite(branch)) throw new Error('decision tree: thresholds must be finite numbers.');
  return { rootThreshold: root, branchThreshold: branch };
}

export function treeRoot({ input, parameters }) {
  const value = inputValue(input), { rootThreshold } = thresholds(parameters);
  return finitePart({ feature: 'value', operator: '<', value, threshold: rootThreshold, outcome: value < rootThreshold ? 'left' : 'right' }, 'root');
}

export function treeBranch({ input, parameters, root }) {
  const value = inputValue(input), { branchThreshold } = thresholds(parameters);
  if (!root || !['left', 'right'].includes(root.outcome)) throw new Error('decision tree: root outcome is required.');
  if (root.outcome === 'left') return finitePart({ feature: 'value', comparison: 'bypassed', parent: root.outcome, outcome: 'low' }, 'branch');
  const branch = value < branchThreshold ? 'middle' : 'high';
  return finitePart({ feature: 'value', operator: '<', value, threshold: branchThreshold, comparison: 'value < branch threshold', parent: root.outcome, outcome: branch }, 'branch');
}

export function treePath({ root, branch }) {
  if (!root || !branch || typeof root.outcome !== 'string' || typeof branch.outcome !== 'string') throw new Error('decision tree: root and branch outcomes are required.');
  return finitePart({ decisions: [root.outcome, branch.outcome], comparisons: ['value < root threshold', branch.comparison ?? 'value < branch threshold'], labels: ['root', branch.outcome], leaf: branch.outcome }, 'path');
}

export function treeLeaf({ input, parameters, root, branch, path }) {
  if (!root || !branch || !path || !Array.isArray(path.decisions)) throw new Error('decision tree: root, branch and path are required.');
  const branchText = root.outcome === 'left' ? `second comparison bypassed; then ${branch.outcome}` : `then ${branch.outcome}`;
  return finitePart({ value: inputValue(input), thresholds: thresholds(parameters), path: path.decisions, label: branch.outcome, explanation: `value ${root.outcome === 'left' ? '<' : '>='} root threshold; ${branchText}` }, 'leaf');
}

export function registerDecisionTree(lab) {
  lab.register('fn.lab.reference.tree.root', treeRoot);
  lab.register('fn.lab.reference.tree.branch', treeBranch);
  lab.register('fn.lab.reference.tree.path', treePath);
  lab.register('fn.lab.reference.tree.leaf', treeLeaf);
  return lab;
}

export function decisionTreeDocument(run) {
  const at = DECISION_TREE_ADDRESSES;
  return {
    composition: `decision-tree-run-${run}`,
    Ticks: [
      { name: 'Root', Calculations: [{ call: 'fn.lab.reference.tree.root', with: { input: at.input(run), parameters: at.parameters(run) }, args: {}, into: at.root(run) }] },
      { name: 'Branch', Calculations: [{ call: 'fn.lab.reference.tree.branch', with: { input: at.input(run), parameters: at.parameters(run), root: at.root(run) }, args: {}, into: at.branch(run) }] },
      { name: 'Path', Calculations: [{ call: 'fn.lab.reference.tree.path', with: { root: at.root(run), branch: at.branch(run) }, args: {}, into: at.path(run) }] },
      { name: 'Leaf', Calculations: [{ call: 'fn.lab.reference.tree.leaf', with: { input: at.input(run), parameters: at.parameters(run), root: at.root(run), branch: at.branch(run), path: at.path(run) }, args: {}, into: at.leaf(run) }] }
    ]
  };
}

const nextRunByLab = new WeakMap();
export function prepareDecisionTree(lab, { input, value, parameters = {}, run = null } = {}) {
  const runNumber = run ?? ((nextRunByLab.get(lab) ?? 0) + 1);
  if (!Number.isInteger(runNumber) || runNumber < 1) throw new Error('decision tree: run must be a positive integer.');
  const sourceInput = input ?? { value };
  inputValue(sourceInput);
  const inputSnapshot = finitePart(typeof sourceInput === 'number' ? { value: sourceInput } : sourceInput, 'input');
  const parameterSnapshot = copy(thresholds(parameters));
  const addresses = DECISION_TREE_ADDRESSES;
  if (Object.values(addresses).some(address => lab.has(address(runNumber)))) throw new Error(`decision tree: run ${runNumber} already exists on this lab.`);
  nextRunByLab.set(lab, Math.max(nextRunByLab.get(lab) ?? 0, runNumber));
  lab.put(addresses.input(runNumber), inputSnapshot);
  lab.put(addresses.parameters(runNumber), parameterSnapshot);
  const document = decisionTreeDocument(runNumber);
  const composition = lab.document(document.composition, document.Ticks);
  return { name: document.composition, run: runNumber, addresses, composition, input: inputSnapshot, parameters: parameterSnapshot };
}

export function runDecisionTree(lab, options = {}) {
  const prepared = prepareDecisionTree(lab, options);
  const { name, run: runNumber, addresses, composition } = prepared;
  const { run: executed, receipt } = lab.run(name, composition);
  const { address: recordAddress, record } = lab.runRecord(name);
  return { ...prepared, executed, receipt, record, recordAddress, root: lab.get(addresses.root(runNumber)), branch: lab.get(addresses.branch(runNumber)), path: lab.get(addresses.path(runNumber)), leaf: lab.get(addresses.leaf(runNumber)) };
}

export function createDecisionTreeLab() {
  const lab = createLab();
  registerDecisionTree(lab);
  return lab;
}
