#!/usr/bin/env python3
"""Generate a fresh puzzle set from a source JSON into temp/ with a timestamped file.

Accepts an optional source path; defaults to data/puzzle_bible.json.
"""

import argparse
import json
import random
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sparc_agi.parser import load_source
from sparc_agi.puzzle import GeneratedPuzzle

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "data" / "puzzle_bible.json"
TEMP = ROOT / "temp"


def _resolve_path(path: Path) -> Path:
    if path.is_absolute():
        return path
    candidate = ROOT / path
    return candidate if candidate.exists() else path


def _rel_to_root(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def _to_jsonable(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return {k: _to_jsonable(v) for k, v in asdict(value).items()}
    if isinstance(value, dict):
        return {str(k): _to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_jsonable(v) for v in value]
    return value


def generate_all(
    source_path: Path = DEFAULT_SOURCE,
    *,
    rng: random.Random | None = None,
) -> dict[str, Any]:
    """Generate unique instances for every puzzle in the source."""
    rng = rng if rng is not None else random.Random()
    source_path = _resolve_path(source_path)
    source = load_source(source_path)
    results: dict[str, GeneratedPuzzle] = {}
    for puzzle_id, puzzle in source.items():
        # Independent stream per puzzle so ordering stays stable if the source grows.
        puzzle_rng = random.Random(rng.randrange(2**63))
        results[puzzle_id] = puzzle.generate(puzzle_rng)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": _rel_to_root(source_path),
        "puzzles": {pid: _to_jsonable(gen) for pid, gen in results.items()},
    }


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

    TEMP.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ")
    out_path = TEMP / f"generated_{stamp}.json"
    payload = generate_all(args.source)
    out_path.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"wrote {out_path.relative_to(ROOT)}")
    print(f"source: {payload['source']}")
    print(f"puzzles: {', '.join(payload['puzzles'])}")


if __name__ == "__main__":
    main()
