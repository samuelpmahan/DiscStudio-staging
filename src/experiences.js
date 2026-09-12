import { FAMILIES } from '../pyto/consumers/discstudio-card/port/painter/painter.mjs';

/**
 * P&C Experience definitions, loaded as ordinary Studio Parts.
 * `specializes` is a reference to shared requirements, not a new grammar or an
 * implicit executor. The focused cloud build will wire actions and views to
 * these definitions. No engagement, photo or specimen is created by loading them.
 */
export function studioExperienceParts() {
  const definition = (id, purpose, details) => ({ id, for: purpose, status: 'defined', ...details });
  const roots = ['uds', 'exploreshelf', 'createbag', 'managebags', 'creategraphics', 'exportgraphics'];
  return [
    ['px.studio.experiences', { for: 'discover the Studio Experiences', definitions: roots.map(key => `px.studio.${key}.definition`) }],
    ['px.studio.discviztype', { for: 'choose a depiction without changing specimen identity', variants: ['px.studio.discviztype.photo', 'px.studio.discviztype.paint'] }],
    ['px.studio.discviztype.photo', { for: 'depict a specimen with a supplied image', value: 'photo', preparation: 'src/media.js#photoData', rendering: 'fn.disc.art' }],
    ['px.studio.discviztype.paint', { for: 'depict a specimen with repeatable authored or generated art', value: 'paint', assignment: 'fn.art.assign', rendering: 'fn.disc.art', recipeFields: ['family', 'seed', 'base', 'accent', 'target', 'label'] }],
    ['px.studio.uds.definition', definition('UploadDiscToShelf', 'add a physical specimen with a useful depiction, with or without a photo', {
      parameter: 'px.studio.discviztype',
      shared: ['specimen identity', 'correctable facts', 'inspect depiction', 'optional bag membership', 'one creation command and undo', 'continue with the same disc reference'],
      actions: { create: { command: 'disc.create', calculation: 'fn.studio.applyCommand' } },
      variants: ['px.studio.uds.photo.definition', 'px.studio.uds.paint.definition'],
      contextPrefix: 'px.studio.uds.context.',
      continues: ['px.studio.exploreshelf.definition', 'px.studio.createbag.definition', 'px.studio.creategraphics.onthecourse.discspotlight.definition']
    })],
    ['px.studio.uds.photo.definition', { for: 'specialize UDS for supplied images', specializes: 'px.studio.uds.definition', discVizType: 'px.studio.discviztype.photo', additional: ['select or replace image', 'inspect prepared image', 'retain source image when changing depiction type'], effect: 'local file read and image preparation' }],
    ['px.studio.uds.paint.definition', { for: 'specialize UDS for deterministic painting', specializes: 'px.studio.uds.definition', discVizType: 'px.studio.discviztype.paint', additional: ['inspect generated candidates', 'vary and retain recipe', 'select a depiction without a file'], families: 'px.studio.uds.paint.families', starterFamilies: 'px.studio.uds.paint.starterfamilies', assignment: 'px.art.assignment', effect: null }],
    ['px.studio.uds.paint.families', { for: 'discover the existing reusable painter vocabulary', values: [...FAMILIES] }],
    ['px.studio.uds.paint.starterfamilies', { for: 'fill the first UDS demo with three contrasting existing painters', values: ['chevron-run', 'pressed-fern', 'contour-basin'] }],
    ['px.studio.exploreshelf.definition', definition('ExploreShelf', 'find, inspect, correct and select physical discs', { calculation: 'fn.shelf.query', result: 'px.shelf.view' })],
    ['px.studio.createbag.definition', definition('CreateBag', 'start a named collection of shared specimen references', { commands: ['entity.add', 'bag.duplicate', 'bag.membership'] })],
    ['px.studio.managebags.definition', definition('ManageBags', 'adapt independent collections of the same physical discs', { commands: ['entity.set', 'bag.membership', 'bag.reorder', 'bag.duplicate', 'bag.remove'] })],
    ['px.studio.onthecourse.definition', { for: 'give graphics a purpose', purposes: ['px.studio.onthecourse.discspotlight', 'px.studio.onthecourse.competition'] }],
    ['px.studio.onthecourse.discspotlight', { for: 'make one disc understandable and visually useful', rendererMode: 'card', projection: 'single', composition: 'on-the-course' }],
    ['px.studio.onthecourse.competition', { for: 'communicate a comparison or contest through authored moments', rendererMode: 'battle', projection: 'competition', composition: 'on-the-course', authoredStates: 'px.comparison.states' }],
    ...['creategraphics', 'exportgraphics'].flatMap(key => [
      [`px.studio.${key}.definition`, definition(key === 'creategraphics' ? 'CreateGraphics' : 'ExportGraphics', key === 'creategraphics' ? 'compose bound material into a useful graphic' : 'export the inspected graphic and identify what produced it', { context: 'px.studio.onthecourse.definition', discVizType: 'px.studio.discviztype', composition: 'on-the-course' })],
      ...['discspotlight', 'competition'].map(purpose => [`px.studio.${key}.onthecourse.${purpose}.definition`, { for: `${key === 'creategraphics' ? 'create' : 'export'} an OnTheCourse ${purpose} graphic`, specializes: `px.studio.${key}.definition`, purpose: `px.studio.onthecourse.${purpose}` }])
    ])
  ];
}
