"""build every Part the data vertical owns, and persist them.

    python -m experiments.brain.data.build [--store-dir D] [--records-dir D] [--quick]

Parts in, Parts out: the built-in dataset Parts, one observed PCR run whose
results land as `px.exp.brain.result.data.*` with its record under `records/`,
one oracle Part per case, a benchmark Part per backend/size pair, the group-by
bracket with its criteria written down BEFORE any judging, the findings and the
map.
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import harness  # noqa: E402

import data.datasets as datasets_module  # noqa: E402
import data.frame as frame  # noqa: E402
import data.frame_cases as frame_cases  # noqa: E402
import data.referee as referee  # noqa: E402
from data.table import canonical  # noqa: E402
import data.shaping as shaping  # noqa: E402
import data.transform as transform  # noqa: E402
import data.transform_cases as transform_cases  # noqa: E402
import data.shaping_cases as shaping_cases  # noqa: E402
import data.timeseries as timeseries  # noqa: E402
import data.timeseries_cases as timeseries_cases  # noqa: E402

VERTICAL = "data"

CASE_MODULES = (
    ("frame", frame_cases, frame.CALCS),
    ("timeseries", timeseries_cases, timeseries.CALCS),
    ("shaping", shaping_cases, shaping.CALCS),
    ("transform", transform_cases, transform.CALCS),
)

CALCS = {}
for _name, _module, _calcs in CASE_MODULES:
    CALCS.update(_calcs)
CALCS.update(datasets_module.CALCS)


def _seg(text):
    """one address segment out of anything: harness.token refuses dots and spaces."""
    return str(text).lower().replace(".", "_").replace(" ", "_")


def _name_of(address):
    """the calculation's own name, the last segment of its address."""
    return address.rsplit(".", 1)[-1]


def _effects_for(address):
    """the ledger an `oc.` case is given: a fixed list of uniforms, so the draw is a fact."""
    return transform_cases.Ledger(transform_cases.DRAWS)


def _call(address, case):
    got = CALCS[address](dict(case["args"]))
    project = case.get("project")
    return project(got) if project else got


def datasets(store):
    """the built-in tables as dataset Parts: fixed bytes, a `for` each."""
    built = []
    for name, table in sorted(datasets_module.BUILT_IN.items()):
        built.append(store.dataset(name, table["for"], table["columns"], table["rows"]))
    built.append(store.dataset(
        "wide400", frame_cases.WIDE_SMALL["for"], frame_cases.WIDE_SMALL["columns"],
        frame_cases.WIDE_SMALL["rows"]))
    built.append(store.dataset(
        "series64", "the 64-point series with a level, a trend and a season of 4",
        ["t", "value"],
        [[i, v] for i, v in enumerate(timeseries_cases.SERIES)]))
    return built


def one_run(store):
    """one observed PCR over the dataset Parts: filter, group, join, then a rolling mean.

    every step binds a Part or a sibling's result, so the record is the whole
    pipeline written down -- which is the point of doing dataframe work as
    Calculations instead of as a script.
    """
    orders = harness.data_address("orders")
    customers = harness.data_address("customers")
    kept = harness.result_address(VERTICAL, "filter", "orders_with_price")
    grouped = harness.result_address(VERTICAL, "group_by", "orders_by_region")
    joined = harness.result_address(VERTICAL, "join", "orders_customers")
    rolled = harness.result_address(VERTICAL, "rolling", "series64_window8")
    ticks = [
        ("Shape", [
            {"calc": frame.FILTER, "id": "kept", "into": kept,
             "inputs": {"table": orders},
             "args": {"where": [["price", "not_null"]],
                      "for": "the orders whose price is actually there"}},
            {"calc": frame.GROUP_BY, "id": "grouped", "into": grouped,
             "inputs": {"table": harness.Ref("kept")},
             "args": {"by": ["region"], "backend": "np",
                      "aggregates": [{"column": "price", "fn": "mean"},
                                     {"column": "price", "fn": "sum"},
                                     {"column": "items", "fn": "sum"},
                                     {"fn": "count", "as": "orders"}],
                      "for": "what each region actually spent"}},
        ]),
        ("Widen", [
            {"calc": frame.JOIN, "id": "joined", "into": joined,
             "inputs": {"table": harness.Ref("kept"), "other": customers},
             "args": {"on": "customer", "how": "left",
                      "for": "every priced order beside the customer who placed it"}},
        ]),
        ("Smooth", [
            {"calc": timeseries.ROLLING_CALC, "id": "rolled", "into": rolled,
             "args": {"values": timeseries_cases.SERIES, "window": 8, "fn": "mean",
                      "backend": "np"}},
        ]),
    ]
    return store.run("brain_data", ticks, record_name="data.pipeline")


def oracles(store):
    """one oracle Part per case: the calculation against the authority its case names.

    a `project` narrows a result to the part the authority has an opinion about.
    the frame cases project both sides (their reference hands back a whole table);
    the time-series cases project only the result (their reference hands back the
    one series it computed).
    """
    passed = failed = 0
    for group, module, _ in CASE_MODULES:
        for case in module.ORACLE_CASES:
            project = case.get("project")
            args = dict(case["args"])
            if case["calc"].startswith("oc."):
                args["effects"] = _effects_for(case["calc"])
            got = CALCS[case["calc"]](args)
            expected = case["expected"]()
            if project:
                got = project(got)
                if group in ("frame", "shaping", "transform") \
                        and isinstance(expected, dict) and "columns" in expected:
                    expected = project(expected)
            ok = store.oracle(
                VERTICAL, _name_of(case["calc"]),
                "%s_%s" % (group, _seg(case["case"])),
                got, expected, case["reference"], case["tolerance"],
                for_="the %s backend of %s answering to %s"
                     % (case["backend"], case["calc"], case["reference"]))
            passed += 1 if ok else 0
            failed += 0 if ok else 1
    return passed, failed


def benchmarks(store, quick=False, n=5):
    built = []
    for group, module, calcs in CASE_MODULES:
        cases = getattr(module, "BENCH_CASES", [])
        if quick:
            cases = [c for c in cases if "4000" not in str(c["size"])][:6]
        for case in cases:
            args = case["make_args"]()
            calc = CALCS[case["calc"]]
            built.append(store.bench(
                VERTICAL, _name_of(case["calc"]), case["backend"], _seg(case["size"]),
                (lambda calc=calc, args=args: calc(args)), n=1 if quick else n,
                for_="how long %s takes on its %s backend at %s"
                     % (case["calc"], case["backend"], case["size"]),
                inputs={"calc": case["calc"], "size": str(case["size"])}))
    return built


GROUP_BY_CRITERIA = [
    {"name": "correctness", "how": "the share of this backend's group_by oracle Parts that pass",
     "direction": "higher", "weight": 3.0},
    {"name": "speed", "how": "wall_ms_median of the largest group_by benchmark Part",
     "direction": "lower", "weight": 2.0},
    {"name": "clarity", "how": "lines of the aggregation function, docstring included",
     "direction": "lower", "weight": 1.0},
]


def group_by_tournament(store):
    """the group-by bracket: pure-python aggregation against numpy aggregation."""
    problem = "group_by_aggregation"
    candidates = [
        {"branch": "py", "calc": "fn.brain.data.group_by",
         "note": "math.fsum and sorted over plain lists, one pass per group"},
        {"branch": "np", "calc": "fn.brain.data.group_by",
         "note": "one numpy array per group per aggregate, reduced by numpy"},
        {"branch": "npsort", "calc": "fn.brain.data.group_by",
         "note": "sort once, then ONE numpy array per aggregated column for the whole "
                 "table, reduced by cumsum and reduceat"},
    ]
    store.bracket(VERTICAL, problem, GROUP_BY_CRITERIA, candidates,
                  for_="whether numpy pays for itself in a group-by, and if the per-group "
                       "array is the thing that stops it paying, whether one array per column "
                       "pays instead")
    for candidate in candidates:
        scores, note = referee.score_group_by(store, candidate["branch"])
        store.judge(VERTICAL, problem, referee.NAME, candidate["branch"], scores, note)
    decided = store.decide(VERTICAL, problem)
    default = frame.DEFAULT_GROUP_BY_BACKEND
    agrees = ("the facade already follows it" if default == decided["winner"] else
              "the facade does NOT follow it: data.frame.DEFAULT_GROUP_BY_BACKEND is %r, "
              "because the bracket's speed criterion reads the LARGEST benchmark and the "
              "engines cross over on the way there -- %r wins at 400 rows and %r at 4000"
              % (default, default, decided["winner"]))
    store.refine(
        VERTICAL, problem,
        "winner %r; fn.brain.data.group_by defaults to %r "
        "(data.frame.DEFAULT_GROUP_BY_BACKEND), so %s. every engine keeps its own oracle and "
        "benchmark Parts and stays reachable by naming args['backend'], so nothing is deleted "
        "and the bracket re-runs against all three."
        % (decided["winner"], default, agrees),
        address="fn.brain.data.group_by")
    return decided


ROLLING_CRITERIA = [
    {"name": "correctness", "how": "the share of this engine's rolling oracle Parts that pass",
     "direction": "higher", "weight": 3.0},
    {"name": "speed", "how": "wall_ms_median of the largest rolling benchmark Part",
     "direction": "lower", "weight": 2.0},
    {"name": "clarity", "how": "lines of the engine, docstring included",
     "direction": "lower", "weight": 1.0},
]


def rolling_tournament(store):
    """the rolling bracket: a slice per point, twice, against one cumulative pass."""
    problem = "rolling_window"
    candidates = [
        {"branch": "py", "calc": "fn.brain.data.rolling",
         "note": "one slice per point, reduced in pure python: O(n w)"},
        {"branch": "np", "calc": "fn.brain.data.rolling",
         "note": "one slice per point, reduced by numpy: O(n w) with an array built per point"},
        {"branch": "cumsum", "calc": "fn.brain.data.rolling",
         "note": "prefix sums of the series and of its squares, one pass: O(n) whatever the "
                 "window, and it covers count/sum/mean/var/std only"},
    ]
    store.bracket(VERTICAL, problem, ROLLING_CRITERIA, candidates,
                  for_="whether a rolling statistic should be a window reduced per point at "
                       "all, once the same answer is available in one pass")
    for candidate in candidates:
        scores, note = referee.score_rolling(store, candidate["branch"])
        store.judge(VERTICAL, problem, referee.NAME, candidate["branch"], scores, note)
    decided = store.decide(VERTICAL, problem)
    default = timeseries._backend({}, timeseries.ROLLING_BACKENDS)
    store.refine(
        VERTICAL, problem,
        "winner %r; fn.brain.data.rolling defaults to %r, and it stays the default because it "
        "is the only engine that answers every fn (min, max and median have no whole-window "
        "form, and the cumsum engine refuses them loudly rather than answering some other "
        "question). the winner is what a caller asking for count/sum/mean/var/std at size "
        "should name. every engine keeps its own oracle and benchmark Parts."
        % (decided["winner"], default),
        address="fn.brain.data.rolling")
    return decided


def findings(store):
    store.finding(
        VERTICAL, "declarative_predicates_keep_the_record_whole", "strength",
        "the predicate of a filter, the aggregate of a group-by and the ordering of a sort are "
        "DATA here -- [column, comparison, value] triples and {'column','fn','as'} mappings -- "
        "never callables. so the whole dataframe pipeline is json-able, lands intact on a run "
        "record, and can be read back by a process that never imported the program. a pandas-"
        "shaped api with lambdas could not have done that.",
        for_="Parts in, Parts out is only true if the program is a Part too")
    store.finding(
        VERTICAL, "missing_is_none_because_json_cannot_hold_nan", "strength",
        "every calculation in this vertical spells a hole as None and never as float('nan'), "
        "because a dataset Part has to survive json.dumps for the digest, the record and the "
        "replay to work. that one rule pushed real design: a rolling window returns None until "
        "it fills, an aggregate over an all-missing group is None rather than nan, and the "
        "oracle helper compares None exactly instead of numerically.",
        for_="the store is the interface; a value it cannot hold is not a result")
    store.finding(
        VERTICAL, "numpy_does_not_pay_on_small_groups", "friction",
        "the group-by bracket measured it three ways. the 'np' engine builds one array per "
        "group per aggregate and is SLOWER than plain python at every size tested: the array "
        "construction costs more than the reduction saves when a group is tens of rows. the "
        "third engine, 'npsort', was built to answer the obvious follow-up -- sort once, then "
        "one array per COLUMN reduced by cumsum and reduceat -- and it wins at 4000 rows and "
        "loses at 400. so the useful statement is not 'numpy is faster' but 'numpy is faster "
        "per ARRAY, and a group-by's arrays are the thing you have to choose'.",
        for_="a backend picked by reputation rather than by a benchmark Part is a guess, and "
             "this one would have been the wrong guess twice over",
        workaround="all three engines stay; args['backend'] names one, "
                   "data.frame.DEFAULT_GROUP_BY_BACKEND records which one is the default and "
                   "why, and the bracket re-runs against all three",
        proposal="a benchmark Part that carries the SIZE it was measured at is already there, "
                 "but harness.decide reads one number per criterion, so a bracket cannot say "
                 "'this one wins above n=2000'. let a criterion name the bench size it scores "
                 "on, or let decide return a winner per size, and a crossover stops being "
                 "invisible to the tournament")
    store.finding(
        VERTICAL, "a_dataset_part_has_no_column_types", "friction",
        "{'for', 'columns', 'rows'} carries no declared type per column, so every calculation "
        "re-derives what a column holds (fn.brain.data.shape exists only to answer that), and a "
        "column that is numbers-with-one-string is only discovered when an aggregate raises. "
        "join and sort therefore need a total order over mixed json cells (data.table.sort_key) "
        "just to be able to compare two cells at all.",
        for_="every relational calculation pays this cost on every call",
        workaround="one sort_key function defines the total order once -- missing first, then "
                   "numbers, then text -- and every calculation uses it, so at least the order "
                   "is the same everywhere",
        proposal="let a dataset Part carry an optional 'kinds' mapping alongside 'columns', "
                 "written by fn.brain.data.shape and trusted (and re-checked) by the rest; the "
                 "harness's dataset() is the natural place to fill it in")
    store.finding(
        VERTICAL, "the_window_did_not_have_to_be_a_window", "strength",
        "the rolling bracket is the clearest thing this vertical measured. both of the "
        "obvious engines take a slice per point and reduce it, so both are O(n w) and both "
        "get slower as the window grows; the third keeps prefix sums of the series and of "
        "its squares and answers every window in one pass, so its cost does not move with "
        "the window at all. it needed one real idea to meet the same 1e-9 oracle -- shift "
        "the series by its own mean before accumulating the squares, so a cumulative "
        "variance is a difference of small numbers rather than of large ones.",
        for_="a facade with a backend argument is what let a third engine be added and "
             "measured without touching a single caller or a single oracle case")
    store.finding(
        VERTICAL, "the_loader_is_an_effect_and_that_is_the_point", "strength",
        "oc.brain.data.load reads csv and json through args['effects'].read_text, so the bytes "
        "it read land on the ledger. a dataset that came off disk is therefore as replayable as "
        "one written out in a module, and the record says which file it came from.",
        for_="a data-science layer whose inputs are unrecorded is not reproducible")
    return True


def built_addresses(store):
    return [a for a in store.brain_addresses()
            if ".data." in a and not a.startswith("px.exp.brain.data.stats_")]


def the_map(store, decided):
    stubbed = [
        {"address": "fn.brain.data.rolling (min, max and median on the cumsum engine)",
         "why": "a running minimum needs a monotonic deque, not a prefix sum; the engine "
                "refuses those three loudly instead of answering a different question"},
        {"address": "fn.brain.data.group_by (median on the npsort engine)",
         "why": "median has no whole-column reduction, so the third engine falls back to the "
                "per-group path for it; a sorted-block median is the obvious next piece"},
        {"address": "fn.brain.data.rolling_join",
         "why": "an as-of join needs an ordered key and a tolerance; the equi-join is here"},
        {"address": "fn.brain.data.resample",
         "why": "needs a time index with real calendar semantics, which no dataset Part carries yet"},
        {"address": "fn.brain.data.stl",
         "why": "loess-based seasonal decomposition; the classical centred-average decomposition "
                "is here and is the reference STL would be checked against"},
        {"address": "fn.brain.data.arima",
         "why": "AR(p) by least squares is here; the moving-average half needs a likelihood, "
                "which needs an optimiser the brain does not have tonight"},
    ]
    next_ = [
        {"what": "a sorted-block median and quantile on the npsort engine",
         "for": "it is the one aggregate the third engine still hands back to the per-group path"},
        {"what": "a bracket criterion that names the benchmark size it scores on",
         "for": "the group-by engines cross over between 400 and 4000 rows and the bracket "
                "cannot currently say so"},
        {"what": "column kinds on the dataset Part (see proposal.brain.data.a_dataset_part_has_no_column_types)",
         "for": "every relational calculation re-derives them on every call"},
        {"what": "resample and a calendar-aware time index, and an as-of (rolling) join on it",
         "for": "real time series arrive with dates, not with positions, and every join "
                "against them is as-of"},
        {"what": "ARIMA on top of the AR fit, and STL on top of the classical decomposition",
         "for": "forecasting is the first thing anyone asks a data layer for"},
    ]
    return store.map_part(VERTICAL, sorted(built_addresses(store)), stubbed, next_,
                          for_="what the data vertical of the brain holds tonight, and what the "
                               "next night should pick up first")


def build(store_dir=None, records_dir=None, quick=False, bench_n=5, commit=False):
    store = harness.Store(store_dir=store_dir, records_dir=records_dir,
                          commit=commit or None)
    datasets(store)
    one_run(store)
    passed, failed = oracles(store)
    benchmarks(store, quick=quick, n=bench_n)
    decided = group_by_tournament(store)
    rolling_tournament(store)
    findings(store)
    the_map(store, decided)
    return store, {"oracles_passed": passed, "oracles_failed": failed,
                   "winner": decided["winner"]}


def main(argv=None):
    parser = argparse.ArgumentParser(description="build the data vertical's Parts")
    parser.add_argument("--store-dir")
    parser.add_argument("--records-dir")
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--bench-n", type=int, default=5)
    parser.add_argument("--commit", action="store_true",
                        help="write store/ and records/ inside the repository")
    parsed = parser.parse_args(argv)
    store, summary = build(parsed.store_dir, parsed.records_dir, parsed.quick,
                           parsed.bench_n, parsed.commit)
    for address in list(store.written):
        store.put(address, canonical(store.get(address)))
    path = store.save(VERTICAL)
    print("oracles: %d passed, %d failed" % (summary["oracles_passed"], summary["oracles_failed"]))
    print("group-by bracket winner:", summary["winner"])
    print("parts:", len(store.written), "->", path)
    return 0 if summary["oracles_failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
