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
