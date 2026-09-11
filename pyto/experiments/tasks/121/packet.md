# Task 121

Intent: renumber the invented Stages to the owner's S4-S7: the nearest-anchor hole assembly becomes the HolesByNearestAnchor fallback, the course graph and the A* round become S7 Pathfinding, and S4/S5/S6 are freed for recovery, the tee-to-badge ray and the straight holes
Starting point: b83025b8e686ff8c61585ab351a86d7e1d9e1c53 (land(task-119): S6 Round: a deterministic search over S5's walkable cells from each tee to its basket and on to the next tee, legs that never cross an obstacle cell, unreachable reported rather than straightened, and the difference from the straight-leg route as a Part)
Verify: node --test tests/*.test.js
Allow: src/lab tests pyto/experiments/tasks
Candidate: not packed yet
Evidence: not packed yet

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)
