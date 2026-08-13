from dataclasses import dataclass, field
from typing import ClassVar

from sparc_agi.puzzle.features.base import Filter
from sparc_agi.puzzle.puzzle import Puzzle
from sparc_agi.puzzle_spec.features.arrangement import ArrangementSpec
from sparc_agi.puzzle_spec.features.base import Access, FeatureSpec
from sparc_agi.puzzle_spec.features.filter import FilterSpec
from sparc_agi.puzzle_spec.features.object import ObjectSpec
from sparc_agi.puzzle_spec.transformations.base import TransformationSpec, register_transformation
from sparc_agi.puzzle_spec.wire import WireRef

@dataclass
class ExtractFeatureSpec[Output: FeatureSpec](TransformationSpec[Output]):
    object: WireRef[ObjectSpec]
    filter: WireRef[FilterSpec] = field(default=None)
    trait: ClassVar[str]

    @classmethod
    def trace(cls, object: ObjectSpec, filter: FilterSpec) -> Output:
        target = filter.target(object)
        type(target).validate_trait_access(cls.trait, Access.GET)
        feature = target.get_trait(cls.trait)
        if feature is None:
            raise ValueError(f"{type(target).tag()} has no {cls.trait!r} to extract")
        return feature

    def alias_stem(self, *, object: ObjectSpec, filter: FilterSpec) -> str:
        return "extracted "

    def describe(
        self,
        ctx: Puzzle,
        *,
        object: ObjectSpec,
        filter: FilterSpec | Filter,
    ) -> str:
        return f"Extract {type(self).trait} from {filter.spec.refer_target(ctx, object)}."

@register_transformation("ExtractArrangement")
@dataclass
class ExtractArrangementSpec(ExtractFeatureSpec[ArrangementSpec]):
    trait = "arrangement"
