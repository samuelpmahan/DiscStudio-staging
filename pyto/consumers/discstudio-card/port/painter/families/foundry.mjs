// families/foundry.mjs -- the foundry studio's disc-art families.
//
// Each export has paint_components.render's shape minus the family name:
//     render(seed, base, accent, target, label) -> string, the whole SVG document
// painter.mjs already dispatches every slug below to the function beside it, so
// filling these in is the whole job; do not edit painter.mjs or core.mjs.
//
// Where the reference bytes come from, per art_registry.py:
//   halftone-screen   _families_foundry.py
//   register-mark     _families_foundry.py
//   hot-foil          _families_foundry.py
//
// Dependency-free: this file may import ../core.mjs and nothing else -- no npm,
// no DOM, Node 22 and browsers alike. core.mjs carries the Python runtime these
// families need, and using it is what keeps the bytes identical.
//
// The foundry module keeps its own copies of the frame helpers (_open, _plate,
// _rim, _label_plate, _close, _sw, _poly): they are NOT paint_components' --
// this studio's gradient stops are spelled #ffffff/#000000 at .16/.30, its rim
// ring sits at r=203 with opacity .92/.30, and its label is a knockout plate,
// not a bare <text>. Porting paint_components' versions here would change bytes.

import {
  PyRandom, escape, fmt1, fmt2, pyMod, strokeFloor,
  sin, cos, radians, C, R, SIZE, TARGETS, TAU,
} from '../core.mjs';

// --------------------------------------------------------------------------- //
// shared shop floor helpers
// --------------------------------------------------------------------------- //

/**
 * _sw: f"{max(source, _floor_width(target, min_output)):.1f}" -- always one
 * decimal, an int source included ("7.0"), which is why core's strokeText (it
 * prints through pyNum, for paint_components' f-string) cannot stand in here.
 * _floor_width is core's strokeFloor: round(min_output / (target / SIZE), 1).
 */
function sw(source, target, minOutput = 1.0) {
  const floor = strokeFloor(target, minOutput);
  return fmt1(floor > source ? floor : source);
}

function check(target) {
  if (!TARGETS.includes(target)) throw new Error(`target must be one of ${TARGETS}`);
}

function poly(cx, cy, radius, sides, rotation) {
  const pts = [];
  for (let i = 0; i < sides; i++) {
    const a = radians(rotation) + i * TAU / sides;
    pts.push(`${fmt1(cx + radius * cos(a))},${fmt1(cy + radius * sin(a))}`);
  }
  return pts.join(' ');
}

function open(target, label, extraDefs = []) {
  const safe = escape(label);
  const out = [
    '<?xml version="1.0" encoding="UTF-8"?>',
    `<svg xmlns="http://www.w3.org/2000/svg" width="${target}" height="${target}"`
    + ` viewBox="0 0 ${SIZE} ${SIZE}" role="img" aria-label="${safe}">`,
    '<defs><clipPath id="disc"><circle cx="256" cy="256" r="220"/></clipPath>',
    '<linearGradient id="depth" x1="0" y1="0" x2="0" y2="1">'
    + '<stop offset="0" stop-color="#ffffff" stop-opacity=".16"/>'
    + '<stop offset="1" stop-color="#000000" stop-opacity=".30"/></linearGradient>',
  ];
  out.push(...extraDefs);
  out.push('</defs>');
  return [out, safe];
}

function plate(base) {
  return [
    '<g id="base" clip-path="url(#disc)">',
    `<circle cx="256" cy="256" r="220" fill="${base}"/>`,
    '<circle cx="256" cy="256" r="220" fill="url(#depth)"/>',
    '</g>',
  ];
}

function rim(accent, target) {
  return [
    '<g id="rim" fill="none">',
    `<circle cx="256" cy="256" r="216" stroke="${accent}"`
    + ` stroke-width="${sw(7, target)}" opacity=".92"/>`,
    '<circle cx="256" cy="256" r="203" stroke="#ffffff"'
    + ` stroke-width="${sw(3, target)}" opacity=".30"/>`,
    '</g>',
  ];
}

// Python's str.strip() strips every code point str.isspace() accepts, which is
// not JS's \s set: it adds \x1c-\x1f and \x85, and it excludes U+FEFF.
const PY_SPACE = /[\u0009\u000a\u000b\u000c\u000d\u001c\u001d\u001e\u001f\u0020\u0085\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000]/;

function pyStrip(text) {
  let start = 0;
  let end = text.length;
  while (start < end && PY_SPACE.test(text[start])) start++;
  while (end > start && PY_SPACE.test(text[end - 1])) end--;
  return text.slice(start, end);
}

/** A knockout plate with the label hot-stamped into it. 220 only. */
function labelPlate(label, base, accent, target) {
  if (target !== 220) return [];
  // Python slices by code point, JS by UTF-16 unit; and the plate is measured
  // AFTER .upper(), which can lengthen the string ('straße' -> 'STRASSE').
  const text = Array.from(pyStrip(label)).slice(0, 10).join('').toUpperCase();
  if (!text) return [];
  const width = 16.0 * Array.from(text).length + 40.0;
  const x = 256.0 - width / 2.0;
  return [
    '<g id="text">',
    `<rect x="${fmt1(x)}" y="396" width="${fmt1(width)}" height="36" rx="4"`
    + ` fill="${base}" stroke="${accent}" stroke-width="3" opacity=".96"/>`,
    '<text x="257.5" y="421" text-anchor="middle" font-family="sans-serif"'
    + ' font-size="20" font-weight="700" letter-spacing="3"'
    + ` fill="${accent}">${escape(text)}</text>`,
    '</g>',
  ];
}

function close(safe) {
  return [`<title>${safe}</title>`, '</svg>'];
}

// --------------------------------------------------------------------------- //
// family 1 - halftone screen
// --------------------------------------------------------------------------- //

/** One ink, screened. A tint wedge that ramps into solid coverage. */
export function halftone_screen(seed, base, accent, target, label) {
  check(target);
  const rng = new PyRandom(seed);
  const screen = rng.choice([15.0, 45.0, 75.0, 105.0]);
  const ramp = rng.uniform(0.0, TAU);
  const openness = rng.uniform(0.16, 0.34);
  const tickPhase = rng.uniform(-10.0, 10.0);

  const [out, safe] = open(target, label);
  out.push(...plate(base));

  const cells = target === 42 ? 5 : (target === 96 ? 9 : 15);
  const cell = 2.0 * R / cells;
  const ca = cos(radians(screen));
  const sa = sin(radians(screen));
  const rx = cos(ramp);
  const ry = sin(ramp);
  const reach = Math.floor(cells / 2) + 2;

  out.push('<g id="art" clip-path="url(#disc)">');
  out.push(`<g id="screen" fill="${accent}">`);
  for (let row = -reach; row <= reach; row++) {
    for (let col = -reach; col <= reach; col++) {
      const u = (col + 0.5 * pyMod(row, 2)) * cell;
      const v = row * cell;
      const x = C + u * ca - v * sa;
      const y = C + u * sa + v * ca;
      const dx = x - C;
      const dy = y - C;
      let t = 0.5 + (dx * rx + dy * ry) / (2.0 * R);
      t = t < 0.0 ? 0.0 : (t > 1.0 ? 1.0 : t);
      const radius = cell * 0.5 * (openness + (1.62 - openness) * Math.pow(t, 1.35));
      if (radius < 1.2 || dx * dx + dy * dy > Math.pow(R + radius, 2)) continue;
      out.push(`<circle cx="${fmt1(x)}" cy="${fmt1(y)}" r="${fmt1(radius)}"/>`);
    }
  }
  out.push('</g>');
  out.push('</g>');

  out.push(...rim(accent, target));

  // Register ticks, cut clean through the rim the way a press sheet marks
  // where the screen was hung. Drawn over the rim, clipped to the plastic.
  out.push('<g id="stamp" clip-path="url(#disc)">');
  if (target !== 42) {
    out.push(`<g stroke="${base}" stroke-width="${sw(16, target, 1.7)}"`
      + ' stroke-linecap="butt">');
    for (let i = 0; i < 4; i++) {
      const a = radians(tickPhase + i * 90.0);
      out.push(`<line x1="${fmt1(C + 150 * cos(a))}" y1="${fmt1(C + 150 * sin(a))}"`
        + ` x2="${fmt1(C + 222 * cos(a))}" y2="${fmt1(C + 222 * sin(a))}"/>`);
    }
    out.push('</g>');
    out.push(`<g stroke="${accent}" stroke-width="${sw(3.5, target, 0.8)}"`
      + ' stroke-linecap="butt" opacity=".95">');
    for (let i = 0; i < 4; i++) {
      const a = radians(tickPhase + i * 90.0);
      out.push(`<line x1="${fmt1(C + 156 * cos(a))}" y1="${fmt1(C + 156 * sin(a))}"`
        + ` x2="${fmt1(C + 222 * cos(a))}" y2="${fmt1(C + 222 * sin(a))}"/>`);
    }
    out.push('</g>');
  }
  out.push('</g>');
  out.push(...labelPlate(label, base, accent, target));
  out.push(...close(safe));
  return out.join('\n') + '\n';
}

// --------------------------------------------------------------------------- //
// family 2 - register mark
// --------------------------------------------------------------------------- //

const TINTS = [1.0, 0.66, 0.40, 0.18];

/** A press registration target blown up to fill the whole face. */
export function register_mark(seed, base, accent, target, label) {
  check(target);
  const rng = new PyRandom(seed);
  const rotation = rng.uniform(-16.0, 16.0);
  const solid = rng.randrange(4);
  const gap = rng.uniform(58.0, 82.0);
  const cropInset = rng.uniform(-10.0, 10.0);

  const [out, safe] = open(target, label);
  out.push(...plate(base));
  out.push('<g id="art" clip-path="url(#disc)">');
  out.push(`<g transform="rotate(${fmt1(rotation)} 256 256)">`);

  // Four quadrants, inked at descending tint steps from the solid one.
  for (let q = 0; q < 4; q++) {
    const tint = TINTS[pyMod(q - solid, 4)];
    if (tint <= 0.0) continue;
    const a0 = q * TAU / 4.0;
    const a1 = a0 + TAU / 4.0;
    const x0 = C + 300 * cos(a0);
    const y0 = C + 300 * sin(a0);
    const x1 = C + 300 * cos(a1);
    const y1 = C + 300 * sin(a1);
    out.push(`<path d="M256 256 L${fmt1(x0)} ${fmt1(y0)} A300 300 0 0 1 ${fmt1(x1)} ${fmt1(y1)} Z"`
      + ` fill="${accent}" opacity="${fmt2(tint)}"/>`);
  }

  // Crop marks: L brackets in the corners of the imposition.
  if (target !== 42) {
    const arm = 46.0;
    const inset = 148.0 + cropInset;
    for (const [sx, sy] of [[-1, -1], [1, -1], [-1, 1], [1, 1]]) {
      const px = C + sx * inset;
      const py = C + sy * inset;
      out.push(`<path d="M${fmt1(px - sx * arm)} ${fmt1(py)} L${fmt1(px)} ${fmt1(py)}`
        + ` L${fmt1(px)} ${fmt1(py - sy * arm)}" fill="none" stroke="${base}"`
        + ` stroke-width="${sw(9, target)}" opacity=".8"/>`);
    }
  }

  // The crosshair: knocked out of the ink, then hairlined in ink down its
  // middle, so it stays crisp over the solid quadrant and the open one alike.
  const arms = [[0, -1], [0, 1], [-1, 0], [1, 0]].map(
    ([dx, dy]) => [C + dx * gap, C + dy * gap, C + dx * 232, C + dy * 232],
  );
  out.push(`<g stroke="${base}" stroke-width="${sw(22, target, 2.2)}"`
    + ' stroke-linecap="butt">');
  for (const [x1, y1, x2, y2] of arms) {
    out.push(`<line x1="${fmt1(x1)}" y1="${fmt1(y1)}" x2="${fmt1(x2)}" y2="${fmt1(y2)}"/>`);
  }
  out.push('</g>');
  if (target !== 42) {
    out.push(`<g stroke="${accent}" stroke-width="${sw(4, target, 0.9)}"`
      + ' stroke-linecap="butt" opacity=".9">');
    for (const [x1, y1, x2, y2] of arms) {
      out.push(`<line x1="${fmt1(x1)}" y1="${fmt1(y1)}" x2="${fmt1(x2)}" y2="${fmt1(y2)}"/>`);
    }
    out.push('</g>');
  }

  out.push('</g>');
  out.push('</g>');

  // Bullseye at dead centre - knocked out of the plastic, ringed in ink.
  out.push('<g id="stamp">');
  out.push(`<circle cx="256" cy="256" r="${fmt1(gap - 8)}" fill="${base}"`
    + ` stroke="${accent}" stroke-width="${sw(12, target)}"/>`);
  if (target === 220) {
    out.push(`<circle cx="256" cy="256" r="${fmt1(gap - 26)}" fill="none"`
      + ` stroke="${accent}" stroke-width="4" opacity=".7"/>`);
  }
  out.push(`<circle cx="256" cy="256" r="${fmt1(Math.max(11.0, gap * 0.24))}" fill="${accent}"/>`);
  out.push('</g>');

  out.push(...rim(accent, target));
  out.push(...labelPlate(label, base, accent, target));
  out.push(...close(safe));
  return out.join('\n') + '\n';
}

// --------------------------------------------------------------------------- //
// family 3 - hot foil
// --------------------------------------------------------------------------- //

/** A hot-stamp foil die: faceted badge, raked sheen, knurled tick ring. */
export function hot_foil(seed, base, accent, target, label) {
  check(target);
  const rng = new PyRandom(seed);
  const facets = rng.choice([6, 6, 8]);
  const dieRotation = rng.uniform(-22.0, 22.0);
  const rake = rng.uniform(-38.0, 38.0);
  const knurlPhase = rng.uniform(0.0, 22.0);

  const badgeR = 144.0;
  const diePoints = poly(C, C, badgeR, facets, dieRotation);
  const defs = [`<clipPath id="die"><polygon points="${diePoints}"/></clipPath>`];
  const [out, safe] = open(target, label, defs);
  out.push(...plate(base));

  out.push('<g id="art" clip-path="url(#disc)">');
  // Knurl: the ring of teeth the stamping die leaves around the impression.
  const teeth = target === 42 ? 12 : (target === 96 ? 20 : 32);
  const toothIn = target === 42 ? 168.0 : 176.0;
  out.push(`<g id="knurl" stroke="${accent}" stroke-width="${sw(14, target)}"`
    + ' stroke-linecap="butt" opacity=".92">');
  for (let i = 0; i < teeth; i++) {
    const a = radians(knurlPhase + i * 360.0 / teeth);
    out.push(`<line x1="${fmt1(C + toothIn * cos(a))}"`
      + ` y1="${fmt1(C + toothIn * sin(a))}"`
      + ` x2="${fmt1(C + 210 * cos(a))}" y2="${fmt1(C + 210 * sin(a))}"/>`);
  }
  out.push('</g>');
  out.push('</g>');

  out.push('<g id="stamp">');
  out.push(`<polygon points="${diePoints}" fill="${accent}"/>`);
  // Foil sheen: the die's bevel splits the badge into a lit half and a shaded
  // half, with one narrow specular band riding the split line.
  out.push('<g clip-path="url(#die)">');
  out.push(`<g transform="rotate(${fmt1(rake)} 256 256)">`);
  out.push('<rect x="-16" y="-16" width="544" height="256" fill="#ffffff" opacity=".22"/>');
  out.push('<rect x="-16" y="256" width="544" height="272" fill="#000000" opacity=".20"/>');
  out.push('<rect x="-16" y="232" width="544" height="26" fill="#ffffff" opacity=".55"/>');
  out.push('<rect x="-16" y="300" width="544" height="14" fill="#ffffff" opacity=".22"/>');
  out.push('</g>');
  out.push('</g>');
  // Keyline: the die's inner step, knocked back to the plastic colour.
  if (target !== 42) {
    const inner = poly(C, C, badgeR - 34.0, facets, dieRotation);
    out.push(`<polygon points="${inner}" fill="none" stroke="${base}"`
      + ` stroke-width="${sw(9, target)}" opacity=".75"/>`);
  }
  out.push('</g>');

  out.push(...rim(accent, target));
  out.push(...labelPlate(label, base, accent, target));
  out.push(...close(safe));
  return out.join('\n') + '\n';
}

export const RENDERERS = {
  'halftone-screen': halftone_screen,
  'register-mark': register_mark,
  'hot-foil': hot_foil,
};
