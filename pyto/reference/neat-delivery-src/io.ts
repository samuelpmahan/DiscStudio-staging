import { open, readdir, readFile, rename, unlink, writeFile } from "node:fs/promises";
import { basename, join } from "node:path";
import { BoardFacts, WorkItem, WorkItemUpdatePatch, updateWorkItem, validateWorkItem, workItemRevision } from "./work-items.js";

export interface NeatSnapshot {
  root: string;
  items: WorkItem[];
  facts: BoardFacts;
}

function itemDirectory(root: string): string { return join(root, ".neat", "items"); }
function factsPath(root: string): string { return join(root, ".neat", "facts.json"); }
function itemPath(root: string, id: string): string {
  if (!/^[A-Za-z0-9._-]+$/.test(id)) throw new Error(`Unsafe work-item identity '${id}'.`);
  return join(itemDirectory(root), `${id}.json`);
}

export async function readSnapshot(root: string): Promise<NeatSnapshot> {
  const directory = itemDirectory(root);
  const names = (await readdir(directory)).filter((name) => name.endsWith(".json")).sort();
  const items = await Promise.all(names.map(async (name) => JSON.parse(await readFile(join(directory, name), "utf8")) as WorkItem));
  const facts = await readFile(factsPath(root), "utf8")
    .then((text) => JSON.parse(text) as BoardFacts)
    .catch((error: unknown) => {
      if ((error as NodeJS.ErrnoException).code === "ENOENT") return {};
      throw error;
    });
  return { root, items, facts };
}

export function snapshotProblems(snapshot: NeatSnapshot): string[] {
  const ids = new Set<string>();
  return snapshot.items.flatMap((item) => {
    const errors = validateWorkItem(item);
    if (ids.has(item.id)) errors.push(`${item.id}: duplicate item id`);
    ids.add(item.id);
    return errors;
  });
}

/**
 * A short exclusive sibling lock makes the content-fingerprint comparison a
 * real guarded update. It intentionally never removes a stale lock.
 */
export async function guardedUpdate(
  root: string,
  id: string,
  expectedFingerprint: string,
  patch: WorkItemUpdatePatch,
): Promise<{ item: WorkItem; previousFingerprint: string }> {
  const path = itemPath(root, id);
  const lockPath = `${path}.lock`;
  let lock;
  try {
    lock = await open(lockPath, "wx");
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code === "EEXIST") throw new Error(`Item '${id}' is locked; inspect ${basename(lockPath)} before retrying.`);
    throw error;
  }
  try {
    const text = await readFile(path, "utf8");
    const current = JSON.parse(text) as WorkItem;
    const result = updateWorkItem([current], id, expectedFingerprint, patch);
    if (!result.ok) {
      if (result.reason === "revision_mismatch") throw new Error(`Expected ${expectedFingerprint}; current item fingerprint is ${result.currentRevision}.`);
      throw new Error(result.reason === "not_found" ? `Item '${id}' was not found.` : result.message);
    }
    const problems = validateWorkItem(result.item);
    if (problems.length) throw new Error(`Refusing invalid update: ${problems.join("; ")}`);
    const temporary = `${path}.${process.pid}.${Date.now()}.tmp`;
    await writeFile(temporary, `${JSON.stringify(result.item, null, 2)}\n`, "utf8");
    await rename(temporary, path);
    return { item: result.item, previousFingerprint: workItemRevision(current) };
  } finally {
    await lock?.close();
    await unlink(lockPath).catch((error: unknown) => {
      if ((error as NodeJS.ErrnoException).code !== "ENOENT") throw error;
    });
  }
}
