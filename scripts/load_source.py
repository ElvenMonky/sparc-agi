#!/usr/bin/env python3
"""Load, validate, describe, and sample-generate from a puzzle source JSON.

Accepts an optional source path; defaults to data/puzzle_bible.json.
"""

import argparse
import pprint
import random
from pathlib import Path

from sparc_agi.parser import converter, load_source

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "data" / "puzzle_bible.json"


def _resolve_path(path: Path) -> Path:
    if path.is_absolute():
        return path
    candidate = ROOT / path
    return candidate if candidate.exists() else path


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "source",
        nargs="?",
        type=Path,
        default=DEFAULT_SOURCE,
        help=f"Puzzle source JSON (default: {DEFAULT_SOURCE.relative_to(ROOT)})",
    )
    args = parser.parse_args(argv)

    source_path = _resolve_path(args.source)
    source = load_source(source_path)
    for puzzle_id, puzzle in source.items():
        print(f"=== {puzzle_id} ===")
        print(puzzle.describe_input())
        print(puzzle.describe_transformations())
        generated = puzzle.generate(random.Random(0))
        print("description:")
        pprint.pp(generated.description)
        print("challenge train[0]:")
        pprint.pp(generated.challenge["train"][0])
        print("challenge test[0] input:")
        pprint.pp(generated.challenge["test"][0])
        print("solution:")
        pprint.pp(generated.solution)
        print("steps train[0]:")
        pprint.pp(generated.steps["train"][0])
        print("cache:")
        pprint.pp(generated.cache)
        print("round-trip:")
        pprint.pp(converter.unstructure(puzzle))


if __name__ == "__main__":
    main()
