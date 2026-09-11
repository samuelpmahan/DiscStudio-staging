/**
 * S2, ported: basket detection. "Construct Basket objects from exact bright-body
 * and dark-shell component pixels" (S2/clean/index.ts).
 *
 * Like S0, S2 has no PQL document in ChainSpot: its composition is three
 * `OperationSpec` Ticks (`Basket.detectFamily`, `Basket.findShellFamily`,
 * `Basket.findPx`) with their `consumes`/`produces`/`calculations` declared, run
 * by the gateway. Those three declarations ARE a PQL document -- each names one
 * Calculation, the addresses it reads and the address it writes -- so the port
 * writes that document out and runs it, the way it did for S0.
 *
 * What S2 consumes is not S1's badges but the generic substrate S1 publishes
 * beside them (`px.components`, bright and dark masks plus their labelled
 * components: `stages/componentPxC.ts`), so the port publishes that substrate
 * from the S1 masks in a Tick of its own -- the LAB's own `components.publish`.
 *
 * Ported faithfully: the sprite family test (exact bbox, area ratio 0.96..1.03,
 * template coverage >= 0.96), the modal shell learner (smallest enclosing dark
 * component, exact margins, no tolerance, ties refuse), the 75% shell consensus,
 * and the basket pixels (white body labels + agreed dark shell pixels).
 */
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { labAddress } from './address.js';
import { SOURCE } from './source.js';
import { labelComponents } from './s1.js';

export const SPRITE = JSON.parse(readFileSync(join(SOURCE, 'basket-sprite.json'), 'utf8'));
const templateWhiteOffsets = SPRITE.rows.flatMap((row, y) => [...row].flatMap((value, x) => (value === '1' ? [y * SPRITE.width + x] : [])));

export const S2_ADDRESSES = {
  masks: labAddress('px.components.masks'),
  fields: labAddress('px.components'),
  family: labAddress('px.baskets.family'),
  shellFamily: labAddress('px.baskets.shellFamily'),
  objects: labAddress('px.baskets')
};

/**
 * The major axis of a component's second moments, as the LAB computes it:
 * LAPACK's deflation test first (a symmetric glyph's ~1e-16 off-diagonal
 * residue must give exact identity eigenvectors), then dlaev2's eigenvector of
 * the larger eigenvalue, then the sign normalization. Ported verbatim, because
 * S3's family vote compares major and minor extents across components and a
 * mirrored axis changes which tees are a family (`components.ts majorAxisOf`).
 */
export function majorAxisOf(cxx, cxy, cyy) {
  const EPS = 1.1102230246251565e-16, SAFMIN = 2.2250738585072014e-308;
  let ax, ay;
  if (cxy * cxy <= EPS * EPS * Math.abs(cxx) * Math.abs(cyy) + SAFMIN) {
    if (cyy > cxx) { ax = 0; ay = 1; } else { ax = 1; ay = 0; }
  } else {
    const a = cxx, b = cxy, c = cyy, sm = a + c, df = a - c, adf = Math.abs(df), tb = b + b, ab = Math.abs(tb);
    const rt = adf > ab ? adf * Math.sqrt(1 + (ab / adf) ** 2) : adf < ab ? ab * Math.sqrt(1 + (adf / ab) ** 2) : ab * Math.sqrt(2);
    const sgn1 = sm < 0 ? -1 : 1;
    const cs = df >= 0 ? df + rt : df - rt, sgn2 = df >= 0 ? 1 : -1, acs = Math.abs(cs);
    let cs1, sn1;
    if (acs > ab) { const ct = -tb / cs; sn1 = 1 / Math.sqrt(1 + ct * ct); cs1 = ct * sn1; }
    else if (ab === 0) { cs1 = 1; sn1 = 0; }
    else { const tn = -cs / tb; cs1 = 1 / Math.sqrt(1 + tn * tn); sn1 = tn * cs1; }
    if (sgn1 === sgn2) { const tn = cs1; cs1 = -sn1; sn1 = tn; }
    ax = cs1; ay = sn1;
  }
  if (ax < 0 || (Math.abs(ax) < 1e-9 && ay < 0)) { ax = -ax; ay = -ay; }
  return { ax, ay };
}

/** `ComponentStats` for one component: bbox and area for S2, the PCA extents and angle for S3. */
export function statsOf(component) {
  let minX = Infinity, minY = Infinity, maxX = -1, maxY = -1, sumX = 0, sumY = 0;
  const xs = [], ys = [];
  for (const pixel of component.pixels) {
    const x = pixel % component.widthPx, y = Math.floor(pixel / component.widthPx);
    minX = Math.min(minX, x); maxX = Math.max(maxX, x); minY = Math.min(minY, y); maxY = Math.max(maxY, y); sumX += x; sumY += y; xs.push(x); ys.push(y);
  }
  const area = component.pixels.length, cx = sumX / area, cy = sumY / area;
  const base = { label: component.label, area, cx, cy, bboxX: minX, bboxY: minY, bboxW: maxX - minX + 1, bboxH: maxY - minY + 1 };
  if (area < 2) return { ...base, major: 1, minor: 1, angle: 0, fill: 1 };
  let cxx = 0, cxy = 0, cyy = 0;
  for (let index = 0; index < area; index++) { const dx = xs[index] - cx, dy = ys[index] - cy; cxx += dx * dx; cxy += dx * dy; cyy += dy * dy; }
  cxx /= area; cxy /= area; cyy /= area;
  const { ax, ay } = majorAxisOf(cxx, cxy, cyy), mx = -ay, my = ax;
  let uMin = Infinity, uMax = -Infinity, vMin = Infinity, vMax = -Infinity;
  for (let index = 0; index < area; index++) {
    const dx = xs[index] - cx, dy = ys[index] - cy, u = dx * ax + dy * ay, v = dx * mx + dy * my;
    uMin = Math.min(uMin, u); uMax = Math.max(uMax, u); vMin = Math.min(vMin, v); vMax = Math.max(vMax, v);
  }
  let major = uMax - uMin + 1, minor = vMax - vMin + 1;
  if (minor > major) { const swap = major; major = minor; minor = swap; }
  return { ...base, major, minor, angle: Math.atan2(ay, ax), fill: area / Math.max(major * minor, 1) };
}

/** The LAB's `components.publish`: the inherited mask and component results as one generic substrate. */
export function publishComponents({ blackMask, blackComponents, whiteMask, whiteComponents }) {
  const field = (mask, set) => ({
    mask: { width: mask.widthPx, height: mask.heightPx, data: mask.pixels },
    labels: labelComponents(mask).labels,
    components: set.components.map(statsOf)
  });
  return { bright: field(whiteMask, whiteComponents), dark: field(blackMask, blackComponents) };
}

function templateCoverage(body, fields) {
  let hit = 0;
  for (const offset of templateWhiteOffsets) {
    const x = offset % SPRITE.width, y = (offset - x) / SPRITE.width;
    if (fields.bright.labels[(body.bboxY + y) * fields.bright.mask.width + body.bboxX + x] === body.label) hit++;
  }
  return hit / Math.max(1, templateWhiteOffsets.length);
}

export function detectFamily({ fields }) {
  const members = fields.bright.components.flatMap(body => {
    if (body.bboxW !== SPRITE.width || body.bboxH !== SPRITE.height) return [];
    const areaRatio = body.area / Math.max(1, templateWhiteOffsets.length), whiteCoverage = templateCoverage(body, fields);
    if (areaRatio < 0.96 || areaRatio > 1.03 || whiteCoverage < 0.96) return [];
    return [{ body, areaRatio, whiteCoverage }];
  });
  return { templateSize: [SPRITE.width, SPRITE.height], members };
}

const bboxOf = stats => [stats.bboxX, stats.bboxY, stats.bboxW, stats.bboxH];
const contains = (outer, inner) => outer[0] <= inner[0] && outer[1] <= inner[1] && outer[0] + outer[2] >= inner[0] + inner[2] && outer[1] + outer[3] >= inner[1] + inner[3];

function smallestEnclosingDark(body, darkComponents) {
  return darkComponents.filter(component => contains(bboxOf(component), bboxOf(body)))
    .sort((a, b) => a.bboxW * a.bboxH - b.bboxW * b.bboxH || b.area - a.area || a.label - b.label)[0] ?? null;
}
const shellMargins = (outer, body) => [body.bboxX - outer.bboxX, body.bboxY - outer.bboxY, outer.bboxX + outer.bboxW - (body.bboxX + body.bboxW), outer.bboxY + outer.bboxH - (body.bboxY + body.bboxH)];

/** Exact modal component geometry, no tolerance: a tie refuses the family. */
export function learnShellMargins(bodies, darkComponents) {
  const counts = new Map();
  for (const body of bodies) {
    const shell = smallestEnclosingDark(body, darkComponents);
    if (!shell) continue;
    const margins = shellMargins(shell, body), key = margins.join(',');
    counts.set(key, { margins, count: (counts.get(key)?.count ?? 0) + 1 });
  }
  const ranked = [...counts.values()].sort((a, b) => b.count - a.count || a.margins.join(',').localeCompare(b.margins.join(',')));
  if (!ranked.length) return null;
  if (ranked.length > 1 && ranked[0].count === ranked[1].count) return null;
  return ranked[0].margins;
}

export function findShellFamily({ family, fields }) {
  const margins = learnShellMargins(family.members.map(member => member.body), fields.dark.components);
  if (!margins) return { margins: null, shellOffsets: [], members: [] };
  const [left, top, right, bottom] = margins;
  const shellWidth = SPRITE.width + left + right, shellHeight = SPRITE.height + top + bottom;
  const counts = new Array(shellWidth * shellHeight).fill(0);
  for (const { body } of family.members) {
    const x0 = body.bboxX - left, y0 = body.bboxY - top;
    for (let y = 0; y < shellHeight; y++) {
      const row = (y0 + y) * fields.dark.mask.width + x0;
      for (let x = 0; x < shellWidth; x++) if (fields.dark.mask.data[row + x]) counts[y * shellWidth + x]++;
    }
  }
  const consensus = Math.ceil(family.members.length * 0.75);
  const shellOffsets = counts.flatMap((count, offset) => (count >= consensus ? [offset] : []));
  return {
    margins, shellOffsets,
    members: family.members.map(candidate => {
      const x0 = candidate.body.bboxX - left, y0 = candidate.body.bboxY - top;
      const blackPx = shellOffsets.flatMap(offset => {
        const x = offset % shellWidth, y = (offset - x) / shellWidth, pixel = (y0 + y) * fields.dark.mask.width + x0 + x;
        return fields.dark.mask.data[pixel] ? [pixel] : [];
      });
      return { candidate, bbox: [x0, y0, shellWidth, shellHeight], blackPx };
    })
  };
}

function materializeComponentPixels(stats, labels, width, height) {
  const pixels = [];
  for (let y = Math.max(0, stats.bboxY); y < Math.min(height, stats.bboxY + stats.bboxH); y++)
    for (let x = Math.max(0, stats.bboxX); x < Math.min(width, stats.bboxX + stats.bboxW); x++)
      if (labels[y * width + x] === stats.label) pixels.push(y * width + x);
  return pixels;
}

/**
 * The LAB calls `fn.Basket.findPx` once per shell member inside one Tick (a loop
 * in `Basket.findPx`). A PQL document names a Calculation once, so the port's
 * Calculation maps over the members and publishes the Basket objects
 * (proposal.lab.pql.fanout).
 */
export function findPx({ shellFamily, fields }) {
  if (!shellFamily.margins) return [];
  const { width, height } = { width: fields.bright.mask.width, height: fields.bright.mask.height };
  return shellFamily.members.map(member => {
    const whitePixels = materializeComponentPixels(member.candidate.body, fields.bright.labels, width, height);
    const px = [...whitePixels, ...member.blackPx].sort((a, b) => a - b);
    return {
      bbox: member.bbox, px, whitePx: whitePixels.length, blackPx: member.blackPx.length,
      has: {
        detectFamily: { fn: labAddress('fn.Basket.detectFamily'), body: { polarity: 'bright', label: member.candidate.body.label, bbox: bboxOf(member.candidate.body) } },
        findShellFamily: { fn: labAddress('fn.Basket.findShellFamily'), margins: shellFamily.margins, blackPx: member.blackPx.length },
        findPx: { fn: labAddress('fn.Basket.findPx'), body: { polarity: 'bright', label: member.candidate.body.label } }
      }
    };
  });
}

export function registerS2(lab) {
  lab.register(labAddress('fn.components.publish'), publishComponents);
  lab.register(labAddress('fn.Basket.detectFamily'), detectFamily);
  lab.register(labAddress('fn.Basket.findShellFamily'), findShellFamily);
  lab.register(labAddress('fn.Basket.findPx'), findPx);
}

/** The document the three S2 OperationSpecs imply, with the substrate Tick S1 publishes in front of it. */
export function s2Document(lab) {
  const s1 = address => labAddress(`px.s1.exp.maskComponents.part.${address}`);
  return lab.document('S2', [
    { name: 'components.publish', Calculations: [{ call: labAddress('fn.components.publish'), with: { blackMask: s1('blackMask'), blackComponents: s1('blackComponents'), whiteMask: s1('whiteMask'), whiteComponents: s1('whiteComponents') }, args: {}, into: S2_ADDRESSES.fields }] },
    { name: 'Basket.detectFamily', Calculations: [{ call: labAddress('fn.Basket.detectFamily'), with: { fields: S2_ADDRESSES.fields }, args: {}, into: S2_ADDRESSES.family }] },
    { name: 'Basket.findShellFamily', Calculations: [{ call: labAddress('fn.Basket.findShellFamily'), with: { family: S2_ADDRESSES.family, fields: S2_ADDRESSES.fields }, args: {}, into: S2_ADDRESSES.shellFamily }] },
    { name: 'Basket.findPx', Calculations: [{ call: labAddress('fn.Basket.findPx'), with: { shellFamily: S2_ADDRESSES.shellFamily, fields: S2_ADDRESSES.fields }, args: {}, into: S2_ADDRESSES.objects }] }
  ]);
}

export function runS2(lab) {
  const composition = s2Document(lab), { run, receipt } = lab.run('S2', composition);
  return { run, receipt, composition, fields: lab.get(S2_ADDRESSES.fields), family: lab.get(S2_ADDRESSES.family), shellFamily: lab.get(S2_ADDRESSES.shellFamily), baskets: lab.get(S2_ADDRESSES.objects) };
}
