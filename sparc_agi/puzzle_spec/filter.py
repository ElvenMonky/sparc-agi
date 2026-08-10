from dataclasses import MISSING, field
from typing import Any

from sparc_agi.puzzle_spec.features.base import Access, FilterSpec
from sparc_agi.puzzle_spec.features.object import ObjectSpec

FILTER_BINDING_KEY = "filter_binding"
FilterBinding = tuple[Access, str]

def filter_ref(
    binding: FilterBinding | None = None,
    *,
    default: Any = MISSING,
) -> Any:
    metadata = {FILTER_BINDING_KEY: binding}
    if default is not MISSING:
        return field(default=default, metadata=metadata)
    return field(metadata=metadata)

def apply_filter(obj: ObjectSpec, filter: FilterSpec) -> ObjectSpec:
    if not filter.index:
        return obj
    current = obj
    for idx in filter.index:
        pool = getattr(current, "pool", None)
        if not pool:
            raise ValueError(
                f"filter index {idx} but {type(current).tag()} has no pool"
            )
        if idx < 0 or idx >= len(pool):
            raise ValueError(
                f"filter index {idx} out of range for {type(current).tag()} "
                f"pool of size {len(pool)}"
            )
        current = pool[idx].value
    return current
