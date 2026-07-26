from dataclasses import dataclass

from sparc_agi.features.base import Feature, Sequence, register_feature
from sparc_agi.features.size import Size


@register_feature("arrangement.grid")
@dataclass
class GridArrangement(Feature):
    size: Size
    sequence: Sequence
    orientation: int = 0
