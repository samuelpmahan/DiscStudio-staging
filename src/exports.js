/**
 * The export queue's model: which jobs a one-tap intent means, and what the
 * queue's progress reads as in one sentence. Pure over its inputs -- app.js
 * runs the jobs through the same runtime.scene and files the same export.record
 * receipt for each, and nothing here touches the DOM or the board.
 */
const slug = text => String(text || '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 40);
const canvasLabel = orientation => orientation === 'portrait' ? 'vertical 1080 × 1920' : '1920 × 1080';

/**
 * `intent` is what the person tapped:
 *   current     this state, as it is on screen
 *   all-states  every state of the battle, in order
 *   vertical    every state of the battle on the 1080x1920 canvas
 *   each-disc   every disc in the battle, on its own, as a single card
 * `kind` is 'png' or 'svg'. Nothing is invented: a job names the state, the
 * disc and the canvas it will render, and the queue runs them in this order.
 */
export function planExports({ intent, kind = 'png', world, discId, mode = 'battle', orientation }) {
  const canvas = orientation ?? world.layout.orientation;
  const states = world.battle.states, current = states.find(s => s.id === world.battle.currentStateId) ?? states[0];
  const discName = key => { const disc = world.objects.Disc?.[key]; return disc?.nickname || world.objects.Mold?.[disc?.moldId]?.name || key; };
  const job = (fields, index) => ({
    id: `job-${index}-${fields.stateId}-${fields.discId ?? 'battle'}-${fields.orientation}-${kind}`,
    kind, status: 'queued', message: '', receiptId: null, ...fields,
    name: fields.mode === 'card' ? slug(discName(fields.discId)) || 'single-disc' : fields.stateId,
    label: `${fields.mode === 'card' ? discName(fields.discId) : fields.stateName} · ${canvasLabel(fields.orientation)} · ${kind.toUpperCase()}`
  });
  if (intent === 'each-disc') {
    const entries = world.battle.entries;
    if (!entries.length) throw new Error('The battle is empty: add a disc before exporting one card each.');
    return entries.map((entry, index) => job({ mode: 'card', discId: entry.discId, stateId: current.id, stateName: current.name, orientation: canvas }, index));
  }
  if (intent === 'all-states' || intent === 'vertical') {
    const canvasFor = intent === 'vertical' ? 'portrait' : canvas;
    return states.map((state, index) => job({ mode, discId, stateId: state.id, stateName: state.name, orientation: canvasFor }, index));
  }
  if (intent === 'current') return [job({ mode, discId, stateId: current.id, stateName: current.name, orientation: canvas }, 0)];
  throw new Error(`Unknown export intent '${intent}'.`);
}

/** Where the queue is, as a sentence a person reads without counting anything. */
export function queueProgress(jobs = []) {
  const by = status => jobs.filter(job => job.status === status);
  const done = by('done').length, failed = by('failed').length, running = by('running')[0] ?? null, queued = by('queued').length;
  const finished = done + failed;
  const sentence = !jobs.length ? 'Nothing queued.'
    : running ? `${finished} of ${jobs.length} done · exporting ${running.label}`
      : queued ? `${finished} of ${jobs.length} done · ${queued} waiting`
        : failed ? `${done} of ${jobs.length} exported · ${failed} failed, and each says why`
          : `All ${jobs.length} exported.`;
  return { total: jobs.length, done, failed, queued, running: running?.id ?? null, complete: !running && !queued, sentence };
}
