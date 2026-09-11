/**
 * The LAB's inputs are photographs of a UDisc course map, held in a corpus this
 * repository does not have (`chainspot-corpus`, `dev/DashsTrack/DashsTrack-full.jpg`).
 * So the port carries its own fixture: one deterministic synthetic capture with
 * the two things S0 and S1 actually look for -- chrome bands top and bottom
 * (constant rows, no entropy) and badges built to the LAB's own geometry: a dark
 * plate, a white border enclosing it, white digits inside it, and a dark loop
 * inside a digit.
 *
 * Deterministic: one seeded LCG, no clock, no `Math.random`, so the S0 crop and
 * every S1 component below is the same on every machine.
 *
 * Two elements are drawn only when asked for, because the Stages above S3 are
 * the ones that need them and the S0..S3 tests count what they already see:
 *
 *   `{ hole11: true }`  a third badge reading "11" and a third tee, and NO third
 *                       basket -- a hole whose basket is missing, which is what
 *                       S4 has to report rather than guess.
 *   `{ obstacle: true }` a dark bar across the straight line from tee-1 to
 *                       basket-1 (and across the walk from basket-2 back to
 *                       tee-1): unexplained dark structure that no Stage object
 *                       owns, which is exactly what S5 calls terrain and what
 *                       S6's legs have to go around.
 *
 * `fixtureBasis()` is the record of why each element is drawn the way it is and
 * which knob of which Stage it answers to; map.js publishes it as a Part.
 */
import { readSourceJson } from './source-data.js';

export const CHROME_TOP = 40, CHROME_BOTTOM = 60, WIDTH = 512, HEIGHT = 1024;

function lcg(seed) { let state = seed >>> 0; return () => (state = (state * 1664525 + 1013904223) >>> 0) / 4294967296; }

function put(rgba, width, x, y, value) { const offset = (y * width + x) * 4; rgba[offset] = value; rgba[offset + 1] = value; rgba[offset + 2] = value; rgba[offset + 3] = 255; }
function rect(rgba, width, x, y, w, h, value) { for (let row = y; row < y + h; row++) for (let column = x; column < x + w; column++) put(rgba, width, column, row, value); }
function ring(rgba, width, x, y, w, h, thickness, value) {
  rect(rgba, width, x, y, w, thickness, value); rect(rgba, width, x, y + h - thickness, w, thickness, value);
  rect(rgba, width, x, y, thickness, h, value); rect(rgba, width, x + w - thickness, y, thickness, h, value);
}

const BLACK = 12, WHITE = 245;

/**
 * One basket, in the shape S2 looks for: the LAB's own basket sprite as the
 * white body (bbox 42x66, 1746 white pixels, one 8-connected component), inside
 * a dark shell whose bbox clears it by the same margin on every side. S2 learns
 * that margin as the family's modal shell (learnBasketShellFamilyV1) and keeps
 * only the bodies that agree.
 */
export const BASKET_MARGIN = 4;
function basket(rgba, width, x, y, sprite) {
  rect(rgba, width, x - BASKET_MARGIN, y - BASKET_MARGIN, sprite.width + BASKET_MARGIN * 2, sprite.height + BASKET_MARGIN * 2, BLACK);
  sprite.rows.forEach((row, dy) => [...row].forEach((value, dx) => { if (value === '1') put(rgba, width, x + dx, y + dy, WHITE); }));
  return { body: [x, y, sprite.width, sprite.height], shell: [x - BASKET_MARGIN, y - BASKET_MARGIN, sprite.width + BASKET_MARGIN * 2, sprite.height + BASKET_MARGIN * 2] };
}

/**
 * One badge, in the shape S1's knobs accept: border ring 60x40 (white), plate
 * 48x32 (dark, inside the ring), two white digits inside the plate, and a dark
 * loop inside the second digit. Returns the geometry the tests read back.
 */
function badge(rgba, width, x, y, reading = '10') {
  ring(rgba, width, x, y, 60, 40, 3, WHITE);
  rect(rgba, width, x + 6, y + 4, 48, 32, BLACK);
  // Two glyph slots, left then right; the reading is what S1 must recover.
  const slots = [x + 12, x + 28];
  const digits = [...reading].map((glyph, index) => {
    const at = slots[index];
    if (glyph === '1') { rect(rgba, width, at, y + 10, 6, 20, WHITE); return { glyph, bbox: [at, y + 10, 6, 20], loop: null }; }
    ring(rgba, width, at, y + 10, 12, 20, 3, WHITE);
    rect(rgba, width, at + 3, y + 13, 6, 14, BLACK);
    return { glyph, bbox: [at, y + 10, 12, 20], loop: [at + 3, y + 13, 6, 14] };
  });
  return { reading, border: [x, y, 60, 40], plate: [x + 6, y + 4, 48, 32], digits: digits.map(digit => digit.bbox), loop: digits.find(digit => digit.loop)?.loop ?? null };
}

/**
 * One visible tee, in the shape S3 looks for: a bright rectangular outline whose
 * enclosed hole is small and elongated. The hole is what S3 detects (flood the
 * background in from the border; what is left is enclosed), the outline is the
 * frame the family vote measures.
 */
export const TEE_WALL = 2, TEE_W = 16, TEE_H = 26;
function tee(rgba, width, x, y) {
  ring(rgba, width, x, y, TEE_W, TEE_H, TEE_WALL, WHITE);
  return { frame: [x, y, TEE_W, TEE_H], hole: [x + TEE_WALL, y + TEE_WALL, TEE_W - TEE_WALL * 2, TEE_H - TEE_WALL * 2] };
}

/**
 * The obstacle: a dark bar, drawn in the same value the badge plates and basket
 * shells are drawn in, so it lands in S1's black mask like they do -- and owned
 * by nothing, so it survives `px.remaining.afterBadges` minus the Basket and Tee
 * pixels. Its height is below S1's `minHeight: 24` plate knob and its width
 * above `maxWidth: 78`, so S1 rejects it as a plate; its bbox is neither the
 * basket sprite's (S2) nor small enough to frame a ring (S3). No Stage object
 * claims it: that is the point.
 */
export const OBSTACLE = { x: 0, y: 380, width: 264, height: 16 };

/**
 * The overlaps, drawn only when asked for: three objects a clean detector loses,
 * each to a different kind of occlusion, and each recoverable from evidence the
 * occlusion does not touch (S4).
 *
 *   badge "11"  its white border ring is cut top and bottom, so no single white
 *               component's bbox encloses the plate and S1's assembly reports
 *               "no enclosing white border". The dark plate is untouched, which
 *               is what the LAB's own `recoverDarkPlateBadges` works from.
 *   basket-2    a white tab is drawn against its body, so the body's component
 *               is no longer the sprite's exact 42x66 bbox and S2's family test
 *               fails. The dark shell is untouched, and the shell's modal
 *               margins are what the family already learned.
 *   tee-1       a dark notch 10px wide is cut through the top wall of its
 *               bright frame -- wider than S3's dilation can close (radii 0..3)
 *               -- so the enclosed hole leaks to the background and no ring is
 *               detected. The frame component keeps its 16x26 bbox, which is
 *               what the component fallback S3's receipt marks NOT RUN works from.
 */
export const OVERLAPS = {
  badgeCut: { width: 10, height: 3 },
  basketTab: { width: 10, height: 4, atRow: 36 },
  teeNotch: { width: 10, height: 2 }
};

/** The third hole's badge and tee. There is deliberately no third basket. */
export const HOLE11 = { badge: [380, 180], tee: [470, 120], reading: '11' };

/** The fixture capture: `{ imageId, widthPx, heightPx, rgba, sourceByteLength, badges, baskets, tees, obstacle }`. */
export function fixtureCapture(seed = 20260911, { hole11 = false, obstacle = false, overlaps = false } = {}) {
  const random = lcg(seed), rgba = new Array(WIDTH * HEIGHT * 4).fill(0);
  for (let y = 0; y < HEIGHT; y++) {
    const chrome = y < CHROME_TOP || y >= HEIGHT - CHROME_BOTTOM;
    for (let x = 0; x < WIDTH; x++) put(rgba, WIDTH, x, y, chrome ? 70 : 80 + Math.floor(random() * 120));
  }
  // Two badges reading different hole numbers, so the route's order is the
  // reading and not the position: badge "01" is hole 1, badge "10" is hole 10.
  const badges = [badge(rgba, WIDTH, 120, 300, '10'), badge(rgba, WIDTH, 300, 620, '01')];
  const sprite = readSourceJson('basket-sprite.json');
  const baskets = [basket(rgba, WIDTH, 150, 470, sprite), basket(rgba, WIDTH, 330, 800, sprite)];
  const tees = [tee(rgba, WIDTH, 60, 250), tee(rgba, WIDTH, 420, 560)];
  if (hole11) { badges.push(badge(rgba, WIDTH, ...HOLE11.badge, HOLE11.reading)); tees.push(tee(rgba, WIDTH, ...HOLE11.tee)); }
  if (obstacle) rect(rgba, WIDTH, OBSTACLE.x, OBSTACLE.y, OBSTACLE.width, OBSTACLE.height, BLACK);
  const occluded = [];
  if (overlaps) {
    // The badge that loses its border: cut the ring top and bottom, clear of the plate.
    const target = hole11 ? HOLE11.badge : [120, 300], cut = OVERLAPS.badgeCut;
    rect(rgba, WIDTH, target[0] + 25, target[1], cut.width, cut.height, BLACK);
    rect(rgba, WIDTH, target[0] + 25, target[1] + 40 - cut.height, cut.width, cut.height, BLACK);
    occluded.push({ kind: 'badge', of: hole11 ? HOLE11.reading : '10', bbox: [target[0], target[1], 60, 40], how: 'the white border ring cut top and bottom; the dark plate untouched' });
    // The basket that loses its exact body: a white tab against the sprite's left edge.
    const body = baskets[1].body, tab = OVERLAPS.basketTab;
    rect(rgba, WIDTH, body[0] - tab.width, body[1] + tab.atRow, tab.width, tab.height, WHITE);
    occluded.push({ kind: 'basket', of: 'basket-2', bbox: body, how: "a white tab fused to the body, so its component is no longer the sprite's exact bbox; the dark shell untouched" });
    // The tee that loses its enclosed hole: a notch through the top wall, wider than S3 can close.
    const frame = tees[0].frame, notch = OVERLAPS.teeNotch;
    rect(rgba, WIDTH, frame[0] + 3, frame[1], notch.width, notch.height, BLACK);
    occluded.push({ kind: 'tee', of: 'tee at ' + frame.slice(0, 2).join(','), bbox: frame, how: 'a notch through the top wall wider than the detector can dilate closed, so the hole leaks to the background; the frame component keeps its bbox' });
  }
  return {
    imageId: `lab-fixture-${seed}${hole11 ? '-h11' : ''}${obstacle ? '-obs' : ''}${overlaps ? '-ovl' : ''}`,
    widthPx: WIDTH, heightPx: HEIGHT, rgba, sourceByteLength: rgba.length,
    badges, baskets, tees, obstacle: obstacle ? { ...OBSTACLE } : null, occluded
  };
}

/**
 * The fixture's basis: every element, the Stage knob it answers to, and why it
 * is drawn that way. The port has no corpus image, so the fixture is the only
 * capture any Stage sees; a fixture with no stated basis is a fixture that can
 * be tuned until a Stage passes, which is the failure this Part exists to make
 * visible (proposal.lab.oracle.nocorpus).
 */
export function fixtureBasis({ hole11 = false, obstacle = false, overlaps = false } = {}) {
  return {
    for: 'why every element of the synthetic capture is drawn the way it is, and which Stage knob it answers to',
    frame: { widthPx: WIDTH, heightPx: HEIGHT, chromeTop: CHROME_TOP, chromeBottom: CHROME_BOTTOM, background: 'seeded LCG, values 80..199: never <= 45 (S1 black) and never >= 210 (S1 white), so every mask pixel below is drawn on purpose' },
    elements: [
      { what: 'chrome bands', basis: 'constant rows top and bottom, no entropy: what S0 crops' },
      { what: 'badge border / plate / digits / loop', basis: "S1's plate knobs (width 34..78, height 24..54, aspect 1..2.4, fill >= 0.55) and the digit templates the port carries in place of the LAB logistic asset" },
      { what: 'basket', basis: "the LAB's own basket sprite (42x66, 1746 white px) inside a dark shell clearing it by 4px on every side: S2 learns that modal margin" },
      { what: 'tee', basis: 'a bright 16x26 outline 2px thick whose enclosed hole is small and elongated: S3 floods the background in and keeps what is enclosed' },
      ...(hole11 ? [{ what: 'the third badge "11" and third tee, with no third basket', basis: 'S4 has to report a hole whose basket is missing instead of binding a basket that belongs to another hole; both digits are bars, so this badge adds no enclosed loop for S3 to mute' }] : []),
      ...(overlaps ? [{ what: 'the three overlaps', basis: 'one object per clean detector is occluded in the one way that detector cannot survive -- a cut border (S1 needs a white component enclosing the plate), a fused body (S2 needs the sprite bbox exactly), a notched frame (S3 needs an enclosed hole) -- and in each case the evidence the OTHER half of the object carries is left untouched, which is what S4 recovers from' }] : []),
      ...(obstacle ? [{ what: 'the obstacle bar', basis: `${OBSTACLE.width}x${OBSTACLE.height} at (${OBSTACLE.x},${OBSTACLE.y}) in source coordinates: dark like a plate but outside every S1/S2/S3 predicate, so it is the one thing in the raster no Stage object owns and S5 can only call terrain` }] : [])
    ],
    seededBy: 'lcg(seed), no clock and no Math.random: the same bytes on every machine'
  };
}

/** The same capture already cropped, for an S1 run that does not need S0 first. */
export function shift(box, dx, dy) { return [box[0] - dx, box[1] - dy, box[2], box[3]]; }
