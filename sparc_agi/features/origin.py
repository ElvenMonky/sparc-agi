from dataclasses import dataclass

from sparc_agi.features.scalars.color import ColorSpec
from sparc_agi.range import Range

@dataclass
class Origin:
    x: Range | None = None
    y: Range | None = None
    color: ColorSpec | None = None
