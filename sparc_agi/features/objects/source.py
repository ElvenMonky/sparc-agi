"""Helpers for resolving an object against a group pool via ``source``."""

from collections.abc import Sequence

from sparc_agi.features.base import Feature
from sparc_agi.features.objects.base import Object


def pool_member_via_source(item: Feature, pool: Sequence[Object]) -> Object | None:
    """Return the pool entry that ``item`` is (or inherits from via ``source``)."""
    pool_by_id = {id(m): m for m in pool}
    for node in item.iter_source():
        found = pool_by_id.get(id(node))
        if found is not None:
            return found
    return None
