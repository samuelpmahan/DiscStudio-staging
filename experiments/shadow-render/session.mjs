import { randomUUID } from 'node:crypto';
import { evidenceBoard, validatePolicy } from './model.mjs';
import { WorkerPeer } from './worker-peer.mjs';

export class ShadowSession {
  constructor({ sources, policy = {}, primary, reference, onPart }) {
    this.policy = validatePolicy(policy);
    this.prefix = `px.exp.shadow.s${randomUUID().replaceAll('-', '')}`;
    this.board = evidenceBoard(this.prefix, onPart);
    this.sourcesAddress = this.board.publish('sources', sources);
    this.policyAddress = this.board.publish('policy', this.policy);
    this.routingAddress = this.board.publish('routing.initial', { serving: 'primary', reason: 'experimental-default', cause: null });
    this.primary = primary ?? new WorkerPeer(sources.primary, { timeoutMs: this.policy.primaryTimeoutMs });
    this.reference = reference ?? new WorkerPeer(sources.reference, { fresh: true, timeoutMs: this.policy.referenceTimeoutMs });
    this.sequence = 0; this.summarySequence = 0; this.active = false; this.closed = false; this.checks = new Set();
  }
  async submit(spec) {
    if (this.closed || this.active) throw new Error(this.closed ? 'Session closed' : 'One primary request at a time in this pilot');
    this.active = true;
    const sequence = ++this.sequence, id = `r${String(sequence).padStart(6, '0')}`, base = `requests.${id}`;
    const { publish, calculate, get } = this.board;
    try {
      const raw = publish(`${base}.request`, { ...spec, label: spec.label ?? id, id, sequence });
      const input = calculate(`${base}.capture`, 'capture', { request: raw }), request = get(input);
      const capacity = publish(`${base}.capacity`, { available: this.reference.available, busy: this.reference.busy });
      const selection = calculate(`${base}.selection`, 'select', { request: input, policy: this.policyAddress, routing: this.routingAddress, capacity, sources: this.sourcesAddress });
      const chosen = get(selection), peer = chosen.serving === 'reference' ? this.reference : this.primary;
      let primary;
      const started = performance.now();
      try { primary = await peer.run(request); }
      catch (error) { primary = { status: 'error', requestId: id, inputDigest: request.inputDigest, sourceId: peer.source.fingerprint, error: error.message }; }
      if (primary.status === 'ok' && (typeof primary.value?.svg !== 'string' || !primary.value.svg)) primary = { ...primary, status: 'error', error: 'Primary did not produce the required SVG' };
      let primaryAddress = publish(`${base}.primary`, primary);
      if (primary.status !== 'ok') {
        publish(`${base}.comparison`, { requestId: id, status: 'primary-error', reason: primary.error ?? 'Primary output unavailable' });
        return { id, delivered: false, error: primary.error ?? 'Primary output unavailable' };
      }
      if (chosen.serving === 'primary' && sequence === this.policy.negativeControlAt) {
        primaryAddress = calculate(`${base}.negativeControl`, 'corrupt', { primary: primaryAddress });
        primary = get(primaryAddress);
      }
      // Delivery is immutable and published before the reference is even dispatched.
      const deliveryAddress = publish(`${base}.delivery`, { requestId: id, inputDigest: request.inputDigest, sourceId: primary.sourceId, serving: chosen.serving, primaryPart: primaryAddress, elapsedMs: performance.now() - started, checkAtDelivery: chosen.check === 'reference-served' ? 'reference-served' : 'unverified', negativeControl: primary.negativeControl === true });
      if (chosen.check !== 'pending') publish(`${base}.comparison`, { requestId: id, status: chosen.check, reason: chosen.check === 'reference-served' ? 'Reference served after an earlier disagreement; no independent check' : chosen.check, negativeControl: primary.negativeControl === true });
      else {
        const pending = publish(`${base}.checkPending`, { requestId: id, status: 'pending', deliveryPart: deliveryAddress });
        const work = this.check(request, input, base, primaryAddress, pending);
        this.checks.add(work);
        work.catch(() => {}); // Retained promise still rejects when drain()/close() awaits it.
        // A persistence failure must remain observable to drain()/close().
      }
      return { id, delivered: true, delivery: get(deliveryAddress), value: primary.value, receipt: primary.receipt };
    } finally { this.active = false; }
  }
  async check(request, input, base, primaryAddress, pending) {
    const { publish, calculate } = this.board;
    let result;
    try { result = await this.reference.run(request); }
    catch (error) { result = { status: 'error', requestId: request.id, inputDigest: request.inputDigest, sourceId: this.reference.source.fingerprint, error: error.message }; }
    const referenceAddress = publish(`${base}.reference`, result);
    const comparison = calculate(`${base}.comparison`, 'compare', { request: input, primary: primaryAddress, reference: referenceAddress, sources: this.sourcesAddress });
    this.routingAddress = calculate(`routing.${request.id}`, 'route', { routing: this.routingAddress, comparison });
    return { comparison, pending };
  }
  async drain() {
    const work = [...this.checks];
    await Promise.all(work);
    for (const promise of work) this.checks.delete(promise);
  }
  summary() {
    const address = this.board.calculate(`summary.s${++this.summarySequence}`, 'summarize', { observations: `${this.prefix}.requests.*`, routing: this.routingAddress });
    return this.board.get(address);
  }
  async close() {
    if (this.active) throw new Error('Await the primary request before closing');
    if (this.closed) return;
    this.closed = true;
    try { await this.drain(); }
    finally { await Promise.all([this.primary.close(), this.reference.close()]); }
  }
}
