# Task 89

Intent: brain ml trees: cart with gini/entropy/squared-error and two split searches (every midpoint by sorting, and equal-width histogram bins), a small bootstrapped random forest with seeded feature subsets, small gradient boosting on squared loss, learning curves as Parts, oracles against hand-built trees and scipy, and the split-search tournament with its criteria recorded before judging
Starting point: a9f3476abcdca3c49000fb6ebc0092715cf5e958 (land(task-84): brain/stats distributions and hypothesis tests as Calculations fn.brain.stats.*: normal t chi2 binomial poisson pdf/pmf cdf ppf in pure python and scipy backends plus oc.brain.stats.sample through the effects handle's random; one-sample two-sample and paired t tests, chi-square test of independence and goodness of fit, one-way anova, mann-whitney u, shapiro-wilk; scipy.stats named as the reference for every one)
Verify: cd pyto && python -m unittest discover -s experiments/brain -p "test_*.py"
Allow: pyto/experiments/brain pyto/experiments/tasks
Candidate: not packed yet
Evidence: not packed yet

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)
