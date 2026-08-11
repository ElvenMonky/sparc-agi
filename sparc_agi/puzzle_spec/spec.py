import random
from dataclasses import dataclass, field

from sparc_agi.puzzle.puzzle import Puzzle
from sparc_agi.puzzle_spec.features.base import FeatureSpec
from sparc_agi.puzzle_spec.features.object import ObjectSpec, with_article
from sparc_agi.puzzle_spec.palette import PaletteSpec
from sparc_agi.puzzle_spec.range import Range
from sparc_agi.puzzle_spec.slot import CacheItemSpec, FeatureSlotSpec
from sparc_agi.puzzle_spec.transformations.base import TransformationSpec
from sparc_agi.puzzle_spec.validate import (
    trace_step_outputs,
    validate_filter_wires,
    validate_linked_mappings,
    validate_step_wires,
)

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
    step_outputs: list[FeatureSpec] = field(init=False, default_factory=list)

    def __post_init__(self) -> None:
        self.step_outputs = trace_step_outputs(self)
        validate_linked_mappings(self)
        validate_step_wires(self)
        validate_filter_wires(self)

    def instantiate(self, rng: random.Random | None = None):
        palette = self.palette.instantiate(rng or random.Random())
        puzzle = Puzzle(spec=self, palette=palette, input="", steps=())
        body = self.input.value.describe(puzzle)
        if not body.startswith(("a ", "an ")):
            body = with_article(body)
        puzzle.input = f"Puzzle input consists of {body}."
        return puzzle
