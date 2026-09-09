# Grouped ablation, cross-cutting 3x5 regroup, seed=7 n=400

Leave-one-group-out over 3 groups x 5 features; baseline `all` keeps every column.
Rank 1 is the largest RMSE increase when the group is dropped.

| rank | variant | rmse | delta vs baseline | planted |w| in group |
|---:|---|---:|---:|---:|
| 1 | drop_h2 | 2.1539 | +1.8503 | 2.0 |
| 2 | drop_h0 | 1.6595 | +1.3559 | 1.5 |
| 3 | drop_h1 | 0.8455 | +0.5419 | 0.8 |
| 4 | all | 0.3036 | +0.0000 | 4.3 |

Ranking (ablations only): drop_h2 > drop_h0 > drop_h1
