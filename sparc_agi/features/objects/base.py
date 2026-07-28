"""Base class for ``object.*`` feature kinds."""

import random
from dataclasses import dataclass

from sparc_agi.canvas import Geometry
from sparc_agi.features.base import Feature
from sparc_agi.instance_ctx import get_forced_source_key, get_instance_cache


@dataclass
class Object(Feature):
    """Renderable object. Instantiation yields a :class:`~sparc_agi.canvas.Geometry` tree.

    Inheritance uses :attr:`Feature.source`: cache key(s), or a parent Feature
    from any earlier stage (cache, puzzle input, or a prior transform). When
    ``source`` is a key list, :meth:`instantiate_from_source` copies a donor
    geometry, paints with the given color, and sets ``Geometry.source`` to the
    donor so later steps can read ``geometry.source.color`` (etc.).
    """

    def cache_source_keys(self) -> list[str]:
        """Bible cache-key list on ``source``, or empty."""
        keys = self.source
        if isinstance(keys, list) and keys and all(isinstance(k, str) for k in keys):
            return list(keys)
        return []

    def instantiate_from_source(self, rng: random.Random, *, color: int) -> Geometry:
        """Copy a cache donor's geometry, recolor, link ``source`` to the donor."""
        keys = self.cache_source_keys()
        if not keys:
            raise ValueError(
                f"{type(self).__name__}.instantiate_from_source requires source cache keys"
            )
        cache = get_instance_cache()
        forced = get_forced_source_key()
        if forced is not None and forced in keys:
            key = forced
        else:
            key = keys[rng.randrange(len(keys))]
        try:
            donor = cache[key]
        except KeyError as exc:
            raise KeyError(f"object source {key!r} not in instance cache") from exc
        if not isinstance(donor, Geometry):
            raise TypeError(
                f"object source {key!r} must be Geometry, got {type(donor).__name__}"
            )
        out = donor.copy()
        out.x = 0
        out.y = 0
        out.slot = None
        out.source = donor
        return out.recolor(color)
