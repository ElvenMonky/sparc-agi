from collections.abc import Iterator
from dataclasses import fields
from typing import get_args, get_origin

from sparc_agi.puzzle_spec.features.base import Access
from sparc_agi.puzzle_spec.features.mapping import MappingSpec
from sparc_agi.puzzle_spec.features.object import ObjectSpec
from sparc_agi.puzzle_spec.wire import WireRef

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
            if source_trait is not None:
                spec_cls.validate_trait_access(source_trait, Access.GET)

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
