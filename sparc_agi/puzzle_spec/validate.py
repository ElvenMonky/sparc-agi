from collections.abc import Iterator
from dataclasses import fields
from typing import Any, get_args, get_origin

from sparc_agi.puzzle_spec.features.base import Access, FeatureSpec
from sparc_agi.puzzle_spec.features.filter import FilterSpec
from sparc_agi.puzzle_spec.features.mapping import MappingSpec
from sparc_agi.puzzle_spec.features.object import ObjectSpec
from sparc_agi.puzzle_spec.slot import FeatureSlotSpec
from sparc_agi.puzzle_spec.wire import FILTER_BINDING_KEY, WireRef, WireValue

def _unwrap_optional(hint: type) -> type:
    args = get_args(hint)
    if args and type(None) in args:
        return next(arg for arg in args if arg is not type(None))
    return hint

def _nested_spec_type(spec_cls: type[FeatureSpec], trait_name: str) -> type[FeatureSpec] | None:
    for dc_field in fields(spec_cls):
        if dc_field.name != trait_name:
            continue
        hint = _unwrap_optional(dc_field.type)
        origin = get_origin(hint)
        if origin is FeatureSlotSpec:
            inner = get_args(hint)[0]
            if FeatureSpec.is_feature(inner):
                return inner
        if FeatureSpec.is_feature(hint):
            return hint
    return None

def _trait_access(spec_cls: type[FeatureSpec], path: str) -> Access | None:
    parts = path.split(".")
    cls = spec_cls
    for index, part in enumerate(parts):
        accesses = cls.trait_accesses()
        if part not in accesses:
            return None
        if index == len(parts) - 1:
            return accesses[part]
        nested = _nested_spec_type(cls, part)
        if nested is None:
            return None
        cls = nested
    return None

def has_trait_access(spec_cls: type[FeatureSpec], path: str, access: Access) -> bool:
    trait_access = _trait_access(spec_cls, path)
    if trait_access is None:
        return False
    return bool(trait_access & access)

def iter_input_objects(root: ObjectSpec) -> Iterator[ObjectSpec]:
    yield root
    pool = getattr(root, "pool", None)
    if pool:
        for item in pool:
            yield from iter_input_objects(item.value)

def validate_linked_mappings(puzzle) -> None:
    for obj in iter_input_objects(puzzle.input.value):
        if not obj.linked_mappings:
            continue
        spec_cls = type(obj)
        for cache_key in obj.linked_mappings:
            item = puzzle.cache.get(cache_key)
            if item is None:
                raise ValueError(
                    f"{spec_cls.tag()} linked_mappings references unknown cache key {cache_key!r}"
                )
            mapping = item.value
            if not isinstance(mapping, MappingSpec):
                raise ValueError(
                    f"{spec_cls.tag()} linked_mappings cache key {cache_key!r} "
                    f"must be a mapping, got {type(mapping).tag()!r}"
                )
            source_trait = type(mapping).source_trait
            if source_trait is not None and not has_trait_access(spec_cls, source_trait, Access.GET):
                raise ValueError(
                    f"{spec_cls.tag()} linked_mappings cache key {cache_key!r} "
                    f"requires gettable trait {source_trait!r}"
                )

def validate_step_wires(puzzle) -> None:
    for step_index, step in enumerate(puzzle.steps):
        step_cls = type(step)
        for dc_field in fields(step_cls):
            spec_type = WireRef.spec_type(dc_field.type)
            if spec_type is None:
                continue
            is_list = get_origin(dc_field.type) is list
            value = getattr(step, dc_field.name)
            wires = value if is_list else [value]
            for ref_index, wire in enumerate(wires):
                label = f"step {step_index} {step_cls.tag()}.{dc_field.name}"
                if is_list:
                    label += f"[{ref_index}]"
                if wire is None:
                    continue
                try:
                    actual = type(puzzle.resolve_wire_value(step_index, wire))
                except ValueError as exc:
                    raise ValueError(f"{label}: {exc}") from exc
                if not issubclass(actual, spec_type):
                    raise ValueError(
                        f"{label}: resolved to {actual.tag()}, expected {spec_type.tag()}"
                    )

def validate_filter_wires(puzzle) -> None:
    for step_index, step in enumerate(puzzle.steps):
        step_cls = type(step)
        object_ref = getattr(step, "object", None)
        if object_ref is None:
            continue
        for dc_field in fields(step_cls):
            if WireRef.spec_type(dc_field.type) is not FilterSpec:
                continue
            if FILTER_BINDING_KEY not in dc_field.metadata:
                continue
            filter_wire = getattr(step, dc_field.name)
            if filter_wire is None:
                continue
            label = f"step {step_index} {step_cls.tag()}.{dc_field.name}"
            if not isinstance(filter_wire, str):
                raise ValueError(f"{label}: filter wire must be a cache key, got {filter_wire!r}")
            item = puzzle.cache.get(filter_wire)
            if item is None:
                raise ValueError(f"{label}: unknown filter cache key {filter_wire!r}")
            filter_spec = item.value
            if not isinstance(filter_spec, FilterSpec):
                raise ValueError(
                    f"{label}: cache key {filter_wire!r} must be a filter, "
                    f"got {type(filter_spec).tag()!r}"
                )
            if not isinstance(object_ref, int):
                continue
            root = puzzle.step_outputs[object_ref]
            if not isinstance(root, ObjectSpec):
                continue
            binding = dc_field.metadata[FILTER_BINDING_KEY]
            if binding is None:
                continue
            target = filter_spec.target(root)
            if target is None:
                at = f"index {filter_spec.index[-1]}" if filter_spec.index else "root"
                raise ValueError(f"{label}: filter {at} resolves to missing pool item")
            access, trait = binding
            spec_cls = type(target)
            if not has_trait_access(spec_cls, trait, access):
                need = "gettable" if access & Access.GET else "settable"
                if access == Access.RW:
                    need = "gettable/settable"
                raise ValueError(
                    f"{label}: filtered {spec_cls.tag()} lacks {need} trait {trait!r}"
                )
