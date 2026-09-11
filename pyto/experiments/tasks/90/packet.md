# Task 90

Intent: brain/stats regression, intervals and effect sizes: OLS by three solvers that are the candidates of a tournament (normal equations, householder QR, numpy lstsq) behind one facade with standard errors, t and F, R2 and adjusted R2; ridge with the intercept unpenalised; logistic by IRLS and by gradient descent; t, welch, wilson and chi-square confidence intervals; oc.brain.stats.bootstrap that resamples through the effects handle so a record replays to the same interval; cohen's d, hedges' g, glass's delta, eta and omega squared, cramer's v and the rank-biserial correlation
Starting point: a9f3476abcdca3c49000fb6ebc0092715cf5e958 (land(task-84): brain/stats distributions and hypothesis tests as Calculations fn.brain.stats.*: normal t chi2 binomial poisson pdf/pmf cdf ppf in pure python and scipy backends plus oc.brain.stats.sample through the effects handle's random; one-sample two-sample and paired t tests, chi-square test of independence and goodness of fit, one-way anova, mann-whitney u, shapiro-wilk; scipy.stats named as the reference for every one)
Verify: cd pyto && python -m unittest discover -s experiments/brain -p 'test_*.py'
Allow: pyto/experiments/brain pyto/experiments/tasks
Candidate: not packed yet
Evidence: not packed yet

## Uncertain

(The agent working on this writes one line per thing it was unsure about, as
`{?} Label: description`, and leaves the decision to the owner. Empty means nothing was unsure.)
