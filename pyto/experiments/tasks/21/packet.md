# Task 21

Intent: The studio exports its own run record: an Export run record action produces a pyto-run-record@1 JSON for the current composition through the existing adapter, and a link opens the Tick render page with that record embedded; no new state store, no renderer fork, no field whitelist
Starting point: 7d2448de2e38568967ca14fc8f1a722da7cd7b5d (land(task-0): Day 3 close-out: the record contract says what both runtimes do (declared_consumes, nested array cap), run_cached derives hit or miss from counters, viewer and materializer agree on every fixture)
Verify: npm test && node --test pyto/viewer/test/*.test.mjs && python3 scripts/browser_test.py --embedded
Allow: src/runtime.js src/app.js src/review.js src/review-data.js tests scripts/browser_test.py pyto/viewer/adapters.js pyto/viewer/embed.mjs .neat/items pyto/experiments/tasks
Candidate: not packed yet
Evidence: not packed yet

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)

{?} RunRecordAddress: the record is kept at `px.run.<pcr>` (the reserved `run` second segment, pyto/BOARD.md:135-136), so a second export of the same composition replaces the first; if one document per execution must be retained, the address needs a run-id segment.
{?} ReviewCheckpointCount: scripts/review_checkpoint.mjs:8 hardcodes `browser.count !== 9` and that file is outside this task's allowed set, so the CI review-checkpoint gate rejects the now ten-check browser report until that number is raised.
{?} DistMissesTheViewer: scripts/build.mjs:7 (outside this task's allowed set) copies src/, public/, concept-b/, index.html and docs/, so pyto/viewer/ is absent from dist/, and because src/app.js and src/runtime.js now import it directly a deployed build does not load at all until that copy list gains pyto/viewer/.
{?} EmbeddedHarnessOrigin: tests/embedded_harness.py (outside the allowed set) mounts the app on about:blank, where no relative URL resolves and the viewer sources cannot be fetched, so scripts/browser_test.py --embedded runs the new run-record block on a real local origin (Python stdlib server) and opens the produced page over file://.
{?} ChromiumPath: scripts/browser_test.py --embedded launched /usr/bin/chromium, which does not exist in this worktree; it now prefers /opt/pw-browsers/chromium and falls back to the old path.
{?} EmbedTopLevelAwait: pyto/viewer/embed.mjs now loads node:fs/node:path/node:url behind a top-level `await import()` guarded on `process.versions.node`, so the same module imports in the browser; the CLI and buildPage/embedFile signatures are unchanged.
