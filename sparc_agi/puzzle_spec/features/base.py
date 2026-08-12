from dataclasses import MISSING, Field, dataclass, field, fields
from enum import IntFlag
from typing import Any, Callable, ClassVar, Self, TypeVar, get_args

import cattrs

from sparc_agi.puzzle.puzzle import Puzzle
from sparc_agi.puzzle_spec.range import Range

ACCESS_KEY = "access"

def with_article(phrase: str) -> str:
    if phrase[:1].lower() in "aeiou":
        return f"an {phrase}"
    return f"a {phrase}"

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

def _follow_trait(value: Any) -> Any:
    if isinstance(value, FeatureSpec):
        return value
    inner = getattr(value, "value", None)
    if isinstance(inner, FeatureSpec):
        return inner
    return value

@dataclass(kw_only=True)
class FeatureSpec:
    REGISTRY: ClassVar[dict[str, type[Self]]] = {}
    alias: str | None = field(default=None, compare=False, repr=False)

    @classmethod
    def tag(cls) -> str:
        for name, registered in FeatureSpec.REGISTRY.items():
            if registered is cls:
                return name
        raise ValueError(f"{cls.__name__} is not registered")

    @staticmethod
    def is_feature(typ: Any) -> bool:
        return isinstance(typ, type) and issubclass(typ, FeatureSpec)

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
    def has_trait_access(cls, path: str, access: Access) -> bool:
        parts = path.split(".")
        spec_cls: type[FeatureSpec] = cls
        for index, part in enumerate(parts):
            accesses = spec_cls.trait_accesses()
            if part not in accesses:
                return False
            if index == len(parts) - 1:
                return bool(accesses[part] & access)
            nested: type[FeatureSpec] | None = None
            for dc_field in fields(spec_cls):
                if dc_field.name != part:
                    continue
                hint = dc_field.type
                args = get_args(hint)
                if args and type(None) in args:
                    hint = next(arg for arg in args if arg is not type(None))
                if cls.is_feature(hint):
                    nested = hint
                else:
                    inner_args = get_args(hint)
                    if inner_args and cls.is_feature(inner_args[0]):
                        nested = inner_args[0]
                    elif isinstance(hint, type) and hasattr(hint, "_value_type"):
                        inner = hint._value_type()
                        if cls.is_feature(inner):
                            nested = inner
                break
            if nested is None:
                return False
            spec_cls = nested
        return False

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

    def get_trait(self, path: str) -> FeatureSpec | None:
        current: Any = self
        for part in path.split("."):
            if current is None:
                return None
            value = getattr(current, part, None)
            if value is None:
                return None
            current = _follow_trait(value)
        return current if isinstance(current, FeatureSpec) else None

    def set_trait(self, path: str, feature: FeatureSpec) -> None:
        current: Any = self
        *prefix, leaf = path.split(".")
        for part in prefix:
            value = getattr(current, part)
            current = _follow_trait(value)
        slot = getattr(current, leaf)
        if isinstance(slot, FeatureSpec):
            setattr(current, leaf, feature)
        else:
            slot.value = feature

    def refer(self, ctx: Puzzle) -> str:
        return self.alias or self.describe(ctx)

    def describe(self, ctx: Puzzle) -> str:
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
        if not FeatureSpec.is_feature(cls):
            raise TypeError(f"{cls.__name__} must subclass FeatureSpec")
        if name in FeatureSpec.REGISTRY:
            raise ValueError(f"feature {name!r} already registered as {FeatureSpec.REGISTRY[name].__name__}")
        FeatureSpec.REGISTRY[name] = cls
        return cls
    return decorator
