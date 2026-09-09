import { PX_TRANSACTION, addressOf, captureValue, freezeSnapshot } from './pxc.js';

let invocationSequence = 0;
function nextInvocationId() {
  invocationSequence += 1;
  return `tick-${invocationSequence}`;
}

/** Execute one tick atomically and return an inspection receipt. */
export function executeTick(pxc, spec) {
  if (!pxc || !pxc[PX_TRANSACTION]?.begin) throw new TypeError('executeTick requires a PxC created by createPxC.');
  if (!spec || typeof spec.run !== 'function') throw new TypeError('executeTick requires { run }.');
  const id = String(spec.id ?? 'tick');
  const consumes = Object.freeze((spec.consumes ?? []).map(addressOf));
  const produces = Object.freeze((spec.produces ?? []).map(addressOf));
  const invocationId = nextInvocationId();
  const startedAt = Date.now();
  const tx = pxc[PX_TRANSACTION].begin(consumes, id);
  const finish = (result) => {
    tx.commit();
    const finishedAt = Date.now();
    return freezeSnapshot({
      invocationId, id, consumes, produces,
      actualConsumes: Object.freeze([...new Set(tx.consumed.map((entry) => entry.address))]),
      actualProduces: Object.freeze([...new Set(tx.produced.map((entry) => entry.address))]),
      inputs: tx.consumed.map((entry) => ({ address: entry.address, value: captureValue(entry.value) })),
      outputs: tx.produced.map((entry) => ({ address: entry.address, value: captureValue(entry.value) })),
      writes: Object.freeze(tx.writes.map((entry) => Object.freeze({ ...entry }))),
      calculations: tx.calculations.map((entry) => ({
        address: entry.address,
        input: captureValue(entry.input),
        output: captureValue(entry.output),
        identityScope: 'registered-address-only',
        limitation: 'function bodies, closures, and transitive dependencies are not hashed'
      })),
      result: captureValue(result), startedAt, finishedAt, durationMs: finishedAt - startedAt
    });
  };
  try {
    const result = spec.run(tx.tracked);
    if (result && typeof result.then === 'function') {
      return result.then(finish, (error) => { tx.rollback(); throw error; });
    }
    return finish(result);
  } catch (error) {
    tx.rollback();
    throw error;
  }
}
