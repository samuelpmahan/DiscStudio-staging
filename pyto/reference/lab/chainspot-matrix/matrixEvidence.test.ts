import { describe, expect, test } from 'vitest';
import { createMatrixReceipt, materializeMatrixJobs, updateMatrixReceipt } from '../../scripts/chainspot-lab/sweep/matrix/manifest';
import { classifyEvidence, compareParity, countCacheEvents, groupEvidence } from '../../scripts/chainspot-lab/sweep/matrix/evidence';

const manifest = { calculationRevision: 'calc-1', sourceRevision: 'src-1', variants: [{ id: 'narrow', params: { width: 40 } }, { id: 'broad', params: { width: 50 } }] as const };

describe('matrix materialization and evidence', () => {
	test('materializes every case × variant pair with stable keys', () => {
		const jobs = materializeMatrixJobs(manifest, [{ id: 'h1', image: 'one.png' }, { id: 'h2', image: 'two.png' }]);
		expect(jobs).toHaveLength(4);
		expect(jobs.map((job) => `${job.caseId}/${job.variantId}`)).toEqual(['h1/narrow', 'h1/broad', 'h2/narrow', 'h2/broad']);
		expect(new Set(jobs.map((job) => job.key)).size).toBe(4);
	});

	test('receipt updates are immutable and resumable by exact key', () => {
		const job = materializeMatrixJobs(manifest, [{ id: 'h1', prerequisites: ['seed'] }])[0];
		const before = createMatrixReceipt(manifest, 'run', [job], 't0');
		const after = updateMatrixReceipt(before, job.key, { status: 'complete', result: { value: 1 } }, 't1');
		expect(before.progress[0].status).toBe('missing-prerequisite');
		expect(after.progress[0].status).toBe('complete');
		expect(after.results[job.key]).toEqual({ value: 1 });
	});

	test('groups observable evidence and retains every requested bucket', () => {
		expect(classifyEvidence({ edgeSupport: 'none', previousEdgeSupport: 'paired' })).toBe('edge_loss');
		expect(classifyEvidence({ widthPx: 50, widthMaxPx: 50 })).toBe('width_boundary');
		const groups = groupEvidence([{ key: 'a', paused: true }, { key: 'b', unresolved: true }]);
		expect(groups.paused).toHaveLength(1);
		expect(groups.unresolved).toHaveLength(1);
		expect(Object.keys(groups)).toEqual(['edge_loss', 'width_boundary', 'branch_reacquired', 'paused', 'unresolved']);
	});

	test('cache counters and parity expose misses and differences', () => {
		expect(countCacheEvents([{ key: 'a', hit: true }, { key: 'a', hit: false, wrote: true }, { key: 'b', hit: false }])).toEqual({ requests: 3, hits: 1, misses: 2, writes: 1, uniqueKeys: 2 });
		expect(compareParity({ a: 1 }, { a: 2, b: 3 })).toMatchObject({ equal: false, compared: 2, mismatches: [{ key: 'a' }, { key: 'b' }] });
	});
});
