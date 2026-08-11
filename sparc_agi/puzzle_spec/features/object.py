from dataclasses import dataclass, field

from sparc_agi.consts import MAX_COLOR, MAX_COUNT
from sparc_agi.puzzle_spec.context import PuzzleContext
from sparc_agi.puzzle_spec.features.base import Access, FeatureSpec, register_feature, trait
from sparc_agi.puzzle_spec.features.cut import CutSpec
from sparc_agi.puzzle_spec.features.arrangement import (
    ArrangementSlotSpec,
    ArrangementSpec,
    GridArrangementSpec,
    OriginSpec,
    SizeSpec,
    TreeArrangementSpec,
)
from sparc_agi.puzzle_spec.features.pattern import PatternSlotSpec, PatternSpec
from sparc_agi.puzzle_spec.features.margin import MarginSpec, group_spacing_phrase
from sparc_agi.puzzle_spec.features.scalar import ColorSpec, CountSpec, HeightSpec, OrientationSpec, WidthSpec
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

    def describe(self, ctx: PuzzleContext) -> str:
        if phrase := self.color.describe(ctx):
            return f"{phrase} {self.kind_noun()}"
        return self.kind_noun()

@dataclass
class PoolItemSpec(FeatureSlotSpec[ObjectSpec]):
    value: ObjectSpec | None = None
    variants: Range[1, MAX_COUNT] | None = None

@register_feature("object.point")
@dataclass
class PointSpec(ObjectSpec):
    origin: OriginSpec | None = trait(access=Access.GET, default=None)
    size: SizeSpec = trait(
        access=Access.GET,
        default_factory=lambda: SizeSpec(width=WidthSpec(Range(1)), height=HeightSpec(Range(1))),
    )

@dataclass
class GeometrySpec(ObjectSpec):
    edge_color: ColorSpec | None = trait(default=None)
    vertice_color: ColorSpec | None = trait(default=None)

@register_feature("object.line")
@dataclass
class LineSpec(GeometrySpec):
    direction: OrientationSpec = trait(default_factory=lambda: OrientationSpec(Range(0)))

@register_feature("object.rectangle")
@dataclass
class RectangleSpec(GeometrySpec):
    cut: CutSpec = trait(default_factory=CutSpec)

    def describe(self, ctx: PuzzleContext) -> str:
        base = f"{self.size.describe(ctx)} rectangle" if not self.is_default("size") else "rectangle"
        if edge := self.edge_color:
            if color := edge.describe(ctx):
                base += f" with {color} edge"
            else:
                base += " with edge"
        if phrase := self.color.describe(ctx):
            return f"{phrase} {base}"
        return base

@dataclass
class BaseGroupSpec(ObjectSpec):
    pool: list[PoolItemSpec] = trait(access=Access.SET, default_factory=list)

@register_feature("object.group")
@dataclass
class GroupSpec(BaseGroupSpec):
    count: CountSpec = trait(default_factory=CountSpec)
    draft: PatternSpec | None = trait(default=None)

    def describe(self, ctx: PuzzleContext) -> str:
        count = self.count.value.describe()
        members = " and ".join(item.value.describe(ctx) for item in self.pool if item.value is not None)
        head = f"group of {count} {members}"
        if not self.is_default("size"):
            head += f" arranged randomly within {self.size.describe(ctx)} area"
        return head + group_spacing_phrase(self.margin, self.pool, ctx)

@register_feature("object.grid")
@dataclass
class GridSpec(BaseGroupSpec):
    arrangement: ArrangementSlotSpec = trait(default_factory=ArrangementSlotSpec(GridArrangementSpec()))
    pattern: PatternSlotSpec | None = trait(default=None)
    mask: PatternSpec | None = trait(access=Access.GET, default=None)

@register_feature("object.glyph")
@dataclass
class GlyphSpec(GridSpec):
    size: SizeSpec = trait(
        access=Access.GET,
        default_factory=lambda: SizeSpec(width=WidthSpec(Range(3)), height=HeightSpec(Range(3))),
    )
    arrangement: ArrangementSlotSpec = trait(
        access=Access.GET,
        default_factory=lambda: ArrangementSlotSpec(ArrangementSpec(count=CountSpec(Range(2, 8)))),
    )
    pool: list[PoolItemSpec] = trait(access=Access(0), default_factory=list)

    def __post_init__(self) -> None:
        self.arrangement.value.size = self.size
        self.pool = [PoolItemSpec(
            variants=Range(1),
            value=PointSpec(color=self.color),
        )]

@register_feature("object.sprite")
@dataclass
class SpriteSpec(BaseGroupSpec):
    color: ColorSpec = trait(
        access=Access.SET,
        default_factory=ColorSpec,
    )
    pool: list[PoolItemSpec] = trait(access=Access(0), default_factory=list)

    def __post_init__(self) -> None:
        value = self.color.value
        if value.lo < 0 or value.hi > MAX_COLOR:
            raise ValueError(f"sprite color must be in 0..{MAX_COLOR}, got {value.describe()}")
        if len(range(value.lo, value.hi + 1, value.step)) < 2:
            raise ValueError(f"sprite color must allow at least 2 colors, got {value.describe()}")
        self.pool = [PoolItemSpec(value=PointSpec(color=self.color))]

    def describe(self, ctx: PuzzleContext) -> str:
        if not self.is_default("size"):
            return f"{self.size.describe(ctx)} sprite"
        return "sprite"

@register_feature("object.tree_structure")
@dataclass
class TreeStructureSpec(BaseGroupSpec):
    count: CountSpec = trait(default_factory=CountSpec)
    arrangement: ArrangementSlotSpec = trait(
        access=Access.GET,
        default_factory=lambda: ArrangementSlotSpec(TreeArrangementSpec()),
    )
    pool: list[PoolItemSpec] = trait(access=Access.SET, default_factory=list)

    def __post_init__(self) -> None:
        self.arrangement.value.count = self.count
        if len(self.pool) == 0:
            self.pool = [PoolItemSpec(
                variants=Range(1),
                value=PointSpec(color=self.color),
            )]

    def kind_noun(self) -> str:
        return "tree structure"
