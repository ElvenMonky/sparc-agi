from dataclasses import MISSING, Field, dataclass, field, fields
from enum import IntFlag
from typing import Any, Callable, ClassVar, Self, TypeVar

import cattrs

ACCESS_KEY = "access"

class Access(IntFlag):
    GET = 1
    SET = 2
    RW = GET | SET

def trait(
    default: Any = MISSING,
    default_factory: Any = MISSING,
    *,
    access: Access = Access.RW,
    **kwargs: Any,
) -> Any:
    metadata = dict(kwargs.pop("metadata", {}))
    metadata[ACCESS_KEY] = access
    if default is not MISSING:
        return field(default=default, metadata=metadata, **kwargs)
    if default_factory is not MISSING:
        return field(default_factory=default_factory, metadata=metadata, **kwargs)
    return field(metadata=metadata, **kwargs)

def _field_default_value(dc_field: Field[Any]) -> Any:
    if dc_field.default is not MISSING:
        return dc_field.default
    if dc_field.default_factory is not MISSING:
        return dc_field.default_factory()
    return MISSING

def _omit_if_default(converter: cattrs.Converter, dc_field: Field[Any], val: Any) -> bool:
    if not converter.omit_if_default:
        return False
    default = _field_default_value(dc_field)
    if default is MISSING:
        return False
    return val == default

@dataclass
class FeatureSpec:
    REGISTRY: ClassVar[dict[str, type[Self]]] = {}

    @classmethod
    def tag(cls) -> str:
        for name, registered in FeatureSpec.REGISTRY.items():
            if registered is cls:
                return name
        raise ValueError(f"{cls.__name__} is not registered")

    @classmethod
    def trait_accesses(cls) -> dict[str, Access]:
        return {
            dc_field.name: dc_field.metadata[ACCESS_KEY]
            for dc_field in fields(cls)
            if ACCESS_KEY in dc_field.metadata
        }

    @classmethod
    def gettable_traits(cls) -> frozenset[str]:
        return frozenset(
            name for name, access in cls.trait_accesses().items() if access & Access.GET
        )

    @classmethod
    def settable_traits(cls) -> frozenset[str]:
        return frozenset(
            name for name, access in cls.trait_accesses().items() if access & Access.SET
        )

    @classmethod
    def unstructure(cls, inst: Self, converter: cattrs.Converter) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        for dc_field in fields(cls):
            if ACCESS_KEY in dc_field.metadata:
                if not (dc_field.metadata[ACCESS_KEY] & Access.SET):
                    continue
            val = getattr(inst, dc_field.name)
            if val is None:
                continue
            if _omit_if_default(converter, dc_field, val):
                continue
            payload[dc_field.name] = converter.unstructure(val)
        return payload

F = TypeVar("F", bound=FeatureSpec)

def register_feature(name: str) -> Callable[[type[F]], type[F]]:
    def decorator(cls: type[F]) -> type[F]:
        if not issubclass(cls, FeatureSpec):
            raise TypeError(f"{cls.__name__} must subclass FeatureSpec")
        if name in FeatureSpec.REGISTRY:
            raise ValueError(f"feature {name!r} already registered as {FeatureSpec.REGISTRY[name].__name__}")
        FeatureSpec.REGISTRY[name] = cls
        return cls
    return decorator

@register_feature("filter")
@dataclass
class FilterSpec(FeatureSpec):
    index: list[int] = field(default_factory=list)
    criteria: list[str] = field(default_factory=list)
