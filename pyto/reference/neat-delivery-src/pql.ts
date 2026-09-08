import {
  CalculationId,
  MissingPartError,
  PartAddress,
  PxC,
  calculationId,
  invokeCalculation,
  readPart,
  writePart,
} from "./pxc.js";

/** A reference is data, not a text/DSL expression. */
export interface PartReference<T = unknown> {
  readonly kind: "part";
  readonly address: PartAddress;
  readonly __value?: T;
}

export type ValueSpec<T = unknown> = T | PartReference<T>;

export function part<T = unknown>(address: PartAddress): PartReference<T> {
  return { kind: "part", address };
}

/**
 * Narrow structured adaptation of ChainSpot's declaration shape. It is not a
 * YAML parser or a new textual grammar; only the object form needed by neat.
 */
export interface CalculationStep {
  readonly call: CalculationId | string;
  readonly with?: Record<string, ValueSpec<unknown>>;
  readonly args?: ValueSpec<unknown>;
  readonly into?: PartAddress;
}

/** Programmatic constructor for the existing `call/with/args/into` shape. */
export function call(
  calculation: CalculationId | string,
  withOrArgs?: Record<string, ValueSpec<unknown>> | ValueSpec<unknown>,
  into?: PartAddress,
): CalculationStep {
  if (withOrArgs !== undefined && withOrArgs !== null && typeof withOrArgs === "object" &&
      !Array.isArray(withOrArgs) && !isPartReference(withOrArgs)) {
    return { call: calculation, with: withOrArgs as Record<string, ValueSpec<unknown>>, into };
  }
  return { call: calculation, args: withOrArgs, into };
}

export interface TickDefinition {
  readonly name: string;
  readonly Calculations: ReadonlyArray<CalculationStep>;
}

export function tick(name: string, calculations: ReadonlyArray<CalculationStep>): TickDefinition {
  if (!name.trim()) throw new Error("Tick identity cannot be empty");
  return { name, Calculations: [...calculations] };
}

export interface PqlProgram {
  readonly PrincipleComponentRender: string;
  readonly Ticks: ReadonlyArray<TickDefinition>;
}

export function program(PrincipleComponentRender: string, Ticks: ReadonlyArray<TickDefinition>): PqlProgram {
  if (!PrincipleComponentRender.trim()) throw new Error("PrincipleComponentRender identity cannot be empty");
  const ids = new Set<string>();
  Ticks.forEach((item) => {
    if (ids.has(item.name)) throw new Error(`Duplicate Tick identity: ${item.name}`);
    ids.add(item.name);
  });
  return { PrincipleComponentRender, Ticks: [...Ticks] };
}

export interface CalculationRun {
  readonly calculation: CalculationId;
  readonly value?: unknown;
  readonly into?: PartAddress;
  readonly status: "completed" | "failed";
}

export interface TickRunResult {
  readonly id: string;
  readonly outcome?: string;
  readonly status: "completed" | "failed";
  readonly calculations: ReadonlyArray<CalculationRun>;
  readonly materializations: ReadonlyArray<{ readonly address: PartAddress; readonly value: unknown }>;
  readonly error?: unknown;
}

export interface PqlRunResult {
  readonly programId: string;
  readonly status: "completed" | "failed";
  readonly ticks: ReadonlyArray<TickRunResult>;
  readonly pxc: PxC;
  /** Snapshot of traffic actually produced by this run. */
  readonly telemetry: PxC["telemetry"];
  readonly error?: unknown;
}

function isPartReference(value: unknown): value is PartReference<unknown> {
  return !!value && typeof value === "object" && (value as { kind?: unknown }).kind === "part" &&
    typeof (value as { address?: unknown }).address === "string";
}

function resolveValue(pxc: PxC, value: unknown, stringsAsParts = false): { pxc: PxC; value: unknown } {
  if (isPartReference(value)) return readPart(pxc, value.address);
  // In ChainSpot's `with` form, values name Parts directly (for example
  // `px.neat.items`). Positional `args` retain ordinary literal strings.
  if (stringsAsParts && typeof value === "string") return readPart(pxc, value);
  if (Array.isArray(value)) {
    let current = pxc;
    const result = value.map((item) => {
      const resolved = resolveValue(current, item, stringsAsParts);
      current = resolved.pxc;
      return resolved.value;
    });
    return { pxc: current, value: result };
  }
  if (value && typeof value === "object") {
    let current = pxc;
    const result: Record<string, unknown> = {};
    Object.keys(value as Record<string, unknown>).forEach((key) => {
      const resolved = resolveValue(current, (value as Record<string, unknown>)[key], stringsAsParts);
      current = resolved.pxc;
      result[key] = resolved.value;
    });
    return { pxc: current, value: result };
  }
  return { pxc, value };
}

function combinedInput(
  pxc: PxC,
  step: CalculationStep,
): { pxc: PxC; value: unknown } {
  if (step.with === undefined) return resolveValue(pxc, step.args, false);
  const bound = resolveValue(pxc, step.with, true);
  if (step.args === undefined) return bound;
  if (!step.args || typeof step.args !== "object" || Array.isArray(step.args)) {
    throw new Error(`Calculation ${step.call}: args must be a mapping when with is present`);
  }
  const literals = step.args as Record<string, unknown>;
  for (const name of Object.keys(literals)) {
    if (Object.hasOwn(bound.value as object, name)) {
      throw new Error(`Calculation ${step.call}: '${name}' appears in both with and args`);
    }
  }
  return { pxc: bound.pxc, value: { ...(bound.value as Record<string, unknown>), ...literals } };
}

export function runPql(initial: PxC, query: PqlProgram): PqlRunResult {
  let current = initial;
  const results: TickRunResult[] = [];
  for (const definition of query.Ticks) {
    const calculations: CalculationRun[] = [];
    const materializations: { address: PartAddress; value: unknown }[] = [];
    let tickError: unknown;
    for (const step of definition.Calculations) {
      try {
        const resolved = combinedInput(current, step);
        current = resolved.pxc;
        const result = invokeCalculation(current, calculationId(String(step.call)), resolved.value);
        current = result.pxc;
        calculations.push({
          calculation: result.invocation.id,
          value: result.value,
          into: step.into,
          status: result.invocation.status,
        });
        if (result.error) {
          tickError = result.error;
          break;
        }
        if (step.into) {
          current = writePart(current, step.into, result.value);
          materializations.push({ address: step.into, value: result.value });
        }
      } catch (error) {
        if (error instanceof MissingPartError) current = error.pxc;
        tickError = error;
        break;
      }
    }
    results.push({
      id: definition.name,
      status: tickError ? "failed" : "completed",
      calculations,
      materializations,
      ...(tickError ? { error: tickError } : {}),
    });
    if (tickError) {
      return {
        programId: query.PrincipleComponentRender,
        status: "failed",
        ticks: results,
        pxc: current,
        telemetry: current.telemetry,
        error: tickError,
      };
    }
  }
  return {
    programId: query.PrincipleComponentRender,
    status: "completed",
    ticks: results,
    pxc: current,
    telemetry: current.telemetry,
  };
}

export const composePql = program;
export const executePql = runPql;
export const defineProgram = program;
export const defineTick = tick;
export const partRef = part;
export const invoke = call;
