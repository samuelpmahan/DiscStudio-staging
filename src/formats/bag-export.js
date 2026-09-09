import { safeImage, stable } from '../domain.js';

const asMap = value => Array.isArray(value) ? Object.fromEntries(value.map(item => [item.id, item])) : (value || {});
// Dotted paths are unambiguous: unusual own keys are URI-encoded by segment,
// while ordinary domain names stay readable (e.g. mold.flight.speed).
const segment = key => /^[A-Za-z][A-Za-z0-9_-]{0,99}$/.test(key) ? key : encodeURIComponent(key).replaceAll('.', '%2E');
const photoKey = key => key === 'photo' || key.endsWith('.photo');

function scalar(value, path) {
  if (photoKey(path) && value != null && !safeImage(value)) return null;
  if (value === undefined) return null;
  if (value && typeof value === 'object') return stable(value);
  return value;
}

function flatten(value, prefix, out) {
  if (value === undefined) return;
  if (value && typeof value === 'object' && !Array.isArray(value)) {
    const keys = Object.keys(value).sort();
    if (!keys.length) { out[prefix] = scalar(value, prefix); return; }
    for (const key of keys) flatten(value[key], `${prefix}.${segment(key)}`, out);
    return;
  }
  out[prefix] = scalar(value, prefix);
}

const csvCell = value => {
  const text = value == null ? '' : typeof value === 'string' ? value : stable(value);
  return `"${text.replaceAll('"', '""')}"`;
};

/** Deterministic, local-only export of one shared Bag and its physical discs. */
export function bagExport({ bag, discs, molds, manufacturers } = {}) {
  if (!bag || typeof bag.id !== 'string' || !Array.isArray(bag.discIds)) throw new Error('Bag export requires a Bag Part.');
  const discMap = asMap(discs), moldMap = asMap(molds), makerMap = asMap(manufacturers);
  const rows = bag.discIds.map((discId) => {
    const disc = discMap[discId];
    if (!disc) throw new Error(`Bag references missing physical disc '${discId}'.`);
    const mold = moldMap[disc.moldId];
    if (!mold) throw new Error(`Disc '${discId}' has unresolved mold identity.`);
    const manufacturer = makerMap[mold.manufacturerId];
    if (!manufacturer) throw new Error(`Mold '${mold.id}' has unresolved manufacturer identity.`);
    const row = Object.create(null);
    flatten(bag, 'bag', row);
    flatten(disc, 'disc', row);
    flatten(mold, 'mold', row);
    flatten(manufacturer, 'manufacturer', row);
    return row;
  });
  const columns = [...new Set(rows.flatMap(row => Object.keys(row)))].sort();
  const jsonRows = rows.map(row => Object.fromEntries(columns.map(column => [column, row[column] ?? null])));
  const json = JSON.stringify({ bagId: bag.id, columns, rows: jsonRows });
  const csv = [columns.map(csvCell).join(','), ...jsonRows.map(row => columns.map(column => csvCell(row[column])).join(','))].join('\n') + '\n';
  return { kind: 'BagExport', format: 'disc.format.bagExport', bagId: bag.id, rowCount: rows.length, columns, json, csv };
}

export default bagExport;
