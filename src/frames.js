/**
 * Reusable frame presets, the way constraints.js holds reusable Constraints:
 * named parameters a person picks, not a second renderer. `composeFrame` is
 * registered as `fn.overlay.frame`; what it returns is the model the same
 * `fn.overlay.svg` draws beneath the same cards, and the same
 * `fn.comparison.layout` stands the cards inside.
 *
 * A frame never invents a palette. Its fill, its title colour and its sponsor
 * lockup are the cards cascade's own global tokens (px.discstudio.cards.global),
 * so the vertical graphic and the cards on it are one design.
 */

/** The two canvases. 1080 × 1920 is the vertical one TikTok, Reels and Shorts want. */
export const canvases = {
  landscape: { id: 'landscape', name: 'Landscape · 1920 × 1080', width: 1920, height: 1080 },
  portrait: { id: 'portrait', name: 'Vertical · 1080 × 1920', width: 1080, height: 1920 }
};
export const orientations = Object.keys(canvases);
export const canvasFor = orientation => canvases[orientation] ?? canvases.landscape;

/**
 * `safe` is [top, right, bottom, left] per orientation. The vertical insets are
 * the room a phone's own furniture takes over a full-screen video -- the caption
 * and buttons along the bottom, the action rail down the right, the search row
 * at the top -- so a card placed inside them is a card that will still be read.
 */
export const framePresets = {
  none: {
    id: 'none', name: 'None · transparent overlay', fill: 'none', title: false, sponsor: false,
    safe: { landscape: [60, 60, 60, 60], portrait: [60, 60, 60, 60] },
    description: 'No frame: the transparent overlay exactly as it has always been exported.'
  },
  safe: {
    id: 'safe', name: 'Safe area · transparent', fill: 'none', title: true, sponsor: true,
    safe: { landscape: [96, 60, 84, 60], portrait: [300, 190, 430, 72] },
    description: 'Transparent, with a title strip and the safe area a phone leaves around its own caption, buttons and top row.'
  },
  filled: {
    id: 'filled', name: 'Safe area · filled background', fill: 'background', title: true, sponsor: true,
    safe: { landscape: [96, 60, 84, 60], portrait: [300, 190, 430, 72] },
    description: 'The same safe area on the cascade’s background colour, so the graphic stands on its own without footage.'
  }
};
export const framePreset = presetId => framePresets[presetId] ?? framePresets.none;

const TITLE_HEIGHT = { landscape: 74, portrait: 112 }, SPONSOR_HEIGHT = { landscape: 30, portrait: 44 }, GUTTER = 24;

/**
 * `fn.overlay.frame`. `spec` is what the world carries (orientation, which
 * preset, the title a person typed or the comparison's own name); `tokens` are
 * the cascade's global tokens, already validated as #rrggbb / 'transparent' by
 * validateCards, so nothing here re-sanitises what the cascade already owns.
 *
 * `safe` is the box the cards get: the preset's inset box, less the title strip
 * and the sponsor lockup when they are drawn, so nothing ever overlaps them.
 */
export function composeFrame({ spec = {}, tokens = {} }) {
  const orientation = spec.orientation === 'portrait' ? 'portrait' : 'landscape';
  const canvas = canvasFor(orientation), preset = framePreset(spec.presetId);
  const [top, right, bottom, left] = preset.safe[orientation];
  const box = { x: left, y: top, width: Math.max(120, canvas.width - left - right), height: Math.max(120, canvas.height - top - bottom) };
  const titleText = String(spec.title ?? '').trim().slice(0, 80);
  const sponsorText = preset.sponsor ? String(tokens.sponsor ?? '').trim().slice(0, 40) : '';
  const safe = { ...box };
  let title = null, sponsor = null;
  if (preset.title && titleText) {
    const h = TITLE_HEIGHT[orientation];
    title = {
      text: titleText, x: box.x, y: box.y, w: box.width, h,
      size: Math.round(h * 0.52), align: orientation === 'portrait' ? 'center' : 'left',
      color: tokens.foreground ?? '#fcfbf5', font: tokens.font ?? 'sans',
      rule: { x: box.x, y: box.y + h - 6, w: Math.min(box.width, orientation === 'portrait' ? box.width : 420), h: 5, fill: tokens.accent ?? '#b9d789' }
    };
    safe.y += h + GUTTER; safe.height -= h + GUTTER;
  }
  if (sponsorText) {
    const h = SPONSOR_HEIGHT[orientation];
    sponsor = {
      text: sponsorText, x: box.x, y: box.y + box.height - h, w: box.width, h,
      size: Math.round(h * 0.55), align: 'right', color: tokens.accent ?? '#b9d789', font: tokens.font ?? 'sans'
    };
    safe.height -= h + GUTTER;
  }
  return {
    orientation, presetId: preset.id, name: preset.name, description: preset.description,
    width: canvas.width, height: canvas.height,
    fill: preset.fill === 'background' ? (tokens.background ?? '#203d36') : 'none',
    box, safe: { ...safe, height: Math.max(120, safe.height) }, title, sponsor,
    note: `${canvas.name}${preset.id === 'none' ? '' : ` · ${preset.name}`}${title ? ` · “${title.text}”` : ''}${sponsor ? ` · ${sponsor.text}` : ''}`
  };
}

/** The box cards may stand in when no frame Part was bound at all: the canvas, inset. */
export const defaultSafe = orientation => {
  const canvas = canvasFor(orientation);
  return { x: 60, y: 60, width: canvas.width - 120, height: canvas.height - 120 };
};
