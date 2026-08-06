from dataclasses import dataclass, fields
from typing import Any, Generic, Self, get_args, get_origin

import cattrs

from sparc_agi.puzzle_spec.features.base import F, FeatureSpec
from sparc_agi.puzzle_spec.features.object import ObjectSpec
from sparc_agi.puzzle_spec.range import Range

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
        for field in fields(cls):
            if field.name == "value":
                continue
            raw = value.get(field.name)
            kwargs[field.name] = None if raw is None else converter.structure(raw, field.type)
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
        for field in fields(cls):
            if field.name == "value":
                continue
            val = getattr(inst, field.name)
            if val is not None:
                payload[field.name] = converter.unstructure(val)
        return payload

@dataclass
class InputSpec(FeatureSlotSpec[ObjectSpec]):
    pass

@dataclass
class CacheItemSpec(FeatureSlotSpec[FeatureSpec]):
    scope: str | None = None

@dataclass
class PoolItemSpec(FeatureSlotSpec[ObjectSpec]):
    variants: Range[1, MAX_COUNT] | None = None
