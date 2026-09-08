# Disc-history calculation experiment

This is a tiny synthetic experiment in `/mnt/d/disc-studio-sandbox/experiments/disc-stats`. It preserves the four questions from the prior packet:

1. Can bag history provide useful statistics before shot tracking exists?
2. What does owning multiple discs of one mold tell us?
3. Can personal descriptions become useful comparisons without losing their meaning?
4. When does accumulated performance justify suggesting that a disc’s behavior changed?

The user-authorized intent was to propose reusable calculations that a Python-capable Luna could run, while preserving the current mental model and testing whether the real `quick_anno` surface can execute them.

## Reusable calculations

### 1. Bag staying power

`continuous_membership_runs(observations, observation_end=None, complete_stream=False)` returns the lengths of observed daily membership runs. A missing date ends a run. A final run is extended through `observation_end` only when `complete_stream=True`; otherwise the result is only an observed lower bound. Formula for one run is `end_day - start_day + 1`.

Observed fixture result: `(2, 1)` for Jan 1–2 and Jan 4. With a complete stream and observation end Jan 6, it becomes `(2, 3)`. Empty input returns `()`.

`{?} MembershipContinuity`
1. History lens: Should a dated bag observation count as continuous possession only when every day in the interval is represented?
2. Measurement lens: Would treating a missing date as a break undercount a disc that was owned but simply not recorded?
3. My perspective: I currently treat gaps as unknown and therefore breaks; is that the right balance between a useful lower bound and an invented duration?

Original question: Can bag history provide useful statistics before shot tracking exists?
Context: Bag history can show observed run lengths, but it cannot prove unrecorded use. The `complete_stream` flag makes the censoring rule visible.
Current lean: Use this as a descriptive history statistic and never as proof of continuous use unless event completeness is explicit.

### 2. Distinct physical discs per mold/plastic

`distinct_discs_by_mold(records)` counts distinct `disc_id` values grouped by explicitly supplied `(mold, plastic)`. Repeated rows for the same physical ID are deduplicated. A physical ID with conflicting labels raises `ValueError`; this avoids silently counting one object twice.

Observed fixture result: `("M1", "P1") -> 2`, `("M2", "P2") -> 1`.

`{?} PhysicalIdentity`
1. Ownership lens: Is the useful signal the number of physically distinct discs a person owns under one mold/plastic label?
2. Data-quality lens: Should conflicting labels be rejected until the physical identity is reviewed?
3. My perspective: I infer that count is a collection/availability statistic, not evidence that the mold performs better; what observation would justify a stronger claim?

Original question: What does owning multiple discs of one mold tell us?
Current lean: It can describe collection breadth and repeated access, while performance conclusions require shot outcomes and comparable conditions.

### 3. Explicit description frequency

`description_frequency(rows)` takes an explicit `term` label and preserves each `raw_phrase`. It reports distinct contributor and disc counts plus contributor and disc denominators. It performs no automatic natural-language extraction.

Observed fixture result: `stable` was reported by 1 of 2 contributors and on 1 of 2 discs, preserving `"holds its line"` and `"very stable"`; `glide` similarly had 1/2 contributors and 1/2 discs.

`{?} DescriptionMeaning`
1. Meaning lens: Should two phrases such as `"holds its line"` and `"very stable"` remain visibly distinct even when grouped under one supplied term?
2. Comparison lens: Is a contributor/disc denominator the minimum context needed before comparing term frequency across collections?
3. My perspective: I preserve raw wording and use only explicit labels; does that retain enough meaning without pretending that term grouping is automatic language understanding?

Original question: Can personal descriptions become useful comparisons without losing their meaning?
Current lean: Yes, when labels are supplied explicitly, raw phrases remain attached, and denominators are shown.

### 4. Later-shot rate comparison

`later_shot_rate(prior, current)` reports later-shot event counts, eligible-event denominators, each rate, and the current-minus-prior difference in percentage points. An empty denominator yields `None`, not zero.

Observed synthetic result: prior `1/2 = 50%`; current `2/3 = 66.67%`; difference `+16.67 percentage points`. This is a synthetic demonstration only; no product shot feature was added.

`{?} ChangeThreshold`
1. Evidence lens: How many eligible events should accumulate before a rate comparison is shown to a user?
2. Causality lens: What additional evidence would be required before calling a rate change a changed disc behavior rather than ordinary variation?
3. My perspective: I currently report the comparison descriptively and avoid causal diagnosis; is that the right stopping point until repeated, comparable observations exist?

Original question: When does accumulated performance justify suggesting that a disc’s behavior changed?
Current lean: This calculation can flag a comparison, but it does not decide that behavior changed. That needs repeated comparable windows and a separately agreed threshold.

## `quick_anno` compatibility

The existing executable API is at `/mnt/d/Chainspot-python-proto/packages/quick_anno_py/chainspot_quick_anno`. `Calculation` wraps a callable, `PCR` composes it, and `PxC` supplies/receives named parts. `run_experiment.py` registers `fn.discStats`, runs it through `PCR.run(PxC)`, and prints the testimony plus result. No production file was changed.

## Evidence receipt

Commands, run from the experiment directory:

```text
python3 test_stats.py
....
Ran 4 tests in 0.000s
OK

PYTHONPATH=. python3 run_experiment.py
PcrRun(... calculation='fn.discStats' ...)
{'membership_runs': (2, 1), 'mold_counts': {('M1', 'P1'): 2, ('M2', 'P2'): 1}, ... 'difference_percentage_points': 16.666666666666664}
```

File hashes from the run:

```text
stats.py         12e454de899d40ff272d306c4da712ded5f1c1b8c1319caf576dd909f7590a0e
test_stats.py    4a1a6af5a84b0d800d847e943408fd043d98c57100e45f01cc8e8f0f9c1ee414
run_experiment.py d1d9ef0874bced466eac68e17d5e8e150b885526034d6aa7b9424ec277b172b1
```

Observed: four deterministic tests pass and the real `quick_anno` runner executes the synthetic fixture.

Intent: provide reusable calculations small enough for a Luna with Python to rerun and inspect.

Inference: the calculations are useful descriptive summaries, not evidence of causality, continuous ownership across missing observations, or automatic semantic extraction.

Unknown: no real bag ledger, physical-ID quality audit, repeated comparable shot windows, or held-out validation was supplied. These fixtures do not establish product-level validity.
