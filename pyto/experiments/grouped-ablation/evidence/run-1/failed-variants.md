# Failed / uninformative variants

A variant is uninformative when |delta vs all| < 0.05. These are retained,
not dropped: an ablation that changes nothing is evidence about the fixture, not noise to hide.

- `drop_g2`: delta +0.0005; planted |w| in g2 = 0.0. Interpretation: the group carries no planted weight (features.py TRUE_W), so removing its three columns cannot raise test RMSE; any nonzero delta is ridge/OLS fit noise on 100 test rows, and a small negative delta means the dropped columns were only fitting noise. The variant is a control, not a failure of the method.
- `drop_g4`: delta +0.0002; planted |w| in g4 = 0.0. Interpretation: the group carries no planted weight (features.py TRUE_W), so removing its three columns cannot raise test RMSE; any nonzero delta is ridge/OLS fit noise on 100 test rows, and a small negative delta means the dropped columns were only fitting noise. The variant is a control, not a failure of the method.
