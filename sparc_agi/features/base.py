"""Feature registry and shared nested value types.

Feature specs are single-key tagged objects::

    { "<tag>": <payload> }

The tag is ``<family>`` or ``<family>.<kind>``.
The family (part before the dot) is what transformations match on;
Kinds are interchangeable in a slot that expects that family (e.g. ``object.sprite`` satisfies an ``object`` slot).

Register a new feature with ``@register_feature("<family>.<kind>")``.

**Traits.** Every dataclass field on a feature (except ``source`` / ``alias``) is an editable trait.
``source`` is not a trait. Pipeline order is cache → input → transformations; ``source`` may refer to any preceding stage.
"""

from dataclasses import MISSING, dataclass, field, fields, replace
from typing import Any, Callable, ClassVar, Self, TypeVar

F = TypeVar("F", bound="Feature")

FEATURE_REGISTRY: dict[str, type[Feature]] = {}

_BASE_FIELDS: frozenset[str] = frozenset({"source", "alias"})

@dataclass
class FeatureSpec:
    """Base class for all registered feature specs."""

    __feature_name__: ClassVar[str]
    __feature_family__: ClassVar[str]
    __non_traits__: ClassVar[frozenset[str]] = frozenset()

    # Inheritance from any preceding stage (cache → input → transforms)
    source: Any = field(default=None, kw_only=True, compare=False, repr=False)
    # Referential name for descriptions ("input sprite", "rotated sprite from step 1").
    alias: str | None = field(default=None, kw_only=True, compare=False, repr=False)

    @classmethod
    def trait_names(cls) -> frozenset[str]:
        excluded = _BASE_FIELDS | cls.__non_traits__
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

    def _iter_features(self):
        yield self
        for f in fields(type(self)):
            if f.name in ("source", "alias", "geometry_index"):
                continue
            val = getattr(self, f.name)
            if isinstance(val, Feature):
                yield from _iter_features(val)
            elif isinstance(val, list):
                for item in val:
                    if isinstance(item, Feature):
                        yield from _iter_features(item)
            elif isinstance(val, dict):
                for item in val.values():
                    if isinstance(item, Feature):
                        yield from _iter_features(item)

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

def register_feature(name: str) -> Callable[[type[F]], type[F]]:
    """Register a Feature subclass under a source tag name."""

    def decorator(cls: type[F]) -> type[F]:
        if not issubclass(cls, Feature):
            raise TypeError(f"{cls.__name__} must subclass Feature")
        if name in FEATURE_REGISTRY:
            raise ValueError(f"feature {name!r} already registered as {FEATURE_REGISTRY[name].__name__}")
        cls.__feature_name__ = name
        cls.__feature_family__ = name.split(".", 1)[0]
        FEATURE_REGISTRY[name] = cls
        return cls

    return decorator
