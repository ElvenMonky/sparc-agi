from dataclasses import dataclass
from typing import TYPE_CHECKING

from sparc_agi.puzzle.palette import Palette

if TYPE_CHECKING:
    from sparc_agi.puzzle_spec.spec import PuzzleSpec

@dataclass
class Puzzle:
    spec: PuzzleSpec
    palette: Palette
    input: str
    steps: tuple[str, ...]
