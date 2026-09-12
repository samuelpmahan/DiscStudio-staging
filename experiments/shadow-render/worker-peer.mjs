import { Worker } from 'node:worker_threads';

/** One in-flight operation, bounded wait, no restart loop or hidden queue. */
export class WorkerPeer {
  constructor(source, { fresh = false, timeoutMs = 5000, workerUrl = new URL('./render-worker.mjs', import.meta.url) } = {}) {
    this.source = source; this.timeoutMs = timeoutMs; this.available = true; this.pending = null;
    this.worker = new Worker(workerUrl, { workerData: { source, fresh } });
    this.worker.on('message', result => {
      if (!this.pending) return;
      const { resolve, reject, request } = this.pending; this.clear();
      if (result.requestId !== request.id || result.inputDigest !== request.inputDigest || result.sourceId !== source.fingerprint) reject(new Error('Worker response identity mismatch'));
      else resolve(result);
    });
    this.worker.on('error', error => this.fail(error));
    this.worker.on('exit', code => this.fail(new Error(`Worker exited (${code})`)));
  }
  get busy() { return this.pending !== null; }
  clear() { if (this.pending) clearTimeout(this.pending.timer); this.pending = null; }
  fail(error) {
    this.available = false;
    if (this.pending) { const { reject } = this.pending; this.clear(); reject(error); }
  }
  run(request) {
    if (!this.available) return Promise.reject(new Error('Worker unavailable'));
    if (this.busy) return Promise.reject(new Error('Worker already has an in-flight request'));
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => { this.fail(new Error(`Worker timeout after ${this.timeoutMs} ms`)); void this.worker.terminate(); }, this.timeoutMs);
      this.pending = { resolve, reject, request, timer };
      try { this.worker.postMessage(request); } catch (error) { this.fail(error); }
    });
  }
  async close() { this.fail(new Error('Worker closed')); await this.worker.terminate(); }
}
