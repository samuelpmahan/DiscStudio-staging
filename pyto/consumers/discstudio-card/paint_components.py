#!/usr/bin/env python3
"""Component-aware, seeded disc SVGs for 42/96/220px display tiers."""
from __future__ import annotations
import argparse, hashlib, html, math, random
from pathlib import Path
import re

import paint_families

HEX = re.compile(r"^#[0-9a-fA-F]{6}$")
SIZE, C, R = 512, 256, 220
# The four originals. Their bytes are frozen: test_paint_families.py pins a
# sha256 per family x target and fails on any drift.
CLASSIC_FAMILIES = ("Orbit Foundry", "Petal Press", "Signal Stamp", "Tessellated Flight")
# Promoted out of the art tournament (experiments/art-tournament/RESULTS.md).
# Rendered by paint_families, which owns their code verbatim from the studios.
PROMOTED_FAMILIES = paint_families.FAMILIES
FAMILIES = CLASSIC_FAMILIES + PROMOTED_FAMILIES
TARGETS = (42, 96, 220)

def hex_color(value: str) -> str:
    if not HEX.fullmatch(value):
        raise argparse.ArgumentTypeError("use a six-digit hex color")
    return value.lower()

def xy(radius: float, angle: float) -> tuple[float, float]:
    return C + radius * math.cos(angle), C + radius * math.sin(angle)

def render(family: str, seed: int, base: str, accent: str, target: int, label: str) -> str:
    if family not in FAMILIES or target not in TARGETS:
        raise ValueError("family or target is unsupported")
    if family in PROMOTED_FAMILIES:
        # Promoted families own their whole document; dispatch before any RNG is
        # touched so the four originals keep rendering byte-for-byte as before.
        return paint_families.render(family, seed, base, accent, target, label)
    # Derive every identity parameter once. Rendering another target consumes no RNG.
    rng = random.Random(seed)
    rotation = rng.uniform(-12, 12)
    dot_angle = rng.uniform(-0.7, 0.7)
    phase = rng.randrange(4)
    safe = html.escape(label, quote=True)
    scale = target / SIZE
    # Values remain in the 512-unit viewBox; floor only the effective output width.
    stroke = lambda source, min_output=1.0: max(source, round(min_output / scale, 1))
    out = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{target}" height="{target}" viewBox="0 0 {SIZE} {SIZE}" role="img" aria-label="{safe}">',
        '<defs><clipPath id="disc"><circle cx="256" cy="256" r="220"/></clipPath>',
        '<linearGradient id="depth" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".18"/><stop offset="1" stop-color="#000" stop-opacity=".28"/></linearGradient></defs>',
        '<g id="base" clip-path="url(#disc)">', f'<circle cx="256" cy="256" r="220" fill="{base}"/>',
        '<circle cx="256" cy="256" r="220" fill="url(#depth)"/>', '</g>',
        '<g id="rim" fill="none">', f'<circle cx="256" cy="256" r="216" stroke="{accent}" stroke-width="{stroke(7)}" opacity=".9"/>',
        f'<circle cx="256" cy="256" r="201" stroke="#fff" stroke-width="{stroke(3)}" opacity=".28"/>', '</g>',
        '<g id="art" clip-path="url(#disc)">',
    ]
    if family == "Orbit Foundry":
        if target == 42:
            out.append(f'<path d="M120 294 Q220 130 356 198" fill="none" stroke="{accent}" stroke-width="{stroke(18)}" stroke-linecap="round"/>')
        else:
            count = 2 if target == 96 else 3
            for i in range(count):
                rad = (92, 146, 194)[i]
                out.append(f'<ellipse cx="256" cy="256" rx="{rad}" ry="{rad*.38:.1f}" fill="none" stroke="{accent}" stroke-width="{stroke(10 if target == 220 else 8)}" opacity=".8" transform="rotate({rotation + i*28:.1f} 256 256)"/>')
    elif family == "Petal Press":
        count = 4 if target == 42 else (6 if target == 96 else 10)
        for i in range(count):
            a = i * math.tau / count + rotation * math.pi / 180
            x, y = xy(78, a)
            out.append(f'<ellipse cx="{x:.1f}" cy="{y:.1f}" rx="{34 if target == 42 else 28}" ry="{72 if target > 42 else 54}" fill="{accent}" opacity=".72" transform="rotate({math.degrees(a)+90:.1f} {x:.1f} {y:.1f})"/>')
    elif family == "Signal Stamp":
        out.append(f'<path d="M160 300 Q256 150 352 300" fill="none" stroke="{accent}" stroke-width="{stroke(24)}" stroke-linecap="round"/>')
        out.append(f'<path d="M172 206 l28 -20" stroke="{accent}" stroke-width="{stroke(18)}" stroke-linecap="round"/>')
        if target == 220:
            out.append(f'<circle cx="256" cy="256" r="74" fill="none" stroke="{accent}" stroke-width="{stroke(8)}" opacity=".65"/>')
    else:
        tiles = 2 if target == 42 else (3 if target == 96 else 4)
        for i in range(tiles):
            x = 80 + (i + phase % 2) * 92
            out.append(f'<path d="M{x} 120 l70 0 120 272 -70 0z" fill="{accent}" opacity="{.72 - i*.08:.2f}"/>')
    out.append('</g>')
    out.append('<g id="stamp">')
    if family == "Petal Press":
        out.append(f'<circle cx="256" cy="256" r="{54 if target < 220 else 62}" fill="{base}" stroke="{accent}" stroke-width="{stroke(12)}"/>')
    elif family == "Tessellated Flight":
        out.append(f'<circle cx="256" cy="256" r="{42 if target < 220 else 52}" fill="{base}" stroke="{accent}" stroke-width="{stroke(10)}"/>')
    else:
        x, y = xy(118 if target == 42 else 156, dot_angle)
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{16 if target == 42 else 12}" fill="{accent}"/>')
    out.append('</g>')
    if target == 220:
            display = html.escape(label.strip()[:10], quote=True)
            out += ['<g id="text">', f'<text x="256" y="420" text-anchor="middle" font-family="sans-serif" font-size="22" letter-spacing="3" fill="{accent}" opacity=".82">{display}</text>', '</g>']
    out += [f'<title>{safe}</title>', '</svg>']
    return "\n".join(out) + "\n"

def main() -> None:
    p = argparse.ArgumentParser(description="Generate a component-scaled display disc SVG")
    p.add_argument("--family", choices=FAMILIES, required=True)
    p.add_argument("--seed", type=int, required=True)
    p.add_argument("--base", type=hex_color, default="#4c9bc6")
    p.add_argument("--accent", type=hex_color, default="#0d3558")
    p.add_argument("--target-px", type=int, choices=TARGETS, required=True)
    p.add_argument("--label", default="painted disc")
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args(); a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(render(a.family, a.seed, a.base, a.accent, a.target_px, a.label), encoding="utf-8")

if __name__ == "__main__": main()
