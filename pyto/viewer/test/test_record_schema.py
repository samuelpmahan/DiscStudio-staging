"""Both directions of pyto-run-record@1 hold.

Python -> JavaScript is covered by `viewer/test/adapters.test.mjs`, which loads
the file `pyto.materialize.run_record` wrote for grouped-ablation run-1,
validates it and renders it.

This suite is the other direction. `emit_adapter_records.mjs` writes out every
JavaScript adapter's output; `record_schema.py` -- a Python validator
transcribed from RECORD.md independently of `adapters.js` -- reads them back. A
field either side invents or omits fails here, because the validator's key sets
are exact in both directions.

It also proves the validator is not vacuous (every rule is shown rejecting its
own violation) and that the two validators agree: the same mutation is refused
by both runtimes, naming the same path.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
VIEWER = os.path.dirname(HERE)
PYTO = os.path.dirname(VIEWER)
REAL_RECORD = os.path.join(PYTO, "experiments", "grouped-ablation", "evidence", "run-1", "record.json")
# The one committed record of a run that performed effects (task 49): one `oc.`
# invocation with a five-entry ledger and one pure `fn.` with an empty one.
EFFECTS_RECORD = os.path.join(PYTO, "tests", "fixtures", "px", "effects-record.json")

sys.path.insert(0, HERE)
from record_schema import (  # noqa: E402
    SCHEMA, RecordSchemaError, derive_part_index, invocation_effects, invocation_placement,
    resolve_binding, run_schedule, tick_latency_ms, validate,
)

NODE = shutil.which("node")
needs_node = unittest.skipIf(NODE is None, "node is not on PATH; the JavaScript adapters cannot be run")


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def load(path):
    return json.loads(read(path))


def normalized_parts(parts):
    """RECORD.md fixes which invocations read an address, not their order."""
    return {
        address: {
            "written_by": part["written_by"],
            "preexisting": part["preexisting"],
            "read_by": sorted(part["read_by"]),
        }
        for address, part in parts.items()
    }


def set_at(document, path, value, delete=False):
    """Return a copy of `document` with the dotted `path` set or removed."""
    clone = json.loads(json.dumps(document))
    node = clone
    keys = path.split(".")
    for key in keys[:-1]:
        node = node[int(key) if key.isdigit() else key]
    last = keys[-1]
    if delete:
        del node[int(last) if last.isdigit() else last]
    else:
        node[int(last) if last.isdigit() else last] = value
    return clone


class AdapterOutputs(unittest.TestCase):
    """Everything the JavaScript adapters produce, read by Python."""

    records = None

    @classmethod
    def setUpClass(cls):
        if NODE is None:
            raise unittest.SkipTest("node is not on PATH")
        cls._tmp = tempfile.TemporaryDirectory(prefix="pyto-adapter-records-")
        subprocess.run(
            [NODE, os.path.join("test", "emit_adapter_records.mjs"), cls._tmp.name],
            cwd=VIEWER, check=True, capture_output=True, text=True,
        )
        manifest = load(os.path.join(cls._tmp.name, "manifest.json"))
        cls.records = {entry["name"]: (entry, load(entry["file"])) for entry in manifest}

    @classmethod
    def tearDownClass(cls):
        if getattr(cls, "_tmp", None) is not None:
            cls._tmp.cleanup()

    def test_every_javascript_adapter_output_passes_the_python_validator(self):
        # The strict pass: exact key sets, so a field invented or dropped by any
        # adapter fails here instead of reaching a reader as a silent null.
        self.assertEqual(
            sorted(self.records),
            ["chesslab", "discstudio-first", "discstudio-second", "pyto", "pyto-value-kinds", "wumpus"],
        )
        for name, (entry, record) in sorted(self.records.items()):
            with self.subTest(adapter=name):
                self.assertIs(validate(record), record)
                self.assertEqual(record["schema"], SCHEMA)
                self.assertEqual(record["source"]["runtime"], entry["runtime"])

    def test_all_four_runtimes_of_RECORD_md_are_covered(self):
        runtimes = sorted({record["source"]["runtime"] for _, record in self.records.values()})
        self.assertEqual(runtimes, ["chesslab", "discstudio", "pyto", "wumpus"])

    def test_the_parts_index_agrees_with_a_third_reading_of_the_rule(self):
        # RECORD.md:115 calls `parts` derived. Python re-derives it from the
        # invocations alone and has to land on what JavaScript wrote.
        for name, (_, record) in sorted(self.records.items()):
            with self.subTest(adapter=name):
                self.assertEqual(
                    normalized_parts(derive_part_index(record["ticks"])),
                    normalized_parts(record["parts"]),
                )

    def test_counters_are_recomputable_from_the_ticks(self):
        for name, (_, record) in sorted(self.records.items()):
            with self.subTest(adapter=name):
                invocations = [i for tick in record["ticks"] for i in tick["invocations"]]
                self.assertEqual(record["counters"]["invocations"], len(invocations))
                self.assertEqual(record["counters"]["hits"], sum(1 for i in invocations if i["hit"]))
                self.assertEqual(
                    record["counters"]["hits"] + record["counters"]["computed"],
                    record["counters"]["invocations"],
                )

    def test_a_runtime_that_records_nothing_writes_null_and_never_invents(self):
        # RECORD.md:114 and :124. ChessLab retains no values and records no
        # implementation hash, so those fields are null and the value kind is
        # "omitted" with a note -- the fields are still present.
        _, chesslab = self.records["chesslab"]
        for tick in chesslab["ticks"]:
            for invocation in tick["invocations"]:
                self.assertIn("implementation_sha256", invocation["calculation"])
                self.assertEqual(invocation["value"]["kind"], "omitted")
                self.assertIsNone(invocation["value"]["data"])
                self.assertTrue(invocation["value"]["note"])
        # DiscStudio's runtime.js records no durations, and says so with null
        # rather than with a zero that would read as "instant".
        _, discstudio = self.records["discstudio-first"]
        for tick in discstudio["ticks"]:
            for invocation in tick["invocations"]:
                self.assertIsNone(invocation["duration_ms"])
        self.assertIsNone(discstudio["counters"]["wall_ms"])

    def test_the_javascript_pass_through_changes_no_field_of_the_python_record(self):
        # fromPytoRecord is a validating pass-through: the document that comes
        # back out of JavaScript is the document Python wrote, field for field.
        _, through_js = self.records["pyto"]
        self.assertEqual(through_js, load(REAL_RECORD))

    def test_the_round_trip_is_equal_as_JSON_and_not_promised_as_bytes(self):
        # An honest limit, pinned here so nobody keys a digest on the record
        # file: JSON has one number type, so an integral float inside a value
        # payload is written "0.0" by Python and "0" by JavaScript. RECORD.md:116
        # constrains key order and indentation, not the spelling of a number,
        # and the two documents are equal once parsed.
        entry, through_js = self.records["pyto"]
        self.assertEqual(through_js, load(REAL_RECORD), "equal as parsed JSON")
        emitted, original = read(entry["file"]), read(REAL_RECORD)
        self.assertEqual(emitted.splitlines()[0], original.splitlines()[0], "same sorted-key, 2-space shape")
        if emitted != original:
            differing = [
                (a, b) for a, b in zip(emitted.splitlines(), original.splitlines()) if a != b
            ]
            self.assertTrue(
                all(a.strip().rstrip(",") + ".0" == b.strip().rstrip(",") for a, b in differing),
                f"the only byte differences may be integral-float spelling, got {differing[:3]}",
            )


def javascript_verdicts(documents):
    """`adapters.js validate`'s verdict on each document: {ok, path}.

    The JavaScript reference reader is run as itself, in its own runtime, over
    exactly the bytes Python judged -- the only way the two readers can be said
    to agree about a record rather than about a description of one.
    """
    with tempfile.TemporaryDirectory(prefix="pyto-record-cases-") as tmp:
        cases_file = os.path.join(tmp, "cases.json")
        with open(cases_file, "w", newline="\n", encoding="utf-8") as handle:
            json.dump(documents, handle)
        result = subprocess.run(
            [NODE, os.path.join("test", "validate_cases.mjs"), cases_file],
            cwd=VIEWER, check=True, capture_output=True, text=True,
        )
    return json.loads(result.stdout)


def calculation(address):
    return {"address": address, "implementation_sha256": None, "identity_scope": "runtime-function-body"}


def multi_produce_record():
    """A record whose first invocation publishes two Parts from one pass.

    Written by hand from RECORD.md, not produced by `pyto.materialize`: this
    suite's whole point is that the contract is read independently of the runtime
    that writes it, and the multi-produce clauses (`into` may be an array, an
    `fn:` binding on such a producer carries the address) are read here the same
    way. The `parts` block is the answer `derive_part_index` has to reach.
    """
    return {
        "schema": SCHEMA,
        "pcr": "multi",
        "source": {"runtime": "pyto", "version": "0.1.0", "commit": None},
        "ticks": [
            {
                "index": 0,
                "name": "Prepare",
                "invocations": [
                    {
                        "id": "stats",
                        "calculation": calculation("fn.multi.stats"),
                        "inputs": {"rows": "px:in.rows"},
                        "args": {},
                        "into": ["out.mean", "out.count"],
                        "declared_consumes": ["px:in.rows"],
                        "actual_consumes": ["in.rows"],
                        "actual_produces": ["out.mean", "out.count"],
                        "writes": [
                            {"address": "out.mean", "kind": "new-address"},
                            {"address": "out.count", "kind": "new-address"},
                        ],
                        "duration_ms": 1.5,
                        "result_sha256": None,
                        "hit": True,
                        "value": {"kind": "json", "data": {"out.mean": 2.5, "out.count": 4}, "note": None},
                    }
                ],
            },
            {
                "index": 1,
                "name": "Report",
                "invocations": [
                    {
                        "id": "report",
                        "calculation": calculation("fn.multi.take"),
                        "inputs": {"value": "fn:stats#out.count"},
                        "args": {},
                        "into": "out.reported",
                        "declared_consumes": [],
                        "actual_consumes": [],
                        "actual_produces": ["out.reported"],
                        "writes": [{"address": "out.reported", "kind": "new-address"}],
                        "duration_ms": 0.5,
                        "result_sha256": None,
                        "hit": False,
                        "value": {"kind": "json", "data": 4, "note": None},
                    }
                ],
            },
        ],
        "parts": {
            "in.rows": {"written_by": None, "read_by": ["stats"], "preexisting": True},
            "out.mean": {"written_by": "stats", "read_by": [], "preexisting": False},
            "out.count": {"written_by": "stats", "read_by": ["report"], "preexisting": False},
            "out.reported": {"written_by": "report", "read_by": [], "preexisting": False},
        },
        "counters": {"invocations": 2, "hits": 1, "computed": 1, "wall_ms": 2.0},
    }


class MultiProduceRecords(unittest.TestCase):
    """RECORD.md: `into` may be an array, and an `fn:` binding on such a producer
    names the produce it reads (`fn:<id>#<address>`).

    The clauses are read here from RECORD.md, checked against the JavaScript
    reference reader in `TheTwoValidatorsAgree`, and produced by the kernel in
    `pyto/tests/test_multi_into.py`.
    """

    def setUp(self):
        self.record = multi_produce_record()

    def test_a_list_into_validates(self):
        """record_schema.py `_into`.

        Mutation: `_nullable_str(inv["into"], ...)` as before -- a legal
        multi-produce record is refused by the Python reader while the runtime that
        wrote it and the JavaScript reader both accept it.
        """
        self.assertIs(validate(self.record), self.record)

    def test_the_part_index_credits_the_named_produce_and_only_that_one(self):
        """record_schema.py `resolve_binding`: `fn:stats#out.count` is a read of
        out.count.

        Mutation: resolve an `fn:` binding to every address its producer published --
        out.mean gains a reader that no binding declares, which is the edge the
        node law and the loop law of `{?} ResultReadsAreReads` turn on.
        """
        self.assertEqual(
            normalized_parts(derive_part_index(self.record["ticks"])),
            normalized_parts(self.record["parts"]),
        )

    def test_resolve_binding_reads_both_spellings_and_prefers_a_known_id(self):
        produced_by = {"stats": ("out.mean", "out.count"), "odd#name": ("out.odd",)}
        self.assertEqual(resolve_binding("px:in.rows", produced_by), ("in.rows",))
        self.assertEqual(resolve_binding("fn:stats#out.count", produced_by), ("out.count",))
        # a bare reference to a producer of several is read as a read of all of them
        self.assertEqual(resolve_binding("fn:stats", produced_by), ("out.mean", "out.count"))
        # a known id wins over the `#` split, so an id carrying a `#` still resolves
        self.assertEqual(resolve_binding("fn:odd#name", produced_by), ("out.odd",))
        self.assertEqual(resolve_binding("fn:nobody#out.x", produced_by), ())

    def test_the_malformed_shapes_of_the_new_clauses_are_refused(self):
        for path, value, expected in [
            ("ticks.0.invocations.0.into", [], "ticks[0].invocations[0].into"),
            ("ticks.0.invocations.0.into", ["out.mean", "out.mean"], "ticks[0].invocations[0].into[1]"),
            ("ticks.0.invocations.0.into", ["out.mean", 7], "ticks[0].invocations[0].into[1]"),
            ("ticks.0.invocations.0.into", {"0": "out.mean"}, "ticks[0].invocations[0].into"),
            ("ticks.1.invocations.0.inputs.value", "fn:stats#", "ticks[1].invocations[0].inputs.value"),
            ("ticks.1.invocations.0.inputs.value", "fn:#out.count", "ticks[1].invocations[0].inputs.value"),
        ]:
            with self.subTest(value=value):
                with self.assertRaises(RecordSchemaError) as caught:
                    validate(set_at(self.record, path, value))
                self.assertEqual(caught.exception.path, expected, str(caught.exception))

    @needs_node
    def test_the_javascript_reader_agrees_on_all_of_it(self):
        """The contract is a contract only if both readers answer the same.

        `validate_cases.mjs` runs `adapters.js validate` over the accepted record
        and every refusal above, and reports the path each names.
        """
        documents = [self.record] + [
            set_at(self.record, path, value)
            for path, value, _ in [
                ("ticks.0.invocations.0.into", [], None),
                ("ticks.0.invocations.0.into", ["out.mean", "out.mean"], None),
                ("ticks.0.invocations.0.into", ["out.mean", 7], None),
                ("ticks.1.invocations.0.inputs.value", "fn:stats#", None),
                ("ticks.1.invocations.0.inputs.value", "fn:#out.count", None),
            ]
        ]
        verdicts = javascript_verdicts(documents)
        self.assertEqual(verdicts[0], {"ok": True, "path": None})
        for document, verdict in zip(documents[1:], verdicts[1:]):
            self.assertFalse(verdict["ok"], "JavaScript accepted a malformed multi-produce record")
            with self.assertRaises(RecordSchemaError) as caught:
                validate(document)
            self.assertEqual(verdict["path"], caught.exception.path)


class TheValidatorActuallyRejects(unittest.TestCase):
    """A validator that accepted everything would pass the suite above."""

    def setUp(self):
        self.record = load(REAL_RECORD)

    def assertRejects(self, record, expected_path):
        with self.assertRaises(RecordSchemaError) as caught:
            validate(record)
        self.assertEqual(caught.exception.path, expected_path, str(caught.exception))
        self.assertTrue(
            str(caught.exception).startswith(SCHEMA + " " + expected_path + ": "), str(caught.exception)
        )
        return caught.exception

    def test_the_unmutated_record_passes(self):
        self.assertIs(validate(self.record), self.record)

    def test_an_invented_field_is_rejected_wherever_it_appears(self):
        # "Missing fields are null, never invented" (RECORD.md:114) reads both
        # ways: a field RECORD.md does not define is the invention it forbids.
        for path, expected in [
            ("provenance", "document"),
            ("source.author", "source"),
            ("ticks.0.elapsed", "ticks[0]"),
            ("ticks.0.invocations.0.cost", "ticks[0].invocations[0]"),
            ("ticks.0.invocations.0.calculation.language", "ticks[0].invocations[0].calculation"),
            ("ticks.0.invocations.0.value.encoding", "ticks[0].invocations[0].value"),
            ("ticks.0.invocations.0.writes.0.when", "ticks[0].invocations[0].writes[0]"),
            ("counters.misses", "counters"),
        ]:
            with self.subTest(path=path):
                error = self.assertRejects(set_at(self.record, path, "invented"), expected)
                self.assertIn("unknown field", error.reason)

    def test_an_omitted_field_is_rejected_rather_than_read_as_null(self):
        for path, expected in [
            ("pcr", "document"),
            ("source.commit", "source"),
            ("ticks.0.name", "ticks[0]"),
            ("ticks.0.invocations.0.result_sha256", "ticks[0].invocations[0]"),
            ("ticks.0.invocations.0.calculation.implementation_sha256", "ticks[0].invocations[0].calculation"),
            ("ticks.0.invocations.0.value.note", "ticks[0].invocations[0].value"),
            ("counters.wall_ms", "counters"),
        ]:
            with self.subTest(path=path):
                error = self.assertRejects(set_at(self.record, path, None, delete=True), expected)
                self.assertIn("missing required field", error.reason)

    def test_every_typed_rule_of_RECORD_md_rejects_its_violation(self):
        cases = [
            ("schema", "pyto-run-record@2", "schema"),
            ("pcr", 42, "pcr"),
            ("source.runtime", "matlab", "source.runtime"),
            ("source.version", 7, "source.version"),
            ("ticks.0.index", 3, "ticks[0].index"),
            ("ticks.0.name", None, "ticks[0].name"),
            ("ticks.0.invocations.0.id", "", "ticks[0].invocations[0].id"),
            ("ticks.0.invocations.0.calculation.identity_scope", None,
             "ticks[0].invocations[0].calculation.identity_scope"),
            # the testimony spelling survives into the record (RECORD.md:80)
            ("ticks.0.invocations.0.inputs.groups", "input.ablation.groups",
             "ticks[0].invocations[0].inputs.groups"),
            ("ticks.0.invocations.0.declared_consumes.0", "input.ablation.groups",
             "ticks[0].invocations[0].declared_consumes[0]"),
            # declared_consumes is exactly the `px:` bindings of `inputs`
            # (RECORD.md:83-93) -- the rule that lets a reader trust `inputs`
            # alone (RECORD.md:94-100). Both halves are checked, and each case
            # isolates one: `fit.all` binds `split` as `fn:split`, so an
            # `fn:split` entry there IS in `inputs.values()` and only the
            # spelling rule refuses it; `px:scratch.ablation.not_bound` is
            # spelled right and only the subset rule refuses it.
            ("ticks.1.invocations.0.declared_consumes", ["fn:split"],
             "ticks[1].invocations[0].declared_consumes[0]"),
            ("ticks.0.invocations.0.declared_consumes.0", "px:scratch.ablation.not_bound",
             "ticks[0].invocations[0].declared_consumes[0]"),
            # actual_* are bare addresses, and an array of them (RECORD.md:101)
            ("ticks.0.invocations.0.actual_consumes", "input.ablation.groups",
             "ticks[0].invocations[0].actual_consumes"),
            ("ticks.0.invocations.0.actual_produces.0", 3, "ticks[0].invocations[0].actual_produces[0]"),
            ("ticks.0.invocations.0.writes.0.kind", "clobber", "ticks[0].invocations[0].writes[0].kind"),
            ("ticks.0.invocations.0.duration_ms", "fast", "ticks[0].invocations[0].duration_ms"),
        # RECORD.md, "Placement and budget": optional, but held to the same rules
        # as everything else once a record carries them (task 39).
        ("ticks.0.latency_ms", "fast", "ticks[0].latency_ms"),
        ("ticks.0.invocations.0.placement", {"worker": -1, "started_ms": 0.0},
         "ticks[0].invocations[0].placement.worker"),
        ("ticks.0.invocations.0.placement", {"worker": 0, "started_ms": "soon"},
         "ticks[0].invocations[0].placement.started_ms"),
        ("ticks.0.invocations.0.placement", {"worker": 0, "started_ms": 0.0, "thread": "main"},
         "ticks[0].invocations[0].placement"),
        ("parallel", "yes", "parallel"),
        ("budget", {"limit_ms": 250.0, "stopped_after_tick": None, "completed": "no"},
         "budget.completed"),
        ("budget", {"limit_ms": 250.0, "stopped_after_tick": "Prepare", "completed": True},
         "budget.stopped_after_tick"),
        ("budget", {"limit_ms": 250.0, "stopped_after_tick": "Nowhere", "completed": False},
         "budget.stopped_after_tick"),
        ("budget", {"limit_ms": 250.0, "completed": False}, "budget"),
            ("ticks.0.invocations.0.hit", "yes", "ticks[0].invocations[0].hit"),
            ("ticks.0.invocations.0.value.kind", "binary", "ticks[0].invocations[0].value.kind"),
            ("counters.invocations", 99, "counters.invocations"),
            ("counters.hits", 1, "counters.hits"),
            ("counters.computed", 1, "counters.computed"),
            ("counters.wall_ms", "quick", "counters.wall_ms"),
        ]
        for path, value, expected in cases:
            with self.subTest(path=path):
                self.assertRejects(set_at(self.record, path, value), expected)

    def test_a_boolean_is_not_an_integer_counter(self):
        # Python's bool is an int, so a validator that forgets that accepts
        # "hits": true on a record with one hit. This one does not.
        self.assertRejects(set_at(self.record, "counters.hits", True), "counters.hits")
        self.assertRejects(set_at(self.record, "ticks.0.index", False), "ticks[0].index")

    def test_the_value_kind_rules_of_RECORD_md_59_to_63(self):
        base = "ticks.0.invocations.0.value"
        # "omitted" has to say why (RECORD.md:112): a null note is not a reason.
        self.assertRejects(
            set_at(self.record, base, {"kind": "omitted", "data": None, "note": None}),
            "ticks[0].invocations[0].value.note",
        )
        self.assertRejects(
            set_at(self.record, base, {"kind": "omitted", "data": "x", "note": "why"}),
            "ticks[0].invocations[0].value.data",
        )
        self.assertRejects(
            set_at(self.record, base, {"kind": "svg", "data": 12, "note": None}),
            "ticks[0].invocations[0].value.data",
        )
        # RECORD.md:109-110 fixes the bytes of a png-data-url, because a viewer
        # makes them an <img src>. Anything else is refused; the real prefix passes.
        for data in ("https://evil.example/beacon.gif", "javascript:alert(1)//", "data:image/svg+xml,<svg/>", ""):
            with self.subTest(data=data):
                self.assertRejects(
                    set_at(self.record, base, {"kind": "png-data-url", "data": data, "note": None}),
                    "ticks[0].invocations[0].value.data",
                )
        good = set_at(self.record, base, {"kind": "png-data-url", "data": "data:image/png;base64,iVBORw0KGgo=", "note": None})
        self.assertIs(validate(good), good)
        # `json` accepts any JSON value, null included: the kind says how to
        # read `data`, not that the value was non-empty.
        ok = set_at(self.record, base, {"kind": "json", "data": None, "note": None})
        self.assertIs(validate(ok), ok)

    def test_a_duplicate_invocation_id_is_rejected_because_ids_anchor_annotations(self):
        error = self.assertRejects(
            set_at(self.record, "ticks.1.invocations.0.id", "split"), "ticks[1].invocations[0].id"
        )
        self.assertIn("duplicate invocation id", error.reason)

    def test_a_malformed_parts_entry_names_the_address(self):
        record = json.loads(json.dumps(self.record))
        record["parts"]["scratch.ablation.split"]["read_by"] = "split"
        self.assertRejects(record, 'parts["scratch.ablation.split"].read_by')

    def test_a_non_object_document_is_rejected(self):
        for document in (None, [], "record", 3):
            with self.subTest(document=document):
                self.assertRejects(document, "document")


class PlacementAndBudget(unittest.TestCase):
    """RECORD.md, "Placement and budget": optional, and read by both runtimes.

    Optional is the load-bearing word. A record that carries none of the four is
    a serial, unbudgeted run -- which is what every runtime but a parallel pyto
    writes, and what the committed Day 1 record is -- so the readers must answer
    the schedule question for a record that never heard of it.
    """

    def setUp(self):
        self.record = load(REAL_RECORD)

    def scheduled(self):
        """The committed record with a schedule bolted on, by hand, from RECORD.md."""
        record = json.loads(json.dumps(self.record))
        record["parallel"] = True
        record["budget"] = {
            "limit_ms": 250.0,
            "stopped_after_tick": record["ticks"][-1]["name"],
            "completed": False,
        }
        for index, tick in enumerate(record["ticks"]):
            tick["latency_ms"] = 1.5 + index
            for position, invocation in enumerate(tick["invocations"]):
                invocation["placement"] = {"worker": position % 2, "started_ms": position * 0.25}
        return record

    def test_the_committed_record_carries_none_of_the_four_and_reads_as_serial(self):
        self.assertNotIn("parallel", self.record)
        self.assertNotIn("budget", self.record)
        for tick in self.record["ticks"]:
            self.assertNotIn("latency_ms", tick)
            for invocation in tick["invocations"]:
                self.assertNotIn("placement", invocation)
        self.assertEqual(
            run_schedule(self.record),
            {"parallel": False,
             "budget": {"limit_ms": None, "stopped_after_tick": None, "completed": True}},
        )
        self.assertIsNone(invocation_placement(self.record["ticks"][0]["invocations"][0]))

    def test_an_absent_latency_is_the_sum_of_the_ticks_durations(self):
        for tick in self.record["ticks"]:
            self.assertAlmostEqual(
                tick_latency_ms(tick),
                sum(inv["duration_ms"] for inv in tick["invocations"]),
                places=9,
            )

    def test_a_null_latency_falls_back_the_same_way_a_missing_one_does(self):
        record = self.scheduled()
        record["ticks"][0]["latency_ms"] = None
        self.assertAlmostEqual(
            tick_latency_ms(record["ticks"][0]),
            sum(inv["duration_ms"] for inv in record["ticks"][0]["invocations"]),
            places=9,
        )

    def test_a_scheduled_record_validates_and_reads_back(self):
        record = self.scheduled()
        self.assertIs(validate(record), record)
        self.assertEqual(
            run_schedule(record),
            {"parallel": True,
             "budget": {"limit_ms": 250.0,
                        "stopped_after_tick": record["ticks"][-1]["name"],
                        "completed": False}},
        )
        self.assertEqual(tick_latency_ms(record["ticks"][0]), 1.5)
        self.assertEqual(
            invocation_placement(record["ticks"][0]["invocations"][0]),
            {"worker": 0, "started_ms": 0.0},
        )

    def test_a_null_placement_is_a_serial_invocation_not_a_violation(self):
        record = self.scheduled()
        record["ticks"][0]["invocations"][0]["placement"] = None
        self.assertIs(validate(record), record)
        self.assertIsNone(invocation_placement(record["ticks"][0]["invocations"][0]))

    @needs_node
    def test_javascript_accepts_the_scheduled_record_too(self):
        self.assertEqual(
            javascript_verdicts([self.record, self.scheduled()]),
            [{"ok": True, "path": None}, {"ok": True, "path": None}],
        )

    @needs_node
    def test_both_readers_expose_the_same_latency_placement_and_schedule(self):
        record = self.scheduled()
        with tempfile.TemporaryDirectory(prefix="pyto-schedule-") as tmp:
            path = os.path.join(tmp, "record.json")
            with open(path, "w", newline="\n", encoding="utf-8") as handle:
                json.dump(record, handle)
            snippet = (
                "import {readFileSync} from 'node:fs';"
                "import {runSchedule, tickLatencyMsFromRecord, invocationPlacement} from './adapters.js';"
                f"const record = JSON.parse(readFileSync({json.dumps(path)}, 'utf8'));"
                "process.stdout.write(JSON.stringify({"
                "schedule: runSchedule(record),"
                "latency: record.ticks.map(tickLatencyMsFromRecord),"
                "placement: record.ticks.map((t) => t.invocations.map(invocationPlacement))"
                "}));"
            )
            result = subprocess.run(
                [NODE, "--input-type=module", "-e", snippet],
                cwd=VIEWER, check=True, capture_output=True, text=True,
            )
        seen = json.loads(result.stdout)
        self.assertEqual(seen["schedule"], run_schedule(record))
        self.assertEqual(seen["latency"], [tick_latency_ms(tick) for tick in record["ticks"]])
        self.assertEqual(
            seen["placement"],
            [[invocation_placement(inv) for inv in tick["invocations"]] for tick in record["ticks"]],
        )

    @needs_node
    def test_both_readers_fall_back_to_the_sum_for_a_record_without_latency(self):
        with tempfile.TemporaryDirectory(prefix="pyto-schedule-") as tmp:
            path = os.path.join(tmp, "record.json")
            with open(path, "w", newline="\n", encoding="utf-8") as handle:
                json.dump(self.record, handle)
            snippet = (
                "import {readFileSync} from 'node:fs';"
                "import {runSchedule, tickLatencyMsFromRecord} from './adapters.js';"
                f"const record = JSON.parse(readFileSync({json.dumps(path)}, 'utf8'));"
                "process.stdout.write(JSON.stringify({"
                "schedule: runSchedule(record), latency: record.ticks.map(tickLatencyMsFromRecord)}));"
            )
            result = subprocess.run(
                [NODE, "--input-type=module", "-e", snippet],
                cwd=VIEWER, check=True, capture_output=True, text=True,
            )
        seen = json.loads(result.stdout)
        self.assertEqual(seen["schedule"], run_schedule(self.record))
        for js_latency, tick in zip(seen["latency"], self.record["ticks"]):
            self.assertAlmostEqual(js_latency, tick_latency_ms(tick), places=3)


class TheTwoValidatorsAgree(unittest.TestCase):
    """The same violation, refused by both runtimes, at the same path."""

    CASES = [
        ("schema", "pyto-run-record@2", "schema"),
        ("source.runtime", "matlab", "source.runtime"),
        ("ticks.0.index", 3, "ticks[0].index"),
        ("ticks.0.invocations.0.id", "", "ticks[0].invocations[0].id"),
        ("ticks.0.invocations.0.calculation.identity_scope", None,
         "ticks[0].invocations[0].calculation.identity_scope"),
        ("ticks.0.invocations.0.inputs.groups", "input.ablation.groups",
         "ticks[0].invocations[0].inputs.groups"),
        ("ticks.0.invocations.0.declared_consumes.0", "input.ablation.groups",
         "ticks[0].invocations[0].declared_consumes[0]"),
        # RECORD.md:83-93: declared_consumes is exactly the `px:` bindings of
        # `inputs`. Neither runtime may read back a record that declares a Part
        # read no binding carries -- before this was enforced, the fixture
        # `viewer/fixtures/pyto-value-kinds.json` shipped six `fn:` entries and
        # both validators accepted them. One case per half of the rule; see the
        # table in TheValidatorActuallyRejects for why `ticks[1]` isolates the
        # spelling half.
        ("ticks.1.invocations.0.declared_consumes", ["fn:split"],
         "ticks[1].invocations[0].declared_consumes[0]"),
        ("ticks.0.invocations.0.declared_consumes.0", "px:scratch.ablation.not_bound",
         "ticks[0].invocations[0].declared_consumes[0]"),
        ("ticks.0.invocations.0.actual_consumes", "input.ablation.groups",
         "ticks[0].invocations[0].actual_consumes"),
        ("ticks.0.invocations.0.writes.0.kind", "clobber", "ticks[0].invocations[0].writes[0].kind"),
        ("ticks.0.invocations.0.duration_ms", "fast", "ticks[0].invocations[0].duration_ms"),
        ("ticks.0.invocations.0.hit", "yes", "ticks[0].invocations[0].hit"),
        ("ticks.0.invocations.0.value.kind", "binary", "ticks[0].invocations[0].value.kind"),
        # RECORD.md:109-110 states a shape, not just a name: a viewer puts this
        # string into an <img src>, so neither runtime may read back a record
        # that spells an arbitrary URL there.
        ("ticks.0.invocations.0.value",
         {"kind": "png-data-url", "data": "https://evil.example/beacon.gif", "note": None},
         "ticks[0].invocations[0].value.data"),
        ("counters.invocations", 99, "counters.invocations"),
        ("counters.hits", 1, "counters.hits"),
        ("counters.wall_ms", "quick", "counters.wall_ms"),
    ]

    def setUp(self):
        if NODE is None:
            self.skipTest("node is not on PATH")
        self.record = load(REAL_RECORD)

    def javascript_verdicts(self, documents):
        return javascript_verdicts(documents)

    def test_javascript_accepts_the_record_python_accepts(self):
        self.assertIs(validate(self.record), self.record)
        self.assertEqual(self.javascript_verdicts([self.record]), [{"ok": True, "path": None}])

    def test_javascript_refuses_what_python_refuses_and_names_the_same_path(self):
        documents = [set_at(self.record, path, value) for path, value, _ in self.CASES]
        verdicts = self.javascript_verdicts(documents)
        self.assertEqual(len(verdicts), len(self.CASES))
        for (path, _value, expected), verdict, document in zip(self.CASES, verdicts, documents):
            with self.subTest(path=path):
                self.assertFalse(verdict["ok"], "JavaScript accepted " + path)
                self.assertEqual(verdict["path"], expected, "JavaScript names a different path")
                with self.assertRaises(RecordSchemaError) as caught:
                    validate(document)
                self.assertEqual(caught.exception.path, expected, "Python names a different path")

    def test_python_is_the_stricter_reader_only_where_RECORD_md_says_so(self):
        # Python rejects an invented or missing key; adapters.js reads the keys
        # it needs and lets an extra one through. Both readings are recorded
        # here so the difference is a known one, not a surprise: a record that
        # only JavaScript has seen can still carry a field RECORD.md does not
        # define, and this suite is where that is caught.
        invented = set_at(self.record, "counters.misses", 3)
        with self.assertRaises(RecordSchemaError):
            validate(invented)
        self.assertEqual(self.javascript_verdicts([invented])[0]["ok"], True)


if __name__ == "__main__":
    unittest.main()


class EffectsLedger(unittest.TestCase):
    """RECORD.md, "Effects": optional like placement, and exact once it is there.

    The record read here is what `pyto.materialize.run_record` actually wrote for
    a run with an `oc.` Calculation in it, so this is the independent reader
    checking the producer, which is the whole reason this file is not
    `from pyto.materialize import ...`.
    """

    def setUp(self):
        self.record = load(EFFECTS_RECORD)

    def assertRejects(self, record, expected_path):
        with self.assertRaises(RecordSchemaError) as caught:
            validate(record)
        self.assertEqual(caught.exception.path, expected_path, str(caught.exception))
        return caught.exception

    def test_the_producers_record_validates_and_carries_one_ledger_per_invocation(self):
        self.assertIs(validate(self.record), self.record)
        stamp, summary = (
            self.record["ticks"][0]["invocations"][0],
            self.record["ticks"][1]["invocations"][0],
        )
        self.assertEqual(
            [entry["kind"] for entry in invocation_effects(stamp)],
            ["write_text", "now_ms", "random_seed", "random", "random"],
        )
        # Present for every invocation of a record that carries the field, and
        # empty for the pure one: "this invocation performed no effect" is a
        # different claim from "this runtime records none".
        self.assertEqual(invocation_effects(summary), [])
        self.assertEqual(summary["effects"], [])

    def test_a_record_that_carries_no_effects_reads_as_a_run_that_performed_none(self):
        """The optional half: the committed Day 1 record never heard of an `oc.`."""
        record = load(REAL_RECORD)
        for tick in record["ticks"]:
            for invocation in tick["invocations"]:
                self.assertNotIn("effects", invocation)
                self.assertEqual(invocation_effects(invocation), [])
        self.assertIs(validate(record), record)

    def test_the_shape_of_an_entry_is_exact(self):
        base = "ticks.0.invocations.0.effects.0"
        where = "ticks[0].invocations[0].effects[0]"
        for path, value, expected in [
            (base + ".kind", "spawn", where + ".kind"),
            (base + ".args", "out/note.txt", where + ".args"),
            (base + ".result_sha256", None, where + ".result_sha256"),
            (base, {"kind": "now_ms", "args": {}, "result": 1.0,
                    "result_sha256": "a" * 64, "actor": "root"}, where),
            (base, {"kind": "now_ms", "args": {}, "result": 1.0}, where),
            # A write keeps its text as a digest alone: `result` is null.
            (base + ".result", "the text", where + ".result"),
            # Paths are relative to the run's effects_root and never absolute.
            (base + ".args.path", "/etc/passwd", where + ".args.path"),
            (base + ".args.path", "../../etc/passwd", where + ".args.path"),
            (base + ".args", {}, where + ".args"),
            ("ticks.0.invocations.0.effects", {"0": "write_text"},
             "ticks[0].invocations[0].effects"),
        ]:
            with self.subTest(path=path):
                self.assertRejects(set_at(self.record, path, value), expected)

    def test_every_kind_the_format_declares_is_accepted(self):
        record = json.loads(json.dumps(self.record))
        record["ticks"][0]["invocations"][0]["effects"] = [
            {"kind": "read_text", "args": {"path": "in/a.txt"}, "result": "a",
             "result_sha256": "0" * 64},
            {"kind": "env", "args": {"name": "PATH"}, "result": None, "result_sha256": "1" * 64},
            {"kind": "random_seed", "args": {}, "result": 7, "result_sha256": "2" * 64},
        ]
        self.assertIs(validate(record), record)
