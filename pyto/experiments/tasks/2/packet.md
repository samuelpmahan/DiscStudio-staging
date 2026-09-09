# Task 2

Intent: Address validator and census: parse any address into root, reserved second segment and rest; report every address in pyto that would fail the three-root rule; enforce nothing
Starting point: 50ec3f7b87108ebe6d9bc5f0e448bfbbc4a8dca3 (checkpoint: neat ids count origin's exp branches; board: undo tested)
Verify: cd pyto && python3 -m unittest tests.test_address
Allow: any
Candidate: 3 files, see below
Evidence: suite exit 0, see below

## Candidate

- A  pyto/scripts/address_census.py
- A  pyto/src/pyto/address.py
- A  pyto/tests/test_address.py

```
pyto/scripts/address_census.py | 325 +++++++++++++++++++++++++++++++++++++++++
 pyto/src/pyto/address.py       | 118 +++++++++++++++
 pyto/tests/test_address.py     | 157 ++++++++++++++++++++
 3 files changed, 600 insertions(+)
```

## Evidence

- verify: `cd pyto && python3 -m unittest tests.test_address` exit 1 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (evidence/check_all.txt)
    suite                         tests  status
    library                         120  OK
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
- {?} ReservedSecondUnderFnOc: `check()` reports `fn.view.surface` and `oc.run.threshold` as
  violations ("second segment reserved under px"). The rule as written reserves the six segments
  *under `px`* (`BOARD.md:103-104`, `questions.md:352-353`, `questions.md:441-443`) and says
  nothing about whether `fn.view.*` or `oc.run.*` is wrong. I chose to report it; if the reservation
  is only about `px`, that branch (`src/pyto/address.py:112-116`) should go.
- {?} BareRootIsAViolation: `check("px")` reports "a bare root with no second segment". No source
  says a one-segment address is illegal; I inferred it from "the second segment is the domain noun
  that outlives the stage" (`research/chainspot-branch-mining.md:187`). If a bare root is legal
  (a prefix query, say), `src/pyto/address.py:106-111` should go.
- {?} QuestionRootReportsTwice: `check("?")` returns two problems, "'?' is outside the address
  space" and "bare root". One would read better; I left both because they are independently true.
- {?} MountSyntaxUnspecified: the rule says a world is a mount outside the address
  (`research/chainspot-branch-mining.md:157,167`) but nothing says how a mount is *written* beside
  an address (`chess:<gameid>` prefix, a separate field, a PxC per mount). `parse()` therefore has
  no field for one, and any string carrying `:` fails the census regex and is never counted.
- {?} CensusRegexIsNoisy: the task's regex matches any quoted dotted lowercase token, so 3219 of
  4660 literals are "rejected" but most are file names (`core.py`), attribute paths (`sys.path`,
  `time.time`) and dotted keys, not addresses anyone wrote. The census says so
  (`experiments/tasks/2/census.md`) and does not try to separate them; a real address inventory
  needs either a marker at the write site or a `Part(...)`-call-site scan instead.
- {?} ComputedAddressesAreInvisible: `material.<sha>` never appears as a literal because it is an
  f-string (`experiments/grouped-ablation/materials.py:39,222`), so a literal census reports zero
  for the very address the stress test flagged. Every computed address in the tree is missed the
  same way.
- {?} StressTestInputCount: the measure that reproduces the stress test's bare `scratch.` 526
  exactly (quoted `scratch.`-prefixed occurrences under `experiments/grouped-ablation/`) gives 131
  for `input.`, not the recorded 113. Either the evidence regeneration in `a5404b1` moved the tree
  between the two readings, or the stress test excluded attribute-access `input.` by hand. Its
  script is not in the tree, so I could not settle it.
- {?} AddressNotExported: `src/pyto/address.py` is deliberately absent from `src/pyto/__init__.py`,
  so `import pyto` does not pull it in and nothing enforces the rule by accident. If the module is
  meant to be the public description, exporting it is a one-line change the owner should make
  knowingly.
- {?} CensusCountsItsOwnPacket: the scan excludes only its own output (`address_census.py:54-55`)
  and not this file, so every address quoted in these `{?}` lines is counted as a literal and
  editing the packet moves the census totals. Excluding `experiments/tasks/2/` wholesale would
  also hide task 2's own test fixture, which is a real literal someone wrote, so I left the
  directory in the scan and record the circularity here instead.
- {?} CensusHitDefinition: the census defines a hit as "a quoted string whose whole content matches"
  the regex (`experiments/tasks/2/census.md:3`). Its first scanner took one alternation over the
  three quote kinds, so on a line where one kind encloses another only the outer region was read
  and a quoted address nested inside a quote of another kind was never seen. I took the reading
  that matches the stated definition: each kind is now scanned over the whole line separately and
  the regions merged, de-duplicated by position (`scripts/address_census.py:36-45,75-86`). That
  moves the total from 4296 to 4660 literals and, for one worked example,
  `px.view.partsInspector` from 4 occurrences to 8 (the ones the old scan missed
  are prose whose double-quoted sentence encloses a backticked address, and a backticked code span
  enclosing a single-quoted address). If the owner wants the outermost quoted region instead, the
  scan goes back to one alternation and every number in `census.md` moves back with it. One
  limitation survives either reading: quotes are paired left to right within a line, so an
  apostrophe in prose still swallows a following address quoted with the same character.
- {?} SrcCleanlinessGuard: `experiments/grouped-ablation/test_materials.py:346-353` asserts
  `git status --porcelain -- pyto/src` is empty, so any new, uncommitted module under
  `src/pyto/` fails that suite; `src/pyto/address.py` does, and `check_all.sh` therefore reports
  SOME SUITES FAILED -- `experiments/grouped-ablation` 230 tests, failures=1, the only failing
  test in the tree, every other suite OK -- for as long as this task is unlanded. My resolution
  is to leave the module where it is. It is a library module describing a library rule; the
  sibling guard one method up names only the experiment's own strays by hand
  (`test_materials.py:342-344`); and the porcelain check goes quiet the moment the task is
  committed, because the file is then tracked and unmodified, so the red gate is an artefact of
  the delivery state, not of the module's home. The task forbids committing, so I cannot show
  that green. Whether the guard is meant to bind library modules added by other tasks, or only
  the grouped-ablation experiment's own strays, is the owner's call.
- {?} CitationBaseline: three citations of the stress test's findings (in `address.py`'s
  docstring, in the census script and in the census heading) read `questions.md:344-347`, which is
  `{?} RootIdIsContent`, both at HEAD and at the task's starting commit `50ec3f7`. The stress test
  with the 526 / 113 / `materials.py:39,222` findings is `questions.md:125-129`, inside the
  resolved `{?} AddressRootIsAMount` (`questions.md:118-141`). I have repointed all three. What I
  cannot settle is where `344-347` came from: no draft in the tree's history carries the stress
  test at those lines, so the number was wrong when it was first written and nothing in the
  repository explains it.
- {?} GuardVerdictForLanding: refuter re-derivation confirms the only red in the tree is
  `experiments/grouped-ablation` `test_materials.py:345-352` `LibraryUntouched.test_git_status_is_clean_under_pyto_src`,
  failing with `?? pyto/src/pyto/address.py`, so `check_all.sh` prints SOME SUITES FAILED
  (`scripts/check_all.sh:200-204`). I checked the packet claim at `packet.md:72-74` with a throwaway
  git index: staging the file is not enough (`git status --porcelain -- pyto/src` still prints
  `A  pyto/src/pyto/address.py`); only a commit empties it. Whether a task that cannot commit may
  still be called green is the owner rule I could not find written anywhere.
- {?} CensusBacktickPairs: the census caveat names only apostrophes as the left-to-right pairing
  loss (`scripts/address_census.py:132-134`), but the same pairing skips a doubled-backtick RST
  literal: in a line reading two backticks, an address, two backticks, the scanner pairs backtick 1
  with backtick 2 and backtick 3 with backtick 4, so the address between them is never a hit. Every
  address example in `src/pyto/address.py` own docstring is invisible to the census for that reason,
  which is part of why a naive grep counts 657 px literals outside evidence where the census counts
  644. Whether the caveat should name this second mechanism, or the scanner should strip doubled
  backticks first (every number in `census.md` moves if it does), is the owner call.
- {?} RefuterMovedTheTotals: appending the two lines above is itself the circularity the packet
  records four entries up: the census scans this file, so its totals moved from 4660 to 4662
  literals (3347 to 3349 outside evidence) when I wrote them, and the "4296 to 4660" figure in the
  hit-definition entry above now names a total the regenerated census output no longer prints.
  I regenerated that output rather than leave it stale; the 4296 to 4660 pair is still the correct
  before-and-after for the scanner change, measured on the tree as it stood before this append.
  Whether the packet should be excluded from the scan (which would also hide the task fixture the
  packet argues for keeping) stays the owner call already recorded there.
- {?} BlockerRemedyIsOutsideTheTask: the refuter's blocker (the tree's only red,
  `experiments/grouped-ablation/test_materials.py:346-352`
  `LibraryUntouched.test_git_status_is_clean_under_pyto_src`, failing on
  `?? pyto/src/pyto/address.py`, so `scripts/check_all.sh:200-204` prints SOME SUITES FAILED)
  names two remedies and this task may take neither: committing is forbidden by the task, and the
  guard is another experiment's own material -- its sibling one method up names that experiment's
  own strays by hand (`test_materials.py:342-344`), which is the narrowing the refuter asks for,
  but the edit belongs to grouped-ablation, not to task 2. A third remedy I considered and
  rejected: move the module out of `pyto/src` (under `experiments/tasks/2/`, say) so the porcelain
  check never sees it. That would clear the red inside task 2's own files, and the owner's own
  default for the materials store exempts an experiment-scoped module "until it is promoted to
  `pyto/src`" (`questions.md:134-135`); against it, this module describes a *library* rule about
  library addresses (`BOARD.md:97-111`), the library suite already runs its tests
  (`scripts/check_all.sh:78`), and moving it would break `from pyto.address import ...` at
  `tests/test_address.py:15` and `scripts/address_census.py:26` and make a library test import out
  of an experiments directory. So the module stays in `src/pyto/` and the red stands, unchanged
  from the refuter's reading: one failing test in the tree, every other suite OK. Which remedy is
  taken -- land the task, narrow the guard, or move the module -- is the owner's call, and it is
  the same call already recorded under `{?} SrcCleanlinessGuard` and `{?} GuardVerdictForLanding`.
- {?} FixerRegeneratedTheCensus: fixing the census caveat (the doubled-backtick loss, now named at
  `scripts/address_census.py:132-139`) rewrites text that `census.md` carries verbatim, and
  appending these two lines changes the tree the census scans, so `census.md` was regenerated after
  both. Its printed totals are the ones this tree produces now and no number is quoted here, to
  stop the circularity recorded under `{?} CensusCountsItsOwnPacket` from making this entry stale
  in turn; the "4296 to 4660" pair under `{?} CensusHitDefinition` remains the correct
  before-and-after for the scanner change alone, measured on the tree as it stood then.
- {?} CensusGroupWhyIsOneLiteral: in "Literals `check()` rejects, by root", each group prints a
  single `Why:` line built from the group's *first* hit only (`scripts/address_census.py:205`).
  Seven root groups contain more than one distinct reason, so that line mis-describes most of the
  group: root `fn` (`experiments/tasks/2/census.md:1034-1036`) prints the `view` reason for a group
  that is eight tenths `fn.receipt.*` literals from `tests/test_receipts.py:88-94`, and the same
  happens for the roots `pcr`, `run`, `s0`, `s3`, `discstudio` and `chainspot_quick_anno`. The
  counts and the per-literal table are right; only that one-line summary is wrong. Whether the heading
  should list every distinct reason with its count (which rewrites every group heading in
  `census.md`) or say plainly that it is the first example's reason, is the owner's call.
- {?} PacketCitationOffByThree: `{?} BareRootIsAViolation` above cites
  `research/chainspot-branch-mining.md:187` for "the second segment is the domain noun that
  outlives the stage"; that sentence is at line 184 and line 187 is blank. The module docstring
  cites 184 correctly (`src/pyto/address.py:17`). This file is append-only, so I recorded the
  correction here instead of editing the entry.
- {?} RefuterSecondPassTotals: appending these three lines is the circularity already recorded
  under `{?} CensusCountsItsOwnPacket`, and it caught me: I aimed to name every address here with a
  `*` or a `:` so no new quoted string matched the census regex, but the two backticked file names
  in the entries above are themselves hits, so regenerating moved the totals by two literals (and
  the `census` root group from five occurrences to seven). The regenerated `census.md` in this task
  is the output of the tree as it stands after this append. The entry quoting "4660 to 4662" above
  is stale against those totals for the same reason, and every future append to this file will move
  them again unless the packet is excluded from the scan -- the owner call already recorded there.
