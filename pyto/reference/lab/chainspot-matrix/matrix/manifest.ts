import { createHash } from 'node:crypto';
import type { MatrixCase, MatrixJob, MatrixManifest, MatrixProgressRow, MatrixReceipt, MatrixVariant } from './types';

/** Stable JSON makes job/cache identities independent of object insertion order. */
export function canonicalJson(value: unknown): string {
	if (value === null || typeof value !== 'object') return JSON.stringify(value);
	if (Array.isArray(value)) return `[${value.map(canonicalJson).join(',')}]`;
	return `{${Object.keys(value as Record<string, unknown>).sort().map((key) => `${JSON.stringify(key)}:${canonicalJson((value as Record<string, unknown>)[key])}`).join(',')}}`;
}

export function sha256(value: unknown): string {
	return createHash('sha256').update(typeof value === 'string' ? value : canonicalJson(value)).digest('hex');
}

function requiredMissing(manifest: MatrixManifest, entry: MatrixCase): string[] {
	const available = new Set(manifest.availablePrerequisites ?? []);
	return (entry.prerequisites ?? []).filter((name) => !available.has(name));
}

/** Expand every case × variant pair in deterministic input order. */
export function materializeMatrixJobs(manifest: MatrixManifest, cases = manifest.cases ?? []): readonly MatrixJob[] {
	if (!Array.isArray(manifest.variants) || manifest.variants.length === 0) throw new Error('matrix manifest requires at least one variant');
	const seenCases = new Set<string>();
	const seenVariants = new Set<string>();
	for (const entry of cases) {
		if (!entry.id?.trim()) throw new Error('matrix case id is required');
		if (seenCases.has(entry.id)) throw new Error(`duplicate matrix case id '${entry.id}'`);
		seenCases.add(entry.id);
	}
	for (const variant of manifest.variants) {
		if (!variant.id?.trim()) throw new Error('matrix variant id is required');
		if (seenVariants.has(variant.id)) throw new Error(`duplicate matrix variant id '${variant.id}'`);
		seenVariants.add(variant.id);
	}
	return cases.flatMap((entry) => manifest.variants.map((variant) => {
		const missing = requiredMissing(manifest, entry);
		const key = matrixJobKey(manifest, entry, variant);
		return Object.freeze({
			key, caseId: entry.id, variantId: variant.id, case: entry, variant,
			status: missing.length ? 'missing-prerequisite' : 'pending',
			missingPrerequisites: Object.freeze(missing)
		}) as MatrixJob;
	}));
}

export function matrixJobKey(manifest: MatrixManifest, entry: MatrixCase, variant: MatrixVariant): string {
	return sha256({ calculationRevision: manifest.calculationRevision ?? 'UNKNOWN', sourceRevision: manifest.sourceRevision ?? 'UNKNOWN', case: entry, variant });
}

export function initialProgress(jobs: readonly MatrixJob[]): readonly MatrixProgressRow[] {
	return jobs.map((job) => ({ key: job.key, caseId: job.caseId, variantId: job.variantId, status: job.status, completed: 0, total: 1, message: job.missingPrerequisites.length ? `missing: ${job.missingPrerequisites.join(', ')}` : undefined }));
}

export function createMatrixReceipt(manifest: MatrixManifest, runId: string, jobs = materializeMatrixJobs(manifest), now = new Date().toISOString()): MatrixReceipt {
	return Object.freeze({ schema: 'chainspot-matrix-receipt@1' as const, runId, createdAt: now, updatedAt: now, manifestHash: sha256(manifest), jobs: Object.freeze([...jobs]), progress: Object.freeze([...initialProgress(jobs)]), results: Object.freeze({}), errors: Object.freeze({}) });
}

/** Update one row while preserving receipt history and job identity. */
export function updateMatrixReceipt<T>(receipt: MatrixReceipt<T>, key: string, update: { status: MatrixJob['status']; result?: T; error?: string; message?: string }, now = new Date().toISOString()): MatrixReceipt<T> {
	if (!receipt.jobs.some((job) => job.key === key)) throw new Error(`unknown matrix job '${key}'`);
	const progress = receipt.progress.map((row) => row.key === key ? { ...row, status: update.status, completed: update.status === 'complete' || update.status === 'failed' || update.status === 'unsupported' ? 1 : row.completed, message: update.message ?? update.error } : row);
	const results = update.result === undefined ? receipt.results : { ...receipt.results, [key]: update.result };
	const errors = update.error === undefined ? receipt.errors : { ...receipt.errors, [key]: update.error };
	return Object.freeze({ ...receipt, updatedAt: now, progress: Object.freeze(progress), results: Object.freeze(results), errors: Object.freeze(errors) });
}
