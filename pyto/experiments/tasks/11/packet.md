# Task 11

Intent: Mounts: a world (a course, a game, a bag) is mounted above an ordinary PxC by an id outside the address space, so one address means the same thing in every world; ported from ChainSpot's PxCRootMounts with its negative test
Starting point: f2e0b8e6e8e2422091239797d04524e2f5feaa49 (land(task-2): Address validator and census: parse any address into root, reserved second segment and rest; report every address in pyto that would fail the three-root rule; enforce nothing)
Verify: cd pyto && python3 -m unittest tests.test_mounts
Allow: pyto/src/pyto/mounts.py pyto/tests/test_mounts.py pyto/CHANGES.md pyto/experiments/tasks
Candidate: not packed yet
Evidence: not packed yet

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)

- {?} MountSyntaxUnspecified: task 2 was asked to record this entry and did not — `questions.md`
  has `AddressRootIsAMount` (`questions.md:118-141,407-411`) and `RootIdIsContent`
  (`questions.md:413-416`) but no `MountSyntaxUnspecified`, and `src/pyto/address.py:26-28` says
  outright that a mount "lives outside the text of the address", so there is no written syntax for
  naming a mounted address in prose, a PCR YAML, a PQL query or the viewer. `mounts.py` needs none
  (the call is `mounts.get(root).get("px.badges.px")`), but the mining's report field writes one —
  `rootSemantics: '<ImgID>/{px.*,fn.*}'`, `43e6ea3:scripts/warm-dev-pxc-roots.mjs:69-70` quoted at
  `research/chainspot-branch-mining.md:80`. Should pyto adopt `<root>/px.badges.px` as the display
  form, with the `/` reserved so it can never be confused with a `.` segment?
- {?} MountsIsGenericNotPxCOnly: ChainSpot's `mounts.ts` is typed to `PxC` and this port copies
  that in the annotations (`src/pyto/mounts.py:44,56,66`), but nothing is enforced at runtime and
  the module imports `PxC` only under `TYPE_CHECKING` (`src/pyto/mounts.py:31-32`), so a `Mounts`
  will happily hold anything. `{?} PortableKernel`'s "two mounts today" is ChainSpot's raster
  material and neat's durable tickets — if neat's tickets are not a `PxC`, is the duck-typing the
  intent, or should `mount` refuse a non-`PxC` the way `Calculation` refuses a non-`fn.` address
  (`src/pyto/core.py:33-34`)?
- {?} LabelOfUnmountedRootIsLoud: the mining fixes only two loud errors — a conflicting re-mount
  (`43e6ea3:packages/alg/src/exec/mounts.ts:32-34`) and a missing root on `get` (`:40`) — and says
  nothing about the label side map, which in ChainSpot is a bare `Map`
  (`43e6ea3:scripts/warm-dev-pxc-roots.mjs:46-48`, `research/chainspot-branch-mining.md:71-74`).
  This port makes both `set_label` and `label` raise `KeyError` for a root that is not mounted
  (`src/pyto/mounts.py:81-82,87-88`) on the fail-loud reading, so `label` never answers about a
  world that does not exist; a mounted-but-unnamed root still returns `None`
  (`src/pyto/mounts.py:89`). Is a loud `label` right, or should it be a plain lookup returning
  `None`?
- {?} MountsAndEverythingIsAPart: `{?} EverythingIsAPart` (`questions.md:607-622`) wants receipts,
  packets and proposals to be Parts under reserved second segments, and names `pcr.py` as needing
  "a `receipt` mount **or** segment" (`questions.md:622`). `Mounts` is the mount half of that
  choice but is not wired to anything: `PcrRun.receipts` still lives on the run object
  (`src/pyto/pcr.py:145`, per `questions.md:614-615`) and no caller in the tree constructs a
  `Mounts`. Is the receipt world meant to become a mount here, or a reserved `px.receipt.*`
  segment, with mounts kept for worlds only?
- {?} LabelMapBelongsOnMounts: the mining names six methods to port —
  "Port `mount/has/get/roots/entries/slice`" (`research/chainspot-branch-mining.md:411`) — and in the
  reference the labels are a `Map` held *beside* the mounts by the caller (`const root =
  s0.fullImage.imageId;` / `roots.mount(root, ...)` / `labels.set(root, label)`,
  `43e6ea3:scripts/warm-dev-pxc-roots.mjs:46-48`, quoted at
  `research/chainspot-branch-mining.md:71-74`). This port folds that map into the type as a second
  dict plus `set_label`/`label` (`src/pyto/mounts.py:42,79-89`), making eight methods, and `slice`
  then has to carry labels across (`src/pyto/mounts.py:75-76`). Nothing in an address changes
  either way (`tests/test_mounts.py:194-207` proves it), so this is a shape question, not a
  correctness one: should `Mounts` own the label side map, or stay the six methods and leave the
  caller its own `dict[str, str]`?
