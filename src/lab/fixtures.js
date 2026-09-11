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
 * One badge, in the shape S1's knobs accept: border ring 60x40 (white), plate
 * 48x32 (dark, inside the ring), two white digits inside the plate, and a dark
 * loop inside the second digit. Returns the geometry the tests read back.
 */
function badge(rgba, width, x, y) {
  ring(rgba, width, x, y, 60, 40, 3, WHITE);
  rect(rgba, width, x + 6, y + 4, 48, 32, BLACK);
  rect(rgba, width, x + 12, y + 10, 6, 20, WHITE);                 // a bar digit
  ring(rgba, width, x + 28, y + 10, 12, 20, 3, WHITE);             // a ring digit
  rect(rgba, width, x + 31, y + 13, 6, 14, BLACK);                 // its loop
  return { border: [x, y, 60, 40], plate: [x + 6, y + 4, 48, 32], digits: [[x + 12, y + 10, 6, 20], [x + 28, y + 10, 12, 20]], loop: [x + 31, y + 13, 6, 14] };
}

/** The fixture capture: `{ imageId, widthPx, heightPx, rgba, sourceByteLength, badges }`. */
export function fixtureCapture(seed = 20260911) {
  const random = lcg(seed), rgba = new Array(WIDTH * HEIGHT * 4).fill(0);
  for (let y = 0; y < HEIGHT; y++) {
    const chrome = y < CHROME_TOP || y >= HEIGHT - CHROME_BOTTOM;
    for (let x = 0; x < WIDTH; x++) put(rgba, WIDTH, x, y, chrome ? 70 : 80 + Math.floor(random() * 120));
  }
  const badges = [badge(rgba, WIDTH, 120, 300), badge(rgba, WIDTH, 300, 620)];
  return { imageId: `lab-fixture-${seed}`, widthPx: WIDTH, heightPx: HEIGHT, rgba, sourceByteLength: rgba.length, badges };
}

/** The same capture already cropped, for an S1 run that does not need S0 first. */
export function shift(box, dx, dy) { return [box[0] - dx, box[1] - dy, box[2], box[3]]; }
