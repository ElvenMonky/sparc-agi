"""Puzzle dataclasses, validation, description, and generation."""

import random
from dataclasses import dataclass, field
from typing import Any

from sparc_agi.features import Feature
from sparc_agi.features.scalars.range import Range
from sparc_agi.transformations import Transformation, WireRef


class SpecError(ValueError):
    """Puzzle failed structural or type validation."""


@dataclass
class SampleCounts:
    """How many train/test samples to instantiate for a puzzle.

    Values are ranges (a bare int in JSON means an exact count).
    """

    train: Range
    test: Range = field(default_factory=lambda: Range(0))


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
    palette: tuple[int, ...]  # display = palette[logical] for 0..9


@dataclass
class Puzzle:
    cache: dict[str, Feature]
    input: Feature
    skeleton: list[Transformation]
    samples: SampleCounts
    # Fixed logical→display colors; remaining 0..9 are shuffled into free slots.
    palette: dict[int, int] = field(default_factory=dict)

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
            text = step.describe(resolved, out, step=i)
            if text:
                step_lines.append(text)
            prior.append(out)
        return PuzzleDescription(input=[self.describe_input()], steps=step_lines)

    def generate(self, rng: random.Random | None = None) -> GeneratedPuzzle:
        """Instantiate cache once, then per-sample inputs through the skeleton."""
        from sparc_agi.features.scalars.color import apply_palette, random_palette, use_palette
        from sparc_agi.instance_ctx import force_source_key, use_instance_cache
        from sparc_agi.grid import to_arc_grid

        self.validate()
        rng = rng if rng is not None else random.Random()
        palette = random_palette(rng, self.palette)
        feature_outputs = self.trace()
        with use_palette(palette):
            description = self.description_lists(feature_outputs)
        cache = {key: feat.instantiate(rng) for key, feat in self.cache.items()}
        source_pool = _primary_source_pool(self.input)

        def emit_grid(value: Any) -> Any:
            from sparc_agi.canvas import Geometry

            if isinstance(value, Geometry):
                value = value.to_grid()
            return apply_palette(to_arc_grid(value), palette)

        def emit_step(value: Any, feat_out: Feature) -> Any:
            """Record object grids (palette-mapped), arrangements, or scalar values."""
            family = type(feat_out).__feature_family__
            if family == "arrangement":
                payload: dict[str, Any] = {"placements": value}
                size = getattr(feat_out, "size", None)
                if size is not None:
                    wv, hv = size.width.value, size.height.value
                    if wv.lo == wv.hi and hv.lo == hv.hi:
                        payload["width"] = wv.lo
                        payload["height"] = hv.lo
                return payload
            if family == "object":
                return emit_grid(value)
            if family == "color" and isinstance(value, int) and not isinstance(value, bool):
                # Same display remap as object grids (logical → palette).
                if 0 <= value < len(palette):
                    return palette[value]
                return value
            # Scalars (orientation, …) and other non-grid outputs.
            return value

        def run_sample(input_value: Any) -> list[Any]:
            outputs: list[Any] = []
            for step_index, step in enumerate(self.skeleton):
                resolved = [
                    self.resolve_instance(wire, cache, input_value, outputs)
                    for wire in step.inputs
                ]
                feat_resolved = [
                    self.resolve(wire, feature_outputs[:step_index])
                    for wire in step.inputs
                ]
                try:
                    outputs.append(
                        step.instantiate(
                            resolved,
                            step=step_index + 1,
                            feature_inputs=feat_resolved,
                            feature_output=feature_outputs[step_index],
                        )
                    )
                except Exception as exc:
                    name = type(step).__transformation_name__
                    raise SpecError(
                        f"step {step_index} ({name}) instantiate failed: {exc}"
                    ) from exc
            return outputs

        def make_input(forced: str | None) -> Any:
            with use_instance_cache(cache), force_source_key(forced):
                return self.input.instantiate(rng)

        n_train = self.samples.train.sample(rng)
        train_forced = _cover_source_keys(source_pool, n_train, rng)
        train_challenge: list[dict[str, Any]] = []
        train_steps: list[list[Any]] = []
        for forced in train_forced:
            inp = make_input(forced)
            outs = run_sample(inp)
            train_challenge.append(
                {"input": emit_grid(inp), "output": emit_grid(outs[-1])}
            )
            train_steps.append(
                [emit_step(out, feature_outputs[i]) for i, out in enumerate(outs)]
            )

        n_test = self.samples.test.sample(rng)
        test_challenge: list[dict[str, Any]] = []
        test_steps: list[list[Any]] = []
        solution: list[Any] = []
        for _ in range(n_test):
            forced = (
                source_pool[rng.randrange(len(source_pool))] if source_pool else None
            )
            inp = make_input(forced)
            outs = run_sample(inp)
            test_challenge.append({"input": emit_grid(inp)})
            test_steps.append(
                [emit_step(out, feature_outputs[i]) for i, out in enumerate(outs)]
            )
            solution.append(emit_grid(outs[-1]))

        def emit_cache_entry(key: str, value: Any) -> Any:
            feat = self.cache[key]
            family = type(feat).__feature_family__
            if family == "object":
                return emit_grid(value)
            if family == "arrangement":
                return emit_step(value, feat)
            if family == "color" and isinstance(value, int) and not isinstance(value, bool):
                if 0 <= value < len(palette):
                    return palette[value]
                return value
            return value

        return GeneratedPuzzle(
            cache={key: emit_cache_entry(key, value) for key, value in cache.items()},
            challenge={"train": train_challenge, "test": test_challenge},
            solution=solution,
            steps={"train": train_steps, "test": test_steps},
            description=description,
            palette=palette,
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
        """Set referential aliases on puzzle input (cache stays unnamed — describe()).

        Cache entries must not be referred to as ``from cache '…'``: solvers never
        see the cache. ``Feature.refer()`` falls through to ``describe()``.
        """
        self.input.alias = f"input {self.input.kind_noun()}"
        for feat in self.cache.values():
            feat.alias = None

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


PuzzleSource = dict[str, Puzzle]


def format_transformations(puzzle: Puzzle, outputs: list[Feature] | None = None) -> str:
    """Human-readable imperative steps for ``puzzle`` (runs ``trace()`` if needed)."""
    results = outputs if outputs is not None else puzzle.trace()
    if outputs is not None:
        puzzle._assign_entry_aliases()
    lines = ["Steps:"]
    prior: list[Feature] = []
    n = 0
    for i, (step, out) in enumerate(zip(puzzle.skeleton, results, strict=True), start=1):
        resolved = [puzzle.resolve(wire, prior) for wire in step.inputs]
        text = step.describe(resolved, out, step=i)
        if text:
            n += 1
            lines.append(f"{n}. {text}")
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


def _iter_features(feat: Feature):
    """Yield ``feat`` and nested feature values (pools, child traits)."""
    from dataclasses import fields as dc_fields

    yield feat
    for f in dc_fields(type(feat)):
        if f.name in ("source", "alias", "geometry_index"):
            continue
        val = getattr(feat, f.name)
        if isinstance(val, Feature):
            yield from _iter_features(val)
        elif isinstance(val, list):
            for item in val:
                if isinstance(item, Feature):
                    yield from _iter_features(item)


def _collect_source_refs(feat: Feature) -> set[str]:
    """Cache keys listed in any ``source`` donor list under ``feat``."""
    refs: set[str] = set()
    for node in _iter_features(feat):
        keys = getattr(node, "source", None)
        if isinstance(keys, list) and keys and all(isinstance(k, str) for k in keys):
            refs.update(keys)
    return refs


def _primary_source_pool(feat: Feature) -> list[str]:
    """First non-empty ``source`` list in the feature tree (coverage target)."""
    for node in _iter_features(feat):
        keys = getattr(node, "source", None)
        if isinstance(keys, list) and keys and all(isinstance(k, str) for k in keys):
            return list(keys)
    return []


def _cover_source_keys(
    pool: list[str], n: int, rng: random.Random
) -> list[str | None]:
    """Build ``n`` picks that include every key in ``pool`` at least once."""
    if not pool:
        return [None] * n
    if n < len(pool):
        raise SpecError(
            f"need at least {len(pool)} train samples to cover source keys "
            f"{pool}, got {n}"
        )
    picks: list[str | None] = list(pool)
    while len(picks) < n:
        picks.append(pool[rng.randrange(len(pool))])
    rng.shuffle(picks)
    return picks


def validate_spec(puzzle: Puzzle) -> None:
    """Check arity, feature-family matches, usage, and final object output."""
    if not puzzle.skeleton:
        raise SpecError("skeleton must contain at least one transformation")

    for logical, display in puzzle.palette.items():
        if not (isinstance(logical, int) and not isinstance(logical, bool) and 0 <= logical <= 9):
            raise SpecError(f"palette key must be int 0..9, got {logical!r}")
        if not (isinstance(display, int) and not isinstance(display, bool) and 0 <= display <= 9):
            raise SpecError(f"palette[{logical}] must be int 0..9, got {display!r}")
    if len(set(puzzle.palette.values())) != len(puzzle.palette):
        raise SpecError(f"palette display colors must be unique, got {puzzle.palette}")

    source_refs = _collect_source_refs(puzzle.input)
    for key in sorted(source_refs):
        if key not in puzzle.cache:
            raise SpecError(f"input source key {key!r} is not in cache")
        if type(puzzle.cache[key]).__feature_family__ != "object":
            raise SpecError(
                f"input source key {key!r} must be an object, "
                f"got {type(puzzle.cache[key]).__feature_name__}"
            )

    source_pool = _primary_source_pool(puzzle.input)
    if source_pool and puzzle.samples.train.lo < len(source_pool):
        raise SpecError(
            f"samples.train must be at least {len(source_pool)} to cover source "
            f"keys {source_pool}, got lo={puzzle.samples.train.lo}"
        )

    used_cache: set[str] = set(source_refs)
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
