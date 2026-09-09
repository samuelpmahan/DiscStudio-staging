#!/usr/bin/env node
/**
 * embed.mjs — write a standalone Tick viewer with one record baked in.
 *
 *   node embed.mjs record.json > page.html
 *   node embed.mjs fixtures/wumpus-belief-tick.json --out /tmp/wumpus.html
 *
 * The output is a single file that opens over file:// with no server, no
 * network and no module graph: adapters.js and tick-viewer.js are concatenated
 * into one inline module, and the record is placed in the page's
 * <script type="application/json" id="record"> block.
 *
 * The input may be a pyto-run-record@1 document or a raw runtime document
 * ({pql, receipt} / {receipts} / {records}); it is converted and validated
 * here, so an invalid record fails at build time instead of in the browser.
 *
 * `composePage` is the page builder itself and touches no file system and no
 * network: it takes the three sources as text. DiscStudio's studio imports this
 * module in the browser and calls it with sources it fetched over its own
 * origin (src/app.js), so the studio and this CLI build the same page from the
 * same code and the renderer is not forked. Everything below `composePage` that
 * reads or writes files is Node-only and loads node: builtins only under Node.
 */

import { coerceToRecord } from './tick-viewer.js';

const IS_NODE = typeof process !== 'undefined' && !!process.versions && !!process.versions.node;
const nodeFs = IS_NODE ? await import('node:fs') : null;
const nodePath = IS_NODE ? await import('node:path') : null;
const nodeUrl = IS_NODE ? await import('node:url') : null;

const HERE = IS_NODE ? nodePath.dirname(nodeUrl.fileURLToPath(import.meta.url)) : null;

/** The three files the page is composed from, in the order composePage takes them. */
export const PAGE_SOURCES = ['tick-viewer.html', 'adapters.js', 'tick-viewer.js'];

const PAGE_SCRIPT = `<script type="module">
  import { mount } from './tick-viewer.js';
  mount(document);
</script>`;

const EMPTY_RECORD_BLOCK = '<script type="application/json" id="record"></script>';

/** Strip ES module syntax so two modules can be concatenated into one script. */
function inlineModule(source, name) {
  const withoutImports = source.replace(/^import[^\n]*from '\.\/adapters\.js';\n/m, '');
  const flattened = withoutImports.replace(/^export (?=(?:default )?(?:function|const|let|var|class)\b)/gm, '');
  const leftover = flattened.match(/^\s*(import|export)\b[^\n]*/m);
  if (leftover) throw new Error(`${name}: cannot inline, unhandled module statement: ${leftover[0].trim()}`);
  // A literal </script anywhere in the source would end the inline element early.
  // The backslash is inert in a comment, a string literal and a regex alike.
  return flattened.replace(/<\/script/gi, '<\\/script');
}

/** JSON that is safe inside a <script> element and inside HTML comments. */
export function embeddableJson(record) {
  return JSON.stringify(record, null, 2)
    .replace(/</g, '\\u003c')
    .replace(/>/g, '\\u003e')
    .replace(/\u2028/g, '\\u2028')
    .replace(/\u2029/g, '\\u2029');
}

/**
 * Build the standalone page from source text alone: no file system, no network,
 * no Node builtins. `html` is tick-viewer.html, `adapters` is adapters.js and
 * `viewer` is tick-viewer.js, each as read from disk or fetched over an origin.
 */
export function composePage({ html, adapters: adaptersSource, viewer: viewerSource, record }) {
  const adapters = inlineModule(adaptersSource, 'adapters.js');
  const viewer = inlineModule(viewerSource, 'tick-viewer.js');

  if (!html.includes(PAGE_SCRIPT)) throw new Error('tick-viewer.html: module bootstrap block not found; embed.mjs and the page have drifted apart');
  if (!html.includes(EMPTY_RECORD_BLOCK)) throw new Error('tick-viewer.html: empty record block not found; embed.mjs and the page have drifted apart');

  const bundle = `<script type="module">\n/* adapters.js + tick-viewer.js, inlined by embed.mjs. No imports, no network. */\n${adapters}\n${viewer}\nmount(document);\n</script>`;
  const recordBlock = `<script type="application/json" id="record">\n${embeddableJson(record)}\n</script>`;
  // Both replacements pass a FUNCTION, never a string. String.prototype.replace
  // expands `$&`, `$'`, '$`' and `$1` inside a replacement *string*, and both of
  // these replacements are record- or source-derived: a Part value, an address or
  // a pcr name holding `$'` (a shell snippet such as `printf $'%s\n'` is enough)
  // spliced the page's own tail into the JSON block, so the record no longer
  // parsed and the module bootstrap was left un-inlined -- a page that can never
  // mount, produced silently at build time. A function replacement is inserted
  // literally.
  return html.replace(EMPTY_RECORD_BLOCK, () => recordBlock).replace(PAGE_SCRIPT, () => bundle);
}

/** Build the standalone page from a viewer directory on disk (Node). */
export function buildPage(record, { viewerDir = HERE } = {}) {
  const [html, adapters, viewer] = PAGE_SOURCES.map((name) => nodeFs.readFileSync(nodePath.resolve(viewerDir, name), 'utf8'));
  return composePage({ html, adapters, viewer, record });
}

/**
 * The same three sources fetched from a served viewer directory (the browser).
 * `baseUrl` is the directory holding tick-viewer.html; a browser caller passes
 * `new URL('../pyto/viewer/', import.meta.url)`.
 */
export async function fetchPageSources(baseUrl, fetchImpl = globalThis.fetch) {
  const read = async (name) => {
    const response = await fetchImpl(new URL(name, baseUrl));
    if (!response.ok) throw new Error(`${name}: ${response.status} ${response.statusText}`);
    return response.text();
  };
  const [html, adapters, viewer] = await Promise.all(PAGE_SOURCES.map(read));
  return { html, adapters, viewer };
}

export function embedFile(inputPath, { viewerDir = HERE } = {}) {
  const parsed = JSON.parse(nodeFs.readFileSync(inputPath, 'utf8'));
  return buildPage(coerceToRecord(parsed), { viewerDir });
}

function main(argv) {
  const args = argv.slice(2);
  const outIndex = args.findIndex((a) => a === '--out' || a === '-o');
  let out = null;
  if (outIndex !== -1) {
    out = args[outIndex + 1];
    if (!out) throw new Error('--out needs a path');
    args.splice(outIndex, 2);
  }
  const input = args[0];
  if (!input) {
    process.stderr.write('usage: node embed.mjs <record.json> [--out page.html]\n');
    process.exit(2);
  }
  const page = embedFile(nodePath.resolve(process.cwd(), input));
  if (out) nodeFs.writeFileSync(nodePath.resolve(process.cwd(), out), page);
  else process.stdout.write(page);
}

if (IS_NODE && process.argv[1] && nodePath.resolve(process.argv[1]) === nodePath.resolve(nodeUrl.fileURLToPath(import.meta.url))) main(process.argv);
