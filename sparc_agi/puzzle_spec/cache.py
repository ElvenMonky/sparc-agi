from dataclasses import dataclass, fields
from typing import Any, Self

import cattrs

from sparc_agi.puzzle_spec.features.base import FeatureSpec
from sparc_agi.puzzle_spec.range import Range

@dataclass
class InputSpec:
    value: FeatureSpec

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
            raise ValueError(f"input must be a single-key tagged object, got {body!r}")
        tag = body[0]
        feature_cls = FeatureSpec.REGISTRY.get(tag)
        if feature_cls is None:
            raise ValueError(f"unknown feature {tag!r}")
        return cls(value=converter.structure(value[tag], feature_cls), **kwargs)

    @classmethod
    def unstructure(cls, inst: InputSpec, converter: cattrs.Converter) -> dict[str, Any]:
        payload = {type(inst.value).tag(): converter.unstructure(inst.value)}
        for field in fields(cls):
            if field.name == "value":
                continue
            val = getattr(inst, field.name)
            if val is not None:
                payload[field.name] = converter.unstructure(val)
        return payload

@dataclass
class CacheItemSpec(InputSpec):
    scope: str | None = None

@dataclass
class PoolItemSpec(InputSpec):
    variants: Range | None = None
