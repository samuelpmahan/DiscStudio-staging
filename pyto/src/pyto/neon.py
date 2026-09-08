"""Neon-first materialization kit.

The investigation convention is **neon first**: make a semantic difference
unmistakable before making a render subtle. If a panel needs pixel-peeping to
tell whether the computation happened, the materialization failed.

Promoted out of the S1 and S2 materializers, which had each grown their own
copy of every function here.
"""

from __future__ import annotations

from typing import Iterable, Sequence

from PIL import Image, ImageDraw, ImageFont

FONT = ImageFont.load_default()

GREEN = (57, 255, 20, 255)
CYAN = (0, 255, 255, 255)
YELLOW = (255, 255, 0, 255)
MAGENTA = (255, 0, 255, 255)
ORANGE = (255, 128, 0, 255)
RED = (255, 40, 40, 255)
GREY = (150, 150, 150, 255)

Color = tuple[int, int, int, int]
Bbox = Sequence[int]
LabelledBox = tuple[Bbox, str]


def dim(image: Image.Image, factor: float = 0.14) -> Image.Image:
    """Darken RGB, preserve alpha — the backdrop that makes neon read."""
    out = image.copy().convert('RGBA')
    red, green, blue, alpha = out.split()
    table = [int(value * factor) for value in range(256)]
    return Image.merge('RGBA', (red.point(table), green.point(table), blue.point(table), alpha))


def draw_boxes(
    image: Image.Image,
    boxes: Iterable[LabelledBox],
    color: Color,
    *,
    label_pad: int = 22,
) -> Image.Image:
    """Thick outlined boxes with an optional label. Black underlay keeps neon legible on light terrain."""
    out = image.copy().convert('RGBA')
    draw = ImageDraw.Draw(out)
    for bbox, text in boxes:
        x, y, width, height = bbox
        draw.rectangle([x - 2, y - 2, x + width + 1, y + height + 1], outline=(0, 0, 0, 255), width=6)
        draw.rectangle([x - 2, y - 2, x + width + 1, y + height + 1], outline=color, width=3)
        if text:
            ty = max(0, y - 18)
            draw.rectangle([x - 2, ty - 2, x + label_pad, ty + 13], fill=(0, 0, 0, 230))
            draw.text((x, ty), text, fill=color, font=FONT)
    return out


def paint_pixels(image: Image.Image, pixels: Iterable[int], color: Color) -> Image.Image:
    """Paint raster-index pixels. Index is y * width + x in canonical pixels."""
    out = image.copy().convert('RGBA')
    px = out.load()
    width = out.width
    height = out.height
    for value in pixels:
        x = value % width
        y = value // width
        if 0 <= x < width and 0 <= y < height:
            px[x, y] = color
    return out


def checkerboard(width: int, height: int, cell: int = 16) -> Image.Image:
    out = Image.new('RGBA', (width, height), (35, 35, 35, 255))
    draw = ImageDraw.Draw(out)
    for y in range(0, height, cell):
        for x in range(0, width, cell):
            if ((x // cell) + (y // cell)) % 2:
                draw.rectangle(
                    [x, y, min(width - 1, x + cell - 1), min(height - 1, y + cell - 1)],
                    fill=(70, 70, 70, 255),
                )
    return out


def remaining(image: Image.Image, removed: Iterable[int]) -> Image.Image:
    """The actual remaining raster: removed pixels transparent over a checkerboard."""
    out = image.copy().convert('RGBA')
    px = out.load()
    width = out.width
    for value in removed:
        x = value % width
        y = value // width
        r, g, b, _ = px[x, y]
        px[x, y] = (r, g, b, 0)
    bg = checkerboard(out.width, out.height)
    bg.alpha_composite(out)
    return bg


def crops(
    image: Image.Image,
    boxes: Iterable[LabelledBox],
    color: Color,
    *,
    pad: int = 18,
    cell: int = 128,
    cols: int = 6,
) -> Image.Image:
    """A contact strip of upscaled crops, one per box.

    Identity precedes geometry: a full-course panel proves *where* an object was
    accepted, never *what* it is. This answers the second question.
    """
    tiles: list[Image.Image] = []
    for bbox, text in boxes:
        x, y, width, height = bbox
        box = (
            max(0, x - pad),
            max(0, y - pad),
            min(image.width, x + width + pad),
            min(image.height, y + height + pad),
        )
        tile = image.crop(box).convert('RGBA')
        side = max(tile.width, tile.height, 1)
        offset_x = (side - tile.width) // 2
        offset_y = (side - tile.height) // 2
        square = Image.new('RGBA', (side, side), (0, 0, 0, 255))
        square.alpha_composite(tile, (offset_x, offset_y))
        tile = square.resize((cell, cell), Image.Resampling.NEAREST)
        draw = ImageDraw.Draw(tile)
        # Mark the subject inside the tile. Without this a crop says "something
        # near here", and a neighbouring object is easily mistaken for the one
        # being judged.
        scale = cell / side
        mark_x = (x - box[0] + offset_x) * scale
        mark_y = (y - box[1] + offset_y) * scale
        draw.rectangle(
            [mark_x - 1, mark_y - 1, mark_x + width * scale + 1, mark_y + height * scale + 1],
            outline=color,
            width=2,
        )
        draw.rectangle([0, 0, cell - 1, cell - 1], outline=color, width=2)
        if text:
            draw.rectangle([2, 2, 26, 15], fill=(0, 0, 0, 230))
            draw.text((4, 3), text, fill=color, font=FONT)
        tiles.append(tile)

    if not tiles:
        return Image.new('RGBA', (cell, cell), (22, 22, 22, 255))

    rows = -(-len(tiles) // cols)
    out = Image.new('RGBA', (cols * (cell + 4) + 4, rows * (cell + 4) + 4), (22, 22, 22, 255))
    for index, tile in enumerate(tiles):
        out.alpha_composite(tile, (4 + (index % cols) * (cell + 4), 4 + (index // cols) * (cell + 4)))
    return out


def fit_width(image: Image.Image, width: int) -> Image.Image:
    scale = width / image.width
    return image.resize((width, max(1, int(image.height * scale))), Image.Resampling.NEAREST)


def panel(title: str, image: Image.Image, width: int = 700) -> Image.Image:
    body = fit_width(image, width)
    title_height = 32
    out = Image.new('RGBA', (width, body.height + title_height), (12, 12, 12, 255))
    ImageDraw.Draw(out).text((8, 9), title, fill=(255, 255, 255, 255), font=FONT)
    out.alpha_composite(body, (0, title_height))
    return out


def sheet(panels: list[Image.Image], cols: int = 2, pad: int = 14) -> Image.Image:
    rows = [panels[index:index + cols] for index in range(0, len(panels), cols)]
    col_width = max(item.width for item in panels)
    row_heights = [max(item.height for item in row) for row in rows]
    out = Image.new(
        'RGBA',
        (cols * col_width + pad * (cols + 1), sum(row_heights) + pad * (len(rows) + 1)),
        (22, 22, 22, 255),
    )
    y = pad
    for row, row_height in zip(rows, row_heights):
        x = pad
        for item in row:
            out.alpha_composite(item, (x, y))
            x += col_width + pad
        y += row_height + pad
    return out
