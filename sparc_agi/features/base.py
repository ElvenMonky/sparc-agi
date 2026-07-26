"""Feature registry and shared nested value types.

Feature specs in the bible are single-key tagged objects::

    { "<feature.name>": <payload> }

The tag is ``<family>`` or ``<family>.<kind>``. The family (part before the
dot) is what transformations match on; kinds are interchangeable in a slot
that expects that family (e.g. ``object.sprite`` satisfies an ``object`` slot).

Register a new feature with ``@register_feature("feature.name")``. If
``scalar=True``, a non-dict payload is wrapped into the dataclass's single
field (e.g. ``{ "orientation": 12 }`` → ``Orientation(value=12)``).
"""

from dataclasses import dataclass, fields
from typing import Callable, ClassVar, TypeVar

F = TypeVar("F", bound="Feature")

FEATURE_REGISTRY: dict[str, type[Feature]] = {}


def feature_family(name: str) -> str:
    """Return the feature family for a registry tag (``arrangement.grid`` → ``arrangement``)."""
    return name.split(".", 1)[0]


@dataclass
class Sequence:
    cycle: list[int]


@dataclass
class Feature:
    """Base class for all registered feature specs."""

    __feature_name__: ClassVar[str]
    __feature_family__: ClassVar[str]
    __feature_scalar__: ClassVar[bool] = False


def register_feature(name: str, *, scalar: bool = False) -> Callable[[type[F]], type[F]]:
    """Register a Feature subclass under a bible tag name."""

    def decorator(cls: type[F]) -> type[F]:
        if not issubclass(cls, Feature):
            raise TypeError(f"{cls.__name__} must subclass Feature")
        if name in FEATURE_REGISTRY:
            raise ValueError(f"feature {name!r} already registered as {FEATURE_REGISTRY[name].__name__}")
        if scalar and len(fields(cls)) != 1:
            raise TypeError(f"scalar feature {cls.__name__} must have exactly one field")
        cls.__feature_name__ = name
        cls.__feature_family__ = feature_family(name)
        cls.__feature_scalar__ = scalar
        FEATURE_REGISTRY[name] = cls
        return cls

    return decorator
