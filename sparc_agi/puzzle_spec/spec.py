from dataclasses import dataclass, field

from sparc_agi.puzzle_spec.features.object import ObjectSpec
from sparc_agi.puzzle_spec.palette import PaletteSpec
from sparc_agi.puzzle_spec.range import Range
from sparc_agi.puzzle_spec.slot import CacheItemSpec, FeatureSlotSpec
from sparc_agi.puzzle_spec.transformations.base import TransformationSpec
from sparc_agi.puzzle_spec.validate import validate_linked_mappings, validate_step_wires

@dataclass
class InputSpec(FeatureSlotSpec[ObjectSpec]):
    pass

@dataclass
class SamplesSpec:
    train: Range[2, 5]
    test: Range[1, 3]

@dataclass
class PuzzleSpec:
    input: InputSpec
    samples: SamplesSpec
    steps: list[TransformationSpec]
    cache: dict[str, CacheItemSpec] = field(default_factory=dict)
    palette: PaletteSpec = field(default_factory=PaletteSpec)

    def __post_init__(self) -> None:
        validate_linked_mappings(self)
        validate_step_wires(self)
