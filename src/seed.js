import { schema, clone } from './domain.js';
import { defaultPresets } from './presentation.js';
import { defaultCards } from './cards.js';
export function createSeed() {
  const objects = Object.fromEntries(Object.keys(schema).map(type => [type, {}]));
  const add = (type, value) => (objects[type][value.id] = { ...value, type });
  const manufacturers = ['Innova', 'Discraft', 'Dynamic Discs', 'Latitude 64', 'Westside Discs', 'MVP Disc Sports', 'Axiom Discs', 'Discmania', 'Prodigy Disc', 'Gateway Disc Sports', 'Kastaplast', 'Thought Space Athletics', 'Lone Star Disc', 'Mint Discs', 'Clash Discs', 'Yikun Discs', 'RPM Discs', 'Infinite Discs', 'Doomsday Discs', 'Viking Discs'];
  for (const name of manufacturers) add('Manufacturer', { id: name.toLowerCase().replace(/[^a-z0-9]+/g, '-'), name, website: '' });
  const molds = [
    ['buzzz', 'Buzzz', 'discraft', 'Midrange', 5, 4, -1, 1], ['zone', 'Zone', 'discraft', 'Putt & approach', 4, 3, 0, 3],
    ['destroyer', 'Destroyer', 'innova', 'Distance driver', 12, 5, -1, 3], ['leopard3', 'Leopard3', 'innova', 'Fairway driver', 7, 5, -2, 1],
    ['mako3', 'Mako3', 'innova', 'Midrange', 5, 5, 0, 0], ['teebird3', 'TeeBird3', 'innova', 'Fairway driver', 8, 4, 0, 2],
    ['luna', 'Luna', 'discraft', 'Putter', 3, 3, 0, 3],
    ['aviar', 'Aviar', 'innova', 'Putter', 2, 3, 0, 1], ['roc', 'Roc', 'innova', 'Midrange', 4, 4, 0, 3],
    ['wraith', 'Wraith', 'innova', 'Distance driver', 11, 5, -1, 3], ['firebird', 'Firebird', 'innova', 'Fairway driver', 9, 3, 0, 4],
    ['valkyrie', 'Valkyrie', 'innova', 'Distance driver', 9, 4, -2, 2], ['sidewinder', 'Sidewinder', 'innova', 'Distance driver', 9, 5, -3, 1],
    ['thunderbird', 'Thunderbird', 'innova', 'Fairway driver', 9, 5, 0, 2], ['eagle', 'Eagle', 'innova', 'Fairway driver', 7, 4, -1, 3],
    ['rhyno', 'Rhyno', 'innova', 'Putter', 2, 1, 0, 3], ['pig', 'Pig', 'innova', 'Putt & approach', 4, 1, 0, 3],
    ['shryke', 'Shryke', 'innova', 'Distance driver', 13, 6, -2, 2], ['beast', 'Beast', 'innova', 'Distance driver', 10, 5, -2, 2],
    ['roach', 'Roach', 'discraft', 'Putter', 2, 4, -1, 1], ['comet', 'Comet', 'discraft', 'Midrange', 4, 5, -2, 1],
    ['meteor', 'Meteor', 'discraft', 'Midrange', 5, 5, -3, 1], ['stalker', 'Stalker', 'discraft', 'Fairway driver', 7, 5, -1, 2],
    ['undertaker', 'Undertaker', 'discraft', 'Distance driver', 9, 5, -1, 2], ['vulture', 'Vulture', 'discraft', 'Distance driver', 10, 5, 0, 2],
    ['force', 'Force', 'discraft', 'Distance driver', 12, 5, 0, 3], ['nuke', 'Nuke', 'discraft', 'Distance driver', 13, 5, -1, 3],
    ['heat', 'Heat', 'discraft', 'Distance driver', 9, 6, -3, 1], ['raptor', 'Raptor', 'discraft', 'Fairway driver', 9, 4, 0, 3],
    ['cicada', 'Cicada', 'discraft', 'Fairway driver', 7, 6, -1, 1], ['passion', 'Passion', 'discraft', 'Fairway driver', 8, 5, -1, 1],
    ['judge', 'Judge', 'dynamic-discs', 'Putter', 2, 4, 0, 1], ['truth', 'Truth', 'dynamic-discs', 'Midrange', 5, 5, -1, 1],
    ['escape', 'Escape', 'dynamic-discs', 'Distance driver', 9, 5, -1, 2], ['felon', 'Felon', 'dynamic-discs', 'Fairway driver', 9, 3, 0.5, 4],
    ['trespass', 'Trespass', 'dynamic-discs', 'Distance driver', 12, 5, -1, 3], ['getaway', 'Getaway', 'dynamic-discs', 'Distance driver', 9, 5, -1, 3],
    ['pure', 'Pure', 'latitude-64', 'Putter', 3, 3, -1, 1], ['fuse', 'Fuse', 'latitude-64', 'Midrange', 5, 6, -1, 0],
    ['saint', 'Saint', 'latitude-64', 'Fairway driver', 9, 7, -1, 2], ['river', 'River', 'latitude-64', 'Fairway driver', 7, 7, -1, 1],
    ['ballista', 'Ballista', 'latitude-64', 'Distance driver', 14, 5, -1, 3], ['diamond', 'Diamond', 'latitude-64', 'Fairway driver', 8, 5, -3, 1],
    ['harp', 'Harp', 'westside-discs', 'Putt & approach', 4, 3, 0, 3], ['shield', 'Shield', 'westside-discs', 'Putter', 3, 3, 0, 1],
    ['tursas', 'Tursas', 'westside-discs', 'Midrange', 5, 5, -2, 1], ['sword', 'Sword', 'westside-discs', 'Distance driver', 12, 5, -0.5, 2],
    ['envy', 'Envy', 'mvp-disc-sports', 'Putter', 3, 3, 0, 2], ['hex', 'Hex', 'mvp-disc-sports', 'Midrange', 5, 5, -1, 1],
    ['volt', 'Volt', 'mvp-disc-sports', 'Fairway driver', 8, 5, -0.5, 2], ['tesla', 'Tesla', 'mvp-disc-sports', 'Distance driver', 9, 5, -1, 2],
    ['wave', 'Wave', 'mvp-disc-sports', 'Distance driver', 11, 6, -2, 2], ['proxy', 'Proxy', 'mvp-disc-sports', 'Putter', 3, 3, -1, 0.5],
    ['p2', 'P2', 'discmania', 'Putter', 2, 3, 0, 1], ['md3', 'MD3', 'discmania', 'Midrange', 5, 5, 0, 1],
    ['fd', 'FD', 'discmania', 'Fairway driver', 7, 6, -1, 1], ['essence', 'Essence', 'discmania', 'Fairway driver', 8, 6, -2, 1],
    ['dd3', 'DD3', 'discmania', 'Distance driver', 12, 5, -1, 3], ['pd', 'PD', 'discmania', 'Distance driver', 10, 4, 0, 3],
    ['wizard', 'Wizard', 'gateway-disc-sports', 'Putter', 2, 3, 0, 2],
    ['kaxe', 'Kaxe', 'kastaplast', 'Fairway driver', 6, 4, 0, 3], ['falk', 'Falk', 'kastaplast', 'Fairway driver', 9, 6, -2, 1],
    ['reko', 'Reko', 'kastaplast', 'Putter', 3, 3, 0, 1], ['berg', 'Berg', 'kastaplast', 'Putter', 1, 1, 0, 2],
    ['grym', 'Grym', 'kastaplast', 'Distance driver', 12, 5, -1, 3],
    ['pathfinder', 'Pathfinder', 'thought-space-athletics', 'Midrange', 5, 5, 0, 1], ['votum', 'Votum', 'thought-space-athletics', 'Distance driver', 9, 5, -1, 2],
    ['pa-3', 'PA-3', 'prodigy-disc', 'Putter', 3, 3, 0, 1], ['m4', 'M4', 'prodigy-disc', 'Midrange', 5, 6, -3, 0],
    ['f5', 'F5', 'prodigy-disc', 'Distance driver', 9, 5, -2, 1], ['d2', 'D2', 'prodigy-disc', 'Distance driver', 12, 5, -1, 3]
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
    layout: { presetId: 'broadcast', singlePresetId: 'spotlight', arrangement: 'row', anchor: 'bottom-left', scale: 1.25, gap: 16, orientation: 'landscape', frame: { presetId: 'none', title: '' } },
    battle: { id: 'comparison', name: 'My disc comparison', templateId: 'open', combine: 'all', constraints: [], entries: [ { id: 'entry-1', discId: 'buzzz-mint' }, { id: 'entry-2', discId: 'zone-peach' }, { id: 'entry-3', discId: 'destroyer-lilac' } ], currentStateId: 'state-1', states: [{ id: 'state-1', name: 'Opening', scores: { 'entry-1': null, 'entry-2': null, 'entry-3': null }, highlight: null, winners: [] }] },
    events: [], exports: [], seedDisclosure: 'Sample collection and PutterWarz setup; no throws, measured results, usage or export events are pre-recorded.'
  };
}
