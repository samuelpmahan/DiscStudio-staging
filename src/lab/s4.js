/**
 * S4, invented: Recovery. The objects the clean detectors lose to an overlap,
 * found again from the evidence the overlap did not touch.
 *
 *   consumes  px.badges.objects  px.baskets  px.tees   the clean produce
 *             px.components                            the masks and their components
 *             px.baskets.shellFamily  px.tees.family   what S2 and S3 already learned
 *             px.s1.whiteDigits.model                  so a recovered badge is READ, not just found
 *   produces  px.recovered.badges / .baskets / .tees   clean objects and recovered ones,
 *                                                      every one carrying its basis
 *             px.recovered.ledger                      what was recovered, from what overlap
 *
 * Recovery is the LAB's own word and the LAB's own shape. S1 already has one:
 * `recoverDarkPlateBadges` (detectors/threeFactor/badgeStage.ts) finds a badge
 * whose bright border never formed, from the dark plate alone, and marks it
 * `basis: 'dark-plate-recovery'` beside `'bright-family'` and `'unresolved'`.
 * S2's and S3's receipts name the two that were never written: `recovery: NOT
 * RUN` (S2/contract.ts:19) and `recovery: NOT RUN` / `component fallback: NOT
 * RUN` (S3/contract.ts:25-26). This Stage writes those two in the same shape.
 *
 *   badge   dark-plate-recovery  the LAB's rule, ported knob for knob: a dark
 *                                component of plate geometry whose interior
 *                                carries between 4% and 40% bright glyph, far
 *                                enough from every clean badge; then read with
 *                                S1's own prepare/match, so it arrives numbered.
 *   basket  shell-recovery       a dark component whose bbox is exactly the
 *                                shell geometry S2's clean family already
 *                                learned (sprite plus its modal margins), with
 *                                bright material inside it, and no clean Basket
 *                                in it. The shell survives what the body does not.
 *   tee     component-fallback    a bright component whose bbox is exactly the
 *                                modal frame of the clean family and whose fill
 *                                matches it, with no accepted ring: a frame that
 *                                is still a frame even though its hole leaked.
 *
 * The rule that makes recovery safe rather than generous is the same in all
 * three: recovery may only ADD, and only where the clean path found nothing. A
 * recovered object never replaces a clean one, never moves one, and always says
 * which rule found it and what evidence it stood on.
 */
import { labAddress, labDocument } from './address.js';
import { compiledStage } from './stage-sources.js';
import { compileMermaidPcr, lowerToPql } from './mermaid.js';
import { prepareDigits, matchDigits } from './s1.js';

export const S4_ADDRESSES = {
  unclaimed: labAddress('px.recovered.unclaimed'),
  badges: labAddress('px.recovered.badges'),
  baskets: labAddress('px.recovered.baskets'),
  tees: labAddress('px.recovered.tees'),
  ledger: labAddress('px.recovered.ledger'),
  check: 'px.exp.lab.s4.recoverycheck'
};

/** `DEFAULT_BADGE_STAGE_KNOBS`, the subset the dark-plate recovery path reads. */
export const PLATE_KNOBS = {
  plateMinWidth: 34, plateMaxWidth: 78, plateMinHeight: 24, plateMaxHeight: 54,
  plateAspectMin: 1, plateAspectMax: 2.4, plateFillMin: 0.55, plateInteriorMargin: 4,
  plateGlyphFractionMin: 0.04, plateGlyphFractionMax: 0.4, plateProximityThreshold: 22, plateBboxMargin: 4
};
/** S1's `WhiteDigitRecognition` knobs, so a recovered badge is read exactly as a clean one is. */
export const DIGIT_KNOBS = { minComponentArea: 6, heightRatioMin: 0.5, wideRatio: 0.95, valleySearchLo: 0.3, valleySearchHi: 0.7, digitW: 24, digitH: 32, confidenceFloorDivisor: 8, labelAmbiguityMargin: 0.045 };

const bboxOf = stats => [stats.bboxX, stats.bboxY, stats.bboxW, stats.bboxH];
const contains = (outer, inner) => outer[0] <= inner[0] && outer[1] <= inner[1] && outer[0] + outer[2] >= inner[0] + inner[2] && outer[1] + outer[3] >= inner[1] + inner[3];
const overlapsBbox = (left, right) => left[0] < right[0] + right[2] && right[0] < left[0] + left[2] && left[1] < right[1] + right[3] && right[1] < left[1] + left[3];
const centerOfBbox = ([x, y, width, height]) => [x + width / 2, y + height / 2];

function componentPixels(component, labels, width, height) {
  const pixels = [];
  for (let y = Math.max(0, component.bboxY); y < Math.min(height, component.bboxY + component.bboxH); y++)
    for (let x = Math.max(0, component.bboxX); x < Math.min(width, component.bboxX + component.bboxW); x++)
      if (labels[y * width + x] === component.label) pixels.push(y * width + x);
  return pixels;
}

/**
 * Tick 1. What the clean path left on the table: every component of either mask
 * that no clean Badge, Basket or Tee owns a pixel of. Recovery searches here and
 * nowhere else, which is why it cannot take an object away from a Stage.
 */
export function unclaimed({ fields, badges, baskets, tees }) {
  const width = fields.bright.mask.width, height = fields.bright.mask.height;
  const owned = new Uint8Array(width * height);
  for (const badge of badges) for (const pixel of badge.pixels) owned[pixel] = 1;
  for (const basket of baskets) for (const pixel of basket.px) owned[pixel] = 1;
  for (const tee of tees) for (const pixel of tee.px) owned[pixel] = 1;
  const take = (polarity) => fields[polarity].components.map(component => {
    const pixels = componentPixels(component, fields[polarity].labels, width, height);
    const free = pixels.filter(pixel => !owned[pixel]);
    return { polarity, label: component.label, bbox: bboxOf(component), area: component.area, stats: component, pixels: free.length, claimed: pixels.length - free.length };
  }).filter(entry => entry.pixels > 0);
  return { frame: { width, height }, bright: take('bright'), dark: take('dark'), claimedPx: owned.reduce((sum, value) => sum + value, 0) };
}

/** How much bright material sits inside a dark component's interior: the LAB's glyph fraction. */
export function glyphFraction(component, bright, width, height, margin) {
  let interior = 0, glyph = 0;
  for (let y = component.bboxY + margin; y < component.bboxY + component.bboxH - margin; y++) {
    if (y < 0 || y >= height) continue;
    for (let x = component.bboxX + margin; x < component.bboxX + component.bboxW - margin; x++) {
      if (x < 0 || x >= width) continue;
      interior++;
      if (bright.data[y * width + x]) glyph++;
    }
  }
  return { interior, glyph, fraction: interior ? glyph / interior : 0 };
}

/** Tick 2. Badges: the LAB's dark-plate recovery, and then S1's own reading of what it found. */
export function recoverBadges({ badges, unclaimed, fields, model, knobs = PLATE_KNOBS, digitKnobs = DIGIT_KNOBS }) {
  const width = fields.bright.mask.width, height = fields.bright.mask.height;
  const clean = badges.map((badge, index) => ({ id: `badge-${index + 1}`, basis: 'bright-family', bbox: badge.unaccountedButOwned.bbox, at: centerOfBbox(badge.unaccountedButOwned.bbox), reading: badge.reading, source: badge, evidence: null }));
  const recovered = [], rejected = [];
  for (const entry of unclaimed.dark) {
    const component = entry.stats, [, , w, h] = entry.bbox, aspect = w / h, why = [];
    if (w < knobs.plateMinWidth || w > knobs.plateMaxWidth) why.push('plate width');
    if (h < knobs.plateMinHeight || h > knobs.plateMaxHeight) why.push('plate height');
    if (aspect < knobs.plateAspectMin || aspect > knobs.plateAspectMax) why.push('plate aspect');
    if (component.area / (w * h) < knobs.plateFillMin) why.push('plate fill');
    const glyph = glyphFraction(component, fields.bright.mask, width, height, knobs.plateInteriorMargin);
    if (glyph.fraction < knobs.plateGlyphFractionMin || glyph.fraction > knobs.plateGlyphFractionMax) why.push('glyph fraction');
    if (clean.some(badge => Math.hypot(badge.at[0] - component.cx, badge.at[1] - component.cy) < knobs.plateProximityThreshold)) why.push('a clean badge is already here');
    if (why.length) { rejected.push({ bbox: entry.bbox, why }); continue; }
    const margin = knobs.plateBboxMargin, bbox = [entry.bbox[0] - margin, entry.bbox[1] - margin, w + margin * 2, h + margin * 2];
    // Read it the way S1 reads a clean one: the white components inside the plate are its digits.
    const digits = fields.bright.components.filter(candidate => contains(entry.bbox, bboxOf(candidate)))
      .map(candidate => ({ part: { pixels: componentPixels(candidate, fields.bright.labels, width, height), widthPx: width, heightPx: height }, bbox: bboxOf(candidate), area: candidate.area }));
    const candidate = { id: `badge-recovered:${component.label}`, border: { bbox }, plate: { part: { widthPx: width, heightPx: height } }, digits, pixels: componentPixels(component, fields.dark.labels, width, height) };
    const read = matchDigits({ prepared: prepareDigits({ badges: { candidates: [candidate], incomplete: [] }, knobs: digitKnobs }), model }).candidates[0];
    recovered.push({
      id: `badge-${clean.length + recovered.length + 1}`, basis: 'dark-plate-recovery', bbox, at: centerOfBbox(bbox), reading: read.reading, source: read,
      evidence: { rule: "the LAB's recoverDarkPlateBadges", plate: entry.bbox, glyphFraction: Math.round(glyph.fraction * 1000) / 1000, interiorPx: glyph.interior, knobs: { min: knobs.plateGlyphFractionMin, max: knobs.plateGlyphFractionMax }, digits: digits.length }
    });
  }
  return { kind: 'badge', clean, recovered, objects: [...clean, ...recovered], rejected };
}

/** Tick 3. Baskets: the shell S2's clean family already measured, standing where a body no longer does. */
export function recoverBaskets({ baskets, unclaimed, shellFamily, fields }) {
  const width = fields.bright.mask.width, height = fields.bright.mask.height;
  const clean = baskets.map((basket, index) => ({ id: `basket-${index + 1}`, basis: 'body-family', bbox: basket.bbox, at: centerOfBbox(basket.bbox), px: basket.px.length, evidence: null }));
  const recovered = [], rejected = [];
  const margins = shellFamily.margins;
  const shellSize = margins && shellFamily.members.length
    ? [shellFamily.members[0].bbox[2], shellFamily.members[0].bbox[3]]
    : null;
  for (const entry of unclaimed.dark) {
    const why = [];
    if (!shellSize) why.push('S2 learned no shell family to compare against');
    else if (entry.bbox[2] !== shellSize[0] || entry.bbox[3] !== shellSize[1]) why.push(`shell geometry ${entry.bbox[2]}x${entry.bbox[3]} is not the family's ${shellSize.join('x')}`);
    if (clean.some(basket => overlapsBbox(basket.bbox, entry.bbox))) why.push('a clean basket is already here');
    const inside = shellSize ? glyphFraction(entry.stats, fields.bright.mask, width, height, Math.max(...margins)) : { fraction: 0, glyph: 0, interior: 0 };
    if (!why.length && inside.glyph === 0) why.push('no bright material inside the shell');
    if (why.length) { rejected.push({ bbox: entry.bbox, why }); continue; }
    recovered.push({
      id: `basket-${clean.length + recovered.length + 1}`, basis: 'shell-recovery', bbox: entry.bbox, at: centerOfBbox(entry.bbox), px: entry.stats.area,
      evidence: { rule: "the recovery S2's receipt marks NOT RUN", shell: entry.bbox, margins, brightInsidePx: inside.glyph, interiorPx: inside.interior }
    });
  }
  return { kind: 'basket', clean, recovered, objects: [...clean, ...recovered], rejected };
}

/** Tick 4. Tees: the component fallback S3's receipt marks NOT RUN -- a frame whose hole leaked. */
export function recoverTees({ tees, unclaimed, fields }) {
  const clean = tees.map((tee, index) => ({ id: `tee-${index + 1}`, basis: 'ring-family', bbox: tee.bbox, at: tee.center, px: tee.px.length, angleRad: tee.angleRad, evidence: null }));
  const frame = clean.length ? [clean[0].bbox[2], clean[0].bbox[3]] : null;
  const fill = clean.length ? tees[0].px.length / (clean[0].bbox[2] * clean[0].bbox[3]) : null;
  const recovered = [], rejected = [];
  for (const entry of unclaimed.bright) {
    const why = [];
    if (!frame) why.push('S3 accepted no tee to take the family frame from');
    else if (entry.bbox[2] !== frame[0] || entry.bbox[3] !== frame[1]) why.push(`frame ${entry.bbox[2]}x${entry.bbox[3]} is not the family's ${frame.join('x')}`);
    const thisFill = entry.stats.area / (entry.bbox[2] * entry.bbox[3]);
    if (!why.length && Math.abs(thisFill - fill) > 0.15) why.push(`fill ${thisFill.toFixed(2)} is not the family's ${fill.toFixed(2)}`);
    if (clean.some(tee => overlapsBbox(tee.bbox, entry.bbox))) why.push('a clean tee is already here');
    if (why.length) { rejected.push({ bbox: entry.bbox, why }); continue; }
    recovered.push({
      // px.components already carries the LAB's measured stats, angle included.
      id: `tee-${clean.length + recovered.length + 1}`, basis: 'component-fallback', bbox: entry.bbox, at: [entry.stats.cx, entry.stats.cy], px: entry.stats.area, angleRad: entry.stats.angle,
      evidence: { rule: "the component fallback S3's receipt marks NOT RUN", frame: entry.bbox, familyFrame: frame, fill: Math.round(thisFill * 1000) / 1000, familyFill: Math.round(fill * 1000) / 1000, ring: null, why: 'no enclosed hole survived, so no ring was accepted' }
    });
  }
  return { kind: 'tee', clean, recovered, objects: [...clean, ...recovered], rejected };
}

/** Tick 5. The ledger: what was recovered, by which rule, and what it overlapped. */
export function recoveryLedger({ badges, baskets, tees, unclaimed }) {
  const kinds = [badges, baskets, tees];
  const overlapWith = object => [...unclaimed.bright, ...unclaimed.dark]
    .filter(entry => overlapsBbox(entry.bbox, object.bbox) && entry.bbox.join() !== object.bbox.join())
    .map(entry => ({ polarity: entry.polarity, bbox: entry.bbox, freePx: entry.pixels }));
  return {
    for: 'what the clean detectors lost to an overlap and what found it again, so that a later Stage reads one list per kind and can still tell how each object got there',
    from: ['px.badges.objects', 'px.baskets', 'px.tees', 'px.components'].map(labAddress),
    counts: Object.fromEntries(kinds.map(kind => [kind.kind, { clean: kind.clean.length, recovered: kind.recovered.length, total: kind.objects.length, rejected: kind.rejected.length }])),
    recovered: kinds.flatMap(kind => kind.recovered.map(object => ({
      kind: kind.kind, id: object.id, basis: object.basis, bbox: object.bbox,
      evidence: object.evidence, overlappedBy: overlapWith(object)
    }))),
    bases: Object.fromEntries(kinds.map(kind => [kind.kind, [...new Set(kind.objects.map(object => object.basis))]]))
  };
}

/** The invariants: recovery adds, it never edits, and nothing arrives without a basis. */
export function checkRecovery({ ledger, badges, baskets, tees, cleanBadges, cleanBaskets, cleanTees }) {
  const kinds = { badge: badges, basket: baskets, tee: tees };
  const raw = { badge: cleanBadges.map(badge => badge.unaccountedButOwned.bbox), basket: cleanBaskets.map(basket => basket.bbox), tee: cleanTees.map(tee => tee.bbox) };
  const checks = {
    // Against the raw S1/S2/S3 Parts, not against S4's own copy of them.
    everyCleanObjectSurvivesUnchanged: Object.entries(kinds).every(([kind, group]) =>
      group.clean.length === raw[kind].length && group.objects.slice(0, group.clean.length).every((object, index) => object.bbox.join() === raw[kind][index].join())),
    recoveryOnlyAdds: Object.values(kinds).every(group => group.objects.length === group.clean.length + group.recovered.length),
    everyObjectNamesItsBasis: Object.values(kinds).every(group => group.objects.every(object => typeof object.basis === 'string' && object.basis.length)),
    everyRecoveredObjectCarriesEvidence: Object.values(kinds).every(group => group.recovered.every(object => object.evidence && object.evidence.rule)),
    noRecoveredObjectSitsOnACleanOne: Object.values(kinds).every(group => group.recovered.every(object => !group.clean.some(other => overlapsBbox(other.bbox, object.bbox)))),
    everyRejectionSaysWhy: Object.values(kinds).every(group => group.rejected.every(entry => entry.why.length > 0)),
    idsAreUnique: Object.values(kinds).every(group => new Set(group.objects.map(object => object.id)).size === group.objects.length)
  };
  return { counts: ledger.counts, checks, balanced: Object.values(checks).every(Boolean) };
}

export function registerS4(lab) {
  lab.register(labAddress('fn.Recover.unclaimed'), unclaimed);
  lab.register(labAddress('fn.Recover.badges'), recoverBadges);
  lab.register(labAddress('fn.Recover.baskets'), recoverBaskets);
  lab.register(labAddress('fn.Recover.tees'), recoverTees);
  lab.register(labAddress('fn.Recover.ledger'), recoveryLedger);
  lab.register('fn.lab.s4.checkrecovery', checkRecovery);
}

export const S4_CONTRACT = {
  stage: 'S4', name: 'Recovery',
  for: 'the objects a clean detector loses to an overlap, found again from the evidence the overlap did not touch, and published per kind so the later Stages read one list',
  consumes: ['px.badges.objects', 'px.baskets', 'px.tees', 'px.components', 'px.baskets.shellFamily', 'px.s1.whiteDigits.model'].map(labAddress),
  produces: [S4_ADDRESSES.badges, S4_ADDRESSES.baskets, S4_ADDRESSES.tees, S4_ADDRESSES.ledger],
  ticks: ['Recover.unclaimed', 'Recover.badges', 'Recover.baskets', 'Recover.tees', 'Recover.ledger'],
  invariants: ['everyCleanObjectSurvivesUnchanged', 'recoveryOnlyAdds', 'everyObjectNamesItsBasis', 'everyRecoveredObjectCarriesEvidence', 'noRecoveredObjectSitsOnACleanOne', 'everyRejectionSaysWhy', 'idsAreUnique']
};

export function s4Ticks() {
  const px = address => labAddress(address);
  return [
    { name: 'Recover.unclaimed', Calculations: [{ call: labAddress('fn.Recover.unclaimed'), with: { fields: px('px.components'), badges: px('px.badges.objects'), baskets: px('px.baskets'), tees: px('px.tees') }, args: {}, into: S4_ADDRESSES.unclaimed }] },
    { name: 'Recover.badges', Calculations: [{ call: labAddress('fn.Recover.badges'), with: { badges: px('px.badges.objects'), unclaimed: S4_ADDRESSES.unclaimed, fields: px('px.components'), model: px('px.s1.whiteDigits.model') }, args: { knobs: PLATE_KNOBS, digitKnobs: DIGIT_KNOBS }, into: S4_ADDRESSES.badges }] },
    { name: 'Recover.baskets', Calculations: [{ call: labAddress('fn.Recover.baskets'), with: { baskets: px('px.baskets'), unclaimed: S4_ADDRESSES.unclaimed, shellFamily: px('px.baskets.shellFamily'), fields: px('px.components') }, args: {}, into: S4_ADDRESSES.baskets }] },
    { name: 'Recover.tees', Calculations: [{ call: labAddress('fn.Recover.tees'), with: { tees: px('px.tees'), unclaimed: S4_ADDRESSES.unclaimed, fields: px('px.components') }, args: {}, into: S4_ADDRESSES.tees }] },
    { name: 'Recover.ledger', Calculations: [{ call: labAddress('fn.Recover.ledger'), with: { badges: S4_ADDRESSES.badges, baskets: S4_ADDRESSES.baskets, tees: S4_ADDRESSES.tees, unclaimed: S4_ADDRESSES.unclaimed }, args: {}, into: S4_ADDRESSES.ledger }] }
  ];
}

export function s4Document(lab) { return lab.document('S4', s4Ticks()); }
export function compiledS4() { return compiledStage('S4', compileMermaidPcr, lowerToPql, labDocument); }

export function s4InvariantDocument(lab) {
  return lab.document('S4.invariants', [
    { name: 'CheckRecovery', Calculations: [{ call: 'fn.lab.s4.checkrecovery', with: { ledger: S4_ADDRESSES.ledger, badges: S4_ADDRESSES.badges, baskets: S4_ADDRESSES.baskets, tees: S4_ADDRESSES.tees, cleanBadges: labAddress('px.badges.objects'), cleanBaskets: labAddress('px.baskets'), cleanTees: labAddress('px.tees') }, args: {}, into: S4_ADDRESSES.check }] }
  ]);
}

/** The Stage as the studio runs it; the demo decides how a recovered object is drawn. */
export function s4Spec() {
  return {
    key: 's4', stage: 'S4', title: 'Recovery', composition: 'lab-s4',
    about: "the objects an overlap hid from the clean detectors, found again from the half of each object the overlap did not touch, each carrying the rule that found it.",
    needs: S4_CONTRACT.consumes, produces: S4_CONTRACT.produces,
    register: registerS4, ticks: lab => s4Document(lab).Ticks
  };
}

export function runS4(lab) {
  const composition = s4Document(lab), { run, receipt } = lab.run('S4', composition);
  const invariants = s4InvariantDocument(lab);
  lab.run('S4.invariants', invariants);
  return {
    run, receipt, composition, invariants, unclaimed: lab.get(S4_ADDRESSES.unclaimed),
    badges: lab.get(S4_ADDRESSES.badges), baskets: lab.get(S4_ADDRESSES.baskets), tees: lab.get(S4_ADDRESSES.tees),
    ledger: lab.get(S4_ADDRESSES.ledger), check: lab.get(S4_ADDRESSES.check)
  };
}
