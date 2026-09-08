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


if __name__ == "__main__":
    unittest.main()
