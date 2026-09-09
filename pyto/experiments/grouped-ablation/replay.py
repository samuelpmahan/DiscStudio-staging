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
   comparison rows and result digests. -> evidence/replay/fresh-process.log
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
   asserted blindly), plus one row replaying against an LF-converted copy of the
   `pyto` package on PYTHONPATH (src/pyto/*.py are CRLF) to show module-source
   digest drift "by construction" while replay result digests do not drift.
   -> evidence/determinism.log

Nothing here is a library change; nothing here is executed by
`scripts/check_all.sh` other than through `test_replay.py`'s `unittest` suite.
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

EVIDENCE = os.path.join(HERE, "evidence")
RUN1 = os.path.join(EVIDENCE, "run-1")
RETAINED_PATH = os.path.join(RUN1, "retained.json")
COMPARISON_PATH = os.path.join(RUN1, "comparison.json")
REPLAY_DIR = os.path.join(EVIDENCE, "replay")
FRESH_PROCESS_LOG = os.path.join(REPLAY_DIR, "fresh-process.log")
TAMPER_DIR = os.path.join(EVIDENCE, "tamper")
TAMPER_REPORT = os.path.join(TAMPER_DIR, "report.json")
TAMPER_RECORD = os.path.join(TAMPER_DIR, "retained-tampered.json")
REGISTRY_HOLE_LOG = os.path.join(EVIDENCE, "registry-hole.log")
DETERMINISM_LOG = os.path.join(EVIDENCE, "determinism.log")

SEED, ROWS_N = 7, 400  # the committed evidence/run-1 pipeline (run.py main() defaults)

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
    """The Day 1 run, retained through lane B's retain_run (registry-keyed, no code)."""
    pxc, _pcr, run = build_day1_pxc_and_run()
    return retain.retain_run(
        pxc, run, [ROWS.address, GROUPS_PART.address], registry=REGISTRY, record_path=RETAINED_PATH
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
    import json, sys
    sys_path_before = list(sys.path)
    sys_modules_before = sorted(sys.modules)
    experiment_dir, record_path = sys.argv[1], sys.argv[2]
    sys.path.insert(0, experiment_dir)
    sys.stderr.write(
        "[replay-child] sys.path.insert(0, %r)"
        "  # intra-repo: this experiment's own modules (retain, calculations);"
        " see experiments/CAPTURE.md 'sys.path: what is logged and what is forbidden'\\n"
        % experiment_dir
    )
    import retain
    from calculations import REGISTRY
    with open(record_path, encoding="utf-8") as handle:
        record = json.load(handle)
    pxc, run = retain.replay(record, REGISTRY)
    comparison_rows = run.results["compare"]
    result_digests = {k: retain.digest_of(v) for k, v in run.results.items()}
    report = {
        "sys_path_before": sys_path_before,
        "sys_path_after": list(sys.path),
        "sys_modules_before": sys_modules_before,
        "sys_modules": sorted(sys.modules),
        "new_modules": sorted(set(sys.modules) - set(sys_modules_before)),
        "comparison_rows": comparison_rows,
        "result_digests": result_digests,
    }
    sys.stdout.write(json.dumps(report, sort_keys=True))
    """
)


def run_fresh_process_replay(record: dict) -> dict:
    """`python3 -I -c <snippet>` from a cwd outside the repo, env stripped to PATH.

    Returns the parsed child report; writes evidence/replay/fresh-process.log with
    the command line, sys.path before/after, and sorted(sys.modules) -- the proof
    that nothing beyond `pyto` + `calculations` (+ `features`, its own import) +
    `retain` was on the child's module table.
    """
    os.makedirs(REPLAY_DIR, exist_ok=True)
    workdir = tempfile.mkdtemp(prefix="replay-cwd-")  # outside the repository on purpose
    try:
        assert not os.path.abspath(workdir).startswith(os.path.normpath(os.path.join(HERE, "..", "..", ".."))), (
            "fresh-process cwd must be outside the repository"
        )
        args = [PYTHON, "-I", "-c", CHILD_REPLAY_SNIPPET, HERE, RETAINED_PATH]
        completed = subprocess.run(
            args, cwd=workdir, env=dict(STRIPPED_ENV), capture_output=True, text=True, timeout=60
        )
        lines = [
            "# Day 2 Lane D: fresh-process replay of evidence/run-1/retained.json",
            f"command: {args!r}",
            f"cwd (outside repo): {workdir}",
            f"env: {STRIPPED_ENV!r}",
            f"returncode: {completed.returncode}",
            "--- child stderr ---",
            completed.stderr.rstrip("\n"),
        ]
        if completed.returncode != 0:
            lines.append("--- child stdout ---")
            lines.append(completed.stdout)
            _write_lf(FRESH_PROCESS_LOG, "\n".join(lines) + "\n")
            raise RuntimeError(f"fresh-process replay child failed (see {FRESH_PROCESS_LOG})")
        report = json.loads(completed.stdout)
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
        with open(COMPARISON_PATH, encoding="utf-8") as handle:
            committed_rows = json.load(handle)["rows"]
        rows_equal = report["comparison_rows"] == committed_rows
        digests_equal = report["result_digests"] == record["results"]
        lines.append(f"comparison.json rows byte-identical: {rows_equal}")
        lines.append(f"result digests identical to record['results']: {digests_equal}")
        _write_lf(FRESH_PROCESS_LOG, "\n".join(lines) + "\n")
        if leaked:
            raise AssertionError(f"fresh-process replay leaked modules: {leaked}")
        if not rows_equal:
            raise AssertionError("fresh-process replay: comparison.json rows differ")
        if not digests_equal:
            raise AssertionError("fresh-process replay: result digests differ")
        return report
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


# sys.modules top-level names a clean `-I` interpreter always carries, regardless
# of stdlib internals imported lazily by import machinery itself (encodings, io,
# _frozen_importlib, ...). Anything else must trace to pyto/calculations/retain.
_ALLOWED_TOP_LEVEL_MODULES = {
    "pyto", "calculations", "features", "retain",
} | set(sys.stdlib_module_names) | {
    m.split(".")[0] for m in sys.builtin_module_names
}


# ------------------------------------------------------------------- 2. tamper


def run_tamper_check(record: dict) -> dict:
    """Edit one variant's `args.columns` in a copy; only its fit/score (and the
    downstream `compare`, which aggregates every score) may change digest."""
    os.makedirs(TAMPER_DIR, exist_ok=True)
    baseline_pxc_results = retain.replay(record, REGISTRY)[1].results
    baseline_digests = {k: retain.digest_of(v) for k, v in baseline_pxc_results.items()}

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
    _, tampered_run = retain.replay(tampered, REGISTRY)
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
    }
    _dump_lf(TAMPER_REPORT, report)
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
    install on Days 1-4, never by pointing at pyto/src) -- this is a one-off
    determinism probe, not part of scripts/check_all.sh or the editable install.
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
    lines = [
        "# Day 2 Lane D: determinism matrix (critic gap 3)",
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

    lines.append("")
    lines.append("## LF-converted pyto package on PYTHONPATH (src/pyto/*.py are CRLF)")
    lf_row = _run_lf_copy_row(RETAINED_PATH)
    provider_modules = record["provider"]["pyto"]["modules"]
    module_drift = {name: (provider_modules.get(name), lf_row["modules"].get(name)) for name in ("core.py", "pcr.py")}
    digests_match_lf = lf_row["result_digests"] == baseline_digests
    lines.append(f"converted files: {lf_row['converted_files']}")
    lines.append(f"child pyto.__file__: {lf_row['pyto_file']}  (used editable install instead of the LF copy: {lf_row['used_editable_install']})")
    for name, (before, after) in module_drift.items():
        lines.append(f"{name} source sha256: editable-install(CRLF)={before} lf-copy(LF)={after} differs_by_construction={before != after}")
    lines.append(f"replay result digests identical to run-1 despite the source-hash drift: {digests_match_lf}")
    if lf_row["used_editable_install"]:
        all_ok = False
        lines.append("  UNEXPECTED: the child imported the editable install, not the LF copy -- PYTHONPATH override failed")
    if not digests_match_lf:
        all_ok = False
        lines.append("  FAILURE: result digests drifted from an LF-only source change")
    if all(before == after for before, after in module_drift.values()):
        lines.append("  NOTE: no module-source drift observed -- either the originals are not CRLF here, or the copy did not convert anything")

    _write_lf(DETERMINISM_LOG, "\n".join(lines) + "\n")
    if not all_ok:
        raise AssertionError(f"determinism matrix found a real discrepancy; see {DETERMINISM_LOG}")
    return {"hashseed_rows": rows, "lf_row": lf_row}


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
    run_tamper_check(record)
    print("wrote", TAMPER_REPORT, TAMPER_RECORD)
    run_registry_hole_check(record)
    print("wrote", REGISTRY_HOLE_LOG)
    run_determinism_matrix(record)
    print("wrote", DETERMINISM_LOG)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
