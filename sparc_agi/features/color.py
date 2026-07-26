from dataclasses import dataclass

from sparc_agi.features.base import Feature, register_feature
from sparc_agi.features.range import Range


@register_feature("color", scalar=True)
@dataclass
class Color(Feature):
    value: Range
