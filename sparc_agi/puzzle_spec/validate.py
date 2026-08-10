from collections.abc import Iterator
from dataclasses import fields
from typing import Any, get_args, get_origin

from sparc_agi.puzzle_spec.features.base import Access, FeatureSpec
from sparc_agi.puzzle_spec.features.filter import FilterSpec
from sparc_agi.puzzle_spec.features.mapping import MappingSpec
from sparc_agi.puzzle_spec.features.object import ObjectSpec, PoolItemSpec
from sparc_agi.puzzle_spec.slot import FeatureSlotSpec
from sparc_agi.puzzle_spec.wire import FILTER_BINDING_KEY, WireRef, WireValue

def _collect_wire_values(
    step,
    puzzle,
    step_index: int,
    outputs: list[FeatureSpec],
) -> dict[str, Any]:
    wire_values: dict[str, Any] = {}
    for dc_field in fields(type(step)):
        if WireRef.spec_type(dc_field.type) is None:
            continue
        value = getattr(step, dc_field.name)
        if get_origin(dc_field.type) is list:
            wire_values[dc_field.name] = [
                _resolve_ref_value(puzzle, step_index, ref, outputs) for ref in value
            ]
        elif value is None:
            wire_values[dc_field.name] = None
        else:
            wire_values[dc_field.name] = _resolve_ref_value(
                puzzle, step_index, value, outputs
            )
    return wire_values

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
            if isinstance(inner, type) and issubclass(inner, FeatureSpec):
                return inner
        if isinstance(hint, type) and issubclass(hint, FeatureSpec):
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

def _resolve_ref_value(
    puzzle,
    step_index: int,
    ref: WireValue,
    outputs: list[FeatureSpec],
) -> FeatureSpec:
    if isinstance(ref, str):
        item = puzzle.cache.get(ref)
        if item is None:
            raise ValueError(f"unknown cache key {ref!r}")
        return item.value
    if isinstance(ref, int):
        if ref < 0 or ref > step_index:
            raise ValueError(f"invalid wire ref {ref}")
        return outputs[ref]
    raise ValueError(f"invalid wire value {ref!r}")

def trace_step_outputs(puzzle) -> list[FeatureSpec]:
    outputs: list[FeatureSpec] = [puzzle.input.value]
    for step_index, step in enumerate(puzzle.steps):
        step_cls = type(step)
        wire_values = _collect_wire_values(step, puzzle, step_index, outputs)
        output = step_cls.trace(**wire_values)
        if output is None:
            raise ValueError(f"step {step_index} {step_cls.tag()}: trace returned None")
        declared = step_cls.output_type()
        if not isinstance(output, declared):
            raise ValueError(
                f"step {step_index} {step_cls.tag()}: trace returned "
                f"{type(output).tag()}, expected {declared.tag()}"
            )
        outputs.append(output)
    return outputs

def _resolve_filter(puzzle, ref: WireValue) -> FilterSpec:
    if not isinstance(ref, str):
        raise ValueError(f"filter wire must be a cache key, got {ref!r}")
    item = puzzle.cache.get(ref)
    if item is None:
        raise ValueError(f"unknown filter cache key {ref!r}")
    filter_spec = item.value
    if not isinstance(filter_spec, FilterSpec):
        raise ValueError(
            f"cache key {ref!r} must be a filter, got {type(filter_spec).tag()!r}"
        )
    return filter_spec

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

def _validate_wire_ref(
    puzzle,
    step_index: int,
    ref: object,
    expected: type[FeatureSpec],
    label: str,
    outputs: list[FeatureSpec],
) -> None:
    if ref is None:
        return
    if isinstance(ref, str):
        item = puzzle.cache.get(ref)
        if item is None:
            raise ValueError(f"{label}: unknown cache key {ref!r}")
        actual = type(item.value)
        if not issubclass(actual, expected):
            raise ValueError(
                f"{label}: cache key {ref!r} is {actual.tag()}, expected {expected.tag()}"
            )
        return
    if isinstance(ref, int):
        actual = type(_resolve_ref_value(puzzle, step_index, ref, outputs))
        if not issubclass(actual, expected):
            raise ValueError(
                f"{label}: step ref {ref} is {actual.tag()}, expected {expected.tag()}"
            )
        return
    raise ValueError(f"{label}: invalid wire value {ref!r}")

def validate_step_wires(puzzle) -> None:
    outputs = puzzle.step_outputs
    for step_index, step in enumerate(puzzle.steps):
        step_cls = type(step)
        for dc_field in fields(step_cls):
            spec_type = WireRef.spec_type(dc_field.type)
            if spec_type is None:
                continue
            is_list = get_origin(dc_field.type) is list
            value = getattr(step, dc_field.name)
            refs = value if is_list else [value]
            for ref_index, ref in enumerate(refs):
                label = f"step {step_index} {step_cls.tag()}.{dc_field.name}"
                if is_list:
                    label += f"[{ref_index}]"
                _validate_wire_ref(puzzle, step_index, ref, spec_type, label, outputs)

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
            filter_spec = _resolve_filter(puzzle, filter_wire)
            if not isinstance(object_ref, int):
                continue
            root = puzzle.step_outputs[object_ref]
            if not isinstance(root, ObjectSpec):
                continue
            binding = dc_field.metadata[FILTER_BINDING_KEY]
            if binding is None:
                continue
            slot = filter_spec.apply(PoolItemSpec(value=root))
            if slot.value is None:
                at = f"index {filter_spec.index[-1]}" if filter_spec.index else "root"
                raise ValueError(f"{label}: filter {at} resolves to missing pool item")
            target = slot.value
            access, trait = binding
            spec_cls = type(target)
            if not has_trait_access(spec_cls, trait, access):
                need = "gettable" if access & Access.GET else "settable"
                if access == Access.RW:
                    need = "gettable/settable"
                raise ValueError(
                    f"{label}: filtered {spec_cls.tag()} lacks {need} trait {trait!r}"
                )
