/**
 * UndoStack ({?} UndoStack): a generic Part `px.undo.<scope>` holding the prior
 * values of addresses written through Calculations, so undo is one more
 * invocation on the record and not a second state store. Every function here is
 * pure over the values the store hands it; nothing reads or writes the board.
 */
const DEPTH = 32;

/** An empty stack for a scope. Seeded once so a pop before any push is still a Calculation. */
export const emptyStack = (scope) => ({ scope, depth: 0, entries: [] });

const stackOf = (stack, scope) => stack && Array.isArray(stack.entries) ? stack : emptyStack(scope);

/** push: record the current value of `address` and the depth it is stored at. */
export function undoPush({ stack, value, address, scope = 'studio' } = {}) {
  if (typeof address !== 'string' || !address) throw new Error('fn.undo.push needs the address it is recording.');
  const current = stackOf(stack, scope);
  const entries = [...current.entries, { address, value, depth: current.entries.length + 1 }].slice(-DEPTH);
  return { scope: current.scope, depth: entries.length, entries: entries.map((entry, index) => ({ ...entry, depth: index + 1 })) };
}

/** pop: the value to write back at `address`. An empty stack restores what is already there. */
export function undoPop({ stack, current, address, scope = 'studio' } = {}) {
  if (typeof address !== 'string' || !address) throw new Error('fn.undo.pop needs the address it is restoring.');
  const top = stackOf(stack, scope).entries.at(-1);
  return top && top.address === address ? top.value : current;
}

/** settle: the stack after the value pop restored has been taken off it. */
export function undoSettle({ stack, address, scope = 'studio' } = {}) {
  if (typeof address !== 'string' || !address) throw new Error('fn.undo.settle needs the address pop restored.');
  const current = stackOf(stack, scope), top = current.entries.at(-1);
  const entries = top && top.address === address ? current.entries.slice(0, -1) : current.entries;
  return { scope: current.scope, depth: entries.length, entries };
}
