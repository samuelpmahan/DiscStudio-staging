import { describe, expect, it } from 'vitest';
import {
	diagnoseReflectedRay,
	headingVariants,
	proposeLossTriggeredPositions,
	readInitialReadings,
	runBranchingProbe,
	serializeContinuation,
	resumeBranchingProbe,
	type BranchingContinuation,
	createLabBranchingFeatureSet,
	labBranchingFeature
} from '../../packages/alg/src/experiments/labBranching';

describe('lab branching experiment', () => {
	it('reads exactly the continuous 3px and 4px initial probes', () => {
		const readings = readInitialReadings({ x: 10, y: 20 }, { x: 2, y: 0 }, () => 'visible');
		expect(readings.map((reading) => reading.distancePx)).toEqual([3, 4]);
		expect(readings.map((reading) => reading.position)).toEqual([
			{ x: 13, y: 20 },
			{ x: 14, y: 20 }
		]);
	});

	it('keeps seeded Poisson proposals deterministic and parent-linked', () => {
		const parent = {
			id: 'p',
			parentId: null,
			position: { x: 0, y: 0 },
			heading: { x: 1, y: 0 },
			status: 'rejected' as const
		};
		const a = proposeLossTriggeredPositions({
			parent,
			count: 4,
			radiusPx: 20,
			minDistancePx: 4,
			seed: 42
		});
		expect(a).toEqual(
			proposeLossTriggeredPositions({ parent, count: 4, radiusPx: 20, minDistancePx: 4, seed: 42 })
		);
		expect(a.every((proposal) => proposal.parentId === 'p')).toBe(true);
		expect(
			proposeLossTriggeredPositions({
				parent: { ...parent, status: 'unknown' },
				count: 2,
				radiusPx: 2,
				minDistancePx: 1,
				seed: 1
			})
		).toEqual([]);
	});

	it('does not quantize heading variants', () => {
		const variants = headingVariants({ x: 1, y: 0 }, [0.123456789]);
		expect(variants[0].offsetRadians).toBe(0.123456789);
		expect(variants[0].heading.x).toBeCloseTo(Math.cos(0.123456789));
	});

	it('reports reflection geometry without auto-bending', () => {
		const diagnostic = diagnoseReflectedRay({
			direction: { x: 1, y: -1 },
			normal: { x: 0, y: 1 },
			widthPx: 7
		});
		expect(diagnostic.autoBend).toBe(false);
		expect(diagnostic.reflectedDirection.y).toBeGreaterThan(0);
		expect(diagnostic.widthPx).toBe(7);
	});

	it('uses one reader call per operation, continues a visible ray past 356px, and keeps its heading', () => {
		let calls = 0;
		const run = runBranchingProbe({
			origin: { x: 0, y: 0 },
			heading: { x: 1, y: 0 },
			reader: () => {
				calls += 1;
				return { status: 'visible', measurements: [{ name: 'brightness', value: calls }] };
			},
			maxObservations: 200
		});
		expect(calls).toBe(200);
		expect(run.observations).toHaveLength(200);
		expect(run.status).toBe('PAUSED');
		expect(Math.max(...run.observations.map((o) => o.position.x))).toBeGreaterThan(356);
		expect(new Set(run.observations.map((o) => `${o.heading.x},${o.heading.y}`))).toEqual(
			new Set(['1,0'])
		);
		expect(run.observations.every((o) => o.measurements?.[0]?.value !== undefined)).toBe(true);
	});

	it('links every non-source sample within 4px and retains full Poisson targets after shortening poses', () => {
		const run = runBranchingProbe({
			origin: { x: 0, y: 0 },
			heading: { x: 1, y: 0 },
			reader: (p) => (p.x >= 11 ? 'loss' : 'visible'),
			seed: 4,
			proposalCount: 5,
			proposalRadiusPx: 20,
			proposalMinDistancePx: 4,
			maxObservations: 30
		});
		const byId = new Map(run.observations.map((o) => [o.id, o]));
		for (const observation of run.observations)
			if (observation.parentId) {
				const parent = byId.get(observation.parentId)!;
				expect(
					Math.hypot(
						observation.position.x - parent.position.x,
						observation.position.y - parent.position.y
					)
				).toBeLessThanOrEqual(4.000001);
			}
		const loss = run.observations.find((o) => o.reason === 'reading-loss')!;
		const branches = run.observations.filter((o) => o.parentId === loss.parentId && o.proposalId);
		expect(branches.length).toBeGreaterThan(1);
		expect(
			branches.every(
				(o) =>
					o.parentId !== loss.id &&
					Math.hypot(
						o.target!.x - byId.get(o.parentId!)!.position.x,
						o.target!.y - byId.get(o.parentId!)!.position.y
					) > 4
			)
		).toBe(true);
		const targets = run.continuation?.proposalDestinations ?? [];
		for (let i = 0; i < targets.length; i++)
			for (let j = i + 1; j < targets.length; j++)
				if (targets[i].ancestorId === targets[j].ancestorId)
					expect(
						Math.hypot(
							targets[i].position.x - targets[j].position.x,
							targets[i].position.y - targets[j].position.y
						)
					).toBeGreaterThanOrEqual(4);
	});

	it('does not cross sibling ancestry after late losses', () => {
		const run = runBranchingProbe({
			origin: { x: 0, y: 0 },
			heading: { x: 1, y: 0 },
			seed: 11,
			proposalCount: 4,
			reader: (p) => (p.x > 7 ? 'loss' : 'visible'),
			maxObservations: 45
		});
		const byId = new Map(run.observations.map((o) => [o.id, o]));
		for (const rejected of run.observations.filter((o) => o.status === 'rejected' && o.parentId)) {
			const parent = byId.get(rejected.parentId!)!;
			const children = run.observations.filter((o) => o.parentId === parent.id && o.proposalId);
			expect(children.every((o) => o.parentId === parent.id)).toBe(true);
			expect(run.observations.some((o) => o.parentId === rejected.id)).toBe(false);
		}
	});

	it('marks initial loss unresolved, keeps unknown explicit, and does not branch when proposalCount is zero', () => {
		const initialLoss = runBranchingProbe({
			origin: { x: 0, y: 0 },
			heading: { x: 1, y: 0 },
			reader: () => 'loss',
			proposalCount: 8
		});
		expect(initialLoss.observations.map((o) => o.reason)).toEqual([
			'unresolved-initial-loss',
			'unresolved-initial-loss'
		]);
		const unknown = runBranchingProbe({
			origin: { x: 0, y: 0 },
			heading: { x: 1, y: 0 },
			reader: () => 'unknown'
		});
		expect(unknown.observations[0]).toMatchObject({ status: 'unknown', reason: 'reading-unknown' });
		const noFork = runBranchingProbe({
			origin: { x: 0, y: 0 },
			heading: { x: 1, y: 0 },
			reader: (p) => (p.x >= 11 ? 'loss' : 'visible'),
			proposalCount: 0
		});
		expect(noFork.status).toBe('COMPLETE');
		expect(noFork.observations.some((o) => o.proposalId)).toBe(false);
	});

	it('resumes exact serialized state in per-invocation budgets without mutating the caller continuation', () => {
		const common = {
			origin: { x: 0, y: 0 },
			heading: { x: 1, y: 0 },
			reader: (p: { x: number }) => (p.x > 15 ? ('loss' as const) : ('visible' as const)),
			seed: 9,
			proposalCount: 3
		};
		const paused = runBranchingProbe({ ...common, maxObservations: 5 });
		expect(paused.observations).toHaveLength(5);
		expect(paused.status).toBe('PAUSED');
		const before = serializeContinuation(paused.continuation!);
		const resumed = resumeBranchingProbe(before, { reader: common.reader, maxObservations: 5 });
		const uninterrupted = runBranchingProbe({ ...common, maxObservations: 10 });
		expect(resumed.observations).toEqual(uninterrupted.observations);
		expect(resumed.observations.some((observation) => observation.reason === 'reading-loss')).toBe(
			true
		);
		expect(resumed.observations.some((observation) => observation.proposalId)).toBe(true);
		expect(serializeContinuation(paused.continuation!)).toBe(before);
		const one = runBranchingProbe({ ...common, maxObservations: 1 });
		expect(one.observations).toHaveLength(1);
		expect(
			resumeBranchingProbe(serializeContinuation(one.continuation!), {
				reader: common.reader,
				maxObservations: 1
			}).observations
		).toHaveLength(2);
	});

	it('keeps same-pose narrow heading variants as distinct queued reader operations', () => {
		const secondHeading = { x: Math.cos(0.000001), y: Math.sin(0.000001) };
		const continuation: BranchingContinuation = {
			version: 1,
			status: 'PAUSED',
			seed: 1,
			rngState: 1,
			nextId: 0,
			queue: [
				{
					position: { x: 3, y: 0 },
					parentId: 'ancestor',
					seed: 1,
					heading: { x: 1, y: 0 },
					kind: 'branch'
				},
				{
					position: { x: 3, y: 0 },
					parentId: 'ancestor',
					seed: 1,
					heading: secondHeading,
					kind: 'branch'
				}
			],
			frontier: [
				{
					position: { x: 3, y: 0 },
					parentId: 'ancestor',
					seed: 1,
					heading: { x: 1, y: 0 },
					kind: 'branch'
				},
				{
					position: { x: 3, y: 0 },
					parentId: 'ancestor',
					seed: 1,
					heading: secondHeading,
					kind: 'branch'
				}
			],
			observations: [
				{
					id: 'ancestor',
					parentId: null,
					position: { x: 0, y: 0 },
					heading: { x: 1, y: 0 },
					status: 'accepted'
				}
			],
			origin: { x: 0, y: 0 },
			heading: { x: 1, y: 0 },
			proposalCount: 0,
			proposalRadiusPx: 12,
			proposalMinDistancePx: 3,
			headingOffsetsRadians: [0],
			proposalDestinations: [],
			visited: ['3|0|1|0', `3|0|${secondHeading.x}|${secondHeading.y}`],
			headingCursor: 0,
			armStepCursor: 0
		};
		const run = resumeBranchingProbe(serializeContinuation(continuation), {
			reader: () => 'unknown',
			maxObservations: 2
		});
		expect(run.observations).toHaveLength(3);
		expect(run.observations.slice(1).map((observation) => observation.heading)).toEqual([
			{ x: 1, y: 0 },
			secondHeading
		]);
	});

	it('is a default-OFF feature with the requested execution slots', () => {
		const set = createLabBranchingFeatureSet();
		expect(labBranchingFeature.defaultEnabled).toBe(false);
		expect(set.seededSlots).toContain('lab.input');
		expect(set.features[0].operations?.[0].spec.produces).toContain('lab.branch.result');
	});
});
