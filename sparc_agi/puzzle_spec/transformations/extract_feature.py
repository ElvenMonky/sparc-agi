from dataclasses import dataclass
from typing import ClassVar

from sparc_agi.puzzle.puzzle import Puzzle
from sparc_agi.puzzle_spec.features.arrangement import ArrangementSpec
from sparc_agi.puzzle_spec.features.base import FeatureSpec
from sparc_agi.puzzle_spec.features.object import ObjectSpec
from sparc_agi.puzzle_spec.transformations.base import TransformationSpec, register_transformation
from sparc_agi.puzzle_spec.wire import WireRef

@dataclass
class ExtractFeatureSpec[Output: FeatureSpec](TransformationSpec[Output]):
    object: WireRef[ObjectSpec]
    trait: ClassVar[str]

    @classmethod
    def trace(cls, object: ObjectSpec) -> Output:
        slot = getattr(object, cls.trait, None)
        if slot is None:
            raise ValueError(f"{type(object).tag()} has no {cls.trait!r} to extract")
        return slot.value

    def alias_stem(self, *, object: ObjectSpec) -> str:
        return "extracted "

    def describe(self, ctx: Puzzle, *, object: ObjectSpec) -> str:
        return f"Extract {type(self).trait} from {object.refer(ctx)}."

@register_transformation("ExtractArrangement")
@dataclass
class ExtractArrangementSpec(ExtractFeatureSpec[ArrangementSpec]):
    trait = "arrangement"
