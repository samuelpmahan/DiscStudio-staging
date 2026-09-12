/**
 * The studio's own receipts, read as Parts. `fn.studio.receipts` binds the
 * prefix query `px.receipt.*` (src/core/exec.js `queryPrefix`) and publishes two
 * Parts from one pass over them (`into` as an array, src/core/exec.js), so the
 * Inspect page reads the record through PQL and not through a second index.
 */
import { labelHash } from '../domain.js';

const PREFIX = 'px.receipt.';
const unique = (values) => [...new Set(values)].sort();

/** One row per receipt: name, consumes, produces, result digest. */
export function receiptRow(address, receipt) {
  const trace = Array.isArray(receipt?.trace) ? receipt.trace : [];
  const consumes = unique(trace.flatMap((step) => Object.values(step?.inputs ?? {})).filter((value) => typeof value === 'string'));
  const produces = unique(trace.flatMap((step) => Array.isArray(step?.produces) ? step.produces : step?.output == null ? [] : [step.output]).filter((value) => typeof value === 'string'));
  return {
    address,
    name: address.startsWith(PREFIX) ? address.slice(PREFIX.length) : address,
    consumes,
    produces,
    // A label over the material identity of every invocation in the receipt, not
    // a content hash of the Parts: runtime.js records materials, never bytes.
    digest: labelHash(trace.map((step) => step?.material ?? null)),
    invocations: trace.length,
    computed: receipt?.computed ?? 0,
    reused: receipt?.reused ?? 0
  };
}

/**
 * Inputs: `receipts`, the resolved `px.receipt.*` query (address -> receipt).
 * Output: keyed by the two addresses the Calculation declares in `into`.
 */
export function receiptList({ receipts = {} } = {}) {
  const rows = Object.entries(receipts)
    .filter(([address, receipt]) => address.startsWith(PREFIX) && receipt && Array.isArray(receipt.trace))
    .map(([address, receipt]) => receiptRow(address, receipt))
    .sort((a, b) => a.name < b.name ? -1 : a.name > b.name ? 1 : 0);
  return {
    'px.studio.receipts': rows,
    'px.studio.receipts.summary': {
      receipts: rows.length,
      invocations: rows.reduce((total, row) => total + row.invocations, 0),
      produces: unique(rows.flatMap((row) => row.produces)).length,
      digest: labelHash(rows.map((row) => [row.name, row.digest]))
    }
  };
}
export default receiptList;
