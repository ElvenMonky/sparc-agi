"""Composite of width/height features.

In the bible, size is nested as bare scalar payloads under field names that
match the feature tags::

    "size": { "width": 3, "height": 3 }

Top-level cache/input entries can still use the tagged feature form
``{ "width": 3 }`` / ``{ "height": 3 }``.
"""

from dataclasses import dataclass

from sparc_agi.features.height import Height
from sparc_agi.features.width import Width


@dataclass
class Size:
    width: Width
    height: Height

    def describe(self) -> str:
        w, h = self.width.value, self.height.value
        if w.lo == w.hi and h.lo == h.hi and w.step == h.step == 1:
            return f"{w.lo}x{h.lo}"
        return f"{self.width.describe()} × {self.height.describe()}"
