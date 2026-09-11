# Task 97

Intent: brain/stats and brain/data, the third wave: kruskal-wallis, levene and bartlett, the exact binomial test and fisher exact on a 2x2, and the multiple-comparison corrections (bonferroni, holm, benjamini-hochberg) as Calculations with scipy named as the reference; and the column transforms a real pipeline needs: standardise, normalise, rank and bin a column, crosstab two, drop duplicates, concatenate two tables, flag outliers by IQR and by z-score, and oc.brain.data.sample which draws its rows through the effects handle
Starting point: e755e1ab96998f1a3b2b580500fe9e50bfc6e094 (board: **started** `task-96`: brain/backend five more ops, one of them the brac)
Verify: cd pyto && python -m unittest discover -s experiments/brain -p 'test_*.py'
Allow: pyto/experiments/brain pyto/experiments/tasks
Candidate: not packed yet
Evidence: not packed yet

## Uncertain

{?} Two stacks, not one: evidence/verify-py312.txt is the same suite on python 3.12.3 + numpy
2.5.3 + scipy 1.18.1 as well as the copy's own venv. Every stats and data test passes on both.
The three failures that stack shows (backend.test_ops eig, backend.test_tournament gram,
ml.test_store saved-document) are in other verticals and were already there.
{?} Committed documents: store/stats.json and store/data.json are written through a
canonicalisation that rounds every float to twelve significant digits (stats.tolerance.canonical,
data.table.canonical), so a fresh build on another BLAS saves the same document. The wall-clock
fields of a benchmark Part are a measurement of this machine and are not expected to reproduce.

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)
