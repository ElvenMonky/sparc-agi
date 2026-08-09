from dataclasses import dataclass, field

from sparc_agi.consts import MAX_SIZE
from sparc_agi.puzzle_spec.features.base import FeatureSpec, register_feature, trait
from sparc_agi.puzzle_spec.features.scalar import ColorSpec, CountSpec, HeightSpec, OrientationSpec, RatioSpec, WidthSpec
from sparc_agi.puzzle_spec.range import Range
from sparc_agi.puzzle_spec.slot import FeatureSlotSpec

@register_feature("size")
@dataclass
class SizeSpec(FeatureSpec):
    width: WidthSpec | None = trait(default=None)
    height: HeightSpec | None = trait(default=None)
    ratio: RatioSpec | None = trait(default=None)

@register_feature("position")
@dataclass
class PositionSpec(FeatureSpec):
    x: Range[0, MAX_SIZE - 1] = field(default_factory=lambda: Range(0, MAX_SIZE - 1))
    y: Range[0, MAX_SIZE - 1] = field(default_factory=lambda: Range(0, MAX_SIZE - 1))

@register_feature("origin")
@dataclass
class OriginSpec(PositionSpec):
    color: ColorSpec | None = trait(default=None)

@register_feature("arrangement")
@dataclass
class ArrangementSpec(FeatureSpec):
    pass

@register_feature("arrangement.flow")
@dataclass
class FlowArrangementSpec(ArrangementSpec):
    orientation: OrientationSpec = trait(default_factory=lambda: OrientationSpec(Range(0)))

@register_feature("arrangement.grid")
@dataclass
class GridArrangementSpec(ArrangementSpec):
    orientation: OrientationSpec = trait(default_factory=lambda: OrientationSpec(Range(0)))

@register_feature("arrangement.star")
@dataclass
class StarArrangementSpec(ArrangementSpec):
    origin: PositionSpec | None = trait(default=None)

@register_feature("arrangement.tree")
@dataclass
class TreeArrangementSpec(ArrangementSpec):
    origin: PositionSpec | None = trait(default=None)

@register_feature("draft")
@dataclass
class DraftSpec(FeatureSpec):
    prefix: list[int] = field(default_factory=list)
    pattern: list[int] = field(default_factory=list)

@register_feature("layout")
@dataclass
class LayoutSpec(FeatureSpec):
    count: CountSpec | None = trait(default=None)
    arrangement: FeatureSlotSpec[ArrangementSpec] | None = trait(default=None)
    size: SizeSpec | None = trait(default=None)
    pattern: DraftSpec | None = trait(default=None)