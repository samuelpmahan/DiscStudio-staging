/**
 * S3, ported: visible Tee detection. "Construct visible Tee objects from exact
 * accepted bright-component pixels" (S3/clean/index.ts), three OperationSpec
 * Ticks like S2 -- `Tee.detectRings`, `Tee.findFamily`, `Tee.findPx` -- so the
 * port writes out the document they declare and runs it.
 *
 * The detector is the enclosed-hole one (`detectors/threeFactor/endpoints.ts`):
 * flood the non-bright background in from the border, and any non-bright pixel
 * left over is a hole fully enclosed by bright pixels. A small elongated hole
 * inside a mostly-bright ring band is a tee glyph. The flood runs against a
 * dilated copy of the mask at radii 0..3 so a 1-4px gap in an outline does not
 * leak the hole to background, and detections merge across radii.
 *
 * S3 consumes what S1 and S2 leave: the generic component substrate (px.components)
 * and S1's Badge objects, whose mute footprint excludes rings that are really
 * badge digit holes. That exclusion is not incidental here: the fixture's badge
 * digit "0" has exactly such a hole, and it is what `excludedByBadge` catches.
 *
 * Beside the Stage, the port also runs the Python analogue's accounting PCR
 * (`experiments/quick-anno-python/s3.py` at 6309ff1): two Ticks, AccountRings
 * then CheckBalance reading the first's published Part, whose balance is the
 * oracle for this Stage's drop surface -- every enclosed ring leaves through
 * exactly one named door.
 */
import { labAddress } from './address.js';
import { statsOf } from './s2.js';

export const S3_ADDRESSES = {
  rings: labAddress('px.tees.rings'),
  family: labAddress('px.tees.family'),
  objects: labAddress('px.tees'),
  ledger: 'px.exp.lab.s3.ringledger',
  summary: 'px.exp.lab.s3.teesummary'
};

/** `DEFAULT_ENDPOINTS_KNOBS`, the subset the enclosed-hole path reads. */
export const ENDPOINTS_KNOBS = {
  holeAreaMin: 10, holeAreaMax: 480, holeDimMax: 44, ringBand: 3, ringFracMin: 0.6,
  dilationRadii: [0, 1, 2, 3], largeRadiiThreshold: 2, largeRadiiAreaMin: 40,
  ringMergeProximity: 10, elongationThreshold: 1.18
};
const FRAME_AREA_MIN = 10, FRAME_AREA_MAX = 500, FRAME_MAX_WIDTH = 50, FRAME_MAX_HEIGHT = 50;
const MAJOR_RATIO = 1.25, MINOR_RATIO = 1.25, AREA_RATIO = 1.5;

function dilate(data, width, height, radius) {
  let wall = data;
  for (let iteration = 0; iteration < radius; iteration++) {
    const source = wall, next = new Uint8Array(width * height);
    for (let y = 0; y < height; y++) for (let x = 0; x < width; x++) {
      let on = 0;
      for (let dy = -1; dy <= 1 && !on; dy++) {
        const yy = y + dy;
        if (yy < 0 || yy >= height) continue;
        for (let dx = -1; dx <= 1; dx++) { const xx = x + dx; if (xx >= 0 && xx < width && source[yy * width + xx]) { on = 1; break; } }
      }
      next[y * width + x] = on;
    }
    wall = next;
  }
  return wall;
}

export function detectTeeRingsPass(bright, wallRadius, areaMin, knobs = ENDPOINTS_KNOBS) {
  const width = bright.width, height = bright.height, data = bright.data, total = width * height;
  const wall = dilate(data, width, height, wallRadius);
  const state = new Uint8Array(total);                       // 0 unknown, 1 background, 2 wall, 3 hole
  for (let index = 0; index < total; index++) if (wall[index]) state[index] = 2;
  const stack = [], pushBackground = index => { if (state[index] === 0) { state[index] = 1; stack.push(index); } };
  for (let x = 0; x < width; x++) { pushBackground(x); pushBackground((height - 1) * width + x); }
  for (let y = 0; y < height; y++) { pushBackground(y * width); pushBackground(y * width + width - 1); }
  while (stack.length) {
    const index = stack.pop(), x = index % width;
    if (x > 0) pushBackground(index - 1);
    if (x < width - 1) pushBackground(index + 1);
    if (index >= width) pushBackground(index - width);
    if (index < total - width) pushBackground(index + width);
  }
  const out = [];
  for (let seed = 0; seed < total; seed++) {
    if (state[seed] !== 0) continue;
    const cells = [], holeStack = [seed];
    state[seed] = 3;
    let overflow = false;
    while (holeStack.length) {
      const index = holeStack.pop();
      cells.push(index);
      if (cells.length > knobs.holeAreaMax * 4) overflow = true;
      const x = index % width;
      for (const next of [index - 1, index + 1, index - width, index + width]) {
        if (next < 0 || next >= total) continue;
        if ((next === index - 1 && x === 0) || (next === index + 1 && x === width - 1)) continue;
        if (state[next] === 0) { state[next] = 3; holeStack.push(next); }
      }
    }
    if (overflow || cells.length < areaMin || cells.length > knobs.holeAreaMax) continue;
    let x0 = width, x1 = -1, y0 = height, y1 = -1, sx = 0, sy = 0;
    for (const index of cells) {
      const x = index % width, y = (index - x) / width;
      x0 = Math.min(x0, x); x1 = Math.max(x1, x); y0 = Math.min(y0, y); y1 = Math.max(y1, y); sx += x; sy += y;
    }
    const bw = x1 - x0 + 1, bh = y1 - y0 + 1;
    if (bw > knobs.holeDimMax || bh > knobs.holeDimMax) continue;
    const cx = sx / cells.length, cy = sy / cells.length;
    let mxx = 0, myy = 0, mxy = 0;
    for (const index of cells) {
      const x = (index % width) - cx, y = (index - (index % width)) / width - cy;
      mxx += x * x; myy += y * y; mxy += x * y;
    }
    mxx /= cells.length; myy /= cells.length; mxy /= cells.length;
    const trace = mxx + myy, determinant = mxx * myy - mxy * mxy;
    const discriminant = Math.sqrt(Math.max(0, (trace * trace) / 4 - determinant));
    const lambda1 = trace / 2 + discriminant, lambda2 = Math.max(trace / 2 - discriminant, 1e-6);
    const elongation = Math.sqrt(lambda1 / lambda2);
    const angle = (Math.atan2(2 * mxy, mxx - myy) / 2 + Math.PI) % Math.PI;
    // The ring band hugs the hole (8-neighbour dilation of the hole itself), not its bbox.
    const lw = bw + 2 * knobs.ringBand, lh = bh + 2 * knobs.ringBand;
    let grid = new Uint8Array(lw * lh);
    for (const index of cells) grid[((index - (index % width)) / width - y0 + knobs.ringBand) * lw + ((index % width) - x0 + knobs.ringBand)] = 1;
    for (let iteration = 0; iteration < knobs.ringBand; iteration++) grid = dilate(grid, lw, lh, 1);
    let ringOn = 0, ringTotal = 0;
    for (let y = 0; y < lh; y++) for (let x = 0; x < lw; x++) {
      if (!grid[y * lw + x]) continue;
      const sxp = x0 - knobs.ringBand + x, syp = y0 - knobs.ringBand + y;
      if (sxp < 0 || sxp >= width || syp < 0 || syp >= height) continue;
      const index = syp * width + sxp;
      if (state[index] === 3) continue;
      ringTotal++;
      if (data[index]) ringOn++;
    }
    const ringFrac = ringTotal ? ringOn / ringTotal : 0;
    if (ringFrac < knobs.ringFracMin) continue;
    out.push({ cx, cy, holeArea: cells.length, bboxX: x0, bboxY: y0, bboxW: bw, bboxH: bh, angle, elongation, ringFrac, kind: elongation >= knobs.elongationThreshold ? 'tee-rect' : 'diamond' });
  }
  return out;
}

export function detectTeeRings(bright, knobs = ENDPOINTS_KNOBS) {
  const merged = [];
  for (const radius of knobs.dilationRadii) {
    const areaMin = radius >= knobs.largeRadiiThreshold ? knobs.largeRadiiAreaMin : knobs.holeAreaMin;
    for (const ring of detectTeeRingsPass(bright, radius, areaMin, knobs))
      if (!merged.some(other => Math.hypot(other.cx - ring.cx, other.cy - ring.cy) < knobs.ringMergeProximity)) merged.push(ring);
  }
  return merged;
}

/**
 * The Badge mute footprint. The LAB's clean S1 carries it on the Badge object
 * (`badge.has.mute.px`); the exp badge-assembly path this port runs carries the
 * same footprint as the ownership declaration's bbox (`queryBadgeMutedPixels`,
 * "bounds are inclusive of the border pixels").
 */
export function badgeMuteSet(badges, width, height) {
  const muted = new Set();
  for (const badge of badges) {
    const [x, y, w, h] = badge.unaccountedButOwned.bbox;
    for (let py = Math.max(0, y); py < Math.min(height, y + h); py++)
      for (let px = Math.max(0, x); px < Math.min(width, x + w); px++) muted.add(py * width + px);
  }
  return muted;
}

export function detectRings({ fields, badges }) {
  const { width, height } = fields.bright.mask;
  const enclosed = detectTeeRings(fields.bright.mask);
  const elongated = enclosed.filter(ring => ring.kind === 'tee-rect');
  const muted = badgeMuteSet(badges, width, height);
  const excludedByBadge = [], candidates = [];
  for (const ring of elongated) {
    const x = Math.round(ring.cx), y = Math.round(ring.cy);
    const pixel = x >= 0 && y >= 0 && x < width && y < height ? y * width + x : null;
    if (pixel !== null && muted.has(pixel)) excludedByBadge.push(ring); else candidates.push(ring);
  }
  return { enclosed, elongated, excludedByBadge, candidates };
}

function enclosingFrame(ring, components) {
  return components.filter(component =>
    component.area >= FRAME_AREA_MIN && component.area <= FRAME_AREA_MAX &&
    component.bboxW <= FRAME_MAX_WIDTH && component.bboxH <= FRAME_MAX_HEIGHT &&
    ring.cx >= component.bboxX && ring.cx <= component.bboxX + component.bboxW &&
    ring.cy >= component.bboxY && ring.cy <= component.bboxY + component.bboxH)
    .sort((left, right) => left.bboxW * left.bboxH - right.bboxW * right.bboxH || right.area - left.area || left.label - right.label)[0] ?? null;
}

const logRatio = (left, right) => Math.abs(Math.log(Math.max(left, 1) / Math.max(right, 1)));

/** The family vote: the largest set of frames within the major/minor/area ratios of one seed, ties by tightest spread. */
export function selectTeeFamily(measured) {
  let members = [], anchor = null, bestSpread = Infinity;
  for (const seed of measured) {
    const family = measured.filter(candidate =>
      logRatio(candidate.frame.major, seed.frame.major) <= Math.log(MAJOR_RATIO) &&
      logRatio(candidate.frame.minor, seed.frame.minor) <= Math.log(MINOR_RATIO) &&
      logRatio(candidate.frame.area, seed.frame.area) <= Math.log(AREA_RATIO));
    const spread = family.reduce((sum, candidate) => sum + logRatio(candidate.frame.major, seed.frame.major) + logRatio(candidate.frame.minor, seed.frame.minor) + logRatio(candidate.frame.area, seed.frame.area), 0);
    if (family.length > members.length || (family.length === members.length && spread < bestSpread)) { members = family; anchor = seed; bestSpread = spread; }
  }
  return { members: [...members].sort((left, right) => left.ring.cy - right.ring.cy || left.ring.cx - right.ring.cx), anchor };
}

export function findFamily({ rings, fields }) {
  const measured = [], unframed = [];
  for (const ring of rings.candidates) {
    const frame = enclosingFrame(ring, fields.bright.components);
    if (frame) measured.push({ ring, frame }); else unframed.push(ring);
  }
  return { measured, unframed, ...selectTeeFamily(measured) };
}

/** One Tee per family member; the LAB calls fn.Tee.findPx once per member inside the Tick (proposal.lab.pql.fanout). */
export function findPx({ family, fields }) {
  const { width, height } = fields.bright.mask;
  return family.members.map(member => {
    const pixels = [];
    for (let y = Math.max(0, member.frame.bboxY); y < Math.min(height, member.frame.bboxY + member.frame.bboxH); y++)
      for (let x = Math.max(0, member.frame.bboxX); x < Math.min(width, member.frame.bboxX + member.frame.bboxW); x++)
        if (fields.bright.labels[y * width + x] === member.frame.label) pixels.push(y * width + x);
    const frame = { polarity: 'bright', label: member.frame.label, bbox: [member.frame.bboxX, member.frame.bboxY, member.frame.bboxW, member.frame.bboxH] };
    return {
      center: [member.ring.cx, member.ring.cy],
      innerBbox: [member.ring.bboxX, member.ring.bboxY, member.ring.bboxW, member.ring.bboxH],
      bbox: frame.bbox, angleRad: member.frame.angle, px: pixels,
      has: {
        detectRings: { fn: labAddress('fn.Tee.detectRings'), hole: member.ring },
        findFamily: { fn: labAddress('fn.Tee.findFamily'), frame },
        findPx: { fn: labAddress('fn.Tee.findPx'), parts: [frame] }
      }
    };
  });
}

/* ------------------------------------- the Python analogue's accounting PCR */
/** Every enclosed ring must leave through exactly one named door. */
export function accountRings({ rings, family }) {
  return {
    enclosed: rings.enclosed.length,
    diamondDropped: rings.enclosed.filter(ring => ring.kind !== 'tee-rect').length,
    elongated: rings.elongated.length,
    excludedByBadge: rings.excludedByBadge.length,
    candidates: rings.candidates.length,
    measured: family.measured.length,
    unframed: family.unframed.length,
    votedOutOfFamily: family.measured.length - family.members.length,
    familyMembers: family.members.length
  };
}
export function checkBalance({ ledger, tees }) {
  return {
    ...ledger, tees: tees.length, teePx: tees.reduce((sum, tee) => sum + tee.px.length, 0),
    balanced: ledger.enclosed === ledger.elongated + ledger.diamondDropped &&
      ledger.elongated === ledger.candidates + ledger.excludedByBadge &&
      ledger.candidates === ledger.measured + ledger.unframed &&
      ledger.measured === ledger.familyMembers + ledger.votedOutOfFamily &&
      ledger.familyMembers === tees.length
  };
}

export function registerS3(lab) {
  lab.register(labAddress('fn.Tee.detectRings'), detectRings);
  lab.register(labAddress('fn.Tee.findFamily'), findFamily);
  lab.register(labAddress('fn.Tee.findPx'), findPx);
  lab.register('fn.lab.quickanno.s3.accountrings', accountRings);
  lab.register('fn.lab.quickanno.s3.checkbalance', checkBalance);
}

/** The document the three S3 OperationSpecs declare. */
export function s3Document(lab) {
  return lab.document('S3', [
    { name: 'Tee.detectRings', Calculations: [{ call: labAddress('fn.Tee.detectRings'), with: { fields: labAddress('px.components'), badges: labAddress('px.badges.objects') }, args: {}, into: S3_ADDRESSES.rings }] },
    { name: 'Tee.findFamily', Calculations: [{ call: labAddress('fn.Tee.findFamily'), with: { rings: S3_ADDRESSES.rings, fields: labAddress('px.components') }, args: {}, into: S3_ADDRESSES.family }] },
    { name: 'Tee.findPx', Calculations: [{ call: labAddress('fn.Tee.findPx'), with: { family: S3_ADDRESSES.family, fields: labAddress('px.components') }, args: {}, into: S3_ADDRESSES.objects }] }
  ]);
}

/** The Python investigation, ported: two Ticks, the second consuming the first's published Part. */
export function s3AccountingDocument(lab) {
  return lab.document('S3.quick-anno', [
    { name: 'AccountRings', Calculations: [{ call: 'fn.lab.quickanno.s3.accountrings', with: { rings: S3_ADDRESSES.rings, family: S3_ADDRESSES.family }, args: {}, into: S3_ADDRESSES.ledger }] },
    { name: 'CheckBalance', Calculations: [{ call: 'fn.lab.quickanno.s3.checkbalance', with: { ledger: S3_ADDRESSES.ledger, tees: S3_ADDRESSES.objects }, args: {}, into: S3_ADDRESSES.summary }] }
  ]);
}

export function runS3(lab) {
  const composition = s3Document(lab), { run, receipt } = lab.run('S3', composition);
  const accounting = s3AccountingDocument(lab);
  lab.run('S3.quick-anno', accounting);
  return { run, receipt, composition, accounting, rings: lab.get(S3_ADDRESSES.rings), family: lab.get(S3_ADDRESSES.family), tees: lab.get(S3_ADDRESSES.objects), ledger: lab.get(S3_ADDRESSES.ledger), summary: lab.get(S3_ADDRESSES.summary) };
}
