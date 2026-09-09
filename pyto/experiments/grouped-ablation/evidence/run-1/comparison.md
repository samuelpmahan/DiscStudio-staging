# Grouped ablation, seed=7 n=400 (synthetic-fixture)

Leave-one-group-out over 5 groups x 3 features; baseline `all` keeps every column.
Rank 1 is the largest RMSE increase when the group is dropped.

| rank | variant | rmse | delta vs all | planted |w| in group |
|---:|---|---:|---:|---:|
| 1 | drop_g3 | 1.9097 | +1.5896 | 2.0 |
| 2 | drop_g0 | 1.5468 | +1.2267 | 1.5 |
| 3 | drop_g1 | 0.9603 | +0.6402 | 0.8 |
| 4 | all | 0.3201 | +0.0000 | 4.3 |
| 5 | drop_g4 | 0.3194 | -0.0007 | 0.0 |
| 6 | drop_g2 | 0.3170 | -0.0031 | 0.0 |

Ranking (ablations only): drop_g3 > drop_g0 > drop_g1 > drop_g4 > drop_g2
