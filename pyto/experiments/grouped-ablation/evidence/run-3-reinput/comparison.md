# Grouped ablation, second input, seed=11 n=800

Leave-one-group-out over 5 groups x 3 features; baseline `all` keeps every column.
Rank 1 is the largest RMSE increase when the group is dropped.

| rank | variant | rmse | delta vs baseline | planted |w| in group |
|---:|---|---:|---:|---:|
| 1 | drop_g3 | 2.1566 | +1.8336 | 2.0 |
| 2 | drop_g0 | 1.6213 | +1.2983 | 1.5 |
| 3 | drop_g1 | 0.8337 | +0.5107 | 0.8 |
| 4 | all | 0.3230 | +0.0000 | 4.3 |
| 5 | drop_g2 | 0.3215 | -0.0014 | 0.0 |
| 6 | drop_g4 | 0.3212 | -0.0018 | 0.0 |

Ranking (ablations only): drop_g3 > drop_g0 > drop_g1 > drop_g2 > drop_g4
