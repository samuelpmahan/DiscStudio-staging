import { createHash } from 'node:crypto';
import { createExecBoard, pxFn, readPql, invokePql } from '../../src/core/exec.js';
import { freeze, stable } from '../../src/domain.js';

export const digest = value => createHash('sha256').update(stable(value)).digest('hex');
export function copyJson(value) {
  return JSON.parse(JSON.stringify(value, (_key, item) => {
    if (['undefined', 'function', 'symbol', 'bigint'].includes(typeof item) || typeof item === 'number' && !Number.isFinite(item)) throw new Error('Shadow inputs must be finite JSON data');
    return item;
  }));
}
export function capture({ request }) {
  const value = copyJson(request);
  if (!Number.isSafeInteger(value.sequence) || value.sequence < 1 || !/^r\d+$/.test(value.id)) throw new Error('Invalid request identity');
  if (!['card', 'scene'].includes(value.method) || !Array.isArray(value.args) || !value.world || typeof value.world !== 'object' || Array.isArray(value.world)) throw new Error('A request needs world, card/scene method and args array');
  return { ...value, inputDigest: digest({ world: value.world, method: value.method, args: value.args }) };
}
export function validatePolicy(policy = {}) {
  const out = { sampleEvery: 3, primaryTimeoutMs: 10000, referenceTimeoutMs: 5000, negativeControlAt: null, ...policy };
  for (const key of ['sampleEvery', 'primaryTimeoutMs', 'referenceTimeoutMs']) if (!Number.isSafeInteger(out[key]) || out[key] < 1 || out[key] > 2147483647) throw new Error(`Invalid ${key}`);
  if (out.negativeControlAt !== null && (!Number.isSafeInteger(out.negativeControlAt) || out.negativeControlAt < 1)) throw new Error('Invalid negativeControlAt');
  return { ...out, maxReferenceInFlight: 1, onMismatch: 'reference-for-rest-of-session', onUnavailable: 'unknown-not-agreement' };
}
export function select({ request, policy, routing, capacity, sources }) {
  const serving = routing.serving, sampled = serving === 'primary' && (request.sequence - 1) % policy.sampleEvery === 0;
  const check = !sampled ? 'not-sampled' : !capacity.available ? 'reference-unavailable' : capacity.busy ? 'budget-exhausted' : 'pending';
  return { requestId: request.id, serving, sourceId: sources[serving].fingerprint, routingReason: routing.reason, routingCause: routing.cause, sampled, check: serving === 'reference' ? 'reference-served' : check };
}
export function corrupt({ primary }) {
  const end = primary.value.svg.lastIndexOf('</svg>');
  if (end < 0) throw new Error('Negative control requires an SVG closing tag');
  const label = '<rect x="0" y="0" width="100%" height="36" fill="#b00020"/><text x="8" y="25" fill="white" font-size="18">DELIBERATE NEGATIVE CONTROL</text>';
  return { ...primary, value: { ...primary.value, svg: primary.value.svg.slice(0, end) + label + primary.value.svg.slice(end) }, negativeControl: true };
}
export function compare({ request, primary, reference, sources }) {
  const common = { requestId: request.id, inputDigest: request.inputDigest, negativeControl: primary.negativeControl === true, contract: 'json-output-except-top-level-run@1' };
  if (primary.status !== 'ok' || reference.status !== 'ok') return { ...common, status: 'unknown', reason: reference.error ?? primary.error ?? 'Output unavailable', differingKeys: [] };
  if (primary.requestId !== request.id || reference.requestId !== request.id || primary.inputDigest !== request.inputDigest || reference.inputDigest !== request.inputDigest || primary.sourceId !== sources.primary.fingerprint || reference.sourceId !== sources.reference.fingerprint) return { ...common, status: 'unknown', reason: 'Request/input/source identity mismatch', differingKeys: [] };
  if (typeof primary.value?.svg !== 'string' || !primary.value.svg || typeof reference.value?.svg !== 'string' || !reference.value.svg) return { ...common, status: 'unknown', reason: 'Missing rendered SVG', differingKeys: [] };
  const keys = [...new Set([...Object.keys(primary.value), ...Object.keys(reference.value)])].sort();
  const differingKeys = keys.filter(key => Object.hasOwn(primary.value, key) !== Object.hasOwn(reference.value, key) || stable(primary.value[key]) !== stable(reference.value[key]));
  return { ...common, status: differingKeys.length ? 'mismatch' : 'matched', reason: differingKeys.length ? 'Declared outputs differ; the reference is not an oracle' : 'Declared outputs agree for this request', differingKeys, primaryDigest: digest(primary.value), referenceDigest: digest(reference.value) };
}
export function route({ routing, comparison }) {
  return comparison.status === 'mismatch' ? { serving: 'reference', reason: 'observed-mismatch', cause: comparison.requestId } : { ...routing };
}
export function summarize({ observations, routing }) {
  const rows = Object.entries(observations).filter(([address]) => address.endsWith('.capture')).map(([address, request]) => {
    const prefix = address.slice(0, -'capture'.length), selection = observations[prefix + 'selection'];
    const delivery = observations[prefix + 'delivery'], comparison = observations[prefix + 'comparison'];
    return { id: request.id, label: request.label, inputDigest: request.inputDigest, serving: selection?.serving ?? null, delivered: !!delivery, status: comparison?.status ?? (delivery ? 'pending' : 'primary-error'), negativeControl: comparison?.negativeControl ?? false, differingKeys: comparison?.differingKeys ?? [], primaryMs: delivery?.elapsedMs ?? null, reason: comparison?.reason ?? observations[prefix + 'primary']?.error ?? 'Not completed' };
  }).sort((a, b) => a.id.localeCompare(b.id));
  const counts = {};
  for (const row of rows) counts[row.status] = (counts[row.status] ?? 0) + 1;
  return { rows, counts, routing, needsReview: rows.some(row => ['mismatch', 'unknown', 'primary-error', 'reference-unavailable'].includes(row.status)), acceptance: null, promotion: null, limitation: 'Sampled agreement is not universal correctness; reference shares rendering logic. Pixels are not checked.' };
}

/** Only the existing PxC board holds experiment observations and decisions. */
export function evidenceBoard(prefix, onPart = () => {}) {
  const pxc = createExecBoard();
  for (const [name, fn] of Object.entries({ capture, select, corrupt, compare, route, summarize })) pxc.register(pxFn(`fn.exp.shadow.${name}`), args => freeze(fn(args)));
  const publish = (suffix, value) => {
    const address = `${prefix}.${suffix}`;
    if (pxc.has(address)) throw new Error(`Refusing to overwrite ${address}`);
    pxc.set(address, freeze(copyJson(value))); onPart(address, pxc.get(address)); return address;
  };
  const calculate = (suffix, name, bindings) => {
    const address = `${prefix}.${suffix}`;
    if (pxc.has(address)) throw new Error(`Refusing to overwrite ${address}`);
    const composition = readPql(JSON.stringify({ PrincipleComponentRender: suffix, Ticks: [{ name, Calculations: [{ call: `fn.exp.shadow.${name}`, with: bindings, into: address }] }] }), JSON.parse);
    const execution = invokePql(composition, { pxc });
    onPart(address, pxc.get(address));
    // Preserve the execution's calls, bindings, actual prefix membership and
    // output digest without recursively copying already-retained Parts into it.
    const testimony = { PrincipleComponentRender: execution.PrincipleComponentRender, Ticks: execution.Ticks.map(tick => ({ name: tick.name, Calculations: tick.Calculations.map(calc => ({ call: calc.call, actualCall: calc.actualCall, with: calc.with, args: calc.args, into: calc.into, produces: calc.produces, prefixMembers: Object.fromEntries(Object.entries(calc.with).filter(([, binding]) => binding.endsWith('.*')).map(([name]) => [name, Object.keys(calc.inputs[name])])), outputDigest: digest(calc.output) })) })) };
    publish(`${suffix}.execution`, { composition, execution: testimony, retention: 'Inputs and outputs are retained as immutable addressed Parts; prefix members are captured above.' });
    return address;
  };
  return { pxc, publish, calculate, get: address => pxc.get(address) };
}
