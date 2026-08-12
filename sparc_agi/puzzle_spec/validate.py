from collections.abc import Iterator
from dataclasses import fields
from typing import get_args, get_origin

from sparc_agi.puzzle_spec.features.base import Access
from sparc_agi.puzzle_spec.features.filter import FilterSpec
from sparc_agi.puzzle_spec.features.mapping import MappingSpec
from sparc_agi.puzzle_spec.features.object import ObjectSpec
from sparc_agi.puzzle_spec.wire import FILTER_BINDING_KEY, WireRef

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
            if source_trait is not None and not spec_cls.has_trait_access(source_trait, Access.GET):
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

def validate_step_outputs(puzzle) -> None:
    referenced: set[int] = set()
    for step in puzzle.steps:
        for dc_field in fields(type(step)):
            if WireRef.spec_type(dc_field.type) is None:
                continue
            value = getattr(step, dc_field.name)
            wires = value if get_origin(dc_field.type) is list else [value]
            for wire in wires:
                if isinstance(wire, int):
                    referenced.add(wire)
    unused = set(range(len(puzzle.steps))) - referenced
    if unused:
        labels = ", ".join(
            f"wire {wire} ({'input' if wire == 0 else f'output of step {wire}'})"
            for wire in sorted(unused)
        )
        raise ValueError(f"unreferenced step outputs: {labels}")
    final = puzzle.step_outputs[-1]
    if not isinstance(final, ObjectSpec):
        raise ValueError(
            f"final output must be an object, got {type(final).tag()}"
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
            if not spec_cls.has_trait_access(trait, access):
                need = "gettable" if access & Access.GET else "settable"
                if access == Access.RW:
                    need = "gettable/settable"
                raise ValueError(
                    f"{label}: filtered {spec_cls.tag()} lacks {need} trait {trait!r}"
                )
