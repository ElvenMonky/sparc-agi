"""PuzzleSpec dataclasses and cattrs converter for the puzzle spec bible.

Bible shape (per puzzle id)::

    {
      "cache": { "<key>": { "<feature.name>": <payload> }, ... },
      "input": { "<feature.name>": <payload> },
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
from dataclasses import dataclass, fields, is_dataclass
from pathlib import Path
from typing import Any, Union

import cattrs
from cattrs.gen import make_dict_structure_fn, make_dict_unstructure_fn

from sparc_agi.features import FEATURE_REGISTRY, Feature, Size
from sparc_agi.features.height import Height
from sparc_agi.features.width import Width
from sparc_agi.transformations import TRANSFORMATION_REGISTRY, Transformation, WireRef


class SpecError(ValueError):
    """Puzzle spec failed structural or type validation."""

converter = cattrs.Converter()

# Dataclass hooks on demand. Exact Feature / Transformation / Size hooks below
# win for those types; concrete subclasses (GridArrangement, Rotate, …) use these.
converter.register_structure_hook_factory(
    lambda t: is_dataclass(t) and isinstance(t, type) and t is not Size,
    lambda t: make_dict_structure_fn(t, converter),
)
converter.register_unstructure_hook_factory(
    lambda t: (
        is_dataclass(t)
        and isinstance(t, type)
        and t is not Size
        and not issubclass(t, (Feature, Transformation))
    ),
    lambda t: make_dict_unstructure_fn(t, converter),
)


def _structure_nested_scalar(payload: Any, cls: type[Feature]) -> Feature:
    """Structure a scalar feature nested under a field (bare payload, not tagged)."""
    if isinstance(payload, cls):
        return payload
    if cls.__feature_scalar__ and not isinstance(payload, dict):
        return cls(**{fields(cls)[0].name: payload})
    return make_dict_structure_fn(cls, converter)(payload, cls)


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


def unstructure_size(obj: Size) -> dict[str, int]:
    # Nested form keeps bare scalars; tagged ``{width: N}`` is only for Feature slots.
    return {"width": obj.width.value, "height": obj.height.value}


converter.register_structure_hook(Size, structure_size)
converter.register_unstructure_hook(Size, unstructure_size)


def _require_single_tag(obj: Any, kind: str) -> tuple[str, Any]:
    if not isinstance(obj, dict) or len(obj) != 1:
        raise ValueError(f"{kind} must be a single-key object, got {obj!r}")
    ((tag, payload),) = obj.items()
    if not isinstance(tag, str):
        raise ValueError(f"{kind} tag must be a string, got {tag!r}")
    return tag, payload


def _structure_concrete(payload: Any, cls: type) -> Any:
    """Structure into a concrete dataclass without re-entering tagged-union hooks."""
    return make_dict_structure_fn(cls, converter)(payload, cls)


def structure_feature(obj: Any, _type: type) -> Feature:
    tag, payload = _require_single_tag(obj, "feature")
    try:
        cls = FEATURE_REGISTRY[tag]
    except KeyError as exc:
        known = ", ".join(sorted(FEATURE_REGISTRY)) or "(none)"
        raise ValueError(f"unknown feature {tag!r}; registered: {known}") from exc

    if cls.__feature_scalar__ and not isinstance(payload, dict):
        field_name = fields(cls)[0].name
        return cls(**{field_name: payload})
    return _structure_concrete(payload, cls)


def unstructure_feature(obj: Feature) -> dict[str, Any]:
    cls = type(obj)
    if cls.__feature_scalar__:
        payload: Any = getattr(obj, fields(cls)[0].name)
    else:
        # Bypass tagged-union unstructure hooks (would recurse on Feature subclasses).
        payload = make_dict_unstructure_fn(cls, converter)(obj)
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
    """Emit the explicit ``{type, input}`` form used in the bible."""
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


@dataclass
class PuzzleSpec:
    cache: dict[str, Feature]
    input: Feature
    skeleton: list[Transformation]

    def validate(self) -> None:
        """Validate wiring, feature-family matches, and that every value is used."""
        validate_spec(self)


converter.register_structure_hook(PuzzleSpec, make_dict_structure_fn(PuzzleSpec, converter))
converter.register_unstructure_hook(PuzzleSpec, make_dict_unstructure_fn(PuzzleSpec, converter))

PuzzleSpecBible = dict[str, PuzzleSpec]


def _wire_family(spec: PuzzleSpec, wire: WireRef, step_index: int) -> str:
    """Resolve the feature family carried by ``wire`` as seen from skeleton step ``step_index``."""
    if isinstance(wire, str):
        if wire not in spec.cache:
            raise SpecError(f"step {step_index}: unknown cache key {wire!r}")
        return type(spec.cache[wire]).__feature_family__

    if isinstance(wire, int) and not isinstance(wire, bool):
        if wire == 0:
            return type(spec.input).__feature_family__
        if wire < 0:
            raise SpecError(f"step {step_index}: invalid wire ref {wire}")
        src = wire - 1
        if src >= step_index:
            raise SpecError(
                f"step {step_index}: wire {wire} refers to step {src} which is not yet available"
            )
        return type(spec.skeleton[src]).output_feature

    raise SpecError(f"step {step_index}: wire ref must be str or int, got {wire!r}")


def validate_spec(spec: PuzzleSpec) -> None:
    """Check arity, feature-family matches, usage, and final object output."""
    if not spec.skeleton:
        raise SpecError("skeleton must contain at least one transformation")

    used_cache: set[str] = set()
    used_input = False
    used_steps: set[int] = set()

    for step_index, step in enumerate(spec.skeleton):
        cls = type(step)
        name = cls.__transformation_name__
        try:
            cls.check_arity(len(step.inputs))
        except ValueError as exc:
            raise SpecError(f"step {step_index} ({name}): {exc}") from exc

        for slot, wire in enumerate(step.inputs):
            expected = cls.expected_input_family(slot)
            actual = _wire_family(spec, wire, step_index)
            if actual != expected:
                raise SpecError(
                    f"step {step_index} ({name}) slot {slot}: expected feature family "
                    f"{expected!r}, got {actual!r} from wire {wire!r}"
                )

            if isinstance(wire, str):
                used_cache.add(wire)
            elif wire == 0:
                used_input = True
            else:
                used_steps.add(wire - 1)

    unused_cache = set(spec.cache) - used_cache
    if unused_cache:
        raise SpecError(f"unused cache keys: {sorted(unused_cache)}")

    if not used_input:
        raise SpecError("puzzle input is never used")

    intermediate = set(range(len(spec.skeleton) - 1))
    unused_steps = intermediate - used_steps
    if unused_steps:
        names = [type(spec.skeleton[i]).__transformation_name__ for i in sorted(unused_steps)]
        raise SpecError(f"unused transformation outputs at steps {sorted(unused_steps)} ({names})")

    final = type(spec.skeleton[-1])
    if final.output_feature != "object":
        raise SpecError(
            f"last transformation {final.__transformation_name__!r} must output feature family "
            f"'object', got {final.output_feature!r}"
        )


def structure_bible(obj: Any, *, validate: bool = True) -> PuzzleSpecBible:
    if not isinstance(obj, dict):
        raise ValueError(f"bible must be an object, got {type(obj).__name__}")
    bible = {puzzle_id: converter.structure(spec, PuzzleSpec) for puzzle_id, spec in obj.items()}
    if validate:
        for puzzle_id, spec in bible.items():
            try:
                spec.validate()
            except SpecError as exc:
                raise SpecError(f"puzzle {puzzle_id}: {exc}") from exc
    return bible


def load_bible(path: Union[str, Path], *, validate: bool = True) -> PuzzleSpecBible:
    with Path(path).open() as f:
        return structure_bible(json.load(f), validate=validate)
