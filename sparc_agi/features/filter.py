from dataclasses import dataclass, field
from typing import Any

from sparc_agi.features.base import FeatureSpec, register_feature

@register_feature("filter")
@dataclass
class FilterSpec(FeatureSpec):
    index: int | str | None = None
    criteria: list[str] = field(default_factory=list)
    values: dict[str, Any] = field(default_factory=dict)
