# Molecules: SUBDUE over the run records

A molecule is a repeated chain of Calculations over Parts: a substructure of the run graph (invocations, the Parts they read and write, and the declared order inside a Tick) that occurs at least twice, vertex-disjoint, and pays for itself under minimum description length -- the graph plus the substructure is fewer bits than the graph alone.  It is what "molecular synthesis" names ({?} ChainsInsideATick): the unit a program keeps re-composing, mined rather than declared.  Each is spelled as SUBDUE's canonical form, as a PQL document that runs the first instance as one Tick of chained Calculations in declared order (the chain rule of task 57 is checked on every emission), and as a PQL query that finds its Parts in a store.  Miner: `experiments/hiding-primitives/subdue.py` with `beam=4, iterations=8, max_size=5, min_instances=2`.  Rebuild with `python mine.py`; `--check` fails if this file drifts.

## Transitions

Counting before mining ({?} ChainsInsideATick): every (from, kind, to) edge the exact scheme draws over every record below, tallied once by `fn.molecules.transitions` before any SUBDUE search looks for one repeated -- published as `px.exp.molecules.transitions`.  165 edges, 78 distinct, top 30 shown.

| from | kind | to | count |
| --- | --- | --- | ---: |
| `scratch.ablation.split` | reads | `fn.ablation.fit` | 14 |
| `scratch.ablation.split` | reads | `fn.ablation.score` | 14 |
| `fn.ablation.fit` | next | `fn.ablation.fit` | 10 |
| `fn.ablation.score` | next | `fn.ablation.score` | 10 |
| `fn.ablation.compare` | writes | `scratch.ablation.comparison` | 3 |
| `fn.ablation.fit` | writes | `scratch.ablation.model.all` | 3 |
| `fn.ablation.fit` | writes | `scratch.ablation.model.drop_g3` | 3 |
| `fn.ablation.score` | writes | `scratch.ablation.score.all` | 3 |
| `fn.ablation.score` | writes | `scratch.ablation.score.drop_g3` | 3 |
| `fn.ablation.selectVariants` | next | `fn.ablation.split` | 3 |
| `fn.ablation.selectVariants` | writes | `scratch.ablation.variants` | 3 |
| `fn.ablation.split` | writes | `scratch.ablation.split` | 3 |
| `input.ablation.groups` | reads | `fn.ablation.selectVariants` | 3 |
| `input.ablation.rows` | reads | `fn.ablation.split` | 3 |
| `scratch.ablation.model.all` | reads | `fn.ablation.score` | 3 |
| `scratch.ablation.model.drop_g3` | reads | `fn.ablation.score` | 3 |
| `fn.ablation.fit` | next | `fn.ablation.score` | 2 |
| `fn.ablation.fit` | writes | `scratch.ablation.model.drop_g0` | 2 |
| `fn.ablation.fit` | writes | `scratch.ablation.model.drop_g1` | 2 |
| `fn.ablation.fit` | writes | `scratch.ablation.model.drop_g2` | 2 |
| `fn.ablation.fit` | writes | `scratch.ablation.model.drop_g4` | 2 |
| `fn.ablation.score` | writes | `scratch.ablation.score.drop_g0` | 2 |
| `fn.ablation.score` | writes | `scratch.ablation.score.drop_g1` | 2 |
| `fn.ablation.score` | writes | `scratch.ablation.score.drop_g2` | 2 |
| `fn.ablation.score` | writes | `scratch.ablation.score.drop_g4` | 2 |
| `scratch.ablation.model.drop_g0` | reads | `fn.ablation.score` | 2 |
| `scratch.ablation.model.drop_g1` | reads | `fn.ablation.score` | 2 |
| `scratch.ablation.model.drop_g2` | reads | `fn.ablation.score` | 2 |
| `scratch.ablation.model.drop_g4` | reads | `fn.ablation.score` | 2 |
| `scratch.ablation.score.all` | reads | `fn.ablation.compare` | 2 |

## Records

| record | nodes | edges | note |
| --- | ---: | ---: | --- |
| `experiments/students/evidence/run-1/record.json` | 11 | 11 |  |
| `experiments/grouped-ablation/evidence/run-1/record.json` | 32 | 52 |  |
| `tests/fixtures/use/order-record.json` | 6 | 5 |  |
| `viewer/fixtures/parallel-demo.json` | 9 | 10 |  |
| `viewer/fixtures/effects-demo.json` | 4 | 3 |  |
| `viewer/fixtures/pyto-grouped-ablation.json` | 32 | 52 |  |
| `viewer/fixtures/pyto-value-kinds.json` | 24 | 29 |  |
| `tests/fixtures/px/effects-record.json` | 4 | 3 |  |

## Scheme `exact` (122 nodes, 165 edges)

| rank | substructure | instances | rarest transition | records | bits | ratio |
| ---: | --- | ---: | ---: | --- | ---: | ---: |
| 1 | `v0=fn.ablation.fit, v1=fn.ablation.fit, v2=fn.ablation.score, v3=scratch.ablation.model.all, v4=scratch.ablation.split ; v0-writes->v3, v3-reads->v2, v4-reads->v0, v4-reads->v1` | 3 | 3 | `experiments/grouped-ablation/evidence/run-1/record.json`, `viewer/fixtures/pyto-grouped-ablation.json`, `viewer/fixtures/pyto-value-kinds.json` | 160.9 | 0.9512 |
| 2 | `v0=SUB1, v1=fn.ablation.score, v2=fn.ablation.selectVariants, v3=fn.ablation.split, v4=input.ablation.groups ; v0-next->v1, v2-next->v3, v3-writes->v0, v4-reads->v2` | 3 | 3 | `experiments/grouped-ablation/evidence/run-1/record.json`, `viewer/fixtures/pyto-grouped-ablation.json`, `viewer/fixtures/pyto-value-kinds.json` | 160.8 | 0.9451 |
| 3 | `v0=SUB2, v1=input.ablation.rows, v2=scratch.ablation.score.all, v3=scratch.ablation.variants ; v0-writes->v2, v0-writes->v3, v1-reads->v0` | 3 | 3 | `experiments/grouped-ablation/evidence/run-1/record.json`, `viewer/fixtures/pyto-grouped-ablation.json`, `viewer/fixtures/pyto-value-kinds.json` | 118.1 | 0.9548 |
| 4 | `v0=SUB3, v1=fn.ablation.compare, v2=fn.ablation.fit, v3=fn.ablation.fit, v4=fn.ablation.fit ; v0-reads->v1, v0-next->v2, v0-reads->v3, v0-reads->v4` | 2 | 2 | `experiments/grouped-ablation/evidence/run-1/record.json`, `viewer/fixtures/pyto-grouped-ablation.json` | 74.6 | 0.9691 |
| 5 | `v0=SUB4, v1=fn.ablation.fit, v2=fn.ablation.score, v3=fn.ablation.score, v4=fn.ablation.score ; v0-next->v1, v0-next->v2, v0-reads->v3, v0-reads->v4` | 2 | 2 | `experiments/grouped-ablation/evidence/run-1/record.json`, `viewer/fixtures/pyto-grouped-ablation.json` | 74.7 | 0.9653 |
| 6 | `v0=SUB5, v1=fn.ablation.score, v2=scratch.ablation.comparison, v3=scratch.ablation.model.drop_g0, v4=scratch.ablation.model.drop_g1 ; v0-next->v1, v0-writes->v2, v0-writes->v3, v0-writes->v4` | 2 | 2 | `experiments/grouped-ablation/evidence/run-1/record.json`, `viewer/fixtures/pyto-grouped-ablation.json` | 74.7 | 0.9598 |
| 7 | `v0=SUB6, v1=scratch.ablation.model.drop_g2, v2=scratch.ablation.model.drop_g3, v3=scratch.ablation.model.drop_g4, v4=scratch.ablation.score.drop_g0 ; v0-writes->v1, v0-writes->v2, v0-writes->v3, v0-writes->v4` | 2 | 2 | `experiments/grouped-ablation/evidence/run-1/record.json`, `viewer/fixtures/pyto-grouped-ablation.json` | 74.5 | 0.9532 |
| 8 | `v0=SUB7, v1=scratch.ablation.score.drop_g1, v2=scratch.ablation.score.drop_g2, v3=scratch.ablation.score.drop_g3, v4=scratch.ablation.score.drop_g4 ; v0-writes->v1, v0-writes->v2, v0-writes->v3, v0-writes->v4` | 2 | 2 | `experiments/grouped-ablation/evidence/run-1/record.json`, `viewer/fixtures/pyto-grouped-ablation.json` | 74.3 | 0.9425 |

### exact rank 1

- experiments/grouped-ablation/evidence/run-1/record.json [Fit, Score] fit.all, fit.drop_g0, score.all, scratch.ablation.model.all, scratch.ablation.split
- viewer/fixtures/pyto-grouped-ablation.json [Fit, Score] fit.all, fit.drop_g0, score.all, scratch.ablation.model.all, scratch.ablation.split
- viewer/fixtures/pyto-value-kinds.json [Fit] fit.all, fit.drop_g3, score.all, scratch.ablation.model.all, scratch.ablation.split

```json
{
  "Ticks": [
    {
      "name": "molecule-1",
      "Calculations": [
        {
          "call": "fn.ablation.fit",
          "with": {
            "split": "scratch.ablation.split"
          },
          "into": "scratch.ablation.model.all"
        },
        {
          "call": "fn.ablation.fit",
          "with": {
            "split": "scratch.ablation.split"
          },
          "into": "scratch.ablation.model.drop_g0"
        },
        {
          "call": "fn.ablation.score",
          "with": {
            "model": "scratch.ablation.model.all",
            "split": "scratch.ablation.split"
          },
          "into": "scratch.ablation.score.all"
        }
      ]
    }
  ]
}
```

Query: `PQL.prefix('scratch.ablation.')` -> `PQL('scratch.ablation.*')`

### exact rank 2

- experiments/grouped-ablation/evidence/run-1/record.json [Fit, Prepare, Score] select, split, fit.all, fit.drop_g0, score.all, score.drop_g0, input.ablation.groups, scratch.ablation.model.all, scratch.ablation.split
- viewer/fixtures/pyto-grouped-ablation.json [Fit, Prepare, Score] select, split, fit.all, fit.drop_g0, score.all, score.drop_g0, input.ablation.groups, scratch.ablation.model.all, scratch.ablation.split
- viewer/fixtures/pyto-value-kinds.json [Fit, Prepare] select, split, fit.all, score.all, fit.drop_g3, score.drop_g3, input.ablation.groups, scratch.ablation.model.all, scratch.ablation.split

compound: built on an earlier rank's SUB node; no document emitted

### exact rank 3

- experiments/grouped-ablation/evidence/run-1/record.json [Fit, Prepare, Score] select, split, fit.all, fit.drop_g0, score.all, score.drop_g0, input.ablation.groups, input.ablation.rows, scratch.ablation.model.all, scratch.ablation.score.all, scratch.ablation.split, scratch.ablation.variants
- viewer/fixtures/pyto-grouped-ablation.json [Fit, Prepare, Score] select, split, fit.all, fit.drop_g0, score.all, score.drop_g0, input.ablation.groups, input.ablation.rows, scratch.ablation.model.all, scratch.ablation.score.all, scratch.ablation.split, scratch.ablation.variants
- viewer/fixtures/pyto-value-kinds.json [Fit, Prepare] select, split, fit.all, score.all, fit.drop_g3, score.drop_g3, input.ablation.groups, input.ablation.rows, scratch.ablation.model.all, scratch.ablation.score.all, scratch.ablation.split, scratch.ablation.variants

compound: built on an earlier rank's SUB node; no document emitted

### exact rank 4

- experiments/grouped-ablation/evidence/run-1/record.json [Compare, Fit, Prepare, Score] select, split, fit.all, fit.drop_g0, fit.drop_g1, fit.drop_g2, fit.drop_g3, score.all, score.drop_g0, compare, input.ablation.groups, input.ablation.rows, scratch.ablation.model.all, scratch.ablation.score.all, scratch.ablation.split, scratch.ablation.variants
- viewer/fixtures/pyto-grouped-ablation.json [Compare, Fit, Prepare, Score] select, split, fit.all, fit.drop_g0, fit.drop_g1, fit.drop_g2, fit.drop_g3, score.all, score.drop_g0, compare, input.ablation.groups, input.ablation.rows, scratch.ablation.model.all, scratch.ablation.score.all, scratch.ablation.split, scratch.ablation.variants

compound: built on an earlier rank's SUB node; no document emitted

### exact rank 5

- experiments/grouped-ablation/evidence/run-1/record.json [Compare, Fit, Prepare, Score] select, split, fit.all, fit.drop_g0, fit.drop_g1, fit.drop_g2, fit.drop_g3, fit.drop_g4, score.all, score.drop_g0, score.drop_g1, score.drop_g2, score.drop_g3, compare, input.ablation.groups, input.ablation.rows, scratch.ablation.model.all, scratch.ablation.score.all, scratch.ablation.split, scratch.ablation.variants
- viewer/fixtures/pyto-grouped-ablation.json [Compare, Fit, Prepare, Score] select, split, fit.all, fit.drop_g0, fit.drop_g1, fit.drop_g2, fit.drop_g3, fit.drop_g4, score.all, score.drop_g0, score.drop_g1, score.drop_g2, score.drop_g3, compare, input.ablation.groups, input.ablation.rows, scratch.ablation.model.all, scratch.ablation.score.all, scratch.ablation.split, scratch.ablation.variants

compound: built on an earlier rank's SUB node; no document emitted

### exact rank 6

- experiments/grouped-ablation/evidence/run-1/record.json [Compare, Fit, Prepare, Score] select, split, fit.all, fit.drop_g0, fit.drop_g1, fit.drop_g2, fit.drop_g3, fit.drop_g4, score.all, score.drop_g0, score.drop_g1, score.drop_g2, score.drop_g3, score.drop_g4, compare, input.ablation.groups, input.ablation.rows, scratch.ablation.comparison, scratch.ablation.model.all, scratch.ablation.model.drop_g0, scratch.ablation.model.drop_g1, scratch.ablation.score.all, scratch.ablation.split, scratch.ablation.variants
- viewer/fixtures/pyto-grouped-ablation.json [Compare, Fit, Prepare, Score] select, split, fit.all, fit.drop_g0, fit.drop_g1, fit.drop_g2, fit.drop_g3, fit.drop_g4, score.all, score.drop_g0, score.drop_g1, score.drop_g2, score.drop_g3, score.drop_g4, compare, input.ablation.groups, input.ablation.rows, scratch.ablation.comparison, scratch.ablation.model.all, scratch.ablation.model.drop_g0, scratch.ablation.model.drop_g1, scratch.ablation.score.all, scratch.ablation.split, scratch.ablation.variants

compound: built on an earlier rank's SUB node; no document emitted

### exact rank 7

- experiments/grouped-ablation/evidence/run-1/record.json [Compare, Fit, Prepare, Score] select, split, fit.all, fit.drop_g0, fit.drop_g1, fit.drop_g2, fit.drop_g3, fit.drop_g4, score.all, score.drop_g0, score.drop_g1, score.drop_g2, score.drop_g3, score.drop_g4, compare, input.ablation.groups, input.ablation.rows, scratch.ablation.comparison, scratch.ablation.model.all, scratch.ablation.model.drop_g0, scratch.ablation.model.drop_g1, scratch.ablation.model.drop_g2, scratch.ablation.model.drop_g3, scratch.ablation.model.drop_g4, scratch.ablation.score.all, scratch.ablation.score.drop_g0, scratch.ablation.split, scratch.ablation.variants
- viewer/fixtures/pyto-grouped-ablation.json [Compare, Fit, Prepare, Score] select, split, fit.all, fit.drop_g0, fit.drop_g1, fit.drop_g2, fit.drop_g3, fit.drop_g4, score.all, score.drop_g0, score.drop_g1, score.drop_g2, score.drop_g3, score.drop_g4, compare, input.ablation.groups, input.ablation.rows, scratch.ablation.comparison, scratch.ablation.model.all, scratch.ablation.model.drop_g0, scratch.ablation.model.drop_g1, scratch.ablation.model.drop_g2, scratch.ablation.model.drop_g3, scratch.ablation.model.drop_g4, scratch.ablation.score.all, scratch.ablation.score.drop_g0, scratch.ablation.split, scratch.ablation.variants

compound: built on an earlier rank's SUB node; no document emitted

### exact rank 8

- experiments/grouped-ablation/evidence/run-1/record.json [Compare, Fit, Prepare, Score] select, split, fit.all, fit.drop_g0, fit.drop_g1, fit.drop_g2, fit.drop_g3, fit.drop_g4, score.all, score.drop_g0, score.drop_g1, score.drop_g2, score.drop_g3, score.drop_g4, compare, input.ablation.groups, input.ablation.rows, scratch.ablation.comparison, scratch.ablation.model.all, scratch.ablation.model.drop_g0, scratch.ablation.model.drop_g1, scratch.ablation.model.drop_g2, scratch.ablation.model.drop_g3, scratch.ablation.model.drop_g4, scratch.ablation.score.all, scratch.ablation.score.drop_g0, scratch.ablation.score.drop_g1, scratch.ablation.score.drop_g2, scratch.ablation.score.drop_g3, scratch.ablation.score.drop_g4, scratch.ablation.split, scratch.ablation.variants
- viewer/fixtures/pyto-grouped-ablation.json [Compare, Fit, Prepare, Score] select, split, fit.all, fit.drop_g0, fit.drop_g1, fit.drop_g2, fit.drop_g3, fit.drop_g4, score.all, score.drop_g0, score.drop_g1, score.drop_g2, score.drop_g3, score.drop_g4, compare, input.ablation.groups, input.ablation.rows, scratch.ablation.comparison, scratch.ablation.model.all, scratch.ablation.model.drop_g0, scratch.ablation.model.drop_g1, scratch.ablation.model.drop_g2, scratch.ablation.model.drop_g3, scratch.ablation.model.drop_g4, scratch.ablation.score.all, scratch.ablation.score.drop_g0, scratch.ablation.score.drop_g1, scratch.ablation.score.drop_g2, scratch.ablation.score.drop_g3, scratch.ablation.score.drop_g4, scratch.ablation.split, scratch.ablation.variants

compound: built on an earlier rank's SUB node; no document emitted

## Scheme `shape` (122 nodes, 165 edges)

| rank | substructure | instances | rarest transition | records | bits | ratio |
| ---: | --- | ---: | ---: | --- | ---: | ---: |
| 1 | `v0=fn/1->1, v1=fn/2->1, v2=part, v3=part ; v0-writes->v2, v1-writes->v3, v2-reads->v1` | 16 | 16 | `experiments/grouped-ablation/evidence/run-1/record.json`, `viewer/fixtures/parallel-demo.json`, `viewer/fixtures/pyto-grouped-ablation.json`, `viewer/fixtures/pyto-value-kinds.json` | 815.5 | 0.7193 |
| 2 | `v0=fn/1->1, v1=part, v2=part ; v0-writes->v1, v2-reads->v0` | 10 | 14 | `experiments/grouped-ablation/evidence/run-1/record.json`, `experiments/students/evidence/run-1/record.json`, `tests/fixtures/px/effects-record.json`, `tests/fixtures/use/order-record.json`, `viewer/fixtures/effects-demo.json`, `viewer/fixtures/parallel-demo.json`, `viewer/fixtures/pyto-grouped-ablation.json`, `viewer/fixtures/pyto-value-kinds.json` | 323.0 | 0.8104 |
| 3 | `v0=SUB1, v1=SUB1, v2=SUB2, v3=fn/1->1, v4=part ; v0-next->v1, v0-reads->v3, v2-next->v0, v3-writes->v4` | 3 | 3 | `experiments/grouped-ablation/evidence/run-1/record.json`, `viewer/fixtures/pyto-grouped-ablation.json`, `viewer/fixtures/pyto-value-kinds.json` | 140.3 | 0.8959 |
| 4 | `v0=SUB1, v1=SUB1, v2=SUB1, v3=SUB1, v4=SUB3 ; v0-next->v1, v1-next->v2, v2-next->v3, v4-next->v0` | 2 | 2 | `experiments/grouped-ablation/evidence/run-1/record.json`, `viewer/fixtures/pyto-grouped-ablation.json` | 66.9 | 0.9305 |
| 5 | `v0=fn/1->1, v1=part ; v0-writes->v1` | 4 | 4 | `experiments/students/evidence/run-1/record.json`, `viewer/fixtures/parallel-demo.json`, `viewer/fixtures/pyto-value-kinds.json` | 50.8 | 0.9111 |
| 6 | `v0=SUB1, v1=SUB2, v2=SUB5 ; v0-next->v2, v1-reads->v0` | 2 | 2 | `viewer/fixtures/parallel-demo.json`, `viewer/fixtures/pyto-value-kinds.json` | 31.2 | 0.9375 |
| 7 | `v0=SUB4, v1=fn/6->1, v2=part, v3=part ; v0-reads->v1, v1-writes->v2, v3-reads->v0` | 2 | 2 | `experiments/grouped-ablation/evidence/run-1/record.json`, `viewer/fixtures/pyto-grouped-ablation.json` | 49.8 | 0.8678 |
| 8 | `v0=SUB2, v1=oc/0->1 ; v1-writes->v0` | 2 | 2 | `tests/fixtures/px/effects-record.json`, `viewer/fixtures/effects-demo.json` | 13.2 | 0.9490 |

### shape rank 1

- experiments/grouped-ablation/evidence/run-1/record.json [Prepare, Score] split, score.all, scratch.ablation.split, scratch.ablation.score.all
- experiments/grouped-ablation/evidence/run-1/record.json [Fit, Score] fit.drop_g0, score.drop_g0, scratch.ablation.model.drop_g0, scratch.ablation.score.drop_g0
- experiments/grouped-ablation/evidence/run-1/record.json [Fit, Score] fit.drop_g1, score.drop_g1, scratch.ablation.model.drop_g1, scratch.ablation.score.drop_g1
- experiments/grouped-ablation/evidence/run-1/record.json [Fit, Score] fit.drop_g2, score.drop_g2, scratch.ablation.model.drop_g2, scratch.ablation.score.drop_g2
- experiments/grouped-ablation/evidence/run-1/record.json [Fit, Score] fit.drop_g3, score.drop_g3, scratch.ablation.model.drop_g3, scratch.ablation.score.drop_g3
- experiments/grouped-ablation/evidence/run-1/record.json [Fit, Score] fit.drop_g4, score.drop_g4, scratch.ablation.model.drop_g4, scratch.ablation.score.drop_g4
- viewer/fixtures/parallel-demo.json [Fan, Score] left, score, px.demo.left, px.demo.score
- viewer/fixtures/pyto-grouped-ablation.json [Prepare, Score] split, score.all, scratch.ablation.split, scratch.ablation.score.all
- viewer/fixtures/pyto-grouped-ablation.json [Fit, Score] fit.drop_g0, score.drop_g0, scratch.ablation.model.drop_g0, scratch.ablation.score.drop_g0
- viewer/fixtures/pyto-grouped-ablation.json [Fit, Score] fit.drop_g1, score.drop_g1, scratch.ablation.model.drop_g1, scratch.ablation.score.drop_g1
- viewer/fixtures/pyto-grouped-ablation.json [Fit, Score] fit.drop_g2, score.drop_g2, scratch.ablation.model.drop_g2, scratch.ablation.score.drop_g2
- viewer/fixtures/pyto-grouped-ablation.json [Fit, Score] fit.drop_g3, score.drop_g3, scratch.ablation.model.drop_g3, scratch.ablation.score.drop_g3
- viewer/fixtures/pyto-grouped-ablation.json [Fit, Score] fit.drop_g4, score.drop_g4, scratch.ablation.model.drop_g4, scratch.ablation.score.drop_g4
- viewer/fixtures/pyto-value-kinds.json [Fit, Prepare] split, score.all, scratch.ablation.split, scratch.ablation.score.all
- viewer/fixtures/pyto-value-kinds.json [Fit] fit.drop_g3, score.drop_g3, scratch.ablation.model.drop_g3, scratch.ablation.score.drop_g3
- viewer/fixtures/pyto-value-kinds.json [Materialize, Retain] sheet, retain, scratch.ablation.sheet, scratch.ablation.retained

```json
{
  "Ticks": [
    {
      "name": "molecule-1",
      "Calculations": [
        {
          "call": "fn.ablation.split",
          "with": {
            "rows": "input.ablation.rows"
          },
          "into": "scratch.ablation.split"
        },
        {
          "call": "fn.ablation.score",
          "with": {
            "model": "scratch.ablation.model.all",
            "split": "scratch.ablation.split"
          },
          "into": "scratch.ablation.score.all"
        }
      ]
    }
  ]
}
```

Query: `PQL.prefix('scratch.ablation.')` -> `PQL('scratch.ablation.*')`

### shape rank 2

- experiments/students/evidence/run-1/record.json [Parse] parse, px.students.roster, px.students.scores_csv
- experiments/students/evidence/run-1/record.json [Histogram] histogram, px.students.histogram, px.students.letters
- experiments/grouped-ablation/evidence/run-1/record.json [Prepare] select, scratch.ablation.variants, input.ablation.groups
- tests/fixtures/use/order-record.json [Sum] sum, px.order.subtotal, px.order.prices
- viewer/fixtures/parallel-demo.json [Prepare] load, px.demo.rows, px.demo.csv
- viewer/fixtures/effects-demo.json [Count] count, px.demo.count, px.demo.roster
- viewer/fixtures/pyto-grouped-ablation.json [Prepare] select, scratch.ablation.variants, input.ablation.groups
- viewer/fixtures/pyto-value-kinds.json [Prepare] select, scratch.ablation.variants, input.ablation.groups
- viewer/fixtures/pyto-value-kinds.json [Text] table, scratch.ablation.table, scratch.ablation.comparison
- tests/fixtures/px/effects-record.json [Summarize] summary, scratch.effects.report, scratch.effects.stamp

```json
{
  "Ticks": [
    {
      "name": "molecule-2",
      "Calculations": [
        {
          "call": "fn.students.parse",
          "with": {
            "text": "px.students.scores_csv"
          },
          "into": "px.students.roster"
        }
      ]
    }
  ]
}
```

Query: `PQL.prefix('px.students.')` -> `PQL('px.students.*')`

### shape rank 3

- experiments/grouped-ablation/evidence/run-1/record.json [Fit, Prepare, Score] select, split, fit.all, fit.drop_g0, score.all, score.drop_g0, input.ablation.groups, scratch.ablation.model.all, scratch.ablation.model.drop_g0, scratch.ablation.score.all, scratch.ablation.score.drop_g0, scratch.ablation.split, scratch.ablation.variants
- viewer/fixtures/pyto-grouped-ablation.json [Fit, Prepare, Score] select, split, fit.all, fit.drop_g0, score.all, score.drop_g0, input.ablation.groups, scratch.ablation.model.all, scratch.ablation.model.drop_g0, scratch.ablation.score.all, scratch.ablation.score.drop_g0, scratch.ablation.split, scratch.ablation.variants
- viewer/fixtures/pyto-value-kinds.json [Fit, Prepare] select, split, fit.all, score.all, fit.drop_g3, score.drop_g3, input.ablation.groups, scratch.ablation.model.all, scratch.ablation.model.drop_g3, scratch.ablation.score.all, scratch.ablation.score.drop_g3, scratch.ablation.split, scratch.ablation.variants

compound: built on an earlier rank's SUB node; no document emitted

### shape rank 4

- experiments/grouped-ablation/evidence/run-1/record.json [Fit, Prepare, Score] select, split, fit.all, fit.drop_g0, fit.drop_g1, fit.drop_g2, fit.drop_g3, fit.drop_g4, score.all, score.drop_g0, score.drop_g1, score.drop_g2, score.drop_g3, score.drop_g4, input.ablation.groups, scratch.ablation.model.all, scratch.ablation.model.drop_g0, scratch.ablation.model.drop_g1, scratch.ablation.model.drop_g2, scratch.ablation.model.drop_g3, scratch.ablation.model.drop_g4, scratch.ablation.score.all, scratch.ablation.score.drop_g0, scratch.ablation.score.drop_g1, scratch.ablation.score.drop_g2, scratch.ablation.score.drop_g3, scratch.ablation.score.drop_g4, scratch.ablation.split, scratch.ablation.variants
- viewer/fixtures/pyto-grouped-ablation.json [Fit, Prepare, Score] select, split, fit.all, fit.drop_g0, fit.drop_g1, fit.drop_g2, fit.drop_g3, fit.drop_g4, score.all, score.drop_g0, score.drop_g1, score.drop_g2, score.drop_g3, score.drop_g4, input.ablation.groups, scratch.ablation.model.all, scratch.ablation.model.drop_g0, scratch.ablation.model.drop_g1, scratch.ablation.model.drop_g2, scratch.ablation.model.drop_g3, scratch.ablation.model.drop_g4, scratch.ablation.score.all, scratch.ablation.score.drop_g0, scratch.ablation.score.drop_g1, scratch.ablation.score.drop_g2, scratch.ablation.score.drop_g3, scratch.ablation.score.drop_g4, scratch.ablation.split, scratch.ablation.variants

compound: built on an earlier rank's SUB node; no document emitted

### shape rank 5

- experiments/students/evidence/run-1/record.json [Stats] mean, px.students.mean
- experiments/students/evidence/run-1/record.json [Stats] median, px.students.median
- viewer/fixtures/parallel-demo.json [Fan] right, px.demo.right
- viewer/fixtures/pyto-value-kinds.json [Materialize] snapshot, scratch.ablation.snapshot

```json
{
  "Ticks": [
    {
      "name": "molecule-5",
      "Calculations": [
        {
          "call": "fn.students.mean",
          "with": {
            "roster": "px.students.roster"
          },
          "into": "px.students.mean"
        }
      ]
    }
  ]
}
```

Query: `PQL.prefix('px.students.mean')` -> `PQL('px.students.mean*')`

### shape rank 6

- viewer/fixtures/parallel-demo.json [Fan, Prepare, Score] load, left, right, score, px.demo.csv, px.demo.left, px.demo.right, px.demo.rows, px.demo.score
- viewer/fixtures/pyto-value-kinds.json [Materialize, Retain, Text] sheet, snapshot, retain, table, scratch.ablation.comparison, scratch.ablation.retained, scratch.ablation.sheet, scratch.ablation.snapshot, scratch.ablation.table

compound: built on an earlier rank's SUB node; no document emitted

### shape rank 7

- experiments/grouped-ablation/evidence/run-1/record.json [Compare, Fit, Prepare, Score] select, split, fit.all, fit.drop_g0, fit.drop_g1, fit.drop_g2, fit.drop_g3, fit.drop_g4, score.all, score.drop_g0, score.drop_g1, score.drop_g2, score.drop_g3, score.drop_g4, compare, input.ablation.groups, input.ablation.rows, scratch.ablation.comparison, scratch.ablation.model.all, scratch.ablation.model.drop_g0, scratch.ablation.model.drop_g1, scratch.ablation.model.drop_g2, scratch.ablation.model.drop_g3, scratch.ablation.model.drop_g4, scratch.ablation.score.all, scratch.ablation.score.drop_g0, scratch.ablation.score.drop_g1, scratch.ablation.score.drop_g2, scratch.ablation.score.drop_g3, scratch.ablation.score.drop_g4, scratch.ablation.split, scratch.ablation.variants
- viewer/fixtures/pyto-grouped-ablation.json [Compare, Fit, Prepare, Score] select, split, fit.all, fit.drop_g0, fit.drop_g1, fit.drop_g2, fit.drop_g3, fit.drop_g4, score.all, score.drop_g0, score.drop_g1, score.drop_g2, score.drop_g3, score.drop_g4, compare, input.ablation.groups, input.ablation.rows, scratch.ablation.comparison, scratch.ablation.model.all, scratch.ablation.model.drop_g0, scratch.ablation.model.drop_g1, scratch.ablation.model.drop_g2, scratch.ablation.model.drop_g3, scratch.ablation.model.drop_g4, scratch.ablation.score.all, scratch.ablation.score.drop_g0, scratch.ablation.score.drop_g1, scratch.ablation.score.drop_g2, scratch.ablation.score.drop_g3, scratch.ablation.score.drop_g4, scratch.ablation.split, scratch.ablation.variants

compound: built on an earlier rank's SUB node; no document emitted

### shape rank 8

- viewer/fixtures/effects-demo.json [Count, Read] read.roster, count, px.demo.count, px.demo.roster
- tests/fixtures/px/effects-record.json [Stamp, Summarize] stamp, summary, scratch.effects.report, scratch.effects.stamp

compound: built on an earlier rank's SUB node; no document emitted

## Reading

Under the exact scheme the top molecule is the ablation's fit-fit-score triple over one split (two fits reading `scratch.ablation.split`, the first one's model scored), found once in each of the three ablation records; every later exact rank is that molecule grown by another sibling, and the students record has no exact molecule because each of its Calculations runs once.  Under the shape scheme the top molecule is a produce-then-consume pair -- a one-input Calculation writing a Part that a two-input Calculation reads before writing its own -- sixteen times: split-then-score and fit-then-score in the ablations, left-then-score in the parallel demo, sheet-then-retain in the value-kinds run; rank 2 is the single read-a-Part-write-a-Part step every record has, and rank 5 is the students' mean and median over one roster beside the demo's right and the ablation's snapshot.  The exact scheme names a program's molecule; the shape scheme names the studio's.
