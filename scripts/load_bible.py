#!/usr/bin/env python3
"""Load and pretty-print data/puzzle_spec_bible.json via PuzzleSpec parsing."""

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
        print("round-trip:")
        pprint.pp(converter.unstructure(spec))


if __name__ == "__main__":
    main()
