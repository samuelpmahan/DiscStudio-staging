import test from 'node:test';
import assert from 'node:assert/strict';
import { createSeed } from '../src/seed.js';
import { createStudioRuntime } from '../src/runtime.js';
const make = () => createStudioRuntime(createSeed());
const bag = (r, key = 'everyday') => r.world().objects.Bag[key];

test('a bag holds an order, and moving a disc in it changes nothing else', () => {
  const r = make(), before = [...bag(r).discIds], other = [...bag(r, 'luna-bag').discIds];
  r.dispatch({ type: 'bag.reorder', bagId: 'everyday', discId: before[0], toIndex: 3 });
  const after = bag(r).discIds;
  assert.equal(after[3], before[0]);
  assert.deepEqual([...after].sort(), [...before].sort(), 'reordering is not adding or removing');
  assert.deepEqual(bag(r, 'luna-bag').discIds, other);
  r.dispatch({ type: 'bag.reorder', bagId: 'everyday', discId: before[0], toIndex: -5 });
  assert.equal(bag(r).discIds[0], before[0], 'an index past the end is the end, not an error');
  r.undo.pop('px.studio.world');
  assert.equal(bag(r).discIds[3], before[0], 'each move is its own undo step');
  assert.throws(() => r.dispatch({ type: 'bag.reorder', bagId: 'everyday', discId: 'luna-mint', toIndex: 0 }), error => /not in this bag/.test(error.cause?.message ?? error.message), 'a disc that is not in the bag cannot be placed in it');
});

test('a bag is duplicated with the same discs in the same order, and the two are then their own', () => {
  const r = make();
  r.dispatch({ type: 'bag.duplicate', id: 'everyday', newId: 'sunday', name: 'Sunday singles' });
  assert.deepEqual(bag(r, 'sunday').discIds, bag(r).discIds);
  assert.equal(bag(r, 'sunday').name, 'Sunday singles');
  r.dispatch({ type: 'entity.set', entityType: 'Bag', id: 'sunday', path: 'name', value: 'Sunday' });
  r.dispatch({ type: 'bag.membership', bagId: 'sunday', discId: 'luna-mint', include: true });
  assert.equal(bag(r).name, 'Everyday bag');
  assert.ok(!bag(r).discIds.includes('luna-mint'), 'the copy is not a view of the original');
  r.dispatch({ type: 'bag.duplicate', id: 'everyday', newId: 'unnamed' });
  assert.equal(bag(r, 'unnamed').name, 'Everyday bag · copy');
});

test('one disc lives in as many bags as it likes, and nothing on the shelf side caps a bag', () => {
  const r = make();
  for (const key of ['luna-bag', 'zone-bag']) r.dispatch({ type: 'bag.membership', bagId: key, discId: 'buzzz-mint', include: true });
  const bags = () => Object.values(r.world().objects.Bag).filter(b => b.discIds.includes('buzzz-mint')).map(b => b.id);
  assert.deepEqual(bags().sort(), ['everyday', 'luna-bag', 'zone-bag']);
  r.dispatch({ type: 'bag.membership', bagId: 'luna-bag', discId: 'buzzz-mint', include: false });
  assert.deepEqual(bags().sort(), ['everyday', 'zone-bag'], 'out of one bag is not off the shelf');
  assert.ok(r.world().objects.Disc['buzzz-mint'], 'and never off the shelf');
  for (const disc of Object.keys(r.world().objects.Disc)) r.dispatch({ type: 'bag.membership', bagId: 'everyday', discId: disc, include: true });
  assert.equal(bag(r).discIds.length, Object.keys(r.world().objects.Disc).length, 'a bag holds whatever a person puts in it');
  const check = r.constraints('putterwarz');
  assert.ok(['pass', 'fail', 'pending', 'unconstrained'].includes(check.status), 'a cap is a competition constraint, and it still runs');
});
