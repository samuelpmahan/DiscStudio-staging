import json
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from test_sandbox import SandboxTest


class ArtBackendTest(SandboxTest):
    def test_art_replay_receipt_and_no_mutation_on_invalid(self):
        request = {"family": "Orbit Foundry", "seed": 202, "base": "#4c9bc6", "accent": "#0d3558", "targetPx": 42, "label": "Mako3", "version": "components-v2"}
        status, first = self.request("POST", "/api/art", request)
        self.assertEqual(status, 200)
        status, second = self.request("POST", "/api/art", request)
        self.assertEqual(status, 200)
        self.assertEqual(first, second)
        self.assertEqual(first["receipt"]["targetPx"], 42)
        self.assertIn('id="rim"', first["svg"])
        self.assertNotIn('id="text"', first["svg"])
        upper = {**request, "base": "#4C9BC6", "accent": "#0D3558"}
        self.assertEqual(self.request("POST", "/api/art", upper)[1], first)
        events_before = (self.root / "data" / "events.jsonl").exists()
        recipes_before = sorted((self.root / "data" / "recipes").glob("*.json"))
        self.assertEqual(self.request("POST", "/api/art", {**request, "targetPx": 43})[0], 400)
        self.assertEqual((self.root / "data" / "events.jsonl").exists(), events_before)
        self.assertEqual(sorted((self.root / "data" / "recipes").glob("*.json")), recipes_before)

    def test_concurrent_events_are_complete_json_lines(self):
        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(lambda i: self.request("POST", "/api/events", {"kind": "parallel", "i": i})[0], range(24)))
        self.assertEqual(results, [201] * 24)
        lines = (self.root / "data" / "events.jsonl").read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 24)
        self.assertEqual({json.loads(line)["event"]["i"] for line in lines}, set(range(24)))


if __name__ == "__main__":
    unittest.main()
