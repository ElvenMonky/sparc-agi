from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sparc_agi.puzzle.features.base import Feature
    from sparc_agi.puzzle_spec.slot import CacheItemSpec

@dataclass
class PuzzleCacheSlot:
    spec: CacheItemSpec
    value: Feature

@dataclass
class SampleCacheSlot:
    spec: CacheItemSpec
    values: list[Feature] = field(default_factory=list)

CacheSlot = PuzzleCacheSlot | SampleCacheSlot
