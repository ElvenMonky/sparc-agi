"""Feature registry and shared nested value types.

Feature specs in the source are single-key tagged objects::

    { "<feature.name>": <payload> }

The tag is ``<family>`` or ``<family>.<kind>``. The family (part before the
dot) is what transformations match on; kinds are interchangeable in a slot
that expects that family (e.g. ``object.sprite`` satisfies an ``object`` slot).

**Traits.** Every dataclass field on a feature (except ``source`` / ``alias`` /
``geometry_index``) is an editable trait. ``source`` is inheritance, not a
filterable trait. Pipeline order is cache → input → transformations; ``source``
may refer to any preceding stage — bible ``list[str]`` / ``str`` cache keys, or
a parent :class:`Feature` (cache entry, puzzle input, or earlier step output)
after :meth:`derived`.

Register a new feature with ``@register_feature("feature.name")``. Scalar
features subclass :class:`Scalar` (single ``value: Range`` field); composites
subclass :class:`Feature` directly.
"""

import random
from collections.abc import Iterator
from dataclasses import MISSING, dataclass, field, fields, replace
from typing import Any, Callable, ClassVar, Self, TypeVar

from sparc_agi.features.scalars.range import Range

F = TypeVar("F", bound="Feature")

FEATURE_REGISTRY: dict[str, type[Feature]] = {}

# Not filterable traits; ``source`` is still loaded from the bible when present.
_PROVENANCE_FIELDS: frozenset[str] = frozenset({"source", "alias", "geometry_index"})


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

    # Inheritance from any preceding stage (cache → input → transforms):
    # bible cache key(s) ``str`` / ``list[str]``, or a parent Feature after
    # ``derived()`` (that parent may itself be cache, input, or a prior step).
    source: Any = field(default=None, kw_only=True, compare=False, repr=False)
    # Referential name for descriptions ("input sprite", "rotated sprite from step 1").
    alias: str | None = field(default=None, kw_only=True, compare=False, repr=False)
    # Child index in a parent Geometry.geometries list (set by PickObject, etc.).
    geometry_index: int | None = field(default=None, kw_only=True, compare=False, repr=False)

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
        """Copy with ``source`` pointing at ``self`` (unless ``source`` is overridden)."""
        if "geometry_index" not in changes:
            changes["geometry_index"] = None
        if "source" not in changes:
            changes["source"] = self
        return replace(self, alias=None, **changes)

    def iter_source(self) -> Iterator[Feature]:
        """Walk ``self``, then each Feature-valued ``source``, until cache keys / None."""
        cur: Feature | None = self
        seen: set[int] = set()
        while isinstance(cur, Feature) and id(cur) not in seen:
            yield cur
            seen.add(id(cur))
            nxt = cur.source
            cur = nxt if isinstance(nxt, Feature) else None

    def refer(self) -> str:
        """Name used when this feature is referenced from another description."""
        return self.alias or self.describe()

    def is_default(self, field_name: str) -> bool:
        """True if ``field_name`` still holds its dataclass default."""
        for f in fields(type(self)):
            if f.name != field_name:
                continue
            val = getattr(self, f.name)
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
