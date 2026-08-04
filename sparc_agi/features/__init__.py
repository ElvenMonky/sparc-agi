from sparc_agi.features.base import FEATURE_REGISTRY, Feature, FeatureSpec, feature_family, register_feature
from sparc_agi.features.scalars import Scalar, ScalarSpec, load_scalar_features
from sparc_agi.range import Range

load_scalar_features()

from sparc_agi.features.layouts import LayoutSpec
from sparc_agi.features.mappings import MappingSpec
from sparc_agi.features.patterns import PatternSpec
from sparc_agi.features.filter import FilterSpec
from sparc_agi.features.objects.group import GroupSpec
from sparc_agi.features.objects.glyph import GlyphSpec
from sparc_agi.features.objects.point import PointSpec
from sparc_agi.features.objects.rectangle import RectangleSpec
from sparc_agi.features.objects.sprite import SpriteSpec
from sparc_agi.features.objects.tree import TreeStructureSpec
from sparc_agi.features.scalars.size import Size

__all__ = [
    "FEATURE_REGISTRY",
    "Feature",
    "FeatureSpec",
    "FilterSpec",
    "GroupSpec",
    "GlyphSpec",
    "LayoutSpec",
    "MappingSpec",
    "PatternSpec",
    "PointSpec",
    "RectangleSpec",
    "Range",
    "Scalar",
    "ScalarSpec",
    "Size",
    "SpriteSpec",
    "TreeStructureSpec",
    "feature_family",
    "register_feature",
]
