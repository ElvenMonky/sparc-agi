from dataclasses import dataclass
from typing import Any

from sparc_agi.puzzle_spec.features.base import FeatureSpec

@dataclass
class CacheItem:
    value: FeatureSpec
    scope: str | None = None

    @classmethod
    def structure(cls, value: Any, _: type) -> "CacheItem":
        if isinstance(value, CacheItem):
            return value
        if not isinstance(value, dict):
            raise ValueError(f"cache item must be an object, got {value!r}")
        feature_keys = [key for key in value if key in FeatureSpec.REGISTRY]
        if len(feature_keys) != 1:
            raise ValueError(
                f"cache item must contain exactly one feature tag, got {value!r}"
            )
        tag = feature_keys[0]
        extra = set(value) - {tag, "scope"}
        if extra:
            raise ValueError(f"unknown cache item fields: {sorted(extra)}")
        scope = value.get("scope")
        if scope is not None and not isinstance(scope, str):
            raise ValueError(f"cache item scope must be a string, got {scope!r}")
        return cls(
            value=FeatureSpec.structure({tag: value[tag]}, FeatureSpec),
            scope=scope,
        )

    def unstructure(self) -> dict[str, Any]:
        payload = dict(self.value.unstructure())
        if self.scope is not None:
            return {"scope": self.scope, **payload}
        return payload
