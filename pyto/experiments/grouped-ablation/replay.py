"""Day 2, Lane D: fresh-process replay of evidence/run-1/retained.json.

Four checks, each retaining its own evidence (research/ULTRACODE-WEEK.md, Day 2
deliverable "replay.py + test_replay.py"; critic gap 9 on the sys.path insert;
critic gap 3 on the PYTHONHASHSEED/`-I` interaction):

1. Fresh-process replay: `[sys.executable, '-I', '-c', <snippet>]`, env stripped
   to PATH only, cwd outside this repository, the child receives the experiment
   directory as argv[1] and the retained record path as argv[2] and performs one
   explicit, logged `sys.path.insert` of that intra-repo directory -- allowed and
   logged per experiments/CAPTURE.md, "sys.path: what is logged and what is
   forbidden" -- then imports only `pyto`, `calculations` (which imports only
   `pyto` and `features`, calculations.py:16) and `retain`, replays, and reports
   comparison rows and result digests, and ends in one terminal `VERDICT:` line
   folding in the four refusals the PARENT makes (module sources, leaked modules,
   comparison rows, result digests) -- `child failed checks: []` is NOT the
   verdict, because two forgeries reach the child cleanly and are caught only in
   the parent (fixer round 2, findings 2 and 3).
   -> evidence/replay/fresh-process.log, and, over lane C's three retained records
   (`cross_verify_lane_c_runs`, fixer round 2, finding 13),
   evidence/replay/fresh-process-run-{2-regroup,3-reinput,4-from-retained}.log
2. Tamper: copy the retained program, edit one variant's `args.columns`, replay,
   and confirm the digest change is local to that variant's fit/score (and to
   `compare`, which aggregates every score -- documented, not hidden).
   -> evidence/tamper/
3. Registry hole: remove a calculation address from a copied registry and assert
   `retain.from_program`/`retain.replay` raise `KeyError` naming the address
   before any calculation runs (a probe substituted for a still-present address
   proves this). -> evidence/registry-hole.log
4. Determinism matrix: PYTHONHASHSEED 0..4 without `-I` (`-I` ignores
   PYTHONHASHSEED -- verified below, and the plan's own "confirmed not gaps"
   note this cuts against for n != 0 is corrected in the log rather than
   asserted blindly), plus the computed count of distinct `hash('pyto')` values
   across the five seeds, which is the only line that shows the seed took effect
   at all. No PYTHONPATH is set by any row. -> evidence/determinism.log
5. LF source-drift probe, OUTSIDE the discovered suite: replay against an
   LF-converted copy of the `pyto` package on PYTHONPATH (src/pyto/*.py are CRLF)
   to show module-source digest drift "by construction" while replay result
   digests do not drift. It is the one check that needs a PYTHONPATH pointing at
   a scratch directory, which experiments/CAPTURE.md forbids for anything
   `scripts/check_all.sh` runs, so it runs only from `python3 replay.py` and the
   tests assert on its committed log. -> evidence/lf-source-drift.log

Nothing here is a library change. Of the five, only 1-4 are executed by
`scripts/check_all.sh` (through `test_replay.py`'s `unittest` suite); check 5 is
a standalone probe whose evidence is committed.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
    print(f"[grouped-ablation] sys.path.insert(0, {HERE!r})  # this experiment's own modules (retain, calculations, features, program)", file=sys.stderr)

from pyto import Calculation, PxC  # noqa: E402

import retain  # noqa: E402
from calculations import REGISTRY, select_variants  # noqa: E402
from features import GROUPS, make_data  # noqa: E402
from program import GROUPS as GROUPS_PART, ROWS, build_program  # noqa: E402
from run import EXTERNAL_ADDRESSES, WATCHED_PATHS, commit_sha  # noqa: E402

EVIDENCE = os.path.join(HERE, "evidence")
RUN1 = os.path.join(EVIDENCE, "run-1")
RETAINED_PATH = os.path.join(RUN1, "retained.json")
COMPARISON_PATH = os.path.join(RUN1, "comparison.json")
TESTIMONY_PATH = os.path.join(RUN1, "testimony.json")
REPLAY_DIR = os.path.join(EVIDENCE, "replay")
FRESH_PROCESS_LOG = os.path.join(REPLAY_DIR, "fresh-process.log")
# Written by test_replay.py::HiddenStateAuditor: the same child, handed a record that
# deleted a step and pre-seeded its output, refusing to replay it (fixer round 1, finding 1).
FORGED_REPLAY_LOG = os.path.join(REPLAY_DIR, "forged-record-refused.log")
TAMPER_DIR = os.path.join(EVIDENCE, "tamper")
TAMPER_REPORT = os.path.join(TAMPER_DIR, "report.json")
TAMPER_RECORD = os.path.join(TAMPER_DIR, "retained-tampered.json")
REGISTRY_HOLE_LOG = os.path.join(EVIDENCE, "registry-hole.log")
DETERMINISM_LOG = os.path.join(EVIDENCE, "determinism.log")
LF_DRIFT_LOG = os.path.join(EVIDENCE, "lf-source-drift.log")

SEED, ROWS_N = 7, 400  # the committed evidence/run-1 pipeline (run.py main() defaults)

# Lane C's runs, so lane D's fresh-process gate covers every retained record and not
# only run-1 (fixer round 2, finding 13). Each row is (label, evidence dir, declared
# external addresses); run-4 replays from a retained split, so its declared inputs
# differ from run.EXTERNAL_ADDRESSES and are named here rather than assumed. The
# addresses are read back out of the committed record by cross_verify_lane_c_runs and
# checked against these, so a silent change to a run's boundary fails rather than
# redefining what the gate expects.
LANE_C_RUNS: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("run-2-regroup", os.path.join(EVIDENCE, "run-2-regroup"), EXTERNAL_ADDRESSES),
    ("run-3-reinput", os.path.join(EVIDENCE, "run-3-reinput"), EXTERNAL_ADDRESSES),
    ("run-4-from-retained", os.path.join(EVIDENCE, "run-4-from-retained"),
     ("input.ablation.groups", "scratch.ablation.split")),
)


def lane_c_log_path(label: str) -> str:
    """evidence/replay/fresh-process-<label>.log for one of LANE_C_RUNS."""
    return os.path.join(REPLAY_DIR, f"fresh-process-{label}.log")

PYTHON = sys.executable
STRIPPED_ENV = {"PATH": os.environ.get("PATH", "")}


class SkippedCheck(RuntimeError):
    """Raised (and caught by the caller) to record a named, non-silent skip."""


# --------------------------------------------------------------- day-1 record


def build_day1_pxc_and_run():
    """Reproduce evidence/run-1 exactly (seed=7, n=400; run.py:run_experiment)."""
    pxc = PxC()
    pxc.set(ROWS, make_data(SEED, ROWS_N))
    pxc.set(GROUPS_PART, GROUPS)
    pcr = build_program(select_variants({"groups": GROUPS}))
    return pxc, pcr, pcr.run(pxc)


def build_retained_record() -> dict:
    """The Day 1 run, retained through lane B's retain_run (registry-keyed, no code).

    `retained_at` is the same sha run.py stamps into commit.txt (computed with the
    evidence directory excluded, so a regenerated evidence set does not mark its own
    producing code dirty), which is what stops record["provider"] from reading as the
    library that *ran* run-1 (fixer round 1, finding 5).
    """
    pxc, _pcr, run = build_day1_pxc_and_run()
    sha = commit_sha(HERE, WATCHED_PATHS, exclude=(os.path.abspath(RUN1),))
    return retain.retain_run(
        pxc, run, [ROWS.address, GROUPS_PART.address], registry=REGISTRY,
        record_path=RETAINED_PATH, retained_at={"commit": sha},
    )


def ensure_retained_record() -> dict:
    """Write evidence/run-1/retained.json (deterministic: seed=7 is fixed) and return it.

    Day 1's run.py protects testimony.json/comparison.json/etc. from accidental
    regeneration because their commit.txt/timings.json/saved-work.json vary run to
    run; retained.json has no such run-varying field (it is `to_program` over the
    same testimony plus JSON-able externals plus a provider identity computed from
    file contents), so two independent builds are byte-identical -- asserted by
    test_replay.py rather than assumed here.
    """
    record = build_retained_record()
    retain.write_record(record, RETAINED_PATH)
    with open(RETAINED_PATH, encoding="utf-8") as handle:
        return json.load(handle)


# --------------------------------------------------------- 1. fresh-process replay

CHILD_REPLAY_SNIPPET = textwrap.dedent(
    """\
    import hashlib, json, os, sys
    sys_path_before = list(sys.path)
    sys_modules_before = sorted(sys.modules)
    experiment_dir, record_path, testimony_path, expected_externals_json = sys.argv[1:5]
    sys.path.insert(0, experiment_dir)
    sys.stderr.write(
        "[replay-child] sys.path.insert(0, %r)"
        "  # intra-repo: this experiment's own modules (retain, calculations);"
        " see experiments/CAPTURE.md 'sys.path: what is logged and what is forbidden'\\n"
        % experiment_dir
    )
    sys.stderr.write("[replay-child] sys.dont_write_bytecode=%r (python3 -B: no __pycache__ is read"
                     " or written, so a stale .pyc cannot serve this replay)\\n" % sys.dont_write_bytecode)
    import retain
    from calculations import REGISTRY
    with open(record_path, encoding="utf-8") as handle:
        record = json.load(handle)
    with open(testimony_path, encoding="utf-8") as handle:
        testimony = json.load(handle)

    # What this record is supposed to be, checked before it is trusted.
    program_matches_committed_testimony = (
        json.dumps(record["program"]["ticks"], sort_keys=True)
        == json.dumps(testimony["ticks"], sort_keys=True)
    )
    expected_externals = sorted(json.loads(expected_externals_json))
    record_externals = sorted(record.get("external") or {})
    externals_match_declared_inputs = record_externals == expected_externals
    provider = retain.verify_provider(record, REGISTRY)
    source_sha256 = {}
    for name in ("retain.py", "calculations.py", "features.py"):
        with open(os.path.join(experiment_dir, name), "rb") as handle:
            source_sha256[name] = hashlib.sha256(handle.read()).hexdigest()
    claimed_provider_sha = sorted({
        entry.get("source_sha256")
        for entry in (record.get("provider", {}).get("registry") or {}).values()
    })
    calculations_source_matches_record = claimed_provider_sha == [source_sha256["calculations.py"]]

    pxc, run = retain.replay(record, REGISTRY)
    comparison_rows = run.results["compare"]
    result_digests = {k: retain.digest_of(v) for k, v in run.results.items()}
    report = {
        "dont_write_bytecode": sys.dont_write_bytecode,
        "sys_path_before": sys_path_before,
        "sys_path_after": list(sys.path),
        "sys_modules_before": sys_modules_before,
        "sys_modules": sorted(sys.modules),
        "new_modules": sorted(set(sys.modules) - set(sys_modules_before)),
        "program_matches_committed_testimony": program_matches_committed_testimony,
        "expected_externals": expected_externals,
        "record_externals": record_externals,
        "externals_match_declared_inputs": externals_match_declared_inputs,
        "provider_agrees": provider["agrees"],
        "provider_disagreeing_addresses": provider["disagreeing_addresses"],
        "provider_pyto_agrees": provider["pyto"]["agrees"],
        "source_sha256": source_sha256,
        "claimed_provider_source_sha256": claimed_provider_sha,
        "calculations_source_matches_record": calculations_source_matches_record,
        "comparison_rows": comparison_rows,
        "result_digests": result_digests,
    }
    failed = [
        name for name in (
            "program_matches_committed_testimony",
            "externals_match_declared_inputs",
            "provider_agrees",
            "calculations_source_matches_record",
        )
        if not report[name]
    ]
    report["failed_checks"] = failed
    sys.stdout.write(json.dumps(report, sort_keys=True))
    sys.exit(3 if failed else 0)
    """
)


def purge_experiment_bytecode() -> list[str]:
    """Delete every __pycache__ this (parent) process wrote under the experiment directory.

    `python3 -B` already stops the child from reading or writing bytecode, but the
    parent's own `__pycache__` is what made the leak possible in the first place
    (fixer round 1, finding 6: a .pyc whose timestamp+size still match a tampered
    source is served instead of the source). Removing it is the belt to -B's braces
    and is reported into the log so the reader can see it happened.
    """
    removed = []
    for root, dirs, _files in os.walk(HERE):
        for name in list(dirs):
            if name == "__pycache__":
                path = os.path.join(root, name)
                shutil.rmtree(path, ignore_errors=True)
                removed.append(os.path.relpath(path, HERE))
                dirs.remove(name)
    return sorted(removed)


def run_fresh_process_replay(
    record: dict,
    record_path: str | None = None,
    log_path: str | None = None,
    comparison_path: str | None = None,
    testimony_path: str | None = None,
    expected_externals: tuple[str, ...] | None = None,
) -> dict:
    """`python3 -I -B -c <snippet>` from a cwd outside the repo, env stripped to PATH.

    Returns the parsed child report; writes a log (default
    evidence/replay/fresh-process.log) with the command line, sys.path before/after,
    sorted(sys.modules) -- the proof that nothing beyond `pyto` + `calculations`
    (+ `features`, its own import) + `retain` was on the child's module table -- the
    four checks the child makes before it trusts the record (fixer round 1, findings
    1, 3 and 6), and a terminal `VERDICT:` line.

    The child's four checks are:

    * the record's program ticks are the committed testimony.json ticks for the run
      being replayed, so a record that deleted a step cannot pass as that run's;
    * the record's external addresses are exactly the run's declared inputs, so an
      address the program is supposed to compute cannot be pre-seeded;
    * retain.verify_provider agrees on the pyto modules and on every per-address
      provider source hash;
    * the child's own sha256 of calculations.py equals the one the record claims,
      which is what -B plus the __pycache__ purge make meaningful.

    Four more refusals are the PARENT's, and `child failed checks: []` does not
    imply them (fixer round 2, findings 2 and 4): the child read the same module
    sources the parent sees on disk, no module leaked past
    `_ALLOWED_TOP_LEVEL_MODULES`, the child's comparison rows are byte-identical to
    the committed comparison.json, and its recomputed result digests equal
    `record["results"]`. Two forgeries reach the child cleanly and are caught only
    here -- a value-forged record with recomputed digests (rows differ) and a
    registry-forged record whose provider block is byte-identical to the honest one
    because `retain.provider_identity` is module-granular (digests differ). So the
    VERDICT line, not `child failed checks`, is this function's answer: it is
    `VERDICT: accepted` only when all eight hold, and otherwise
    `VERDICT: refused (<reasons>)` naming each one that did not.

    `record_path`/`comparison_path`/`testimony_path`/`expected_externals` default to
    evidence/run-1's; passing another run's makes this the cross-verification gate
    over run-2/3/4 as well (fixer round 2, finding 13).
    """
    os.makedirs(REPLAY_DIR, exist_ok=True)
    record_path = RETAINED_PATH if record_path is None else record_path
    log_path = FRESH_PROCESS_LOG if log_path is None else log_path
    comparison_path = COMPARISON_PATH if comparison_path is None else comparison_path
    testimony_path = TESTIMONY_PATH if testimony_path is None else testimony_path
    expected_externals = EXTERNAL_ADDRESSES if expected_externals is None else expected_externals
    purged = purge_experiment_bytecode()
    workdir = tempfile.mkdtemp(prefix="replay-cwd-")  # outside the repository on purpose
    try:
        assert not os.path.abspath(workdir).startswith(os.path.normpath(os.path.join(HERE, "..", "..", ".."))), (
            "fresh-process cwd must be outside the repository"
        )
        expected_externals_json = json.dumps(sorted(expected_externals))
        args = [
            PYTHON, "-I", "-B", "-c", CHILD_REPLAY_SNIPPET,
            HERE, record_path, testimony_path, expected_externals_json,
        ]
        completed = subprocess.run(
            args, cwd=workdir, env=dict(STRIPPED_ENV), capture_output=True, text=True, timeout=60
        )
        lines = [
            "# Day 2 Lane D: fresh-process replay",
            f"record: {record_path}",
            f"committed comparison: {comparison_path}",
            f"committed testimony: {testimony_path}",
            f"command: {args!r}",
            f"cwd (outside repo): {workdir}",
            f"env: {STRIPPED_ENV!r}",
            f"__pycache__ directories purged under the experiment before the spawn: {purged!r}",
            f"returncode: {completed.returncode}",
            "--- child stderr ---",
            completed.stderr.rstrip("\n"),
        ]
        try:
            report = json.loads(completed.stdout)
        except ValueError:
            lines.append("--- child stdout (not JSON) ---")
            lines.append(completed.stdout)
            lines.append("VERDICT: refused (child produced no JSON report)")
            _write_lf(log_path, "\n".join(lines) + "\n")
            raise RuntimeError(f"fresh-process replay child failed (see {log_path})")
        lines.append(f"child sys.dont_write_bytecode (python3 -B): {report['dont_write_bytecode']}")
        lines.append(f"sys.path before: {report['sys_path_before']!r}")
        lines.append(f"sys.path after:  {report['sys_path_after']!r}")
        lines.append(f"sys.modules before this script's own imports ({len(report['sys_modules_before'])}): {report['sys_modules_before']!r}")
        lines.append(f"sys.modules after replay ({len(report['sys_modules'])}): {report['sys_modules']!r}")
        lines.append(f"new modules introduced by this script's own imports: {report['new_modules']!r}")
        leaked = sorted(
            name.split(".")[0]
            for name in report["new_modules"]
            if name.split(".")[0] not in _ALLOWED_TOP_LEVEL_MODULES
        )
        lines.append(f"new modules outside {{pyto, calculations, features, retain}}: {leaked!r}")
        lines.append(
            f"record program ticks identical to the committed {os.path.basename(os.path.dirname(testimony_path))}"
            f"/testimony.json ticks: {report['program_matches_committed_testimony']}"
        )
        lines.append(
            f"record external addresses {report['record_externals']!r} equal the declared inputs "
            f"{report['expected_externals']!r}: {report['externals_match_declared_inputs']}"
        )
        lines.append(
            f"provider identity accepted (retain.verify_provider): {report['provider_agrees']}"
            f"  pyto modules agree: {report['provider_pyto_agrees']}"
            f"  disagreeing addresses: {report['provider_disagreeing_addresses']!r}"
        )
        parent_source_sha256 = _source_sha256(("retain.py", "calculations.py", "features.py"))
        for name in sorted(parent_source_sha256):
            child_sha = report["source_sha256"].get(name)
            lines.append(
                f"{name} sha256: parent(on disk)={parent_source_sha256[name]} child(read at replay)={child_sha} "
                f"agree={parent_source_sha256[name] == child_sha}"
            )
        lines.append(
            f"calculations.py sha256 the record claims {report['claimed_provider_source_sha256']!r} equals the "
            f"one the child computed: {report['calculations_source_matches_record']}"
        )
        with open(comparison_path, encoding="utf-8") as handle:
            committed_rows = json.load(handle)["rows"]
        rows_equal = report["comparison_rows"] == committed_rows
        digests_equal = report["result_digests"] == record["results"]
        sources_equal = parent_source_sha256 == report["source_sha256"]
        lines.append(f"comparison.json rows byte-identical: {rows_equal}")
        lines.append(f"result digests identical to record['results']: {digests_equal}")
        lines.append(f"child failed checks: {report['failed_checks']!r}")

        # The verdict folds the child's own checks together with the four the parent
        # makes, so no refused record can produce an accepted-looking log
        # (fixer round 2, finding 3).
        reasons = []
        if report["failed_checks"]:
            reasons.append(f"child failed checks {report['failed_checks']!r}")
        if completed.returncode != 0:
            reasons.append(f"child returncode {completed.returncode}")
        if not sources_equal:
            reasons.append("child read different module sources than the parent")
        if leaked:
            reasons.append(f"modules leaked beyond the allowed set: {leaked!r}")
        if not rows_equal:
            reasons.append("comparison rows differ from the committed comparison.json")
        if not digests_equal:
            reasons.append("result digests differ from record['results']")
        verdict = "VERDICT: accepted" if not reasons else f"VERDICT: refused ({'; '.join(reasons)})"
        lines.append(verdict)
        _write_lf(log_path, "\n".join(lines) + "\n")
        if reasons:
            raise AssertionError(
                f"fresh-process replay refused {record_path}: {'; '.join(reasons)} (see {log_path})"
            )
        return report
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


def cross_verify_lane_c_runs() -> dict[str, dict]:
    """Run the fresh-process gate over every lane-C retained record, not just run-1.

    The Day 2 plan's cross-verification gate is "lane (c)'s outputs must be
    reproduced by lane (b)'s fresh-process replay carrying lane (a)'s digests". Run-1
    had retained evidence and a test; run-2/3/4 did not, so nothing in the repository
    replayed them and nothing would have caught future drift (fixer round 2, finding
    13). Each run is replayed against its OWN committed comparison.json,
    testimony.json and retained.json["results"], and each leaves
    evidence/replay/fresh-process-<label>.log ending in its VERDICT line.

    Returns {label: child report}. Raises AssertionError (through
    run_fresh_process_replay) on the first refusal, leaving that run's log behind.
    """
    reports: dict[str, dict] = {}
    for label, directory, externals in LANE_C_RUNS:
        record_path = os.path.join(directory, "retained.json")
        with open(record_path, encoding="utf-8") as handle:
            record = json.load(handle)
        declared = tuple(sorted(record.get("external") or {}))
        if declared != tuple(sorted(externals)):
            raise AssertionError(
                f"{label}: retained externals {declared} are not the declared inputs "
                f"{tuple(sorted(externals))} LANE_C_RUNS names"
            )
        reports[label] = run_fresh_process_replay(
            record,
            record_path=record_path,
            log_path=lane_c_log_path(label),
            comparison_path=os.path.join(directory, "comparison.json"),
            testimony_path=os.path.join(directory, "testimony.json"),
            expected_externals=externals,
        )
    return reports


def _source_sha256(names: tuple[str, ...]) -> dict[str, str]:
    """sha256 of the named files in this experiment directory, read from disk now."""
    out = {}
    for name in names:
        with open(os.path.join(HERE, name), "rb") as handle:
            out[name] = hashlib.sha256(handle.read()).hexdigest()
    return out


# sys.modules top-level names a clean `-I` interpreter always carries, regardless
# of stdlib internals imported lazily by import machinery itself (encodings, io,
# _frozen_importlib, ...). Anything else must trace to pyto/calculations/retain.
_ALLOWED_TOP_LEVEL_MODULES = {
    "pyto", "calculations", "features", "retain",
} | set(sys.stdlib_module_names) | {
    m.split(".")[0] for m in sys.builtin_module_names
}


# ------------------------------------------------------------------- 2. tamper


def run_tamper_check(record: dict, replay_fn=None) -> dict:
    """Edit one variant's `args.columns` in a copy; only its fit/score (and the
    downstream `compare`, which aggregates every score) may change digest.

    Both sides replay from a deep copy of the caller's record, so a mutation on one
    side cannot contaminate the other (fixer round 1, finding 2).
    `record_unchanged_by_baseline_replay` compares the bytes of **the copy that was
    actually handed to the baseline replay**, before and after that replay. It used
    to compare the caller's `record` -- an object the baseline replay was never
    given -- which made it `json.dumps(record) == json.dumps(record)` by
    construction: it could not be False, and a Calculation rewriting the program in
    place still produced a clean-looking report (fixer round 2, finding 4). Measured
    on the handed object it is a real check of what the baseline replay did, and
    `replay_fn` (default `retain.replay`) exists so a test can supply a replay that
    does mutate and watch the flag go False.
    """
    os.makedirs(TAMPER_DIR, exist_ok=True)
    replay_fn = retain.replay if replay_fn is None else replay_fn
    handed_to_baseline = copy.deepcopy(record)
    handed_bytes_before = json.dumps(handed_to_baseline, sort_keys=True)
    baseline_pxc_results = replay_fn(handed_to_baseline, REGISTRY)[1].results
    baseline_digests = {k: retain.digest_of(v) for k, v in baseline_pxc_results.items()}
    record_unchanged_by_baseline_replay = (
        json.dumps(handed_to_baseline, sort_keys=True) == handed_bytes_before
    )

    tampered = copy.deepcopy(record)
    target_id = "fit.drop_g0"
    entry = next(
        e
        for tick in tampered["program"]["ticks"]
        for e in tick["calculations"]
        if e["id"] == target_id
    )
    original_columns = list(entry["args"]["columns"])
    # A materially different column set (the baseline "all" variant's full column
    # list), not a no-op edit, so a digest that failed to move would be a real bug.
    all_entry = next(
        e
        for tick in record["program"]["ticks"]
        for e in tick["calculations"]
        if e["id"] == "fit.all"
    )
    entry["args"]["columns"] = list(all_entry["args"]["columns"])
    assert entry["args"]["columns"] != original_columns, "tamper edit must be a real change"

    retain.write_record(tampered, TAMPER_RECORD)
    _, tampered_run = replay_fn(tampered, REGISTRY)
    tampered_digests = {k: retain.digest_of(v) for k, v in tampered_run.results.items()}

    expected_to_change = {target_id, "score.drop_g0", "compare"}
    changed = sorted(k for k in baseline_digests if baseline_digests[k] != tampered_digests.get(k))
    unexpected = sorted(set(changed) - expected_to_change)
    missing = sorted(expected_to_change - set(changed))

    report = {
        "tampered_invocation": target_id,
        "original_columns": original_columns,
        "tampered_columns": entry["args"]["columns"],
        "expected_to_change": sorted(expected_to_change),
        "changed": changed,
        "note": (
            "'compare' is expected to change: it aggregates every variant's score "
            "(program.py build_program, id='compare', **scores), so tampering one "
            "variant's input necessarily changes the comparison table too. Only "
            "fit.drop_g0 and score.drop_g0 are the tampered locus; every other "
            "fit/score id must be untouched."
        ),
        "baseline_digests": baseline_digests,
        "tampered_digests": tampered_digests,
        "unexpected_changes": unexpected,
        "missing_expected_changes": missing,
        "record_unchanged_by_baseline_replay": record_unchanged_by_baseline_replay,
    }
    _dump_lf(TAMPER_REPORT, report)
    if not record_unchanged_by_baseline_replay:
        raise AssertionError(
            "tamper test: the baseline replay mutated the record it was handed, so the report's "
            "two sides are not independent (fixer round 1, finding 2; fixer round 2, finding 4 "
            "made this flag able to be False)"
        )
    if unexpected:
        raise AssertionError(f"tamper test: unexpected digest changes at {unexpected}")
    if missing:
        raise AssertionError(f"tamper test: expected digest changes missing at {missing}")
    return report


# ------------------------------------------------------------- 3. registry hole

PROBE_CALLS: list[dict] = []


def _probe(args: dict) -> dict:
    PROBE_CALLS.append(dict(args))
    return {"seen": sorted(args)}


def run_registry_hole_check(record: dict) -> str:
    """Remove a real address from a copied registry; assert loud failure naming it
    before any calculation runs.

    The Day 2 brief names 'fn.ablation.rmse'; no such address exists in this
    registry (calculations.py:121-125 lists selectVariants/split/fit/score/
    compare). 'fn.ablation.score' is used instead, following lane B's own
    precedent (test_retain.py::FromProgram::
    test_missing_registry_address_raises_keyerror_before_any_execution).
    """
    PROBE_CALLS.clear()
    holed = dict(REGISTRY)
    del holed["fn.ablation.score"]
    holed["fn.ablation.split"] = Calculation("fn.ablation.split", _probe)  # would run first if execution proceeded

    lines = [
        "# Day 2 Lane D: registry-hole check",
        "requested address (Day 2 brief text, not present in REGISTRY): 'fn.ablation.rmse'",
        f"REGISTRY addresses: {sorted(REGISTRY)}",
        "substituted address (lane B precedent, test_retain.py FromProgram."
        "test_missing_registry_address_raises_keyerror_before_any_execution): 'fn.ablation.score'",
    ]
    try:
        retain.replay(record, holed)
    except KeyError as error:
        lines.append(f"KeyError raised: {error}")
        lines.append(f"names the missing address: {'fn.ablation.score' in str(error)}")
        lines.append(f"probe calculation (a still-present address) was never called: {PROBE_CALLS == []}")
        _write_lf(REGISTRY_HOLE_LOG, "\n".join(lines) + "\n")
        if "fn.ablation.score" not in str(error):
            raise AssertionError("KeyError did not name the missing address") from error
        if PROBE_CALLS:
            raise AssertionError("a calculation ran before the registry hole was detected") from None
        return str(error)
    else:
        lines.append("NO EXCEPTION RAISED -- this is a failure, not a skip")
        _write_lf(REGISTRY_HOLE_LOG, "\n".join(lines) + "\n")
        raise AssertionError("retain.replay did not raise on a registry hole")


# --------------------------------------------------------- 4. determinism matrix

CHILD_HASHSEED_SNIPPET = textwrap.dedent(
    """\
    import json, sys
    experiment_dir, record_path = sys.argv[1], sys.argv[2]
    sys.path.insert(0, experiment_dir)
    sys.stderr.write("[determinism-child] sys.path.insert(0, %r)\\n" % experiment_dir)
    import retain
    from calculations import REGISTRY
    with open(record_path, encoding="utf-8") as handle:
        record = json.load(handle)
    _pxc, run = retain.replay(record, REGISTRY)
    result_digests = {k: retain.digest_of(v) for k, v in run.results.items()}
    report = {
        "hash_randomization": sys.flags.hash_randomization,
        "hash_pyto": hash("pyto"),
        "result_digests": result_digests,
    }
    sys.stdout.write(json.dumps(report, sort_keys=True))
    """
)

CHILD_LF_SNIPPET = textwrap.dedent(
    """\
    import hashlib, json, sys
    experiment_dir, record_path = sys.argv[1], sys.argv[2]
    sys.path.insert(0, experiment_dir)
    sys.stderr.write("[determinism-lf-child] sys.path.insert(0, %r)\\n" % experiment_dir)
    import pyto
    import retain
    from calculations import REGISTRY
    with open(record_path, encoding="utf-8") as handle:
        record = json.load(handle)
    _pxc, run = retain.replay(record, REGISTRY)
    result_digests = {k: retain.digest_of(v) for k, v in run.results.items()}
    lib_dir = __import__("os").path.dirname(__import__("os").path.abspath(pyto.core.__file__))
    modules = {}
    for name in ("core.py", "pcr.py"):
        with open(__import__("os").path.join(lib_dir, name), "rb") as fh:
            modules[name] = hashlib.sha256(fh.read()).hexdigest()
    report = {
        "pyto_file": pyto.__file__,
        "modules": modules,
        "result_digests": result_digests,
    }
    sys.stdout.write(json.dumps(report, sort_keys=True))
    """
)


def _run_hashseed_row(seed: int, record_path: str) -> dict:
    env = {"PATH": os.environ.get("PATH", ""), "PYTHONHASHSEED": str(seed)}
    args = [PYTHON, "-s", "-P", "-c", CHILD_HASHSEED_SNIPPET, HERE, record_path]
    completed = subprocess.run(args, env=env, capture_output=True, text=True, timeout=60)
    if completed.returncode != 0:
        raise RuntimeError(f"hashseed row {seed} failed: {completed.stderr}")
    report = json.loads(completed.stdout)
    report["seed"] = seed
    report["stderr"] = completed.stderr.rstrip("\n")
    return report


def _lf_copy_of_pyto_package(dest_root: str) -> str:
    """Copy the `pyto` package into dest_root/pyto, converting CRLF -> LF.

    dest_root itself carries no directory literally named 'src' (CAPTURE.md forbids
    a PYTHONPATH containing 'src'; the library is reached through the editable
    install on Days 1-4, never by pointing at pyto/src).

    This row sets PYTHONPATH to a scratch directory, which experiments/CAPTURE.md
    ("sys.path: what is logged and what is forbidden") forbids for any import that
    scripts/check_all.sh performs. It is therefore NOT part of any test_*.py: it runs
    only from `python3 experiments/grouped-ablation/replay.py`, and its committed
    output is evidence/lf-source-drift.log (fixer round 1, finding 4). The PYTHONPATH
    value is printed into that log and to stderr so it is visible rather than implied.
    """
    src_pkg_dir = os.path.dirname(os.path.abspath(__import__("pyto").__file__))
    dest_pkg_dir = os.path.join(dest_root, "pyto")
    shutil.copytree(src_pkg_dir, dest_pkg_dir, ignore=shutil.ignore_patterns("__pycache__"))
    converted = []
    for name in os.listdir(dest_pkg_dir):
        if not name.endswith(".py"):
            continue
        path = os.path.join(dest_pkg_dir, name)
        with open(path, "rb") as handle:
            data = handle.read()
        if b"\r\n" in data:
            with open(path, "wb") as handle:
                handle.write(data.replace(b"\r\n", b"\n"))
            converted.append(name)
    return dest_pkg_dir, converted


def _run_lf_copy_row(record_path: str) -> dict:
    tmp = tempfile.mkdtemp(prefix="determinism-lf-")
    try:
        dest_pkg_dir, converted = _lf_copy_of_pyto_package(tmp)
        env = {"PATH": os.environ.get("PATH", ""), "PYTHONPATH": tmp}
        print(
            f"[grouped-ablation] PYTHONPATH={tmp} for the LF-source-drift probe only "
            f"(standalone `python3 replay.py`; not run by scripts/check_all.sh -- "
            f"experiments/CAPTURE.md forbids a scratch PYTHONPATH inside the suites)",
            file=sys.stderr,
        )
        args = [PYTHON, "-c", CHILD_LF_SNIPPET, HERE, record_path]
        completed = subprocess.run(args, env=env, capture_output=True, text=True, timeout=60)
        if completed.returncode != 0:
            raise RuntimeError(f"LF-copy row failed: {completed.stderr}")
        report = json.loads(completed.stdout)
        report["converted_files"] = sorted(converted)
        report["pythonpath"] = tmp
        report["stderr"] = completed.stderr.rstrip("\n")
        report["used_editable_install"] = not report["pyto_file"].startswith(dest_pkg_dir)
        return report
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def run_determinism_matrix(record: dict) -> dict:
    """PYTHONHASHSEED 0..4, twice each, in real child processes. No PYTHONPATH.

    The LF-converted-package row lives in `run_lf_source_drift_probe` instead: it is
    the one check that needs a scratch PYTHONPATH, which experiments/CAPTURE.md
    forbids inside anything scripts/check_all.sh runs (fixer round 1, finding 4).
    """
    lines = [
        "# Day 2 Lane D: determinism matrix (critic gap 3)",
        "",
        "No PYTHONPATH is set by any row below; each child is spawned with env",
        "{PATH, PYTHONHASHSEED} only. The LF-converted-package row that needs a",
        "scratch PYTHONPATH was moved out of the discovered test suite and into",
        "`python3 experiments/grouped-ablation/replay.py` -> evidence/lf-source-drift.log",
        "(experiments/CAPTURE.md, 'sys.path: what is logged and what is forbidden').",
        "",
        "## PYTHONHASHSEED rows (no -I: -I implies -E, which ignores PYTHONHASHSEED)",
        "verified in this sandbox (Python " + sys.version.split()[0] + "):",
        "sys.flags.hash_randomization is 0 ONLY for PYTHONHASHSEED=0; for n=1..4 it",
        "reports 1 (CPython treats an explicit nonzero seed as 'randomization enabled,",
        "with a fixed seed', not as disabled) while hash('pyto') is still reproducible",
        "for a given seed across independent processes (checked below by running each",
        "seed twice). This corrects research/ULTRACODE-WEEK.md's 'confirmed not gaps'",
        "note ('without -E the seed takes effect (hash_randomization=0)'), which held",
        "only for n=0 when re-verified here; the assertion this evidence backs is",
        "digest/hash reproducibility per seed, not the flag's value for n != 0.",
        "",
    ]
    rows = []
    baseline_digests = record["results"]
    all_ok = True
    for seed in range(5):
        first = _run_hashseed_row(seed, RETAINED_PATH)
        second = _run_hashseed_row(seed, RETAINED_PATH)
        reproducible = first["hash_pyto"] == second["hash_pyto"]
        digests_match = first["result_digests"] == baseline_digests and second["result_digests"] == baseline_digests
        rows.append({"seed": seed, "first": first, "second": second, "reproducible_hash": reproducible, "digests_match_baseline": digests_match})
        lines.append(
            f"seed={seed}: hash_randomization={first['hash_randomization']} "
            f"hash('pyto') first={first['hash_pyto']} second={second['hash_pyto']} "
            f"reproducible={reproducible} digests_match_baseline={digests_match}"
        )
        if seed == 0 and first["hash_randomization"] != 0:
            all_ok = False
            lines.append(f"  UNEXPECTED: seed=0 should report hash_randomization=0")
        if not reproducible or not digests_match:
            all_ok = False

    # The matrix's central claim is that the seed took effect at all. Within-seed
    # equality cannot show that: on a build where PYTHONHASHSEED were ignored, all
    # five rows would collapse to one hash value and every row above would still
    # read reproducible=True (fixer round 1, finding 7). Computed, never a literal.
    distinct_hashes = len({row["first"]["hash_pyto"] for row in rows})
    lines.append("")
    lines.append(
        f"distinct hash('pyto') across the {len(rows)} seeds: {distinct_hashes} "
        f"(equal to the number of seeds: {distinct_hashes == len(rows)} -- if this ever "
        f"reads 1, PYTHONHASHSEED stopped taking effect and every per-seed row above "
        f"would still pass)"
    )
    if distinct_hashes != len(rows):
        all_ok = False
        lines.append("  FAILURE: the seeds did not produce distinct hashes; the matrix proves nothing")

    _write_lf(DETERMINISM_LOG, "\n".join(lines) + "\n")
    if not all_ok:
        raise AssertionError(f"determinism matrix found a real discrepancy; see {DETERMINISM_LOG}")
    return {"hashseed_rows": rows, "distinct_hashes": distinct_hashes}


def run_lf_source_drift_probe(record: dict) -> dict:
    """Standalone probe: replay against an LF-converted copy of `pyto` on PYTHONPATH.

    Not called by any test_*.py and therefore not by scripts/check_all.sh: it is the
    one row that needs a PYTHONPATH pointing at a scratch directory, which
    experiments/CAPTURE.md forbids for the suites (fixer round 1, finding 4). Run it
    with `python3 experiments/grouped-ablation/replay.py`; its committed output,
    evidence/lf-source-drift.log, is what the tests read.

    `record_results_sha256` pins the log to the record it was produced against, so a
    stale log is a failing test rather than an unnoticed drift.
    """
    lf_row = _run_lf_copy_row(RETAINED_PATH)
    baseline_digests = record["results"]
    provider_modules = record["provider"]["pyto"]["modules"]
    module_drift = {name: (provider_modules.get(name), lf_row["modules"].get(name)) for name in ("core.py", "pcr.py")}
    digests_match_lf = lf_row["result_digests"] == baseline_digests
    results_sha = hashlib.sha256(
        json.dumps(baseline_digests, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    lines = [
        "# Day 2 Lane D: LF-converted pyto package on PYTHONPATH (src/pyto/*.py are CRLF)",
        "",
        "Produced by `python3 experiments/grouped-ablation/replay.py` ONLY. This probe",
        "sets PYTHONPATH to a scratch directory to import a modified copy of the library,",
        "which experiments/CAPTURE.md forbids for anything scripts/check_all.sh runs; it",
        "is therefore outside the discovered test suite, and the tests assert on this",
        "committed log instead of re-running it (fixer round 1, finding 4).",
        "",
        f"PYTHONPATH (scratch, removed after the run): {lf_row['pythonpath']}",
        f"command: {[PYTHON, '-c', '<CHILD_LF_SNIPPET>', HERE, RETAINED_PATH]!r}",
        f"record_results_sha256 (the retained.json this log was produced against): {results_sha}",
        f"converted files: {lf_row['converted_files']}",
        f"child pyto.__file__: {lf_row['pyto_file']}  (used editable install instead of the LF copy: {lf_row['used_editable_install']})",
    ]
    for name, (before, after) in module_drift.items():
        lines.append(f"{name} source sha256: editable-install(CRLF)={before} lf-copy(LF)={after} differs_by_construction={before != after}")
    lines.append(f"replay result digests identical to run-1 despite the source-hash drift: {digests_match_lf}")
    ok = True
    if lf_row["used_editable_install"]:
        ok = False
        lines.append("  UNEXPECTED: the child imported the editable install, not the LF copy -- PYTHONPATH override failed")
    if not digests_match_lf:
        ok = False
        lines.append("  FAILURE: result digests drifted from an LF-only source change")
    if all(before == after for before, after in module_drift.values()):
        ok = False
        lines.append("  UNEXPECTED: no module-source drift observed -- either the originals are not CRLF here, or the copy did not convert anything")
    lines.append("")
    lines.append(
        "This row is the reason retain.replay does NOT compare provider identity: it "
        "replays under a deliberately different library copy and must not be refused. "
        "retain.verify_provider makes the comparison available to callers that do need "
        "to reject (replay.run_fresh_process_replay asserts on it)."
    )
    _write_lf(LF_DRIFT_LOG, "\n".join(lines) + "\n")
    if not ok:
        raise AssertionError(f"LF source-drift probe found a real discrepancy; see {LF_DRIFT_LOG}")
    return {"lf_row": lf_row, "record_results_sha256": results_sha, "module_drift": module_drift}


# ------------------------------------------------------------------------ util


def _write_lf(path: str, text: str) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def _dump_lf(path: str, obj) -> None:
    _write_lf(path, json.dumps(obj, indent=2, sort_keys=True) + "\n")


def main() -> int:
    record = ensure_retained_record()
    print("wrote", RETAINED_PATH)
    run_fresh_process_replay(record)
    print("wrote", FRESH_PROCESS_LOG)
    cross_verify_lane_c_runs()
    print("wrote", *[lane_c_log_path(label) for label, _dir, _ext in LANE_C_RUNS])
    run_tamper_check(record)
    print("wrote", TAMPER_REPORT, TAMPER_RECORD)
    run_registry_hole_check(record)
    print("wrote", REGISTRY_HOLE_LOG)
    run_determinism_matrix(record)
    print("wrote", DETERMINISM_LOG)
    run_lf_source_drift_probe(record)
    print("wrote", LF_DRIFT_LOG)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
