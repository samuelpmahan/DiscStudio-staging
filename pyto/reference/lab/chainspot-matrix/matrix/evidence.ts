import { canonicalJson, sha256 } from './manifest';
import type { CacheCounters, EvidenceObservation, GalleryCategory, GalleryRow, ParityReport } from './types';

export const GALLERY_CATEGORIES: readonly GalleryCategory[] = ['edge_loss', 'width_boundary', 'branch_reacquired', 'paused', 'unresolved'];

/** Observable grouping only; unresolved is a deliberate final bucket. */
export function classifyEvidence(observation: EvidenceObservation): GalleryCategory {
	return classifyEvidenceCategories(observation)[0] ?? 'unresolved';
}

/** Return every observable tag; a row may belong to several gallery groups. */
export function classifyEvidenceCategories(observation: EvidenceObservation): readonly GalleryCategory[] {
	const categories: GalleryCategory[] = [];
	if (observation.paused === true || observation.stopReason === 'paused' || observation.stopReason === 'budget-exhausted') categories.push('paused');
	if (observation.branchReacquired === true) categories.push('branch_reacquired');
	if (observation.widthAtBoundary === true || (observation.widthPx != null && ((observation.widthMinPx != null && observation.widthPx <= observation.widthMinPx) || (observation.widthMaxPx != null && observation.widthPx >= observation.widthMaxPx)))) categories.push('width_boundary');
	const priorSupported = observation.previousEdgeSupport === 'paired' || observation.previousEdgeSupport === 'left' || observation.previousEdgeSupport === 'right';
	if ((observation.edgeSupport === 'none' || observation.edgeSupport === 'unknown') && priorSupported) categories.push('edge_loss');
	if (categories.length === 0) categories.push('unresolved');
	return categories;
}

export function groupEvidence(rows: readonly EvidenceObservation[], requested: readonly GalleryCategory[] = GALLERY_CATEGORIES): Readonly<Record<GalleryCategory, readonly GalleryRow[]>> {
	const groups = Object.fromEntries(requested.map((category) => [category, [] as GalleryRow[]])) as Record<GalleryCategory, GalleryRow[]>;
	for (const row of rows) {
		for (const category of classifyEvidenceCategories(row)) if (groups[category]) groups[category].push(Object.freeze({ ...row, category }));
	}
	return Object.freeze(Object.fromEntries(Object.entries(groups).map(([category, values]) => [category, Object.freeze(values)])) as Record<GalleryCategory, readonly GalleryRow[]>);
}

export function evidenceCacheKey(input: { calculationRevision: string; sourceRevision: string; inputHash: string; frame?: string; format?: string; parameters?: unknown }): string {
	return sha256({ calculationRevision: input.calculationRevision, sourceRevision: input.sourceRevision, inputHash: input.inputHash, frame: input.frame ?? 'UNKNOWN', format: input.format ?? 'UNKNOWN', parameters: input.parameters ?? {} });
}

export function countCacheEvents(events: readonly { readonly key: string; readonly hit: boolean; readonly wrote?: boolean }[]): CacheCounters {
	return { requests: events.length, hits: events.filter((event) => event.hit).length, misses: events.filter((event) => !event.hit).length, writes: events.filter((event) => event.wrote === true).length, uniqueKeys: new Set(events.map((event) => event.key)).size };
}

export function compareParity<T>(expected: Readonly<Record<string, T>>, actual: Readonly<Record<string, T>>): ParityReport {
	const keys = [...new Set([...Object.keys(expected), ...Object.keys(actual)])].sort();
	const mismatches = keys.filter((key) => canonicalJson(expected[key]) !== canonicalJson(actual[key])).map((key) => ({ key, expected: expected[key], actual: actual[key] }));
	return { equal: mismatches.length === 0, compared: keys.length, mismatches };
}

export function formatProgressRows(rows: readonly { readonly caseId: string; readonly variantId: string; readonly status: string; readonly completed: number; readonly total: number; readonly message?: string }[]): string {
	return rows.map((row) => `${row.caseId}\t${row.variantId}\t${row.status}\t${row.completed}/${row.total}${row.message ? `\t${row.message}` : ''}`).join('\n');
}

/** Machine-readable gallery index: source crops and all variant tracks stay attached to one case. */
export interface GalleryEntry {
	readonly caseId: string;
	readonly category: GalleryCategory;
	readonly sourceCrop?: string;
	readonly variants: readonly GalleryRow[];
}

export function buildGalleryIndex(rows: readonly EvidenceObservation[], requested: readonly GalleryCategory[] = GALLERY_CATEGORIES): readonly GalleryEntry[] {
	const grouped = groupEvidence(rows, requested);
	const byCase = new Map<string, GalleryEntry>();
	for (const category of requested) {
		for (const row of grouped[category] ?? []) {
			const caseId = row.caseId ?? row.key ?? 'UNKNOWN';
			const id = `${caseId}:${category}`;
			const prior = byCase.get(id);
			byCase.set(id, prior ? { ...prior, variants: Object.freeze([...prior.variants, row]) } : { caseId, category, sourceCrop: row.sourceCrop, variants: Object.freeze([row]) });
		}
	}
	return Object.freeze([...byCase.values()]);
}
