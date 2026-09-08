/**
 * The small semantic execution store used by neat.
 *
 * PxC deliberately keeps Parts and Calculations separate from the execution
 * receipts.  Every public operation returns a new value; calculations may
 * use the context passed to them, but cannot mutate a caller's PxC.
 */

export type PartAddress = string;

/** Calculation identities follow ChainSpot's address convention. */
export type CalculationId = string & { readonly __calculationId: unique symbol };

export function calculationId(value: string): CalculationId {
  if (!/^fn\.[A-Za-z0-9._-]+$/.test(value)) {
    throw new Error(`Calculation identity must use the fn.* form: ${value}`);
  }
  return value as CalculationId;
}

export interface Part<T = unknown> {
  readonly address: PartAddress;
  readonly value: T;
}

export interface PartRead {
  readonly address: PartAddress;
  readonly sequence: number;
  readonly found: boolean;
}

export interface PartWrite {
  readonly address: PartAddress;
  readonly sequence: number;
  readonly value: unknown;
  readonly replaced: boolean;
}

export interface CalculationInvocation {
  readonly id: CalculationId;
  readonly sequence: number;
  readonly status: "completed" | "failed";
  readonly args: unknown;
  readonly result?: unknown;
  readonly error?: unknown;
}

export type ExecutionEvent =
  | { readonly kind: "read"; readonly receipt: PartRead }
  | { readonly kind: "write"; readonly receipt: PartWrite }
  | {
      readonly kind: "invocation";
      readonly receipt: CalculationInvocation;
    };

export interface ExecutionTelemetry {
  readonly reads: ReadonlyArray<PartRead>;
  readonly writes: ReadonlyArray<PartWrite>;
  readonly invocations: ReadonlyArray<CalculationInvocation>;
  /** A total order of the observed traffic, useful for exact testimony. */
  readonly events: ReadonlyArray<ExecutionEvent>;
}

export interface CalculationContext {
  read<T = unknown>(address: PartAddress): T;
  write<T = unknown>(address: PartAddress, value: T): void;
  invoke<I, O>(id: CalculationId | string, args: I): O;
}

export interface Calculation<I = unknown, O = unknown> {
  readonly id: CalculationId;
  readonly run: (args: I, context: CalculationContext) => O;
}

export interface PxC {
  readonly parts: ReadonlyMap<PartAddress, unknown>;
  readonly calculations: ReadonlyMap<CalculationId, Calculation<unknown, unknown>>;
  readonly telemetry: ExecutionTelemetry;
}

export interface ReadPartResult<T> {
  readonly pxc: PxC;
  readonly value: T;
}

export interface InvokeResult<O> {
  readonly pxc: PxC;
  readonly value?: O;
  readonly invocation: CalculationInvocation;
  readonly error?: unknown;
}

/** Raised after an attempted read has already been recorded in `pxc`. */
export class MissingPartError extends Error {
  readonly pxc: PxC;

  constructor(pxc: PxC, address: PartAddress) {
    super(`Part not found: ${address}`);
    this.name = "MissingPartError";
    this.pxc = pxc;
  }
}

const emptyTelemetry = (): ExecutionTelemetry => ({
  reads: [],
  writes: [],
  invocations: [],
  events: [],
});

export function createPxC(
  parts: ReadonlyMap<PartAddress, unknown> | ReadonlyArray<Part<unknown>> | Record<string, unknown> = {},
): PxC {
  const map = new Map<PartAddress, unknown>();
  if (parts instanceof Map) {
    parts.forEach((value, address) => map.set(address, value));
  } else if (Array.isArray(parts)) {
    parts.forEach(({ address, value }) => map.set(address, value));
  } else {
    const record = parts as Record<string, unknown>;
    Object.keys(record).forEach((address) => map.set(address, record[address]));
  }
  return { parts: map, calculations: new Map(), telemetry: emptyTelemetry() };
}

export function registerPart<T>(pxc: PxC, address: PartAddress, value: T): PxC {
  const parts = new Map(pxc.parts);
  parts.set(address, value);
  return { ...pxc, parts };
}

export function registerCalculation<I, O>(pxc: PxC, calculation: Calculation<I, O>): PxC {
  const id = calculationId(calculation.id);
  if (pxc.calculations.has(id)) {
    throw new Error(`Calculation already registered: ${id}`);
  }
  const calculations = new Map(pxc.calculations);
  calculations.set(id, calculation as Calculation<unknown, unknown>);
  return { ...pxc, calculations };
}

function appendEvent(pxc: PxC, event: ExecutionEvent): PxC {
  const events = [...pxc.telemetry.events, event];
  const reads = event.kind === "read" ? [...pxc.telemetry.reads, event.receipt] : pxc.telemetry.reads;
  const writes = event.kind === "write" ? [...pxc.telemetry.writes, event.receipt] : pxc.telemetry.writes;
  const invocations = event.kind === "invocation"
    ? [...pxc.telemetry.invocations, event.receipt]
    : pxc.telemetry.invocations;
  const telemetry: ExecutionTelemetry = { reads, writes, invocations, events };
  return { ...pxc, telemetry };
}

function readPartInternal<T>(pxc: PxC, address: PartAddress): ReadPartResult<T> {
  const sequence = pxc.telemetry.events.length;
  const found = pxc.parts.has(address);
  const receipt: PartRead = { address, sequence, found };
  const next = appendEvent(pxc, { kind: "read", receipt });
  if (!found) throw new MissingPartError(next, address);
  return { pxc: next, value: pxc.parts.get(address) as T };
}

export function readPart<T = unknown>(pxc: PxC, address: PartAddress): ReadPartResult<T> {
  return readPartInternal(pxc, address);
}

export function readPartValue<T = unknown>(pxc: PxC, address: PartAddress): T {
  return readPartInternal<T>(pxc, address).value;
}

/** Explicit get/set names for callers treating Parts as an addressed map. */
export const getPart = readPart;

export function writePart<T>(pxc: PxC, address: PartAddress, value: T): PxC {
  const sequence = pxc.telemetry.events.length;
  const receipt: PartWrite = {
    address,
    sequence,
    value,
    replaced: pxc.parts.has(address),
  };
  const parts = new Map(pxc.parts);
  parts.set(address, value);
  return appendEvent({ ...pxc, parts }, { kind: "write", receipt });
}

export const setPart = writePart;

class NestedCalculationError extends Error {
  readonly pxc: PxC;
  readonly cause: unknown;

  constructor(pxc: PxC, cause: unknown) {
    super(cause instanceof Error ? cause.message : String(cause));
    this.name = "NestedCalculationError";
    this.pxc = pxc;
    this.cause = cause;
  }
}

function executeCalculation<I, O>(pxc: PxC, id: CalculationId, args: I): InvokeResult<O> {
  const calculation = pxc.calculations.get(id) as Calculation<I, O> | undefined;
  if (!calculation) throw new Error(`Calculation not registered: ${id}`);

  // The invocation event is placed before the calculation's actual traffic,
  // making nested calls and reads/writes observable in one total order.
  const sequence = pxc.telemetry.events.length;
  const started = appendEvent(pxc, {
    kind: "invocation",
    receipt: { id, sequence, status: "completed", args },
  });
  let current = started;
  const context: CalculationContext = {
    read<T>(address: PartAddress): T {
      try {
        const result = readPartInternal<T>(current, address);
        current = result.pxc;
        return result.value;
      } catch (error) {
        if (error instanceof MissingPartError) current = error.pxc;
        throw new NestedCalculationError(current, error);
      }
    },
    write<T>(address: PartAddress, value: T): void {
      current = writePart(current, address, value);
    },
    invoke<I2, O2>(nestedId: CalculationId | string, nestedArgs: I2): O2 {
      const childId = calculationId(String(nestedId));
      const child = executeCalculation<I2, O2>(current, childId, nestedArgs);
      current = child.pxc;
      if (child.error) throw new NestedCalculationError(current, child.error);
      return child.value as O2;
    },
  };

  try {
    const value = calculation.run(args, context);
    const invocation = {
      id,
      sequence,
      status: "completed" as const,
      args,
      result: value,
    };
    // Replace the provisional start receipt with the completed receipt while
    // preserving its event position and all intervening traffic.
    const invocations = current.telemetry.invocations.map((item) =>
      item.sequence === sequence ? invocation : item,
    );
    const events = current.telemetry.events.map((event) =>
      event.kind === "invocation" && event.receipt.sequence === sequence
        ? { kind: "invocation" as const, receipt: invocation }
        : event,
    );
    return { pxc: { ...current, telemetry: { ...current.telemetry, invocations, events } }, value, invocation };
  } catch (error) {
    const cause = error instanceof NestedCalculationError ? error.cause : error;
    current = error instanceof NestedCalculationError ? error.pxc : current;
    const invocation = {
      id,
      sequence,
      status: "failed" as const,
      args,
      error: cause,
    };
    const invocations = current.telemetry.invocations.map((item) =>
      item.sequence === sequence ? invocation : item,
    );
    const events = current.telemetry.events.map((event) =>
      event.kind === "invocation" && event.receipt.sequence === sequence
        ? { kind: "invocation" as const, receipt: invocation }
        : event,
    );
    return { pxc: { ...current, telemetry: { ...current.telemetry, invocations, events } }, invocation, error: cause };
  }
}

export function invokeCalculation<I, O>(pxc: PxC, id: CalculationId | string, args: I): InvokeResult<O> {
  return executeCalculation<I, O>(pxc, calculationId(String(id)), args);
}
