# Task 14

Intent: determinism log oracle survives a different interpreter: the log keeps naming its Python, the comparison normalizes the version and skips by name when the hash algorithm differs
Starting point: 76bc3d2a51c0e5442a0e4e8f519fe7d01484e9f5 (land(task-11): Mounts: a world (a course, a game, a bag) is mounted above an ordinary PxC by an id outside the address space, so one address means the same thing in every world; ported from ChainSpot's PxCRootMounts with its negative test)
Verify: cd pyto/experiments/grouped-ablation && python -m unittest test_replay.DeterminismMatrix -q
Allow: pyto/experiments/grouped-ablation/test_replay.py pyto/experiments/grouped-ablation/replay.py
Candidate: not packed yet
Evidence: not packed yet

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)
