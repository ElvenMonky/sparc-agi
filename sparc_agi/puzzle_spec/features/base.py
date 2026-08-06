from dataclasses import dataclass
from typing import Callable, ClassVar, TypeVar

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
    pass
