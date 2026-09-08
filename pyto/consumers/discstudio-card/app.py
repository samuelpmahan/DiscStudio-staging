#!/usr/bin/env python3
"""Tiny, deterministic HTTP backend for the disc-studio sandbox."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import uuid
import hashlib
import threading
import importlib
import inspect
from dataclasses import asdict
from importlib.metadata import version as package_version
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from paint_components import FAMILIES, TARGETS, render as render_art
from pyto import Calculation, PCR, Part, PxC
from card_composition import canonical_bytes, execute_card, normalize_recipe


def normalize_for_receipt(recipe: dict[str, object]) -> dict[str, object]:
    """Receipt input is canonical and stable across JSON key order."""
    return normalize_recipe(recipe)

PAINTER_SOURCE_SHA256 = hashlib.sha256(Path(__file__).with_name("paint_components.py").read_bytes()).hexdigest()
PYTO_SOURCE_SHA256 = {
    module: hashlib.sha256(Path(inspect.getsourcefile(importlib.import_module(module)) or "").read_bytes()).hexdigest()
    for module in ("pyto.core", "pyto.pcr")
}
APP_SOURCE_SHA256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def render_art_via_pyto(payload: dict[str, object]) -> tuple[str, dict[str, object]]:
    request = Part("px.disc.art.request")
    output = Part("px.disc.art.svg")
    pxc = PxC()
    pxc.set(request, payload)
    calculation = Calculation("fn.discArt.render", lambda args: render_art(
        args["value"]["family"], args["value"]["seed"], args["value"]["base"],
        args["value"]["accent"], args["value"]["targetPx"], args["value"]["label"]))
    pcr = PCR("disc-art-render")
    pcr.calc("render", calculation, id="render-art", value=request, into=output)
    run = pcr.run(pxc)
    return pxc.get(output), {
        "pyto": {"package": "pyto-lab", "version": package_version("pyto-lab"), "moduleSourceSha256": PYTO_SOURCE_SHA256},
        "composition": {"pcr": run.pcr, "ticks": [asdict(tick) for tick in run.ticks], "adapterSourceSha256": APP_SOURCE_SHA256},
    }

MAX_BODY = 256 * 1024
LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1"}
HOST_RE = re.compile(r"^\[?([^\]:]+|::1)\]?(?::\d+)?$")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def json_bytes(value: object) -> bytes:
    return json.dumps(value, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


class SandboxHandler(BaseHTTPRequestHandler):
    server_version = "DiscStudioSandbox/1.0"

    @property
    def root(self) -> Path:
        return self.server.root  # type: ignore[attr-defined]

    def send_json(self, status: int, value: object) -> None:
        body = json_bytes(value)
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path == "/api/health":
            self.send_json(200, {"ok": True})
            return
        if self.path == "/api/recipes":
            recipes_dir = self.root / "data" / "recipes"
            recipes = []
            for path in sorted(recipes_dir.glob("*.json")):
                try:
                    value = json.loads(path.read_text(encoding="utf-8"))
                    recipes.append(value)
                except (OSError, ValueError):
                    continue
            self.send_json(200, recipes)
            return
        if self.path == "/":
            index = self.root / "index.html"
            try:
                body = index.read_bytes()
            except OSError:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_error(404)

    def do_POST(self) -> None:
        if not self.local_request():
            self.send_json(403, {"error": "local origin required"})
            return
        if self.path not in {"/api/events", "/api/recipes", "/api/art", "/api/cards"}:
            self.send_error(404)
            return
        length = self.headers.get("Content-Length")
        try:
            size = int(length) if length is not None else -1
        except ValueError:
            size = -1
        if size < 0 or size > MAX_BODY:
            self.send_json(413, {"error": "request body exceeds 256KB limit"})
            return
        try:
            payload = json.loads(self.rfile.read(size).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self.send_json(400, {"error": "invalid JSON"})
            return
        if not isinstance(payload, dict):
            self.send_json(400, {"error": "JSON object required"})
            return
        if self.path == "/api/events":
            record = {"timestamp": utc_now(), "event": payload}
            events = self.root / "data" / "events.jsonl"
            events.parent.mkdir(parents=True, exist_ok=True)
            with self.server.write_lock:  # type: ignore[attr-defined]
                with events.open("a", encoding="utf-8") as stream:
                    stream.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
            self.send_json(201, record)
            return
        if self.path == "/api/art":
            try:
                family = payload["family"]
                seed = payload["seed"]
                base = payload["base"]
                accent = payload["accent"]
                target_px = payload["targetPx"]
                label = payload.get("label", "painted disc")
                version = payload.get("version", "components-v2")
                if (version != "components-v2" or family not in FAMILIES or
                        type(seed) is not int or type(target_px) is not int or target_px not in TARGETS or
                        not isinstance(base, str) or not isinstance(accent, str) or
                        not isinstance(label, str) or len(label) > 120 or
                        not re.fullmatch(r"#[0-9a-fA-F]{6}", base) or not re.fullmatch(r"#[0-9a-fA-F]{6}", accent)):
                    raise ValueError
                base, accent = base.lower(), accent.lower()
                art_payload = {"family": family, "seed": seed, "base": base, "accent": accent, "targetPx": target_px, "label": label}
                svg, composition_evidence = render_art_via_pyto(art_payload)
            except (KeyError, TypeError, ValueError):
                self.send_json(400, {"error": "invalid art request"})
                return
            input_bytes = json_bytes({"family": family, "seed": seed, "base": base.lower(), "accent": accent.lower(), "targetPx": target_px, "label": label, "version": version})
            receipt = {"generatorVersion": version, "sourceSha256": PAINTER_SOURCE_SHA256, "inputSha256": hashlib.sha256(input_bytes).hexdigest(), "outputSha256": hashlib.sha256(svg.encode()).hexdigest(), "targetPx": target_px, "family": family, "seed": seed}
            receipt["compositionEvidence"] = composition_evidence
            self.send_json(200, {"svg": svg, "receipt": receipt})
            return
        if self.path == "/api/cards":
            try:
                recipe = payload.get("recipe", payload)
                composition, evidence = execute_card(recipe)
            except (KeyError, TypeError, ValueError):
                self.send_json(400, {"error": "invalid card request"})
                return
            canonical = json_bytes(composition)
            receipt = {"inputSha256": hashlib.sha256(canonical_bytes(normalize_for_receipt(recipe))).hexdigest(),
                       "outputSha256": hashlib.sha256(canonical).hexdigest(),
                       "theme": composition["theme"], "compositionEvidence": evidence}
            self.send_json(200, {"composition": composition, "receipt": receipt})
            return
        recipe = payload.get("recipe")
        if not isinstance(recipe, dict):
            self.send_json(400, {"error": "recipe object required"})
            return
        recipe_id = str(uuid.uuid4())
        saved = {"id": recipe_id, "recipe": recipe}
        target = self.root / "data" / "recipes" / f"{recipe_id}.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        with self.server.write_lock:  # type: ignore[attr-defined]
            with target.open("x", encoding="utf-8") as stream:
                stream.write(json.dumps(saved, ensure_ascii=False, indent=2) + "\n")
        self.send_json(201, saved)

    def local_request(self) -> bool:
        host = self.headers.get("Host", "")
        match = HOST_RE.fullmatch(host)
        if not match or match.group(1).lower() not in LOCAL_HOSTS:
            return False
        origin = self.headers.get("Origin")
        if not origin:
            return True
        parsed = urlparse(origin)
        return parsed.scheme == "http" and parsed.hostname in LOCAL_HOSTS

    def log_message(self, fmt: str, *args: object) -> None:
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))


def make_server(root: Path, host: str, port: int) -> ThreadingHTTPServer:
    root = root.resolve()
    (root / "data" / "recipes").mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer((host, port), SandboxHandler)
    server.root = root  # type: ignore[attr-defined]
    server.write_lock = threading.Lock()  # type: ignore[attr-defined]
    return server


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    server = make_server(args.root, args.host, args.port)
    print(f"READY http://{args.host}:{server.server_port}/", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
