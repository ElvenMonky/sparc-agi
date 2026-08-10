from collections.abc import Iterator
from dataclasses import fields
from typing import get_args, get_origin

from sparc_agi.puzzle_spec.features.base import FeatureSpec
from sparc_agi.puzzle_spec.features.mapping import MappingSpec
from sparc_agi.puzzle_spec.features.object import ObjectSpec
from sparc_agi.puzzle_spec.slot import FeatureSlotSpec
from sparc_agi.puzzle_spec.wire import wire_spec_type

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

def is_gettable_trait_path(spec_cls: type[FeatureSpec], path: str) -> bool:
    parts = path.split(".")
    cls = spec_cls
    for index, part in enumerate(parts):
        if part not in cls.gettable_traits():
            return False
        if index == len(parts) - 1:
            return True
        nested = _nested_spec_type(cls, part)
        if nested is None:
            return False
        cls = nested
    return False

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
            if not is_gettable_trait_path(spec_cls, mapping.key):
                raise ValueError(
                    f"{spec_cls.tag()} linked_mappings cache key {cache_key!r} "
                    f"uses non-gettable trait {mapping.key!r}"
                )

def _validate_wire_ref(
    puzzle,
    step_index: int,
    ref: object,
    expected: type[FeatureSpec],
    label: str,
    outputs: list[type[FeatureSpec]],
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
        if ref == 0:
            actual = type(puzzle.input.value)
        elif ref >= 1:
            out_step = ref - 1
            if out_step >= step_index:
                raise ValueError(f"{label}: forward reference to step output {ref}")
            actual = outputs[out_step]
        else:
            raise ValueError(f"{label}: invalid wire ref {ref}")
        if not issubclass(actual, expected):
            raise ValueError(
                f"{label}: step ref {ref} is {actual.tag()}, expected {expected.tag()}"
            )
        return
    raise ValueError(f"{label}: invalid wire value {ref!r}")

def validate_step_wires(puzzle) -> None:
    outputs: list[type[FeatureSpec]] = []
    for step_index, step in enumerate(puzzle.steps):
        step_cls = type(step)
        for dc_field in fields(step_cls):
            spec_type = wire_spec_type(dc_field.type)
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
        outputs.append(type(step).output_type())
