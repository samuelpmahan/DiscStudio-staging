"""`python -m pyto.study` -- an honest study of a table you actually have.

Point it at a csv (or json rows) and it reads the table, profiles every column,
looks for what moves together, tests the one hypothesis the data invites,
clusters, and -- with `--target` -- cross-validates every model the brain owns
and keeps the one the folds preferred. Nothing is printed and thrown away:
every step is a `Calculation` from `pyto/experiments/brain`, run through an
observed `PCR`, so the study is Parts with receipts. What comes out is a store
(`store.json`), the run records (`records/*.json`), one page (`study.html`: the
summary over the Tick viewer) and a map of what ran and what was refused.

    python -m pyto.study data.csv --out study
    python -m pyto.study data.csv --target price --out study
    python -m pyto.study --example shelf --out shelf-study

Three rules, and they are the whole design.

**Every number is a Part.** The summary at the top of the page is not written
from local variables: it is `px.exp.study.<name>.summary`, and every line in it
cites the address and the key its number came from, so `tests/test_study.py`
can check the prose against the store rather than against itself.

**A step that does not fit is refused, not forced.** A numeric test on a text
column, a method with fewer rows than it needs, a t-test whose normality check
failed: each is a skip Part with its reason, its `needed` and its `had`, and
the summary says what the study would not say.

**`fn.study.*` never decides anything a reader cannot recompute.** The study
owns a handful of Calculations and every one of them is a *fold* over the
brain's: it selects, it ranks, it dispatches, and every number it publishes was
produced by `fn.brain.*`. Nothing here is promoted: the addresses are
`px.exp.study.*` and the findings are `proposal.study.*`.

The program is three observed `PCR`s, because a `PCR`'s Ticks are declared
before it runs and this one decides what to run from its own first result:
`study_read` (load, shape, profile, plan), `study_weigh` (the assumption checks
behind a hypothesis) and `study` (everything the plan chose). See
`proposal.study.a_program_that_decides_its_own_ticks`.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import math
import os
import subprocess
import sys

PX = "px.exp.study."
PROPOSAL = "proposal.study."

# --- floors: what a method needs before it is allowed to answer ----------------
MIN_PROFILE = 2        # describe
MIN_SHAPIRO = 3        # shapiro-wilk
MAX_SHAPIRO = 5000     # royston's approximation is stated for n <= 5000
MIN_CORRELATION = 4    # pearson with a p-value beside it
MIN_GROUP = 3          # rows in one level of a group column
MIN_TEST_ROWS = 6      # rows across all levels
MAX_LEVELS = 6         # levels of a group column the study will split on
MIN_CLUSTER_ROWS = 6
MIN_MODEL_ROWS = 12
ALPHA = 0.05           # the assumption checks' threshold, written down once
CORRELATION_THRESHOLD = 0.5
MAX_PROFILE_COLUMNS = 16
MAX_CLUSTER_COLUMNS = 10


# --- finding the brain --------------------------------------------------------


def brain_root() -> str:
    """the directory holding `harness.py`, or a refusal that says where it looked.

    the brain is an experiment, not part of the installed package, so it is found
    rather than imported: `PYTO_BRAIN`, then beside this checkout, then beside the
    working directory.
    """
    tried = []
    named = os.environ.get("PYTO_BRAIN")
    if named:
        tried.append(named)
    here = os.path.dirname(os.path.abspath(__file__))
    pyto_root = os.path.dirname(os.path.dirname(here))  # src/pyto -> src -> pyto
    tried.append(os.path.join(pyto_root, "experiments", "brain"))
    tried.append(os.path.join(os.getcwd(), "experiments", "brain"))
    tried.append(os.path.join(os.getcwd(), "pyto", "experiments", "brain"))
    for candidate in tried:
        if os.path.isfile(os.path.join(candidate, "harness.py")):
            return os.path.abspath(candidate)
    raise SystemExit(
        "pyto study: the brain is not here. It looked in:\n  "
        + "\n  ".join(os.path.abspath(one) for one in tried)
        + "\nSet PYTO_BRAIN to the directory holding experiments/brain/harness.py."
    )


_BRAIN = {}


def brain():
    """every brain module the study uses, imported once, as one mapping."""
    if _BRAIN:
        return _BRAIN
    root = brain_root()
    pyto_root = os.path.dirname(os.path.dirname(root))  # experiments/brain -> experiments -> pyto
    for path in (root, pyto_root):
        if path not in sys.path:
            sys.path.insert(0, path)
    from experiments.brain import harness  # noqa: E402
    from experiments.brain.backend import choose  # noqa: E402
    from experiments.brain.ml import calcs as mlcalcs  # noqa: E402

    import data.datasets as datasets  # noqa: E402
    import data.frame as frame  # noqa: E402
    import data.shaping as shaping  # noqa: E402
    import data.transform as transform  # noqa: E402
    import stats.comparisons as comparisons  # noqa: E402
    import stats.correlation as correlation  # noqa: E402
    import stats.descriptive as descriptive  # noqa: E402
    import stats.hypothesis as hypothesis  # noqa: E402
    import stats.intervals as intervals  # noqa: E402
    import stats.nonparametric as nonparametric  # noqa: E402

    _BRAIN.update(
        root=root, pyto_root=pyto_root, harness=harness, choose=choose, ml=mlcalcs,
        datasets=datasets, frame=frame, shaping=shaping, transform=transform,
        comparisons=comparisons, correlation=correlation, descriptive=descriptive,
        hypothesis=hypothesis, intervals=intervals, nonparametric=nonparametric,
    )
    return _BRAIN


# --- the store ----------------------------------------------------------------


def study_store(out_dir: str):
    """`harness.Store` with the study's own address space and a world to read from.

    two overrides and no more: `put` accepts `px.exp.study.*` / `proposal.study.*`
    (the harness refuses anything outside the brain --
    `proposal.study.the_harness_store_is_the_brains_only`), and `run` takes an
    `effects_root`, which the harness's does not, because the study's first
    Calculation is an `oc.` that reads a file.
    """
    from pyto import PCR, Part
    from pyto.materialize import run_record, write_record

    harness = brain()["harness"]

    class StudyStore(harness.Store):
        def put(self, address, value):
            address = str(address)
            if address != address.lower():
                raise ValueError(f"study: address {address!r} must be lowercase")
            if not (address.startswith(PX) or address.startswith(PROPOSAL)):
                raise ValueError(f"study: address {address!r} is outside the study ({PX}* or {PROPOSAL}*)")
            self.pxc.set(Part(address), harness.jsonable(value))
            if address not in self.written:
                self.written.append(address)
            return address

        def mine(self, address):
            return address.startswith(PX) or address.startswith(PROPOSAL)

        def run(self, name, ticks, record_name=None, effects_root=None):
            name = harness.token(name, "pcr name")
            pcr = PCR(name)
            refs = {}
            for tick_name, steps in ticks:
                for step in steps:
                    into = step["into"]
                    into_arg = Part(into) if isinstance(into, str) else [Part(str(one)) for one in into]
                    bindings = {}
                    for key, source in dict(step.get("inputs", {})).items():
                        if isinstance(source, harness.Ref):
                            ref = refs[source.id]
                            bindings[key] = ref if source.address is None else ref[Part(source.address)]
                        elif isinstance(source, str):
                            bindings[key] = Part(source)
                        else:
                            bindings[key] = source
                    refs[step["id"]] = pcr.calc(
                        tick_name, step["calc"], id=step["id"], into=into_arg,
                        args=dict(step.get("args", {})), **bindings
                    )
            preexisting = set(self.pxc.addresses())
            run = pcr.run(self.pxc, observe=True, effects_root=effects_root)
            record = run_record(run, self.pxc, preexisting=preexisting)
            os.makedirs(self.records_dir, exist_ok=True)
            path = os.path.join(self.records_dir, f"{record_name or name}.json")
            write_record(record, path)
            self.records.append(path)
            for address in self.pxc.addresses():
                if self.mine(address) and address not in self.written:
                    self.written.append(address)
            return run

    store = StudyStore(store_dir=out_dir, records_dir=os.path.join(out_dir, "records"))
    # read the brain's committed store, not the output directory: this is where
    # `backend="auto"` gets the plan the benchmark Parts wrote.
    store.load_store(harness.STORE_DIR)
    return store


# --- names --------------------------------------------------------------------


def slug(text: str) -> str:
    """one lowercase address segment out of a column name."""
    out = []
    for ch in str(text).lower():
        out.append(ch if (ch.isalnum() and ch.isascii()) else "_")
    cleaned = "_".join(part for part in "".join(out).split("_") if part)
    return cleaned or "x"


def slugs(names):
    """a distinct segment per name, in order, collisions numbered."""
    taken, out = {}, []
    for name in names:
        base = slug(name)
        if base in taken:
            taken[base] += 1
            base = f"{base}_{taken[base]}"
        else:
            taken[base] = 0
        out.append(base)
    return out


# --- backend="auto", resolved -------------------------------------------------


def engine(plan, vertical, calc, engines, default="py"):
    """the engine the benchmark Parts chose for this calculation, or the reference.

    the stats, data and ml facades take a named engine and not the word "auto"
    (`proposal.study.no_facade_takes_the_word_auto`), so the plan is read here and
    the name it gives is what the step's args carry -- which is what puts the
    choice on the record.
    """
    choose = brain()["choose"]
    return choose.engine_for_calc(plan, vertical, calc, tuple(engines)) or default


def engine_table(plan, wanted):
    """what `auto` decided, per calculation, as one readable Part."""
    choose = brain()["choose"]
    out = {}
    for vertical, calc, engines in wanted:
        key = f"{vertical}.{calc}"
        chosen = choose.engine_for_calc(plan, vertical, calc, tuple(engines))
        row = (plan or {}).get("by_calc", {}).get(key) or {}
        out[key] = {
            "engine": chosen or "py",
            "from": "plan" if chosen else "reference",
            "measured_at": row.get("at"),
            "spread": row.get("spread"),
            "engines": list(engines),
        }
    return out


# --- the model bench: every candidate the brain owns, scored on the same folds --

REGRESSORS = (
    {"name": "linear", "fit": "linreg_fit", "predict": "linreg_predict", "fit_args": {},
     "says": "one straight line through every column at once"},
    {"name": "ridge", "fit": "ridge_fit", "predict": "linreg_predict", "fit_args": {"alpha": 1.0},
     "says": "the same line, with big coefficients penalised"},
    {"name": "lasso", "fit": "lasso_fit", "predict": "linreg_predict", "fit_args": {"alpha": 0.1},
     "says": "the same line, with weak columns pushed to exactly zero"},
    {"name": "tree", "fit": "tree_fit", "predict": "tree_predict",
     "fit_args": {"criterion": "mse", "max_depth": 3}, "needs_seed": True,
     "says": "a depth-3 tree of yes/no splits"},
    {"name": "forest", "fit": "forest_fit", "predict": "forest_predict",
     "fit_args": {"criterion": "mse", "n_trees": 20, "max_depth": 4}, "needs_seed": True,
     "says": "twenty bootstrapped trees, averaged"},
    {"name": "knn", "fit": "knn_fit", "predict": "knn_predict",
     "fit_args": {"task": "regress", "k": 3}, "says": "the average of the three nearest rows"},
)

CLASSIFIERS_TWO = (
    {"name": "logistic", "fit": "logreg_fit", "predict": "logreg_predict", "fit_args": {},
     "says": "one logistic boundary"},
    {"name": "tree", "fit": "tree_fit", "predict": "tree_predict",
     "fit_args": {"criterion": "gini", "max_depth": 3}, "needs_seed": True,
     "says": "a depth-3 tree of yes/no splits"},
    {"name": "forest", "fit": "forest_fit", "predict": "forest_predict",
     "fit_args": {"criterion": "gini", "n_trees": 20, "max_depth": 4}, "needs_seed": True,
     "says": "twenty bootstrapped trees, voting"},
    {"name": "knn", "fit": "knn_fit", "predict": "knn_predict",
     "fit_args": {"task": "classify", "k": 3}, "says": "the vote of the three nearest rows"},
)

CLASSIFIERS_MANY = (
    {"name": "softmax", "fit": "softmax_fit", "predict": "softmax_predict", "fit_args": {},
     "says": "one multinomial logistic boundary per class"},
) + CLASSIFIERS_TWO[1:]


# --- the study's own Calculations: folds over the brain's ----------------------


def _cells(table, name):
    at = list(table["columns"]).index(name)
    return [row[at] for row in table["rows"]]


def _numbers(cells):
    return [float(c) for c in cells if c is not None and not isinstance(c, bool) and isinstance(c, (int, float))]


def _levels_of(cells):
    """the distinct present values of a column, in first-seen order, with their counts."""
    order, counts = [], {}
    for cell in cells:
        if cell is None:
            continue
        key = cell if isinstance(cell, str) else json.dumps(cell, sort_keys=True)
        if key not in counts:
            order.append((key, cell))
            counts[key] = 0
        counts[key] += 1
    return [(label, value, counts[label]) for label, value in order]


def study_values(args):
    """fn.study.values -- one column of a dataset Part as a bare list of numbers.

    every `fn.brain.stats.*` calculation takes `args["values"]` as a list and no
    brain calculation hands one over (`fn.brain.ml.column` returns a mapping), so
    this is the adapter: it drops the holes and says how many it dropped nowhere
    but in the Part that follows it (`describe`'s `n` is the answer).
    See `proposal.study.no_calculation_returns_a_column_as_a_list`.
    """
    return _numbers(_cells(args["table"], args["column"]))


def study_plan(args):
    """fn.study.plan -- what this table can honestly be asked, and what it cannot.

    pure over the table and the three Parts that describe it. Every choice it
    makes is positional and written down: the group column is the FIRST column
    with between 2 and `max_levels` levels of at least `min_group` rows, never
    the one that would give the smallest p-value.
    """
    table, shape, profile = args["table"], args["shape"], args["profile"]
    holes = args["missing"]
    target = args.get("target")
    seed = int(args.get("seed", 7))
    rows = int(shape["rows"])
    kinds = dict(shape["kinds"])
    head = list(profile["columns"])
    prof = {row[head.index("column")]: dict(zip(head, row)) for row in profile["rows"]}

    skipped, numeric, constant, categorical = [], [], [], []
    columns = []
    for name in shape["columns"]:
        row = prof.get(name, {})
        kind = kinds.get(name, "empty")
        n = int(row.get("n") or 0)
        spread = row.get("stdev")
        columns.append({
            "name": name, "kind": kind, "n": n,
            "missing": int(row.get("missing") or 0),
            "distinct": int(row.get("distinct") or 0),
            "mean": row.get("mean"), "stdev": spread,
            "min": row.get("min"), "max": row.get("max"),
        })
        if kind == "number":
            if n < MIN_PROFILE:
                skipped.append({"what": f"profile.{name}", "why": "a column needs at least two present values to describe",
                                "needed": MIN_PROFILE, "had": n})
            elif spread in (None, 0) or float(spread or 0.0) == 0.0:
                constant.append(name)
                skipped.append({"what": f"profile.{name}", "why": "the column never changes, so it has no distribution to describe and no correlation to take",
                                "needed": "any spread", "had": 0.0})
            else:
                numeric.append(name)
        else:
            levels = _levels_of(_cells(table, name))
            categorical.append({"name": name, "kind": kind, "levels": [one[0] for one in levels],
                                "sizes": [one[2] for one in levels]})

    profiled = numeric[:MAX_PROFILE_COLUMNS]
    if len(numeric) > len(profiled):
        skipped.append({"what": "profile.columns", "why": f"only the first {MAX_PROFILE_COLUMNS} varying numeric columns are profiled one by one",
                        "needed": MAX_PROFILE_COLUMNS, "had": len(numeric)})

    complete = [row for row in table["rows"]
                if all(row[list(table["columns"]).index(c)] is not None for c in numeric)]
    complete_rows = len(complete)
    # a column can vary over the whole table and stop varying once the rows with holes
    # are dropped; everything below works on the complete rows, so it is asked there.
    steady = []
    for name in numeric:
        at = list(table["columns"]).index(name)
        if len({row[at] for row in complete}) > 1:
            steady.append(name)
        else:
            skipped.append({"what": f"complete.{name}",
                            "why": "the column stops varying once the rows with a hole anywhere are dropped",
                            "needed": 2, "had": 1})

    # correlations
    correlate = len(steady) >= 2 and complete_rows >= MIN_CORRELATION
    if not correlate:
        skipped.append({"what": "correlation",
                        "why": "a correlation needs two varying numeric columns and enough complete rows to put a p-value beside it",
                        "needed": {"numeric": 2, "rows": MIN_CORRELATION},
                        "had": {"numeric": len(steady), "rows": complete_rows}})

    # the one hypothesis this table invites
    value = target if (target in numeric) else (numeric[0] if numeric else None)
    group, group_levels, group_sizes = None, [], []
    reasons = []
    for candidate in categorical:
        if candidate["name"] == value:
            continue
        keep = [(label, size) for label, size in zip(candidate["levels"], candidate["sizes"]) if size >= MIN_GROUP]
        if len(candidate["levels"]) < 2:
            reasons.append({"column": candidate["name"], "why": "one level only"})
        elif len(candidate["levels"]) > MAX_LEVELS:
            reasons.append({"column": candidate["name"], "why": f"{len(candidate['levels'])} levels is more than the {MAX_LEVELS} the study will split on"})
        elif len(keep) < 2:
            reasons.append({"column": candidate["name"], "why": f"fewer than two levels have the {MIN_GROUP} rows a test needs"})
        else:
            group = candidate["name"]
            group_levels = [label for label, _ in keep]
            group_sizes = [size for _, size in keep]
            break
    tested = sum(group_sizes)
    hypothesis = bool(group and value and tested >= MIN_TEST_ROWS)
    if not hypothesis:
        skipped.append({"what": "hypothesis",
                        "why": "no column splits the rows into two or more groups big enough to compare a numeric column across"
                               if not group else f"the levels of {group} hold {tested} rows between them",
                        "needed": {"levels": 2, "rows_per_level": MIN_GROUP, "rows": MIN_TEST_ROWS},
                        "had": {"candidates": reasons, "value": value, "rows": tested}})

    # clustering
    cluster_columns = steady[:MAX_CLUSTER_COLUMNS]
    ks = []
    if len(cluster_columns) >= 2 and complete_rows >= MIN_CLUSTER_ROWS:
        ks = list(range(2, min(6, max(2, complete_rows // 3)) + 1))
    if not ks:
        skipped.append({"what": "clustering",
                        "why": "clustering needs two varying numeric columns and enough complete rows for three rows a cluster",
                        "needed": {"numeric": 2, "rows": MIN_CLUSTER_ROWS},
                        "had": {"numeric": len(cluster_columns), "rows": complete_rows}})

    # the model comparison
    models, model_kind, classes, folds, baseline = [], None, None, 0, None
    features = [c for c in steady if c != target]
    if target is not None:
        target_kind = kinds.get(target)
        if target not in kinds:
            skipped.append({"what": "model", "why": f"there is no column named {target!r} in this table",
                            "needed": target, "had": list(shape["columns"])})
        elif not features:
            skipped.append({"what": "model", "why": "a model needs at least one varying numeric column that is not the target",
                            "needed": 1, "had": 0})
        else:
            model_rows = [row for row in table["rows"]
                          if all(row[list(table["columns"]).index(c)] is not None for c in features + [target])]
            n = len(model_rows)
            at = list(table["columns"]).index(target)
            distinct = _levels_of([row[at] for row in model_rows])
            asked = args.get("task", "auto")
            label_like = max(2, min(10, n // 5))
            if asked == "regression" or (asked == "auto" and target_kind == "number"
                                         and len(distinct) > label_like):
                model_kind, classes = "regression", None
            else:
                model_kind, classes = "classification", [one[0] for one in distinct]
            folds = max(2, min(5, n // 4))
            if n < MIN_MODEL_ROWS:
                skipped.append({"what": "model", "why": "fewer rows than a cross-validated comparison can say anything with",
                                "needed": MIN_MODEL_ROWS, "had": n})
                model_kind = None
            elif model_kind == "classification" and min((one[2] for one in distinct), default=0) < folds:
                skipped.append({"what": "model", "why": f"a class with fewer than {folds} rows cannot appear in every fold",
                                "needed": folds, "had": min((one[2] for one in distinct), default=0)})
                model_kind = None
            elif model_kind == "classification" and len(distinct) < 2:
                skipped.append({"what": "model", "why": "a classifier needs at least two classes in the target column",
                                "needed": 2, "had": len(distinct)})
                model_kind = None
            else:
                models = REGRESSORS if model_kind == "regression" else (
                    CLASSIFIERS_TWO if len(classes) == 2 else CLASSIFIERS_MANY)
                models = [dict(one, fit_args=dict(one["fit_args"])) for one in models]
                for one in models:
                    if one.get("needs_seed"):
                        one["fit_args"]["seed"] = seed
                if model_kind == "regression":
                    baseline = {"score": 0.0, "says": "predicting the mean of the training rows "
                                                      "(an r2 of 0); a negative r2 is worse than that"}
                else:
                    share = max((one[2] for one in distinct), default=0) / float(n or 1)
                    baseline = {"score": share, "says": "always guessing the commonest class "
                                                        "(%s of the rows)" % _fmt(share, 3)}
    return {
        "for": args.get("for", "what this table can honestly be asked"),
        "rule": ("the group column is the first column with between 2 and %d levels of at least %d rows; "
                 "the value column is --target when it is numeric, else the first varying numeric column. "
                 "Chosen by position, never by which pair gives the smallest p-value." % (MAX_LEVELS, MIN_GROUP)),
        "rows": rows, "complete_rows": complete_rows, "complete_rows_of": list(numeric),
        "columns": columns, "numeric": numeric, "steady": steady, "profiled": profiled, "constant": constant,
        "categorical": categorical, "missing": holes,
        "seed": seed,
        "correlation": {"run": correlate, "columns": steady, "threshold": CORRELATION_THRESHOLD},
        "hypothesis": {"run": hypothesis, "group": group, "value": value,
                       "levels": group_levels, "sizes": group_sizes, "rows": tested, "alpha": ALPHA},
        "clustering": {"run": bool(ks), "columns": cluster_columns, "ks": ks},
        "model": {"run": bool(model_kind), "kind": model_kind, "target": target,
                  "kind_rule": ("--task says so, or: a numeric target with more distinct values than "
                                "max(2, min(10, rows // 5)) is a regression, anything else is a classification"),
                  "features": features, "classes": classes, "folds": folds,
                  "metric": ("r2" if model_kind == "regression" else "accuracy") if model_kind else None,
                  "baseline": baseline,
                  "candidates": [one["name"] for one in models]},
        "models": models,
        "skipped": skipped,
    }


def study_values_by_group(args):
    """fn.study.values_by_group -- the value column split by the group column.

    the shape every `groups=` test in the brain takes (levene, anova, kruskal): a
    list of lists, in the plan's level order, missing cells dropped.
    """
    table, plan = args["table"], args["plan"]
    where = plan["hypothesis"]
    at_group = list(table["columns"]).index(where["group"])
    at_value = list(table["columns"]).index(where["value"])
    out = []
    for label in where["levels"]:
        values = []
        for row in table["rows"]:
            cell = row[at_group]
            key = cell if isinstance(cell, str) else json.dumps(cell, sort_keys=True)
            if key == label and row[at_value] is not None:
                values.append(float(row[at_value]))
        out.append(values)
    return out


def study_group_values(args):
    """fn.study.group_values -- one level's values, for the tests that take two samples."""
    return study_values_by_group(args)[int(args["level_index"])]


def study_group_levels(args):
    """fn.study.group_levels -- which level is which, and how many rows each holds."""
    table, plan = args["table"], args["plan"]
    where = plan["hypothesis"]
    groups = study_values_by_group({"table": table, "plan": plan})
    return {
        "for": args.get("for", f"{where['value']} split by {where['group']}"),
        "group": where["group"], "value": where["value"],
        "levels": list(where["levels"]),
        "sizes": [len(one) for one in groups],
        "means": [(math.fsum(one) / len(one)) if one else None for one in groups],
    }


def study_normality_by_group(args):
    """fn.study.normality_by_group -- `fn.brain.stats.shapiro` per group, as one verdict.

    the assumption check that decides between a t test and a rank test. A group
    too small for shapiro-wilk is not guessed at: it is listed in `skipped` and
    the verdict says the normality of the whole split is unknown.
    """
    hypothesis = brain()["hypothesis"]
    groups = args["groups"]
    levels = args.get("levels") or [f"group {i}" for i in range(len(groups))]
    alpha = float(args.get("alpha", ALPHA))
    backend = args.get("backend", "py")
    checked, skipped = [], []
    for label, values in zip(levels, groups):
        if len(values) < MIN_SHAPIRO or len(values) > MAX_SHAPIRO:
            skipped.append({"level": label, "why": "shapiro-wilk is stated for 3 to 5000 observations",
                            "needed": [MIN_SHAPIRO, MAX_SHAPIRO], "had": len(values)})
            continue
        if len(set(values)) < 2:
            skipped.append({"level": label, "why": "the group never varies, so there is no distribution to test",
                            "needed": 2, "had": 1})
            continue
        verdict = hypothesis.shapiro({"values": values, "backend": backend})
        checked.append({"level": label, "n": len(values), "statistic": verdict["statistic"],
                        "pvalue": verdict["pvalue"], "normal": verdict["pvalue"] >= alpha})
    return {
        "for": args.get("for", "whether each group looks normal enough for a t test"),
        "test": "fn.brain.stats.shapiro", "backend": backend, "alpha": alpha,
        "checked": checked, "skipped": skipped,
        "known": bool(checked) and not skipped,
        "normal": bool(checked) and not skipped and all(one["normal"] for one in checked),
    }


def study_choose_test(args):
    """fn.study.choose_test -- which test the assumption checks allow, and why.

    no search over outcomes: the branch is decided by the number of levels and by
    the two assumption Parts, and the reason is written into the Part beside the
    name of the calculation that will run.
    """
    levels, normal, spread = args["levels"], args["normality"], args["variance"]
    alpha = float(args.get("alpha", ALPHA))
    k = len(levels["levels"])
    equal_var = bool(spread and spread.get("pvalue", 0.0) >= alpha)
    assumptions = [
        {"name": "normality", "test": "fn.brain.stats.shapiro", "alpha": alpha,
         "known": normal["known"], "passed": normal["normal"],
         "detail": [{"level": one["level"], "pvalue": one["pvalue"]} for one in normal["checked"]],
         "unchecked": normal["skipped"]},
        {"name": "equal variance", "test": "fn.brain.stats.levene", "alpha": alpha,
         "known": bool(spread), "passed": equal_var,
         "detail": {"pvalue": spread.get("pvalue") if spread else None}},
    ]
    if k == 2:
        if normal["normal"]:
            chosen = ("ttest_ind", "fn.brain.stats.ttest_ind", "two samples",
                      "both groups pass shapiro-wilk, so the means may be compared directly"
                      + ("; levene passes, so the pooled t test" if equal_var
                         else "; levene fails, so welch's unequal-variance t test"))
            targs = {"equal_var": equal_var}
        else:
            chosen = ("mannwhitneyu", "fn.brain.stats.mannwhitneyu", "two samples",
                      ("normality is not established (%s), so the ranks are compared instead of the means"
                       % ("a group is too small to check" if not normal["known"] else "shapiro-wilk rejects it")))
            targs = {}
    else:
        if normal["normal"] and equal_var:
            chosen = ("f_oneway", "fn.brain.stats.f_oneway", "groups",
                      "every group passes shapiro-wilk and levene, so a one-way anova")
            targs = {}
        else:
            chosen = ("kruskal", "fn.brain.stats.kruskal", "groups",
                      "normality or equal variance is not established, so the rank-based kruskal-wallis")
            targs = {}
    effect = ("cohens_d", "fn.brain.stats.cohens_d", "two samples") if k == 2 else \
             ("eta_squared", "fn.brain.stats.eta_squared", "groups")
    return {
        "for": args.get("for", "the test the assumption checks allow"),
        "levels": list(levels["levels"]), "group": levels["group"], "value": levels["value"],
        "sizes": list(levels["sizes"]),
        "test": chosen[0], "calc": chosen[1], "takes": chosen[2], "why": chosen[3], "args": targs,
        "effect": {"name": effect[0], "calc": effect[1], "takes": effect[2]},
        "alpha": alpha,
        "assumptions": assumptions,
        "refused": [one["name"] for one in assumptions if not one["passed"]],
    }


def study_pairs(args):
    """fn.study.pairs -- the column pairs that actually move together, ranked.

    the coefficient comes from the correlation matrix Part; the p-value beside it
    is `fn.brain.stats.pearson_p` on the same two columns. Every pair is computed
    and every pair is kept in `all`; `matters` is the ones over the threshold, and
    the threshold is in the Part.
    """
    nonparametric = brain()["nonparametric"]
    table, matrix = args["table"], args["correlation"]
    threshold = float(args.get("threshold", CORRELATION_THRESHOLD))
    backend = args.get("backend", "py")
    columns = list(matrix["columns"])
    series = {name: _numbers(_cells(table, name)) for name in columns}
    n = min((len(one) for one in series.values()), default=0)
    every = []
    for i, a in enumerate(columns):
        for b in columns[i + 1:]:
            r = float(matrix["matrix"][i][columns.index(b)])
            row = {"a": a, "b": b, "r": r, "abs": abs(r)}
            if n >= MIN_CORRELATION and len(series[a]) == len(series[b]):
                verdict = nonparametric.pearson_p({"x": series[a], "y": series[b], "backend": backend})
                row["pvalue"] = verdict["pvalue"]
                row["n"] = verdict["n"]
            every.append(row)
    every.sort(key=lambda one: (-one["abs"], one["a"], one["b"]))
    return {
        "for": args.get("for", "which columns move together, and whether that is more than luck"),
        "threshold": threshold, "n": n, "backend": backend,
        "test": "fn.brain.stats.pearson_p",
        "all": every,
        "matters": [one for one in every if one["abs"] >= threshold],
    }


def study_best_of(args):
    """fn.study.best_of -- the winner among candidates, by a score already recorded.

    every candidate arrives as a Part bound under `c_<name>`; the score is read at
    `score_key` and nothing is recomputed, so the choice is a fact about the store
    and `margin` is how much the runner-up lost by.
    """
    names = list(args["candidates"])
    key = args.get("score_key", "mean")
    direction = args.get("direction", "higher")
    table = []
    for name in names:
        part = args[f"c_{name}"]
        value = part
        for step in (key if isinstance(key, list) else [key]):
            value = value[step]
        table.append({"name": name, "score": float(value), "from": args.get("addresses", {}).get(name)})
    if not table:
        raise ValueError("best_of needs at least one candidate")
    table.sort(key=lambda one: (-one["score"] if direction == "higher" else one["score"], one["name"]))
    margin = abs(table[0]["score"] - table[1]["score"]) if len(table) > 1 else None
    floor = args.get("floor")
    beats = True
    if floor is not None:
        beats = (table[0]["score"] > floor["score"]) if direction == "higher" \
            else (table[0]["score"] < floor["score"])
    return {
        "for": args.get("for", "the candidate the recorded scores prefer"),
        "by": args.get("by", key if isinstance(key, str) else ".".join(key)),
        "direction": direction,
        "chosen": table[0]["name"], "score": table[0]["score"],
        "runner_up": table[1]["name"] if len(table) > 1 else None,
        "margin": margin,
        "floor": floor,
        "beats_floor": bool(beats),
        "ranking": table,
    }


def study_model_table(args):
    """fn.study.model_table -- the feature columns and the target, ready to fit.

    the ml vertical's dataset Part is all numbers, so a categorical target is
    encoded to its class index here and the classes it stands for ride along on
    the Part. Nothing else changes: the rows are the rows.
    """
    table = args["table"]
    target = args["target"]
    features = list(args["features"])
    columns = list(table["columns"])
    at = [columns.index(name) for name in features]
    at_target = columns.index(target)
    raw = [row[at_target] for row in table["rows"]]
    classes = args.get("classes")
    if classes:
        codes = {label: float(index) for index, label in enumerate(classes)}

        def code(cell):
            key = cell if isinstance(cell, str) else json.dumps(cell, sort_keys=True)
            if key not in codes:
                raise ValueError(f"the target holds {cell!r}, which is not one of {list(codes)}")
            return codes[key]
    else:
        def code(cell):
            return float(cell)
    rows = [[float(row[i]) for i in at] + [code(row[at_target])] for row in table["rows"]]
    out = {
        "for": args.get("for", f"{target} and the columns that might explain it"),
        "columns": features + [target],
        "rows": rows,
        "target": target,
        "kind": "classification" if classes else "regression",
    }
    if classes:
        out["classes"] = list(classes)
        out["counts"] = [sum(1 for cell in raw if (cell if isinstance(cell, str) else json.dumps(cell, sort_keys=True)) == label)
                         for label in classes]
    return out


# --- the summary: prose that cites the Part every number came from -------------


def _fmt(value, places=3):
    if value is None:
        return "?"
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if value != value:
            return "nan"
        if value and (abs(value) < 1e-3 or abs(value) >= 1e6):
            return f"{value:.2e}"
        text = f"{value:.{places}f}".rstrip("0").rstrip(".")
        return text or "0"
    return str(value)


def _p(value):
    if value is None:
        return "?"
    return "<0.001" if value < 0.001 else _fmt(value, 3)


def study_summary(args):
    """fn.study.summary -- the study in sentences, every number citing its Part.

    it computes nothing. Each line carries `cites`: the address, the key path and
    the value, so `tests/test_study.py` can walk the store and check the prose
    against the Parts rather than against another copy of the same arithmetic.
    """
    addresses = dict(args.get("addresses", {}))
    plan = args["plan"]
    sections = []

    def cite(binding, path, transform=None):
        value = args[binding]
        for step in path:
            value = value[step] if not isinstance(value, list) else value[int(step)]
        return {"address": addresses.get(binding), "binding": binding, "path": list(path), "value": value} \
            if transform is None else {"address": addresses.get(binding), "binding": binding,
                                       "path": list(path), "value": transform(value)}

    def line(text, *cites):
        return {"text": text, "cites": [one for one in cites if one is not None]}

    def section(title, lines, note=None):
        sections.append({"title": title, "lines": [one for one in lines if one], "note": note})

    # 1. the table
    rows = cite("plan", ["rows"])
    complete = cite("plan", ["complete_rows"])
    columns = plan["columns"]
    kinds = {}
    for one in columns:
        kinds[one["kind"]] = kinds.get(one["kind"], 0) + 1
    holes = sum(one["missing"] for one in columns)
    section("the table", [
        line(f"{args.get('source', 'the table')}: {rows['value']} rows, {len(columns)} columns "
             f"({', '.join(f'{count} {kind}' for kind, count in sorted(kinds.items()))}).", rows),
        line(f"{complete['value']} rows have every numeric column present; {holes} cells are missing in total.", complete),
        line("varying numeric columns: " + (", ".join(plan["numeric"]) or "none")
             + ("; constant: " + ", ".join(plan["constant"]) if plan["constant"] else "")),
    ])

    # 2. the columns
    lines = []
    for one in args.get("columns", []):
        name, key = one["name"], one["binding"]
        if key not in args:
            continue
        d = args[key]
        parts = [f"{name}: n={d['n']}, mean {_fmt(d['mean'])} (sd {_fmt(d['stdev'])}), "
                 f"median {_fmt(d['median'])}, range {_fmt(d['min'])} to {_fmt(d['max'])}"]
        cites = [cite(key, ["mean"]), cite(key, ["stdev"]), cite(key, ["n"])]
        if one.get("outliers") in args:
            out = args[one["outliers"]]
            parts.append(f"{out['outliers']} outlier(s) by the iqr rule "
                         f"(outside {_fmt(out['bounds']['low'])} to {_fmt(out['bounds']['high'])})")
            cites.append(cite(one["outliers"], ["outliers"]))
        if one.get("normality") in args:
            norm = args[one["normality"]]
            verdict = "normal enough" if norm["pvalue"] >= ALPHA else "not normal"
            parts.append(f"shapiro p={_p(norm['pvalue'])}, {verdict}")
            cites.append(cite(one["normality"], ["pvalue"]))
        if "skewness" in d:
            parts.append(f"skew {_fmt(d['skewness'], 2)}")
            cites.append(cite(key, ["skewness"]))
        lines.append(line("; ".join(parts) + ".", *cites))
    for one in plan["categorical"]:
        shown = list(zip(one["levels"], one["sizes"]))[:MAX_LEVELS]
        more = len(one["levels"]) - len(shown)
        lines.append(line(f"{one['name']}: {one['kind']}, {len(one['levels'])} level(s) -- "
                          + ", ".join(f"{label} ({size})" for label, size in shown)
                          + (f", and {more} more" if more > 0 else "") + "."))
    section("the columns", lines)

    # 3. what moves together
    if "pairs" in args:
        pairs = args["pairs"]
        lines = []
        for index, one in enumerate(pairs["matters"][:6]):
            p = one.get("pvalue")
            lines.append(line(
                f"{one['a']} and {one['b']}: r = {_fmt(one['r'])}"
                + (f", p = {_p(p)} on n = {one.get('n', pairs['n'])}" if p is not None else "")
                + ("." if p is None else (" -- more than luck at 0.05." if p < ALPHA else " -- inside what chance would give.")),
                cite("pairs", ["matters", index, "r"]),
                cite("pairs", ["matters", index, "pvalue"]) if p is not None else None))
        if not pairs["matters"]:
            lines.append(line(f"no pair of columns reaches |r| >= {pairs['threshold']}; "
                              f"the strongest is {pairs['all'][0]['a']} and {pairs['all'][0]['b']} at "
                              f"r = {_fmt(pairs['all'][0]['r'])}." if pairs["all"] else "there was nothing to pair.",
                              cite("pairs", ["all", 0, "r"]) if pairs["all"] else None))
        section("what moves together", lines,
                note=(f"pearson, on {pairs['n']} complete rows."
                      + (" A correlation on this few rows swings hard with one row; read it as a "
                         "direction, not a measurement." if pairs["n"] < 30 else "")))

    # 4. the hypothesis
    if "test" in args and "choice" in args:
        choice, verdict = args["choice"], args["test"]
        levels = args["levels"]
        lines = [line(
            f"{choice['value']} across {choice['group']}: "
            + ", ".join(f"{label} (n={size}, mean {_fmt(mean)})"
                        for label, size, mean in zip(levels["levels"], levels["sizes"], levels["means"])) + ".",
            cite("levels", ["sizes"]), cite("levels", ["means"]))]
        for one in choice["assumptions"]:
            if one["name"] == "normality":
                if one["known"]:
                    lines.append(line("normality (shapiro-wilk): "
                                      + ", ".join(f"{d['level']} p={_p(d['pvalue'])}" for d in one["detail"])
                                      + f" -- {'passes' if one['passed'] else 'fails'} at {one['alpha']}.",
                                      cite("normality", ["checked"])))
                else:
                    lines.append(line("normality: not established -- "
                                      + "; ".join(f"{d['level']}: {d['why']}" for d in one["unchecked"]) + ".",
                                      cite("normality", ["skipped"])))
            elif one["detail"].get("pvalue") is not None:
                lines.append(line(f"equal variance (levene): p={_p(one['detail']['pvalue'])} -- "
                                  f"{'passes' if one['passed'] else 'fails'} at {one['alpha']}.",
                                  cite("variance", ["pvalue"])))
        lines.append(line(f"so the study ran {choice['calc']}: {choice['why']}."))
        lines.append(line(
            f"{choice['test']}: statistic {_fmt(verdict['statistic'])}, p = {_p(verdict['pvalue'])} -- "
            + ("the groups differ by more than chance at 0.05."
               if verdict["pvalue"] < ALPHA else
               "no difference this test can tell from chance at 0.05."),
            cite("test", ["statistic"]), cite("test", ["pvalue"])))
        if "effect" in args:
            size = args["effect"]
            lines.append(line(f"effect size ({choice['effect']['name']}): {_fmt(size, 3)}.", cite("effect", [])))
        section("the hypothesis", lines,
                note="the pair was chosen by position, not by its p-value: " + plan["rule"])

    # 5. the clusters
    if "bestk" in args:
        best = args["bestk"]
        chosen = best["chosen"]
        km, sil = args.get(f"km_{chosen}"), args.get(f"sil_{chosen}")
        scale = "a silhouette above 0.5 is a real separation, 0.25 to 0.5 is weak, below 0.25 is none"
        mean = sil["mean"]
        verdict = "the clusters are real" if mean >= 0.5 else (
            "the clusters are weak" if mean >= 0.25 else "there are no clusters here worth the name")
        sizes = {}
        for label in km["labels"]:
            sizes[label] = sizes.get(label, 0) + 1
        lines = [
            line(f"k = {chosen} of the {len(best['ranking'])} tried scores best: silhouette {_fmt(mean)} -- {verdict}.",
                 cite("bestk", ["score"]), cite(f"sil_{chosen}", ["mean"])),
            line("every k tried: " + ", ".join(f"k={one['name']} {_fmt(one['score'])}" for one in best["ranking"]) + ".",
                 cite("bestk", ["ranking"])),
            line("cluster sizes: " + ", ".join(f"{label}: {size}" for label, size in sorted(sizes.items()))
                 + f", over {len(plan['clustering']['columns'])} standardised columns ("
                 + ", ".join(plan["clustering"]["columns"]) + ")."),
        ]
        section("the clusters", lines, note=scale)

    # 6. the directions
    if "pca" in args:
        pca = args["pca"]
        ratio = pca["explained_variance_ratio"]
        lines = [line(
            f"the first {len(ratio)} components hold {_fmt(100.0 * sum(ratio), 1)}% of the variance "
            f"({', '.join(_fmt(100.0 * one, 1) + '%' for one in ratio)}).", cite("pca", ["explained_variance_ratio"]))]
        names = plan["clustering"]["columns"]
        for index, component in enumerate(pca["components"][:2]):
            weighted = sorted(zip(names, component), key=lambda pair: -abs(pair[1]))[:3]
            lines.append(line(f"component {index + 1} is mostly "
                              + ", ".join(f"{name} ({_fmt(value, 2)})" for name, value in weighted) + ".",
                              cite("pca", ["components", index])))
        section("the directions the data varies in", lines)

    # 7. the model
    if "best" in args:
        best = args["best"]
        model = plan["model"]
        metric = model["metric"]
        floor = best.get("floor") or {}
        lines = [
            line(f"{best['chosen']} wins on {metric}: {_fmt(best['score'], 4)}"
                 + (f", ahead of {best['runner_up']} by {_fmt(best['margin'], 4)}." if best["runner_up"] else "."),
                 cite("best", ["score"]), cite("best", ["margin"]) if best["margin"] is not None else None),
            line((f"and it clears the baseline ({_fmt(floor.get('score'), 4)}: {floor.get('says')}), "
                  "so this study will name it a predictor."
                  if best.get("beats_floor") else
                  f"but it does NOT clear the baseline ({_fmt(floor.get('score'), 4)}: {floor.get('says')}), "
                  "so this study names no predictor: on these rows, nothing here beats the obvious guess."),
                 cite("best", ["beats_floor"])),
            line("every candidate, same folds, same seed: "
                 + ", ".join(f"{one['name']} {_fmt(one['score'], 4)}" for one in best["ranking"]) + ".",
                 cite("best", ["ranking"])),
            line(f"{model['folds']}-fold cross-validation of {model['target']} on "
                 f"{len(model['features'])} column(s) ({', '.join(model['features'])}), seed {plan['seed']}."),
        ]
        section("the best predictor", lines, note=(args.get("model_note") or "").strip() or None)

    # 8. what the study would not say
    refusals = list(plan["skipped"]) + list(args.get("skipped", []))
    if "best" in args and not args["best"].get("beats_floor", True):
        refusals.append({"what": "model.winner",
                         "why": "no candidate beat the baseline, so the study names no predictor",
                         "needed": (args["best"].get("floor") or {}).get("score"),
                         "had": args["best"]["score"]})
    section("what this study would not say", [
        line(f"{one['what']}: {one['why']}"
             + (f" (needed {json.dumps(one['needed'])}, had {json.dumps(one['had'])})" if "needed" in one else "") + ".")
        for one in refusals
    ] or [line("nothing was refused: every step the plan named ran.")])

    return {
        "for": args.get("for", "the study, in sentences whose numbers name the Part they came from"),
        "name": args.get("name"), "source": args.get("source"),
        "rows": plan["rows"], "columns": len(plan["columns"]),
        "sections": sections,
        "refused": len(refusals),
    }


def study_map(args):
    """fn.study.map -- what ran, what was refused, and where every Part of it is.

    the one Part a reader should open first, and the one `PQL.prefix` reaches for:
    every invocation of every Tick with the address it wrote, beside every step
    the plan would not allow and why.
    """
    plan, summary = args["plan"], args["summary"]
    ran = list(args.get("ran", []))
    skipped = list(plan["skipped"]) + list(args.get("skipped", []))
    best = args.get("best")
    if best and not best.get("beats_floor", True):
        skipped.append({"what": "model.winner",
                        "why": "no candidate beat the baseline, so the study names no predictor",
                        "needed": (best.get("floor") or {}).get("score"), "had": best["score"]})
    calcs = {}
    for one in ran:
        calcs[one["calc"]] = calcs.get(one["calc"], 0) + 1
    return {
        "for": args.get("for", "what this study ran, what it refused, and where to read each answer"),
        "name": args.get("name"), "source": args.get("source"),
        "records": list(args.get("records", [])),
        "ran": ran,
        "skipped": skipped,
        "calculations": dict(sorted(calcs.items())),
        "engines": args.get("engines", {}),
        "counts": {"steps": len(ran), "skipped": len(skipped),
                   "calculations": len(calcs), "sections": len(summary["sections"])},
    }


# --- the calculations, by name ------------------------------------------------

_CALCS = {}


def calcs():
    """the study's own Calculations, built once. `fn.study.*`: folds over the brain."""
    if _CALCS:
        return _CALCS
    from pyto import Calculation

    for name, fn in (
        ("values", study_values), ("plan", study_plan), ("values_by_group", study_values_by_group),
        ("group_values", study_group_values), ("group_levels", study_group_levels),
        ("normality_by_group", study_normality_by_group), ("choose_test", study_choose_test),
        ("pairs", study_pairs), ("best_of", study_best_of), ("model_table", study_model_table),
        ("summary", study_summary), ("map", study_map),
    ):
        _CALCS[name] = Calculation(f"fn.study.{name}", fn)
    return _CALCS


def brain_calc(address):
    """one brain `Calculation` by its address, whichever vertical owns it."""
    b = brain()
    if address.startswith("fn.brain.ml."):
        return b["ml"].calc(address.rsplit(".", 1)[-1])
    for key in ("frame", "shaping", "transform", "datasets", "descriptive",
                "correlation", "hypothesis", "comparisons", "intervals", "nonparametric"):
        table = getattr(b[key], "CALCS", {})
        if address in table:
            return table[address]
    raise KeyError(f"study: no brain Calculation at {address}")


# --- the program --------------------------------------------------------------

WANTED_ENGINES = (
    ("stats", "describe", ("py", "np")), ("stats", "mean", ("py", "np")),
    ("stats", "variance", ("py", "np")), ("stats", "quantile", ("py", "np")),
    ("stats", "skewness", ("py", "np")), ("stats", "shapiro", ("py", "sp")),
    ("stats", "pearson", ("py", "np")), ("stats", "levene", ("py", "sp")),
    ("stats", "ttest_ind", ("py", "sp")), ("stats", "mannwhitneyu", ("py", "sp")),
    ("stats", "kruskal", ("py", "sp")), ("data", "outliers", ("py", "np")),
    ("data", "standardize", ("py", "np")), ("ml", "kmeans", ("py", "np", "gram")),
    ("ml", "silhouette", ("py", "np")), ("ml", "linreg_fit", ("py", "np")),
    ("ml", "logreg_fit", ("py", "np")), ("ml", "softmax_fit", ("py", "np")),
    ("ml", "lasso_fit", ("py", "np")), ("ml", "knn_predict", ("py", "np")),
)


class Program:
    """the study as declared steps: what to run, where it writes, what it read."""

    def __init__(self, store, prefix, plan_part):
        self.store = store
        self.prefix = prefix
        self.plan_part = plan_part
        self.ticks = []
        self.ran = []
        self.skipped = []

    def at(self, *segments):
        return self.prefix + ".".join(str(one) for one in segments)

    def tick(self, name):
        self.ticks.append((name, []))
        return self.ticks[-1][1]

    def step(self, steps, step_id, calc, into, args=None, **inputs):
        steps.append({"id": step_id, "calc": calc, "into": into, "args": dict(args or {}), "inputs": inputs})
        self.ran.append({"id": step_id, "calc": getattr(calc, "address", str(calc)), "into": into,
                         "tick": self.ticks[-1][0]})
        return into

    def refuse(self, what, why, needed=None, had=None):
        entry = {"what": what, "why": why}
        if needed is not None:
            entry["needed"] = needed
            entry["had"] = had
        self.skipped.append(entry)
        return entry

    def run(self, name, effects_root=None):
        run = self.store.run(name, self.ticks, effects_root=effects_root)
        self.ticks = []
        return run


def read_program(store, prefix, plan_part, source_name, fmt, target, seed, for_, task="auto"):
    """`study_read`: the table, its shape, its per-column summary, and the plan."""
    program = Program(store, prefix, plan_part)
    auto = lambda v, c, e: engine(plan_part, v, c, e)  # noqa: E731
    steps = program.tick("read")
    table = program.step(steps, "load", brain_calc("oc.brain.data.load"), program.at("table"),
                         {"path": source_name, "format": fmt, "for": for_})
    steps = program.tick("shape")
    shape = program.step(steps, "shape", brain_calc("fn.brain.data.shape"), program.at("shape"), table=table)
    holes = program.step(steps, "missing", brain_calc("fn.brain.data.missing_report"),
                         program.at("missing"), table=table)
    profile = program.step(steps, "profile", brain_calc("fn.brain.data.describe_table"), program.at("profile"),
                           {"backend": auto("data", "describe_table", ("py", "np")),
                            "for": "every column of %s, summarised" % source_name}, table=table)
    steps = program.tick("plan")
    program.step(steps, "plan", calcs()["plan"], program.at("plan"),
                 {"target": target, "seed": seed, "task": task,
                  "for": "what this table can honestly be asked"},
                 table=table, shape=shape, missing=holes, profile=profile)
    return program


def weigh_program(store, prefix, plan_part, plan):
    """`study_weigh`: the split and the assumption checks the test choice reads."""
    program = Program(store, prefix, plan_part)
    auto = lambda v, c, e: engine(plan_part, v, c, e)  # noqa: E731
    where = plan["hypothesis"]
    table, planned = program.at("table"), program.at("plan")
    steps = program.tick("split")
    groups = program.step(steps, "groups", calcs()["values_by_group"], program.at("groups"),
                          {"for": f"{where['value']} split by {where['group']}"}, table=table, plan=planned)
    levels = program.step(steps, "levels", calcs()["group_levels"], program.at("levels"),
                          table=table, plan=planned)
    if len(where["levels"]) == 2:
        for index, side in enumerate(("x", "y")):
            program.step(steps, side, calcs()["group_values"], program.at("group", side),
                         {"level_index": index, "for": f"the {where['levels'][index]} rows"},
                         table=table, plan=planned)
    steps = program.tick("assume")
    normality = program.step(steps, "normality", calcs()["normality_by_group"], program.at("normality"),
                             {"levels": where["levels"], "alpha": ALPHA,
                              "backend": auto("stats", "shapiro", ("py", "sp"))}, groups=groups)
    variance = program.step(steps, "variance", brain_calc("fn.brain.stats.levene"), program.at("variance"),
                            {"backend": auto("stats", "levene", ("py", "sp")), "center": "median"}, groups=groups)
    steps = program.tick("choose")
    program.step(steps, "choice", calcs()["choose_test"], program.at("choice"), {"alpha": ALPHA},
                 levels=levels, normality=normality, variance=variance)
    return program


def study_program(store, prefix, plan_part, plan, choice, source, name):
    """`study`: every step the plan allowed, ending in the summary and the map."""
    program = Program(store, prefix, plan_part)
    auto = lambda v, c, e: engine(plan_part, v, c, e)  # noqa: E731
    table = program.at("table")
    bindings = {"plan": program.at("plan")}
    columns_for_summary = []

    steady = plan["steady"]
    complete = None
    if steady:
        steps = program.tick("frame")
        numeric = program.step(steps, "numeric", brain_calc("fn.brain.data.select"), program.at("numeric"),
                               {"columns": steady, "for": "the varying numeric columns of " + source}, table=table)
        complete = program.step(steps, "complete", brain_calc("fn.brain.data.missing"), program.at("complete"),
                                {"strategy": "drop", "how": "any",
                                 "for": "the rows with every numeric column present"}, table=numeric)

    profiled = [c for c in plan["profiled"] if c in steady]
    names = slugs(profiled)
    if complete is not None and profiled:
        steps = program.tick("columns")
        rows = plan["complete_rows"]
        for column, key in zip(profiled, names):
            only = program.step(steps, f"only_{key}", brain_calc("fn.brain.data.select"),
                                program.at("column", key, "only"), {"columns": [column]}, table=complete)
            values = program.step(steps, f"values_{key}", calcs()["values"], program.at("column", key, "values"),
                                  {"column": column}, table=only)
            described = program.step(steps, f"describe_{key}", brain_calc("fn.brain.stats.describe"),
                                     program.at("column", key, "describe"),
                                     {"backend": auto("stats", "describe", ("py", "np"))}, values=values)
            entry = {"name": column, "binding": f"d_{key}"}
            bindings[f"d_{key}"] = described
            if MIN_SHAPIRO <= rows <= MAX_SHAPIRO:
                normal = program.step(steps, f"normal_{key}", brain_calc("fn.brain.stats.shapiro"),
                                      program.at("column", key, "normality"),
                                      {"backend": auto("stats", "shapiro", ("py", "sp"))}, values=values)
                entry["normality"] = f"n_{key}"
                bindings[f"n_{key}"] = normal
            else:
                program.refuse(f"normality.{column}", "shapiro-wilk is stated for 3 to 5000 observations",
                               [MIN_SHAPIRO, MAX_SHAPIRO], rows)
            flagged = program.step(steps, f"outliers_{key}", brain_calc("fn.brain.data.outliers"),
                                   program.at("column", key, "outliers"),
                                   {"column": column, "rule": "iqr", "k": 1.5,
                                    "backend": auto("data", "outliers", ("py", "np"))}, table=only)
            entry["outliers"] = f"o_{key}"
            bindings[f"o_{key}"] = flagged
            columns_for_summary.append(entry)

    if plan["correlation"]["run"]:
        steps = program.tick("correlate")
        matrix = program.step(steps, "correlation", brain_calc("fn.brain.stats.correlation_matrix"),
                              program.at("correlation"),
                              {"columns": plan["correlation"]["columns"], "method": "pearson",
                               "backend": auto("stats", "pearson", ("py", "np"))}, table=complete)
        program.step(steps, "spearman", brain_calc("fn.brain.stats.correlation_matrix"),
                     program.at("correlation_spearman"),
                     {"columns": plan["correlation"]["columns"], "method": "spearman",
                      "backend": auto("stats", "pearson", ("py", "np"))}, table=complete)
        bindings["pairs"] = program.step(steps, "pairs", calcs()["pairs"], program.at("pairs"),
                                         {"threshold": CORRELATION_THRESHOLD,
                                          "backend": auto("stats", "ttest_ind", ("py", "sp"))},
                                         table=complete, correlation=matrix)

    if choice is not None:
        steps = program.tick("test")
        takes = choice["takes"]
        inputs = ({"x": program.at("group", "x"), "y": program.at("group", "y")}
                  if takes == "two samples" else {"groups": program.at("groups")})
        verdict = program.step(steps, "test", brain_calc(choice["calc"]), program.at("test"),
                               dict(choice["args"], backend=auto("stats", choice["test"], ("py", "sp")),
                                    **{"for": f"{choice['value']} across {choice['group']}"}), **inputs)
        effect = program.step(steps, "effect", brain_calc(choice["effect"]["calc"]), program.at("effect"),
                              {}, **({"x": inputs["x"], "y": inputs["y"]} if takes == "two samples"
                                     else {"groups": program.at("groups")}))
        bindings.update(choice=program.at("choice"), levels=program.at("levels"),
                        normality=program.at("normality"), variance=program.at("variance"),
                        test=verdict, effect=effect)

    if plan["clustering"]["run"]:
        steps = program.tick("standardise")
        source_table = complete
        zs = []
        for column, key in zip(plan["clustering"]["columns"], slugs(plan["clustering"]["columns"])):
            label = f"{column}__z"
            zs.append(label)
            source_table = program.step(steps, f"z_{key}", brain_calc("fn.brain.data.standardize"),
                                        program.at("standard", key),
                                        {"column": column, "as": label, "ddof": 0,
                                         "backend": auto("data", "standardize", ("py", "np"))},
                                        table=source_table)
        standard = program.step(steps, "standard", brain_calc("fn.brain.data.select"), program.at("standard"),
                                {"columns": zs, "for": "every numeric column in standard-deviation units"},
                                table=source_table)
        steps = program.tick("cluster")
        candidates, addresses = [], {}
        for k in plan["clustering"]["ks"]:
            fitted = program.step(steps, f"kmeans_{k}", brain_calc("fn.brain.ml.kmeans"),
                                  program.at("cluster", f"k{k}"),
                                  {"k": k, "seed": plan["seed"],
                                   "backend": auto("ml", "kmeans", ("py", "np", "gram")),
                                   "for": f"{k} clusters of {source}"}, data=standard)
            scored = program.step(steps, f"silhouette_{k}", brain_calc("fn.brain.ml.silhouette"),
                                  program.at("silhouette", f"k{k}"),
                                  {"backend": auto("ml", "silhouette", ("py", "np"))},
                                  data=standard, labels=fitted)
            candidates.append(str(k))
            addresses[str(k)] = scored
            bindings[f"km_{k}"] = fitted
            bindings[f"sil_{k}"] = scored
        steps = program.tick("weigh the clusters")
        bindings["bestk"] = program.step(
            steps, "bestk", calcs()["best_of"], program.at("clusters"),
            {"candidates": candidates, "score_key": "mean", "direction": "higher", "addresses": addresses,
             "by": "the mean silhouette", "for": "how many clusters the silhouette actually supports"},
            **{f"c_{one}": addresses[one] for one in candidates})
        steps = program.tick("directions")
        bindings["pca"] = program.step(steps, "pca", brain_calc("fn.brain.ml.pca"), program.at("pca"),
                                       {"n_components": min(2, len(plan["clustering"]["columns"])),
                                        "for": "the directions this table actually varies in"}, data=standard)

    model_note = None
    if plan["model"]["run"]:
        model = plan["model"]
        steps = program.tick("frame the model")
        chosen = program.step(steps, "model_columns", brain_calc("fn.brain.data.select"),
                              program.at("model", "columns"),
                              {"columns": model["features"] + [model["target"]]}, table=table)
        kept = program.step(steps, "model_rows", brain_calc("fn.brain.data.missing"),
                            program.at("model", "rows"), {"strategy": "drop", "how": "any"}, table=chosen)
        fitting = program.step(steps, "model_table", calcs()["model_table"], program.at("model", "table"),
                               {"target": model["target"], "features": model["features"],
                                "classes": model["classes"]}, table=kept)
        steps = program.tick("cross-validate")
        candidates, addresses = [], {}
        for one in plan["models"]:
            into = program.at("model", "cv", slug(one["name"]))
            program.step(steps, f"cv_{slug(one['name'])}", brain_calc("fn.brain.ml.cross_validate"), into,
                         {"target": model["target"], "seed": plan["seed"], "k": model["folds"],
                          "fit": one["fit"], "predict": one["predict"], "fit_args": one["fit_args"],
                          "metric": model["metric"], "for": one["says"]}, data=fitting)
            candidates.append(one["name"])
            addresses[one["name"]] = into
            bindings[f"cv_{one['name']}"] = into
        steps = program.tick("weigh the models")
        bindings["best"] = program.step(
            steps, "best", calcs()["best_of"], program.at("model", "best"),
            {"candidates": candidates, "score_key": "mean",
             "direction": "lower" if model["metric"] in ("mse", "mae") else "higher",
             "addresses": addresses, "floor": model["baseline"],
             "by": f"the cross-validated {model['metric']}",
             "for": "the model the folds preferred, not the one anyone expected"},
            **{f"c_{one}": addresses[one] for one in candidates})
        model_note = (f"every score is the mean over {model['folds']} folds of the same "
                      f"{len(plan['models'])} candidates on the same rows and the same seed."
                      + (" A cross-validated score on this few rows is a hint, not a measurement."
                         if plan["rows"] < 60 else ""))
    return program, bindings, columns_for_summary, model_note


# --- the page -----------------------------------------------------------------

PAGE_STYLE = """
<style id="study-summary-style">
  .study-summary { font: 15px/1.55 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    max-width: 62rem; margin: 0 auto; padding: 1.5rem 1.25rem 0.5rem; }
  .study-summary h1 { font-size: 1.45rem; margin: 0 0 .2rem; }
  .study-summary .source { opacity: .7; font-size: .9rem; margin-bottom: 1.2rem; }
  .study-summary section { margin: 0 0 1.15rem; }
  .study-summary h2 { font-size: 1rem; text-transform: lowercase; letter-spacing: .02em;
    margin: 0 0 .35rem; padding-bottom: .2rem; border-bottom: 1px solid currentColor; opacity: .85; }
  .study-summary ul { margin: .2rem 0; padding-left: 1.1rem; }
  .study-summary li { margin: .15rem 0; }
  .study-summary .note { opacity: .68; font-size: .88rem; font-style: italic; margin-top: .3rem; }
  .study-summary .cites { opacity: .55; font-size: .78rem; font-family: ui-monospace, Menlo, Consolas, monospace; }
  .study-summary .refused li { opacity: .8; }
  .study-summary hr { margin: 1.4rem 0 0; border: 0; border-top: 1px solid currentColor; opacity: .25; }
</style>
"""


def escape(text):
    return (str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def summary_html(summary):
    """the summary Part as the block that sits above the Tick viewer."""
    out = [PAGE_STYLE, '<div class="study-summary">',
           f"<h1>{escape(summary.get('name') or 'study')}</h1>",
           f"<p class=\"source\">{escape(summary.get('source'))} &middot; "
           f"{summary['rows']} rows &times; {summary['columns']} columns &middot; "
           f"{summary['refused']} step(s) refused</p>"]
    for section in summary["sections"]:
        refused = "refused" if section["title"].startswith("what this study would not") else ""
        out.append(f'<section class="{refused}"><h2>{escape(section["title"])}</h2><ul>')
        for line in section["lines"]:
            cites = " ".join(escape(one["address"] or one["binding"]) for one in line["cites"] if one)
            out.append(f"<li>{escape(line['text'])}"
                       + (f' <span class="cites">{cites}</span>' if cites else "") + "</li>")
        out.append("</ul>")
        if section.get("note"):
            out.append(f'<p class="note">{escape(section["note"])}</p>')
        out.append("</section>")
    out.append("<hr></div>")
    return "\n".join(out)


def fallback_page(summary, records):
    """the page when node is not there: the same summary, the records still embedded."""
    blocks = "\n".join(
        f'<script type="application/json" id="record-{index}">\n'
        + json.dumps(record, indent=2).replace("<", "\\u003c") + "\n</script>"
        for index, record in enumerate(records))
    return ("<!doctype html>\n<html><head><meta charset=\"utf-8\">"
            f"<title>{escape(summary.get('name') or 'study')}</title></head><body>\n"
            + summary_html(summary)
            + '\n<p class="study-summary">The Tick viewer needs node to be baked in; the run records are '
              'embedded below and open in <code>pyto/viewer/tick-viewer.html</code>.</p>\n'
            + blocks + "\n</body></html>\n")


def write_page(out_dir, summary, record_paths):
    """study.html: the summary over the Tick viewer, one file, no server.

    the viewer page is built by `pyto/viewer/embed.mjs` -- the same builder the
    studio uses -- and the summary block is spliced in after `<body>`. Without
    node the summary is still written, with the records embedded raw.
    """
    target = os.path.join(out_dir, "study.html")
    viewer = os.path.join(brain()["pyto_root"], "viewer", "embed.mjs")
    block = summary_html(summary)
    page = None
    if os.path.isfile(viewer) and record_paths:
        try:
            built = subprocess.run(["node", viewer] + list(record_paths),
                                   capture_output=True, text=True, timeout=180)
            if built.returncode == 0 and "<body" in built.stdout:
                opened = built.stdout.index("<body")
                closed = built.stdout.index(">", opened)
                page = built.stdout[:closed + 1] + "\n" + block + built.stdout[closed + 1:]
        except (OSError, subprocess.SubprocessError):
            page = None
    if page is None:
        records = []
        for path in record_paths:
            with open(path, encoding="utf-8") as handle:
                records.append(json.load(handle))
        page = fallback_page(summary, records)
    with open(target, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(page)
    return target


def print_summary(summary, stream=sys.stdout):
    """the same Part, in the terminal."""
    stream.write(f"{summary.get('name')}  --  {summary.get('source')}\n")
    for section in summary["sections"]:
        stream.write(f"\n== {section['title']}\n")
        for line in section["lines"]:
            stream.write(f"  - {line['text']}\n")
        if section.get("note"):
            stream.write(f"  ({section['note']})\n")


# --- findings -----------------------------------------------------------------

FINDINGS = (
    ("the_harness_store_is_the_brains_only", "friction",
     "harness.Store.put refuses any address outside px.exp.brain.* / proposal.brain.*, so a consumer of "
     "the brain cannot keep its own Parts in the brain's own store class. The study subclasses it to "
     "widen the prefix check and to add an effects_root to run(), which harness.Store.run does not take "
     "at all -- so the one Calculation that reads the caller's file (oc.brain.data.load) cannot be run "
     "by the harness as it stands.",
     "for anything built ON the brain rather than IN it: the address space and the effects root are the "
     "two things a consumer needs and the harness has neither",
     "StudyStore subclasses harness.Store and overrides put and run",
     "harness.Store takes a `space` (the address prefixes it accepts) and run() takes effects_root"),
    ("no_facade_takes_the_word_auto", "friction",
     "backend='auto' is built in experiments.brain.backend.choose and the backend facade reads the plan, "
     "but the stats, data and ml facades validate args['backend'] against their own engine tuples and "
     "raise on 'auto'. The study therefore resolves the plan itself -- choose.engine_for_calc(plan, "
     "vertical, calc, engines) -- and passes the engine's NAME, which is also what puts the choice on the "
     "record. This is the same gap proposal.brain.backend.the_pass_reached_the_loops_not_the_facades "
     "named from the inside, seen now from a caller.",
     "a caller who wants the measured engine everywhere has to know the plan's shape and every facade's "
     "engine tuple; one line in each facade's _backend would make 'auto' mean 'auto' everywhere",
     "engine() in pyto/src/pyto/study.py reads the plan and names the engine",
     "every facade's _backend accepts 'auto' and calls choose.engine_for_calc with its own engine tuple"),
    ("no_calculation_returns_a_column_as_a_list", "friction",
     "every fn.brain.stats.* calculation takes args['values'] as a bare list, and nothing in the brain "
     "produces one: fn.brain.ml.column returns {for, name, values} and fn.brain.data.select returns a "
     "table. A Part is bound whole, so neither can feed a describe. fn.study.values exists only to cross "
     "that gap, once per column.",
     "it is the most common join in any study -- a column into a summary -- and it costs a Calculation "
     "the brain should own",
     "fn.study.values (four lines) between select and describe",
     "fn.brain.data.column, returning the column as a list, beside fn.brain.data.select"),
    ("a_program_that_decides_its_own_ticks", "friction",
     "a PCR's Ticks are declared before it runs, and a study decides what to run from its own first "
     "result: which columns can be profiled, which pair can be tested, which test the assumption checks "
     "allow. So `pyto study` is three observed PCRs (study_read, study_weigh, study) rather than one, and "
     "a reader has to open three records to see one study.",
     "every program that reads data it did not write has this shape; the record is the deliverable and it "
     "is split three ways for a reason that is not about the data",
     "three PCRs, each observed, each with its record, joined by the store",
     "a Tick whose invocations may be declared from an earlier Tick's result -- a PCR that can grow one "
     "Tick from a Part, with the testimony still written down before it runs"),
    ("the_plan_part_is_what_made_this_honest", "strength",
     "every refusal in this study is a row in one Part (px.exp.study.<name>.plan, and the map beside it) "
     "written BEFORE any step ran, with its `needed` and its `had`. Nothing downstream can quietly decide "
     "not to run: a step that is missing from the record is a row in the plan that says why. The same "
     "shape the brain's brackets use for criteria-before-judging turned out to be the shape for "
     "steps-before-running.",
     "'usable, then useful' needs a study that says what it would not say, and this is the mechanism "
     "rather than the intention"),
    ("the_engine_choice_rides_on_the_record", "strength",
     "because the engine is resolved from the plan Part and passed as args['backend'], every invocation "
     "in the run record carries the engine it ran on and px.exp.study.<name>.map carries where each one "
     "came from (plan or reference, and the spread it won by). A reader can see that shapiro ran on scipy "
     "and kmeans on the gram expansion without running anything.",
     "the brain's benchmark Parts stop being a document about the brain and become a thing a caller's "
     "record shows"),
)


def write_findings(store):
    for key, kind, text, for_, *rest in FINDINGS:
        value = {"for": for_, "kind": kind, "text": text}
        if rest:
            value["workaround"] = rest[0]
        if len(rest) > 1:
            value["proposal"] = rest[1]
        store.put(f"{PROPOSAL}{key}", value)


# --- the study ----------------------------------------------------------------


def study(path, target=None, out_dir="study", seed=7, fmt=None, name=None, page=True,
          quiet=False, task="auto"):
    """read the table at `path` and write the study under `out_dir`. returns the store."""
    from experiments.brain.backend import choose as chooser  # noqa: F401  (imported through brain())

    b = brain()
    source = os.path.abspath(path)
    if not os.path.isfile(source):
        raise SystemExit(f"pyto study: no file at {source}")
    fmt = fmt or ("json" if source.lower().endswith(".json") else "csv")
    label = name or os.path.splitext(os.path.basename(source))[0]
    study_name = slug(label)
    out = os.path.abspath(out_dir)
    os.makedirs(out, exist_ok=True)

    store = study_store(out)
    plan_part = store.get(b["choose"].PLAN) if store.has(b["choose"].PLAN) else None
    prefix = f"{PX}{study_name}."

    first = read_program(store, prefix, plan_part, os.path.basename(source), fmt, target, int(seed),
                         f"the table at {os.path.basename(source)}, as the study read it", task)
    first.run("study_read", effects_root=os.path.dirname(source) or ".")
    plan = store.get(prefix + "plan")
    ran, skipped = list(first.ran), list(first.skipped)

    choice = None
    if plan["hypothesis"]["run"]:
        second = weigh_program(store, prefix, plan_part, plan)
        second.run("study_weigh")
        choice = store.get(prefix + "choice")
        ran += second.ran
        skipped += second.skipped

    third, bindings, columns, model_note = study_program(store, prefix, plan_part, plan, choice,
                                                         os.path.basename(source), study_name)
    skipped = skipped + third.skipped
    steps = third.tick("say")
    third.step(steps, "summary", calcs()["summary"], prefix + "summary",
               {"name": study_name, "source": os.path.basename(source), "columns": columns,
                "skipped": skipped, "model_note": model_note,
                "addresses": dict(bindings),
                "for": "the study in sentences whose numbers name the Part they came from"},
               **bindings)
    records = [os.path.relpath(one, out) for one in store.records] + ["records/study.json"]
    declared = ran + list(third.ran) + [
        {"id": "map", "calc": "fn.study.map", "into": prefix + "map", "tick": "say"}]
    third.step(steps, "map", calcs()["map"], prefix + "map",
               {"name": study_name, "source": os.path.basename(source), "ran": declared,
                "skipped": skipped, "records": records,
                "engines": engine_table(plan_part, WANTED_ENGINES)},
               plan=prefix + "plan", summary=prefix + "summary",
               **({"best": bindings["best"]} if "best" in bindings else {}))
    third.run("study")

    for one in store.get(prefix + "map")["skipped"]:
        store.put(prefix + "skipped." + slug(one["what"]), dict(one, **{"for": "a step this study refused"}))
    write_findings(store)
    store.save("study", path=os.path.join(out, "store.json"))

    summary = store.get(prefix + "summary")
    if page:
        write_page(out, summary, list(store.records))
    if not quiet:
        print_summary(summary)
        print(f"\nwrote {os.path.join(out, 'store.json')}"
              + (f", {os.path.join(out, 'study.html')}" if page else "")
              + f", {len(store.records)} record(s) under {os.path.join(out, 'records')}")
    return store


# --- the two worked examples --------------------------------------------------

#: the studio's own shelf: one row per disc, its mold's flight numbers beside it.
#: the mold order and the twelve weights are `experiments/brain/shelf.py`'s
#: (which are `src/seed.js`'s); the pairing is the seed's disc list.
SHELF_DISCS = (
    ("buzzz-mint", "Buzzz", "ESP"), ("zone-peach", "Zone", "Z"),
    ("destroyer-lilac", "Destroyer", "Star"), ("leopard3-gold", "Leopard3", "Star"),
    ("mako3-blue", "Mako3", "Champion"), ("teebird3-sand", "TeeBird3", "Star"),
    ("buzzz-rose", "Buzzz", "ESP"), ("luna-mint", "Luna", "Rubber blend"),
    ("luna-lilac", "Luna", "Rubber blend"), ("luna-blue", "Luna", "Rubber blend"),
    ("zone-gold", "Zone", "Z"), ("zone-rose", "Zone", "Z"),
)


def write_csv(path, columns, rows):
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(columns)
        writer.writerows(rows)
    return path


def write_shelf_csv(path):
    """the disc shelf as a csv anyone can open: twelve discs, ten columns."""
    brain()
    from experiments.brain import shelf as shelf_module

    molds = {one[0]: one for one in shelf_module.MOLDS}
    rows = []
    for (disc, mold, plastic), weight in zip(SHELF_DISCS, shelf_module.WEIGHTS):
        name, maker, category, speed, glide, turn, fade = molds[mold]
        rows.append([disc, name, maker, category, plastic, weight, speed, glide, turn, fade])
    return write_csv(path, ["disc", "mold", "maker", "category", "plastic", "weight",
                            "speed", "glide", "turn", "fade"], rows)


def planted(seed=11, n=180):
    """a table with a structure that is known before the study runs: the oracle's truth.

    the clusters come from `fn.brain.ml.synthetic_blobs`, so the draw is a pure
    function of the seed. The target, the decoy and the constant column are laid
    on top HERE, outside the brain, on purpose: a study must not be checked by the
    thing it is made of.
    """
    b = brain()
    from experiments.brain.ml import core

    blobs = b["ml"].call("synthetic_blobs", {"seed": seed, "n": n, "d": 3, "k": 3,
                                             "spread": 0.9, "separation": 7.0})
    coefficients = [2.0, -1.5, 0.5]
    intercept, noise = 4.0, 0.4
    rng = core.stream(seed + 1)
    rows = []
    for row in blobs["rows"]:
        x = [float(v) for v in row[:3]]
        which = int(row[3])
        y = intercept + math.fsum(c * v for c, v in zip(coefficients, x)) + rng.normal(0.0, noise)
        rows.append([round(x[0], 6), round(x[1], 6), round(x[2], 6),
                     round(rng.normal(0.0, 1.0), 6), 1.0, f"g{which}", round(y, 6)])
    truth = {
        "for": "what was planted in this table before the study ever saw it",
        "seed": seed, "rows": n, "k": 3, "group": "arm", "target": "y",
        "coefficients": dict(zip(("x0", "x1", "x2"), coefficients)),
        "intercept": intercept, "noise": noise,
        "decoy": "decoy", "constant": "site",
        "centres": blobs["truth"]["centres"],
    }
    return ["x0", "x1", "x2", "decoy", "site", "arm", "y"], rows, truth


def write_planted_csv(path, seed=11, n=180):
    columns, rows, truth = planted(seed, n)
    write_csv(path, columns, rows)
    return truth


def planted_oracle(store, name, truth):
    """the study's own claims, checked against what was planted. an oracle for the study.

    each row is a claim the study made, what the truth says, and whether they
    agree -- the same shape `harness.oracle` writes for a Calculation, applied one
    level up, to a whole study.
    """
    prefix = f"{PX}{slug(name)}."
    checks = []

    def check(claim, expected, got, passed, reference):
        checks.append({"claim": claim, "expected": expected, "got": got,
                       "pass": bool(passed), "reference": reference})

    clusters = store.get(prefix + "clusters")
    silhouette = store.get(prefix + "silhouette.k" + clusters["chosen"])
    check("the number of clusters the silhouette supports", truth["k"], int(clusters["chosen"]),
          int(clusters["chosen"]) == truth["k"], prefix + "clusters")
    check("the clusters are real (silhouette above 0.5)", "> 0.5", silhouette["mean"],
          silhouette["mean"] > 0.5, prefix + "silhouette.k" + clusters["chosen"])

    pairs = store.get(prefix + "pairs")
    decoyed = [one for one in pairs["matters"] if truth["decoy"] in (one["a"], one["b"])]
    check("the planted noise column is not called a finding", [], decoyed, not decoyed, prefix + "pairs")
    planted_columns = sorted(truth["coefficients"])
    with_target = sorted({one["a"] if one["b"] == truth["target"] else one["b"]
                          for one in pairs["matters"] if truth["target"] in (one["a"], one["b"])})
    check("the columns the target really depends on are the ones found with it",
          "a non-empty subset of %s" % planted_columns, with_target,
          bool(with_target) and set(with_target) <= set(planted_columns), prefix + "pairs")
    against_target = {(one["a"] if one["b"] == truth["target"] else one["b"]): one["abs"]
                      for one in pairs["all"] if truth["target"] in (one["a"], one["b"])}
    weakest = min(against_target, key=lambda name: against_target[name]) if against_target else None
    check("the planted noise column is the weakest of all against the target",
          truth["decoy"], weakest, weakest == truth["decoy"], prefix + "pairs")

    plan = store.get(prefix + "plan")
    check("the constant column is refused, not described", truth["constant"], plan["constant"],
          plan["constant"] == [truth["constant"]], prefix + "plan")

    verdict = store.get(prefix + "test")
    check("the planted group difference is found", "p < 0.01", verdict["pvalue"],
          verdict["pvalue"] < 0.01, prefix + "test")

    best = store.get(prefix + "model.best")
    check("a cross-validated model of the planted linear rule", "r2 > 0.9", best["score"],
          best["score"] > 0.9, prefix + "model.best")
    check("the winner is from the linear family, because the truth is linear",
          ["linear", "ridge", "lasso"], best["chosen"],
          best["chosen"] in ("linear", "ridge", "lasso"), prefix + "model.best")
    return checks


EXAMPLES = {
    "shelf": ("shelf.csv", write_shelf_csv, "weight",
              "the studio's own disc shelf: twelve discs, their molds' flight numbers, and what they weigh"),
    "planted": ("planted.csv", write_planted_csv, "y",
                "a table with three planted clusters, a planted linear target, a decoy and a constant"),
}


# --- the command line ---------------------------------------------------------


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="python -m pyto.study",
        description="an honest study of a csv (or json rows): every step a Calculation, "
                    "every number a Part, every refusal written down.")
    parser.add_argument("file", nargs="?", help="the csv or json file to study")
    parser.add_argument("--target", default=None, help="the column to predict (a model comparison is added)")
    parser.add_argument("--out", default="study", help="where store.json, records/ and study.html go")
    parser.add_argument("--seed", type=int, default=7, help="the seed every seeded step reads (default 7)")
    parser.add_argument("--format", dest="fmt", choices=("csv", "json"), default=None)
    parser.add_argument("--name", default=None, help="the study's name in its addresses (default: the file's)")
    parser.add_argument("--example", choices=sorted(EXAMPLES), default=None,
                        help="write one of the built-in examples into --out and study that")
    parser.add_argument("--task", choices=("auto", "regression", "classification"), default="auto",
                        help="what --target is: a number to predict or a label to sort into (default auto)")
    parser.add_argument("--no-page", action="store_true", help="skip study.html")
    parser.add_argument("--quiet", action="store_true", help="write the files, print nothing")
    parsed = parser.parse_args(argv)

    target, truth = parsed.target, None
    source = parsed.file
    if parsed.example:
        out = os.path.abspath(parsed.out)
        os.makedirs(out, exist_ok=True)
        filename, write, default_target, note = EXAMPLES[parsed.example]
        source = os.path.join(out, filename)
        truth = write(source)
        target = target or default_target
        if not parsed.quiet:
            print(f"{parsed.example}: {note}\nwrote {source}\n")
    if not source:
        parser.error("name a file to study, or --example shelf")

    store = study(source, target=target, out_dir=parsed.out, seed=parsed.seed, fmt=parsed.fmt,
                  name=parsed.name, page=not parsed.no_page, quiet=parsed.quiet, task=parsed.task)
    if parsed.example == "planted" and truth:
        checks = planted_oracle(store, parsed.name or "planted", truth)
        if not parsed.quiet:
            print("\n== the oracle: what was planted, against what the study said")
            for one in checks:
                print(f"  [{'ok  ' if one['pass'] else 'FAIL'}] {one['claim']}: "
                      f"expected {one['expected']!r}, got {one['got']!r}")
        return 0 if all(one["pass"] for one in checks) else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
