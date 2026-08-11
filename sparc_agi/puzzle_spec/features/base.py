from dataclasses import MISSING, Field, dataclass, field, fields
from enum import IntFlag
from typing import Any, Callable, ClassVar, Self, TypeVar

import cattrs

from sparc_agi.puzzle_spec.context import PuzzleContext
from sparc_agi.puzzle_spec.range import Range

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

    @staticmethod
    def is_plural(count: Range | int | None) -> bool:
        if count is None:
            return False
        if isinstance(count, Range):
            return not (count.lo == count.hi == 1)
        return count != 1

    def kind_noun(self, count: Range | int | None = None) -> str:
        noun = type(self).tag().rsplit(".", 1)[-1].replace("_", " ")
        if count is None:
            return noun
        if not self.is_plural(count):
            return noun
        return f"{noun}es" if noun.endswith("s") else f"{noun}s"

    def is_default(self, field_name: str) -> bool:
        for dc_field in fields(self):
            if dc_field.name != field_name:
                continue
            val = getattr(self, dc_field.name)
            if dc_field.default_factory is not MISSING:
                return val == dc_field.default_factory()
            if dc_field.default is not MISSING:
                return val == dc_field.default
            return False
        raise AttributeError(f"{type(self).__name__} has no field {field_name!r}")

    def describe(self, ctx: PuzzleContext) -> str:
        return type(self).tag()

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
