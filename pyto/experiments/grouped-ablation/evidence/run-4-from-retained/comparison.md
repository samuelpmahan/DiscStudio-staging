# Grouped ablation, split reused from run-1's retained record, seed=7 n=400

Leave-one-group-out over 5 groups x 3 features; baseline `all` keeps every column.
Rank 1 is the largest RMSE increase when the group is dropped.

| rank | variant | rmse | delta vs baseline | planted |w| in group |
|---:|---|---:|---:|---:|
| 1 | drop_g3 | 2.1689 | +1.8653 | 2.0 |
| 2 | drop_g0 | 1.6896 | +1.3860 | 1.5 |
| 3 | drop_g1 | 0.8491 | +0.5455 | 0.8 |
| 4 | drop_g2 | 0.3041 | +0.0005 | 0.0 |
| 5 | drop_g4 | 0.3038 | +0.0002 | 0.0 |
| 6 | all | 0.3036 | +0.0000 | 4.3 |

Ranking (ablations only): drop_g3 > drop_g0 > drop_g1 > drop_g2 > drop_g4
