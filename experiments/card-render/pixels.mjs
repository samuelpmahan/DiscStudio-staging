#!/usr/bin/env node
import { createRequire } from 'node:module';
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { resolve, join, dirname } from 'node:path';
import { json, sha, seal, verifySeal, writeJson } from './lib.mjs';

const [baselineArg, candidateArg, outArg, modulesArg, browserArg] = process.argv.slice(2);
if (!outArg || !modulesArg || !browserArg) throw new Error('Usage: node pixels.mjs BASELINE ATTEMPT NEW_OUTPUT NODE_MODULES CHROMIUM_EXECUTABLE');
const baseline = resolve(baselineArg), candidate = resolve(candidateArg), out = resolve(outArg);
const baseDigest = verifySeal(baseline), candidateDigest = verifySeal(candidate);
if (json(join(candidate, 'baseline.json')).digest !== baseDigest) throw new Error('Candidate belongs to a different baseline');
const contract = json(join(baseline, 'contract.json'));
const require = createRequire(join(resolve(modulesArg), '_resolve.cjs'));
const { chromium } = require('playwright'), { PNG } = require('pngjs');
mkdirSync(dirname(out), { recursive: true }); mkdirSync(out);
let browser;
try {
  browser = await chromium.launch({ executablePath: resolve(browserArg), headless: true });
  const context = await browser.newContext({ viewport: contract.viewport, deviceScaleFactor: contract.deviceScaleFactor, locale: 'en-US', timezoneId: 'UTC', colorScheme: 'light', reducedMotion: 'reduce' });
  await context.route('**/*', route => route.abort());
  const page = await context.newPage(), errors = [];
  page.on('pageerror', error => errors.push(error.message));
  const reference = json(join(baseline, 'reference.json')), variants = json(join(candidate, 'candidate.json'));
  if (JSON.stringify(reference.map(r => r.id)) !== JSON.stringify(variants.map(r => r.id))) throw new Error('Pixel cases differ');
  const rows = [];
  async function capture(svg, name) {
    await page.setContent('<!doctype html><style>html,body{margin:0;background:transparent}img{display:block}</style><img alt="experiment output">');
    await page.locator('img').evaluate(async (img, content) => { img.src = 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(content))); await img.decode(); await document.fonts.ready; }, svg);
    const png = await page.locator('img').screenshot({ animations: 'disabled', omitBackground: true });
    writeFileSync(join(out, name), png, { flag: 'wx' });
    return PNG.sync.read(png);
  }
  for (let i = 0; i < reference.length; i++) {
    const expected = await capture(reference[i].svg, `${i}-baseline.png`), actual = await capture(variants[i].svg, `${i}-candidate.png`);
    const sameSize = expected.width === actual.width && expected.height === actual.height;
    let differingPixels = 0;
    if (sameSize) for (let p = 0; p < expected.data.length; p += 4) if (!expected.data.subarray(p, p + 4).equals(actual.data.subarray(p, p + 4))) differingPixels++;
    rows.push({ id: reference[i].id, width: expected.width, height: expected.height, sameSize, differingPixels: sameSize ? differingPixels : null, baselineRgba: sha(expected.data), candidateRgba: sha(actual.data), pass: sameSize && differingPixels === 0 });
  }
  // Negative control: ensure a changed image really produces a different observation.
  const black = await capture('<svg xmlns="http://www.w3.org/2000/svg" width="2" height="2"><rect width="2" height="2" fill="black"/></svg>', 'control-black.png');
  const white = await capture('<svg xmlns="http://www.w3.org/2000/svg" width="2" height="2"><rect width="2" height="2" fill="white"/></svg>', 'control-white.png');
  const controlPass = !black.data.equals(white.data);
  const result = { pass: rows.every(r => r.pass) && !errors.length && controlPass, baseline: baseDigest, candidate: candidateDigest, browser: browser.version(), executable: resolve(browserArg), executableSha256: sha(readFileSync(browserArg)), os: process.platform, arch: process.arch, viewport: contract.viewport, deviceScaleFactor: contract.deviceScaleFactor, playwright: require('playwright/package.json').version, pngjs: require('pngjs/package.json').version, scriptSha256: sha(readFileSync(new URL(import.meta.url))), fontScope: 'Same process and installed system fonts; not portable across machines.', controlPass, errors, rows };
  writeJson(join(out, 'pixels.json'), result);
  verifySeal(baseline); verifySeal(candidate); seal(out);
  console.log(`Pixel parity: ${rows.filter(r => r.pass).length}/${rows.length}; negative control ${controlPass ? 'passed' : 'failed'}`);
  if (!result.pass) process.exitCode = 1;
} catch (error) {
  writeJson(join(out, 'failure.json'), { message: error.message }); seal(out); process.exitCode = 1; console.error(error.message);
} finally { await browser?.close(); }
