# Task 0

Intent: Day 3 close-out: the record contract says what both runtimes do (declared_consumes, nested array cap), run_cached derives hit or miss from counters, viewer and materializer agree on every fixture
Starting point: 9d5ba26dd027779403a9c8154a535c3d8520cb98 (land(landing-protocol): one script, one receipt per landing, checkpoints labelled; neat as the caveman front)
Verify: cd pyto && python3 -m unittest tests.test_materialize && node --test viewer/test/*.test.mjs && python3 -m unittest discover -s experiments/grouped-ablation -p 'test_materials.py'
Allow: any
Candidate: not packed yet
Evidence: not packed yet

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)

- {?} Truncation note wording: matched exactly, no blocker. adapters.js:280-283 now emits the
  same string materialize.py:236-239 writes ("N array(s) truncated to the first 200 entries;
  original lengths: [...]", lengths sorted descending), pinned by a fixture generated from
  pyto.materialize.render_value itself (adapters.test.mjs, "materialize truncates nested arrays
  exactly as the Python materializer does"). Recording it only because the task asked to say so
  if it could not be matched.
- {?} Stale truncation wording left in two files I do not own: pyto/viewer/fixtures/
  pyto-value-kinds.json:146 and pyto/viewer/test/render.test.mjs:251-253 still carry the retired
  JS spelling "array truncated: showing the first 3 of 6 entries". Both use it as an opaque note
  payload (validate does not constrain note text, renderValue just prints it), so nothing fails —
  but they are now the only places in the tree that spell truncation the old way. Owner decides
  whether the fixture and its render test get re-spelled to match materialize.py.
- {?} The over-cap note still diverges between the runtimes, in the same function: when a value
  is over 256 KB, materialize.py:254-260 writes "json value is N bytes, over the 262144 byte cap;
  sha256 = <hex>" and APPENDS the truncation note after it, while adapters.js:326-331 writes
  "value omitted: N bytes over the 262144-byte cap; digest <material id>" and DROPS the block's
  note, so the browser never says the arrays were also cut. RECORD.md:63-64 only requires that
  the note carry "the size and the digest", so both are conformant text and I left it alone —
  but a reader comparing a pyto record with a browser one still sees two different sentences,
  and the browser one loses information. Owner decides whether that is a second fix.
- {?} The 256 KB cap can still land on different sides in the two runtimes for a value within a
  few bytes of it: materialize.py:250 measures json.dumps(data, sort_keys=True,
  separators=(",",":")) while adapters.js:284 measures JSON.stringify(data). Key order does not
  change the byte count, but number spelling does — an integral float is "0.0" from Python and
  "0" from JavaScript, the difference viewer/README.md:203-205 already pins for the round trip.
  Out of scope for this fix; noting it because it is the remaining way the two caps disagree.
- {?} CHANGES.md is outside my declared file list. The task said to note the RECORD.md edit
  under Day 3, so I appended one section ("Day 3 contract fix: `declared_consumes` is the Part
  reads, not a copy of `inputs`") at the end of pyto/CHANGES.md. If another agent appended to
  the same tail this hour, the two entries need ordering by hand. Owner decides whether
  CHANGES.md should be owned by one agent per pack.
- {?} `declared_consumes` may be dead weight rather than a second witness. After this fix it is,
  for pyto, exactly the `px:` subset of `inputs` — derivable, carrying nothing `inputs` does not
  already say (`pcr.py:308-315`, `materialize.py:416`; the new test asserts the equality on all
  15 invocations of evidence/run-1/record.json). It only earns its place if another runtime can
  declare a Part read that is *not* a binding: ChessLab's `declaredConsumes`
  (`viewer/adapters.js`, RECORD.md's Adapters table) is the candidate. I wrote the contract so
  both are legal ("a subset of `inputs.values()`, never a superset") and told readers to union.
  Owner decides whether `declared_consumes` stays a field or becomes derived like `parts`.
- {?} "In binding order" is unverifiable from a record on disk. RECORD.md:67 requires sorted
  keys, so `inputs` loses binding order the moment it is written; only `declared_consumes`
  preserves it. In evidence/run-1/record.json no invocation has two `px:` bindings, so the two
  orders cannot be told apart there — the ordering half of the rule is pinned by an in-memory
  test instead (`test_two_part_bindings_keep_binding_order_not_alphabetical_order`, parameter
  names `zebra` then `alpha`). Owner decides whether `inputs` should be exempted from the
  sorted-keys rule so the record itself carries binding order.
- {?} `compare` in viewer/fixtures/pyto-value-kinds.json has `inputs: {}` while its `args` hold
  six `fn:` strings (`"all": "fn:score.all"`, …). That is a binding smuggled through `args`,
  which no reader resolves, so the fixture's part index shows `scratch.ablation.score.all` with
  `read_by: []`. I left it: it is not the convention this task is about, and changing it moves
  the fixture's `parts` block. Owner decides whether the fixture should bind those as inputs.
- {?} `reuse-ledger.json`'s key `ms_saved_total_for_two_hits` is gone; the ledger now carries
  `hits_observed` (how many of the three resolutions' own counters recorded a hit) and
  `ms_saved_total` (`ms_saved_per_hit * hits_observed`), and each `resolutions` row carries a
  `counters_delta` (`run_cached.py:141-165, 253-270, 291-292`). The old name asserted the
  answer in the key itself, which is the same failure as the literal `"outcome": "hit (disk)"`
  it sat beside. Nothing outside `evidence/run-6-cached/` read the old key (grep over the
  worktree), but two docs still narrate the outcome as fixed — `pyto/BOARD.md:33` and
  `pyto/scripts/neat.sh:146` both say "one miss, then two hits". They are still true of a run
  against an intact store (evidence regenerated with `--force`: `hits_observed` 2, counters.json
  byte-identical), and I do not own either file. Owner decides whether that prose should be
  reworded to "outcomes read off the counters".
- {?} `outcome_from_delta` (`run_cached.py:148-165`) has two branches no live run can reach
  today: `"miss (no write)"` (a miss whose `store.save` did not increment `writes`) and
  `"no counter movement"` (a resolution that moved nothing). `material()` always saves on a miss
  and always increments `requests`, so both are dead unless `save()` starts failing softly
  (`materials.py:245-250`). I kept them because the function's contract is "report what the
  counters say", and a silent `"hit (disk)"` for an unmoved counter is exactly the bug being
  fixed; they are pinned by a unit test rather than by a program run. Owner decides whether an
  unreachable-but-honest branch pair is worth its cost, or whether these should raise instead.
- {?} RECORD.md line-number citations across the tree (verifier): the Day 3 edit added 54 lines
  above `## Field rules`, so every `RECORD.md:NN` citation written before it now points at the
  wrong line -- `src/pyto/materialize.py:49` (`# RECORD.md:63 -- 256 KB`) now lands on
  `"hit": false,`, `src/pyto/materialize.py:480` (`RECORD.md:67`, sorted keys) lands on `}`,
  `viewer/test/record_schema.py:28` (`RECORD.md:16`) lands on prose, and ~20 more in
  `materialize.py`, `record_schema.py`, `test_record_schema.py`, `render.test.mjs` and
  `questions.md`. Only two were updated (`viewer/README.md:79`, `viewer/test/adapters.test.mjs:246`).
  Owner decides whether the contract gets stable anchors (section names, not line numbers) or
  whether every citation is renumbered on each RECORD.md edit.
- {?} check_all.sh suite-count pins (verifier): the only pin that actually failed after this
  work was `EXPECT_VIEWER=83` against 85 tests (I ran HEAD's script: `-- viewer: FAILED (expected
  exactly 83 tests, got 85)`, every other suite OK). The fix deleted `expect_count()` and all four
  pins instead, citing `BOARD.md:55` ("Owner: checks that cause friction get disabled"), which was
  written about the landing protocol. Owner decides whether that directive reaches the suite-count
  kill criteria, or whether `EXPECT_VIEWER` should simply have gone to 85.
- {?} `evidence/run-6-cached/reuse-ledger.json` now records this worktree (verifier): lines 166
  and 171 carry `/home/user/DiscStudio-staging/EXP/0/.venv/bin/python` and
  `/home/user/DiscStudio-staging/EXP/0/pyto/experiments/grouped-ablation`. It is the only evidence
  file in the tree carrying `EXP/0`; every other one records the MAIN path. Owner decides whether
  regenerated evidence should be produced from MAIN, or whether these paths should be recorded
  relative to the pyto root.
- {?} `declared_consumes` is unenforced by either validator (verifier): `viewer/adapters.js:153-154`
  and `viewer/test/record_schema.py:188-189` both run the entries through the px-or-fn binding
  check, so an `fn:` entry -- exactly what `viewer/fixtures/pyto-value-kinds.json` had to be
  hand-edited to remove in six places -- still validates. The new rule is pinned only by tests over
  pyto's own output. Owner decides whether the validators should reject a non-`px:`
  `declared_consumes` entry, and an entry that is not in `inputs.values()`.
- {?} ViewerPin: `EXPECT_VIEWER` still reads 83 in `scripts/check_all.sh:160` while the viewer
  suite runs 85. The blocker finding's own remedy is a one-number bump there, but this pack is
  forbidden to edit that file, so `scripts/check_all.sh` is back at HEAD byte for byte
  (`git checkout HEAD -- pyto/scripts/check_all.sh`) and the pin is left as the owner wrote it.
  The pin is env-overridable by design at `check_all.sh:160` (`${EXPECT_VIEWER:-83}`), so the
  suites were run green as `EXPECT_VIEWER=85 bash pyto/scripts/check_all.sh`; run unaltered, HEAD's
  script reports `-- viewer: FAILED (expected exactly 83 tests, got 85)` and every other suite OK.
  `experiments/runs/day2/untested.md:175-181` documents this pin as one the adding session bumps
  itself. Owner decides: bump `EXPECT_VIEWER` to 85, or drop the two viewer tests this pack's
  earlier round added (`$&`/`` $` ``/`$'` in a served record, and `deriveHit` on an overwritten
  address), or lift the no-edit rule for a one-number pin bump.
- {?} RECORD.md citations in dated prose and archived runs: the live-code and live-doc citations
  are renumbered against the amended contract, but two classes are deliberately untouched --
  the dated entries earlier in `CHANGES.md` (`CHANGES.md:372,399,408,448,500,519,560,607,637,648,663`
  and `:691`, which says "before this change" in so many words) and the archived records under
  `experiments/runs/day3/` (`diff.patch`, `meta.json`, `tests.txt`, `untested.md`, `verdicts/*.json`),
  `experiments/landings/*/check_all.txt`, and the built page
  `experiments/grouped-ablation/evidence/run-1/tick-viewer.html`. Each quotes RECORD.md as it stood
  when it was written. Owner decides whether a changelog entry's citation is a pointer to the rule
  today (renumber it) or part of the record of that day (leave it), and whether the contract should
  carry stable anchors so the question stops recurring.
- {?} Closed by this round, listed so the entries above them are not read as still open: the
  RECORD.md renumbering question is answered for live code and live prose (all renumbered); the
  reuse-ledger worktree paths are gone (`run_cached.portable()`, evidence regenerated, no path
  under the checkout survives in `evidence/run-6-cached/`); and the `declared_consumes` rule is now
  enforced by both validators, so the fixture cannot drift back. What is left for the owner in each
  of those three is only the narrower question restated above.
- {?} The twelve `RECORD.md:NN` citations in `src/pyto/materialize.py` (lines
  15, 20, 49, 50, 51, 187, 223, 296, 308, 394, 480, 595) are still numbered against the
  pre-amendment contract, and could not be fixed here: renumbering them dirties `pyto/src`,
  which `experiments/grouped-ablation/test_materials.py:352`
  (`LibraryUntouched.test_git_status_is_clean_under_pyto_src`) fails on -- I made the edit,
  the suite went red with `M pyto/src/pyto/materialize.py`, and I reverted it. Owner decides
  whether a comment-only renumbering counts as touching the kernel for that rule, or whether
  the contract should carry stable anchors so a kernel comment never needs to move.

- {?} ViewerPin, re-derived (second verifier): run unaltered as the task's check step asks
  (`PYTHON=.../EXP/0/.venv/bin/python bash pyto/scripts/check_all.sh`), the suite ends
  `SOME SUITES FAILED` -- `-- viewer: FAILED (expected exactly 83 tests, got 85)`,
  `scripts/check_all.sh:160`. Every other suite is OK (library 106, grouped-ablation 240,
  s3-synthetic 5, consumer 61, disc-stats 4, examples 3, art-registry-md, viewer-record-schema 19).
  The pin's own comment at `check_all.sh:152-159` already reconciles to 83 (77 + 4 + 2), so the two
  tests this round added to `viewer/test/adapters.test.mjs` are unaccounted for in it. The pack is
  forbidden to edit that file and the pin is env-overridable, so nothing here is wrong except that
  the tree as it stands does not pass its own gate. Owner decides: bump to 85, or move the pin out
  of the file the packs may not touch.
- {?} `hits.py:14` renumbering is off by a bullet (verifier): the citation was
  `RECORD.md:53-56` (the four-line `hit` bullet) and is now `RECORD.md:83-105`, which starts on the
  `declared_consumes` bullet (`viewer/RECORD.md:83`) and stops two lines into `hit`
  (`viewer/RECORD.md:104-107`). The sentence it annotates is about the `hit` rule, so the range
  should have been `104-107`. Every other renumbering in this round lands correctly
  (`materialize_run.py:23` -> :122 pyto adapter row, `questions.md:444` -> :112 the 256 KB clause,
  `emit_adapter_records.mjs:9,24` -> :116 sorted keys, `tick-viewer.js:123` and
  `render.test.mjs:226` -> :109-110 png-data-url, `record_schema.py` -> :20/:22/:108-113/:115).
  Owner decides whether a line range that spans two bullets is worth a follow-up or is the cost of
  line-number citations (see the stable-anchors question above).
- {?} The `declared_consumes` rule is enforced in `viewer/adapters.js:153-171` but no test in the
  JavaScript suite fails when that enforcement is deleted (verifier, mutation-checked): removing the
  `!entry.startsWith('px:')` branch leaves `node --test viewer/test/*.test.mjs` at 85 pass / 0 fail,
  and so does removing the `!boundValues.has(entry)` branch. Both mutants are caught, at the same
  JSON path, by the Python cross-check suite (`viewer/test/test_record_schema.py`,
  `test_javascript_refuses_what_python_refuses_and_names_the_same_path` and
  `test_every_typed_rule_of_RECORD_md_rejects_its_violation`), which is a real kill and is the suite
  whose whole job is cross-runtime agreement. Owner decides whether a JS-side rule should also be
  pinned by a JS-side test, so `node --test viewer/test/` alone is a meaningful gate.
- {?} `evidence/run-6-cached/reuse-ledger.json:166` now spells the child interpreter
  `"<pyto>/../.venv/bin/python"` -- a `<pyto>`-relative path that climbs out of the pyto root,
  because this worktree's venv sits at the checkout root and `portable()`
  (`run_cached.py:186-203`) rewrites anything under the checkout relative to `pyto/`. The committed
  value it replaced was `/usr/local/bin/python3`, a system interpreter `portable()` would have left
  alone. Nothing is false and no directory that landing deletes is named, but the recorded command
  is no longer one a reader can run. Owner decides whether `portable()` should anchor at the
  checkout root (`<checkout>/.venv/bin/python`) rather than at `pyto/`.
- {?} ViewerPin, after fix round 3: the pin is now two further tests behind. `viewer` runs
  87 pass / 0 fail (`node --test test/*.test.mjs` in `pyto/viewer`) against
  `scripts/check_all.sh:160`'s `EXPECT_VIEWER="${EXPECT_VIEWER:-83}"`, so the unaltered
  `bash pyto/scripts/check_all.sh` still ends `SOME SUITES FAILED` on that one line
  (`-- viewer: FAILED (expected exactly 83 tests, got 87)`) and on nothing else. 83 -> 85 was
  fix round 2's two truncation tests in `viewer/test/adapters.test.mjs`; 85 -> 87 is fix round
  3's two `declared_consumes` tests in the same file, added because the second verifier found
  the JS rule unpinned on the JS side. This pack may not edit `scripts/check_all.sh`, so the
  number is the owner's to change. Everything else is green:
  `EXPECT_VIEWER=87 bash pyto/scripts/check_all.sh` ends `ALL SUITES PASSED`. Owner decides:
  bump the pin to 87, or move it out of the file the packs may not touch.
- {?} The three minor findings of the second verifier are fixed in this round, so the three
  `{?}` entries above that record them are answered, not open: `hits.py:14` now cites
  `pyto/viewer/RECORD.md:104-107` (the `hit` bullet); `viewer/test/adapters.test.mjs:439-460`
  adds one test per branch of `viewer/adapters.js:162-167`, each killed only by its own branch;
  and `portable()` (`experiments/grouped-ablation/run_cached.py:176-200`) now anchors at the
  root that contains the path, so `evidence/run-6-cached/reuse-ledger.json:166` reads
  `<checkout>/.venv/bin/python`. Owner decides whether `<checkout>` is the right placeholder
  name for a second root in committed evidence, since RECORD.md and the evidence files so far
  have only ever spelled `<pyto>`, and whether `portable()` should be shared rather than
  living in one experiment script.

- {?} RECORD.md's worked example is prose nothing pins (third verifier): no test in the tree
  reads `pyto/viewer/RECORD.md` (grep for `open(`/`readFileSync`/`read_text` beside `RECORD.md`
  over `tests/`, `viewer/`, `experiments/grouped-ablation/`, `scripts/` returns nothing), so the
  amended example block (`viewer/RECORD.md:19-76`) is checked by reading only. That is how its
  `split` row can carry `"hit": false` (`viewer/RECORD.md:41`) beside a `parts` row saying
  `scratch.ablation.raw` is `preexisting: true` and unwritten (`viewer/RECORD.md:70`) while the
  rule two bullets down (`viewer/RECORD.md:104-107`) and both implementations
  (`viewer/adapters.js:258-265` `deriveHit`, `src/pyto/materialize.py:383`) make that read a hit,
  and `experiments/grouped-ablation/evidence/run-1/record.json` records `split` with `hit: true`.
  Owner decides whether the example should be extracted and run through both validators plus
  `deriveHit`/`derive_part_index` as a fixture, so the contract's illustration cannot drift from
  the contract's rules.
- {?} `declared_consumes` is enforced as a subset, stated as an equality (third verifier):
  `viewer/RECORD.md:83-84` says it is "exactly the `px:` bindings of `inputs`, in binding order",
  but what both validators check is spelling plus membership (`viewer/adapters.js:158-168`,
  `viewer/test/record_schema.py:192-199`) -- which `viewer/RECORD.md:85-86` states accurately, so
  the text is not false. The gap is that a producer may under-declare: a record with
  `inputs: {"raw": "px:a.b"}` and `declared_consumes: []` passes both validators, and
  `deriveHit` reads `declared_consumes`, so such a record loses a hit rather than a read (the
  part index survives because both readers union `inputs`). No producer in the tree does this
  today (all 15 invocations of `evidence/run-1/record.json` satisfy the equality; the three JS
  adapters build `inputs` from `declared` at `viewer/adapters.js:529-532,614,670`). Owner decides
  whether the validators should check equality and order, or whether RECORD.md should state the
  weaker rule the validators actually keep.
- {?} ViewerPin, after fix round 4 (unchanged, and the round's only blocker): fix round 4 added
  and removed no test, so `viewer` is still 87 pass / 0 fail
  (`node --test test/*.test.mjs` in `pyto/viewer`) against `scripts/check_all.sh:160`'s
  `EXPECT_VIEWER="${EXPECT_VIEWER:-83}"`, and the unaltered `bash pyto/scripts/check_all.sh`
  still ends `SOME SUITES FAILED` on `-- viewer: FAILED (expected exactly 83 tests, got 87)`
  and on nothing else (`EXPECT_VIEWER=87` ends `ALL SUITES PASSED`). The four unpinned tests
  are this pack's own: two array-truncation tests from fix round 2 and the two
  `declared_consumes` branch tests from fix round 3, all in `viewer/test/adapters.test.mjs`.
  The reconciling comment at `scripts/check_all.sh:152-159` still accounts for only 77+4+2=83.
  This pack is forbidden to edit `scripts/check_all.sh`, so the tree cannot be made to pass its
  own gate from inside the pack. Owner decides: bump the pin to 87 and extend the comment with
  the four tests, lift the no-edit rule for that file for count-pin lines, or move the
  per-suite count pins out of the file packs may not touch (a `scripts/expected-counts` data
  file the script reads would let a pack that adds tests update its own count).
- {?} The `hit` example bug the third verifier found is fixed in round 4
  (`viewer/RECORD.md:41` now reads `"hit": true`), but the reason it could exist is not: still
  no test in the tree reads `pyto/viewer/RECORD.md`, so the worked example remains prose that
  only a reader checks. That is the open `{?}` above about extracting the example as a fixture;
  round 4 corrected the instance, not the class.

- {?} `viewer/README.md:77` cites the wrong line for `materialize` (third verifier): the new
  "two caps" bullet added by this pack says ``materialize` (`adapters.js:254`)`, but
  `adapters.js:254` is inside `deriveHit`'s docblock ("invocation of the same run"); `export
  function materialize` is at `viewer/adapters.js:268`. Every other citation the bullet makes is
  correct -- `src/pyto/materialize.py:229-234` (serializability decided on the whole value) and
  `:236-239` (the note wording) both land exactly, and I confirmed the note is byte-identical
  across the runtimes. Owner decides whether this is a one-number fix or another instance of the
  stable-anchors question above.
- {?} ViewerPin, re-derived a third time (third verifier, independent run): unaltered
  `PYTHON=<venv> bash pyto/scripts/check_all.sh` ends `SOME SUITES FAILED` on exactly one line --
  `-- viewer: FAILED (expected exactly 83 tests, got 87)` (`scripts/check_all.sh:160`,
  `EXPECT_VIEWER="${EXPECT_VIEWER:-83}"`). library 106 OK, grouped-ablation 240 OK, s3-synthetic 5
  OK, consumer 61 OK, disc-stats 4 OK, examples 3 OK, art-registry-md OK, viewer-record-schema 19
  OK. The tree therefore does not pass its own gate as it stands. This is the same question the
  entries above raise; recorded once more only because it is the sole reason the pack is not green.
