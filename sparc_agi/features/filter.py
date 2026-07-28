"""Object filter: match pool items by optional kind and/or color."""

import random
from dataclasses import dataclass
from typing import Any

from sparc_agi.features.base import Feature, register_feature
from sparc_agi.features.scalars.color import Color
from sparc_agi.features.objects.base import Object


@register_feature("filter")
@dataclass
class Filter(Feature):
    """Selection criteria for :class:`~sparc_agi.transformations.pick_object.PickObject`.

    JSON::

        { "filter": { "color": 1, "kind": "glyph" } }
        { "filter": {} }   # match-all (must uniquely identify one pool item)
    """

    color: Color | None = None
    kind: str | None = None

    def describe(self) -> str:
        if self.kind is not None and self.color is not None:
            return f"{self.color.describe()} {self.kind}"
        if self.kind is not None:
            return self.kind
        if self.color is not None:
            return f"{self.color.describe()} object"
        return "any object"

    def matches(self, obj: Object) -> bool:
        """True if ``obj`` satisfies every set criterion."""
        if self.kind is not None and obj.kind_noun() != self.kind:
            return False
        if self.color is not None:
            if not obj.has_trait("color"):
                return False
            obj_color: Color = obj.color
            # Exact range match (filters use concrete colors in practice).
            if obj_color.value != self.color.value:
                return False
        return True

    def instantiate(self, rng: random.Random) -> dict[str, Any]:
        del rng
        out: dict[str, Any] = {}
        if self.color is not None:
            # Filters are criteria, not samples — keep the exact range endpoint(s).
            out["color"] = self.color.value.to_raw()
        if self.kind is not None:
            out["kind"] = self.kind
        return out
