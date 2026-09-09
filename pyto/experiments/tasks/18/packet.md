# Task 18

Intent: four worlds, one terminal: one page opens the ChainSpot, ChessLab, Wumpus, DiscStudio and pyto records side by side with a picker, the same tick page for every runtime, playback included
Starting point: e1e888ae343112999e43016ddd3287f64f618506 (land(task-16): watch it think: the tick page plays a record Tick by Tick with play, pause and step, each Calculation's reads, writes and value appearing when it finished, at recorded speed or slower)
Verify: node --test pyto/viewer/test/*.test.mjs
Allow: pyto/viewer pyto/viewer/test
Candidate: 6 files, see below
Evidence: suite exit 0, see below

## Candidate

- M  pyto/viewer/README.md
- M  pyto/viewer/embed.mjs
- M  pyto/viewer/test/embed.test.mjs
- M  pyto/viewer/test/render.test.mjs
- M  pyto/viewer/tick-viewer.html
- M  pyto/viewer/tick-viewer.js

```
pyto/viewer/README.md            | 14 +++++-
 pyto/viewer/embed.mjs            | 78 ++++++++++++++++++++++++++++++---
 pyto/viewer/test/embed.test.mjs  | 94 ++++++++++++++++++++++++++++++++++++++--
 pyto/viewer/test/render.test.mjs | 28 +++++++++++-
 pyto/viewer/tick-viewer.html     | 14 ++++++
 pyto/viewer/tick-viewer.js       | 72 +++++++++++++++++++++++++++++-
 6 files changed, 287 insertions(+), 13 deletions(-)
```

## Evidence

- verify: `node --test pyto/viewer/test/*.test.mjs` exit 0 (evidence/verify.txt)
- suite: `bash pyto/scripts/check_all.sh` exit 0, last line: ALL SUITES PASSED (evidence/check_all.txt)
    suite                         tests  status
    library                         144  OK
    experiments/grouped-ablation    240  OK
    experiments/s3-synthetic          5  OK
    consumer                         61  OK
    disc-stats                        4  OK
    examples                          3  OK
    art-registry-md                   -  OK
    viewer                          103  OK
    viewer-record-schema             19  OK
    
    ALL SUITES PASSED

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)

{?} Picker widget: built the world picker as a single `<select id="world">` in the toolbar rather than a tab strip, since it stays dependency-free and legible with six-plus worlds; a tab row (as the task text also allowed) would read better with only two or three, but scales worse. Worth revisiting if the owner wants worlds to feel more like distinct "screens".
{?} Label format: labelled a working world `${pcr} · ${source.runtime}` (e.g. `ablation.grouped · pyto`) and a failed one by its filename with the extension stripped (e.g. `garbled`). Reasonable, but arbitrary — no existing convention in RECORD.md or the viewer fixes this spelling.
{?} UNKNOWN convention: the viewer had no existing panel literally named "UNKNOWN" to mirror — the closest precedent is `say()`'s `status error` styling and `validate()`'s thrown, path-naming `RecordSchemaError`. I built `renderUnknown` to reuse that same CSS class and put the raw validator message in the panel. If the owner had a different "loud failure" convention in mind (e.g. from another part of the OS reframing), this may not be it.
{?} Playback-bar `[hidden]` CSS gap: found and fixed a pre-existing bug (not introduced by this task) where `.playback-bar { display: flex }` always overrides the `hidden` attribute's UA `display: none`, because an author rule beats a user-agent rule regardless of specificity — so toggling `bar.hidden = true` (both the existing single-record "Watch it think" off-switch and the new `forceOff()`) never visually hid the bar. Added `.playback-bar[hidden] { display: none; }` in `tick-viewer.html` to fix it, since it directly undermines "a picker switch ... must reset playback state" being visible. Flagging in case the owner wants this split into its own change instead of riding along here.
{?} Fifth world / "four worlds": the packet's Intent line names five records (ChainSpot, ChessLab, Wumpus, DiscStudio, pyto) under a title that says "four" — I read ChainSpot as the founding, still-unadapted world (no fixture, no adapter) and the other four as the ones actually rendered, which is why `--worlds` bakes those four fixtures' five records (pyto has two fixtures) plus ChainSpot as the labelled empty slot. If "four worlds" was meant literally, one of the five should probably be dropped instead.
