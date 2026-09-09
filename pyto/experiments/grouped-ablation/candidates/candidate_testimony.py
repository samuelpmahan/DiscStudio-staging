"""Candidate A (testimony-shaped) -- SURVIVOR, merged as ../retain.py.

Retained calculation entries are exactly the fields of CalculationTestimony
(pcr.py:63-69): {id, calculation, inputs: {name: 'px:<addr>'|'fn:<id>'}, args, into}.
This file is the candidate's adapter to the shared lens harness in refute.py; the
implementation under test is ../retain.py itself, so the lens verdicts describe
merged code, not a copy of it.
"""

from __future__ import annotations

import os
import sys
from typing import Any, Mapping

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import retain  # noqa: E402

NAME = "A. testimony-shaped"
SHAPE = "{name, ticks:[{name, calculations:[{id, calculation, inputs, args, into}]}]}"


def export(program: Mapping[str, Any]) -> dict[str, Any]:
    """The retained program dict is the document: no translation layer at all."""
    return dict(program)


def restore(document: Mapping[str, Any], registry: Mapping[str, Any]):
    return retain.from_program(document, registry)
