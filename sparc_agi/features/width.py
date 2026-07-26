from dataclasses import dataclass

from sparc_agi.features.base import Feature, register_feature


@register_feature("width", scalar=True)
@dataclass
class Width(Feature):
    value: int
