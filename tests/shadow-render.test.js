import test from 'node:test';
import assert from 'node:assert/strict';
import { resolve } from 'node:path';
import { capture, compare, validatePolicy } from '../experiments/shadow-render/model.mjs';
import { ShadowSession } from '../experiments/shadow-render/session.mjs';
import { WorkerPeer } from '../experiments/shadow-render/worker-peer.mjs';
import { json, verifySeal } from '../experiments/card-render/lib.mjs';

const sources = { primary: { fingerprint: 'candidate' }, reference: { fingerprint: 'baseline' } };
const spec = { label: 'example', method: 'card', args: ['disc'], world: { value: 1 } };
const deferred = () => { let resolve, reject; const promise = new Promise((a, b) => { resolve = a; reject = b; }); return { promise, resolve, reject }; };
class FakePeer {
  constructor(source, handler = async request => ({ svg: `<svg>${request.world.value}</svg>` })) { this.source = source; this.handler = handler; this.busy = false; this.available = true; this.calls = []; }
  async run(request) {
    if (this.busy) throw new Error('Fake worker busy');
    this.busy = true; this.calls.push(request);
    try { const value = await this.handler(request); return { status: 'ok', requestId: request.id, inputDigest: request.inputDigest, sourceId: this.source.fingerprint, value, receipt: { run: { computed: this.source.fingerprint === 'baseline' ? 1 : 0 } }, elapsedMs: 1 }; }
    finally { this.busy = false; }
  }
  async close() { this.available = false; }
}
function fixture(options = {}) {
  const primary = options.primary ?? new FakePeer(sources.primary), reference = options.reference ?? new FakePeer(sources.reference);
  return { primary, reference, session: new ShadowSession({ sources, primary, reference, ...options }) };
}

test('capture owns a finite JSON snapshot and rejects unsupported methods', () => {
  const input = structuredClone(spec), result = capture({ request: { ...input, id: 'r1', sequence: 1 } });
  input.world.value = 9; assert.equal(result.world.value, 1);
  assert.throws(() => capture({ request: { ...spec, id: 'r1', sequence: 1, method: 'dispatch' } }), /card\/scene/);
  assert.throws(() => capture({ request: { ...spec, id: 'r1', sequence: 1, args: [NaN] } }), /finite JSON/);
  assert.throws(() => validatePolicy({ sampleEvery: 0 }), /sampleEvery/);
});

test('primary is delivered while checker remains unresolved; same captured input goes to both', async () => {
  const gate = deferred(), events = [], reference = new FakePeer(sources.reference, async request => { await gate.promise; return { svg: `<svg>${request.world.value}</svg>` }; });
  const { session, primary } = fixture({ reference, onPart: (address, value) => events.push({ address, value }) });
  try {
    const request = structuredClone(spec), pending = session.submit(request); request.world.value = 99;
    const delivered = await pending;
    assert.equal(delivered.value.svg, '<svg>1</svg>'); assert.equal(reference.busy, true);
    assert.equal(session.summary().rows[0].status, 'pending');
    assert.deepEqual(primary.calls[0], reference.calls[0]);
    gate.resolve(); await session.drain();
    assert.equal(session.summary().rows[0].status, 'matched');
    assert.ok(events.findIndex(e => e.address.endsWith('.delivery')) < events.findIndex(e => e.address.endsWith('.comparison')));
    assert.ok(events.some(e => e.value?.composition?.Ticks?.[0]?.Calculations?.[0]?.call === 'fn.exp.shadow.compare'));
  } finally { gate.resolve(); await session.close(); }
});

test('sampling and an occupied reference budget are explicit, never agreement', async () => {
  const gate = deferred(), reference = new FakePeer(sources.reference, async () => { await gate.promise; return { svg: '<svg>1</svg>' }; });
  const { session } = fixture({ reference, policy: { sampleEvery: 2 } });
  try {
    await session.submit(spec); await session.submit(spec); await session.submit(spec);
    assert.deepEqual(session.summary().rows.map(r => r.status), ['pending', 'not-sampled', 'budget-exhausted']);
    assert.equal(reference.calls.length, 1); gate.resolve(); await session.drain();
    assert.equal(session.summary().counts.matched, 1);
  } finally { gate.resolve(); await session.close(); }
});

test('disagreement preserves the served result and switches later requests within this session', async () => {
  const reference = new FakePeer(sources.reference, async () => ({ svg: '<svg>reference</svg>' }));
  const { session, primary } = fixture({ reference, policy: { sampleEvery: 1 } });
  try {
    const delivered = await session.submit(spec); await session.drain();
    assert.equal(delivered.value.svg, '<svg>1</svg>');
    const next = await session.submit(spec); assert.equal(next.value.svg, '<svg>reference</svg>');
    assert.equal(primary.calls.length, 1);
    const summary = session.summary(); assert.deepEqual(summary.rows.map(r => r.status), ['mismatch', 'reference-served']);
    assert.equal(summary.routing.cause, 'r000001'); assert.equal(summary.acceptance, null);
    const inputAddress = `${session.prefix}.requests.r000001.capture`;
    assert.throws(() => { session.board.get(inputAddress).world.value = 99; }, TypeError);
  } finally { await session.close(); }
  const other = fixture(); assert.equal(other.session.summary().routing.serving, 'primary'); await other.session.close();
});

test('checker error is unknown, not mismatch or forced reference routing', async () => {
  const reference = new FakePeer(sources.reference, async () => { throw new Error('reference exploded'); });
  const { session } = fixture({ reference });
  try { await session.submit(spec); await session.drain(); const summary = session.summary(); assert.equal(summary.rows[0].status, 'unknown'); assert.match(summary.rows[0].reason, /exploded/); assert.equal(summary.routing.serving, 'primary'); }
  finally { await session.close(); }
});

test('unavailable reference is disclosed and primary failure produces no delivery', async () => {
  const reference = new FakePeer(sources.reference); reference.available = false;
  const { session } = fixture({ reference });
  try { await session.submit(spec); assert.equal(session.summary().rows[0].status, 'reference-unavailable'); assert.equal(session.summary().needsReview, true); } finally { await session.close(); }
  const failed = fixture({ primary: new FakePeer(sources.primary, async () => { throw new Error('primary failed'); }) });
  try { const result = await failed.session.submit(spec); assert.equal(result.delivered, false); assert.equal(failed.reference.calls.length, 0); assert.equal(failed.session.summary().rows[0].status, 'primary-error'); } finally { await failed.session.close(); }
});

test('malformed primary output is retained as an error, never delivered', async () => {
  const { session, reference } = fixture({ primary: new FakePeer(sources.primary, async () => ({ other: 'no SVG' })) });
  try { const result = await session.submit(spec); assert.equal(result.delivered, false); assert.equal(reference.calls.length, 0); assert.equal(session.summary().rows[0].status, 'primary-error'); }
  finally { await session.close(); }
});

test('comparison excludes execution receipts but refuses cross-request/source evidence', () => {
  const request = capture({ request: { ...spec, id: 'r1', sequence: 1 } });
  const primary = { status: 'ok', requestId: request.id, inputDigest: request.inputDigest, sourceId: 'candidate', value: { svg: '<svg/>' }, receipt: { reused: true } };
  const reference = { ...primary, sourceId: 'baseline', receipt: { reused: false } };
  assert.equal(compare({ request, primary, reference, sources }).status, 'matched');
  assert.equal(compare({ request, primary, reference: { ...reference, inputDigest: 'wrong' }, sources }).status, 'unknown');
  assert.equal(compare({ request, primary, reference: { ...reference, sourceId: 'wrong' }, sources }).status, 'unknown');
  assert.equal(compare({ request, primary, reference: { ...reference, value: {} }, sources }).status, 'unknown');
});

test('explicit negative control retains original primary and labels the derived corruption', async () => {
  const { session } = fixture({ policy: { negativeControlAt: 1 } });
  try {
    const delivered = await session.submit(spec); await session.drain();
    assert.equal(delivered.delivery.negativeControl, true);
    assert.equal(session.board.get(`${session.prefix}.requests.r000001.primary`).value.svg, '<svg>1</svg>');
    assert.equal(session.summary().rows[0].status, 'mismatch'); assert.equal(session.summary().rows[0].negativeControl, true);
  } finally { await session.close(); }
});

test('one in-flight primary is explicit and closed sessions cannot receive requests', async () => {
  const gate = deferred(), { session } = fixture({ primary: new FakePeer(sources.primary, async () => { await gate.promise; return { svg: '<svg/>' }; }) });
  const running = session.submit(spec);
  await assert.rejects(session.submit(spec), /One primary/); gate.resolve(); await running; await session.close();
  await assert.rejects(session.submit(spec), /closed/);
});

test('real independent workers serve warm primary and fresh reference with equal outputs', async () => {
  const artifacts = { primary: resolve('evidence/card-render/attempt-02-lazy-signature'), reference: resolve('evidence/card-render/baseline-941f354') };
  const realSources = Object.fromEntries(Object.entries(artifacts).map(([role, artifact]) => { verifySeal(artifact); return [role, { path: resolve(artifact, 'source'), fingerprint: json(resolve(artifact, 'source.json')).fingerprint }]; }));
  const original = json(resolve(artifacts.reference, 'inputs.json')).cases[0];
  const session = new ShadowSession({ sources: realSources, policy: { sampleEvery: 1 } });
  try {
    await session.submit({ ...original, label: 'cold' }); await session.drain();
    const warm = await session.submit({ ...original, label: 'warm' }); await session.drain();
    assert.equal(warm.receipt.run.computed, 0);
    assert.ok(session.board.get(`${session.prefix}.requests.r000002.reference`).receipt.run.computed > 0);
    assert.deepEqual(session.summary().rows.map(r => r.status), ['matched', 'matched']);
  } finally { await session.close(); }
});

test('worker deadline terminates the checker and cannot later bless the request', async () => {
  const peer = new WorkerPeer({ fingerprint: 'timeout', path: '.' }, { timeoutMs: 30, workerUrl: new URL('data:text/javascript,import {parentPort} from "node:worker_threads"; parentPort.on("message",()=>{});') });
  try { await assert.rejects(peer.run({ id: 'r1', inputDigest: 'x' }), /timeout/); assert.equal(peer.available, false); assert.equal(peer.busy, false); await assert.rejects(peer.run({ id: 'r2' }), /unavailable/); }
  finally { await peer.close(); }
});
