from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from sparc_agi.puzzle.palette import Palette
from sparc_agi.puzzle.slot import CacheSlot

if TYPE_CHECKING:
    from sparc_agi.puzzle_spec.spec import PuzzleSpec

@dataclass
class PuzzleDescription:
    input: str
    steps: tuple[str, ...]

@dataclass
class Puzzle:
    spec: PuzzleSpec
    palette: Palette
    cache: dict[str, CacheSlot] = field(default_factory=dict)
    description: PuzzleDescription | None = None
