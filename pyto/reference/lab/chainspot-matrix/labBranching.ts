/** Default-OFF LAB experiment: deterministic branch probing. */
import type { ABFeature, FeatureContext } from '../detectors/threeFactor/features/types';
import type { ABFeatureSet, ABFeatureOperation } from '../exec/feature-set';
import type { ExecBoard } from '../exec/board';
import type { CalculationBinding } from '../exec/gateway';
import type { ProbeReader, Point, Heading, BranchingRun } from '../experimental/branching';
import {
	runBranchingProbe,
	readInitialReadings,
	proposeLossTriggeredPositions,
	headingVariants,
	diagnoseReflectedRay,
	serializeContinuation,
	deserializeContinuation,
	resumeBranchingProbe
} from '../experimental/branching';

export * from '../experimental/branching';

export interface LabBranchingInput {
	readonly origin: Point;
	readonly heading: Heading;
	readonly reader: ProbeReader;
	readonly sourceHash?: string;
	readonly seed?: number;
	readonly mode?: 'fixed' | 'poisson' | 'reflection';
	readonly maxObservations?: number;
	readonly widthPx?: number;
	readonly normal?: Heading;
	readonly contact?: Point;
	/** Serialized PAUSED state from a previous gateway slice. */
	readonly continuation?: string;
}

export interface LabBranchingOptions {
	readonly proposalCount?: number;
	readonly proposalRadiusPx?: number;
	readonly proposalMinDistancePx?: number;
	readonly headingOffsetsRadians?: readonly number[];
	readonly maxObservations?: number;
}

export interface LabBranchingResult {
	readonly status: BranchingRun['status'];
	readonly observations: BranchingRun['observations'];
	readonly continuation?: string;
	readonly initialReadings: ReturnType<typeof readInitialReadings>;
	readonly reflection?: ReturnType<typeof diagnoseReflectedRay>;
	readonly reflectionUnsupported?: 'missing-normal-or-contact';
}

const featureId = 'lab.branching';

function nonNegative(value: unknown): string | null {
	return typeof value === 'number' && Number.isFinite(value) && value >= 0 ? null : 'must be a finite non-negative number';
}

export const labBranchingFeature: ABFeature = {
	id: featureId,
	gate: 'G6',
	kind: 'deviation',
	defaultEnabled: false,
	resolveOnlyWhenConfigured: true,
	note: 'Experimental loss-triggered branch probing; probe model/calculation only.',
	knobs: {
		proposalRadiusPx: { default: 12, validate: nonNegative },
		proposalMinDistancePx: { default: 3, validate: nonNegative },
		proposalCount: { default: 8, validate: nonNegative }
	}
};

function calculateBranch(input: LabBranchingInput, options: LabBranchingOptions): LabBranchingResult {
	const mode = input.mode ?? 'poisson';
	const reflection = mode === 'reflection' && input.normal && input.contact
		? diagnoseReflectedRay({
			direction: input.heading,
			normal: input.normal,
			widthPx: input.widthPx ?? 0
		})
		: undefined;
	const run = input.continuation
		? resumeBranchingProbe(input.continuation, {
			reader: input.reader,
			seed: input.seed,
			...options,
			...(input.maxObservations !== undefined ? { maxObservations: input.maxObservations } : {})
		})
		: runBranchingProbe({
		origin: input.origin,
		heading: input.heading,
		reader: input.reader,
		seed: input.seed,
		...options,
		...(input.maxObservations !== undefined ? { maxObservations: input.maxObservations } : {}),
		...(mode === 'fixed' ? { proposalCount: 0, headingOffsetsRadians: [0] } : {}),
		...(mode === 'reflection' ? { proposalCount: 0, headingOffsetsRadians: [0] } : {})
		});
	const initialReadings = run.observations.filter(observation => observation.id === 'initial-3' || observation.id === 'initial-4').map(observation => ({ position: observation.position, heading: observation.heading, distancePx: observation.id === 'initial-3' ? 3 as const : 4 as const, status: observation.status === 'accepted' ? 'visible' as const : observation.status === 'rejected' ? 'loss' as const : 'unknown' as const }));
	return {
		status: run.status,
		observations: run.observations,
		initialReadings,
		...(reflection ? { reflection } : {}),
		...(mode === 'reflection' && !reflection ? { reflectionUnsupported: 'missing-normal-or-contact' as const } : {}),
		...(run.continuation ? { continuation: serializeContinuation(run.continuation) } : {})
	};
}

function makeOperation(feature: ABFeature): ABFeatureOperation {
	return {
	spec: {
		id: 'lab.branching.probe',
		kind: 'compute',
		gate: 'G6',
		unit: 'labBranching',
		consumes: ['lab.input'],
		produces: ['lab.branch.result'],
		calculations: ['fn.labBranching.probe'],
		features: [feature.id],
		knobBindings: ['proposalRadiusPx', 'proposalMinDistancePx', 'proposalCount'],
		note: 'Seeded deterministic probe calculation; rejection and UNKNOWN remain explicit.'
	},
	run(board: ExecBoard, ctx: FeatureContext) {
		const input = board.get<LabBranchingInput>('lab.input');
		const knobs = ctx.resolve(feature).knobs as unknown as LabBranchingOptions;
		board.set('lab.branch.result', calculateBranch(input, knobs));
	},
	calculationBindings: [
		{ address: 'fn.labBranching.probe', calculate: calculateBranch as (...args: never[]) => unknown }
	] as readonly CalculationBinding[]
	};
}

/** Composition boundary for the default-OFF LAB experiment. */
export function createLabBranchingFeatureSet(
	_input?: LabBranchingInput,
	_options: LabBranchingOptions = {}
): ABFeatureSet {
	const feature: ABFeature = {
		...labBranchingFeature,
		knobs: {
			proposalRadiusPx: { ...labBranchingFeature.knobs.proposalRadiusPx, default: _options.proposalRadiusPx ?? 12 },
			proposalMinDistancePx: { ...labBranchingFeature.knobs.proposalMinDistancePx, default: _options.proposalMinDistancePx ?? 3 },
			proposalCount: { ...labBranchingFeature.knobs.proposalCount, default: _options.proposalCount ?? 8 }
		}
	};
	return {
		id: 'lab.branching',
		features: [{ ...feature, operations: [makeOperation(feature)] }],
		seededSlots: ['lab.input'],
		note: 'Experimental only. Caller seeds lab.input and reads lab.branch.result.'
	};
}
