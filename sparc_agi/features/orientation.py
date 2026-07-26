from dataclasses import dataclass

from sparc_agi.features.base import Feature, register_feature


@register_feature("orientation", scalar=True)
@dataclass
class Orientation(Feature):
    value: int
