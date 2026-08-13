import random
from dataclasses import dataclass, field, fields
from typing import Any, Self, get_origin

import cattrs

from sparc_agi.puzzle.features.base import LinearPattern, Pattern
from sparc_agi.puzzle.puzzle import Puzzle
from sparc_agi.puzzle_spec.features.base import FeatureSpec, register_feature, trait
from sparc_agi.consts import MAX_POOL
from sparc_agi.puzzle_spec.features.scalar import DirectionSpec
from sparc_agi.puzzle_spec.range import Range
from sparc_agi.puzzle_spec.sequence import Sequence
from sparc_agi.puzzle_spec.slot import FeatureSlotSpec

_LINEAR_DIRECTION = (
    "left-to-right",
    "top-left-to-bottom-right",
    "top-to-bottom",
    "top-right-to-bottom-left",
    "right-to-left",
    "bottom-right-to-top-left",
    "bottom-to-top",
    "bottom-left-to-top-right",
)

@register_feature("pattern")
@dataclass
class PatternSpec(FeatureSpec):
    prefix: list[int] = field(default_factory=list)
    pattern: list[int] = field(default_factory=list)

    @classmethod
    def structure(cls, value: Any, typ: type, converter: cattrs.Converter) -> Self:
        concrete = get_origin(typ) or typ
        if isinstance(value, concrete):
            return value
        if not isinstance(value, dict):
            raise ValueError(f"pattern must be an object, got {value!r}")
        seq = Sequence.structure(value, Sequence[-1, MAX_POOL])
        kwargs: dict[str, Any] = {
            "prefix": list(seq.prefix),
            "pattern": list(seq.pattern),
        }
        for dc_field in fields(concrete):
            if dc_field.name in kwargs:
                continue
            if dc_field.name not in value:
                continue
            kwargs[dc_field.name] = converter.structure(value[dc_field.name], dc_field.type)
        return concrete(**kwargs)

    def instantiate(self, rng: random.Random) -> Pattern:
        del rng
        return Pattern(spec=self)

    def describe(self, ctx: Puzzle, instance: Pattern | None = None) -> str:
        del ctx, instance
        parts: list[str] = []
        if self.prefix:
            parts.append(f"{self.prefix} prefix")
        if self.pattern:
            parts.append(f"{self.pattern} pattern")
        if not parts:
            return ""
        return " and ".join(parts)

@dataclass
class PatternSlotSpec(FeatureSlotSpec[PatternSpec]):
    pass

@register_feature("pattern.linear")
@dataclass
class LinearPatternSpec(PatternSpec):
    direction: DirectionSpec = trait(default_factory=lambda: DirectionSpec(Range(0)))

    def instantiate(self, rng: random.Random) -> LinearPattern:
        return LinearPattern(
            spec=self,
            direction=self.direction.instantiate(rng),
        )

    def describe(self, ctx: Puzzle, instance: LinearPattern | None = None) -> str:
        body = super().describe(ctx, instance)
        if not body:
            return ""
        direction = self.direction.resolved_value(instance.direction if instance else None)
        if direction is None:
            return body
        return f"{_LINEAR_DIRECTION[direction]} {body}"
