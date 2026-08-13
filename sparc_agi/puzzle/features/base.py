from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sparc_agi.puzzle.puzzle import Puzzle
    from sparc_agi.puzzle_spec.features.base import FeatureSpec

@dataclass
class Feature:
    spec: FeatureSpec

    def refer(self, ctx: Puzzle) -> str:
        return self.spec.refer(ctx, self)

@dataclass
class Scalar(Feature):
    value: int

@dataclass
class Size(Feature):
    width: Scalar
    height: Scalar

@dataclass
class Filter(Feature):
    pass

@dataclass
class Arrangement(Feature):
    size: Size | None
    value: int  # bitmask

@dataclass
class Pattern(Feature):
    pass

@dataclass
class LinearPattern(Pattern):
    direction: Scalar

@dataclass
class Mapping(Feature):
    value: dict[int, int]

@dataclass
class Geometry(Feature):
    bbox: tuple[int, int, int, int]
    grid: list[list[int]]
    children: list[Geometry]
