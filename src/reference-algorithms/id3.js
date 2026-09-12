/** A binary-pixel ID3 lesson. Arithmetic and model changes are ordinary LAB Calculations. */
import { freeze } from '../domain.js';
import { digestOf } from '../lab/lab.js';
import { fromDiscStudioReceipt, validate } from '../../pyto/viewer/adapters.js';

const snapshot = value => freeze(structuredClone(value));
const registrations = new WeakSet(), runs = new WeakMap(), names = new WeakMap();
const numericLabelOrder = (a, b) => a - b;

function checkDataset(dataset) {
 if (!dataset || !Number.isInteger(dataset.width) || !Number.isInteger(dataset.height) || dataset.width < 1 || dataset.height < 1) throw Error('id3: a positive integer image shape is required.');
 if (!Number.isFinite(dataset.threshold)) throw Error('id3: an explicit finite pixel threshold is required.');
 if (!Array.isArray(dataset.samples) || !dataset.samples.length) throw Error('id3: at least one labelled training image is required.');
 const ids = new Set();
 for (const sample of dataset.samples) {
  if (typeof sample?.id !== 'string' || !sample.id || ids.has(sample.id)) throw Error('id3: each training image needs a unique non-empty id.');
  if (!Number.isInteger(sample.label) || sample.label < 0 || sample.label > 9) throw Error('id3: labels must be digits 0 through 9.');
  checkPixels(sample.pixels, dataset.width * dataset.height); ids.add(sample.id);
 }
 return dataset;
}

function checkPixels(pixels, length) {
 if (!Array.isArray(pixels) || pixels.length !== length || Array.from({length}, (_, i) => pixels[i]).some(value => !Number.isInteger(value) || value < 0 || value > 16)) throw Error(`id3: an image needs ${length} integer pixel values from 0 through 16.`);
}

/** Shannon entropy in bits; zero-count classes contribute zero. */
export function id3Entropy(counts) {
 const values = Object.values(counts), n = values.reduce((sum, count) => sum + count, 0);
 return n ? -values.reduce((sum, count) => count ? sum + (count / n) * Math.log2(count / n) : sum, 0) : 0;
}

function classCounts(samples, labels) {
 const counts = Object.fromEntries(labels.map(label => [label, 0]));
 for (const sample of samples) counts[sample.label]++;
 return counts;
}

function majority(counts, labels) {
 return labels.reduce((best, label) => counts[label] > counts[best] ? label : best, labels[0]);
}

function group(samples, labels) {
 const counts = classCounts(samples, labels);
 return { sampleIds: samples.map(sample => sample.id), counts, entropy: id3Entropy(counts) };
}

function chooseCandidate(candidates) {
 return candidates.filter(candidate => candidate.eligible).reduce((best, candidate) => !best || candidate.gain > best.gain
  || candidate.gain === best.gain && candidate.pixel < best.pixel ? candidate : best, null);
}

/** One calculation scores every remaining categorical pixel question at one pending node. */
export function scoreId3Node({ tree, dataset, config }) {
 if (tree.phase !== 'score' || !tree.queue.length) throw Error('id3: there is no pending node to score.');
 const nodeId = tree.queue[0], node = tree.nodes[nodeId], ids = new Set(node.sampleIds);
 const samples = dataset.samples.filter(sample => ids.has(sample.id));
 const counts = classCounts(samples, config.labels), parentEntropy = id3Entropy(counts);
 const candidates = node.availablePixels.map(pixel => {
  const off = group(samples.filter(sample => sample.pixels[pixel] < config.threshold), config.labels);
  const on = group(samples.filter(sample => sample.pixels[pixel] >= config.threshold), config.labels);
  const weightedEntropy = (off.sampleIds.length * off.entropy + on.sampleIds.length * on.entropy) / samples.length;
  return {pixel, row: Math.floor(pixel / config.width), column: pixel % config.width, gain: parentEntropy - weightedEntropy, weightedEntropy,
   eligible: off.sampleIds.length > 0 && on.sampleIds.length > 0, off, on};
 });
 const scores = {nodeId, sampleIds: node.sampleIds, counts, parentEntropy, candidates,
  recommendedCandidate: parentEntropy === 0 ? null : chooseCandidate(candidates)};
 const nextTree = {...tree, phase: 'split', nodes: {...tree.nodes, [nodeId]: {...node, counts, entropy: parentEntropy}}};
 return snapshot([nextTree, scores]);
}

/** ID3 removes the selected categorical attribute on each branch. Zero gain does not imply a leaf. */
export function splitId3Node({ tree, scores, config }) {
 if (tree.phase !== 'split' || scores.nodeId !== tree.queue[0]) throw Error('id3: the split requires the scores for the next pending node.');
 const nodeId = scores.nodeId, node = tree.nodes[nodeId], nodes = {...tree.nodes}, queue = tree.queue.slice(1);
 const prediction = majority(scores.counts, config.labels);
 const eligible = scores.candidates.filter(candidate => candidate.eligible);
 const reason = scores.parentEntropy === 0 ? 'pure' : !scores.candidates.length ? 'no-features'
  : !eligible.length ? 'remaining-pixels-cannot-separate' : null;
 let selectedCandidate = null;
 if (reason) {
  nodes[nodeId] = {...node, status: 'leaf', prediction, reason};
 } else {
  // A strict numeric tie preserves the lowest pixel index because attributes are ascending.
  selectedCandidate = chooseCandidate(eligible);
  const children = {off: `${nodeId}.0`, on: `${nodeId}.1`};
  nodes[nodeId] = {...node, status: 'split', pixel: selectedCandidate.pixel, children, gain: selectedCandidate.gain};
  for (const side of ['off', 'on']) {
   const childId = children[side], branch = selectedCandidate[side], empty = branch.sampleIds.length === 0;
   nodes[childId] = {id: childId, parent: nodeId, depth: node.depth + 1, branch: side, sampleIds: branch.sampleIds,
    availablePixels: node.availablePixels.filter(pixel => pixel !== selectedCandidate.pixel), counts: branch.counts, entropy: branch.entropy,
    status: empty ? 'leaf' : 'pending', ...(empty ? {prediction, reason: 'empty-branch-parent-majority'} : {})};
   if (!empty) queue.push(childId);
  }
 }
 const decision = {nodeId, kind: reason ? 'leaf' : 'split', reason, prediction: reason ? prediction : null, selectedCandidate,
  tieRule: 'highest information gain among pixels that divide the examples; exact ties use the lowest pixel index', majorityTieRule: 'lowest digit label'};
 return snapshot([{...tree, nodes, queue, phase: queue.length ? 'score' : 'complete'}, decision]);
}

/** Prediction is a separate computation over one named image and one retained tree snapshot. */
export function predictId3({ tree, image, config }) {
 checkPixels(image.pixels, config.width * config.height);
 const visited = []; let nodeId = tree.root;
 for (let depth = 0; depth <= config.width * config.height + 1; depth++) {
  const node = tree.nodes[nodeId];
  if (!node) throw Error(`id3: tree node '${nodeId}' is missing.`);
  if (node.status === 'pending') {
   visited.push({nodeId, status: 'pending'});
   return snapshot({status: 'unresolved', prediction: null, visited, reason: 'The path reached an unexpanded node.'});
  }
  if (node.status === 'leaf') {
   visited.push({nodeId, status: 'leaf', prediction: node.prediction, reason: node.reason});
   return snapshot({status: 'prediction', prediction: node.prediction, visited, reason: node.reason});
  }
  const value = image.pixels[node.pixel], on = value >= config.threshold, nextNodeId = node.children[on ? 'on' : 'off'];
  visited.push({nodeId, status: 'split', pixel: node.pixel, value, threshold: config.threshold, on, nextNodeId});
  nodeId = nextNodeId;
 }
 throw Error('id3: prediction exceeded the finite attribute depth.');
}

/** The frame copies computed Parts and their bindings; it never scores a candidate or grows a node. */
export function projectId3Frame({spec, tree, dataset, scores = null, decision = null}) {
 return snapshot({kind: 'id3', number: spec.number, label: spec.label, phase: decision?.kind || (scores ? 'scored' : 'ready'),
  tree, activeNodeId: decision?.nodeId || scores?.nodeId || tree.queue[0] || null, candidates: scores,
  selectedCandidate: decision?.selectedCandidate || null, previewCandidate: decision?.selectedCandidate || scores?.recommendedCandidate || null,
  decision, dataset, sourceAddresses: spec.sourceAddresses,
  treeAddress: spec.treeAddress, datasetAddress: spec.datasetAddress, scoresAddress: spec.scoresAddress, candidatesAddress: spec.scoresAddress,
  decisionAddress: spec.decisionAddress, receiptAddress: spec.step?.receiptAddress || null, step: spec.step});
}

export function registerId3(lab) {
 if (registrations.has(lab)) return lab;
 for (const [name, calculation] of Object.entries({score: scoreId3Node, split: splitId3Node, predict: predictId3, frame: projectId3Frame})) lab.register(`fn.lab.reference.id3.${name}`, calculation);
 registrations.add(lab); return lab;
}

/** The cursor declares and runs one single-Tick document on the retained LAB board per Next. */
export function createId3Session(lab, {dataset, name} = {}) {
 checkDataset(dataset);
 const run = (runs.get(lab) || 0) + 1, prefix = `px.reference.id3.run-${run}`, runName = name ?? `id3-${run}`;
 if (typeof runName !== 'string' || !/^[a-z0-9][a-z0-9.-]*$/.test(runName)) throw Error('id3: name must contain lowercase letters, numbers, dots or hyphens.');
 const usedNames = names.get(lab) || new Set();
 if (usedNames.has(runName) || lab.has(`${prefix}.session`) || lab.has(`px.receipt.${runName}`)) throw Error('id3: that run already exists.');
 registerId3(lab); runs.set(lab, run); usedNames.add(runName); names.set(lab, usedNames);
 const addresses = {dataset: `${prefix}.dataset`, config: `${prefix}.config`, initialTree: `${prefix}.tree.0`};
 const sessionAddress = `${prefix}.session`, labels = [...new Set(dataset.samples.map(sample => sample.label))].sort(numericLabelOrder);
 lab.put(addresses.dataset, snapshot(dataset));
 lab.put(addresses.config, snapshot({width: dataset.width, height: dataset.height, threshold: dataset.threshold, labels,
  question: 'pixel >= threshold', criterion: 'information gain (Shannon entropy, bits)', attributeKind: 'binary categorical',
  stop: ['pure labels', 'no remaining attributes', 'remaining pixels cannot separate these examples'], zeroGain: 'continue if a question divides the examples; zero gain alone does not imply a leaf',
  featureTie: 'lowest pixel index', majorityTie: 'lowest digit label', queueOrder: 'first in, first out'}));
 lab.put(addresses.initialTree, snapshot({root: 'n0', nodes: {n0: {id: 'n0', parent: null, depth: 0,
  sampleIds: dataset.samples.map(sample => sample.id), availablePixels: Array.from({length: dataset.width * dataset.height}, (_, i) => i),
  status: 'pending', counts: null, entropy: null}}, queue: ['n0'], phase: 'score'}));
 const read = () => lab.get(sessionAddress), write = value => lab.put(sessionAddress, snapshot(value));
 write({kind: 'id3', name: runName, source: {dataset_sha256: digestOf(dataset), implementation_identity: 'registered-address-only'}, addresses,
  inputAddresses: [addresses.dataset, addresses.config], treeAddress: addresses.initialTree, scoresAddress: null, decisionAddress: null,
  nextTick: 0, status: 'ready', steps: [], frames: [], records: [], compositions: [], error: null});

 function project(number, step = null) {
  const current = read(), specAddress = `${prefix}.frame-spec.${number}`, frameAddress = `${prefix}.frame.${number}`;
  const bindings = {tree: current.treeAddress, dataset: addresses.dataset};
  if (current.scoresAddress) bindings.scores = current.scoresAddress;
  if (current.decisionAddress) bindings.decision = current.decisionAddress;
  lab.put(specAddress, snapshot({number, label: step?.tick || 'Training images: no questions scored yet', step,
   sourceAddresses: Object.values(bindings), treeAddress: current.treeAddress, datasetAddress: addresses.dataset,
   scoresAddress: current.scoresAddress, decisionAddress: current.decisionAddress}));
  const frameName = `${runName}.frame-${number}`;
  lab.run(frameName, lab.document(frameName, [{name: 'ProjectID3Frame', Calculations: [{call: 'fn.lab.reference.id3.frame', with: {spec: specAddress, ...bindings}, into: frameAddress}]}]));
  lab.runRecord(frameName); write({...current, frames: [...current.frames, frameAddress]});
  return lab.get(frameAddress);
 }
 project(0);
 let pending = null, predictionCount = 0;
 function next() {
  if (pending) return pending;
  if (read().status === 'complete') return Promise.resolve(frame());
  if (read().status === 'failed') return Promise.reject(Error(read().error));
  pending = Promise.resolve().then(() => {
   const current = read(), number = current.nextTick + 1, tree = lab.get(current.treeAddress), phase = tree.phase;
   const treeAddress = `${prefix}.tree.${number}`, detailAddress = `${prefix}.${phase === 'score' ? 'scores' : 'decision'}.${number}`;
   const inputs = phase === 'score' ? {tree: current.treeAddress, dataset: addresses.dataset, config: addresses.config}
    : {tree: current.treeAddress, scores: current.scoresAddress, config: addresses.config};
   const stepName = `${runName}.step-${number}`, tickName = `${phase === 'score' ? 'Score pixel questions' : 'Choose split or leaf'} at ${tree.queue[0]}`;
   write({...current, status: 'executing'});
   try {
    const document = lab.document(stepName, [{name: tickName, Calculations: [{call: `fn.lab.reference.id3.${phase}`, with: inputs, into: [treeAddress, detailAddress]}]}]);
    const started = performance.now(); lab.run(stepName, document); const executionMs = performance.now() - started;
    const {record, address: recordAddress} = lab.runRecord(stepName), invocations = record.ticks[0].invocations;
    const stepAddress = `${prefix}.step.${number}`, step = snapshot({number, tick: tickName, phase, nodeId: tree.queue[0],
     composition: stepName, receiptAddress: `px.receipt.${stepName}`, recordAddress,
     actual_consumes: [...new Set(invocations.flatMap(inv => inv.actual_consumes))], actual_produces: [...new Set(invocations.flatMap(inv => inv.actual_produces))],
     execution_ms: executionMs, timing_scope: 'LAB run including receipt settlement; excludes projection and animation'});
    lab.put(stepAddress, step);
    const steps = [...current.steps, stepAddress], compositions = [...current.compositions, stepName];
    const ticks = compositions.flatMap(name => lab.get(`px.pql.${name}`).Ticks);
    const trace = compositions.flatMap(name => lab.get(`px.receipt.${name}`).trace);
    const cumulativeName = `${runName}.through-${number}`, aggregateAddress = `px.run.${cumulativeName}`;
    lab.put(aggregateAddress, snapshot(validate(fromDiscStudioReceipt({PrincipleComponentRender: cumulativeName, Ticks: ticks}, {trace}))));
    write({...current, nextTick: number, treeAddress, scoresAddress: phase === 'score' ? detailAddress : current.scoresAddress,
     decisionAddress: phase === 'split' ? detailAddress : null, steps, compositions, records: [...current.records, aggregateAddress], status: 'projecting'});
    const result = project(number, step);
    write({...read(), status: lab.get(treeAddress).phase === 'complete' ? 'complete' : 'ready'});
    return result;
   } catch (error) {write({...read(), status: 'failed', error: error.cause?.message || error.message}); throw error;}
  }).finally(() => {pending = null;});
  return pending;
 }
 function frame(index = read().frames.length - 1) {
  if (!Number.isInteger(index) || index < 0 || index >= read().frames.length) throw Error('id3: that frame has not been calculated.');
  return lab.get(read().frames[index]);
 }
 function predict(pixels, {frameIndex = read().frames.length - 1} = {}) {
  const config = lab.get(addresses.config);
  checkPixels(pixels, config.width * config.height);
  const source = frame(frameIndex), index = ++predictionCount, name = `${runName}.prediction-${index}`;
  const imageAddress = `${prefix}.prediction.${index}.image`, resultAddress = `${prefix}.prediction.${index}.result`;
  lab.put(imageAddress, snapshot({width: config.width, height: config.height, pixels}));
  lab.run(name, lab.document(name, [{name: 'Follow learned pixel questions', Calculations: [{call: 'fn.lab.reference.id3.predict',
   with: {tree: source.treeAddress, image: imageAddress, config: addresses.config}, into: resultAddress}]}]));
  const {record, address: recordAddress} = lab.runRecord(name);
  return Object.freeze({result: lab.get(resultAddress), resultAddress, imageAddress, treeAddress: source.treeAddress, record, recordAddress});
 }
 return Object.freeze({kind: 'id3', addresses, sessionAddress, get state() {return read();},
  get recordAddress() {return read().records.at(-1) || null;}, get record() {return this.recordAddress ? lab.get(this.recordAddress) : null;},
  frame, next, predict, async all() {while (read().status !== 'complete') await next(); return frame();}});
}
