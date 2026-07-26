"""Puzzle dataclasses and cattrs converter for puzzle source documents.

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

from __future__ import annotations

import json
import random
from dataclasses import MISSING, dataclass, fields, is_dataclass
from pathlib import Path
from typing import Any, Union, get_type_hints

import cattrs
from cattrs.gen import make_dict_structure_fn, make_dict_unstructure_fn, override

from sparc_agi.features import FEATURE_REGISTRY, Feature, Size, feature_family
from sparc_agi.features.height import Height
from sparc_agi.features.range import Range
from sparc_agi.features.width import Width
from sparc_agi.transformations import TRANSFORMATION_REGISTRY, Transformation, WireRef


class SpecError(ValueError):
    """Puzzle failed structural or type validation."""

converter = cattrs.Converter()


def _is_scalar_feature_type(t: Any) -> bool:
    return (
        isinstance(t, type)
        and issubclass(t, Feature)
        and t is not Feature
        and getattr(t, "__feature_scalar__", False)
    )


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


def _scalar_value_field(cls: type[Feature]) -> str:
    value_fields = [f for f in fields(cls) if f.name not in ("source", "alias")]
    if len(value_fields) != 1:
        raise TypeError(f"{cls.__name__} must have exactly one value field")
    return value_fields[0].name


def structure_scalar_feature(obj: Any, cls: type[Feature]) -> Feature:
    """Structure a concrete scalar feature from a bare Range payload (or instance)."""
    if isinstance(obj, cls):
        return obj
    return cls(**{_scalar_value_field(cls): converter.structure(obj, Range)})


converter.register_structure_hook_func(_is_scalar_feature_type, structure_scalar_feature)


def _is_composite_feature_type(t: Any) -> bool:
    return (
        isinstance(t, type)
        and issubclass(t, Feature)
        and t is not Feature
        and not getattr(t, "__feature_scalar__", False)
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

    Source form::

        "arrangement": {
          "footprint.grid": { ... },
          "sequence": { "cycle": [0, 1, 0] }
        }

    becomes field-keyed ``footprint: { "footprint.grid": ... }, sequence: ...``
    so polymorphic ``Feature`` slots keep their kind tag.
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
        and not cls.__feature_scalar__
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

    if cls.__feature_scalar__:
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
        if isinstance(val, Feature) and type(val).__feature_scalar__:
            payload[f.name] = converter.unstructure(getattr(val, _scalar_value_field(type(val))))
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
    if cls.__feature_scalar__:
        payload: Any = converter.unstructure(getattr(obj, _scalar_value_field(cls)))
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


@dataclass
class SampleCounts:
    """How many train/test samples to instantiate for a puzzle."""

    train: int
    test: int = 0


@dataclass
class PuzzleDescription:
    """Natural-language strings for the puzzle input and transformation steps."""

    input: list[str]
    steps: list[str]


@dataclass
class GeneratedPuzzle:
    """Fully generated puzzle in ARC-compatible challenge/solution form."""

    cache: dict[str, Any]
    challenge: dict[str, list[dict[str, Any]]]
    solution: list[Any]
    steps: dict[str, list[list[Any]]]
    description: PuzzleDescription


@dataclass
class Puzzle:
    cache: dict[str, Feature]
    input: Feature
    skeleton: list[Transformation]
    samples: SampleCounts

    def validate(self) -> None:
        """Validate wiring, feature-family matches, and that every value is used."""
        validate_spec(self)

    def describe_input(self) -> str:
        """Natural-language description of the puzzle input feature tree."""
        return f"Puzzle input consists of {self.input.describe()}."

    def describe_transformations(self, outputs: list[Feature] | None = None) -> str:
        """Imperative description of each skeleton transformation step."""
        return format_transformations(self, outputs)

    def description_lists(self, outputs: list[Feature] | None = None) -> PuzzleDescription:
        """Input + step descriptions as string lists (no ``Steps:`` / numbering)."""
        results = outputs if outputs is not None else self.trace()
        if outputs is not None:
            self._assign_entry_aliases()
        step_lines: list[str] = []
        prior: list[Feature] = []
        for i, (step, out) in enumerate(zip(self.skeleton, results, strict=True), start=1):
            resolved = [self.resolve(wire, prior) for wire in step.inputs]
            step_lines.append(step.describe(resolved, out, step=i))
            prior.append(out)
        return PuzzleDescription(input=[self.describe_input()], steps=step_lines)

    def generate(self, rng: random.Random | None = None) -> GeneratedPuzzle:
        """Instantiate cache once, then per-sample inputs through the skeleton."""
        from sparc_agi.grid import to_arc_grid

        self.validate()
        rng = rng if rng is not None else random.Random()
        feature_outputs = self.trace()
        description = self.description_lists(feature_outputs)
        cache = {key: feat.instantiate(rng) for key, feat in self.cache.items()}

        def run_sample(input_value: Any) -> list[Any]:
            outputs: list[Any] = []
            for step_index, step in enumerate(self.skeleton):
                resolved = [
                    self.resolve_instance(wire, cache, input_value, outputs)
                    for wire in step.inputs
                ]
                try:
                    outputs.append(step.instantiate(resolved, step=step_index + 1))
                except Exception as exc:
                    name = type(step).__transformation_name__
                    raise SpecError(
                        f"step {step_index} ({name}) instantiate failed: {exc}"
                    ) from exc
            return outputs

        train_challenge: list[dict[str, Any]] = []
        train_steps: list[list[Any]] = []
        for _ in range(self.samples.train):
            inp = self.input.instantiate(rng)
            outs = run_sample(inp)
            train_challenge.append(
                {"input": to_arc_grid(inp), "output": to_arc_grid(outs[-1])}
            )
            train_steps.append([to_arc_grid(out) for out in outs])

        test_challenge: list[dict[str, Any]] = []
        test_steps: list[list[Any]] = []
        solution: list[Any] = []
        for _ in range(self.samples.test):
            inp = self.input.instantiate(rng)
            outs = run_sample(inp)
            test_challenge.append({"input": to_arc_grid(inp)})
            test_steps.append([to_arc_grid(out) for out in outs])
            solution.append(to_arc_grid(outs[-1]))

        return GeneratedPuzzle(
            cache=cache,
            challenge={"train": train_challenge, "test": test_challenge},
            solution=solution,
            steps={"train": train_steps, "test": test_steps},
            description=description,
        )

    def resolve(self, wire: WireRef, outputs: list[Feature]) -> Feature:
        """Resolve a wire ref against cache, puzzle input, or prior step outputs."""
        if isinstance(wire, str):
            try:
                return self.cache[wire]
            except KeyError as exc:
                raise SpecError(f"unknown cache key {wire!r}") from exc
        if isinstance(wire, int) and not isinstance(wire, bool):
            if wire == 0:
                return self.input
            src = wire - 1
            if src < 0 or src >= len(outputs):
                raise SpecError(f"wire {wire} is not available (have {len(outputs)} step output(s))")
            return outputs[src]
        raise SpecError(f"wire ref must be str or int, got {wire!r}")

    def resolve_instance(
        self,
        wire: WireRef,
        cache: dict[str, Any],
        input_value: Any,
        outputs: list[Any],
    ) -> Any:
        """Resolve a wire ref against instantiated cache / input / step outputs."""
        if isinstance(wire, str):
            try:
                return cache[wire]
            except KeyError as exc:
                raise SpecError(f"unknown cache key {wire!r}") from exc
        if isinstance(wire, int) and not isinstance(wire, bool):
            if wire == 0:
                return input_value
            src = wire - 1
            if src < 0 or src >= len(outputs):
                raise SpecError(
                    f"wire {wire} is not available (have {len(outputs)} step output(s))"
                )
            return outputs[src]
        raise SpecError(f"wire ref must be str or int, got {wire!r}")

    def _assign_entry_aliases(self) -> None:
        """Set referential aliases on puzzle input and cache features."""
        self.input.alias = f"input {self.input.kind_noun()}"
        for key, feat in self.cache.items():
            feat.alias = f"{feat.kind_noun()} from cache '{key}'"

    def trace(self) -> list[Feature]:
        """Apply each skeleton step to resolved inputs; return per-step output features."""
        self.validate()
        self._assign_entry_aliases()
        outputs: list[Feature] = []
        for step_index, step in enumerate(self.skeleton):
            resolved = [self.resolve(wire, outputs) for wire in step.inputs]
            try:
                outputs.append(step.apply(resolved, step=step_index + 1))
            except Exception as exc:
                name = type(step).__transformation_name__
                raise SpecError(f"step {step_index} ({name}) apply failed: {exc}") from exc
        return outputs





converter.register_structure_hook(Puzzle, make_dict_structure_fn(Puzzle, converter))
converter.register_unstructure_hook(Puzzle, make_dict_unstructure_fn(Puzzle, converter))

PuzzleSource = dict[str, Puzzle]


def format_transformations(puzzle: Puzzle, outputs: list[Feature] | None = None) -> str:
    """Human-readable imperative steps for ``puzzle`` (runs ``trace()`` if needed)."""
    results = outputs if outputs is not None else puzzle.trace()
    if outputs is not None:
        puzzle._assign_entry_aliases()
    lines = ["Steps:"]
    prior: list[Feature] = []
    for i, (step, out) in enumerate(zip(puzzle.skeleton, results, strict=True), start=1):
        resolved = [puzzle.resolve(wire, prior) for wire in step.inputs]
        lines.append(f"{i}. {step.describe(resolved, out, step=i)}")
        prior.append(out)
    return "\n".join(lines)


def _wire_family(puzzle: Puzzle, wire: WireRef, step_index: int) -> str:
    """Resolve the feature family carried by ``wire`` as seen from skeleton step ``step_index``."""
    if isinstance(wire, str):
        if wire not in puzzle.cache:
            raise SpecError(f"step {step_index}: unknown cache key {wire!r}")
        return type(puzzle.cache[wire]).__feature_family__

    if isinstance(wire, int) and not isinstance(wire, bool):
        if wire == 0:
            return type(puzzle.input).__feature_family__
        if wire < 0:
            raise SpecError(f"step {step_index}: invalid wire ref {wire}")
        src = wire - 1
        if src >= step_index:
            raise SpecError(
                f"step {step_index}: wire {wire} refers to step {src} which is not yet available"
            )
        return type(puzzle.skeleton[src]).output_feature

    raise SpecError(f"step {step_index}: wire ref must be str or int, got {wire!r}")


def validate_spec(puzzle: Puzzle) -> None:
    """Check arity, feature-family matches, usage, and final object output."""
    if not puzzle.skeleton:
        raise SpecError("skeleton must contain at least one transformation")

    used_cache: set[str] = set()
    used_input = False
    used_steps: set[int] = set()

    for step_index, step in enumerate(puzzle.skeleton):
        cls = type(step)
        name = cls.__transformation_name__
        try:
            cls.check_arity(len(step.inputs))
        except ValueError as exc:
            raise SpecError(f"step {step_index} ({name}): {exc}") from exc

        for slot, wire in enumerate(step.inputs):
            expected = cls.expected_input_family(slot)
            actual = _wire_family(puzzle, wire, step_index)
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

    unused_cache = set(puzzle.cache) - used_cache
    if unused_cache:
        raise SpecError(f"unused cache keys: {sorted(unused_cache)}")

    if not used_input:
        raise SpecError("puzzle input is never used")

    intermediate = set(range(len(puzzle.skeleton) - 1))
    unused_steps = intermediate - used_steps
    if unused_steps:
        names = [type(puzzle.skeleton[i]).__transformation_name__ for i in sorted(unused_steps)]
        raise SpecError(f"unused transformation outputs at steps {sorted(unused_steps)} ({names})")

    final = type(puzzle.skeleton[-1])
    if final.output_feature != "object":
        raise SpecError(
            f"last transformation {final.__transformation_name__!r} must output feature family "
            f"'object', got {final.output_feature!r}"
        )


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
