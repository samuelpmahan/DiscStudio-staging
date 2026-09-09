/**
 * Build a small, JSON-friendly explanation of where a PxC address came from.
 * Records are executeTick receipts in chronological order.
 */

function assertAddress(address) {
  if (typeof address !== 'string' || address.length === 0) {
    throw new TypeError('traceAddress requires a non-empty address string.');
  }
  return address;
}

function entries(record, key) {
  return Array.isArray(record?.[key]) ? record[key] : [];
}

function latestOutput(records, address, beforeIndex) {
  for (let index = Math.min(beforeIndex, records.length) - 1; index >= 0; index -= 1) {
    const output = entries(records[index], 'outputs').findLast((entry) => entry?.address === address);
    if (output) return { index, record: records[index], output };
  }
  return null;
}

function latestInput(records, address, beforeIndex) {
  for (let index = Math.min(beforeIndex, records.length) - 1; index >= 0; index -= 1) {
    const input = entries(records[index], 'inputs').findLast((entry) => entry?.address === address);
    if (input) return input;
  }
  return undefined;
}

/**
 * Trace an address through executeTick receipts.
 *
 * `beforeIndex` is an exclusive record index. It is useful when callers want
 * to inspect an address as it existed before a particular receipt. A read is
 * always bound to a write in an earlier receipt; outputs from the same receipt
 * are therefore never considered.
 */
export function traceAddress(records, address, { beforeIndex } = {}) {
  if (!Array.isArray(records)) throw new TypeError('traceAddress requires an array of records.');
  assertAddress(address);
  const boundary = beforeIndex === undefined ? records.length : Number(beforeIndex);
  if (!Number.isInteger(boundary) || boundary < 0) {
    throw new TypeError('traceAddress beforeIndex must be a non-negative integer.');
  }

  const build = (target, limit, fallback) => {
    const producer = latestOutput(records, target, limit);
    const node = { address: target, producer: null, inputs: [], calculations: [] };
    if (producer) {
      const { index, record, output } = producer;
      node.producer = {
        id: record?.id,
        invocationId: record?.invocationId,
        index,
      };
      if (Object.prototype.hasOwnProperty.call(output, 'value')) node.value = output.value;
      node.inputs = entries(record, 'inputs').map((input) =>
        build(input?.address, index, input && Object.prototype.hasOwnProperty.call(input, 'value') ? input.value : undefined));
      node.calculations = entries(record, 'calculations')
        .map((calculation) => typeof calculation === 'string' ? calculation : calculation?.address)
        .filter((calculation) => typeof calculation === 'string');
      return node;
    }

    // When this node is an input of a producer, its fallback is the value
    // captured by that producer's receipt and must take precedence over older
    // unrelated reads of the same address.
    if (fallback !== undefined) node.value = fallback;
    else {
      const input = latestInput(records, target, limit);
      if (input && Object.prototype.hasOwnProperty.call(input, 'value')) node.value = input.value;
    }
    return node;
  };

  return build(address, boundary, undefined);
}
