/**
 * S1, ported: badge assembly and reading, the Stage whose composition ChainSpot
 * writes as a PQL document (`S1/exp/badge-assembly/PrincipleComponentRender.yaml`).
 * That document is read here by the studio's own `readPql`, with its addresses
 * lowercased by one rule (address.js) and its Calculations registered as
 * `fn.lab.*` ports of the TypeScript:
 *
 *   BlackMask / WhiteMask  select an HSV mask, group it 8-connected  (exp/mask-components)
 *   BadgeAssembly          plates, borders, digits, loops, assemble  (exp/badge-assembly)
 *   WhiteDigitRecognition  prepare the glyphs, match them            (exp/badge-assembly/white-recognition)
 *   BadgeOutputs           ownership, owned / muted / remaining px   (exp/badge-assembly/ownership)
 *
 * Ported faithfully: the masks (OpenCV 8-bit saturation and its sdiv table), the
 * union-find 8-connected labelling with raster-scan first-encounter relabelling,
 * the plate predicate, both relation predicates, the assembly acceptance, and
 * every pixel-set query. Reduced: recognition. The LAB matches digits with a
 * logistic model asset over segmented, normalized glyphs; the port normalizes
 * the same way and matches against a template model Part, because the asset and
 * the corpus it was fitted on are not in this repository
 * (proposal.lab.s1.recognition).
 */
import { labAddress, labDocument } from './address.js';
import { readSource, readSourceJson } from './source-data.js';
import { parseYaml } from './yaml.js';
import { compileMermaidPcr, lowerToPql } from './mermaid.js';
import { S0_ADDRESSES } from './s0.js';

/* ---------------------------------------------------------------- masks */
const HSV_SHIFT = 12;
function roundHalfToEven(x) { const floor = Math.floor(x), diff = x - floor; if (diff < 0.5) return floor; if (diff > 0.5) return floor + 1; return floor % 2 === 0 ? floor : floor + 1; }
const sdivTable = (() => { const table = new Array(256).fill(0); for (let index = 1; index < 256; index++) table[index] = roundHalfToEven((255 * (1 << HSV_SHIFT)) / index); return table; })();
/** OpenCV 8-bit HSV saturation for one pixel (detectors/threeFactor/raster.ts). */
export function opencvSaturation(r, g, b) { const v = Math.max(r, g, b), vmin = Math.min(r, g, b); return ((v - vmin) * sdivTable[v] + (1 << (HSV_SHIFT - 1))) >> HSV_SHIFT; }

const FRAME = labAddress('px.course.canonicalPixels');
const partAddress = id => labAddress(`px.s1.exp.maskComponents.part.${id.replace(/-([a-z])/g, (_, letter) => letter.toUpperCase())}`);

export function selectHsvMask({ raster, polarity, valueMax, valueMin, saturationMax }) {
  const pixels = new Array(raster.widthPx * raster.heightPx).fill(0);
  for (let index = 0, rgba = 0; index < pixels.length; index++, rgba += 4) {
    const r = raster.pixels[rgba], g = raster.pixels[rgba + 1], b = raster.pixels[rgba + 2], value = Math.max(r, g, b);
    pixels[index] = polarity === 'black' ? Number(value <= valueMax) : Number(value >= valueMin && opencvSaturation(r, g, b) <= saturationMax);
  }
  const id = `${polarity}-mask`;
  return { id, address: partAddress(id), kind: 'mask', polarity, widthPx: raster.widthPx, heightPx: raster.heightPx, coordinateFrameId: FRAME, pixels, sourceTickId: null };
}

/** `extractComponents`: union-find over provisional labels, compacted in raster-scan first-encounter order. */
export function labelComponents({ widthPx, heightPx, pixels }) {
  const total = widthPx * heightPx, labels = new Array(total).fill(0), parent = [0];
  const find = a => { let root = a; while (parent[root] !== root) root = parent[root]; while (parent[a] !== root) { const next = parent[a]; parent[a] = root; a = next; } return root; };
  const union = (a, b) => { const ra = find(a), rb = find(b); if (ra !== rb) { if (ra < rb) parent[rb] = ra; else parent[ra] = rb; } };
  let next = 1;
  for (let y = 0; y < heightPx; y++) {
    const row = y * widthPx, previous = row - widthPx;
    for (let x = 0; x < widthPx; x++) {
      if (!pixels[row + x]) continue;
      let best = 0;
      const tryNeighbor = index => { const label = labels[index]; if (label) { if (!best) best = label; else if (label !== best) union(best, label); } };
      if (x > 0 && pixels[row + x - 1]) tryNeighbor(row + x - 1);
      if (y > 0) {
        if (pixels[previous + x]) tryNeighbor(previous + x);
        if (x > 0 && pixels[previous + x - 1]) tryNeighbor(previous + x - 1);
        if (x < widthPx - 1 && pixels[previous + x + 1]) tryNeighbor(previous + x + 1);
      }
      if (!best) { best = next++; parent.push(best); }
      labels[row + x] = best;
    }
  }
  const remap = new Array(next).fill(0);
  let finalCount = 0;
  for (let index = 0; index < total; index++) { const label = labels[index]; if (!label) continue; const root = find(label); if (!remap[root]) remap[root] = ++finalCount; labels[index] = remap[root]; }
  return { labels, count: finalCount };
}

export function group8Connected({ mask, connectivity, retainSingletons }) {
  if (connectivity !== 8 || !retainSingletons) throw new Error('lab s1: only the known-good 8-connected singleton-retaining grouping is declared.');
  const { labels } = labelComponents(mask), groups = new Map();
  for (let index = 0; index < labels.length; index++) { const label = labels[index]; if (!label) continue; (groups.get(label) ?? groups.set(label, []).get(label)).push(index); }
  const ordered = [...groups.entries()].sort(([left], [right]) => left - right);
  const pixels = ordered.flatMap(([, members]) => members);
  const components = ordered.map(([label, members]) => {
    const id = `${mask.polarity}-component-${label}`;
    return { id, address: partAddress(id), kind: 'component', polarity: mask.polarity, label, widthPx: mask.widthPx, heightPx: mask.heightPx, coordinateFrameId: FRAME, pixels: members, sourceTickId: null };
  });
  const id = `${mask.polarity}-components`;
  return { id, address: partAddress(id), kind: 'component-set', polarity: mask.polarity, widthPx: mask.widthPx, heightPx: mask.heightPx, coordinateFrameId: FRAME, pixels, components, sourceTickId: null };
}

/* ------------------------------------------------------- badge assembly */
function measure(part) {
  if (!part.pixels.length) throw new Error(`lab s1: cannot measure empty component ${part.id}.`);
  let minX = Infinity, minY = Infinity, maxX = -1, maxY = -1;
  for (const pixel of part.pixels) {
    const x = pixel % part.widthPx, y = Math.floor(pixel / part.widthPx);
    minX = Math.min(minX, x); maxX = Math.max(maxX, x); minY = Math.min(minY, y); maxY = Math.max(maxY, y);
  }
  return { part, area: part.pixels.length, bbox: [minX, minY, maxX - minX + 1, maxY - minY + 1] };
}
const containsBbox = (outer, inner) => outer[0] <= inner[0] && outer[1] <= inner[1] && outer[0] + outer[2] >= inner[0] + inner[2] && outer[1] + outer[3] >= inner[1] + inner[3];

export function selectComponents(args) {
  if (args.predicate !== 'plate-bbox-and-fill') throw new Error(`lab s1: unknown plate predicate: ${args.predicate}`);
  const selected = [], rejected = [];
  for (const part of args.components.components) {
    const component = measure(part), [, , width, height] = component.bbox, reasons = [];
    if (width < args.minWidth || width > args.maxWidth) reasons.push('width outside range');
    if (height < args.minHeight || height > args.maxHeight) reasons.push('height outside range');
    if (width / height < args.minAspect || width / height > args.maxAspect) reasons.push('aspect outside range');
    if (component.area / (width * height) < args.minFill) reasons.push('fill below minimum');
    if (reasons.length) rejected.push({ component, reasons }); else selected.push(component);
  }
  return { selected, rejected };
}

export function findRelated({ anchors, candidates, anchorRole, predicate }) {
  if (predicate !== 'candidate-bbox-contains-anchor' && predicate !== 'anchor-bbox-contains-candidate') throw new Error(`lab s1: unknown relationship predicate: ${predicate}`);
  let resolved;
  if (anchorRole === 'plate' && 'selected' in anchors) resolved = anchors.selected.map(plate => ({ plate, anchor: plate }));
  else if (anchorRole === 'related-component' && 'rows' in anchors) resolved = anchors.rows.flatMap(row => row.matches.map(anchor => ({ plate: row.plate, anchor })));
  else throw new Error('lab s1: relationship input does not match declared anchorRole.');
  const measured = candidates.components.map(measure);
  return { predicate, rows: resolved.map(({ plate, anchor }) => ({ plate, anchor, matches: measured.filter(candidate => {
    if (candidate.part.coordinateFrameId !== anchor.part.coordinateFrameId || candidate.part.widthPx !== anchor.part.widthPx || candidate.part.heightPx !== anchor.part.heightPx) throw new Error('lab s1: cannot relate components in different raster frames.');
    return predicate === 'candidate-bbox-contains-anchor' ? containsBbox(candidate.bbox, anchor.bbox) : containsBbox(anchor.bbox, candidate.bbox);
  }) })) };
}

const same = (left, right) => left.part.id === right.part.id;

export function assemble({ plates, plateBorders, plateDigits, digitLoops, acceptance }) {
  if (acceptance !== 'border-and-digit-material') throw new Error(`lab s1: unknown assembly predicate: ${acceptance}`);
  const candidates = [], incomplete = [];
  for (const plate of plates.selected) {
    const borders = plateBorders.rows.filter(row => same(row.plate, plate)).flatMap(row => row.matches);
    const digits = plateDigits.rows.filter(row => same(row.plate, plate)).flatMap(row => row.matches);
    if (!borders.length || !digits.length) { incomplete.push({ plate, borders, digits, reason: !borders.length ? 'no enclosing white border' : 'no contained white digit material' }); continue; }
    for (const border of borders) {
      const digitParts = digits.filter(digit => !same(digit, border));
      if (!digitParts.length) { incomplete.push({ plate, borders: [border], digits: digitParts, reason: 'border leaves no separate digit material' }); continue; }
      const loops = digitLoops.rows.filter(row => same(row.plate, plate) && digitParts.some(digit => same(digit, row.anchor)));
      const parts = [plate, border, ...digitParts, ...loops.flatMap(row => row.matches)];
      const pixels = [...new Set(parts.flatMap(item => item.part.pixels))].sort((a, b) => a - b);
      candidates.push({ id: `badge-candidate:${plate.part.id}:${border.part.id}`, plate, border, digits: digitParts, digitLoops: loops, pixels });
    }
  }
  return { candidates, incomplete };
}

/* --------------------------------------------------- white digit reading */
/** Normalize one digit's mask into the knobs' digitW x digitH grid, nearest sample. */
function normalize(part, bbox, { digitW, digitH }) {
  const member = new Set(part.pixels), [x0, y0, width, height] = bbox, cells = new Array(digitW * digitH).fill(0);
  for (let y = 0; y < digitH; y++) for (let x = 0; x < digitW; x++) {
    const sx = x0 + Math.min(width - 1, Math.floor((x * width) / digitW)), sy = y0 + Math.min(height - 1, Math.floor((y * height) / digitH));
    cells[y * digitW + x] = member.has(sy * part.widthPx + sx) ? 1 : 0;
  }
  return cells;
}

export function prepareDigits({ badges, knobs }) {
  return {
    badges: badges.candidates.map(badge => ({
      badge,
      glyph: { origin: [badge.border.bbox[0], badge.border.bbox[1]], width: badge.border.bbox[2], height: badge.border.bbox[3], pixels: badge.pixels },
      digits: [...badge.digits].sort((left, right) => left.bbox[0] - right.bbox[0]).filter(digit => digit.area >= knobs.minComponentArea)
        .map(digit => ({ bbox: digit.bbox, method: 'cc', normalized: normalize(digit.part, digit.bbox, knobs), notes: [] })),
      notes: []
    })),
    incomplete: badges.incomplete
  };
}

export function matchDigits({ prepared, model }) {
  const score = (cells, template) => cells.reduce((sum, value, index) => sum + (value === template[index] ? 1 : 0), 0) / cells.length;
  return {
    candidates: prepared.badges.map(entry => {
      const digits = entry.digits.map(digit => {
        const rankings = model.labels.map(label => ({ label, score: score(digit.normalized, model.templates[label]) })).sort((left, right) => right.score - left.score || left.label.localeCompare(right.label));
        return { ...digit, rankings };
      });
      const confident = digits.every(digit => digit.rankings[0].score >= model.floor && digit.rankings[0].score - digit.rankings[1].score >= model.margin);
      return { ...entry.badge, reading: { value: confident ? digits.map(digit => digit.rankings[0].label).join('') : null, status: confident ? 'read' : 'unread', digits } };
    }),
    incomplete: prepared.incomplete
  };
}

/* ---------------------------------------------------------- badge outputs */
const pixelSet = (raster, id, pixels) => ({ kind: 'pixel-set', id, widthPx: raster.widthPx, heightPx: raster.heightPx, coordinateFrameId: FRAME, pixels: [...pixels] });
function badgeMutedPixels(badge) {
  const [x, y, width, height] = badge.unaccountedButOwned.bbox, rasterWidth = badge.plate.part.widthPx, rasterHeight = badge.plate.part.heightPx, pixels = [];
  for (let py = Math.max(0, y); py < Math.min(rasterHeight, y + height); py++) for (let px = Math.max(0, x); px < Math.min(rasterWidth, x + width); px++) pixels.push(py * rasterWidth + px);
  return pixels;
}
export function declareOwnership({ recognized }) {
  return recognized.candidates.map(badge => ({ ...badge, unaccountedButOwned: { rule: 'outer-border-bbox', outerBorder: badge.border.part.id, bbox: badge.border.bbox } }));
}
export function ownedPixels({ badges, raster }) { return pixelSet(raster, 'badge-component-pixels', [...new Set(badges.flatMap(badge => badge.pixels))].sort((a, b) => a - b)); }
export function mutedPixels({ badges, owned, raster }) {
  const explained = new Set(owned.pixels), extra = new Set();
  for (const badge of badges) for (const pixel of badgeMutedPixels(badge)) if (!explained.has(pixel)) extra.add(pixel);
  return pixelSet(raster, 'unaccounted-but-owned', [...extra].sort((a, b) => a - b));
}
export function remainingPixels({ owned, muted, raster }) {
  const excluded = new Uint8Array(raster.widthPx * raster.heightPx);
  for (const pixel of owned.pixels) excluded[pixel] = 1;
  for (const pixel of muted.pixels) excluded[pixel] = 1;
  const pixels = [];
  for (let pixel = 0; pixel < excluded.length; pixel++) if (!excluded[pixel]) pixels.push(pixel);
  return pixelSet(raster, 'remaining-after-badges', pixels);
}

/** The raster adapter the Mermaid S1 computes and the YAML path seeds warm. */
export function asMaskRaster(image) {
  return { id: 'cropped-raster', address: partAddress('cropped-raster'), kind: 'cropped-raster', widthPx: image.widthPx, heightPx: image.heightPx, coordinateFrameId: FRAME, pixels: image.rgba, pixelFormat: 'rgba-8', sourceAddress: FRAME, sourceTickId: null };
}

export function registerS1(lab) {
  lab.register(labAddress('fn.s0.asMaskRaster'), ({ image }) => asMaskRaster(image));
  lab.register(labAddress('fn.s1.exp.maskComponents.selectHsvMask'), selectHsvMask);
  lab.register(labAddress('fn.s1.exp.maskComponents.group8Connected'), group8Connected);
  lab.register(labAddress('fn.s1.exp.badgeAssembly.selectComponents'), selectComponents);
  lab.register(labAddress('fn.s1.exp.badgeAssembly.findRelated'), findRelated);
  lab.register(labAddress('fn.s1.exp.badgeAssembly.assemble'), assemble);
  lab.register(labAddress('fn.s1.whiteDigits.prepare'), prepareDigits);
  lab.register(labAddress('fn.s1.whiteDigits.match'), matchDigits);
  lab.register(labAddress('fn.s1.badges.declareOwnership'), declareOwnership);
  lab.register(labAddress('fn.s1.badges.ownedPixels'), ownedPixels);
  lab.register(labAddress('fn.s1.badges.mutedPixels'), mutedPixels);
  lab.register(labAddress('fn.s1.badges.remainingPixels'), remainingPixels);
}

/* --------------------------------------------------------- the documents */

export const S1_ADDRESSES = {
  croppedRaster: labAddress('px.s1.exp.maskComponents.part.croppedRaster'),
  model: labAddress('px.s1.whiteDigits.model'),
  outputs: ['px.badges.objects', 'px.badges.px', 'px.badges.muted', 'px.remaining.afterBadges'].map(labAddress)
};

/** The LAB's S1 document, lowercased: the baseline path, with the raster seeded warm. */
export function s1YamlDocument(lab) { return lab.document('S1', labDocument(parseYaml(readSource('S1.pcr.yaml'))).Ticks); }

/** The compiled Mermaid S1: the same Calculations, plus the RasterInput Tick that computes the warm raster. */
export function s1MermaidDocument(lab) {
  const compiled = compileMermaidPcr(readSource('S1.mmd'), readSourceJson('S1.args.json'));
  return lab.document('S1-mermaid', labDocument(lowerToPql(compiled).document).Ticks);
}

/**
 * The digit model Part: one normalized template per label, built from the two
 * glyph shapes the fixture draws (a solid bar, and a ring of thickness 3), at
 * the knobs' digitW x digitH. The LAB fits a logistic model on a corpus instead.
 */
export function digitModel(knobs) {
  const shape = (width, height, inside) => {
    const pixels = [];
    for (let y = 0; y < height; y++) for (let x = 0; x < width; x++) if (inside(x, y)) pixels.push(y * width + x);
    return { widthPx: width, heightPx: height, pixels };
  };
  const bar = shape(6, 20, () => true), ring = shape(12, 20, (x, y) => x < 3 || x >= 9 || y < 3 || y >= 17);
  return {
    for: 'the digit templates this port matches against, in place of the LAB logistic model asset',
    labels: ['1', '0'], floor: 0.8, margin: 0.05,
    templates: { 1: normalize(bar, [0, 0, 6, 20], knobs), 0: normalize(ring, [0, 0, 12, 20], knobs) }
  };
}

/** Seed one board for S1 and run one of its two documents. */
export function runS1(lab, { croppedImage, document, seedRaster }) {
  lab.put(S0_ADDRESSES.canonicalPixels, croppedImage);
  const knobs = labDocument(parseYaml(readSource('S1.pcr.yaml'))).Ticks.find(tick => tick.name === 'WhiteDigitRecognition').Calculations[0].args.knobs;
  lab.put(S1_ADDRESSES.model, digitModel(knobs));
  if (seedRaster) lab.put(S1_ADDRESSES.croppedRaster, asMaskRaster(croppedImage));
  const { run, receipt } = lab.run(document.PrincipleComponentRender, document);
  return { run, receipt, badges: lab.get(labAddress('px.badges.objects')), outputs: Object.fromEntries(S1_ADDRESSES.outputs.map(address => [address, lab.get(address)])) };
}
