import { createHash } from "node:crypto";
import { execFile } from "node:child_process";
import { createReadStream } from "node:fs";
import { chmod, copyFile, lstat, mkdir, open, readFile, readdir, rename, rm, stat, unlink, writeFile } from "node:fs/promises";
import { dirname, isAbsolute, join, relative, resolve, sep } from "node:path";
import { promisify } from "node:util";

const runFile = promisify(execFile);
const SAFE_ID = /^[A-Za-z0-9][A-Za-z0-9._-]*$/;

export type DeliveryStage = "frozen" | "offered" | "claimed" | "partial" | "consumed" | "rejected";

export interface DeliverySpec {
  schemaVersion: 1;
  id: string;
  repositoryId: string;
  producer: string;
  source: { repository: string; payload: string; baseCommit: string; exclude?: string[] };
  archiveRoot: string;
  mailbox: {
    name: string;
    consumer: string;
    obligations: Array<{ id: string; text: string }>;
  };
  evidence?: string[];
}

export interface DeliveryEntry {
  path: string;
  kind: "directory" | "file";
  mode?: number;
  size?: number;
  sha256?: string;
}

export interface DeliveryManifest {
  schemaVersion: 1;
  id: string;
  repositoryId: string;
  createdAt: string;
  producer: string;
  source: {
    repository: string;
    payload: string;
    baseCommit: string;
    headCommit: string;
    worktreeStatusSha256: string;
    exclude: string[];
  };
  archivePath: string;
  mailbox: DeliverySpec["mailbox"];
  evidence: string[];
  entries: DeliveryEntry[];
  payloadDigest: string;
  deliveryDigest: string;
}

export interface DeliveryEvent {
  stage: DeliveryStage;
  actor: string;
  at: string;
  note?: string;
  receipt?: { id: string; sha256: string };
  remainingObligations?: string[];
}

export interface DeliveryState {
  schemaVersion: 1;
  id: string;
  deliveryDigest: string;
  stage: DeliveryStage;
  satisfiedObligations: string[];
  history: DeliveryEvent[];
}

export interface ConsumerReceipt {
  schemaVersion: 1;
  id: string;
  deliveryId: string;
  deliveryDigest: string;
  consumer: string;
  destination: string;
  obligations: Array<{ id: string; status: "passed" | "failed" | "deferred" | "observed"; evidence?: string }>;
  evidence?: string[];
}

function json(value: unknown): string { return `${JSON.stringify(value, null, 2)}\n`; }
function hashText(value: string | Buffer): string { return createHash("sha256").update(value).digest("hex"); }
function nativePath(root: string, path: string): string { return join(root, ...path.split("/")); }
function displayPath(path: string): string { return path.split(sep).join("/"); }
function inside(parent: string, child: string): boolean {
  const path = relative(parent, child);
  return path === "" || (!path.startsWith(`..${sep}`) && path !== ".." && !isAbsolute(path));
}
function assertId(value: string, label: string): void {
  if (!SAFE_ID.test(value)) throw new Error(`${label} must contain only letters, numbers, dot, underscore, or dash.`);
}
function assertRelative(value: string, label: string): string {
  const normalized = displayPath(value).replace(/^\.\//, "").replace(/\/$/, "");
  if (!normalized || isAbsolute(value) || normalized === ".." || normalized.startsWith("../") || normalized.includes("/../")) {
    throw new Error(`${label} must be a safe relative path.`);
  }
  return normalized;
}

async function fileHash(path: string): Promise<string> {
  const hash = createHash("sha256");
  for await (const chunk of createReadStream(path)) hash.update(chunk);
  return hash.digest("hex");
}

function excluded(path: string, exclusions: readonly string[]): boolean {
  return exclusions.some((entry) => path === entry || path.startsWith(`${entry}/`));
}

async function inventory(root: string, exclusions: readonly string[], directory = "", includeMode = false): Promise<DeliveryEntry[]> {
  const entries = await readdir(nativePath(root, directory), { withFileTypes: true });
  entries.sort((a, b) => a.name < b.name ? -1 : a.name > b.name ? 1 : 0);
  const found: DeliveryEntry[] = [];
  for (const entry of entries) {
    const path = directory ? `${directory}/${entry.name}` : entry.name;
    if (excluded(path, exclusions)) continue;
    const absolute = nativePath(root, path);
    const details = await lstat(absolute);
    if (details.isSymbolicLink()) throw new Error(`Delivery payload cannot contain symlink '${path}'.`);
    if (details.isDirectory()) {
      found.push({ path, kind: "directory", ...(includeMode ? { mode: details.mode & 0o777 } : {}) }, ...await inventory(root, exclusions, path, includeMode));
    } else if (details.isFile()) {
      found.push({ path, kind: "file", ...(includeMode ? { mode: details.mode & 0o777 } : {}), size: details.size, sha256: await fileHash(absolute) });
    } else {
      throw new Error(`Delivery payload contains unsupported entry '${path}'.`);
    }
  }
  return found;
}

async function copyPayload(source: string, destination: string, entries: readonly DeliveryEntry[]): Promise<void> {
  await mkdir(destination, { recursive: true });
  for (const entry of entries) {
    const target = nativePath(destination, entry.path);
    if (entry.kind === "directory") await mkdir(target, { recursive: true });
    else {
      await mkdir(dirname(target), { recursive: true });
      await copyFile(nativePath(source, entry.path), target);
      if (entry.mode !== undefined) await chmod(target, entry.mode);
    }
  }
  for (const entry of [...entries].reverse()) {
    if (entry.kind === "directory" && entry.mode !== undefined) await chmod(nativePath(destination, entry.path), entry.mode);
  }
}

function deliveryDirectory(root: string, id: string): string {
  assertId(id, "Delivery id");
  return join(resolve(root), ".neat", "deliveries", id);
}

async function readManifestAt(directory: string): Promise<DeliveryManifest> {
  return JSON.parse(await readFile(join(directory, "manifest.json"), "utf8")) as DeliveryManifest;
}

async function readStateAt(directory: string): Promise<DeliveryState> {
  return JSON.parse(await readFile(join(directory, "state.json"), "utf8")) as DeliveryState;
}

function manifestIdentity(manifest: Omit<DeliveryManifest, "deliveryDigest">): unknown {
  return {
    schemaVersion: manifest.schemaVersion,
    id: manifest.id,
    repositoryId: manifest.repositoryId,
    producer: manifest.producer,
    source: manifest.source,
    mailbox: manifest.mailbox,
    evidence: manifest.evidence,
    entries: manifest.entries,
    payloadDigest: manifest.payloadDigest,
  };
}

async function verifyAt(directory: string): Promise<{ manifest: DeliveryManifest; state: DeliveryState }> {
  const manifest = await readManifestAt(directory);
  if (manifest.schemaVersion !== 1) throw new Error(`Delivery manifest at '${directory}' has an unsupported schemaVersion.`);
  const expectedDigest = hashText(JSON.stringify(manifestIdentity(manifest)));
  if (manifest.deliveryDigest !== expectedDigest) throw new Error(`Delivery '${manifest.id}' manifest digest does not match.`);
  const comparesMode = manifest.entries.some((entry) => entry.mode !== undefined);
  const actualEntries = await inventory(join(directory, "payload"), [], "", comparesMode);
  if (JSON.stringify(actualEntries) !== JSON.stringify(manifest.entries)) throw new Error(`Delivery '${manifest.id}' payload inventory does not match.`);
  const payloadDigest = hashText(JSON.stringify(actualEntries));
  if (payloadDigest !== manifest.payloadDigest) throw new Error(`Delivery '${manifest.id}' payload digest does not match.`);
  const state = await readStateAt(directory);
  if (state.id !== manifest.id || state.deliveryDigest !== manifest.deliveryDigest) throw new Error(`Delivery '${manifest.id}' state targets another candidate.`);
  if (state.schemaVersion !== 1 || state.history.at(-1)?.stage !== state.stage) throw new Error(`Delivery '${manifest.id}' state history is inconsistent.`);
  return { manifest, state };
}

async function git(repository: string, args: string[]): Promise<string> {
  const result = await runFile("git", ["-C", repository, ...args], { encoding: "utf8", maxBuffer: 10 * 1024 * 1024 });
  return result.stdout.trim();
}

export async function freezeDelivery(root: string, spec: DeliverySpec): Promise<DeliveryManifest> {
  if (spec.schemaVersion !== 1) throw new Error("Unsupported delivery spec schemaVersion.");
  assertId(spec.id, "Delivery id");
  assertId(spec.repositoryId, "Repository id");
  if (!spec.producer || !spec.mailbox?.name || !spec.mailbox.consumer) throw new Error("Delivery producer and mailbox identity are required.");
  if (!isAbsolute(spec.archiveRoot)) throw new Error("archiveRoot must be absolute.");
  if (!/^[0-9a-fA-F]{7,64}$/.test(spec.source.baseCommit)) throw new Error("baseCommit must be a Git commit id.");
  const obligationIds = new Set<string>();
  for (const obligation of spec.mailbox.obligations) {
    assertId(obligation.id, "Obligation id");
    if (!obligation.text || obligationIds.has(obligation.id)) throw new Error(`Invalid or duplicate obligation '${obligation.id}'.`);
    obligationIds.add(obligation.id);
  }

  const repository = resolve(root, spec.source.repository);
  const repositoryTop = resolve(await git(repository, ["rev-parse", "--show-toplevel"]));
  const payload = resolve(repository, spec.source.payload);
  if (!inside(repositoryTop, payload)) throw new Error("Delivery payload must be inside the source repository.");
  if (!(await stat(payload)).isDirectory()) throw new Error("Delivery payload must be a directory.");
  const baseCommit = await git(repositoryTop, ["rev-parse", "--verify", `${spec.source.baseCommit}^{commit}`]);
  const headCommit = await git(repositoryTop, ["rev-parse", "HEAD"]);
  const status = await runFile("git", ["-C", repositoryTop, "status", "--porcelain=v1", "-z", "--untracked-files=all"], { encoding: "utf8", maxBuffer: 10 * 1024 * 1024 });

  const exclusions = new Set([".git", ...(spec.source.exclude ?? []).map((path) => assertRelative(path, "Excluded path"))]);
  const localParent = join(resolve(root), ".neat", "deliveries");
  if (inside(payload, localParent)) exclusions.add(displayPath(relative(payload, localParent)));
  const archiveRoot = resolve(spec.archiveRoot);
  if (inside(repositoryTop, archiveRoot)) throw new Error("archiveRoot must be outside the source repository.");
  if (inside(payload, archiveRoot)) exclusions.add(displayPath(relative(payload, archiveRoot)));
  const exclude = [...exclusions].filter((path) => path && path !== ".").sort();
  const entries = await inventory(payload, exclude);
  const payloadDigest = hashText(JSON.stringify(entries));
  const archivePath = join(archiveRoot, spec.repositoryId, spec.id);
  const withoutDigest: Omit<DeliveryManifest, "deliveryDigest"> = {
    schemaVersion: 1,
    id: spec.id,
    repositoryId: spec.repositoryId,
    createdAt: new Date().toISOString(),
    producer: spec.producer,
    source: {
      repository: repositoryTop,
      payload,
      baseCommit,
      headCommit,
      worktreeStatusSha256: hashText(status.stdout),
      exclude,
    },
    archivePath,
    mailbox: spec.mailbox,
    evidence: [...(spec.evidence ?? [])],
    entries,
    payloadDigest,
  };
  const manifest: DeliveryManifest = { ...withoutDigest, deliveryDigest: hashText(JSON.stringify(manifestIdentity(withoutDigest))) };
  const initialState: DeliveryState = {
    schemaVersion: 1,
    id: spec.id,
    deliveryDigest: manifest.deliveryDigest,
    stage: "frozen",
    satisfiedObligations: [],
    history: [{ stage: "frozen", actor: spec.producer, at: manifest.createdAt }],
  };

  const localPath = deliveryDirectory(root, spec.id);
  // Archive first: if the local projection fails, the complete candidate is still recoverable.
  for (const finalPath of [archivePath, localPath]) {
    try {
      await lstat(finalPath);
      const existing = await verifyAt(finalPath);
      if (existing.manifest.deliveryDigest === manifest.deliveryDigest) continue;
      throw new Error(`Delivery path already contains another candidate: ${finalPath}`);
    } catch (error) {
      if ((error as NodeJS.ErrnoException).code !== "ENOENT") throw error;
    }
    const temporary = `${finalPath}.tmp-${process.pid}-${Date.now()}`;
    await mkdir(dirname(finalPath), { recursive: true });
    try {
      await copyPayload(payload, join(temporary, "payload"), entries);
      await writeFile(join(temporary, "manifest.json"), json(manifest), { encoding: "utf8", flag: "wx" });
      await writeFile(join(temporary, "state.json"), json(initialState), { encoding: "utf8", flag: "wx" });
      await verifyAt(temporary);
      await rename(temporary, finalPath);
    } catch (error) {
      await rm(temporary, { recursive: true, force: true });
      throw error;
    }
  }
  return manifest;
}

export async function verifyDelivery(root: string, id: string, archive = false): Promise<{ manifest: DeliveryManifest; state: DeliveryState }> {
  const local = deliveryDirectory(root, id);
  const manifest = await readManifestAt(local);
  return verifyAt(archive ? manifest.archivePath : local);
}

const ALLOWED: Record<DeliveryStage, DeliveryStage[]> = {
  frozen: ["offered"],
  offered: ["claimed", "rejected"],
  claimed: ["partial", "consumed", "rejected"],
  partial: ["partial", "consumed", "rejected"],
  consumed: [],
  rejected: ["offered"],
};

async function withDeliveryLock<T>(root: string, id: string, operation: (directory: string) => Promise<T>): Promise<T> {
  const directory = deliveryDirectory(root, id);
  const lockPath = join(directory, "state.lock");
  let lock;
  try {
    lock = await open(lockPath, "wx");
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code === "EEXIST") throw new Error(`Delivery '${id}' is locked; inspect state.lock before retrying.`);
    throw error;
  }
  try { return await operation(directory); }
  finally {
    await lock?.close();
    await unlink(lockPath).catch((error: unknown) => {
      if ((error as NodeJS.ErrnoException).code !== "ENOENT") throw error;
    });
  }
}

async function writeState(directory: string, state: DeliveryState): Promise<void> {
  const temporary = join(directory, `state.${process.pid}.${Date.now()}.tmp`);
  await writeFile(temporary, json(state), "utf8");
  await rename(temporary, join(directory, "state.json"));
}

export async function stageDelivery(root: string, id: string, stage: Exclude<DeliveryStage, "consumed">, actor: string, note?: string): Promise<DeliveryState> {
  if (!actor) throw new Error("Stage actor is required.");
  return withDeliveryLock(root, id, async (directory) => {
    const { manifest, state } = await verifyAt(directory);
    if (state.stage === stage) return state;
    if (!ALLOWED[state.stage].includes(stage)) throw new Error(`Cannot move delivery '${id}' from ${state.stage} to ${stage}.`);
    const next: DeliveryState = {
      ...state,
      stage,
      history: [...state.history, { stage, actor, at: new Date().toISOString(), ...(note ? { note } : {}) }],
    };
    if (next.deliveryDigest !== manifest.deliveryDigest) throw new Error(`Delivery '${id}' state targets another candidate.`);
    await writeState(manifest.archivePath, next);
    await writeState(directory, next);
    return next;
  });
}

async function writeImmutable(path: string, contents: string): Promise<void> {
  await mkdir(dirname(path), { recursive: true });
  try { await writeFile(path, contents, { encoding: "utf8", flag: "wx" }); }
  catch (error) {
    if ((error as NodeJS.ErrnoException).code !== "EEXIST") throw error;
    if (await readFile(path, "utf8") !== contents) throw new Error(`Immutable record already exists with different content: ${path}`);
  }
}

export async function consumeDelivery(root: string, id: string, receipt: ConsumerReceipt): Promise<DeliveryState> {
  assertId(receipt.id, "Receipt id");
  return withDeliveryLock(root, id, async (directory) => {
    const { manifest, state } = await verifyAt(directory);
    if (receipt.schemaVersion !== 1 || receipt.deliveryId !== id || receipt.deliveryDigest !== manifest.deliveryDigest) {
      throw new Error(`Receipt '${receipt.id}' does not target this exact delivery candidate.`);
    }
    if (receipt.consumer !== manifest.mailbox.consumer) throw new Error(`Receipt consumer does not match mailbox '${manifest.mailbox.name}'.`);
    const obligationIds = new Set(manifest.mailbox.obligations.map((obligation) => obligation.id));
    const results = new Map(receipt.obligations.map((result) => [result.id, result]));
    const contents = json(receipt);
    const receiptHash = hashText(contents);
    const localReceipt = join(directory, "receipts", `${receipt.id}.json`);
    const archiveReceipt = join(manifest.archivePath, "receipts", `${receipt.id}.json`);
    const prior = state.history.find((event) => event.receipt?.id === receipt.id)?.receipt;
    if (prior) {
      if (prior.sha256 === receiptHash) {
        await writeImmutable(archiveReceipt, contents);
        await writeImmutable(localReceipt, contents);
        return state;
      }
      throw new Error(`Receipt '${receipt.id}' was already recorded with different content.`);
    }
    if (state.stage === "consumed") throw new Error(`Delivery '${id}' was already consumed by another receipt.`);
    if (state.stage !== "claimed" && state.stage !== "partial") throw new Error(`Delivery '${id}' must be claimed before consumption.`);
    await writeImmutable(archiveReceipt, contents);
    await writeImmutable(localReceipt, contents);
    const satisfied = new Set(state.satisfiedObligations);
    for (const result of results.values()) {
      if (obligationIds.has(result.id) && result.status === "passed") satisfied.add(result.id);
    }
    const remaining = manifest.mailbox.obligations.map((obligation) => obligation.id).filter((obligation) => !satisfied.has(obligation));
    const nextStage: DeliveryStage = remaining.length === 0 ? "consumed" : "partial";
    const next: DeliveryState = {
      ...state,
      stage: nextStage,
      satisfiedObligations: [...satisfied].sort(),
      history: [...state.history, {
        stage: nextStage,
        actor: receipt.consumer,
        at: new Date().toISOString(),
        receipt: { id: receipt.id, sha256: receiptHash },
        ...(remaining.length ? { remainingObligations: remaining } : {}),
      }],
    };
    await writeState(manifest.archivePath, next);
    await writeState(directory, next);
    return next;
  });
}

export async function restoreDelivery(root: string, id: string, destination: string): Promise<DeliveryManifest> {
  const { manifest } = await verifyDelivery(root, id, true);
  const target = resolve(destination);
  try {
    await lstat(target);
    throw new Error(`Restore destination already exists: ${target}`);
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code !== "ENOENT") throw error;
  }
  const temporary = `${target}.tmp-${process.pid}-${Date.now()}`;
  try {
    await copyPayload(join(manifest.archivePath, "payload"), temporary, manifest.entries);
    const restored = await inventory(temporary, []);
    if (JSON.stringify(restored) !== JSON.stringify(manifest.entries)) throw new Error("Restored payload does not match the delivery manifest.");
    await mkdir(dirname(target), { recursive: true });
    await rename(temporary, target);
    return manifest;
  } catch (error) {
    await rm(temporary, { recursive: true, force: true });
    throw error;
  }
}
