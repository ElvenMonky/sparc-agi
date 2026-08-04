from dataclasses import dataclass, fields
from typing import Any, Callable, ClassVar, TypeVar

F = TypeVar("F", bound="FeatureSpec")

@dataclass
class FeatureSpec:
    REGISTRY: ClassVar[dict[str, type["FeatureSpec"]]] = {}

    @classmethod
    def tag(cls) -> str:
        for name, registered in FeatureSpec.REGISTRY.items():
            if registered is cls:
                return name
        raise ValueError(f"{cls.__name__} is not registered")

    @classmethod
    def structure(cls, value: Any, expected: type) -> "FeatureSpec":
        if isinstance(value, expected):
            return value
        if not isinstance(value, dict) or len(value) != 1:
            raise ValueError(f"feature must be a single-key tagged object, got {value!r}")
        ((tag, payload),) = value.items()
        try:
            feature_cls = FeatureSpec.REGISTRY[tag]
        except KeyError as exc:
            known = ", ".join(sorted(FeatureSpec.REGISTRY)) or "(none)"
            raise ValueError(f"unknown feature {tag!r}; registered: {known}") from exc
        if not issubclass(feature_cls, expected):
            raise ValueError(
                f"feature {tag!r} is {feature_cls.__name__}, expected {expected.__name__}"
            )
        if payload is None:
            payload = {}
        if not isinstance(payload, dict):
            return feature_cls()
        names = {f.name for f in fields(feature_cls)}
        return feature_cls(**{key: value for key, value in payload.items() if key in names})

    def unstructure(self) -> dict[str, Any]:
        payload = {
            f.name: getattr(self, f.name)
            for f in fields(type(self))
            if getattr(self, f.name) is not None
        }
        return {type(self).tag(): payload}

def register_feature(name: str) -> Callable[[type[F]], type[F]]:
    def decorator(cls: type[F]) -> type[F]:
        if not issubclass(cls, FeatureSpec):
            raise TypeError(f"{cls.__name__} must subclass FeatureSpec")
        if name in FeatureSpec.REGISTRY:
            raise ValueError(f"feature {name!r} already registered as {FeatureSpec.REGISTRY[name].__name__}")
        FeatureSpec.REGISTRY[name] = cls
        return cls
    return decorator

@register_feature("object")
@dataclass
class ObjectSpec(FeatureSpec):
    pass

@register_feature("object.sprite")
@dataclass
class SpriteSpec(ObjectSpec):
    pass

@register_feature("object.glyph")
@dataclass
class GlyphSpec(ObjectSpec):
    pass

@register_feature("object.group")
@dataclass
class GroupSpec(ObjectSpec):
    pass

@register_feature("orientation")
@dataclass
class OrientationSpec(FeatureSpec):
    pass

@register_feature("filter")
@dataclass
class FilterSpec(FeatureSpec):
    pass

@register_feature("color")
@dataclass
class ColorSpec(FeatureSpec):
    pass

@register_feature("layout")
@dataclass
class LayoutSpec(FeatureSpec):
    pass

@register_feature("layout.grid")
@dataclass
class GridLayoutSpec(LayoutSpec):
    pass

@register_feature("mapping")
@dataclass
class MappingSpec(FeatureSpec):
    pass

@register_feature("mapping.color")
@dataclass
class ColorMappingSpec(MappingSpec):
    pass
