import random
from dataclasses import dataclass, field

from sparc_agi.puzzle_spec.context import PuzzleContext
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
class PuzzleDescription:
    ctx: PuzzleContext
    input: str
    steps: list[str] = field(default_factory=list)

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

    def describe(self, rng: random.Random | None = None) -> PuzzleDescription:
        ctx = PuzzleContext(
            palette=self.palette.instantiate(rng or random.Random()),
            step_outputs=tuple(self.step_outputs),
        )
        body = self.input.value.describe(ctx)
        if not body.startswith(("a ", "an ")):
            body = with_article(body)
        return PuzzleDescription(
            ctx=ctx,
            input=f"Puzzle input consists of {body}.",
        )
