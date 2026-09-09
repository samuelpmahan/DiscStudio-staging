// "Watch it think": pure playback scheduling. No DOM, no timers.
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';

import { validate, fromPytoRecord } from '../adapters.js';
import { computeSchedule, scheduleFrame } from '../tick-viewer.js';

const HERE = dirname(fileURLToPath(import.meta.url));
const fixture = (name) => JSON.parse(readFileSync(resolve(HERE, '..', 'fixtures', name), 'utf8'));
const record = fromPytoRecord(fixture('pyto-grouped-ablation.json'));

const flatIds = (rec) => rec.ticks.flatMap((tick) => tick.invocations.map((invocation) => invocation.id));
const totalDuration = (rec) => rec.ticks.flatMap((t) => t.invocations).reduce((sum, i) => sum + (typeof i.duration_ms === 'number' ? i.duration_ms : 0), 0);

test('computeSchedule orders events exactly as the record does: Tick order, then invocation order', () => {
  const schedule = computeSchedule(record, 1);
  assert.equal(schedule.length, record.counters.invocations);
  assert.deepEqual(schedule.map((e) => e.invocation), flatIds(record));
  assert.deepEqual(schedule.map((e) => e.tick), record.ticks.flatMap((t) => t.invocations.map(() => t.index)));
});

test('at 1x, at_ms is the cumulative sum of recorded durations, strictly increasing', () => {
  const schedule = computeSchedule(record, 1);
  let running = 0;
  for (let i = 0; i < schedule.length; i += 1) {
    running += record.ticks.flatMap((t) => t.invocations)[i].duration_ms;
    assert.ok(Math.abs(schedule[i].at_ms - running) < 0.001, `event ${i}: ${schedule[i].at_ms} vs ${running}`);
    if (i > 0) assert.ok(schedule[i].at_ms >= schedule[i - 1].at_ms, 'never goes backwards');
  }
});

test('the last event lands on the run total, at 1x and scaled by speed', () => {
  const total = totalDuration(record);
  const at1x = computeSchedule(record, 1);
  const at100x = computeSchedule(record, 100);
  assert.ok(Math.abs(at1x[at1x.length - 1].at_ms - total) < 0.001);
  // A 26 ms run at 100x slower takes about 2.6 s -- the ratio is exact, not just "about".
  assert.ok(Math.abs(at100x[at100x.length - 1].at_ms - total * 100) < 0.1);
  assert.ok(Math.abs(at100x[at100x.length - 1].at_ms - at1x[at1x.length - 1].at_ms * 100) < 0.05);
});

test('speed scales every event proportionally, not just the last one', () => {
  const at1x = computeSchedule(record, 1);
  const at10x = computeSchedule(record, 10);
  for (let i = 0; i < at1x.length; i += 1) {
    assert.ok(Math.abs(at10x[i].at_ms - at1x[i].at_ms * 10) < 0.01, `event ${i}`);
  }
});

test('a run with no durations recorded plays at a fixed 400 ms per Calculation, unaffected by speed', () => {
  const undurated = structuredClone(record);
  for (const tick of undurated.ticks) for (const invocation of tick.invocations) invocation.duration_ms = null;
  validate(undurated);

  for (const speed of [1, 10, 100]) {
    const schedule = computeSchedule(undurated, speed);
    assert.deepEqual(schedule.map((e) => e.at_ms), schedule.map((_, i) => (i + 1) * 400));
    assert.equal(schedule[schedule.length - 1].at_ms, schedule.length * 400);
  }
});

test('scheduleFrame reveals Ticks and Calculations in order and never a partial Tick out of sequence', () => {
  const schedule = computeSchedule(record, 1);

  const nothing = scheduleFrame(record, schedule, -1);
  assert.deepEqual(nothing.record.ticks, []);
  assert.equal(nothing.now, null);

  const afterFirst = scheduleFrame(record, schedule, schedule[0].at_ms);
  assert.equal(afterFirst.record.ticks.length, 1);
  assert.equal(afterFirst.record.ticks[0].invocations.length, 1);
  assert.equal(afterFirst.record.ticks[0].invocations[0].id, schedule[0].invocation);
  assert.equal(afterFirst.now.invocation, schedule[0].invocation);
  validate(afterFirst.record);

  const everything = scheduleFrame(record, schedule, schedule[schedule.length - 1].at_ms);
  assert.deepEqual(everything.record.ticks, record.ticks);
  assert.equal(everything.now.invocation, schedule[schedule.length - 1].invocation);
  validate(everything.record);
  assert.equal(everything.record.counters.invocations, record.counters.invocations);
});

test('scheduleFrame keeps counters and the Part index honest for the partial record', () => {
  const schedule = computeSchedule(record, 1);
  // Halfway through Fit: Prepare (2) plus the first three of Fit's six.
  const halfway = scheduleFrame(record, schedule, schedule[4].at_ms);
  const shownCount = halfway.record.ticks.reduce((sum, t) => sum + t.invocations.length, 0);
  assert.equal(shownCount, 5);
  assert.equal(halfway.record.counters.invocations, 5);
  assert.ok(Object.keys(halfway.record.parts).length <= Object.keys(record.parts).length);
});
