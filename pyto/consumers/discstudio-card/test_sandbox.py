import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parent


class SandboxTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=ROOT / "data")
        self.root = Path(self.tmp.name)
        (self.root / "data" / "recipes").mkdir(parents=True)
        (self.root / "index.html").write_text("<h1>test</h1>", encoding="utf-8")
        env = os.environ.copy()
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        env["TMPDIR"] = str(ROOT / "data")
        self.proc = subprocess.Popen(
            [sys.executable, str(ROOT / "app.py"), "--host", "127.0.0.1", "--port", "0", "--root", str(self.root)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env,
        )
        line = self.proc.stdout.readline().strip()
        self.assertTrue(line.startswith("READY http://127.0.0.1:"), line)
        self.base = line.removeprefix("READY ").removesuffix("/")

    def tearDown(self):
        self.proc.terminate()
        self.proc.wait(timeout=3)
        for stream in (self.proc.stdout, self.proc.stderr):
            if stream:
                stream.close()
        self.tmp.cleanup()

    def request(self, method, path, value=None, headers=None):
        data = None if value is None else json.dumps(value).encode()
        req = urllib.request.Request(self.base + path, data=data, method=method, headers=headers or {})
        if data is not None:
            req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=3) as response:
                body = response.read()
                return response.status, json.loads(body) if response.headers.get_content_type() == "application/json" else body.decode()
        except urllib.error.HTTPError as error:
            body = error.read()
            error.close()
            try:
                value = json.loads(body)
            except json.JSONDecodeError:
                value = body.decode(errors="replace")
            return error.code, value

    def test_health_recipe_event_and_reload(self):
        self.assertEqual(self.request("GET", "/api/health"), (200, {"ok": True}))
        status, saved = self.request("POST", "/api/recipes", {"recipe": {"steps": ["measure", "mix"]}})
        self.assertEqual(status, 201)
        self.assertEqual(saved["recipe"]["steps"], ["measure", "mix"])
        self.assertTrue((self.root / "data" / "recipes" / (saved["id"] + ".json")).exists())
        status, event = self.request("POST", "/api/events", {"kind": "probe", "value": 3})
        self.assertEqual(status, 201)
        self.assertIn("timestamp", event)
        self.assertEqual(len((self.root / "data" / "events.jsonl").read_text().splitlines()), 1)
        self.proc.terminate()
        self.proc.wait(timeout=3)
        for stream in (self.proc.stdout, self.proc.stderr):
            if stream:
                stream.close()
        env = os.environ.copy()
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        self.proc = subprocess.Popen([sys.executable, str(ROOT / "app.py"), "--port", "0", "--root", str(self.root)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)
        line = self.proc.stdout.readline().strip()
        self.base = line.removeprefix("READY ").removesuffix("/")
        status, recipes = self.request("GET", "/api/recipes")
        self.assertEqual(status, 200)
        self.assertEqual(recipes, [saved])

    def test_rejects_bad_input_origin_and_traversal(self):
        self.assertEqual(self.request("POST", "/api/events", ["array"])[0], 400)
        self.assertEqual(self.request("POST", "/api/recipes", {"recipe": []})[0], 400)
        self.assertEqual(self.request("POST", "/api/events", {"x": 1}, {"Host": "evil.example"})[0], 403)
        self.assertEqual(self.request("GET", "/../data/events.jsonl")[0], 404)
        huge = {"x": "a" * (256 * 1024)}
        self.assertEqual(self.request("POST", "/api/events", huge)[0], 413)

    def test_root_only_serves_index(self):
        status, body = self.request("GET", "/")
        self.assertEqual((status, body), (200, "<h1>test</h1>"))


if __name__ == "__main__":
    unittest.main()
