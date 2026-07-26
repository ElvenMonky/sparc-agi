"""cattrs converter for puzzle source documents.

Source shape (per puzzle id)::

    {
      "cache": { "<key>": { "<feature.name>": <payload> }, ... },
      "input": { "<feature.name>": <payload> },
      "samples": { "train": <int>, "test": <int> },
      "skeleton": [
        { "<Transform>": [<wire>, ...] },
        // or equivalently:
        { "type": "<Transform>", "input": [<wire>, ...] }
      ]
    }

New features / transformations only need a registered class; this module's
hooks resolve tags through the registries and do not hard-code type names.
"""

import json
from dataclasses import MISSING, fields, is_dataclass
from pathlib import Path
from typing import Any, Union, get_type_hints

import cattrs
from cattrs.gen import make_dict_structure_fn, make_dict_unstructure_fn, override

from sparc_agi.features import FEATURE_REGISTRY, Feature, Size, feature_family
from sparc_agi.features.base import Scalar
from sparc_agi.features.height import Height
from sparc_agi.features.range import Range
from sparc_agi.features.width import Width
from sparc_agi.puzzle import Puzzle, PuzzleSource, SpecError
from sparc_agi.transformations import TRANSFORMATION_REGISTRY, Transformation, WireRef

converter = cattrs.Converter()


def _is_scalar_feature_type(t: Any) -> bool:
    return isinstance(t, type) and issubclass(t, Scalar) and t is not Scalar


def _is_plain_dataclass(t: Any) -> bool:
    return (
        is_dataclass(t)
        and isinstance(t, type)
        and t not in (Size, Range)
        and not issubclass(t, (Feature, Transformation))
    )


# Plain nested dataclasses on demand. Size / Range / Features have dedicated hooks.
converter.register_structure_hook_factory(
    _is_plain_dataclass,
    lambda t: make_dict_structure_fn(t, converter),
)
converter.register_unstructure_hook_factory(
    _is_plain_dataclass,
    lambda t: make_dict_unstructure_fn(t, converter),
)


def structure_range(obj: Any, _type: type) -> Range:
    return Range.from_raw(obj)


def unstructure_range(obj: Range) -> int | list[int]:
    return obj.to_raw()


converter.register_structure_hook(Range, structure_range)
converter.register_unstructure_hook(Range, unstructure_range)


def structure_scalar_feature(obj: Any, cls: type[Feature]) -> Feature:
    """Structure a concrete scalar feature from a bare Range payload (or instance)."""
    if isinstance(obj, cls):
        return obj
    return cls(value=converter.structure(obj, Range))


converter.register_structure_hook_func(_is_scalar_feature_type, structure_scalar_feature)


def _is_composite_feature_type(t: Any) -> bool:
    return (
        isinstance(t, type)
        and issubclass(t, Feature)
        and t is not Feature
        and not issubclass(t, Scalar)
    )


def structure_composite_feature(obj: Any, cls: type[Feature]) -> Feature:
    """Structure a concrete composite feature from its bare payload object."""
    if isinstance(obj, cls):
        return obj
    return _structure_concrete(obj, cls)


converter.register_structure_hook_func(_is_composite_feature_type, structure_composite_feature)


def _structure_nested_scalar(payload: Any, cls: type[Feature]) -> Feature:
    """Structure a scalar feature nested under a field (bare payload, not tagged)."""
    return structure_scalar_feature(payload, cls)


def structure_size(obj: Any, _type: type) -> Size:
    if not isinstance(obj, dict):
        raise ValueError(f"size must be an object, got {obj!r}")
    try:
        return Size(
            width=_structure_nested_scalar(obj["width"], Width),
            height=_structure_nested_scalar(obj["height"], Height),
        )
    except KeyError as exc:
        raise ValueError(f"size requires 'width' and 'height', got {obj!r}") from exc


def unstructure_size(obj: Size) -> dict[str, int | list[int]]:
    # Nested form keeps bare range payloads; tagged form is only for Feature slots.
    return {
        "width": converter.unstructure(obj.width.value),
        "height": converter.unstructure(obj.height.value),
    }


converter.register_structure_hook(Size, structure_size)
converter.register_unstructure_hook(Size, unstructure_size)


def _require_single_tag(obj: Any, kind: str) -> tuple[str, Any]:
    if not isinstance(obj, dict) or len(obj) != 1:
        raise ValueError(f"{kind} must be a single-key object, got {obj!r}")
    ((tag, payload),) = obj.items()
    if not isinstance(tag, str):
        raise ValueError(f"{kind} tag must be a string, got {tag!r}")
    return tag, payload


def _normalize_composite_payload(payload: dict[str, Any], cls: type[Feature]) -> dict[str, Any]:
    """Map flat child tags onto field names.

    When a payload key is a registered feature tag whose family matches a field
    name (e.g. ``object.sprite`` → field ``object``), rewrite it to a tagged
    nested value so polymorphic ``Feature`` slots keep their kind.
    """
    hints = get_type_hints(cls)
    field_names = {f.name for f in fields(cls) if f.name not in ("source", "alias")}
    out = dict(payload)
    for key in list(out):
        if key in field_names or key not in FEATURE_REGISTRY:
            continue
        family = feature_family(key)
        if family not in field_names or family in out:
            continue
        child_payload = out.pop(key)
        ann = hints.get(family)
        if ann is Feature:
            out[family] = {key: child_payload}
        else:
            expected = getattr(ann, "__feature_name__", None)
            out[family] = child_payload if expected == key else {key: child_payload}
    return out


def _structure_concrete(payload: Any, cls: type) -> Any:
    """Structure into a concrete dataclass without re-entering tagged-union hooks."""
    if (
        isinstance(payload, dict)
        and isinstance(cls, type)
        and issubclass(cls, Feature)
        and not issubclass(cls, Scalar)
    ):
        payload = _normalize_composite_payload(payload, cls)
    kwargs: dict[str, Any] = {}
    if isinstance(cls, type) and issubclass(cls, Feature):
        # Provenance / aliases are runtime-only; never read from the source JSON.
        kwargs["source"] = override(omit=True)
        kwargs["alias"] = override(omit=True)
    return make_dict_structure_fn(cls, converter, **kwargs)(payload, cls)


def structure_feature(obj: Any, _type: type) -> Feature:
    tag, payload = _require_single_tag(obj, "feature")
    try:
        cls = FEATURE_REGISTRY[tag]
    except KeyError as exc:
        known = ", ".join(sorted(FEATURE_REGISTRY)) or "(none)"
        raise ValueError(f"unknown feature {tag!r}; registered: {known}") from exc

    if issubclass(cls, Scalar):
        return structure_scalar_feature(payload, cls)
    return _structure_concrete(payload, cls)


def _unstructure_composite_payload(obj: Feature) -> dict[str, Any]:
    """Unstructure composite feature fields; nested scalars stay bare (untagged)."""
    cls = type(obj)
    hints = get_type_hints(cls)
    payload: dict[str, Any] = {}
    for f in fields(cls):
        if f.name in ("source", "alias", "pool_origins"):
            continue
        val = getattr(obj, f.name)
        if val is None:
            continue
        # Omit nested defaults (e.g. Group.spacing, Sequence.prefix).
        if f.default_factory is not MISSING and val == f.default_factory():
            continue
        if f.default is not MISSING and val == f.default:
            continue
        if isinstance(val, Scalar):
            payload[f.name] = converter.unstructure(val.value)
        elif isinstance(val, Feature):
            tagged = unstructure_feature(val)
            ((tag, inner),) = tagged.items()
            # Field name matches tag → bare payload; polymorphic Feature slot → flat tag.
            if tag == f.name:
                payload[f.name] = inner
            elif hints.get(f.name) is Feature:
                payload[tag] = inner
            else:
                payload[f.name] = tagged
        else:
            payload[f.name] = converter.unstructure(val)
    return payload


def unstructure_feature(obj: Feature) -> dict[str, Any]:
    cls = type(obj)
    if isinstance(obj, Scalar):
        payload: Any = converter.unstructure(obj.value)
    else:
        payload = _unstructure_composite_payload(obj)
    return {cls.__feature_name__: payload}


def _parse_transformation_tag(obj: Any) -> tuple[str, Any]:
    """Accept tagged ``{Name: payload}`` or explicit ``{type, input}`` forms."""
    if not isinstance(obj, dict):
        raise ValueError(f"transformation must be an object, got {obj!r}")

    if "type" in obj:
        tag = obj["type"]
        if not isinstance(tag, str):
            raise ValueError(f"transformation type must be a string, got {tag!r}")
        if "input" in obj:
            return tag, obj["input"]
        if "inputs" in obj:
            return tag, obj["inputs"]
        # Remaining keys are treated as the structured payload (minus type).
        return tag, {k: v for k, v in obj.items() if k != "type"}

    return _require_single_tag(obj, "transformation")


def structure_transformation(obj: Any, _type: type) -> Transformation:
    tag, payload = _parse_transformation_tag(obj)
    try:
        cls = TRANSFORMATION_REGISTRY[tag]
    except KeyError as exc:
        known = ", ".join(sorted(TRANSFORMATION_REGISTRY)) or "(none)"
        raise ValueError(f"unknown transformation {tag!r}; registered: {known}") from exc

    # List payload is the common skeleton form.
    # A dict payload is allowed for future per-transform fields.
    if isinstance(payload, list):
        data: dict[str, Any] = {"inputs": payload}
    elif isinstance(payload, dict):
        data = dict(payload)
        if "input" in data and "inputs" not in data:
            data["inputs"] = data.pop("input")
    else:
        raise ValueError(f"transformation {tag!r} payload must be a list or object, got {payload!r}")
    return _structure_concrete(data, cls)


def unstructure_transformation(obj: Transformation) -> dict[str, Any]:
    """Emit the explicit ``{type, input}`` form used in the source."""
    cls = type(obj)
    return {
        "type": cls.__transformation_name__,
        "input": converter.unstructure(obj.inputs),
    }


# Exact base types only — concrete subclasses structure via _structure_concrete.
converter.register_structure_hook_func(lambda t: t is Feature, structure_feature)
converter.register_structure_hook_func(lambda t: t is Transformation, structure_transformation)

converter.register_unstructure_hook_func(
    lambda cls: isinstance(cls, type) and issubclass(cls, Feature),
    unstructure_feature,
)
converter.register_unstructure_hook_func(
    lambda cls: isinstance(cls, type) and issubclass(cls, Transformation),
    unstructure_transformation,
)


def _structure_wire_ref(value: Any, _type: type) -> WireRef:
    if isinstance(value, (str, int)) and not isinstance(value, bool):
        return value
    raise ValueError(f"wire ref must be str or int, got {value!r}")


converter.register_structure_hook(WireRef, _structure_wire_ref)

converter.register_structure_hook(Puzzle, make_dict_structure_fn(Puzzle, converter))
converter.register_unstructure_hook(Puzzle, make_dict_unstructure_fn(Puzzle, converter))


def structure_source(obj: Any, *, validate: bool = True) -> PuzzleSource:
    if not isinstance(obj, dict):
        raise ValueError(f"source must be an object, got {type(obj).__name__}")
    source = {puzzle_id: converter.structure(raw, Puzzle) for puzzle_id, raw in obj.items()}
    if validate:
        for puzzle_id, puzzle in source.items():
            try:
                puzzle.validate()
            except SpecError as exc:
                raise SpecError(f"puzzle {puzzle_id}: {exc}") from exc
    return source


def load_source(path: Union[str, Path], *, validate: bool = True) -> PuzzleSource:
    with Path(path).open() as f:
        return structure_source(json.load(f), validate=validate)
