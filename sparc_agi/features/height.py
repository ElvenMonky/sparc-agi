from dataclasses import dataclass

from sparc_agi.features.base import Feature, register_feature


@register_feature("height", scalar=True)
@dataclass
class Height(Feature):
    value: int
