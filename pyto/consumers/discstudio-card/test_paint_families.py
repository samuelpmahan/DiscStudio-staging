"""Guards for the disc-art families after the art-tournament promotion.

Two jobs:

  * the four original families must render byte-for-byte as they did before
    ``paint_families`` existed -- the sha256 table below was recorded against
    the pre-promotion ``paint_components.py`` and is the freeze;
  * the three promoted families (pressed-fern, nodding-seedhead, wind-rose)
    must be deterministic, lint-clean at every target, and visually distinct
    from each other and from the originals at the 42px bag-card tier.

The lint checks mirror ``experiments/art-tournament/harness/lint_svg.py``.
They are restated here rather than imported so the consumer's suite does not
reach outside its own directory to test itself; the two were verified to agree
over every family x target x palette at promotion time.
"""

import hashlib
import os
import re
import subprocess
import sys
import unittest
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import paint_components
import paint_families

# sha256 of paint_components.render(family, 7, "#4c9bc6", "#0d3558", target,
# "warm mako"), recorded BEFORE paint_families was wired in. Any change to
# these bytes is a regression, not a redesign.
FROZEN_CLASSIC = {
    ("Orbit Foundry", 42): "94b54d6f2d8916a1d7d4d0fdcb554d1d3db5559accef62cebcf8e5845ff448f4",
    ("Orbit Foundry", 96): "286f22c9d33b0a5a88f4b406ab361101adf51c2a805ea7e9dfc1cda88c225f30",
    ("Orbit Foundry", 220): "7ae23c2066df2c06a19a001734a686f0a5afd1d86975d1bed7a59eba825aa365",
    ("Petal Press", 42): "205f3e6cffe09c653e1c4f12f7400610634bbbb453b0646047820082d8c21fb0",
    ("Petal Press", 96): "bbe4abf62587c2d93b515229f7b5022e765980140141ecfe859fe86e2489fd32",
    ("Petal Press", 220): "b2e067e97cd72abcd60f12691c0063453e66cd482f853c774fc3d5d360d42a34",
    ("Signal Stamp", 42): "3c13324f2a934f91c3b9a5d7a67372ce3ed9e149a4db929b37ce68d6a5ab38d2",
    ("Signal Stamp", 96): "42840ed7d36ce6fa04ec60d6831ed620a95c310cb10113c287e9ea1d00ee485b",
    ("Signal Stamp", 220): "ea1d8d6476da27577cc1081b4ea95781fd5e563e59be8070f809cc1f6b62e198",
    ("Tessellated Flight", 42): "5f6caf53873aad501526ef5d7147949f24ff8e8f1251e66fac477ec861b52423",
    ("Tessellated Flight", 96): "f430697722fc6944de9658bd7a29b85a9e6b50e6fdc94a9ba43984ab3963c649",
    ("Tessellated Flight", 220): "c22c1af5550bbcb336ee10679b48242df8c29f472ca14fd630bb821ddc1805ba",
}

COOL = ("#4c9bc6", "#0d3558")
PALETTES = {"cool": COOL, "warm": ("#f2c14e", "#1b1b1b"), "dark": ("#101318", "#ffd166")}
SEEDS = (0, 3, 7, 42, 2024)
LABEL = "warm mako"
CHROMIUM = "/opt/pw-browsers/chromium"

MAX_BYTES = 64 * 1024
SVG_NS = "http://www.w3.org/2000/svg"
_URL_FN = re.compile(r"url\s*\(", re.IGNORECASE)
_FONT_FACE = re.compile(r"@font-face", re.IGNORECASE)


def _local(tag):
    return tag.split("}", 1)[1] if "}" in tag else tag


def lint(text):
    """Return a list of hygiene failures; empty means clean."""
    failures = []
    data = text.encode("utf-8")
    if len(data) > MAX_BYTES:
        failures.append("size %dB exceeds %dB cap" % (len(data), MAX_BYTES))
    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        return failures + ["not well-formed XML: %s" % exc]
    if _local(root.tag) != "svg":
        failures.append("root element is <%s>, not <svg>" % _local(root.tag))
    if not root.tag.startswith("{" + SVG_NS + "}"):
        failures.append("root <svg> is missing the SVG xmlns")
    if "viewBox" not in root.attrib:
        failures.append("root <svg> is missing a viewBox")
    for elem in root.iter():
        if _local(elem.tag) == "image":
            failures.append("contains a forbidden <image> element")
        for name, value in elem.attrib.items():
            if _local(name) == "href" and not value.startswith("#"):
                failures.append("forbidden external/data href: %r" % value[:60])
    if _FONT_FACE.search(text):
        failures.append("contains @font-face")
    for match in _URL_FN.finditer(text):
        tail = text[match.end():match.end() + 40].lstrip()
        if not tail.startswith(("#", "'#", '"#')):
            failures.append("forbidden url(...) near byte %d" % match.start())
    return failures


class ClassicFamiliesAreFrozenTest(unittest.TestCase):
    def test_every_original_family_and_target_matches_its_recorded_hash(self):
        self.assertEqual(paint_components.CLASSIC_FAMILIES,
                         ("Orbit Foundry", "Petal Press", "Signal Stamp", "Tessellated Flight"))
        for (family, target), expected in sorted(FROZEN_CLASSIC.items()):
            with self.subTest(family=family, target=target):
                svg = paint_components.render(family, 7, COOL[0], COOL[1], target, LABEL)
                self.assertEqual(hashlib.sha256(svg.encode("utf-8")).hexdigest(), expected)

    def test_promotion_only_appended_to_the_family_list(self):
        self.assertEqual(paint_components.FAMILIES,
                         paint_components.CLASSIC_FAMILIES + paint_components.PROMOTED_FAMILIES)
        self.assertEqual(paint_components.PROMOTED_FAMILIES,
                         ("pressed-fern", "nodding-seedhead", "wind-rose"))
        self.assertFalse(set(paint_components.CLASSIC_FAMILIES) & set(paint_components.PROMOTED_FAMILIES))


class PromotedFamiliesTest(unittest.TestCase):
    def test_render_is_deterministic_within_and_across_processes(self):
        wanted = []
        digest = hashlib.sha256()
        for family in paint_families.FAMILIES:
            for seed in SEEDS:
                for base, accent in PALETTES.values():
                    for target in paint_components.TARGETS:
                        first = paint_components.render(family, seed, base, accent, target, LABEL)
                        second = paint_components.render(family, seed, base, accent, target, LABEL)
                        self.assertEqual(first, second, "%s/%s/%s is not stable" % (family, seed, target))
                        digest.update(first.encode("utf-8"))
                        wanted.append(family)
        self.assertEqual(len(wanted), 3 * len(SEEDS) * len(PALETTES) * len(paint_components.TARGETS))
        script = (
            "import hashlib, sys; sys.path.insert(0, %r); import paint_components as pc, paint_families as pf;"
            "d = hashlib.sha256();"
            "[d.update(pc.render(f, s, b, a, t, %r).encode()) for f in pf.FAMILIES for s in %r"
            " for b, a in %r for t in pc.TARGETS];"
            "print(d.hexdigest())"
        ) % (os.path.dirname(os.path.abspath(__file__)), LABEL, SEEDS, tuple(PALETTES.values()))
        env = dict(os.environ, PYTHONHASHSEED="1", PYTHONDONTWRITEBYTECODE="1")
        out = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, env=env, timeout=120)
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(out.stdout.strip(), digest.hexdigest())

    def test_every_family_and_target_is_lint_clean(self):
        for family in paint_components.FAMILIES:
            for target in paint_components.TARGETS:
                for name, (base, accent) in PALETTES.items():
                    svg = paint_components.render(family, 7, base, accent, target, LABEL)
                    with self.subTest(family=family, target=target, palette=name):
                        self.assertEqual(lint(svg), [])

    def test_document_contract_holds_at_every_target(self):
        for family in paint_families.FAMILIES:
            for target in paint_components.TARGETS:
                svg = paint_components.render(family, 11, COOL[0], COOL[1], target, "Warm Mako")
                with self.subTest(family=family, target=target):
                    root = ET.fromstring(svg)
                    self.assertEqual(root.attrib["viewBox"], "0 0 512 512")
                    self.assertEqual(root.attrib["width"], str(target))
                    self.assertEqual(root.attrib["height"], str(target))
                    self.assertTrue(root.attrib.get("aria-label"))
                    self.assertTrue(root.findall("{%s}title" % SVG_NS))
                    texts = root.iter("{%s}text" % SVG_NS)
                    self.assertEqual(bool(list(texts)), target == 220,
                                     "label text must appear only at 220")

    def test_unknown_family_is_rejected(self):
        with self.assertRaises(ValueError):
            paint_components.render("no-such-family", 1, COOL[0], COOL[1], 42, LABEL)
        with self.assertRaises(ValueError):
            paint_families.render("Orbit Foundry", 1, COOL[0], COOL[1], 42, LABEL)

    def test_reuse_surface_is_registrable(self):
        self.assertEqual(sorted(paint_families.FAMILY_PARAMS), sorted(paint_families.FAMILIES))
        for slug, params in paint_families.FAMILY_PARAMS.items():
            with self.subTest(slug=slug):
                for key in ("name", "seed", "base", "accent", "label", "target"):
                    self.assertTrue(params.get(key), "%s is missing %s" % (slug, key))
        self.assertEqual(sorted(paint_families.CALCULATIONS),
                         ["fn.discArt.nodding-seedhead", "fn.discArt.pressed-fern", "fn.discArt.wind-rose"])
        for key, fn in paint_families.CALCULATIONS.items():
            with self.subTest(key=key):
                self.assertNotEqual(fn.__name__, "<lambda>", "%s must not be a lambda" % key)
                self.assertIs(fn, paint_families.RENDERERS[key.rsplit(".", 1)[1]])


class FamiliesAreDistinctAt42Test(unittest.TestCase):
    """Rasterize the 42px tier and require every family to differ as pixels."""

    def test_no_two_families_rasterize_alike_at_42px(self):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:  # pragma: no cover - optional rasterizer
            self.skipTest("playwright is not installed")
        if not os.path.exists(CHROMIUM):  # pragma: no cover - optional rasterizer
            self.skipTest("chromium is not available at %s" % CHROMIUM)
        seen = {}
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path=CHROMIUM)
            try:
                page = browser.new_page(device_scale_factor=2.0)
                for family in paint_components.FAMILIES:
                    svg = paint_components.render(family, 7, COOL[0], COOL[1], 42, LABEL)
                    page.set_viewport_size({"width": 42, "height": 42})
                    page.set_content(
                        "<!doctype html><html><head><meta charset='utf-8'><style>"
                        "html,body{margin:0;padding:0;background:transparent}"
                        "svg{display:block;width:42px;height:42px}</style></head><body>"
                        + svg + "</body></html>", wait_until="load")
                    shot = page.screenshot(omit_background=True)
                    seen[family] = hashlib.sha256(shot).hexdigest()
            finally:
                browser.close()
        collisions = {}
        for family, pixels in seen.items():
            collisions.setdefault(pixels, []).append(family)
        clashing = [group for group in collisions.values() if len(group) > 1]
        self.assertEqual(clashing, [], "families rasterize identically at 42px: %r" % clashing)
        self.assertEqual(len(seen), len(paint_components.FAMILIES))


if __name__ == "__main__":
    unittest.main()
