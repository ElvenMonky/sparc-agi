from dataclasses import dataclass

from sparc_agi.features.base import Feature, register_feature
from sparc_agi.features.size import Size


@register_feature("object.sprite")
@dataclass
class Sprite(Feature):
    size: Size
