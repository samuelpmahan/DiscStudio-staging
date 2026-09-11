import { sha256HexSync } from './core/sha256.js';
export function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob), a = document.createElement('a'); a.href = url; a.download = filename; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1500);
}
export const downloadJson = (value, filename) => downloadBlob(new Blob([JSON.stringify(value, null, 2)], { type: 'application/json' }), filename);
export async function photoData(file) {
  if (!['image/png', 'image/jpeg', 'image/webp'].includes(file.type) || file.size > 15_000_000) throw new Error('Choose a PNG, JPEG or WebP photo under 15 MB.');
  const bitmap = await createImageBitmap(file), scale = Math.min(1, 1024 / Math.max(bitmap.width, bitmap.height));
  const canvas = document.createElement('canvas'); canvas.width = Math.round(bitmap.width * scale); canvas.height = Math.round(bitmap.height * scale);
  const ctx = canvas.getContext('2d'); if (!ctx) throw new Error('Image preparation is unavailable.'); ctx.drawImage(bitmap, 0, 0, canvas.width, canvas.height); bitmap.close();
  return canvas.toDataURL('image/webp', .86);
}
/** The PNG is the SVG Part at its own size: 1920x1080, or the 1080x1920 vertical canvas. */
export async function pngFromSvg(svg, width = 1920, height = 1080) {
  const url = URL.createObjectURL(new Blob([svg], { type: 'image/svg+xml;charset=utf-8' }));
  try {
    const image = new Image(); image.src = url; await image.decode();
    const canvas = document.createElement('canvas'); canvas.width = width; canvas.height = height;
    const ctx = canvas.getContext('2d'); if (!ctx) throw new Error('PNG export is unavailable.');
    ctx.drawImage(image, 0, 0, width, height);
    return await new Promise((resolve, reject) => canvas.toBlob(blob => blob ? resolve(blob) : reject(new Error('PNG conversion failed.')), 'image/png'));
  } finally { URL.revokeObjectURL(url); }
}
export async function sha256(value) {
  const bytes = typeof value === 'string' ? new TextEncoder().encode(value) : await value.arrayBuffer();
  return sha256HexSync(bytes instanceof Uint8Array ? bytes : new Uint8Array(bytes));
}
