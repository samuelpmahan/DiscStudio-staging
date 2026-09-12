/**
 * The LAB port's harness: one PxC board, `fn.lab.*` Calculations, PQL documents
 * read by the studio's own `readPql`, runs through `invokePql`, and the Parts
 * written to a JSON store a PQL reader can open.
 *
 * It is the studio's `src/runtime.js` reduced to what a port needs: `register`
 * wraps a plain function as a Calculation, `execute` composes and runs, and
 * `settle` files the same receipt shape runtime.js files, so `runRecord` can
 * hand the run to the shared pyto-run-record adapter unchanged.
 */
import { createExecBoard, pxFn, readPql, invokePql } from '../core/exec.js';
import { sha256HexSyncText } from '../core/sha256.js';
import { fromDiscStudioReceipt, validate } from '../../pyto/viewer/adapters.js';

/**
 * The store is a folder of files, and the Stage modules beside this one now also
 * run in the browser, where there is no file system at all: src/runtime.js
 * registers the same `fn.lab.*` Calculations on the studio's own board. So node's
 * modules are imported only where there is a node to import them from, and
 * `save`/`saveRecord` refuse in plain words anywhere else. Nothing below is
 * evaluated in a browser, and every other export here is portable.
 */
const ON_NODE = !!globalThis.process?.versions?.node;
const nodeModules = ON_NODE ? { fs: await import('node:fs'), path: await import('node:path'), url: await import('node:url') } : null;
export const STORE = ON_NODE ? nodeModules.path.join(nodeModules.path.dirname(nodeModules.url.fileURLToPath(import.meta.url)), 'store') : null;
function onDisk() {
  if (!nodeModules) throw new Error('lab: the store is a folder of files, and this runtime has no file system. Read the Parts off the board instead.');
  return nodeModules;
}

/** The one digest rule (pyto/src/pyto/neat/diff.py `structural_digest`): sha256 of canonical JSON. */
export function canonicalJson(value) {
  if (value === null || typeof value !== 'object') return JSON.stringify(value ?? null);
  if (Array.isArray(value)) return `[${value.map(canonicalJson).join(',')}]`;
  return `{${Object.keys(value).sort().map(key => `${JSON.stringify(key)}:${canonicalJson(value[key])}`).join(',')}}`;
}
export function digestOf(value) { return sha256HexSyncText(canonicalJson(value)); }

/**
 * A raster Part is JSON-able but not JSON-*readable*: a million pixel samples
 * are not something a reader of the store wants to scroll. Stored Parts keep
 * their shape and replace any long numeric run with its length and digest,
 * which is exactly what the LAB compares when it compares two runs
 * (`compare.ts` `sameBytes`, "canonical pixel bytes").
 */
export function summarize(value, limit = 64) {
  if (Array.isArray(value)) {
    if (value.length > limit && value.every(entry => typeof entry === 'number')) return { kind: 'numbers', length: value.length, sha256: digestOf(value) };
    return value.map(entry => summarize(entry, limit));
  }
  if (value && typeof value === 'object') return Object.fromEntries(Object.entries(value).map(([key, entry]) => [key, summarize(entry, limit)]));
  return value;
}

export function createLab() {
  const core = createExecBoard(), addresses = new Set();
  const pxc = { ...core, set(address, value) { addresses.add(typeof address === 'string' ? address : address.address); core.set(address, value); } };
  const calls = [];
  const lab = {
    pxc,
    addresses: () => [...addresses].sort(),
    put(address, value) { pxc.set(address, value); return address; },
    get: address => pxc.get(address),
    has: address => pxc.has(address),
    /** A Calculation is `fn.lab.*`, lowercase, and pure over its inputs. */
    register(address, calculate) {
      if (!/^fn\.lab\.[a-z0-9.]+$/.test(address)) throw new Error(`lab: '${address}' is not a lowercase fn.lab.* address.`);
      pxc.register(pxFn(address), inputs => { calls.push({ call: address, reused: false, material: null, revision: 1 }); return calculate(inputs); });
    },
    /** A PQL document, read by the studio's reader exactly as the studio reads its own. */
    document: (name, ticks) => readPql(JSON.stringify({ PrincipleComponentRender: name, Ticks: ticks }), JSON.parse),
    /** Run one composition; file `px.receipt.<name>` the way runtime.js does. */
    run(name, composition) {
      const mark = calls.length, run = invokePql(composition, pxc, {});
      const invoked = calls.slice(mark);
      const trace = run.Ticks.flatMap(tick => tick.Calculations.map(calculation => ({ tick: tick.name, call: calculation.actualCall, inputs: calculation.with, output: calculation.into, produces: calculation.produces })))
        .map((step, index) => ({ ...step, ...invoked[index] }));
      const receipt = { composition, trace, computed: trace.length, reused: 0 };
      pxc.set(`px.receipt.${name}`, receipt);
      return { run, receipt };
    },
    /** The pyto-run-record@1 view, built by the shared adapter from the two Parts the run wrote. */
    runRecord(name) {
      const record = validate(fromDiscStudioReceipt(pxc.get(`px.pql.${name}`), pxc.get(`px.receipt.${name}`)));
      pxc.set(`px.run.${name}`, record);
      return { address: `px.run.${name}`, record };
    },
    /** Every `px.exp.lab.*` and `proposal.lab.*` Part, summarized, as one JSON file. */
    save(name, extra = {}) {
      const parts = Object.fromEntries([...addresses].filter(address => address.startsWith('px.exp.lab.') || address.startsWith('proposal.lab.')).sort().map(address => [address, summarize(pxc.get(address))]));
      const { fs, path } = onDisk(), file = path.join(STORE, `${name}.json`);
      fs.mkdirSync(STORE, { recursive: true });
      fs.writeFileSync(file, JSON.stringify({ ...extra, parts }, null, 2) + '\n');
      return file;
    },
    /** One run record per composition, under store/records, the way the brain's harness files them. */
    saveRecord(name) {
      const { record } = lab.runRecord(name), { fs, path } = onDisk(), records = path.join(STORE, 'records');
      fs.mkdirSync(records, { recursive: true });
      fs.writeFileSync(path.join(records, `${name}.json`), JSON.stringify(summarize(record), null, 2) + '\n');
      return record;
    }
  };
  return lab;
}

/** A finding Part: `proposal.lab.<k>`, with its `for`. */
export function finding(lab, key, { kind, text, for: why, workaround = null, proposal = null }) {
  return lab.put(`proposal.lab.${key}`, { for: why, kind, text, workaround, proposal });
}
