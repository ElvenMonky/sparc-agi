import importlib
import pkgutil

from sparc_agi.puzzle_spec.features.base import ColorSpec, FeatureSpec, FilterSpec, register_feature
from sparc_agi.puzzle_spec.features.layout import LayoutSpec, SizeSpec
from sparc_agi.puzzle_spec.features.mapping import ColorMappingSpec, MappingSpec
from sparc_agi.puzzle_spec.features.margin import MarginSpec
from sparc_agi.puzzle_spec.features.object import GlyphSpec, GroupSpec, ObjectSpec, SpriteSpec

for module in pkgutil.walk_packages(__path__, prefix=f"{__name__}."):
    importlib.import_module(module.name)

__all__ = [
    "ColorMappingSpec",
    "ColorSpec",
    "FeatureSpec",
    "FilterSpec",
    "GlyphSpec",
    "GroupSpec",
    "LayoutSpec",
    "MappingSpec",
    "MarginSpec",
    "ObjectSpec",
    "SizeSpec",
    "SpriteSpec",
    "register_feature",
]
