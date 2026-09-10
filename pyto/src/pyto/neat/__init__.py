"""neat.* Parts: work items, reviews, captures, and gate results.

Kept to this docstring, with no imports of its own: task 65 builds
``pyto/src/pyto/neat/review.py`` in this same package in another copy at the same
time, and a package `__init__` that imported one sibling module eagerly would make
the other's absence (or presence) here a collision instead of two files landing
side by side. Import each module directly -- ``from pyto.neat import diff``, or
``from pyto.neat.diff import candidates`` -- never through this file.
"""
