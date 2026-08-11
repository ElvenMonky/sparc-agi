from dataclasses import dataclass
from typing import TYPE_CHECKING

from sparc_agi.puzzle_spec.palette import Palette

if TYPE_CHECKING:
    from sparc_agi.puzzle_spec.features.base import FeatureSpec

@dataclass(frozen=True)
class PuzzleContext:
    palette: Palette
    step_outputs: tuple[FeatureSpec, ...]
