"""run.py's fn.evo.render, computed the fast way: the candidate `neat equiv` witnesses.

Same argument as run.py's render (one dict holding `spec`), same pixels, as a uint8
array instead of a list of 196,608 ints: geometry evaluates each stroke on its own
bounding box and tint is one broadcast (fast.py).

    neat equiv observed/record.json --calc fn.evo.render --candidate exp/evo-pxc/fast_render.py:render

`render_palette_swapped` is the control: the same renderer with the palette's base and
accent exchanged, which must witness 0/32.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for path in (str(ROOT / 'exp/evolution-painting'), str(HERE)):
    if path not in sys.path:
        sys.path.insert(0, path)
import evolve as existing  # noqa: E402
import fast  # noqa: E402


def _field(spec):
    genome = spec['candidate']['genome']
    return fast.geometry(dict(fields_module=existing.FIELDS, genome=genome, size=spec['size'],
                              geometry_size=spec['geometry_size'], defaults=spec['defaults']))


def render(a):
    """spec -> uint8 rgb array (size, size, 3), the same pixels run.py's render listed."""
    spec = a['spec']
    palette = spec['palettes'][spec['candidate']['genome']['palette']]
    return fast.tint({'field': _field(spec), 'palette': palette})


def render_palette_swapped(a):
    """The same renderer with base and accent exchanged: the deliberately wrong candidate."""
    spec = a['spec']
    palette = spec['palettes'][spec['candidate']['genome']['palette']]
    swapped = dict(palette, base=palette['accent'], accent=palette['base'])
    return fast.tint({'field': _field(spec), 'palette': swapped})
