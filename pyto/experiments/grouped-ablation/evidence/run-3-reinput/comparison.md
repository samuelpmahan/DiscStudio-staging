# Grouped ablation, second input, seed=11 n=800

Leave-one-group-out over 5 groups x 3 features; baseline `all` keeps every column.
Rank 1 is the largest RMSE increase when the group is dropped.

| rank | variant | rmse | delta vs baseline | planted |w| in group |
|---:|---|---:|---:|---:|
| 1 | drop_g3 | 2.0205 | +1.7219 | 2.0 |
| 2 | drop_g0 | 1.6220 | +1.3234 | 1.5 |
| 3 | drop_g1 | 0.8170 | +0.5184 | 0.8 |
| 4 | drop_g4 | 0.2996 | +0.0010 | 0.0 |
| 5 | drop_g2 | 0.2989 | +0.0002 | 0.0 |
| 6 | all | 0.2986 | +0.0000 | 4.3 |

Ranking (ablations only): drop_g3 > drop_g0 > drop_g1 > drop_g4 > drop_g2
