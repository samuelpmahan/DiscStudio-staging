# Task 105

Intent: brain ml out-of-bag: a random forest scores itself on the rows each of its trees never saw, so a held-out number comes free with the fit; the bag each tree drew is recorded, oob_predict votes only the trees that missed a row, and the oob score is oracled against a real held-out split
Starting point: f8f15fa059e4aae8247fac2c52e7685806cf127c (board: **started** `task-104`: brain/stats and brain/data, closing two named st)
Verify: cd pyto && python -m unittest discover -s experiments/brain -p "test_*.py"
Allow: pyto/experiments/brain pyto/experiments/tasks
Candidate: not packed yet
Evidence: not packed yet

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)
