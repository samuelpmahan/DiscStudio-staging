"""S3 investigation: visible Tee detection, as first-class Python PxC / PCR / PQL.

Production executes S3. Python consumes the resulting material and asks one
bounded question of it: does S3's drop surface balance? Every enclosed ring must
end up either a Tee or in a named rejection bucket. See S3_CHECKPOINT.md.

Two Calculations rather than one, because S3 is the first Stage with something to
compose: the second consumes the first's result directly inside the same PCR.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from investigation import StageInvestigation
from pyto import Calculation, Part, PCR, PQL, PxC

INV = StageInvestigation('S3', Path(__file__).parent)


def build_investigation(snapshot: dict) -> tuple[PxC, PCR]:
    pxc = PxC()

    rings = Part('px.tees.rings')
    family = Part('px.tees.family')
    tees = Part('px.tees')
    tee_px = Part('px.tees.px')
    ledger = Part('scratch.s3.ringLedger')
    summary = Part('scratch.s3.teeSummary')

    pxc.set(rings, snapshot['rings'])
    pxc.set(family, snapshot['family'])
    pxc.set(tees, snapshot['tees'])
    pxc.set(tee_px, snapshot['teePixels'])

    account = Calculation(
        'fn.quickAnno.s3.accountRings',
        lambda args: {
            'enclosed': len(args['rings']['enclosed']),
            'diamondDropped': sum(1 for ring in args['rings']['enclosed'] if ring['kind'] != 'tee-rect'),
            'elongated': len(args['rings']['elongated']),
            'excludedByBadge': len(args['rings']['excludedByBadge']),
            'candidates': len(args['rings']['candidates']),
            'measured': len(args['family']['measured']),
            'unframed': len(args['family']['unframed']),
            'votedOutOfFamily': sum(1 for item in args['family']['measured'] if not item['inFamily']),
            'familyMembers': len(args['family']['members']),
        },
    )

    # Every enclosed ring must leave through exactly one named door.
    balance = Calculation(
        'fn.quickAnno.s3.checkBalance',
        lambda args: {
            **args['ledger'],
            'tees': len(args['tees']),
            'teePx': len(args['teePx']),
            'balanced': (
                args['ledger']['enclosed'] == args['ledger']['elongated'] + args['ledger']['diamondDropped']
                and args['ledger']['elongated']
                == args['ledger']['candidates'] + args['ledger']['excludedByBadge']
                and args['ledger']['candidates'] == args['ledger']['measured'] + args['ledger']['unframed']
                and args['ledger']['measured']
                == args['ledger']['familyMembers'] + args['ledger']['votedOutOfFamily']
                and args['ledger']['familyMembers'] == len(args['tees'])
            ),
        },
    )

    pcr = PCR('S3.quick-anno')
    pcr.calc(
        'AccountRings',
        account,
        id='accountRings',
        rings=rings,
        family=family,
        into=ledger,
    )
    pcr.calc(
        'CheckBalance',
        balance,
        id='checkBalance',
        ledger=ledger,
        tees=tees,
        teePx=tee_px,
        into=summary,
    )
    pcr.run(pxc)
    return pxc, pcr


def main() -> None:
    image = INV.image_from_argv(sys.argv)
    inv = INV.for_image(image)
    snapshot = inv.export(image)
    pxc, pcr = build_investigation(snapshot)

    summary = PQL.part('scratch.s3.teeSummary').one(pxc)
    inv.emit(summary)
    # inv.write_mermaid(pcr) renders the composition when a graph needs a picture.
    inv.materialize()

    print(json.dumps(summary, indent=2))
    print(f"\nexperimental fill-consistent variant: {snapshot['experimental']['fillConsistent']}")
    print(f"\nNeon correctness: {inv.out_dir / 's3-neon-correctness-sheet.png'}")
    print(f'Snapshot: {inv.snapshot_path}')


if __name__ == '__main__':
    main()
