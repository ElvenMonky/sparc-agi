from dataclasses import dataclass, field

from sparc_agi.features.base import FeatureSpec
from sparc_agi.puzzle_spec.palette import PaletteSpec
from sparc_agi.puzzle_spec.sample import SampleSpec
from sparc_agi.transformations import Transformation

@dataclass
class CacheItem:
    feature: FeatureSpec
    scope: str = "puzzle"

@dataclass
class PuzzleSpec:
    cache: dict[str, CacheItem] = field(default_factory=dict)
    input: FeatureSpec | None = None
    samples: SampleSpec = field(default_factory=SampleSpec)
    palette: PaletteSpec = field(default_factory=PaletteSpec)
    skeleton: list[Transformation] = field(default_factory=list)
