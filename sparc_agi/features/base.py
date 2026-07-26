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

from dataclasses import MISSING, dataclass, field, fields, replace
from typing import Any, Callable, ClassVar, Self, TypeVar

F = TypeVar("F", bound="Feature")

FEATURE_REGISTRY: dict[str, type[Feature]] = {}


def feature_family(name: str) -> str:
    """Return the feature family for a registry tag (``arrangement.grid`` → ``arrangement``)."""
    return name.split(".", 1)[0]


@dataclass
class Sequence:
    cycle: list[int]

    def describe(self) -> str:
        return f"cycle {self.cycle}"


@dataclass
class Feature:
    """Base class for all registered feature specs."""

    __feature_name__: ClassVar[str]
    __feature_family__: ClassVar[str]
    __feature_scalar__: ClassVar[bool] = False

    # Provenance link set when a transformation derives a copy from this feature.
    # Typed as Any so cattrs/dataclass tooling does not choke on a self-type.
    source: Any = field(default=None, kw_only=True, compare=False, repr=False)
    # Referential name for descriptions ("input sprite", "rotated sprite from step 1").
    alias: str | None = field(default=None, kw_only=True, compare=False, repr=False)

    def kind_noun(self) -> str:
        """Short kind word from the feature tag (``object.sprite`` → ``sprite``)."""
        return self.__feature_name__.rsplit(".", 1)[-1]

    def derived(self, **changes) -> Self:
        """Return a copy of this feature with ``source`` pointing at ``self``."""
        return replace(self, source=self, alias=None, **changes)

    def refer(self) -> str:
        """Name used when this feature is referenced from another description."""
        return self.alias or self.describe()

    def is_default(self, field_name: str) -> bool:
        """True if ``field_name`` still holds its dataclass default."""
        for f in fields(type(self)):
            if f.name != field_name:
                continue
            val = getattr(self, field_name)
            if f.default_factory is not MISSING:
                return val == f.default_factory()
            if f.default is not MISSING:
                return val == f.default
            return False
        raise AttributeError(f"{type(self).__name__} has no field {field_name!r}")

    def describe(self) -> str:
        """Human-readable phrase for this feature; composites include child describes."""
        if type(self).__feature_scalar__:
            value_fields = [f for f in fields(type(self)) if f.name not in ("source", "alias")]
            val = getattr(self, value_fields[0].name)
            val_text = val.describe() if hasattr(val, "describe") else str(val)
            return f"{self.__feature_name__} {val_text}"
        return self.__feature_name__


def register_feature(name: str, *, scalar: bool = False) -> Callable[[type[F]], type[F]]:
    """Register a Feature subclass under a bible tag name."""

    def decorator(cls: type[F]) -> type[F]:
        if not issubclass(cls, Feature):
            raise TypeError(f"{cls.__name__} must subclass Feature")
        if name in FEATURE_REGISTRY:
            raise ValueError(f"feature {name!r} already registered as {FEATURE_REGISTRY[name].__name__}")
        value_fields = [f for f in fields(cls) if f.name not in ("source", "alias")]
        if scalar and len(value_fields) != 1:
            raise TypeError(f"scalar feature {cls.__name__} must have exactly one value field")
        cls.__feature_name__ = name
        cls.__feature_family__ = feature_family(name)
        cls.__feature_scalar__ = scalar
        FEATURE_REGISTRY[name] = cls
        return cls

    return decorator
