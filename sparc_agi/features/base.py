"""Feature registry and shared nested value types.

Feature specs in the source are single-key tagged objects::

    { "<feature.name>": <payload> }

The tag is ``<family>`` or ``<family>.<kind>``. The family (part before the
dot) is what transformations match on; kinds are interchangeable in a slot
that expects that family (e.g. ``object.sprite`` satisfies an ``object`` slot).

**Traits.** Every dataclass field on a feature (except provenance ``source`` /
``alias``) is an editable trait. Transformations use :meth:`has_trait` to
require or optionally special-case a trait (e.g. Rotate + ``orientation``).
Prefer methods for non-editable structure (e.g. Sprite ``as_group()``). To
keep a dataclass field that is *not* a trait, list it on ``__non_traits__``::

    __non_traits__ = frozenset({"internal_cache"})

Provenance fields are always excluded; ``__non_traits__`` only names extras.

Register a new feature with ``@register_feature("feature.name")``. Scalar
features subclass :class:`Scalar` (single ``value: Range`` field); composites
subclass :class:`Feature` directly.
"""

import random
from dataclasses import MISSING, dataclass, field, fields, replace
from typing import Any, Callable, ClassVar, Self, TypeVar

from sparc_agi.features.range import Range

F = TypeVar("F", bound="Feature")

FEATURE_REGISTRY: dict[str, type[Feature]] = {}

# Provenance fields present on every Feature; never traits / source payload.
_PROVENANCE_FIELDS: frozenset[str] = frozenset({"source", "alias"})


def feature_family(name: str) -> str:
    """Return the feature family for a registry tag (``arrangement.grid`` → ``arrangement``)."""
    return name.split(".", 1)[0]


@dataclass
class Feature:
    """Base class for all registered feature specs."""

    __feature_name__: ClassVar[str]
    __feature_family__: ClassVar[str]
    # Extra field names that are not traits (provenance is always excluded).
    __non_traits__: ClassVar[frozenset[str]] = frozenset()

    # Provenance link set when a transformation derives a copy from this feature.
    # Typed as Any so cattrs/dataclass tooling does not choke on a self-type.
    source: Any = field(default=None, kw_only=True, compare=False, repr=False)
    # Referential name for descriptions ("input sprite", "rotated sprite from step 1").
    alias: str | None = field(default=None, kw_only=True, compare=False, repr=False)

    @classmethod
    def trait_names(cls) -> frozenset[str]:
        """Editable trait field names for this feature kind."""
        excluded = _PROVENANCE_FIELDS | cls.__non_traits__
        return frozenset(f.name for f in fields(cls) if f.name not in excluded)

    def has_trait(self, name: str) -> bool:
        """True if this feature kind exposes editable trait ``name``."""
        return name in type(self).trait_names()

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
        return self.__feature_name__

    def instantiate(self, rng: random.Random) -> Any:
        """Sample a concrete value for this feature."""
        raise NotImplementedError(f"{type(self).__name__}.instantiate() is not implemented")


@dataclass
class Scalar(Feature):
    """Range-valued scalar feature (width, color, orientation, …)."""

    value: Range

    def describe(self) -> str:
        return f"{self.__feature_name__} {self.value.describe()}"

    def instantiate(self, rng: random.Random) -> int:
        return self.value.sample(rng)


def register_feature(name: str) -> Callable[[type[F]], type[F]]:
    """Register a Feature subclass under a source tag name."""

    def decorator(cls: type[F]) -> type[F]:
        if not issubclass(cls, Feature):
            raise TypeError(f"{cls.__name__} must subclass Feature")
        if name in FEATURE_REGISTRY:
            raise ValueError(f"feature {name!r} already registered as {FEATURE_REGISTRY[name].__name__}")
        if issubclass(cls, Scalar):
            value_fields = [f for f in fields(cls) if f.name not in _PROVENANCE_FIELDS]
            if len(value_fields) != 1 or value_fields[0].name != "value":
                raise TypeError(f"scalar feature {cls.__name__} must declare a single 'value' field")
        cls.__feature_name__ = name
        cls.__feature_family__ = feature_family(name)
        FEATURE_REGISTRY[name] = cls
        return cls

    return decorator
