"""The bounded transfer pattern, once instead of once per Stage.

Every quick_anno Stage investigation runs the same spine:

    real production Stage  ->  smallest useful snapshot  ->  first-class Python
    PxC Parts  ->  bounded PCR Calculation  ->  published scratch Part  ->  PQL
    query  ->  Mermaid view  ->  neon-first correctness materialization

Only the middle (which Parts, which Calculation) is Stage-specific, so only that
stays in `experiments/quick-anno-python/s<N>.py`. This module owns the rest.

Promoted after S3 made it the third identical copy.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from pyto import PCR


class StageInvestigation:
    """Paths, the Node snapshot bridge, and the emit/materialize steps for one Stage."""

    def __init__(self, stage: str, script_dir: Path | str, course: str = 'DashsTrack') -> None:
        self.stage = stage
        self.course = course
        self.script_dir = Path(script_dir).resolve()
        self.repo_root = self.script_dir.parents[1]
        self.out_dir = self.script_dir / 'generated' / f'{course}-{stage}'
        self.snapshot_path = self.out_dir / 'snapshot.json'
        self.bridge = self.script_dir / f'export_{stage.lower()}_snapshot.cjs'
        self.materializer = self.script_dir / f'materialize_{stage.lower()}_neon.py'

    def for_image(self, image: Path) -> 'StageInvestigation':
        """Same Stage, bound to whichever course this raster belongs to."""
        return StageInvestigation(self.stage, self.script_dir, self.course_of(image))

    @staticmethod
    def course_of(image: Path) -> str:
        """Course identity is the filename stem, not the directory.

        The corpus directory does not always match the course name
        (`dev/Heritage/HeritagePark-full.png`), so the stem is what to trust.
        """
        stem = image.stem
        return stem[: -len('-full')] if stem.endswith('-full') else stem

    def course_image(self, course: str) -> Path:
        """Locate a course raster in the sibling corpus checkout.

        Extensions vary in kind and in case across the corpus (.jpg, .png,
        .PNG), so the extension is globbed rather than assumed.
        """
        root = self.repo_root.parent / 'chainspot-corpus' / 'dev'
        matches = sorted(path for path in root.glob(f'*/{course}-full.*') if path.is_file())
        if not matches:
            raise FileNotFoundError(f'no corpus raster for course {course!r} under {root}')
        return matches[0].resolve()

    def default_image(self) -> Path:
        return self.course_image(self.course)

    def image_from_argv(self, argv: list[str]) -> Path:
        return Path(argv[1]).resolve() if len(argv) > 1 else self.default_image()

    def export(self, image: Path) -> dict[str, Any]:
        """Execute the real production Stages in Node and read back the snapshot."""
        self.out_dir.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ['node', str(self.bridge), str(image), str(self.out_dir)],
            cwd=self.repo_root,
            check=True,
        )
        return json.loads(self.snapshot_path.read_text())

    def emit(self, summary: Any) -> Path:
        """Write the PQL answer."""
        summary_path = self.out_dir / 'python-summary.json'
        summary_path.write_text(json.dumps(summary, indent=2) + '\n')
        return summary_path

    def write_mermaid(self, pcr: PCR) -> Path:
        """Render the composition as a picture. Call this when a graph is big
        enough that a human would rather look than read.

        Not part of the pattern's spine: nothing consumes the .mmd, and a
        two-node graph needs no diagram. The emitter stays because the day a
        Stage graph has a dozen nodes it will be the cheapest way to see it.
        """
        mermaid_path = self.out_dir / f'python-{self.stage}.mmd'
        mermaid_path.write_text(pcr.mermaid())
        return mermaid_path

    def materialize(self) -> None:
        subprocess.run(
            [sys.executable, str(self.materializer), str(self.snapshot_path)],
            cwd=self.repo_root,
            check=True,
        )
