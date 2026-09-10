// "Watch it think": pure playback scheduling. No DOM, no timers.
//
// Ticks are in series and the Calculations inside one Tick are in parallel
// (pyto/questions.md, `{?} TicksAsCircuits`), so the schedule adds Tick times
// and a parallel Tick's branches share one timestamp -- the Tick's latency.
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';

import { validate, fromPytoRecord } from '../adapters.js';
import {
  computeSchedule, scheduleFrame, isParallelTick, tickLatencyMs, runWorkMs, runCriticalPathMs
} from '../tick-viewer.js';

const HERE = dirname(fileURLToPath(import.meta.url));
const fixture = (name) => JSON.parse(readFileSync(resolve(HERE, '..', 'fixtures', name), 'utf8'));
const record = fromPytoRecord(fixture('pyto-grouped-ablation.json'));

const flatIds = (rec) => rec.ticks.flatMap((tick) => tick.invocations.map((invocation) => invocation.id));
const totalDuration = (rec) => rec.ticks.flatMap((t) => t.invocations).reduce((sum, i) => sum + (typeof i.duration_ms === 'number' ? i.duration_ms : 0), 0);

/**
 * The times the page must produce, written out here rather than imported from
 * the scheduler: a serial Tick's Calculations add one after another, a parallel
 * Tick's branches all land on the Tick's latency.
 */
function expectedTimes(rec, speed = 1) {
  const times = [];
  let cumulative = 0;
  for (const tick of rec.ticks) {
    if (isParallelTick(tick)) {
      cumulative += tickLatencyMs(tick);
      for (let i = 0; i < tick.invocations.length; i += 1) times.push(cumulative * speed);
    } else {
      for (const invocation of tick.invocations) {
        cumulative += invocation.duration_ms;
        times.push(cumulative * speed);
      }
    }
  }
  return times;
}

test('computeSchedule orders events exactly as the record does: Tick order, then invocation order', () => {
  const schedule = computeSchedule(record, 1);
  assert.equal(schedule.length, record.counters.invocations);
  assert.deepEqual(schedule.map((e) => e.invocation), flatIds(record));
  assert.deepEqual(schedule.map((e) => e.tick), record.ticks.flatMap((t) => t.invocations.map(() => t.index)));
});

test('at 1x, Ticks add and a parallel Tick\'s branches share one timestamp', () => {
  const schedule = computeSchedule(record, 1);
  const expected = expectedTimes(record, 1);
  schedule.forEach((event, i) => {
    assert.ok(Math.abs(event.at_ms - expected[i]) < 0.001, `event ${i}: ${event.at_ms} vs ${expected[i]}`);
    if (i > 0) assert.ok(event.at_ms >= schedule[i - 1].at_ms, 'never goes backwards');
  });
  // This record's Ticks are Prepare (2 branches), Fit (6), Score (6), Compare (1):
  // one timestamp each, not fifteen.
  const perTick = new Map();
  for (const event of schedule) {
    if (!perTick.has(event.tick)) perTick.set(event.tick, new Set());
    perTick.get(event.tick).add(event.at_ms);
  }
  assert.deepEqual([...perTick.values()].map((times) => times.size), [1, 1, 1, 1]);
});

test('the last event lands on the run critical path, not on its total work', () => {
  const work = runWorkMs(record);
  const critical = runCriticalPathMs(record);
  assert.ok(Math.abs(work - totalDuration(record)) < 0.001, 'work is every branch added up');
  assert.ok(critical < work, 'this record has parallel Ticks, so its critical path is shorter than its work');

  const at1x = computeSchedule(record, 1);
  const at100x = computeSchedule(record, 100);
  assert.ok(Math.abs(at1x[at1x.length - 1].at_ms - critical) < 0.001);
  // A 12 ms critical path at 100x slower takes about 1.2 s -- the ratio is exact, not just "about".
  assert.ok(Math.abs(at100x[at100x.length - 1].at_ms - critical * 100) < 0.1);
  assert.ok(Math.abs(at100x[at100x.length - 1].at_ms - at1x[at1x.length - 1].at_ms * 100) < 0.05);
});

test('speed scales every event proportionally, not just the last one', () => {
  const at1x = computeSchedule(record, 1);
  const at10x = computeSchedule(record, 10);
  for (let i = 0; i < at1x.length; i += 1) {
    assert.ok(Math.abs(at10x[i].at_ms - at1x[i].at_ms * 10) < 0.01, `event ${i}`);
  }
});

test('a run with no durations recorded plays at a fixed 400 ms a step, a parallel Tick being one step', () => {
  const undurated = structuredClone(record);
  for (const tick of undurated.ticks) for (const invocation of tick.invocations) invocation.duration_ms = null;
  validate(undurated);

  const steps = [];
  let step = 0;
  for (const tick of undurated.ticks) {
    if (isParallelTick(tick)) {
      step += 1;
      for (let i = 0; i < tick.invocations.length; i += 1) steps.push(step * 400);
    } else {
      for (let i = 0; i < tick.invocations.length; i += 1) steps.push((step += 1) * 400);
    }
  }
  for (const speed of [1, 10, 100]) {
    const schedule = computeSchedule(undurated, speed);
    assert.deepEqual(schedule.map((e) => e.at_ms), steps, `speed ${speed}`);
    assert.equal(schedule[schedule.length - 1].at_ms, step * 400);
  }
});

test('scheduleFrame reveals Ticks in order, a parallel Tick as one whole row', () => {
  const schedule = computeSchedule(record, 1);

  const nothing = scheduleFrame(record, schedule, -1);
  assert.deepEqual(nothing.record.ticks, []);
  assert.equal(nothing.now, null);

  // Prepare is a parallel Tick, so its first event is its whole row: both cards
  // appear together, never one and then the other.
  const afterFirst = scheduleFrame(record, schedule, schedule[0].at_ms);
  assert.equal(afterFirst.record.ticks.length, 1);
  assert.deepEqual(
    afterFirst.record.ticks[0].invocations.map((invocation) => invocation.id),
    record.ticks[0].invocations.map((invocation) => invocation.id)
  );
  assert.equal(afterFirst.now.tick, 0);
  validate(afterFirst.record);

  const everything = scheduleFrame(record, schedule, schedule[schedule.length - 1].at_ms);
  assert.deepEqual(everything.record.ticks, record.ticks);
  assert.equal(everything.now.invocation, schedule[schedule.length - 1].invocation);
  validate(everything.record);
  assert.equal(everything.record.counters.invocations, record.counters.invocations);
});

test('scheduleFrame keeps counters and the Part index honest for the partial record', () => {
  const schedule = computeSchedule(record, 1);
  // Inside Fit: Prepare's two branches plus Fit's six, which arrive together.
  const halfway = scheduleFrame(record, schedule, schedule[4].at_ms);
  const shownCount = halfway.record.ticks.reduce((sum, t) => sum + t.invocations.length, 0);
  assert.equal(shownCount, 8);
  assert.equal(halfway.record.counters.invocations, 8);
  assert.ok(Object.keys(halfway.record.parts).length <= Object.keys(record.parts).length);
});
