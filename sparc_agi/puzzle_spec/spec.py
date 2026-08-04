from dataclasses import dataclass, field
from typing import Any

from sparc_agi.puzzle_spec.cache import CacheItem
from sparc_agi.puzzle_spec.features.base import ObjectSpec
from sparc_agi.puzzle_spec.palette import PaletteSpec
from sparc_agi.puzzle_spec.range import Range

@dataclass
class SamplesSpec:
    train: Range
    test: Range

@dataclass
class PuzzleSpec:
    input: ObjectSpec
    samples: SamplesSpec
    steps: list[dict[str, list[Any]]]
    cache: dict[str, CacheItem] = field(default_factory=dict)
    palette: PaletteSpec = field(default_factory=PaletteSpec)
