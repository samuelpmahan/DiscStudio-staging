/**
 * S0, ported: intake. "produce one cropped image for S1" (S0.stage.yaml), whose
 * exit condition is `px.course.canonicalPixels` being readable by S1.
 *
 * In ChainSpot S0's clean path has no PQL document at all: `S0.pcr.yaml` is a
 * description (input / sanitation / transform / output / last / receipt) and the
 * composition is three `OperationSpec` Ticks in TypeScript run by the execution
 * gateway. The Mermaid experiment is the first S0 written as a composition. So
 * this port builds the S0 PQL document from the description -- one Calculation
 * per named step, in the order `S0.stage.yaml` gives -- and `mermaid.js` proves
 * the compiled `S0.mmd` is the same document.
 *
 * The three Calculations are the LAB's, ported: Rec.601 luma (`g0/inputAsset.ts`),
 * the single-image portrait-phone row-entropy chrome detector
 * (`g0/stripChrome.ts`), and the single-tile crop (`g0/composite.ts`).
 */
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { digestOf } from './lab.js';
import { SOURCE } from './source.js';
import { compileMermaidPcr, lowerToPql } from './mermaid.js';
import { labDocument } from './address.js';

export const S0_ADDRESSES = {
  selectedInput: 'px.exp.lab.source.selectedinput',
  // The Mermaid S0 publishes no FullImage Part: decode's result is bound
  // straight into bounds and crop. `lowerToPql` gives it the one address the
  // studio's grammar needs, and this is that address.
  fullImage: 'px.exp.lab.s0.local.decode',
  cropBounds: 'px.exp.lab.source.cropbounds',
  canonicalPixels: 'px.exp.lab.course.canonicalpixels',
  cacheReceipt: 'px.exp.lab.s0.cachereceipt'
};

const ENTROPY_BINS = 16, ENTROPY_THRESHOLD_RATIO = 0.74, ENTROPY_SMOOTH_RADIUS = 1;
const ENTROPY_RUN_LINES = 6, ENTROPY_REQUIRED_LINES = 4, ENTROPY_INWARD_SAFETY_PX = 1;
const MAX_INSET_FRACTION = 0.25, MIN_BAND_PX = 2, MARGIN_PX = 2;

/** Integer Rec.601 luma, the formula both LAB adapters use. */
export function toGray({ widthPx, heightPx, rgba }) {
  const gray = new Array(widthPx * heightPx);
  for (let index = 0; index < gray.length; index++) { const offset = index * 4; gray[index] = (rgba[offset] * 77 + rgba[offset + 1] * 150 + rgba[offset + 2] * 29) >> 8; }
  return { widthPx, heightPx, gray };
}

function median(values) { const sorted = [...values].sort((a, b) => a - b), middle = Math.floor(sorted.length / 2); return sorted.length % 2 === 0 ? (sorted[middle - 1] + sorted[middle]) / 2 : sorted[middle]; }

function smoothedRowEntropy({ widthPx, heightPx, gray }) {
  const shift = 8 - Math.log2(ENTROPY_BINS), entropy = new Array(heightPx);
  for (let y = 0; y < heightPx; y++) {
    const histogram = new Array(ENTROPY_BINS).fill(0), base = y * widthPx;
    let samples = 0;
    for (let x = 0; x < widthPx; x += 2) { histogram[gray[base + x] >> shift]++; samples++; }
    let value = 0;
    for (const count of histogram) { if (!count) continue; const p = count / samples; value -= p * Math.log2(p); }
    entropy[y] = value;
  }
  return entropy.map((_, y) => {
    let sum = 0, count = 0;
    for (let row = Math.max(0, y - ENTROPY_SMOOTH_RADIUS); row <= Math.min(heightPx - 1, y + ENTROPY_SMOOTH_RADIUS); row++) { sum += entropy[row]; count++; }
    return sum / count;
  });
}

/** `stripChromeProposal` for one raster: the deterministic portrait-phone entropy detector. */
export function stripChromeProposal(raster) {
  if (!(raster.heightPx >= 1000 && raster.widthPx >= 500 && raster.heightPx > raster.widthPx)) return { insets: null, source: 'none' };
  const entropy = smoothedRowEntropy(raster), height = raster.heightPx;
  const reference = median(entropy.slice(Math.floor(height * 0.35), Math.floor(height * 0.65)));
  if (!Number.isFinite(reference) || reference <= 0) return { insets: null, source: 'none' };
  const threshold = reference * ENTROPY_THRESHOLD_RATIO;
  let topBoundary = null;
  for (let y = 1; y < Math.floor(height * 0.32) - ENTROPY_RUN_LINES; y++) {
    let passing = 0;
    for (let k = 0; k < ENTROPY_RUN_LINES; k++) if (entropy[y + k] >= threshold) passing++;
    if (passing >= ENTROPY_REQUIRED_LINES) { topBoundary = y; break; }
  }
  let bottomBoundary = null;
  for (let y = height - 2; y > Math.floor(height * 0.68) + ENTROPY_RUN_LINES; y--) {
    let passing = 0;
    for (let k = 0; k < ENTROPY_RUN_LINES; k++) if (entropy[y - k] >= threshold) passing++;
    if (passing >= ENTROPY_REQUIRED_LINES) { bottomBoundary = y; break; }
  }
  const maxInset = Math.floor(height * MAX_INSET_FRACTION);
  const topDetected = topBoundary === null ? 0 : topBoundary + ENTROPY_INWARD_SAFETY_PX;
  const bottomDetected = bottomBoundary === null ? 0 : height - 1 - bottomBoundary + ENTROPY_INWARD_SAFETY_PX;
  const top = topDetected >= MIN_BAND_PX ? Math.min(maxInset, topDetected + MARGIN_PX) : 0;
  const bottom = bottomDetected >= MIN_BAND_PX ? Math.min(maxInset, bottomDetected + MARGIN_PX) : 0;
  const insets = top || bottom ? { top, right: 0, bottom, left: 0 } : null;
  return { insets, source: insets ? 'single-phone-entropy' : 'none' };
}

/** `materializeComposite` for one tile at the origin: the crop itself. */
export function materializeComposite(tile, insets) {
  const effective = insets ?? { top: 0, right: 0, bottom: 0, left: 0 };
  const widthPx = tile.widthPx - effective.left - effective.right, heightPx = tile.heightPx - effective.top - effective.bottom;
  if (widthPx <= 0 || heightPx <= 0) throw new Error('lab s0: insets exceed the tile.');
  const rgba = new Array(widthPx * heightPx * 4).fill(0);
  for (let y = 0; y < heightPx; y++) {
    const source = ((y + effective.top) * tile.widthPx + effective.left) * 4, destination = y * widthPx * 4;
    for (let index = 0; index < widthPx * 4; index++) rgba[destination + index] = tile.rgba[source + index];
  }
  return { imageId: `composite:${digestOf({ of: tile.imageId, insets: effective })}`.slice(0, 28), widthPx, heightPx, rgba };
}

/** The S0 crop receipt, the seven fields `S0.pcr.yaml` names under `receipt.fields`. */
export function cropReceipt(fullImage, croppedImage, crop) {
  const originalPixelCount = fullImage.widthPx * fullImage.heightPx, croppedPixelCount = croppedImage.widthPx * croppedImage.heightPx;
  const totalPxRemoved = originalPixelCount - croppedPixelCount;
  return {
    originalPx: { width: fullImage.widthPx, height: fullImage.heightPx },
    cropMethod: crop.source,
    upperRowsRemoved: crop.insets?.top ?? 0,
    lowerRowsRemoved: crop.insets?.bottom ?? 0,
    croppedPx: { width: croppedImage.widthPx, height: croppedImage.heightPx },
    totalPxRemoved,
    pctPxRemoved: originalPixelCount === 0 ? 0 : (totalPxRemoved / originalPixelCount) * 100
  };
}

export function registerS0(lab, { cache = new Map() } = {}) {
  lab.register('fn.lab.s0.decodefullimage', ({ source }) => source.decoded);
  lab.register('fn.lab.s0.findchromebounds', ({ image }) => stripChromeProposal(toGray(image)));
  lab.register('fn.lab.s0.applycrop', ({ image, bounds }) => materializeComposite(image, bounds.insets));
  // The LAB's third S0 Tick writes FullImage to a cache and produces no Part
  // (`S0_CACHE_TICK.produces: []`). The studio's PQL refuses a Calculation that
  // publishes nothing, so the cache write publishes its receipt instead
  // (proposal.lab.pql.effecttick).
  lab.register('fn.lab.s0.cachefullimage', ({ image }) => { cache.set(image.imageId, image); return { cached: image.imageId, at: 'last', widthPx: image.widthPx, heightPx: image.heightPx }; });
  return cache;
}

/** The compiled Mermaid S0, lowered and lowercased: the Ticks Decode and Crop. */
export function compiledS0() {
  const compiled = compileMermaidPcr(readFileSync(join(SOURCE, 'S0.mmd'), 'utf8'), JSON.parse(readFileSync(join(SOURCE, 'S0.args.json'), 'utf8')));
  const { document, local } = lowerToPql(compiled);
  return { compiled, local, document: labDocument(document) };
}

/**
 * The S0 PQL document that runs here: the compiled Mermaid graph, plus the one
 * Tick `S0.pcr.yaml` names that the graph does not (`last: cache: FullImage`,
 * the LAB's S0_CACHE_TICK). `withoutCalls(.., ['fn.lab.s0.cachefullimage'])`
 * takes it back to the compiled document exactly, which is what the test checks.
 */
export function s0Document(lab, { cache = true } = {}) {
  const { document } = compiledS0();
  const ticks = [...document.Ticks];
  if (cache) ticks.push({ name: 'Cache', Calculations: [{ call: 'fn.lab.s0.cachefullimage', with: { image: S0_ADDRESSES.fullImage }, args: {}, into: S0_ADDRESSES.cacheReceipt }] });
  return lab.document('S0', ticks);
}

/** Run S0 over one encoded source; returns the run and the crop receipt. */
export function runS0(lab, source) {
  lab.put(S0_ADDRESSES.selectedInput, source);
  const composition = s0Document(lab), { run, receipt } = lab.run('S0', composition);
  const cropped = lab.get(S0_ADDRESSES.canonicalPixels);
  return { run, receipt, composition, fullImage: lab.get(S0_ADDRESSES.fullImage), croppedImage: cropped, crop: lab.get(S0_ADDRESSES.cropBounds), cropReceipt: cropReceipt(lab.get(S0_ADDRESSES.fullImage), cropped, lab.get(S0_ADDRESSES.cropBounds)) };
}
