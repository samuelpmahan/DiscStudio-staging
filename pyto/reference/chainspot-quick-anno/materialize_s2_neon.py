"""S2 neon-first correctness sheet: Basket family, shell, objects and exact BasketPx."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image

from pyto.neon import (
    CYAN,
    GREEN,
    MAGENTA,
    ORANGE,
    YELLOW,
    dim,
    draw_boxes,
    paint_pixels,
    panel,
    remaining,
    sheet,
)


def ordered(items: list[dict]) -> list[tuple[list[int], str]]:
    return [(item['bbox'], str(item.get('order', ''))) for item in items]


def main() -> None:
    snapshot_path = Path(sys.argv[1]).resolve()
    snapshot = json.loads(snapshot_path.read_text())
    out_dir = snapshot_path.parent
    canonical = Image.open(out_dir / snapshot['panels']['s2:CroppedImage from S1 PxC']).convert('RGBA')

    family = draw_boxes(canonical, ordered(snapshot['family']), CYAN)
    shells = draw_boxes(canonical, ordered(snapshot['shellMembers']), YELLOW)
    baskets = draw_boxes(canonical, ordered(snapshot['baskets']), GREEN)
    basket_pixels = set(snapshot['basketPixels'])
    owned = paint_pixels(dim(canonical), basket_pixels, MAGENTA)
    removed = paint_pixels(dim(canonical), basket_pixels, ORANGE)
    remain = remaining(canonical, basket_pixels)

    panels = [
        panel(f"1  BASKET FAMILY — neon cyan ({len(snapshot['family'])})", family),
        panel(f"2  SHELL FAMILY — neon yellow ({len(snapshot['shellMembers'])})", shells),
        panel(f"3  BASKET OBJECTS — neon green ({len(snapshot['baskets'])})", baskets),
        panel(f"4  BASKET PX — neon magenta ({len(basket_pixels):,})", owned),
        panel('5  REMOVED FROM REMAINING — neon orange', removed),
        panel('6  ACTUAL REMAINING — transparent BasketPx over checkerboard', remain),
    ]

    out = out_dir / 's2-neon-correctness-sheet.png'
    sheet(panels).save(out)
    family.save(out_dir / 's2-family-neon.png')
    shells.save(out_dir / 's2-shell-family-neon.png')
    baskets.save(out_dir / 's2-baskets-neon.png')
    owned.save(out_dir / 's2-basket-px-neon.png')
    remain.save(out_dir / 's2-remaining-checkerboard.png')
    print(out)


if __name__ == '__main__':
    main()
