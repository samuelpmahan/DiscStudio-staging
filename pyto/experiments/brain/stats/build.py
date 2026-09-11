"""build every Part the stats vertical owns, and persist them.

    python -m experiments.brain.stats.build [--store-dir D] [--records-dir D] [--quick]

Parts in, Parts out: the dataset Parts this vertical reads, one observed PCR run
whose results land as `px.exp.brain.result.stats.*` with its record under
`records/`, one oracle Part per case in every `*_cases.py` module, a benchmark
Part per backend/size pair, the two brackets with their criteria written down
BEFORE any judging, the findings, and the map. `--quick` runs a small slice of
the benchmarks; the tests use it, the committed store does not.
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import harness  # noqa: E402

import stats.correlation as correlation  # noqa: E402
import stats.correlation_cases as correlation_cases  # noqa: E402
import stats.descriptive as descriptive  # noqa: E402
import stats.descriptive_cases as descriptive_cases  # noqa: E402
import stats.distributions as distributions  # noqa: E402
import stats.distributions_cases as distributions_cases  # noqa: E402
import stats.hypothesis as hypothesis  # noqa: E402
import stats.hypothesis_cases as hypothesis_cases  # noqa: E402
import stats.intervals as intervals  # noqa: E402
import stats.intervals_cases as intervals_cases  # noqa: E402
import stats.nonparametric as nonparametric  # noqa: E402
import stats.nonparametric_cases as nonparametric_cases  # noqa: E402
import stats.referee as referee  # noqa: E402
import stats.regression as regression  # noqa: E402
import stats.regression_cases as regression_cases  # noqa: E402

VERTICAL = "stats"

CASE_MODULES = (
    ("descriptive", descriptive_cases, descriptive.CALCS),
    ("correlation", correlation_cases, correlation.CALCS),
    ("distributions", distributions_cases, distributions.CALCS),
    ("hypothesis", hypothesis_cases, hypothesis.CALCS),
    ("regression", regression_cases, regression.CALCS),
    ("intervals", intervals_cases, intervals.CALCS),
    ("nonparametric", nonparametric_cases, nonparametric.CALCS),
)

CALCS = {}
for _name, _module, _calcs in CASE_MODULES:
    CALCS.update(_calcs)


def _seg(text):
    """one address segment out of anything: harness.token refuses dots and spaces."""
    return str(text).lower().replace(".", "_").replace(" ", "_")


def _name_of(address):
    """the calculation's own name, the last segment of its address."""
    return address.rsplit(".", 1)[-1]


def _call(address, case):
    """run one case's calculation, handing an `oc.` the ledger its case carries."""
    args = dict(case["args"])
    if address.startswith("oc."):
        args["effects"] = intervals_cases.Ledger(intervals_cases.LEDGER)
    got = CALCS[address](args)
    project = case.get("project")
    return project(got) if project else got


def datasets(store):
    """the dataset Parts this vertical reads, as Parts: json-able, fixed, named."""
    built = [
        store.dataset("stats_sample57", "the 57-point sample the descriptive oracles read",
                      ["value"], [[v] for v in descriptive_cases.SAMPLE]),
        store.dataset("stats_pair63", "the 63 paired points the correlation oracles read",
                      ["x", "y"], list(map(list, zip(correlation_cases.X, correlation_cases.Y)))),
        store.dataset("stats_groups", "the three groups the anova and the effect sizes read",
                      ["group", "value"],
                      [[i, v] for i, group in enumerate(hypothesis_cases.GROUPS) for v in group]),
        store.dataset("stats_design80",
                      "the 80-row three-predictor design the regression oracles read",
                      ["x1", "x2", "x3", "y"],
                      [row + [y] for row, y in zip(regression_cases.DESIGN, regression_cases.Y)]),
    ]
    return built


def one_run(store):
    """one observed PCR: a real analysis of the design, Parts in and Parts out.

    it reads the dataset Part, describes a column, correlates two, tests a
    difference and fits an OLS -- four calculations whose results land at
    `px.exp.brain.result.stats.*` and whose record lands under `records/`.
    """
    design = harness.data_address("stats_design80")
    ticks = [
        ("Read", [
            {"calc": descriptive.DESCRIBE, "id": "describe",
             "into": harness.result_address(VERTICAL, "describe", "design80_y"),
             "args": {"values": regression_cases.Y, "backend": "py"}},
            {"calc": correlation.PEARSON, "id": "pearson",
             "into": harness.result_address(VERTICAL, "pearson", "design80_x1_y"),
             "args": {"x": regression_cases.X1, "y": regression_cases.Y, "backend": "np"}},
        ]),
        ("Test", [
            {"calc": hypothesis.TTEST_IND, "id": "welch",
             "into": harness.result_address(VERTICAL, "ttest_ind", "sample_other"),
             "args": {"x": intervals_cases.SAMPLE, "y": intervals_cases.OTHER,
                      "equal_var": False, "backend": "py"}},
            {"calc": intervals.CI_DIFF_MEANS, "id": "interval",
             "into": harness.result_address(VERTICAL, "ci_diff_means", "sample_other"),
             "args": {"x": intervals_cases.SAMPLE, "y": intervals_cases.OTHER}},
        ]),
        ("Fit", [
            {"calc": regression.OLS, "id": "ols",
             "into": harness.result_address(VERTICAL, "ols", "design80_qr"),
             "args": {"x": regression_cases.DESIGN, "y": regression_cases.Y, "solver": "qr"}},
        ]),
    ]
    return store.run("brain_stats", ticks, record_name="stats.analysis"), design


def oracles(store):
    """one oracle Part per case: the calculation against the authority its case names."""
    passed = failed = 0
    for group, module, _ in CASE_MODULES:
        for case in module.ORACLE_CASES:
            got = _call(case["calc"], case)
            ok = store.oracle(
                VERTICAL, _name_of(case["calc"]),
                "%s_%s" % (group, _seg(case["case"])),
                got, case["expected"](), case["reference"], case["tolerance"],
                for_="the %s backend of %s answering to %s"
                     % (case["backend"], case["calc"], case["reference"]))
            passed += 1 if ok else 0
            failed += 0 if ok else 1
    return passed, failed


def benchmarks(store, quick=False, n=5):
    """a benchmark Part per backend and size; only pairs whose oracles passed are compared."""
    built = []
    for group, module, calcs in CASE_MODULES:
        cases = getattr(module, "BENCH_CASES", [])
        if quick:
            cases = [c for c in cases if "100000" not in str(c["size"])
                     and "50000" not in str(c["size"])][:6]
        for case in cases:
            args = case["make_args"]()
            calc = CALCS[case["calc"]]
            value = store.bench(
                VERTICAL, _name_of(case["calc"]), case["backend"], _seg(case["size"]),
                (lambda calc=calc, args=args: calc(args)), n=1 if quick else n,
                for_="how long %s takes on its %s backend at %s"
                     % (case["calc"], case["backend"], case["size"]),
                inputs={"calc": case["calc"], "size": str(case["size"])})
            built.append(value)
    return built


OLS_CRITERIA = [
    {"name": "correctness", "how": "the share of this solver's oracle Parts that pass",
     "direction": "higher", "weight": 3.0},
    {"name": "conditioning",
     "how": "worst relative disagreement with numpy.linalg.lstsq on a nearly collinear design",
     "direction": "lower", "weight": 2.0},
    {"name": "speed", "how": "wall_ms_median of the n=2000 benchmark Part",
     "direction": "lower", "weight": 1.0},
    {"name": "clarity", "how": "lines of the solver function, docstring included",
     "direction": "lower", "weight": 1.0},
]

GROUP_BY_CRITERIA = [
    {"name": "correctness", "how": "the share of this backend's group_by oracle Parts that pass",
     "direction": "higher", "weight": 3.0},
    {"name": "speed", "how": "wall_ms_median of the largest group_by benchmark Part",
     "direction": "lower", "weight": 2.0},
    {"name": "clarity", "how": "lines of the aggregation function, docstring included",
     "direction": "lower", "weight": 1.0},
]


def ols_tournament(store, quick=False):
    """the OLS bracket: normal equations against householder QR against numpy lstsq."""
    problem = "ols_solver"
    candidates = [
        {"branch": "normal", "calc": "fn.brain.stats.ols_normal",
         "note": "X'X b = X'y solved by gauss-jordan; forms the gram matrix"},
        {"branch": "qr", "calc": "fn.brain.stats.ols_qr",
         "note": "householder QR of the design; never forms X'X"},
        {"branch": "lstsq", "calc": "fn.brain.stats.ols_lstsq",
         "note": "numpy.linalg.lstsq, an SVD under the hood"},
    ]
    store.bracket(VERTICAL, problem, OLS_CRITERIA, candidates,
                  for_="which route to the same least-squares answer the facade should default to")
    for candidate in candidates:
        scores, note = referee.score_ols(store, candidate["branch"], quick=quick)
        store.judge(VERTICAL, problem, referee.NAME, candidate["branch"], scores, note)
    decided = store.decide(VERTICAL, problem)
    default = regression.DEFAULT_SOLVER
    agrees = ("the facade already follows it" if default == decided["winner"] else
              "the facade does NOT follow it on this machine: stats.regression.DEFAULT_SOLVER is "
              "the one line to change")
    store.refine(
        VERTICAL, problem,
        "winner %r; fn.brain.stats.ols defaults to %r (stats.regression.DEFAULT_SOLVER), so %s. "
        "the losing solvers stay in the store as Calculations of their own, with their own "
        "oracle and benchmark Parts, so the bracket re-runs against all three."
        % (decided["winner"], default, agrees),
        address="fn.brain.stats.ols")
    return decided


def findings(store):
    """what the facade carried and what it fought, as Parts."""
    store.finding(
        VERTICAL, "parts_are_the_whole_interface", "strength",
        "every calculation here is pure over json-able Parts and a plain args mapping, so the "
        "same function is callable by hand, bindable in a PCR, replayable from a record and "
        "comparable across backends without a single adapter. the backend facade "
        "(args['backend'] py/np/sp) cost nothing structurally: it is one branch inside one "
        "function, and the oracle Parts are what keep the branches honest.",
        for_="it is the reason a 200-calculation surface could be built in one night")
    store.finding(
        VERTICAL, "effects_handle_makes_sampling_replayable", "strength",
        "oc.brain.stats.sample and oc.brain.stats.bootstrap take their randomness through "
        "args['effects'].random, so the draws land on the run's ledger. a bootstrap interval "
        "is therefore a fact of the record, not a re-roll: the same record replays to the same "
        "interval, which is exactly what a confidence interval published as a Part needs.",
        for_="statistics that draw are the ones a reader most wants to be able to check")
    store.finding(
        VERTICAL, "no_authority_for_relational_shape", "friction",
        "the contract asks for an oracle against scipy/numpy, and for descriptive statistics, "
        "distributions, tests and regression that is exactly right. it has no answer for the "
        "relational half of the data vertical (select, filter, join, pivot, sort, window) or for "
        "the smoothers: numpy has no join and no holt. pandas and statsmodels are not installed.",
        for_="an oracle whose reference is vague is not evidence, it is a claim",
        workaround="those cases name a SECOND, independent implementation written in the same "
                   "*_cases.py module (a nested-loop join where the calculation uses a hash index, "
                   "a selection sort where it uses python's sort) and the reference string says so, "
                   "so a reader can see which kind of authority a Part rests on",
        proposal="let an oracle Part carry an explicit 'authority' field with values like "
                 "'library' / 'second-implementation' / 'closed-form', so navigate() can report "
                 "how much of the brain is checked against an outside library and how much "
                 "against itself")
    store.finding(
        VERTICAL, "tolerance_is_a_property_of_the_case_not_the_kernel", "friction",
        "one relative tolerance (1e-9) covers almost everything, but not everything: the "
        "shapiro-wilk p-value reproduces scipy's fortran only to about 5e-9 because AS R94's "
        "normalising polynomials are published to seven figures, and a survival function "
        "computed as 1 - cdf loses the far tail. a single DEFAULT_TOLERANCE would either hide "
        "those or fail them.",
        for_="a backend that changes semantics is a failed backend, so the line has to be drawn "
             "somewhere a reader can see",
        workaround="every case carries its own tolerance and the looser ones are tested to be "
                   "exactly the cases that named a reason",
        proposal="harness.oracle could take a 'why' beside 'tolerance' and refuse a tolerance "
                 "looser than the default without one")
    store.finding(
        VERTICAL, "pql_cannot_ask_across_kinds", "friction",
        "the questions worth asking of this store are joins: 'every calculation with an np "
        "backend whose oracle passes but whose benchmark is slower than py', 'every bracket "
        "whose winner is not the facade default', 'every calculation with a benchmark and no "
        "oracle'. addresses carry the kind, the vertical, the calc and the case as dotted "
        "segments, so each of those is a scan plus a python dict join.",
        for_="the map is supposed to be readable through PQL, not through a script that "
             "reimplements a join each time",
        workaround="navigate() in the harness does the joins in python and the map Part records "
                   "the answers as lists of addresses",
        proposal="a PQL that can group by an address segment and join two groups on a shared "
                 "segment -- 'px.exp.brain.oracle.<v>.<calc>.* JOIN px.exp.brain.bench.<v>.<calc>.*' "
                 "-- would turn every one of those questions into one line")
    store.finding(
        VERTICAL, "judging_needs_a_reader_that_did_not_build", "friction",
        "the contract asks for a judge that did not build a candidate, and harness.judge "
        "enforces it by name. this vertical could not put an independent agent in the chair, so "
        "the judge is stats.referee: a scorer that never sees the solvers' internals, only the "
        "recorded oracle Parts, the recorded benchmark Parts and the line counts of the "
        "candidate functions.",
        for_="a bracket whose scores cannot be recomputed is a claim, not a receipt",
        workaround="referee.py reads Parts and source files only, records the exact numbers it "
                   "scored on in the judgment's note, and is re-runnable from the store alone",
        proposal="the harness could accept a judgment signed with the list of addresses it read, "
                 "so decide() can refuse a judge that scored on something the store does not hold")
    return True


def built_addresses(store):
    return [a for a in store.brain_addresses() if ".stats." in a or a.startswith("px.exp.brain.data.stats_")]


def the_map(store, decided):
    stubbed = [
        {"address": "fn.brain.stats.ols_weighted",
         "why": "weighted least squares is the same three solvers with a weight vector; "
                "the tournament had to be settled on the unweighted case first"},
        {"address": "fn.brain.stats.kstwo_exact",
         "why": "the EXACT two-sided kolmogorov distribution (what scipy's ks_2samp reaches for "
                "at small n) is the marsaglia-tsang-wang matrix power; the limiting tail is "
                "here and both backends agree on it, which is the rule that mattered"},
        {"address": "fn.brain.stats.mannwhitneyu (exact)",
         "why": "the exact null under n=20 is its own combinatorial table; the asymptotic "
                "tail with the tie correction is what is built"},
        {"address": "fn.brain.stats.wilcoxon (exact)",
         "why": "same table, same reason: scipy's method='approx' is the one both backends meet"},
        {"address": "fn.brain.stats.kruskal",
         "why": "the rank-based one-way anova; f_oneway and mann-whitney cover its two ends"},
    ]
    next_ = [
        {"what": "weighted and robust least squares on the winning solver (%s)" % decided["winner"],
         "for": "every real regression in a consumer has weights or outliers"},
        {"what": "the exact small-sample nulls: kstwo, wilcoxon and mann-whitney under n=20",
         "for": "small-sample work is exactly where an asymptotic p-value is most wrong, and "
                "every one of them is now a tail away from a calculation that already exists"},
        {"what": "an 'authority' field on oracle Parts (see proposal.brain.stats.no_authority_for_relational_shape)",
         "for": "so a reader can see which Parts rest on a library and which on a second implementation"},
        {"what": "a PQL that joins two address families on a shared segment",
         "for": "so the map is a query and not a script"},
    ]
    return store.map_part(VERTICAL, sorted(built_addresses(store)), stubbed, next_,
                          for_="what the stats vertical of the brain holds tonight, and what the "
                               "next night should pick up first")


def build(store_dir=None, records_dir=None, quick=False, bench_n=5, commit=False):
    """build everything into a fresh Store and return it. the tests call this with temp dirs."""
    store = harness.Store(store_dir=store_dir, records_dir=records_dir,
                          commit=commit or None)
    datasets(store)
    one_run(store)
    passed, failed = oracles(store)
    benchmarks(store, quick=quick, n=bench_n)
    decided = ols_tournament(store, quick=quick)
    findings(store)
    the_map(store, decided)
    return store, {"oracles_passed": passed, "oracles_failed": failed,
                   "winner": decided["winner"]}


def main(argv=None):
    parser = argparse.ArgumentParser(description="build the stats vertical's Parts")
    parser.add_argument("--store-dir")
    parser.add_argument("--records-dir")
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--bench-n", type=int, default=5)
    parser.add_argument("--commit", action="store_true",
                        help="write store/ and records/ inside the repository")
    parsed = parser.parse_args(argv)
    store, summary = build(parsed.store_dir, parsed.records_dir, parsed.quick,
                           parsed.bench_n, parsed.commit)
    path = store.save(VERTICAL)
    print("oracles: %d passed, %d failed" % (summary["oracles_passed"], summary["oracles_failed"]))
    print("ols bracket winner:", summary["winner"])
    print("parts:", len(store.written), "->", path)
    return 0 if summary["oracles_failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
