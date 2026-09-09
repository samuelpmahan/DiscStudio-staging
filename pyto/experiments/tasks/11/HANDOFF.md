# Task 11: Mounts: a world (a course, a game, a bag) is mounted above an ordinary PxC by an id outside the address space, so one address means the same thing in every world; ported from ChainSpot's PxCRootMounts with its negative test

You are a fresh agent. Everything you need is on this page and in the files it names. The
conversation that produced this task is not needed and you will not see it.

## Get the code (once)

```
git clone -b claude/python-ultracode-supercharge-st8hnu https://github.com/samuelpmahan/DiscStudio-staging DiscStudio-staging     # or: cd into the clone you have
cd DiscStudio-staging
git fetch origin exp/11
python -m pip install -e "./pyto[drawing]"         # Python 3.11+, Node 22 for the viewer suite
git show origin/exp/11:pyto/experiments/tasks/11/packet.md  # this task's packet (also: HANDOFF.md, evidence/)
git diff f2e0b8e origin/exp/11 -- . ':!pyto/experiments/tasks'   # the candidate itself, as a diff
```

## Why this repository is worth twenty minutes

pyto is a Python transfer of a design the owner proved three times in JavaScript and TypeScript
(ChainSpot, ChessLab, EmbodiedWumpusWorld): a store of named values (PxC), pure functions over them
(Calculations), and a program that names which functions run in which order (a PCR, made of Ticks).
Every run leaves receipts: what each function read and wrote, how long it took, and a digest of its
source. From receipts you get three things for free: a cache (same inputs and digest, skip the call,
also across processes), a replay that verifies a shipped record in a fresh process, and a per-Tick
view of what the algorithm used. The founding need is the last one: the owner's course-map parser
had to fit five seconds on a phone, and nothing it used was visible. pyto is the workshop where that
visibility is designed before it is stripped for speed. JavaScript is first class; Python is where
the design is checked.

Do not take that from this page. In two minutes:

```
bash pyto/scripts/check_all.sh                                        # nine suites, ~600 tests
python pyto/experiments/grouped-ablation/run_cached.py --out /tmp/hit  # a miss, then two hits, one from a fresh process
node pyto/viewer/embed.mjs pyto/viewer/fixtures/pyto-grouped-ablation.json --out /tmp/hit/ticks.html
```

The tests were checked by mutation (each guards a specific line). The fixtures for the JavaScript
port are 440 byte-exact cases. `pyto/questions.md` is where anyone unsure writes `{?} Label: ...`
and the owner answers; read it before assuming. `pyto/BOARD.md` is the owner's one page.

## What was asked

Mounts: a world (a course, a game, a bag) is mounted above an ordinary PxC by an id outside the address space, so one address means the same thing in every world; ported from ChainSpot's PxCRootMounts with its negative test

## Starting point

f2e0b8e6e8e2422091239797d04524e2f5feaa49 (land(task-2): Address validator and census: parse any address into root, reserved second segment and rest; report every address in pyto that would fail the three-root rule; enforce nothing). MAIN may have moved since: `git log --oneline f2e0b8e..origin/claude/python-ultracode-supercharge-st8hnu` shows how far.
Landing merges the candidate onto MAIN as it is now and re-runs the suite on the result.

## What changed (the candidate)

- M  pyto/CHANGES.md
- A  pyto/src/pyto/mounts.py
- A  pyto/tests/test_mounts.py

```
pyto/CHANGES.md           |  63 ++++++++++++
 pyto/src/pyto/mounts.py   |  89 ++++++++++++++++
 pyto/tests/test_mounts.py | 257 ++++++++++++++++++++++++++++++++++++++++++++++
 3 files changed, 409 insertions(+)
```

## Evidence

- verify: `cd pyto && python3 -m unittest tests.test_mounts` exit 1 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (evidence/check_all.txt)
    suite                         tests  status
    library                         141  OK
    experiments/grouped-ablation    230  OK
    experiments/s3-synthetic          5  OK
    consumer                         61  OK
    disc-stats                        4  OK
    examples                          3  OK
    art-registry-md                   -  OK
    viewer                           83  OK
    viewer-record-schema             19  OK
    
    ALL SUITES PASSED

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

## What to do

1. Explain this to the owner in plain words: what was asked, what changed file by file (one line
   each), what the evidence shows, what is uncertain. Use no term this page does not define.
2. Ask the owner: land it, drop some files, or send it back. To drop files, from the clone:
   `bash pyto/scripts/neat.sh drop 11 <path> ...` (they go back to the starting point, the
   packet is rewritten, the suite runs again).
3. Land: `bash pyto/scripts/neat.sh land 11`. It merges the candidate into MAIN, runs the suite
   again on the merged tree, writes a receipt under `pyto/experiments/landings/`, commits
   `land(task-11): Mounts: a world (a course, a game, a bag) is mounted above an ordinary PxC by an id outside the address space, so one address means the same thing in every world; ported from ChainSpot's PxCRootMounts with its negative test`, pushes, and writes one line under "Today" on `pyto/BOARD.md`.
   If it refuses, it says exactly why, and nothing has changed.
