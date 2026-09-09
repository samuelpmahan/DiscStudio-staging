/** Square share-image Calculation over the final rendered overlay Part. */
const esc = (value) => String(value ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

const innerSvg = (svg) => {
  if (typeof svg !== 'string' || !svg.trim()) throw new Error('Share image requires a rendered SVG Part.');
  const root = /<svg\b[^>]*>/i.exec(svg), close = svg.lastIndexOf('</svg>');
  if (!root || close < root.index + root[0].length) throw new Error('Rendered SVG is malformed.');
  const body = svg.slice(root.index + root[0].length, close);
  return body;
};

/**
 * Produce a deterministic 1080-square image from the existing final overlay.
 * The overlay already contains composed cards, ported art, photos and authored state.
 */
export function shareImage({ rendered, svg = rendered?.svg, width = rendered?.width, height = rendered?.height, background = 'transparent', label = 'DiscStudio share image' } = {}) {
  if (!Number.isFinite(width) || width <= 0 || !Number.isFinite(height) || height <= 0) throw new Error('Share image requires positive rendered dimensions.');
  const body = innerSvg(svg), scale = Math.min(1, 960 / width, 960 / height);
  const x = (1080 - width * scale) / 2, y = (1080 - height * scale) / 2;
  const backdrop = background === 'transparent' ? '' : `<rect width="1080" height="1080" fill="${esc(background)}"/>`;
  return { kind: 'ShareImage', format: 'disc.format.shareImage', width: 1080, height: 1080, label, svg: `<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1080" viewBox="0 0 1080 1080" role="img" aria-label="${esc(label)}">${backdrop}<g transform="translate(${x} ${y}) scale(${scale})">${body}</g></svg>` };
}

export default shareImage;
