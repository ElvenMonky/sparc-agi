from dataclasses import dataclass

from sparc_agi.puzzle_spec.features.base import FeatureSpec, register_feature, trait
from sparc_agi.puzzle_spec.features.layout import LayoutSpec
from sparc_agi.puzzle_spec.features.margin import MarginSpec

@register_feature("object")
@dataclass
class ObjectSpec(FeatureSpec):
    margin: MarginSpec = trait(default_factory=MarginSpec)
    layout: LayoutSpec | None = trait(default=None)

@register_feature("object.sprite")
@dataclass
class SpriteSpec(ObjectSpec):
    pass

@register_feature("object.glyph")
@dataclass
class GlyphSpec(ObjectSpec):
    pass

@register_feature("object.group")
@dataclass
class GroupSpec(ObjectSpec):
    pass
