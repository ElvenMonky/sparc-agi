"""Puzzle dataclasses, validation, description, and generation."""

import random
from dataclasses import dataclass
from typing import Any

from sparc_agi.features import Feature
from sparc_agi.transformations import Transformation, WireRef


class SpecError(ValueError):
    """Puzzle failed structural or type validation."""


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
            text = step.describe(resolved, out, step=i)
            if text:
                step_lines.append(text)
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
                        )
                    )
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
