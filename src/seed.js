import { schema, clone } from './domain.js';
import { defaultPresets } from './presentation.js';
import { defaultCards } from './cards.js';
export function createSeed() {
  const objects = Object.fromEntries(Object.keys(schema).map(type => [type, {}]));
  const add = (type, value) => (objects[type][value.id] = { ...value, type });
  add('Manufacturer', { id: 'discraft', name: 'Discraft', website: '' });
  add('Manufacturer', { id: 'innova', name: 'Innova', website: '' });
  const molds = [
    ['buzzz', 'Buzzz', 'discraft', 'Midrange', 5, 4, -1, 1], ['zone', 'Zone', 'discraft', 'Putt & approach', 4, 3, 0, 3],
    ['destroyer', 'Destroyer', 'innova', 'Distance driver', 12, 5, -1, 3], ['leopard3', 'Leopard3', 'innova', 'Fairway driver', 7, 5, -2, 1],
    ['mako3', 'Mako3', 'innova', 'Midrange', 5, 5, 0, 0], ['teebird3', 'TeeBird3', 'innova', 'Fairway driver', 8, 4, 0, 2],
    ['luna', 'Luna', 'discraft', 'Putter', 3, 3, 0, 3]
  ];
  for (const [id, name, manufacturerId, category, speed, glide, turn, fade] of molds) add('Mold', { id, name, manufacturerId, category, flight: { speed, glide, turn, fade } });
  const discs = [
    ['buzzz-mint', 'buzzz', 'Mint practice disc', 'ESP', 177, 'Mint', 150], ['zone-peach', 'zone', 'Peach approach disc', 'Z', 173, 'Peach', 22],
    ['destroyer-lilac', 'destroyer', 'Lilac bomber', 'Star', 172, 'Lilac', 269], ['leopard3-gold', 'leopard3', 'Sunrise fairway', 'Star', 170, 'Gold', 45],
    ['mako3-blue', 'mako3', 'Straight & true', 'Champion', 180, 'Blue', 204], ['teebird3-sand', 'teebird3', 'Sand fairway', 'Star', 173, 'Sand', 41],
    ['buzzz-rose', 'buzzz', 'Rose backup disc', 'ESP', 175, 'Rose', 331],
    ['luna-mint', 'luna', 'Luna · putter one', 'Rubber blend', 173, 'Mint', 148], ['luna-lilac', 'luna', 'Luna · putter two', 'Rubber blend', 174, 'Lilac', 268], ['luna-blue', 'luna', 'Luna · putter three', 'Rubber blend', 173, 'Blue', 205],
    ['zone-gold', 'zone', 'Zone · putter two', 'Z', 174, 'Gold', 45], ['zone-rose', 'zone', 'Zone · putter three', 'Z', 173, 'Rose', 328]
  ];
  discs.forEach(([id, moldId, nickname, plastic, weight, color, sampleHue]) => add('Disc', { id, moldId, nickname, plastic, weight, color, sampleHue, photo: null, notes: '' }));
  add('Bag', { id: 'everyday', name: 'Everyday bag', discIds: discs.slice(0, 6).map(d => d[0]), notes: 'My regular lineup' });
  add('Bag', { id: 'luna-bag', name: 'Luna squad', discIds: ['luna-mint', 'luna-lilac', 'luna-blue'], notes: '' });
  add('Bag', { id: 'zone-bag', name: 'Zone squad', discIds: ['zone-peach', 'zone-gold', 'zone-rose'], notes: '' });
  add('Team', { id: 'team-luna', name: 'Team Luna', bagId: 'luna-bag' });
  add('Team', { id: 'team-zone', name: 'Team Zone', bagId: 'zone-bag' });
  add('Round', { id: 'hole-1', name: 'Hole 1', complete: false });
  add('Competition', { id: 'putterwarz', name: 'PutterWarz', teamIds: ['team-luna', 'team-zone'], roundIds: ['hole-1'], combine: 'all', constraints: [
    { id: 'bag-size', kind: 'bagLimit', value: 5, enabled: true }, { id: 'single-mold', kind: 'oneMold', value: 1, enabled: true }, { id: 'round-throws', kind: 'teamThrows', value: 3, enabled: true }
  ] });
  // The preset IS the projection layer (task 79): broadcast's own `sponsor`
  // override (defaultPresets, src/presentation.js) is what makes the
  // OnTheCourse lockup show up, not a projection-layer default here. One
  // instance override is still seeded, so the editor opens with something
  // inherited AND something overridden to look at.
  const cards = defaultCards();
  cards.instances.shelf = { ...cards.instances.shelf, 'buzzz-mint': { accent: '#d47d54' } };
  return {
    version: 2, schemas: clone(schema), objects, presets: defaultPresets(), cards,
    layout: { presetId: 'broadcast', arrangement: 'row', anchor: 'bottom-left', scale: 1.25, gap: 16, orientation: 'landscape', frame: { presetId: 'none', title: '' } },
    battle: { id: 'comparison', name: 'My disc comparison', templateId: 'open', combine: 'all', constraints: [], entries: [ { id: 'entry-1', discId: 'buzzz-mint' }, { id: 'entry-2', discId: 'zone-peach' }, { id: 'entry-3', discId: 'destroyer-lilac' } ], currentStateId: 'state-1', states: [{ id: 'state-1', name: 'Opening', scores: { 'entry-1': null, 'entry-2': null, 'entry-3': null }, highlight: null, winners: [] }] },
    events: [], exports: [], seedDisclosure: 'Sample collection and PutterWarz setup; no throws, measured results, usage or export events are pre-recorded.'
  };
}
