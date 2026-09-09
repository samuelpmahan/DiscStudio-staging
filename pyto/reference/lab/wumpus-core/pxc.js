/**
 * A small, dependency-free value store used by the Wumpus execution core.
 * Addresses are deliberately strings so callers can introduce new slots
 * without changing this package.
 */

export const PX_TRANSACTION = Symbol('pxc.transaction');

function addressOf(value) {
  const address = typeof value === 'string' ? value : value?.address;
  if (typeof address !== 'string' || address.length === 0) {
    throw new TypeError('PxC address must be a non-empty string or { address }.');
  }
  return address;
}

export function pxKey(address) {
  return Object.freeze({ address: addressOf(address) });
}

export function pxFn(address) {
  return Object.freeze({ address: addressOf(address) });
}

/** Clone values while retaining typed-array constructors and array buffers. */
export function captureValue(value, seen = new WeakMap()) {
  if (value === null || typeof value !== 'object') return value;
  if (typeof value === 'function') return value;
  if (seen.has(value)) return seen.get(value);
  if (ArrayBuffer.isView(value)) {
    if (value instanceof DataView) {
      const copy = new DataView(value.buffer.slice(value.byteOffset, value.byteOffset + value.byteLength));
      seen.set(value, copy);
      return copy;
    }
    const copy = new value.constructor(value);
    seen.set(value, copy);
    return copy;
  }
  if (value instanceof ArrayBuffer) return value.slice(0);
  if (value instanceof Date) return new Date(value.getTime());
  if (value instanceof RegExp) return new RegExp(value.source, value.flags);
  if (value instanceof Map) {
    const copy = new Map();
    seen.set(value, copy);
    for (const [key, entry] of value) copy.set(captureValue(key, seen), captureValue(entry, seen));
    return copy;
  }
  if (value instanceof Set) {
    const copy = new Set();
    seen.set(value, copy);
    for (const entry of value) copy.add(captureValue(entry, seen));
    return copy;
  }
  if (Array.isArray(value)) {
    const copy = [];
    seen.set(value, copy);
    for (const item of value) copy.push(captureValue(item, seen));
    return copy;
  }
  const copy = Object.create(Object.getPrototypeOf(value));
  seen.set(value, copy);
  for (const key of Reflect.ownKeys(value)) {
    const descriptor = Object.getOwnPropertyDescriptor(value, key);
    if (descriptor && 'value' in descriptor) descriptor.value = captureValue(descriptor.value, seen);
    try { Object.defineProperty(copy, key, descriptor); } catch { copy[key] = descriptor.value; }
  }
  return copy;
}

/** Freeze ordinary snapshot containers recursively. Typed arrays remain mutable
 * JavaScript objects, but are always independently captured before exposure. */
export function freezeSnapshot(value, seen = new WeakSet()) {
  if (value === null || typeof value !== 'object' || seen.has(value)) return value;
  seen.add(value);
  if (ArrayBuffer.isView(value) || value instanceof ArrayBuffer || value instanceof Map || value instanceof Set) {
    return value;
  }
  for (const key of Reflect.ownKeys(value)) {
    const descriptor = Object.getOwnPropertyDescriptor(value, key);
    if (descriptor && 'value' in descriptor) freezeSnapshot(descriptor.value, seen);
  }
  return Object.freeze(value);
}

export function createPxC() {
  let slots = new Map();
  let calculations = new Map();

  const api = {
    get(slot) {
      const address = addressOf(slot);
      if (!slots.has(address)) throw new Error(`PxC: address '${address}' has not been produced.`);
      return captureValue(slots.get(address));
    },
    has(slot) { return slots.has(addressOf(slot)); },
    set(slot, value) { slots.set(addressOf(slot), captureValue(value)); },
    register(fn, calculate) {
      const address = addressOf(fn);
      if (typeof calculate !== 'function') throw new TypeError(`PxC: calculation '${address}' must be a function.`);
      const current = calculations.get(address);
      if (current && current !== calculate) throw new Error(`PxC: calculation '${address}' is already registered.`);
      calculations.set(address, calculate);
    },
    call(fn, args) {
      const address = addressOf(fn);
      const calculate = calculations.get(address);
      if (!calculate) throw new Error(`PxC: calculation '${address}' is not registered.`);
      return calculate(args);
    }
  };

  Object.defineProperty(api, PX_TRANSACTION, {
    enumerable: false,
    value: {
      begin(consumes = [], id = 'tick') {
        const working = new Map();
        for (const [key, value] of slots) working.set(key, captureValue(value));
        const workingCalculations = new Map(calculations);
        const declared = new Set(consumes.map(addressOf));
        const consumed = [], produced = [], writes = [], calculationCalls = [];
        const tracked = {
          get(slot) {
            const address = addressOf(slot);
            consumed.push({ address, value: captureValue(working.has(address) ? working.get(address) : undefined) });
            if (!working.has(address)) throw new Error(`PxC: Tick '${id}' read missing address '${address}'.`);
            return captureValue(working.get(address));
          },
          has(slot) { return working.has(addressOf(slot)); },
          set(slot, value) {
            const address = addressOf(slot);
            const existed = working.has(address);
            produced.push({ address, value: captureValue(value) });
            writes.push({ address, kind: !existed ? 'new-address' : declared.has(address) ? 'refinement' : 'replacement' });
            working.set(address, captureValue(value));
          },
          register(fn, calculate) {
            const address = addressOf(fn);
            if (typeof calculate !== 'function') throw new TypeError(`PxC: calculation '${address}' must be a function.`);
            const current = workingCalculations.get(address);
            if (current && current !== calculate) throw new Error(`PxC: calculation '${address}' is already registered.`);
            workingCalculations.set(address, calculate);
          },
          call(fn, args) {
            const address = addressOf(fn);
            const calculate = workingCalculations.get(address);
            if (!calculate) throw new Error(`PxC: calculation '${address}' is not registered.`);
            const input = captureValue(args);
            const result = calculate(input);
            const output = captureValue(result);
            calculationCalls.push({ address, input: captureValue(input), output });
            return captureValue(output);
          }
        };
        return {
          tracked, consumed, produced, writes, calculations: calculationCalls,
          commit() { slots = working; calculations = workingCalculations; },
          rollback() { /* working is private, so rollback needs no mutation */ }
        };
      }
    }
  });
  return api;
}

export { addressOf };
