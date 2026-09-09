# Task 20

Intent: Hiding primitives: a SUBDUE-style miner over the paint studio's call graphs finds the helper sequences that recur across the sixteen families, scores them by compression, and reports them beside what the JavaScript port extracted by hand; workshop only, no images, no kernel change
Starting point: a10b969df04891792ca8744f93174e8dd1c01f67 (checkpoint: {?} ResidueMining at the root (SUBDUE over the residue graph and over run records; residue count as the landable piece))
Verify: cd pyto/experiments/hiding-primitives && python3 -m unittest discover -s . -p 'test_*.py' && python3 mine.py --check
Allow: pyto/experiments/hiding-primitives pyto/experiments/tasks pyto/research/primary-sources.md
Candidate: 5 files, see below
Evidence: suite exit 0, see below

## Candidate

- A  pyto/experiments/hiding-primitives/graphs.py
- A  pyto/experiments/hiding-primitives/mine.py
- A  pyto/experiments/hiding-primitives/report.md
- A  pyto/experiments/hiding-primitives/subdue.py
- A  pyto/experiments/hiding-primitives/test_mine.py

```
pyto/experiments/hiding-primitives/graphs.py    | 194 ++++++++++++++++++++++++
 pyto/experiments/hiding-primitives/mine.py      | 130 ++++++++++++++++
 pyto/experiments/hiding-primitives/report.md    |  81 ++++++++++
 pyto/experiments/hiding-primitives/subdue.py    | 179 ++++++++++++++++++++++
 pyto/experiments/hiding-primitives/test_mine.py | 122 +++++++++++++++
 5 files changed, 706 insertions(+)
```

## Evidence

- verify: `cd pyto/experiments/hiding-primitives && python3 -m unittest discover -s . -p 'test_*.py' && python3 mine.py --check` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (evidence/check_all.txt)
    suite                         tests  status
    library                         144  OK
    experiments/cross-project         9  OK
    experiments/grouped-ablation    240  OK
    experiments/hiding-primitives      6  OK
    experiments/s3-synthetic          5  OK
    consumer                         61  OK
    disc-stats                        4  OK
    examples                          3  OK
    art-registry-md                   -  OK
    viewer                          103  OK
    viewer-record-schema             19  OK

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)
- {?} Nested functions: the brief names only `for` and `if` as control nodes, so a nested
  `def` (e.g. `paint_families.pressed_fern.frond`, paint_families.py:258) is not a node at
  all -- it becomes a graph of its own, keyed `module.outer.inner`, and the enclosing
  function keeps only the call node. The alternative was a third control label.
- {?} Comprehensions: a list/set/dict/generator comprehension is labelled `for`, the same
  label as a statement loop (graphs.py:80). It is a loop, but the brief listed only the two
  statement forms.
- {?} Card renderers: `art_registry.CARD_RENDERERS` (art_registry.py:395) maps kind and
  studio, not a slug, and `_card_*.py` are not among the paint studio sources named in the
  brief, so the 8 card renderers are outside the mined graph; only the 16 family slugs are in.
- {?} "Same callee set": read as `callees(S)` non-empty and contained in that port helper's
  studio spellings (mine.py:88, report.md "Beside the port"). Strict set equality matches
  nothing at all, because every mined substructure mixes a helper with something else -- which
  is itself the finding, but it would have left the whole column empty.
- {?} The port-helper alias table (mine.py:15-26) is hand-written: which Python callee each
  `core.mjs` export stands for cannot be derived from the two sources by name alone
  (`strokeFloor` is `stroke_for` and `_floor_width`; `fmt1` is an f-string spec and no call).
- {?} `core.mjs` const exports (SIZE, C, R, TARGETS, TAU, HEX at core.mjs:584-589) are not
  listed as helpers in the report: they are values, not extracted procedures.
- {?} `probe` (subdue.py:139): how many candidate substructures per beam level are re-matched
  and scored, ranked by a cheap extension count first. It is a fifth search argument the brief
  did not name; default 16.
- {?} One-instance compression: `subdue.py:105-107` says the fixed-width endpoint cost means a
  one-instance "substructure" cannot compress, but `compress` (subdue.py:97-102) also deletes
  instance-internal edges beyond `sub.edges` and drops merged/self external edges, and those bits
  are paid in neither DL(S) nor DL(G|S). On the real studio graph 20 of 166 one-instance
  two-vertex substructures score +13.5 bits, and a hand-built graph makes a one-instance
  substructure (27.0 bits) outrank a two-instance one of the same size (5.8 bits).
  `min_instances=2` (subdue.py:152) keeps this out of report.md; whether to narrow the docstring
  and the name `check_one_instance_does_not_pay` (test_mine.py:29) is the owner's call.
- {?} `strokeFloor` alias: mine.py:23 gives `strokeFloor` the studio spellings `stroke_for` and
  `_floor_width`, but `stroke_for` (_families_botanical.py:78-81) returns `max(source, round(...))`,
  which is core.mjs:613 `strokeText`; core.mjs:605 `strokeFloor` is `_floor_width`
  (_families_foundry.py:94-96) alone. Both rows read "not mined" either way, so no number moves.
- {?} `checkHex` at rank 14: rank 14 is `if ...: raise ValueError`, and only 3 of its 10 instances
  are hex guards (_families_botanical.py:53-54, _families_cartography.py:46-47,
  paint_families.py:50-51); the other 7 are target-range or unknown-family guards
  (_families_foundry.py:104-105, _families_signal.py:146-147, paint_components.py:30-31,
  paint_families.py:677-678, and the three target halves). It counts as a hit only because bare
  `ValueError` is in checkHex's spellings (mine.py:24); dropping it would make report.md:80 read
  "2 of its 22 helpers" and "17 of the 20".
- {?} `hex_color` (mine.py:24) never appears as a call anywhere in the mined graph -- a dead alias.
- {?} Refuter round, one-instance compression: settled by charging, not by narrowing the claim.
  `score` (subdue.py:122-123) now adds `lost = len(edges) - len(small_edges) - len(instances) *
  len(sub.edges)` -- every edge `compress` destroys beyond the ones `sub` accounts for -- to the
  edge count of DL(G|S), so DL(S) + DL(G|S) accounts for all of G and the per-edge cost cancels.
  The refuter's counterexample now scores -4.170 for the one-instance substructure against +5.807
  for the two-instance one; on the studio graph 0 of 166 one-instance two-vertex substructures
  score > 0 (was 20), and a 4000-graph random sweep finds 0 positives and 0 outrankings (was 3644
  and 217). The docstring at subdue.py:107-112 states the mechanism; `check_one_instance_does_not_pay`
  (test_mine.py:29-46) now also asserts the extra-internal-edge case, and a new mutation
  `dropped-edges-uncharged` (test_mine.py:62-64) reverts `lost` to 0 and is killed by it. The bits
  in report.md all moved (rank 2's 1320.4 is gone with the substructure that earned it), and the
  mined order changed; the owner may prefer the cheaper option of narrowing the docstring instead
  and keeping the old numbers.
- {?} Refuter round, checkHex: bare `ValueError` and dead `hex_color` dropped from the alias table
  (mine.py:28), so `checkHex` reads `_check, _guard, fullmatch` and now prints "not mined"; the
  guard composition `if ...: raise ValueError` survives as an unnamed mined substructure (report.md
  rank 12). The headline moved from "3 of its 22 helpers / 16 of the 20" to "2 of its 22 / 17 of
  the 20". No alias in the table is dead now: every name in PORT_PY resolves to a call node.
- {?} Refuter round, strokeFloor alias: `stroke_for` moved to `strokeText` (mine.py:26-27), since
  _families_botanical.py:78-81 is `max(source, round(...))` = core.mjs:613 and
  _families_foundry.py:94-96 is the bare floor = core.mjs:605. Both rows still read "not mined",
  so no count moved.
- {?} Whether charging every dropped edge at full price is the right code: it is an upper bound, not
  the tightest one -- merged-duplicate and self-loop external edges could in principle be recovered
  from the instance membership more cheaply. The bound is enough for "one instance cannot compress",
  which is what the docstring claims; a tighter accounting would raise every reported bits figure.
- {?} Refuter round 2, `PyRandom` is a use and not the helper: report.md's "Beside the port" gives
  `PyRandom` ranks 4 and 16, but rank 4 is `uniform/2 -next-> uniform/2` (two consecutive draws,
  _families_botanical.py:474-475) and rank 16 is `random.Random/1 -next-> SUB4` (the seeding line
  plus that pair, _families_botanical.py:473-475). Neither substructure *is* the class core.mjs:25
  exports; each is a composition over two of its methods, and it counts as a hit only because
  mine.py:88 reads correspondence as `callees(S) <= alts` (the "same callee set" {?} above). Under a
  strict "the substructure is that helper" reading only `pyRoundInt` survives, and report.md:80 would
  read "1 of its 22 helpers / 18 of the 20". The looser count is conservative against the report's own
  thesis, so nothing is overstated in the direction of the claim; the owner may still want the
  sentence to say "answers to" rather than "come back as".
- {?} Refuter round 2, `bits` is not comparable across ranks: `mine` (subdue.py:159-171) scores each
  round against the graph the previous round already compressed, so report.md's bits column is not
  monotone (rank 8's 529.0 above rank 7's 528.8, rank 10's 469.4 above rank 9's 410.2, rank 20's 350.3
  above ranks 12-19) and "rank" is round order, not a bits ordering. The table does not claim otherwise,
  but one column of bits invites the comparison.
- {?} Refuter round 2, twenty is the cap and not convergence: `PARAMS` (mine.py:12) sets
  `iterations=20` and `subdue.mine` (subdue.py:163) only breaks early when the best round scores <= 0,
  which never happens here -- `collect(iterations=25)` returns 25 rows (rank 21 `<linearGradient>,
  <stop>, <stop>`, ..., rank 25 `<path>, SUB10, _stroke/3+`). So "17 of the 20 mined substructures"
  (report.md:80) counts a truncated list, and rank 24 (`SUB4 -next-> uniform/2`, callees `{uniform}`)
  would be a third `PyRandom` row if the cap moved. The parameter is printed in report.md:3, so nothing
  is hidden; whether the headline should name the cap is the owner's call.
