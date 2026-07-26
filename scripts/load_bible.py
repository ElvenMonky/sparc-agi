#!/usr/bin/env python3
"""Load, validate, and describe data/puzzle_spec_bible.json."""

import pprint
from pathlib import Path

from sparc_agi.puzzle_spec import converter, load_bible

ROOT = Path(__file__).resolve().parents[1]
BIBLE = ROOT / "data" / "puzzle_spec_bible.json"


def main() -> None:
    bible = load_bible(BIBLE)
    for puzzle_id, spec in bible.items():
        print(f"=== {puzzle_id} ===")
        pprint.pp(spec)
        print("validated ok")
        print(spec.describe_input())
        print(spec.describe_transformations())
        print("round-trip:")
        pprint.pp(converter.unstructure(spec))


if __name__ == "__main__":
    main()
