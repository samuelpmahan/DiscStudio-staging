/**
 * The LAB's addresses, lowercased for the studio.
 *
 * ChainSpot writes `px.s1.exp.maskComponents.part.blackMask` and
 * `fn.s1.exp.maskComponents.selectHsvMask`: camelCase segments, and an `exp`
 * segment in the middle naming the experiment. Tonight everything the port
 * publishes is lowercase and lives under the experiment prefix the sprint
 * reserves (`px.exp.lab.*`, `fn.lab.*`), so one mechanical rule rewrites every
 * address the LAB names:
 *
 *   drop the `exp` segment, lowercase the rest, and put it under the prefix.
 *
 *   px.course.canonicalPixels                     -> px.exp.lab.course.canonicalpixels
 *   px.s1.exp.maskComponents.part.blackMask       -> px.exp.lab.s1.maskcomponents.part.blackmask
 *   fn.s1.exp.maskComponents.selectHsvMask        -> fn.lab.s1.maskcomponents.selecthsvmask
 *   fn.s0.decodeFullImage                         -> fn.lab.s0.decodefullimage
 *
 * The rule is a function, not a table, so the compiled Mermaid document and the
 * hand-written YAML document are rewritten by the same code and stay comparable.
 */
export function labAddress(address) {
  if (typeof address !== 'string' || !address.length) throw new Error('lab: an address is a nonempty string.');
  const [kind, ...rest] = address.split('.');
  if (kind !== 'px' && kind !== 'fn') throw new Error(`lab: '${address}' is neither a px. Part nor a fn. Calculation.`);
  const tail = rest.filter(segment => segment !== 'exp').join('.').toLowerCase();
  return kind === 'px' ? `px.exp.lab.${tail}` : `fn.lab.${tail}`;
}

/** The same rule over a whole PQL document: every `call`, every `with` binding, every `into`. */
export function labDocument(document) {
  return {
    PrincipleComponentRender: document.PrincipleComponentRender,
    Ticks: document.Ticks.map(tick => ({
      name: tick.name,
      Calculations: tick.Calculations.map(calculation => ({
        call: labAddress(calculation.call),
        with: Object.fromEntries(Object.entries(calculation.with ?? {}).map(([name, address]) => [name, labAddress(address)])),
        args: calculation.args ?? {},
        into: Array.isArray(calculation.into) ? calculation.into.map(labAddress) : labAddress(calculation.into)
      }))
    }))
  };
}
