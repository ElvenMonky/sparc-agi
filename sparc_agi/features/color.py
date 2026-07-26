from dataclasses import dataclass

from sparc_agi.features.base import Scalar, register_feature


@register_feature("color")
@dataclass
class Color(Scalar):
    pass
