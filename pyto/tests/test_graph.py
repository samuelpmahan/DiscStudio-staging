import unittest

from pyto import Pcr


class PcrGraphTest(unittest.TestCase):
    def test_direct_result_and_publication_shape(self):
        pcr = Pcr("S0")
        source = pcr.part("px.source.selectedInput")
        decode = pcr.calc("Decode", "fn.s0.decodeFullImage", id="decode", source=source)
        pcr.calc("Crop", "fn.s0.findChromeBounds", id="bounds", image=decode, into="px.source.cropBounds")

        # Deliberately consume the published Part rather than keeping the ValueRef.
        # The graph should still encode a direct function-result dependency, matching
        # the Mermaid compiler's current semantics.
        pcr.calc(
            "Crop",
            "fn.s0.applyCrop",
            id="crop",
            image=decode,
            bounds=pcr.part("px.source.cropBounds"),
            into="px.course.canonicalPixels",
        )

        root = pcr.to_pcr_dict()
        crop = root["Ticks"][1]["Calculations"][1]
        self.assertEqual(crop["with"]["image"], {"kind": "fn", "ref": "decode"})
        self.assertEqual(crop["with"]["bounds"], {"kind": "fn", "ref": "bounds"})
        self.assertEqual(crop["into"], "px.course.canonicalPixels")

    def test_rejects_duplicate_writer(self):
        pcr = Pcr("dupe")
        source = pcr.part("px.source")
        pcr.calc("A", "fn.a", id="a", source=source, into="px.out")
        with self.assertRaisesRegex(ValueError, "multiple writers"):
            pcr.calc("B", "fn.b", id="b", source=source, into="px.out")

    def test_mermaid_is_a_view_of_same_graph(self):
        pcr = Pcr("tiny")
        pcr.calc("Tick1", "fn.example", id="example", source=pcr.part("px.in"), into="px.out")
        mermaid = pcr.to_mermaid()
        self.assertIn('subgraph PCR["PCR: tiny"]', mermaid)
        self.assertIn('subgraph Tick_Tick1["Tick: Tick1"]', mermaid)
        self.assertIn('example["fn.example"]', mermaid)
        self.assertIn('p0 -->|source| example', mermaid)
        self.assertIn('example --> p1', mermaid)

    def test_a_calculation_that_publishes_several_parts(self):
        """graph.py reads every produce address, not one `into.address`.

        A Calculation may publish several Parts from one pass ({?} WhatIsATick,
        owner 2026-09-10), so `into=[a, b]` is emitted as an array, both addresses
        get a writer and a Mermaid node, and a binding on one of them names which
        produce it read (`<id>#<address>`, the RECORD.md spelling without the `fn:`
        prefix the `kind` field already carries).

        Mutation: `item["into"] = calc.into.address` and `part_id(calc.into.address)`
        as before -- every assertion below raises AttributeError on a tuple, which is
        the crash this test exists to prevent.
        """
        pcr = Pcr("multi")
        pcr.calc(
            "Prepare", "fn.multi.stats", id="stats",
            rows=pcr.part("px.in.rows"), into=["px.out.mean", "px.out.count"],
        )
        pcr.calc("Report", "fn.multi.take", id="report", value=pcr.part("px.out.count"), into="px.out.reported")

        root = pcr.to_pcr_dict()
        stats = root["Ticks"][0]["Calculations"][0]
        self.assertEqual(stats["into"], ["px.out.mean", "px.out.count"])
        report = root["Ticks"][1]["Calculations"][0]
        self.assertEqual(report["with"]["value"], {"kind": "fn", "ref": "stats#px.out.count"})
        self.assertEqual(report["into"], "px.out.reported")

        mermaid = pcr.to_mermaid()
        for address in ("px.out.mean", "px.out.count", "px.out.reported"):
            self.assertIn(f'["{address}"]', mermaid)
        self.assertEqual(mermaid.count("    stats --> p"), 2)

        # the writer rule is per address, so it holds across the list
        with self.assertRaisesRegex(ValueError, "multiple writers for px.out.mean"):
            pcr.calc("Prepare", "fn.other", id="other", into="px.out.mean")

    def test_one_address_calls_are_unchanged_by_multi_produce(self):
        """The compatibility half: one address is still a bare string in the emitted
        document and a bare `<id>` in a result binding.
        """
        pcr = Pcr("single")
        pcr.calc("T", "fn.a", id="a", source=pcr.part("px.in"), into="px.mid")
        pcr.calc("T", "fn.b", id="b", mid=pcr.part("px.mid"), into="px.out")
        root = pcr.to_pcr_dict()
        self.assertEqual(root["Ticks"][0]["Calculations"][0]["into"], "px.mid")
        self.assertEqual(root["Ticks"][0]["Calculations"][1]["with"]["mid"], {"kind": "fn", "ref": "a"})


if __name__ == "__main__":
    unittest.main()
