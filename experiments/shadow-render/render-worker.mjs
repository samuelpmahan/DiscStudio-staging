import { parentPort, workerData } from 'node:worker_threads';
import { pathToFileURL } from 'node:url';
import { join } from 'node:path';
import { createHash } from 'node:crypto';

const { createStudioRuntime } = await import(pathToFileURL(join(workerData.source.path, 'src/runtime.js')));
let runtime = null, previousWorld = null;
parentPort.on('message', request => {
  const start = performance.now();
  const envelope = { requestId: request.id, inputDigest: request.inputDigest, sourceId: workerData.source.fingerprint };
  try {
    if (!['card', 'scene'].includes(request.method)) throw new Error('Unsupported render method');
    const worldHash = createHash('sha256').update(JSON.stringify(request.world)).digest('hex');
    // The serving candidate retains its own memo state; the checker starts fresh.
    if (workerData.fresh || !runtime) runtime = createStudioRuntime(request.world);
    else if (worldHash !== previousWorld) runtime.replace(request.world);
    previousWorld = worldHash;
    const { run, ...output } = runtime[request.method](...request.args);
    const elapsedMs = performance.now() - start;
    const { record } = runtime.runRecord(request.method === 'card' ? 'display-card' : 'on-the-course');
    // Explicit contract: compare JSON-visible outputs, keep execution separately.
    parentPort.postMessage({ ...envelope, status: 'ok', value: JSON.parse(JSON.stringify(output)), receipt: JSON.parse(JSON.stringify({ run, record })), elapsedMs });
  } catch (error) {
    runtime = null; previousWorld = null;
    parentPort.postMessage({ ...envelope, status: 'error', error: error.message, elapsedMs: performance.now() - start });
  }
});
