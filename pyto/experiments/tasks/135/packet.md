# Task 135

Intent: constraints defining DiscComp: a battle is composed from reusable Constraints with parameters (discCap, placesPoints, tieRule) the way a competition is, scoring is one Calculation over the battle's states with a receipt (ranks, points, a running total), and the UX for a 5-disc cap battle where the top 3 score 3,2,1 is pick the template, add discs against the cap, tap the order Also carries the review item Boone (the AI PM) raised for the vertical frame, worded for the orientation control task 133 landed ('frame': Landscape and vertical export frames, on the OnTheCourse inspector).
Starting point: bbcf4dc374ee3aa50d76b2c5d1e557e8f64b7e10 (land(task-133): vertical content: a 1080x1920 portrait canvas beside the 1920x1080 one, composed by the same fn.comparison.layout, plus a reusable frame preset (fill, safe area, title strip, sponsor lockup on the cards cascade's global tokens) materialized by the same fn.overlay.svg, and exports that honour the orientation)
Verify: npm test
Allow: src index.html tests scripts/browser_test.py scripts/demo_beats.py pyto/experiments/tasks
Candidate: not packed yet
Evidence: not packed yet

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)

{?} HarnessWasExponential: tests/embedded_harness.py inlined every module's data: URL into its
parent, once per import edge, so one source byte in a diamond like src/domain.js was mounted dozens of
times: 48 modules totalling ~1 MB of source were reaching the browser as a single 32 MB data: URL, and
this slice's one extra import into domain.js was enough to crash the renderer ("Target crashed" on the
first pointer drag, three runs in a row, on an otherwise idle machine). The harness now mounts each
module once and resolves `mod:<path>` specifiers through an import map: 1.03 MB instead of 32 MB, and
the whole browser suite runs in about a minute instead of ten. Anything that reads the shape of the
mounted page (rather than the app) should know it changed.

{?} EntryIsAPart: a card's BattleEntry is now published by `fn.battle.entry`, and `fn.domain.fields`
takes it as a second input so the values a card shows come from that Part. The material Part still
carries `roots.entry` with a null record beside it -- two ways to say "this card's entry", one now
vestigial. A root that could name an address instead of carrying a record would remove the second and
make the material state-independent outright.

{?} OneBattleTwoReceipts: the battle's Constraints run as their own composition (`discomp`) and its
standings run inside `on-the-course`; both read `px.battle.material`, and the memo makes the second
free. But "one battle, two receipts" is a shape the board has no word for. A composition that could
declare it consumes another composition's produce -- rather than re-deriving it -- would be one.

{?} TieShareRounding: `tieRule: share` averages the tied places' points and rounds to two decimals, so
3,2,1 shared over two places puts 2.5 on a card. Integers with a stated rounding rule, or fractions on
screen, is the owner's call; the Constraint has the parameter either way.
