"""S3 neon-first correctness sheet: rings -> frames -> family vote -> visible Tee objects.

S3's drop surface is wider than S1's or S2's — a ring can die as a diamond, as a
Badge-muted center, as an unframed ring, or by losing the family size vote. Each
death gets a colour here, because a candidate that vanishes with no record is a
bug, not a filter.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image

from pyto.neon import (
    GREEN,
    GREY,
    MAGENTA,
    ORANGE,
    RED,
    YELLOW,
    crops,
    dim,
    draw_boxes,
    paint_pixels,
    panel,
    remaining,
    sheet,
)


def bare(items: list[dict], key: str = 'bbox') -> list[tuple[list[int], str]]:
    return [(item[key], '') for item in items]


def ordered(items: list[dict], key: str = 'bbox') -> list[tuple[list[int], str]]:
    return [(item[key], str(item.get('order', ''))) for item in items]


def main() -> None:
    snapshot_path = Path(sys.argv[1]).resolve()
    snapshot = json.loads(snapshot_path.read_text())
    out_dir = snapshot_path.parent
    canonical = Image.open(out_dir / snapshot['panels']['s3:CroppedImage']).convert('RGBA')

    counts = snapshot['counts']
    rings = snapshot['rings']
    family = snapshot['family']
    diamonds = [ring for ring in rings['enclosed'] if ring['kind'] != 'tee-rect']
    voted_out = [item for item in family['measured'] if not item['inFamily']]

    candidates_view = draw_boxes(canonical, bare(rings['candidates']), YELLOW)

    # One panel for every way a ring can die, each its own colour.
    rejected_view = draw_boxes(canonical, bare(diamonds), GREY)
    rejected_view = draw_boxes(rejected_view, bare(rings['excludedByBadge']), RED)
    rejected_view = draw_boxes(rejected_view, bare(family['unframed']), ORANGE)

    frames_view = draw_boxes(canonical, [(item['frame']['bbox'], '') for item in family['measured']], ORANGE)

    vote_view = draw_boxes(canonical, [(item['frame']['bbox'], '') for item in voted_out], MAGENTA)
    vote_view = draw_boxes(vote_view, ordered(family['members']), GREEN)

    tees_view = draw_boxes(canonical, ordered(snapshot['tees']), GREEN)

    tee_pixels = set(snapshot['teePixels'])
    tee_px_view = paint_pixels(dim(canonical), tee_pixels, MAGENTA)
    remaining_view = remaining(canonical, tee_pixels)

    tees_strip = crops(canonical, ordered(snapshot['tees']), GREEN)
    # Rejections get more surrounding context than acceptances: the question a
    # rejection panel has to answer is "what IS this thing", not "where was it".
    # Every bucket gets one, so no drop is judged by its bounding box alone.
    voted_strip = crops(
        canonical,
        [(item['frame']['bbox'], str(item['order'])) for item in voted_out],
        MAGENTA,
        pad=52,
        cell=192,
    )
    muted_strip = crops(
        canonical,
        [(ring['bbox'], str(order)) for order, ring in enumerate(rings['excludedByBadge'], 1)],
        RED,
        pad=52,
        cell=192,
    )
    unframed_strip = crops(
        canonical,
        [(ring['bbox'], str(order)) for order, ring in enumerate(family['unframed'], 1)],
        ORANGE,
        pad=52,
        cell=192,
    )

    panels = [
        panel(
            f"1  RING CANDIDATES after Badge mute — neon yellow, inner holes ({counts['candidates']})",
            candidates_view,
        ),
        panel(
            f"2  REJECTED — grey diamond ({len(diamonds)}) · red Badge-muted ({counts['excludedByBadge']})"
            f" · orange unframed ({counts['unframed']})",
            rejected_view,
        ),
        panel(
            f"3  ENCLOSING BRIGHT FRAMES — neon orange ({counts['measured']})",
            frames_view,
        ),
        panel(
            f"4  FAMILY VOTE — green kept ({counts['familyMembers']}) · magenta voted out ({len(voted_out)})",
            vote_view,
        ),
        panel(f"5  TEE OBJECTS — neon green, frame bbox ({counts['tees']})", tees_view),
        panel(f"6  TEE PX — neon magenta ({len(tee_pixels):,})", tee_px_view),
        panel('7  ACTUAL REMAINING — transparent TeePx over checkerboard', remaining_view),
        panel(f"8  WHAT EACH ACCEPTED TEE IS — crop per object ({counts['tees']})", tees_strip),
        panel(f'9  WHAT WAS VOTED OUT — crop per rejected frame ({len(voted_out)})', voted_strip),
        panel(
            f"10  WHAT THE BADGE MUTE EXCLUDED — crop per ring ({counts['excludedByBadge']})",
            muted_strip,
        ),
        panel(f"11  WHAT HAD NO ENCLOSING FRAME — crop per ring ({counts['unframed']})", unframed_strip),
    ]

    out = out_dir / 's3-neon-correctness-sheet.png'
    sheet(panels).save(out)
    candidates_view.save(out_dir / 's3-ring-candidates-neon.png')
    rejected_view.save(out_dir / 's3-rejected-neon.png')
    frames_view.save(out_dir / 's3-frames-neon.png')
    vote_view.save(out_dir / 's3-family-vote-neon.png')
    tees_view.save(out_dir / 's3-tees-neon.png')
    tee_px_view.save(out_dir / 's3-tee-px-neon.png')
    remaining_view.save(out_dir / 's3-remaining-checkerboard.png')
    tees_strip.save(out_dir / 's3-tee-crops.png')
    voted_strip.save(out_dir / 's3-voted-out-crops.png')
    muted_strip.save(out_dir / 's3-badge-muted-crops.png')
    unframed_strip.save(out_dir / 's3-unframed-crops.png')
    print(out)


if __name__ == '__main__':
    main()
