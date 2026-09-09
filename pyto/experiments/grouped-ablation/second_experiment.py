"""Shared machinery for Day 2's second experiments.

run_regrouped.py, run_reinput.py and run_from_retained.py apply Day 1's
comparison procedure to a cross-cutting grouping, a second input, and a program
that reuses run-1's retained split. Nothing here edits program.py or
calculations.py: build_program, family and REGISTRY are imported unchanged
everywhere in this file (research/ULTRACODE-WEEK.md, Day 2 kill criterion --
"if the regrouped or re-input run requires editing program.py or
calculations.py ... stop and record 'reconstruction required'").

This module holds the parts of run.py's Day 1 evidence writer that assumed
features.GROUPS (planted-weight lookup keyed by group name), generalised to
work for any {name: [columns]} grouping, plus the Day 2 additions: retained.json
(already written by run.write_evidence for run-1; here for runs 2-4),
receipts.json, a reuse-focused saved-work.json and interpretation.md.
"""

from __future__ import annotations

import json
import os
import subprocess
from typing import Any, Mapping

HERE = os.path.dirname(os.path.abspath(__file__))
import sys  # noqa: E402

if HERE not in sys.path:
    sys.path.insert(0, HERE)

import compare_local  # noqa: E402
import retain  # noqa: E402
from features import FEATURES, TRUE_W, _total  # noqa: E402
from program import BASELINE_KEY  # noqa: E402
from run import (  # noqa: E402
    UNINFORMATIVE_DELTA,
    WATCHED_PATHS,
    _dump,
    _text,
    commit_sha,
    evidence_excludes,
    jsonable,
    receipts_payload,
    ranking,
)

EVIDENCE = os.path.join(HERE, "evidence")
RUN_1 = os.path.join(EVIDENCE, "run-1")

# The base the "no program edits" diff is taken against: the last commit that touched the
# program (program.py or calculations.py), never HEAD. On Day 2 this was the day's base
# (d9dded6; fixer round 1, finding 11: a checkpoint committing a program edit must not make a
# HEAD-based diff report 0). Since the landing protocol, a committed program change is a
# landing with a receipt and its own `land(...)` commit, visible in git log, so the honest
# reading of the criterion is: these scripts edit nothing in the program as last landed. An
# uncommitted, run-time edit still shows as lines changed. Recorded in saved-work.json as
# program_lines_changed_base.


def _program_base() -> str:
    completed = subprocess.run(
        ["git", "log", "-1", "--format=%H", "--", "program.py", "calculations.py"],
        cwd=HERE, capture_output=True, text=True,
    )
    sha = completed.stdout.strip()
    return sha or "d9dded6"


DAY2_BASE = _program_base()


def resolve_named_out_dir(out: str | None, default_rel: str, force: bool) -> str:
    """Unlike run.py's resolve_out_dir (whose default is a fresh temp dir so Day 1's
    audited evidence/run-1 is never rewritten by accident), these scripts' evidence
    directories (evidence/run-2-regroup, ...) ARE the thing being produced, so the
    default `--out` is that tracked directory itself. An existing non-empty directory
    is still refused without --force, so a bare re-run cannot silently overwrite it."""
    out_dir = os.path.join(HERE, default_rel) if out is None else (out if os.path.isabs(out) else os.path.join(HERE, out))
    if os.path.isdir(out_dir) and os.listdir(out_dir) and not force:
        raise FileExistsError(f"{out_dir} already holds evidence; pass --force to overwrite it")
    return out_dir


# --------------------------------------------------------------- grouping-generic markdown


def planted_weight_of_variant(variant: Mapping[str, Any], groups: Mapping[str, list[str]]) -> float:
    """Sum of |TRUE_W| over the columns this variant's dropped group(s) hold.

    Unlike features.planted_weight_by_group() (keyed by Day 1's group names
    g0..g4), this reads the columns straight from `groups[name]` for whatever
    name the variant's `drop` list carries, so it works for run_regrouped.py's
    h0/h1/h2 grouping without a name-lookup mismatch.
    """
    columns = [column for name in variant["drop"] for column in groups[name]]
    return _total(abs(TRUE_W[FEATURES.index(column)]) for column in columns)


def failed_variants(comparison: list[dict], groups: Mapping[str, list[str]]) -> list[dict]:
    out = []
    for row in comparison:
        if row["variant"] == BASELINE_KEY:
            continue
        if abs(row["delta_vs_baseline"]) < UNINFORMATIVE_DELTA:
            variant = {"key": row["variant"], "drop": [row["variant"].removeprefix("drop_")]}
            out.append({
                "variant": row["variant"],
                "delta_vs_baseline": row["delta_vs_baseline"],
                "planted_weight": planted_weight_of_variant(variant, groups),
            })
    return out


def comparison_markdown(*, title: str, seed: int, n: int, groups: Mapping[str, list[str]], variants: list[dict], comparison: list[dict]) -> str:
    by_key = {variant["key"]: variant for variant in variants}
    lines = [
        f"# {title}, seed={seed} n={n}",
        "",
        f"Leave-one-group-out over {len(groups)} groups x {len(next(iter(groups.values())))} features; "
        f"baseline `{BASELINE_KEY}` keeps every column.",
        "Rank 1 is the largest RMSE increase when the group is dropped.",
        "",
        "| rank | variant | rmse | delta vs baseline | planted |w| in group |",
        "|---:|---|---:|---:|---:|",
    ]
    for row in comparison:
        weight = (
            planted_weight_of_variant(by_key[row["variant"]], groups)
            if row["variant"] != BASELINE_KEY
            else _total(abs(w) for w in TRUE_W)
        )
        lines.append(f"| {row['rank']} | {row['variant']} | {row['rmse']:.4f} | {row['delta_vs_baseline']:+.4f} | {weight:.1f} |")
    lines.append("")
    lines.append(f"Ranking (ablations only): {' > '.join(ranking(comparison))}")
    lines.append("")
    return "\n".join(lines)


def failed_variants_markdown(comparison: list[dict], groups: Mapping[str, list[str]]) -> str:
    rows = failed_variants(comparison, groups)
    lines = [
        "# Failed / uninformative variants",
        "",
        f"A variant is uninformative when |delta vs baseline| < {UNINFORMATIVE_DELTA}. Retained, not dropped.",
        "",
    ]
    if not rows:
        lines.append("None for this grouping/seed.")
    for row in rows:
        lines.append(
            f"- `{row['variant']}`: delta {row['delta_vs_baseline']:+.4f}; planted |w| in its dropped group(s) = "
            f"{row['planted_weight']:.1f}."
        )
    lines.append("")
    return "\n".join(lines)


# --------------------------------------------------------------- program-lines-changed


def changed_lines(paths: list[str], repo_dir: str = HERE, base: str = DAY2_BASE) -> dict[str, int]:
    """{basename: added+deleted lines} against `base`; 0 for a path git diff reports nothing for.

    Measured, not asserted: run_regrouped.py/run_reinput.py/run_from_retained.py change
    only input Parts and the variants list, so this is expected (and tested) to be all
    zeros -- but it is computed here, not hard-coded (gap 18b: "every number ... computed
    at run time").

    `base` defaults to DAY2_BASE rather than HEAD (fixer round 1, finding 11) and the
    caller records it in saved-work.json, so a reader can see what the zero is measured
    against instead of inferring a moving checkpoint.
    """
    counts = {os.path.basename(path): 0 for path in paths}
    proc = subprocess.run(
        ["git", "diff", "--numstat", base, "--", *paths],
        cwd=repo_dir, capture_output=True, text=True, check=True,
    )
    for line in proc.stdout.strip().splitlines():
        added, deleted, name = line.split("\t")
        total = (0 if added == "-" else int(added)) + (0 if deleted == "-" else int(deleted))
        counts[os.path.basename(name)] = total
    return counts


# --------------------------------------------------------------- retained record + receipts


def load_json(path: str) -> Any:
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def write_retained(pxc, run, external_addresses: list[str], registry: Mapping[str, Any], out_dir: str) -> dict:
    """retained.json for runs 2-4. `retained_at` carries the same sha commit.txt does,
    so record["provider"] is never read as the library that produced the run when it is
    only the library that retained the record (fixer round 1, finding 5)."""
    path = os.path.join(out_dir, "retained.json")
    sha = commit_sha(HERE, WATCHED_PATHS, exclude=evidence_excludes(out_dir))
    record = retain.retain_run(
        pxc, run, external_addresses, registry=registry, record_path=path,
        retained_at={"commit": sha},
    )
    retain.write_record(record, path)
    return record


def write_receipts(run, out_dir: str) -> dict:
    payload = receipts_payload(run)
    _dump(os.path.join(out_dir, "receipts.json"), payload)
    return payload


# --------------------------------------------------------------- input Parts, by digest


def external_digests(record: Mapping[str, Any]) -> dict[str, str | None]:
    """{external address: sha256 of that entry} for one retained record.

    An inline external is digested with `retain.digest_of` -- the same canonical JSON,
    no `default=`, that produced `record["results"]`. A sidecar external
    ({"digest", "ref"}, retain.py:579-582) is represented by the digest it already
    carries, so a value too large or too non-JSON to inline is compared by the same
    kind of measurement as an inline one rather than by the filename beside it.
    """
    out: dict[str, str | None] = {}
    for address, entry in (record.get("external") or {}).items():
        if isinstance(entry, Mapping) and "digest" in entry and "ref" in entry:
            out[address] = entry["digest"]
        else:
            out[address] = retain.digest_of(entry)
    return out


def input_parts_changed(
    record_prior: Mapping[str, Any], record_this: Mapping[str, Any]
) -> list[str]:
    """The external addresses whose value differs between two retained records.

    Computed, never passed in (Day 2 fixer round 3, finding 4). Each of the three
    Day 2 scripts used to hand `saved_work` a literal list naming what its author
    believed it had changed -- `["input.ablation.groups"]`, `["input.ablation.rows"]`,
    `[SPLIT.address]` -- so the field agreed with the script's intent by construction
    and would have kept agreeing if the script had changed a different Part, or none.
    It is now read out of the two records' `external` maps by digest, which is the
    same evidence `compare_local._external_changed` reasons over.

    Scope is the UNION of both records' external addresses, so an input Part that one
    run reads and the other does not counts as changed: run-4 dropping
    `input.ablation.rows` (it consumes run-1's retained split instead) is a change to
    the run's input Parts exactly as much as the `scratch.ablation.split` it added,
    and reporting only the addition would describe half of the boundary move.
    An address present in both with an equal digest is not listed.
    """
    prior, this = external_digests(record_prior), external_digests(record_this)
    return sorted(
        address
        for address in set(prior) | set(this)
        if prior.get(address) != this.get(address)
    )


# --------------------------------------------------------------- saved-work.json (reuse ledger)


def saved_work(
    *,
    run_label: str,
    prior_run_label: str,
    registry_addresses_used: list[str],
    all_registry_addresses: list[str],
    record_prior: Mapping[str, Any],
    record_this: Mapping[str, Any],
    prior_receipts: Mapping[str, Mapping[str, Any]],
    program_lines: Mapping[str, int],
    program_lines_base: str,
    skip_reason: str,
) -> dict:
    """The Day 2 reuse ledger: what compare_local.explain_changes says can be skipped,
    and how many ms that would have saved, read from the *prior* run's receipts.json.

    `program_lines_base` is the sha the program-lines diff was taken against (DAY2_BASE,
    not HEAD): the kill criterion asks whether *this day* edited program.py or
    calculations.py, and HEAD moves while the day runs (fixer round 1, finding 11).

    `skip_reason` names which half of explain_changes' output counts as "skippable"
    for this run: 'unchanged_upstream' (run_regrouped.py, run_reinput.py -- the
    invocation still exists in both programs and its retained digest matches) or
    'removed' (run_from_retained.py -- the invocation was not declared at all
    because its output was seeded as an external Part instead).

    `input_parts_changed` is NOT a parameter: it is derived here from the two
    records' external digests by `input_parts_changed(record_prior, record_this)`
    (fixer round 3, finding 4), so no caller can assert what it changed.
    """
    explanation = compare_local.explain_changes(record_prior, record_this)
    skippable = explanation[skip_reason]
    ms_saved_by_invocation = {
        invocation_id: prior_receipts[invocation_id]["duration_ms"]
        for invocation_id in skippable
        if invocation_id in prior_receipts
    }
    calculations_added = sorted(set(registry_addresses_used) - set(all_registry_addresses))
    return {
        "run": run_label,
        "prior_run": prior_run_label,
        "calculations_inherited": sorted(registry_addresses_used),
        "calculations_added": calculations_added,
        "program_lines_changed": {**program_lines, "total": sum(program_lines.values())},
        "program_lines_changed_base": program_lines_base,
        "input_parts_changed": input_parts_changed(record_prior, record_this),
        "explain_changes": explanation,
        "skip_reason": skip_reason,
        "invocations_skippable_by_digest": skippable,
        "ms_saved_by_invocation": ms_saved_by_invocation,
        "ms_saved": round(sum(ms_saved_by_invocation.values()), 3),
    }


def write_common_evidence(
    out_dir: str,
    *,
    title: str,
    seed: int,
    n: int,
    groups: Mapping[str, list[str]],
    variants: list[dict],
    testimony: dict,
    comparison: list[dict],
    pcr,
    timings: list[dict],
    repo_dir: str = HERE,
    watch: tuple[str, ...] = WATCHED_PATHS,
) -> None:
    """The Day 1 file set minus saved-work.json (each run's saved-work.json differs
    in shape from Day 1's and is written separately by the caller with `saved_work`).
    `timings` is the only field here that is not expected to reproduce byte-for-byte
    across two regenerations of the same run (wall-clock, not semantics)."""
    os.makedirs(out_dir, exist_ok=True)
    sha = commit_sha(repo_dir, watch, exclude=evidence_excludes(out_dir))
    _dump(os.path.join(out_dir, "testimony.json"), testimony)
    _dump(os.path.join(out_dir, "comparison.json"), {
        "seed": seed, "n": n, "baseline": BASELINE_KEY,
        "ranking": ranking(comparison), "rows": comparison,
    })
    _text(os.path.join(out_dir, "comparison.md"), comparison_markdown(
        title=title, seed=seed, n=n, groups=groups, variants=variants, comparison=comparison,
    ))
    _dump(os.path.join(out_dir, "timings.json"), {"seed": seed, "n": n, "timings": timings})
    _dump(os.path.join(out_dir, "variants.json"), {
        "seed": seed, "groups": groups, "variants": variants,
        "failed_or_uninformative": failed_variants(comparison, groups),
    })
    _text(os.path.join(out_dir, "failed-variants.md"), failed_variants_markdown(comparison, groups))
    _text(os.path.join(out_dir, "mermaid.mmd"), pcr.mermaid())
    _text(os.path.join(out_dir, "commit.txt"), sha + "\n")
