#!/usr/bin/env python3
"""Write puzzle descriptions from a puzzle source file to a JSON file."""

import argparse
import json
import random
from dataclasses import asdict, dataclass
from pathlib import Path

from sparc_agi.puzzle_spec.repo import PuzzleSpecRepository

DEFAULT_SOURCE = Path(__file__).resolve().parents[1] / "data" / "puzzle_bible.json"
DEFAULT_OUTPUT = Path(__file__).resolve().parents[1] / "temp" / "puzzle_descriptions.json"

@dataclass
class DescriptionRecord:
    input: str
    steps: list[str]
    palette: list[int]

def describe_source(
    source_path: Path,
    output_path: Path,
    *,
    seed: int | None = 0,
) -> dict[str, DescriptionRecord]:
    repo = PuzzleSpecRepository.load(source_path)
    rng = random.Random(seed) if seed is not None else None
    records: dict[str, DescriptionRecord] = {}
    for puzzle_id, puzzle in repo.puzzles.items():
        ctx = puzzle.instantiate(rng)
        records[puzzle_id] = DescriptionRecord(
            input=ctx.input,
            steps=list(ctx.steps),
            palette=list(ctx.palette),
        )
    output_path.write_text(json.dumps(
        {puzzle_id: asdict(record) for puzzle_id, record in records.items()},
        indent=2,
    ) + "\n")
    return records

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--seed",
        type=int,
        default=0,
        help="palette RNG seed (omit with --no-seed for a fresh palette per puzzle)",
    )
    parser.add_argument("--no-seed", action="store_true")
    args = parser.parse_args()

    seed = None if args.no_seed else args.seed
    records = describe_source(args.source, args.output, seed=seed)
    print(f"Wrote {len(records)} descriptions to {args.output}")

if __name__ == "__main__":
    main()
