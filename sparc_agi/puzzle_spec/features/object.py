from dataclasses import dataclass, field

from sparc_agi.consts import MAX_COUNT
from sparc_agi.puzzle_spec.features.base import Access, FeatureSpec, register_feature, trait
from sparc_agi.puzzle_spec.features.cut import CutSpec
from sparc_agi.puzzle_spec.features.layout import (
    DraftSpec,
    LayoutSpec,
    SizeSpec,
    TreeArrangementSpec,
)
from sparc_agi.puzzle_spec.features.margin import MarginSpec
from sparc_agi.puzzle_spec.features.scalar import ColorSpec, CountSpec, HeightSpec, WidthSpec
from sparc_agi.puzzle_spec.range import Range
from sparc_agi.puzzle_spec.slot import FeatureSlotSpec

@register_feature("object")
@dataclass
class ObjectSpec(FeatureSpec):
    color: ColorSpec = trait(default_factory=ColorSpec)
    margin: MarginSpec = trait(default_factory=MarginSpec)
    origin: PositionSpec | None = trait(default=None)
    size: SizeSpec = trait(default_factory=SizeSpec)

@dataclass
class PoolItemSpec(FeatureSlotSpec[ObjectSpec]):
    variants: Range[1, MAX_COUNT] | None = None
    mapping: str | None = None

@register_feature("object.point")
@dataclass
class PointSpec(ObjectSpec):
    origin: PositionSpec = trait(access=Access.GET, default=None)
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

@dataclass
class BaseGroupSpec(ObjectSpec):
    pool: list[PoolItemSpec] = field(default_factory=list)

@register_feature("object.group")
@dataclass
class GroupSpec(BaseGroupSpec):
    count: CountSpec = trait(default_factory=CountSpec)
    draft: DraftSpec | None = trait(default=None)

@register_feature("object.grid")
@dataclass
class GridSpec(BaseGroupSpec):
    layout: LayoutSpec = trait(default_factory=LayoutSpec)

@register_feature("object.glyph")
@dataclass
class GlyphSpec(GridSpec):
    size: SizeSpec = trait(
        access=Access.GET,
        default_factory=lambda: SizeSpec(width=WidthSpec(Range(3)), height=HeightSpec(Range(3))),
    )
    layout: LayoutSpec = trait(
        access=Access.GET,
        default_factory=lambda: LayoutSpec(count=CountSpec(Range(2, 8))),
    )
    pool: list[PoolItemSpec] = field(
        default_factory=list
    )

    def __post_init__(self) -> None:
        self.layout.size = self.size
        self.pool = [PoolItemSpec(
            variants=Range(1),
            value=PointSpec(color=self.color)
        )]

@register_feature("object.sprite")
@dataclass
class SpriteSpec(GridSpec):
    layout: LayoutSpec = trait(
        access=Access.GET,
        default_factory=lambda: LayoutSpec(arrangement=FeatureSlotSpec(GridArrangementSpec())),
    )
    pool: list[PoolItemSpec] = field(
        default_factory=list
    )

    def __post_init__(self) -> None:
        self.layout.size = self.size
        self.pool = [PoolItemSpec(
            value=PointSpec(color=self.color)
        )]

@register_feature("object.tree_structure")
@dataclass
class TreeStructureSpec(BaseGroupSpec):
    count: CountSpec = trait(default_factory=CountSpec)
    layout: LayoutSpec = trait(
        access=Access.GET,
        default_factory=lambda: LayoutSpec(arrangement=FeatureSlotSpec(TreeArrangementSpec())),
    )

    def __post_init__(self) -> None:
        self.layout.count = self.count
