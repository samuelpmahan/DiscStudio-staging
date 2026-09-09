#!/usr/bin/env python3
"""Generate ``ART-REGISTRY.md``, an executable index over ``art_registry.py``.

This is not a hand-maintained document. Every row below is read straight out
of ``art_registry.ALL_FAMILIES`` / ``art_registry.CARD_RENDERERS`` -- the same
objects the consumer's tests hold to being complete (``test_art_registry.py``)
-- plus the tally table in
``pyto/experiments/art-tournament/RESULTS.md``. Nothing here is typed twice:
if a slug's status, tally or evidence changes in ``art_registry.py``, running
this script again changes the row. That is also the enforcement mechanism:
``scripts/check_all.sh`` runs this generator and then ``git diff --quiet`` on
its output, so a stale ``ART-REGISTRY.md`` (regenerated content differs from
what is committed) fails the check.

Owner directive, carried into the header this script writes: keep everything
until it can be tested in the browser. Every one of the 16 disc-art families
and all 8 studios' card renderers is registered as a Calculation here,
``status`` records only which module serves the code today, and promotion is
reversible vocabulary -- see ``art_registry.PROMOTION_POLICY``.

Exit status: this script exits non-zero, writing nothing, if any entry that
should carry a tally (every family or card renderer except the four classic
originals, which predate the tournament) lacks one, or if any entry -- classic
included -- lacks a resolvable evidence path. Those are exactly the invariants
``art_registry._family`` and ``art_registry._card`` already enforce at import
time; this is a second, independent check over the generated document's own
data so a broken index cannot be produced silently.
"""
from __future__ import annotations

import os
import sys

CONSUMER_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if CONSUMER_DIR not in sys.path:
    sys.path.insert(0, CONSUMER_DIR)

import art_registry  # noqa: E402

OUT_PATH = os.path.join(CONSUMER_DIR, "ART-REGISTRY.md")
TOURNAMENT_DIR = os.path.join(os.path.dirname(os.path.dirname(CONSUMER_DIR)),
                              "experiments", "art-tournament")
RESULTS_RELATIVE = "pyto/experiments/art-tournament/RESULTS.md"

# The test that pins each kind of entry, keyed by status. Family and card
# renderer tests live in different files, so the two tables are separate.
FAMILY_TEST_BY_STATUS = {
    "classic": "test_paint_families.py (FROZEN_CLASSIC sha256) + "
               "test_art_registry.py::RegisteredCodeIsTheSourceCodeTest::"
               "test_classic_families_render_exactly_as_paint_components_does + "
               "::test_the_frozen_classic_bytes_are_untouched_by_this_registry",
    "promoted": "test_paint_families.py (promotion freeze) + "
                "test_art_registry.py::RegisteredCodeIsTheSourceCodeTest::"
                "test_promoted_families_render_exactly_as_paint_components_does + "
                "::test_promoted_families_are_the_promoted_function_not_a_second_copy",
    "retained": "test_art_registry.py::RegisteredCodeIsTheSourceCodeTest::"
                "test_retained_families_render_exactly_as_their_studio_source_does",
}
CARD_TEST_BY_STATUS = {
    "promoted": "test_card_render.py + "
                "test_art_registry.py::EveryCardRendererDrawsTest::"
                "test_the_promoted_pair_is_card_render_itself_not_a_copy",
    "retained": "test_art_registry.py::EveryCardRendererDrawsTest::"
                "test_every_renderer_draws_exactly_what_its_studio_source_draws",
}

STATUS_HEADING = {
    "classic": "Classic",
    "promoted": "Promoted (provisional)",
    "retained": "Retained (available, not promoted)",
}


def _tally_text(tally):
    if tally is None:
        return "no tally -- predates the tournament"
    j1, j2, j3 = tally.judges
    return "rank %d, judges %d + %d + %d = **%d**/%d, outcome *%s* (%s)" % (
        tally.rank, j1, j2, j3, tally.total, tally.ceiling, tally.outcome, tally.source)


def _stringify_param(value):
    """A FAMILY_PARAMS value: usually a sentence, sometimes a per-field dict."""
    if isinstance(value, dict):
        return "; ".join("%s: %s" % (key, value[key]) for key in value)
    return str(value)


def _param_change_text(entry):
    params = entry.params
    target_note = params.get("target") or params.get("targets") or ""
    parts = []
    for key in ("seed", "base", "accent", "label"):
        value = params.get(key)
        if value:
            parts.append("**%s** -- %s" % (key, _stringify_param(value)))
    if target_note:
        parts.append("**target** -- %s" % _stringify_param(target_note))
    return "<br>".join(parts)


def _evidence_paths(entry):
    missing = [path for path in entry.evidence
               if not os.path.isfile(os.path.join(TOURNAMENT_DIR, path))]
    return entry.evidence, missing


def _validate():
    """Return a list of problems; empty means the registry is fit to index."""
    problems = []
    for slug, entry in sorted(art_registry.ALL_FAMILIES.items()):
        if entry.status != "classic" and entry.tally is None:
            problems.append("family %s (status=%s) has no tally" % (slug, entry.status))
        evidence, missing = _evidence_paths(entry)
        if not evidence:
            problems.append("family %s has no evidence path" % slug)
        for path in missing:
            problems.append("family %s evidence path does not exist: %s" % (slug, path))
    for kind in ("single", "battle"):
        for studio, entry in sorted(art_registry.CARD_RENDERERS[kind].items()):
            if entry.tally is None:
                problems.append("card %s/%s has no tally" % (kind, studio))
            evidence, missing = _evidence_paths(entry)
            if not evidence:
                problems.append("card %s/%s has no evidence path" % (kind, studio))
            for path in missing:
                problems.append("card %s/%s evidence path does not exist: %s" % (kind, studio, path))
    return problems


def _family_render_line(slug):
    return "`art_registry.family_render(%r, seed, base, accent, target, label)`" % slug


def _card_render_line(kind, studio):
    return ("`art_registry.card_renderer(%r, %r).render(card, art, width)`"
            % (kind, studio))


def _family_row(entry):
    return "| `%s` | %s | %s | %s | %s | %s | %s | %s |" % (
        entry.slug,
        entry.name,
        entry.studio,
        entry.status,
        _tally_text(entry.tally),
        _param_change_text(entry),
        _family_render_line(entry.slug),
        ", ".join(entry.evidence),
    )


def _family_section(status):
    entries = [entry for entry in art_registry.ALL_FAMILIES.values() if entry.status == status]
    entries.sort(key=lambda entry: entry.slug)
    lines = [
        "### " + STATUS_HEADING[status],
        "",
        "Pinned by: " + FAMILY_TEST_BY_STATUS[status],
        "",
        "| slug | name | studio | status | tally | seed/base/accent/label/target | render | evidence |",
        "|---|---|---|---|---|---|---|---|",
    ]
    lines.extend(_family_row(entry) for entry in entries)
    lines.append("")
    return lines


def _card_section():
    lines = [
        "## Card renderers",
        "",
        "All 8 studio Single and Battle renderers, addressed "
        "`fn.card.<kind>.render.<studio>`. The promoted pair also answers to the "
        "un-suffixed aliases `fn.card.single.render` / `fn.card.battle.render` "
        "that `card_render.py` already published.",
        "",
        "| kind | studio | status | tally | address | render | evidence | pinned by |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for kind in ("single", "battle"):
        for studio, entry in sorted(art_registry.CARD_RENDERERS[kind].items()):
            lines.append("| %s | %s | %s | %s | `%s` | %s | %s | %s |" % (
                kind, studio, entry.status, _tally_text(entry.tally),
                entry.address, _card_render_line(kind, studio),
                ", ".join(entry.evidence), CARD_TEST_BY_STATUS[entry.status]))
    lines.append("")
    return lines


def build_document():
    counts = art_registry.STATUS_COUNTS
    header = [
        "# Art registry",
        "",
        "Generated by `scripts/generate_art_registry_md.py` from `art_registry.py` "
        "and `" + RESULTS_RELATIVE + "`. Do not hand-edit -- regenerate instead; "
        "`scripts/check_all.sh` fails if this file does not match what "
        "`art_registry.py` currently says.",
        "",
        "**Owner directive: keep everything until it can be tested in the "
        "browser.** All 16 disc-art families (4 classic, 3 promoted, 9 "
        "retained) and all 8 studios' Single and Battle card renderers (2 "
        "promoted, 6 retained) are registered here as addressed Calculations. "
        "`status` records only which module currently serves the code -- "
        "**local promotion is reversible vocabulary, not a stability claim**: "
        "" + art_registry.PROMOTION_POLICY + " Every scored entry carries the "
        "judge tally that produced its status as provenance; the four classic "
        "families predate the tournament and carry no tally.",
        "",
        "Family status counts: classic %d, promoted %d, retained %d. "
        "Card renderer status counts: promoted %d, retained %d." % (
            counts["families"]["classic"], counts["families"]["promoted"],
            counts["families"]["retained"], counts["cards"]["promoted"],
            counts["cards"]["retained"]),
        "",
        "---",
        "",
        "## Disc-art families",
        "",
    ]
    lines = list(header)
    for status in ("classic", "promoted", "retained"):
        lines.extend(_family_section(status))
    lines.append("---")
    lines.append("")
    lines.extend(_card_section())
    return "\n".join(lines).rstrip("\n") + "\n"


def main() -> int:
    problems = _validate()
    if problems:
        sys.stderr.write("generate_art_registry_md: registry is not fit to index:\n")
        for problem in problems:
            sys.stderr.write("  - %s\n" % problem)
        return 1
    document = build_document()
    with open(OUT_PATH, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(document)
    print("wrote %s (%d bytes)" % (OUT_PATH, len(document.encode("utf-8"))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
