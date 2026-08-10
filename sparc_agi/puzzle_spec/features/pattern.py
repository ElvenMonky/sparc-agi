from dataclasses import dataclass, field, fields
from typing import Any, Self, get_origin

import cattrs

from sparc_agi.puzzle_spec.features.base import FeatureSpec, register_feature, trait
from sparc_agi.consts import MAX_POOL
from sparc_agi.puzzle_spec.features.scalar import OrientationSpec
from sparc_agi.puzzle_spec.range import Range
from sparc_agi.puzzle_spec.sequence import Sequence
from sparc_agi.puzzle_spec.slot import FeatureSlotSpec

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

@dataclass
class PatternSlotSpec(FeatureSlotSpec[PatternSpec]):
    pass

@register_feature("pattern.linear")
@dataclass
class LinearPatternSpec(PatternSpec):
    direction: OrientationSpec = trait(default_factory=lambda: OrientationSpec(Range(0)))
