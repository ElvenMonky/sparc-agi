import random
from dataclasses import dataclass, fields
from typing import Any, Generic, Literal, Self, get_args, get_origin

import cattrs

from sparc_agi.puzzle.slot import PuzzleCacheSlot, SampleCacheSlot
from sparc_agi.puzzle_spec.features.base import F, FeatureSpec, _omit_if_default

@dataclass
class FeatureSlotSpec(Generic[F]):
    value: F

    @classmethod
    def _value_type(cls) -> type[FeatureSpec]:
        for base in cls.__orig_bases__:
            if get_origin(base) is FeatureSlotSpec:
                value_type = get_args(base)[0]
                if isinstance(value_type, type):
                    return value_type
        raise TypeError(f"{cls.__name__} must specialize FeatureSlotSpec[FeatureSpec]")

    @classmethod
    def structure(cls, value: Any, _: type, converter: cattrs.Converter) -> Self:
        if isinstance(value, cls):
            return value
        if not isinstance(value, dict):
            raise ValueError(f"{cls.__name__} must be an object, got {value!r}")
        kwargs: dict[str, Any] = {}
        for dc_field in fields(cls):
            if dc_field.name == "value":
                continue
            raw = value.get(dc_field.name)
            if raw is not None:
                kwargs[dc_field.name] = converter.structure(raw, dc_field.type)
        body = [key for key in value if key not in kwargs]
        if len(body) != 1:
            raise ValueError(f"slot must be a single-key tagged object, got {body!r}")
        tag = body[0]
        feature_cls = FeatureSpec.REGISTRY.get(tag)
        if feature_cls is None or not issubclass(feature_cls, cls._value_type()):
            raise ValueError(f"unknown or incompatible feature {tag!r}")
        return cls(value=converter.structure(value[tag], feature_cls), **kwargs)

    @classmethod
    def unstructure(cls, inst: Self, converter: cattrs.Converter) -> dict[str, Any]:
        payload = {type(inst.value).tag(): converter.unstructure(inst.value)}
        for dc_field in fields(cls):
            if dc_field.name == "value":
                continue
            val = getattr(inst, dc_field.name)
            if val is None:
                continue
            if _omit_if_default(converter, dc_field, val):
                continue
            payload[dc_field.name] = converter.unstructure(val)
        return payload

@dataclass
class CacheItemSpec(FeatureSlotSpec[FeatureSpec]):
    scope: Literal["puzzle", "sample"] = "puzzle"

    def instantiate(self, rng: random.Random) -> PuzzleCacheSlot | SampleCacheSlot:
        if self.scope == "sample":
            return SampleCacheSlot(spec=self)
        return PuzzleCacheSlot(spec=self, value=self.value.instantiate(rng))
