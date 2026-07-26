from dataclasses import dataclass

from sparc_agi.features.base import Feature, register_feature
from sparc_agi.features.range import Range


@register_feature("count", scalar=True)
@dataclass
class Count(Feature):
    value: Range
