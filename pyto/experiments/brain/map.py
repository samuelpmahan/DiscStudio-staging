"""`python -m experiments.brain.map` (from pyto/): the territory, through pql.

it loads every vertical's `store/*.json` into one `PxC` and prints what
`harness.navigate` reads back out of it. no vertical is privileged: the map is
whatever the stores hold.
"""

from experiments.brain.harness import Store, territory


def main() -> int:
    store = Store()
    store.load_store()
    print(territory(store))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
