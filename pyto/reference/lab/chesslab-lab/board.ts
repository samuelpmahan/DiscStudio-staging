// Generic evidence store for the compiled-operation execution model.
// Structurally identical to threeFactor/features/types.ts's EvidenceBoard
// (get/has/set, fail-loud reads) but keyed by the open SlotRef string
// instead of the closed EvidenceSlot enum, so it can carry BOTH the
// classic unit-level slots ('stage', 'badges', 'measurement', ...) and the
// new dotted sub-slots a decomposed operation introduces ('badgeStage.
// masks', 'assignment.scoredPairs', ...) in one store. Browser-safe: no
// I/O, no node built-ins.

import type { OperationSpec, PxWriteTestimony, SlotRef } from './contract.ts';

export interface PxKey<T> {
	readonly address: SlotRef;
	readonly __value?: T;
}

export interface PxFn<Args, Result> {
	readonly address: `fn.${string}`;
	readonly __args?: Args;
	readonly __result?: Result;
}

export type PxCalculation<Args, Result> = (args: Args) => Result;

export function pxKey<T>(address: SlotRef): PxKey<T> {
	return Object.freeze({ address });
}

export function pxFn<Args, Result>(address: `fn.${string}`): PxFn<Args, Result> {
	return Object.freeze({ address });
}

function addressOf(slot: SlotRef | PxKey<unknown>): SlotRef {
	return typeof slot === 'string' ? slot : slot.address;
}

/**
 * PxC's browser-safe address space.  ExecBoard remains as a compatibility
 * name because this is the existing production board evolving in place, not
 * a second synchronized store.
 */
export interface PxC {
	get<T>(slot: SlotRef | PxKey<T>): T;
	has(slot: SlotRef | PxKey<unknown>): boolean;
	set<T>(slot: SlotRef | PxKey<T>, value: T): void;
	register<Args, Result>(fn: PxFn<Args, Result>, calculate: PxCalculation<Args, Result>): void;
	call<Args, Result>(fn: PxFn<Args, Result>, args: Args): Result;
}

export type ExecBoard = PxC;

export function createExecBoard(): PxC {
	const slots = new Map<SlotRef, unknown>();
	const calculations = new Map<string, PxCalculation<unknown, unknown>>();
	return {
		get<T>(slot: SlotRef | PxKey<T>): T {
			const address = addressOf(slot);
			if (!slots.has(address)) throw new Error(`exec board: slot '${address}' not produced yet.`);
			return slots.get(address) as T;
		},
		has: (slot) => slots.has(addressOf(slot)),
		set: (slot, value) => {
			slots.set(addressOf(slot), value);
		},
		register(fn, calculate) {
			const current = calculations.get(fn.address);
			if (current && current !== calculate) {
				throw new Error(`PxC: calculation '${fn.address}' is already registered.`);
			}
			calculations.set(fn.address, calculate as PxCalculation<unknown, unknown>);
		},
		call<Args, Result>(fn: PxFn<Args, Result>, args: Args): Result {
			const calculate = calculations.get(fn.address);
			if (!calculate) throw new Error(`PxC: calculation '${fn.address}' is not registered.`);
			return calculate(args) as Result;
		}
	};
}

/**
 * Wraps a board so every get()/set() call made through the wrapper during
 * one operation's run is recorded — the gateway's source for `actualConsumes`/
 * `actualProduces` on that operation's Receipt (see contract.ts). The
 * underlying board is untouched; this is a one-shot recorder, not a
 * persistent proxy.
 */
export function trackAccess(
	board: PxC,
	tick: Pick<OperationSpec, 'id' | 'consumes'>
): {
	tracked: PxC;
	consumed: Set<SlotRef>;
	produced: Set<SlotRef>;
	writes: PxWriteTestimony[];
	/** Calculations actually registered by this Tick, keyed by their fn.* address. */
	registered: Map<`fn.${string}`, PxCalculation<unknown, unknown>>;
	/** fn.* addresses actually called by this Tick. */
	called: Set<`fn.${string}`>;
} {
	const consumed = new Set<SlotRef>();
	const produced = new Set<SlotRef>();
	const writes: PxWriteTestimony[] = [];
	const registered = new Map<`fn.${string}`, PxCalculation<unknown, unknown>>();
	const called = new Set<`fn.${string}`>();
	const declaredConsumes = new Set(tick.consumes);
	const tracked: PxC = {
		get<T>(slot: SlotRef | PxKey<T>): T {
			const address = addressOf(slot);
			consumed.add(address);
			try {
				return board.get<T>(slot);
			} catch (error) {
				if (!board.has(slot)) {
					throw new Error(`PxC: Tick '${tick.id}' read missing address '${address}'.`, {
						cause: error
					});
				}
				throw error;
			}
		},
		has: (slot) => board.has(slot),
		set: (slot, value) => {
			const address = addressOf(slot);
			const existed = board.has(slot);
			produced.add(address);
			writes.push({
				address,
				kind: !existed
					? 'new-address'
					: declaredConsumes.has(address)
						? 'refinement'
						: 'replacement'
			});
			board.set(slot, value);
		},
		register: (fn, calculate) => {
			registered.set(fn.address, calculate as PxCalculation<unknown, unknown>);
			board.register(fn, calculate);
		},
		call: (fn, args) => {
			called.add(fn.address);
			return board.call(fn, args);
		}
	};
	return { tracked, consumed, produced, writes, registered, called };
}
