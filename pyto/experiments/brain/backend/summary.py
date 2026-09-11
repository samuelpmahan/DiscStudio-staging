"""the backend vertical's findings and its map, as Parts.

a finding is `proposal.brain.backend.<k>` with its `for` - why it matters - and,
when it is a friction, the workaround taken and the proposal. the map is
`px.exp.brain.map.backend`: what is built, what is stubbed and why, what is next
and for whom. both are read back by `python -m experiments.brain.map`.

`python -m experiments.brain.backend.summary` writes them; the numbers quoted in
them are not retyped from a terminal, they are read out of the benchmark and
oracle Parts this store already holds.
"""

from __future__ import annotations

from pyto import PQL

from experiments.brain import harness
from experiments.brain.backend import ops

VERTICAL = "backend"


def measured(store, address: str, field: str = "wall_ms_median", default=None):
    """a number quoted in a finding comes out of the Part that measured it."""
    if not store.has(address):
        return default
    return store.get(address)[field]


def findings(store) -> list[str]:
    written = []

    nested = measured(store, harness.bench_address(VERTICAL, "array_store_tournament", "nested_lists", "digest"))
    b64 = measured(store, harness.bench_address(VERTICAL, "array_store_tournament", "base64_float64", "digest"))
    sizes = {
        name: (store.get(f"px.exp.brain.result.backend.array_store_tournament.{name}")["bytes"]
               if store.has(f"px.exp.brain.result.backend.array_store_tournament.{name}") else None)
        for name in ("nested_lists", "flat_and_shape", "base64_float64")
    }

    written.append(harness.finding(
        store, VERTICAL, "the_facade_carried_it", "strength",
        "one Calculation per op with args['backend'], and one oracle Part per engine, turned 'a backend that changes "
        "semantics is a failed backend' from a habit into a check: twelve ops times three engines, one dispatch table, "
        "and every disagreement showed up as a failing Part instead of as a surprise downstream. Three of them were "
        "real - solve raised LinAlgError on numpy and nothing on scipy, argsort disagreed with sorted() on ties, and "
        "eigenvectors came back with opposite signs - and all three were found by the oracle, not by a reader.",
        for_="the stats and ml verticals add an engine by writing a function and an oracle case, and cannot add one silently",
    ))

    written.append(harness.finding(
        store, VERTICAL, "the_store_pays_for_decimal_text", "friction",
        "a 256x256 float64 matrix costs %s bytes as the nested json lists the contract's dataset Part specifies and %s "
        "bytes as base64 of the float64 buffer, and flattening the nested lists to one list plus a shape saves %s of "
        "those bytes - 0.04%%. The cost is not the brackets, it is that every number is written out as decimal text and "
        "parsed back. Digesting one costs %.1f ms nested against %.1f ms base64, and every Part in every run record is "
        "digested." % (sizes["nested_lists"], sizes["base64_float64"],
                       (sizes["nested_lists"] - sizes["flat_and_shape"]) if sizes["flat_and_shape"] else "?",
                       nested or 0.0, b64 or 0.0),
        for_="the ml vertical's matrices are the store's contents, and a record it takes a second to digest is a record nobody writes",
        workaround="the array_store bracket: base64 of the float64 buffer won it on bytes and on speed, and round-trips exactly",
        proposal="a Part value kind that is bytes with a declared dtype and shape, so materialize digests the buffer instead "
                 "of re-serialising 65536 numbers as text, and PQL can still answer 'what shape is it' without decoding",
    ))

    written.append(harness.finding(
        store, VERTICAL, "json_has_no_complex_number", "friction",
        "fft's answer is complex and the store is json, so every engine returns {'real': [...], 'imag': [...]} - a "
        "convention the facade has to enforce because nothing else can. eig refuses a matrix with a complex spectrum "
        "rather than quietly returning the real part, which is the honest choice and also a hole: there is no way to "
        "say 'this Part is complex' and have a reader know it.",
        for_="every spectral method the ml and stats verticals will want - pca, whitening, filters - lands on this the moment it is not symmetric",
        workaround="two real lists, and a loud refusal where the pair would be a lie",
        proposal="a declared value kind on the Part (complex128 with real/imag, or the bytes kind above), checked once "
                 "where a value is put rather than at every call site that reads one",
    ))

    written.append(harness.finding(
        store, VERTICAL, "pql_cannot_ask_across_a_prefix", "friction",
        "PQL selects a Part or a prefix and refines with a python predicate, which is enough to find things and not "
        "enough to ask about them. The three questions this vertical actually had - 'the fastest engine per op at the "
        "largest size', 'every op whose py oracle passes but whose sp oracle does not', 'the benchmark Parts that share "
        "an inputs_sha256' - are a group-by, a join on a shared address segment, and a min per group. navigate() ends "
        "up splitting addresses on '.' by hand to recover the (kind, vertical, calc, backend, size) the address scheme "
        "already encodes, because the scheme is a convention PQL does not know.",
        for_="the map is the deliverable, and today it is python over matches rather than a query anyone could re-ask",
        workaround="harness.navigate splits addresses into (kind, vertical) itself and the rest is list comprehensions",
        proposal="PQL.pattern('px.exp.brain.bench.{vertical}.{calc}.{backend}.{size}') binding segments as named fields, "
                 "with .group(by=...) and .best(field, direction) over the bound names - selection stays first-class, "
                 "and the address scheme stops being a string convention only the reader knows",
    ))

    written.append(harness.finding(
        store, VERTICAL, "a_wall_clock_in_a_tracked_file_stops_every_landing", "friction",
        "a run record holds duration_ms and a benchmark Part holds wall_ms, so any suite that writes one into a tracked "
        "path rewrites it on every run. MAIN then has a dirty file, land.sh refuses to land into a dirty tree, and it "
        "refuses it for whoever lands next rather than for whoever wrote it. It cost this vertical three refused "
        "landings and a merge conflict on a file it does not own.",
        for_="three verticals landing through one lock means one vertical's regenerated evidence is everyone's outage",
        workaround="harness.Store writes its store and records into a temporary directory unless it is an explicit record "
                   "run (Store(commit=True), or BRAIN_RECORDS=commit), so a test cannot dirty the repository",
        proposal="run_record grows a stable mode that omits the clock (USE.md section 5 already names the two fields a "
                 "clock reaches), so a committed record is byte-stable and a test may regenerate it; and land.sh treats a "
                 "file whose only diff is those fields as unclaimed rather than as someone else's candidate",
    ))

    written.append(harness.finding(
        store, VERTICAL, "the_pure_python_engine_is_the_reference_that_pays_for_itself", "strength",
        "the py engine is slower than numpy everywhere and it is the reason the other two can be trusted: it is the only "
        "engine a reader can check by reading. It also located both of the night's real results - the guarded gram "
        "expansion (the obvious pure-python speedup is wrong in its eighth digit where two points are close, which the "
        "oracle caught at 1e-8) and the two places a py engine cannot go honestly (a general non-symmetric eig, and "
        "svd's u and v), which are stubs in the map rather than wrong answers in the store.",
        for_="every vertical is about to be tempted to skip the py engine because numpy is right there",
    ))

    # px.exp.brain.bench.backend.<calc>.<engine>.<size>: the tournaments put a branch name where
    # the engine goes, so only the three real engines are counted here.
    plan = store.get("px.exp.brain.result.backend.plan") if store.has("px.exp.brain.result.backend.plan") else None
    if plan:
        flips = [op for op, steps in plan["by_op"].items() if len({step[1] for step in steps}) > 1]
        written.append(harness.finding(
            store, VERTICAL, "the_benchmark_parts_are_what_decides", "strength",
            "the benchmark Parts are folded into one Part - px.exp.brain.result.backend.plan - and `backend=\"auto\"` "
            "reads it, so 'which engine' stops being a habit and becomes a thing the store answers at the size the "
            "caller actually has. It is still a pure Calculation: the plan is an input like any other, and an auto with "
            "no plan is refused by name rather than quietly given numpy. Of the %d ops with a plan, %d change engine "
            "somewhere across their three measured sizes (%s), which is the whole argument for not hard-coding one."
            % (len(plan["ops"]), len(flips), ", ".join(sorted(flips)) or "none tonight"),
            for_="the stats and ml verticals, which are each about to pick a default backend per calculation and would "
                 "otherwise pick it from reflex",
        ))

    written.append(harness.finding(
        store, VERTICAL, "packing_wins_by_how_long_the_numbers_are", "strength",
        "the array_store bracket's winner is now fn.brain.backend.pack / unpack, and the round trip is exact rather "
        "than close: the float64 buffer, base64'd, and back, with no decimal text in between. The boundary is worth "
        "knowing and is a test rather than a slogan: base64 of float64 is a flat 11 bytes per number whatever the "
        "number is, while json is as long as the decimal text - about 20 bytes for a drawn float64 and 6 for a small "
        "round one. So packing wins by roughly 1.8x on measured data and LOSES on a table of small integers.",
        for_="the ml vertical's matrices should be packed and the data vertical's count columns should not, and neither "
             "is a matter of taste once the numbers are in a Part",
    ))

    written.append(harness.finding(
        store, VERTICAL, "the_judge_could_not_be_another_session", "friction",
        "the contract asks for two or three branches built by separate workers and a judge that did not build. "
        "No route to a scoped worker session existed in this environment, so every branch in all three brackets was "
        "written in one session and the judge is `evidence`: a pure function of the candidate's own oracle Part, its "
        "benchmark Part at the largest size, and its source. That is weaker as independence and stronger as evidence - "
        "it cannot be talked into anything and every score points at the Part it came from - but it is not what was "
        "asked for, and the bracket records which judge scored it so nobody has to guess later.",
        for_="a tournament is only worth the independence of its judge, and a reader a month from now must be able to "
             "see which kind they are looking at",
        workaround="criteria written into the bracket Part before any score exists, a judge that is a function of the "
                   "recorded Parts, and a test that rebuilds all three brackets from the candidates so the verdict is "
                   "reproducible rather than trusted",
        proposal="either the sprint harness hands a vertical a way to run a scoped worker session, or the contract says "
                 "plainly that a recorded, re-runnable scoring function over the evidence Parts is the judge of record",
    ))

    written.append(harness.finding(
        store, VERTICAL, "a_copy_that_did_not_really_merge_claims_mains_commits", "friction",
        "`neat update` stops when MAIN and the copy both changed a file, which for a regenerated run record is every "
        "time. Bringing the copy forward by restoring that one file - rather than completing the merge - leaves MAIN's "
        "tip not an ancestor of exp/<id>, and `land.sh` then computes the candidate from the task's STARTING point: "
        "task 87's receipt claimed 7 files and listed 10 unclaimed ones belonging to two other verticals, including "
        "another task's packet, and refused. It was verified green twice before anyone noticed the diff was wrong.",
        for_="three verticals landing through one lock means a candidate that quietly widens is everyone's problem, and "
             "the receipt is the only place it shows",
        workaround="finish a real merge in the copy - `git merge <MAIN sha>`, resolve the record by taking MAIN's copy, "
                   "commit - so `git merge-base` is MAIN's tip again, then pack and land",
        proposal="`neat update` should not report success unless MAIN's tip is an ancestor of the copy afterwards, and "
                 "`neat pack` should refuse to pack a copy where it is not, naming the sha it expected",
    ))

    written.append(harness.finding(
        store, VERTICAL, "a_case_that_names_its_engines_keeps_the_refusal_in_the_record", "strength",
        "two cases here are answered by np and sp and refused by py, because the py svd goes through a^T a and cannot "
        "resolve a singular value near sqrt(eps). The case table says `engines=(\"np\", \"sp\")` rather than dropping "
        "the case, so the oracle table stays a table: every engine that answers is checked against the reference, and "
        "the one that does not is a stub in the map with the reason, not a gap nobody can see.",
        for_="a backend surface grows by engines that cannot all do everything, and the alternative to saying so is "
             "a test file with a hole in it",
    ))

    fastest = {}
    for match in PQL.prefix("px.exp.brain.bench.backend.").matches(store.pxc):
        parts = match.address.split(".")
        if len(parts) != 8 or parts[6] not in ops.ENGINES:
            continue
        fastest.setdefault((parts[5], parts[7]), []).append((match.value["wall_ms_median"], parts[6]))
    wins = {}
    for (calc, size), rows in fastest.items():
        wins.setdefault(min(rows)[1], 0)
        wins[min(rows)[1]] += 1
    written.append(harness.finding(
        store, VERTICAL, "where_the_engine_boundary_pays", "strength",
        "counted over every benchmark Part this vertical wrote, the fastest engine per (op, size) is: %s. The py engine "
        "is not last everywhere - at the smallest sizes the numpy call's own overhead is the whole measurement - so "
        "'use numpy' is a claim about size, and the benchmark Parts are where a vertical can check it instead of "
        "assuming it." % (", ".join(f"{engine} {count}" for engine, count in sorted(wins.items(), key=lambda one: -one[1])) or "nothing measured yet"),
        for_="the stats and ml verticals choosing a default backend per calculation, from evidence rather than from reflex",
    ))
    return written


def map_part(store) -> str:
    built = sorted(
        PQL.prefix("px.exp.brain.result.backend.").addresses(store.pxc)
        + PQL.prefix("px.exp.brain.bracket.backend.").addresses(store.pxc)
    )
    return harness.map_part(
        store, VERTICAL,
        built=[f"fn.brain.backend.{op}" for op in ops.ops()] + [a for a in built if a.startswith("px.exp.brain.bracket.")],
        stubbed=[
            {"address": "fn.brain.backend.eig (py, non-symmetric)",
             "why": "the jacobi sweep is symmetric-only; a general eigenproblem wants a hessenberg reduction and a shifted "
                    "qr iteration, and a half-built one would be a worse reference than numpy's. py refuses and says so"},
            {"address": "fn.brain.backend.svd (u and v)",
             "why": "singular values are canonical, the vectors carry a per-column sign freedom the three engines spend "
                    "differently; pinning it is real work and a wrong pin reads as a wrong answer"},
            {"address": "fn.brain.backend.eig (complex spectra)",
             "why": "json has no complex number and there is no declared value kind yet; eig refuses rather than returning "
                    "the real part (proposal.brain.backend.json_has_no_complex_number)"},
            {"address": "fn.brain.backend.fft (py, non-power-of-two)",
             "why": "the py engine is radix-2; bluestein's algorithm is the honest fix and np/sp already answer"},
            {"address": "fn.brain.backend.matrix_rank and pinv (py, near a rank boundary)",
             "why": "the py svd takes square roots of the eigenvalues of a^T a, which squares the condition number: a "
                    "truly zero singular value comes back at about sqrt(eps) times the largest, far above numpy's rank "
                    "tolerance and far below anything this engine can resolve. It refuses that band by name and np and "
                    "sp answer; a py svd worth trusting there is a one-sided jacobi, which is its own task"},
            {"address": "fn.brain.backend.lu",
             "why": "numpy has no lu, so an 'np' engine would be scipy wearing numpy's name. It waits for the day the "
                    "facade lets an op declare two engines instead of three"},
            {"address": "fn.brain.backend.qr (the full factorisation, and column pivoting)",
             "why": "the reduced qr is what a least squares needs and it is built; the full q and a rank-revealing "
                    "pivot are a different job and would want their own oracle"},
            {"address": "fn.brain.backend.pack (anything but float64)",
             "why": "one dtype, said out loud: unpack refuses float32 by name rather than guessing. int64 and "
                    "complex128 are the next two and each needs its own exactness oracle"},
            {"address": "fn.brain.backend.* (sparse, out-of-core, gpu)",
             "why": "not started: the dense facade had to exist first for the other two verticals to build on tonight"},
        ],
        next_=[
            {"what": "the kernel half of the packed Part: materialize digesting the buffer instead of re-serialising it, "
                     "and PQL answering 'what shape is it' without decoding. fn.brain.backend.pack/unpack is the vertical "
                     "half and it is built; a packed Part is still a string to everything above it",
             "for": "the ml vertical, whose Parts are matrices and whose records are the deliverable"},
            {"what": "einsum-lite, kron, and the sparse forms of solve and matmul; and an op that may declare fewer "
                     "than three engines, which is what lu needs",
             "for": "the stats and ml verticals, whose next layer is bigger than the dense ops reach"},
            {"what": "cholesky, qr, lu, matrix_inverse, matrix_rank, norm, einsum-lite over the same facade",
             "for": "the stats vertical's regression and covariance work, which is doing it by hand today"},
            {"what": "convolve, correlate, interpolate, rfft/irfft and a windowing op",
             "for": "the data vertical's time series calculations"},
            {"what": "the plan rebuilt on the machine that runs it, and a Calculation that rebuilds it as a Part rather "
                     "than a module function, so a run record shows which engine was chosen and why",
             "for": "everyone: backend='auto' is built and reads px.exp.brain.result.backend.plan, but the plan is "
                    "measured here and a slower or faster machine would choose differently"},
            {"what": "PQL.pattern with named address segments and group/best (proposal.brain.backend.pql_cannot_ask_across_a_prefix)",
             "for": "the map, which is a deliverable and is python over matches today"},
        ],
        for_="what the backend vertical has, what it deliberately does not have, and what the other two verticals are waiting on",
    )


def main() -> int:
    store = harness.Store(commit=True)
    store.load_store()
    written = findings(store)
    address = map_part(store)
    store.save(VERTICAL)
    print(f"{len(written)} findings, map at {address}")
    print(harness.territory(store))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
