import random
from dataclasses import dataclass, field, fields
from typing import Any, get_args, get_origin

from sparc_agi.puzzle.features.base import Feature
from sparc_agi.puzzle.puzzle import Puzzle, PuzzleDescription
from sparc_agi.puzzle.slot import PuzzleCacheSlot
from sparc_agi.puzzle_spec.features.base import FeatureSpec, with_article
from sparc_agi.puzzle_spec.features.filter import FilterSpec
from sparc_agi.puzzle_spec.features.object import ObjectSpec
from sparc_agi.puzzle_spec.palette import PaletteSpec
from sparc_agi.puzzle_spec.range import Range
from sparc_agi.puzzle_spec.slot import CacheItemSpec, FeatureSlotSpec
from sparc_agi.puzzle_spec.transformations.base import TransformationSpec
from sparc_agi.puzzle_spec.validate import (
    validate_linked_mappings,
    validate_step_outputs,
    validate_step_wires,
)
from sparc_agi.puzzle_spec.wire import WireRef, WireValue

@dataclass
class InputSpec(FeatureSlotSpec[ObjectSpec]):
    pass

@dataclass
class SamplesSpec:
    train: Range[2, 5]
    test: Range[1, 3]

@dataclass
class PuzzleSpec:
    input: InputSpec
    samples: SamplesSpec
    steps: list[TransformationSpec]
    cache: dict[str, CacheItemSpec] = field(default_factory=dict)
    palette: PaletteSpec = field(default_factory=PaletteSpec)
    step_outputs: list[FeatureSpec] = field(init=False, default_factory=list)

    def resolve_wire_value(self, step_index: int, wire: WireValue) -> FeatureSpec:
        if isinstance(wire, str):
            item = self.cache.get(wire)
            if item is None:
                raise ValueError(f"unknown cache key {wire!r}")
            return item.value
        if isinstance(wire, int):
            if wire < 0 or wire > step_index:
                raise ValueError(f"invalid wire index {wire}")
            return self.step_outputs[wire]
        raise ValueError(f"invalid wire value {wire!r}")

    def get_input(self, step: TransformationSpec, step_index: int) -> dict[str, Any]:
        input: dict[str, Any] = {}
        for dc_field in fields(type(step)):
            if WireRef.spec_type(dc_field.type) is None:
                continue
            value = getattr(step, dc_field.name)
            if get_origin(dc_field.type) is list:
                input[dc_field.name] = [
                    self.resolve_wire_value(step_index, wire) for wire in value
                ]
            elif value is None:
                input[dc_field.name] = None
                if WireRef.spec_type(dc_field.type) is FilterSpec:
                    input[dc_field.name] = FilterSpec()
            else:
                input[dc_field.name] = self.resolve_wire_value(step_index, value)
        return input

    def get_describe_input(
        self,
        step: TransformationSpec,
        step_index: int,
        ctx: Puzzle,
    ) -> dict[str, FeatureSpec | Feature | list[FeatureSpec]]:
        input = self.get_input(step, step_index)
        for dc_field in fields(type(step)):
            if WireRef.spec_type(dc_field.type) is None:
                continue
            if get_origin(dc_field.type) is list:
                continue
            wire = getattr(step, dc_field.name)
            if not isinstance(wire, str):
                continue
            slot = ctx.cache.get(wire)
            if slot is None:
                raise ValueError(f"unknown cache key {wire!r}")
            if isinstance(slot, PuzzleCacheSlot):
                input[dc_field.name] = slot.value
        return input

    def __post_init__(self) -> None:
        self.step_outputs = [self.input.value]
        self.step_outputs[0].alias = f"input {self.step_outputs[0].kind_noun()}"
        for step_index, step in enumerate(self.steps):
            step_cls = type(step)
            input = self.get_input(step, step_index)
            output = step_cls.trace(**input)
            if output is None:
                raise ValueError(f"step {step_index} {step_cls.tag()}: trace returned None")
            declared = step_cls.output_type()
            if not isinstance(output, declared):
                raise ValueError(
                    f"step {step_index} {step_cls.tag()}: trace returned "
                    f"{type(output).tag()}, expected {declared.tag()}"
                )
            output.alias = f"{step.alias_stem(**input)}{output.kind_noun()} from step {step_index + 1}"
            self.step_outputs.append(output)
        validate_linked_mappings(self)
        validate_step_wires(self)
        validate_step_outputs(self)

    def instantiate(self, rng: random.Random | None = None) -> Puzzle:
        rng = rng or random.Random()
        palette = self.palette.instantiate(rng)
        cache = {key: item.instantiate(rng) for key, item in self.cache.items()}
        ctx = Puzzle(spec=self, palette=palette, cache=cache)
        body = self.input.value.describe(ctx)
        if not body.startswith(("a ", "an ")):
            body = with_article(body)
        steps: list[str] = []
        for step_index, step in enumerate(self.steps):
            if text := step.describe(ctx, **self.get_describe_input(step, step_index, ctx)):
                steps.append(text)
        ctx.description = PuzzleDescription(
            input=f"Puzzle input consists of {body}.",
            steps=tuple(steps),
        )
        return ctx
