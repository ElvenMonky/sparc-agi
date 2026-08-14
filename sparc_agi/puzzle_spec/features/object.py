import random
from dataclasses import dataclass, field

from sparc_agi.consts import MAX_COLOR, MAX_COUNT
from sparc_agi.puzzle.features.base import Geometry
from sparc_agi.puzzle.puzzle import Puzzle
from sparc_agi.puzzle_spec.features.base import FeatureSpec, register_feature, trait, with_article
from sparc_agi.puzzle_spec.features.arrangement import OriginSpec, SizeSpec
from sparc_agi.puzzle_spec.features.margin import MarginSpec
from sparc_agi.puzzle_spec.features.scalar import ColorSpec, OrientationSpec
from sparc_agi.puzzle_spec.range import Range
from sparc_agi.puzzle_spec.slot import FeatureSlotSpec

@register_feature("object")
@dataclass
class ObjectSpec(FeatureSpec):
    color: ColorSpec = trait(default_factory=lambda: ColorSpec(value=Range(1, MAX_COLOR)))
    margin: MarginSpec = trait(default_factory=MarginSpec)
    orientation: OrientationSpec | None = trait(default=None)
    origin: OriginSpec | None = trait(default=None)
    size: SizeSpec = trait(default_factory=SizeSpec)
    linked_mappings: list[str] = field(default_factory=list)

    def describe_head(
        self,
        ctx: Puzzle,
        *,
        count: Range | int | None = None,
        article: bool = False,
    ) -> str:
        head = self.kind_noun(count)
        if size := self.size.describe(ctx):
            head = f"{size} {head}"
        if phrase := self.color.describe(ctx):
            head = f"{phrase} {head}"
        if article:
            head = with_article(head)
        return head

    def describe_tail(self, ctx: Puzzle) -> str:
        if self.origin is not None:
            return self.origin.describe(ctx)
        return ""

    def describe(self, ctx: Puzzle, *, count: Range | int | None = None, article: bool = False) -> str:
        return self.describe_head(ctx, count=count, article=article) + self.describe_tail(ctx)

    def instantiate(self, rng: random.Random) -> Geometry:
        del rng
        return Geometry(spec=self, bbox=(0, 0, 0, 0), grid=[], children=[])

@dataclass
class PoolItemSpec(FeatureSlotSpec[ObjectSpec]):
    value: ObjectSpec | None = None
    variants: Range[1, MAX_COUNT] | None = None
