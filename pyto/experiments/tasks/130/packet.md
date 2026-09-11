# Task 130

Intent: every disc looked the same: the painter port (2026-09-09) replaced the per-disc hue with one fixed base and accent for every disc that has no authored art colours, so twelve discs painted one wind-rose in one grey-green; a disc's sample hue is its colours again (base and accent derived from sampleHue when artBase/artAccent are not authored, exactly the original prepareDiscArt's rule), the sanitised-colour test expects the disc's own defaults, and the two art-bearing fixtures are regenerated from the real runtime
Starting point: 50746348e4094e3ee1e374399019fff15130b966 (land(task-129): the wedge: the Course route off the demo path, and the tease-then-razzle storyboard as a test that screenshots every beat)
Verify: npm test
Allow: src tests pyto/viewer/fixtures pyto/viewer/test pyto/experiments/tasks
Candidate: not packed yet
Evidence: not packed yet

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)
