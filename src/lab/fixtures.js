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
 */
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { SOURCE } from './source.js';

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

/** The fixture capture: `{ imageId, widthPx, heightPx, rgba, sourceByteLength, badges, baskets, tees }`. */
export function fixtureCapture(seed = 20260911) {
  const random = lcg(seed), rgba = new Array(WIDTH * HEIGHT * 4).fill(0);
  for (let y = 0; y < HEIGHT; y++) {
    const chrome = y < CHROME_TOP || y >= HEIGHT - CHROME_BOTTOM;
    for (let x = 0; x < WIDTH; x++) put(rgba, WIDTH, x, y, chrome ? 70 : 80 + Math.floor(random() * 120));
  }
  // Two badges reading different hole numbers, so the route's order is the
  // reading and not the position: badge "01" is hole 1, badge "10" is hole 10.
  const badges = [badge(rgba, WIDTH, 120, 300, '10'), badge(rgba, WIDTH, 300, 620, '01')];
  const sprite = JSON.parse(readFileSync(join(SOURCE, 'basket-sprite.json'), 'utf8'));
  const baskets = [basket(rgba, WIDTH, 150, 470, sprite), basket(rgba, WIDTH, 330, 800, sprite)];
  const tees = [tee(rgba, WIDTH, 60, 250), tee(rgba, WIDTH, 420, 560)];
  return { imageId: `lab-fixture-${seed}`, widthPx: WIDTH, heightPx: HEIGHT, rgba, sourceByteLength: rgba.length, badges, baskets, tees };
}

/** The same capture already cropped, for an S1 run that does not need S0 first. */
export function shift(box, dx, dy) { return [box[0] - dx, box[1] - dy, box[2], box[3]]; }
