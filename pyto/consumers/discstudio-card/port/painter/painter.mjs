// painter.mjs -- the disc-art painter in JavaScript, byte-identical to the Python.
//
//   import { render } from './painter.mjs';
//   render(family, seed, base, accent, target, label) -> string  // the whole SVG document
//
// `family` is a slug from art_registry.ALL_FAMILIES ('orbit-foundry', 'wind-rose',
// ...); the four classic display names ('Orbit Foundry', ...) are accepted too.
// Dependency-free ES module: no npm, no DOM, Node 22 and browsers alike.
//
// The four classic families are ported here from paint_components.py. The twelve
// tournament families are served from ./families/<studio>.mjs, exactly as
// art_registry.py serves them from the studio modules.

import {
  PyRandom, escape, fmt1, fmt2, pyNum, strokeFloor, xy, degrees,
  SIZE, TARGETS, TAU,
} from './core.mjs';
import * as foundry from './families/foundry.mjs';
import * as cartography from './families/cartography.mjs';
import * as signal from './families/signal.mjs';
import * as botanical from './families/botanical.mjs';

// The four originals. Their bytes are frozen upstream by test_paint_families.py.
export const CLASSIC_FAMILIES = ['Orbit Foundry', 'Petal Press', 'Signal Stamp', 'Tessellated Flight'];

const CLASSIC_SLUGS = {
  'orbit-foundry': 'Orbit Foundry',
  'petal-press': 'Petal Press',
  'signal-stamp': 'Signal Stamp',
  'tessellated-flight': 'Tessellated Flight',
};

function classicRenderer(name) {
  return (seed, base, accent, target, label) => renderClassic(name, seed, base, accent, target, label);
}

/** art_registry.ALL_FAMILIES: slug -> render(seed, base, accent, target, label). */
export const RENDERERS = {
  // classic -- paint_components.py, through this module's own port
  'orbit-foundry': classicRenderer('Orbit Foundry'),
  'petal-press': classicRenderer('Petal Press'),
  'signal-stamp': classicRenderer('Signal Stamp'),
  'tessellated-flight': classicRenderer('Tessellated Flight'),
  // promoted -- paint_families.py, ported beside the studio that produced them
  'pressed-fern': botanical.pressed_fern,
  'nodding-seedhead': botanical.nodding_seedhead,
  'wind-rose': cartography.wind_rose,
  // retained -- _families_<studio>.py
  'halftone-screen': foundry.halftone_screen,
  'register-mark': foundry.register_mark,
  'hot-foil': foundry.hot_foil,
  'chevron-run': signal.chevron_run,
  'score-bug': signal.score_bug,
  'sweep-clock': signal.sweep_clock,
  'contour-basin': cartography.contour_basin,
  'fairway-plat': cartography.fairway_plat,
  'block-print': botanical.block_print,
};

export const FAMILIES = Object.keys(RENDERERS);

/** paint_components.render / art_registry.family_render over the whole vocabulary. */
export function render(family, seed, base, accent, target, label) {
  const slug = Object.hasOwn(RENDERERS, family)
    ? family
    : Object.keys(CLASSIC_SLUGS).find((key) => CLASSIC_SLUGS[key] === family);
  if (slug === undefined) throw new Error('family is unsupported');
  return RENDERERS[slug](seed, base, accent, target, label);
}

// ------------------------------------------------- the four classic families

function renderClassic(family, seed, base, accent, target, label) {
  if (!CLASSIC_FAMILIES.includes(family) || !TARGETS.includes(target)) {
    throw new Error('family or target is unsupported');
  }
  // Derive every identity parameter once. Rendering another target consumes no RNG.
  const rng = new PyRandom(seed);
  const rotation = rng.uniform(-12, 12);
  const dotAngle = rng.uniform(-0.7, 0.7);
  const phase = rng.randrange(4);
  const safe = escape(label);
  // Values remain in the 512-unit viewBox; floor only the effective output width.
  const stroke = (source, minOutput = 1.0) => {
    const floor = strokeFloor(target, minOutput);
    return floor > source ? pyNum(floor) : pyNum(source);
  };
  const out = [
    '<?xml version="1.0" encoding="UTF-8"?>',
    `<svg xmlns="http://www.w3.org/2000/svg" width="${target}" height="${target}" viewBox="0 0 ${SIZE} ${SIZE}" role="img" aria-label="${safe}">`,
    '<defs><clipPath id="disc"><circle cx="256" cy="256" r="220"/></clipPath>',
    '<linearGradient id="depth" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".18"/><stop offset="1" stop-color="#000" stop-opacity=".28"/></linearGradient></defs>',
    '<g id="base" clip-path="url(#disc)">', `<circle cx="256" cy="256" r="220" fill="${base}"/>`,
    '<circle cx="256" cy="256" r="220" fill="url(#depth)"/>', '</g>',
    '<g id="rim" fill="none">', `<circle cx="256" cy="256" r="216" stroke="${accent}" stroke-width="${stroke(7)}" opacity=".9"/>`,
    `<circle cx="256" cy="256" r="201" stroke="#fff" stroke-width="${stroke(3)}" opacity=".28"/>`, '</g>',
    '<g id="art" clip-path="url(#disc)">',
  ];
  if (family === 'Orbit Foundry') {
    if (target === 42) {
      out.push(`<path d="M120 294 Q220 130 356 198" fill="none" stroke="${accent}" stroke-width="${stroke(18)}" stroke-linecap="round"/>`);
    } else {
      const count = target === 96 ? 2 : 3;
      for (let i = 0; i < count; i++) {
        const rad = [92, 146, 194][i];
        out.push(`<ellipse cx="256" cy="256" rx="${rad}" ry="${fmt1(rad * 0.38)}" fill="none" stroke="${accent}" stroke-width="${stroke(target === 220 ? 10 : 8)}" opacity=".8" transform="rotate(${fmt1(rotation + i * 28)} 256 256)"/>`);
      }
    }
  } else if (family === 'Petal Press') {
    const count = target === 42 ? 4 : (target === 96 ? 6 : 10);
    for (let i = 0; i < count; i++) {
      const a = i * TAU / count + rotation * Math.PI / 180;
      const [x, y] = xy(78, a);
      out.push(`<ellipse cx="${fmt1(x)}" cy="${fmt1(y)}" rx="${target === 42 ? 34 : 28}" ry="${target > 42 ? 72 : 54}" fill="${accent}" opacity=".72" transform="rotate(${fmt1(degrees(a) + 90)} ${fmt1(x)} ${fmt1(y)})"/>`);
    }
  } else if (family === 'Signal Stamp') {
    out.push(`<path d="M160 300 Q256 150 352 300" fill="none" stroke="${accent}" stroke-width="${stroke(24)}" stroke-linecap="round"/>`);
    out.push(`<path d="M172 206 l28 -20" stroke="${accent}" stroke-width="${stroke(18)}" stroke-linecap="round"/>`);
    if (target === 220) {
      out.push(`<circle cx="256" cy="256" r="74" fill="none" stroke="${accent}" stroke-width="${stroke(8)}" opacity=".65"/>`);
    }
  } else {
    const tiles = target === 42 ? 2 : (target === 96 ? 3 : 4);
    for (let i = 0; i < tiles; i++) {
      const x = 80 + (i + phase % 2) * 92;
      out.push(`<path d="M${x} 120 l70 0 120 272 -70 0z" fill="${accent}" opacity="${fmt2(0.72 - i * 0.08)}"/>`);
    }
  }
  out.push('</g>');
  out.push('<g id="stamp">');
  if (family === 'Petal Press') {
    out.push(`<circle cx="256" cy="256" r="${target < 220 ? 54 : 62}" fill="${base}" stroke="${accent}" stroke-width="${stroke(12)}"/>`);
  } else if (family === 'Tessellated Flight') {
    out.push(`<circle cx="256" cy="256" r="${target < 220 ? 42 : 52}" fill="${base}" stroke="${accent}" stroke-width="${stroke(10)}"/>`);
  } else {
    const [x, y] = xy(target === 42 ? 118 : 156, dotAngle);
    out.push(`<circle cx="${fmt1(x)}" cy="${fmt1(y)}" r="${target === 42 ? 16 : 12}" fill="${accent}"/>`);
  }
  out.push('</g>');
  if (target === 220) {
    // Python slices by code point; JS slices by UTF-16 unit, so an astral
    // character would be cut in half by label.slice(0, 10).
    const display = escape(Array.from(pyStrip(label)).slice(0, 10).join(''));
    out.push('<g id="text">', `<text x="256" y="420" text-anchor="middle" font-family="sans-serif" font-size="22" letter-spacing="3" fill="${accent}" opacity=".82">${display}</text>`, '</g>');
  }
  out.push(`<title>${safe}</title>`, '</svg>');
  return out.join('\n') + '\n';
}

// Python's str.strip() strips every code point str.isspace() accepts, which is
// not JS's \s set: it adds \x1c-\x1f and \x85, and it excludes U+FEFF.
const PY_SPACE = /[\u0009\u000a\u000b\u000c\u000d\u001c\u001d\u001e\u001f\u0020\u0085\u00a0\u1680\u2028\u2029\u202f\u205f\u3000\u2000-\u200a]/;

function pyStrip(text) {
  let start = 0;
  let end = text.length;
  while (start < end && PY_SPACE.test(text[start])) start++;
  while (end > start && PY_SPACE.test(text[end - 1])) end--;
  return text.slice(start, end);
}

export default { render, RENDERERS, FAMILIES };
