"""S1 neon-first correctness sheet: Badge ownership and mute, made unmistakable."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image

from pyto.neon import (
    CYAN,
    GREEN,
    MAGENTA,
    YELLOW,
    dim,
    draw_boxes,
    paint_pixels,
    panel,
    remaining,
    sheet,
)


def main() -> None:
    snapshot_path = Path(sys.argv[1]).resolve()
    snapshot = json.loads(snapshot_path.read_text())
    out_dir = snapshot_path.parent

    canonical = Image.open(out_dir / snapshot['panels']['s0:CroppedImage']).convert('RGBA')
    masks = Image.open(out_dir / snapshot['panels']['s1:Masks']).convert('RGBA')
    owned = set(snapshot['ownedPixels'])
    muted = set(snapshot['mutedPixels'])
    added = muted - owned

    owned_view = paint_pixels(dim(canonical), owned, CYAN)
    added_view = paint_pixels(dim(canonical), added, YELLOW)
    muted_view = paint_pixels(paint_pixels(dim(canonical), owned, CYAN), added, YELLOW)
    removed_view = paint_pixels(dim(canonical), muted, MAGENTA)
    remaining_view = remaining(canonical, muted)
    badge_view = draw_boxes(
        canonical,
        [(badge['bbox'], str(badge['label'] or order)) for order, badge in enumerate(snapshot['badges'], 1)],
        GREEN,
        label_pad=18,
    )

    panels = [
        panel('1  BADGE OBJECTS — neon green boxes + labels', badge_view),
        panel('2  MASKS — production bright/dark mask', masks),
        panel(f'3  OWNED PX — neon cyan ({len(owned):,})', owned_view),
        panel(f'4  ADDED MUTE ONLY — neon yellow ({len(added):,})', added_view),
        panel(f'5  MUTED TOTAL — cyan owned + yellow added ({len(muted):,})', muted_view),
        panel('6  REMOVED FROM REMAINING — neon magenta', removed_view),
        panel('7  ACTUAL REMAINING — transparent removals over checkerboard', remaining_view),
    ]

    sheet_path = out_dir / 's1-neon-correctness-sheet.png'
    sheet(panels).save(sheet_path)
    owned_view.save(out_dir / 's1-owned-neon.png')
    added_view.save(out_dir / 's1-added-mute-neon.png')
    muted_view.save(out_dir / 's1-muted-neon.png')
    removed_view.save(out_dir / 's1-removed-neon.png')
    remaining_view.save(out_dir / 's1-remaining-checkerboard.png')
    badge_view.save(out_dir / 's1-badge-objects-neon.png')
    print(sheet_path)


if __name__ == '__main__':
    main()
