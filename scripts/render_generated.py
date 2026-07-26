#!/usr/bin/env python3
"""Render generated puzzle JSON into PNGs under temp/.

Accepts an optional generated-JSON path (default: latest in temp/) and an optional
source path for cache labels (default: source recorded in the JSON, else
data/puzzle_bible.json).
"""

import argparse
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt

from sparc_agi.plotting import render_generated_puzzle
from sparc_agi.parser import load_source

ROOT = Path(__file__).resolve().parents[1]
TEMP = ROOT / "temp"
DEFAULT_SOURCE = ROOT / "data" / "puzzle_bible.json"


def _resolve_path(path: Path) -> Path:
    if path.is_absolute():
        return path
    candidate = ROOT / path
    return candidate if candidate.exists() else path


def _latest_generated_json() -> Path:
    files = sorted(TEMP.glob("generated_*.json"))
    if not files:
        raise FileNotFoundError(f"no generated_*.json files in {TEMP}")
    return max(files, key=lambda p: p.stat().st_mtime)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "json_path",
        nargs="?",
        type=Path,
        help="Path to generated_*.json (default: latest in temp/)",
    )
    parser.add_argument(
        "puzzle_id",
        nargs="?",
        help="Optional puzzle id to render (default: all puzzles in the file)",
    )
    parser.add_argument(
        "--source",
        type=Path,
        help="Puzzle source JSON for cache feature labels "
        f"(default: 'source' from the generated file, else {DEFAULT_SOURCE.relative_to(ROOT)})",
    )
    args = parser.parse_args(argv)

    json_path = _resolve_path(args.json_path) if args.json_path else _latest_generated_json()
    payload = json.loads(json_path.read_text())
    puzzles = payload.get("puzzles") or {}
    if not puzzles:
        print(f"no puzzles in {json_path}", file=sys.stderr)
        return 1

    ids = [args.puzzle_id] if args.puzzle_id else list(puzzles)
    missing = [pid for pid in ids if pid not in puzzles]
    if missing:
        print(f"unknown puzzle id(s): {', '.join(missing)}", file=sys.stderr)
        return 1

    if args.source is not None:
        source_path = _resolve_path(args.source)
    elif payload.get("source"):
        source_path = _resolve_path(Path(payload["source"]))
    else:
        source_path = DEFAULT_SOURCE
    source = load_source(source_path) if source_path.exists() else {}

    TEMP.mkdir(parents=True, exist_ok=True)
    stem = json_path.stem
    written: list[Path] = []
    for puzzle_id in ids:
        cache_features = source[puzzle_id].cache if puzzle_id in source else {}
        fig = render_generated_puzzle(
            puzzle_id,
            puzzles[puzzle_id],
            generated_at=payload.get("generated_at"),
            cache_features=cache_features,
        )
        out_path = TEMP / f"{stem}_{puzzle_id}.png"
        fig.savefig(out_path, dpi=150, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        written.append(out_path)

    for path in written:
        try:
            rel = path.relative_to(ROOT)
        except ValueError:
            rel = path
        print(f"wrote {rel}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
