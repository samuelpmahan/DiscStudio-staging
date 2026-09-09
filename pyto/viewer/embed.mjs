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
 */

import { readFileSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';
import { coerceToRecord } from './tick-viewer.js';

const HERE = dirname(fileURLToPath(import.meta.url));

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

/** Build the standalone page as a string. `play` bakes in `<body data-play="1">`, the offline equivalent of `?play=1`. */
export function buildPage(record, { viewerDir = HERE, play = false } = {}) {
  let html = readFileSync(resolve(viewerDir, 'tick-viewer.html'), 'utf8');
  const adapters = inlineModule(readFileSync(resolve(viewerDir, 'adapters.js'), 'utf8'), 'adapters.js');
  const viewer = inlineModule(readFileSync(resolve(viewerDir, 'tick-viewer.js'), 'utf8'), 'tick-viewer.js');

  if (!html.includes(PAGE_SCRIPT)) throw new Error('tick-viewer.html: module bootstrap block not found; embed.mjs and the page have drifted apart');
  if (!html.includes(EMPTY_RECORD_BLOCK)) throw new Error('tick-viewer.html: empty record block not found; embed.mjs and the page have drifted apart');
  if (play) html = html.replace('<body>', '<body data-play="1">');

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

export function embedFile(inputPath, { viewerDir = HERE, play = false } = {}) {
  const parsed = JSON.parse(readFileSync(inputPath, 'utf8'));
  return buildPage(coerceToRecord(parsed), { viewerDir, play });
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
  const playIndex = args.indexOf('--play');
  const play = playIndex !== -1;
  if (play) args.splice(playIndex, 1);
  const input = args[0];
  if (!input) {
    process.stderr.write('usage: node embed.mjs <record.json> [--out page.html] [--play]\n');
    process.exit(2);
  }
  const page = embedFile(resolve(process.cwd(), input), { play });
  if (out) writeFileSync(resolve(process.cwd(), out), page);
  else process.stdout.write(page);
}

if (process.argv[1] && resolve(process.argv[1]) === resolve(fileURLToPath(import.meta.url))) main(process.argv);
