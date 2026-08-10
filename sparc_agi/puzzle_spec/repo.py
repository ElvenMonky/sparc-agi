import json
from dataclasses import InitVar, dataclass, field
from pathlib import Path
from typing import ClassVar, Self, get_args, get_origin, get_type_hints

import cattrs

import sparc_agi.puzzle_spec.features  # noqa: F401
import sparc_agi.puzzle_spec.transformations  # noqa: F401
from sparc_agi.puzzle_spec.slot import FeatureSlotSpec
from sparc_agi.puzzle_spec.features.base import FeatureSpec
from sparc_agi.puzzle_spec.features.pattern import PatternSpec
from sparc_agi.puzzle_spec.features.scalar import ScalarSpec
from sparc_agi.puzzle_spec.palette import PaletteSpec
from sparc_agi.puzzle_spec.range import Range
from sparc_agi.puzzle_spec.sequence import Sequence
from sparc_agi.puzzle_spec.spec import PuzzleSpec
from sparc_agi.puzzle_spec.transformations.base import TransformationSpec

def _field_type(cls: type, name: str) -> type:
    hint = get_type_hints(cls, include_extras=True)[name]
    if isinstance(hint, InitVar):
        hint = hint.type
    args = get_args(hint)
    if args and type(None) in args:
        hint = next(arg for arg in args if arg is not type(None))
    return hint

def _is_range_type(typ: type) -> bool:
    return typ is Range or get_origin(typ) is Range

def _is_sequence_type(typ: type) -> bool:
    return isinstance(typ, type) and issubclass(typ, Sequence)

def _input_spec_structure_hook(spec_cls: type, converter: cattrs.Converter):
    def hook(value: object, typ: type) -> object:
        return spec_cls.structure(value, typ, converter)
    return hook

def _input_spec_unstructure_hook(spec_cls: type, converter: cattrs.Converter):
    def hook(inst: object) -> object:
        return spec_cls.unstructure(inst, converter)
    return hook

def _structure_feature(value: object, cls: type, converter: cattrs.Converter) -> object:
    if isinstance(cls, type) and issubclass(cls, PatternSpec):
        return PatternSpec.structure(value, cls, converter)
    if isinstance(value, cls):
        return value
    if isinstance(value, (int, list, Range)):
        return cls(value=converter.structure(value, _field_type(cls, "value")))
    if not isinstance(value, dict):
        raise ValueError(f"{cls.__name__} must be a range or object, got {value!r}")
    if not value:
        return cls()
    if set(value) <= {"x", "y"}:
        return cls(
            x=converter.structure(value["x"], _field_type(cls, "x")) if "x" in value else None,
            y=converter.structure(value["y"], _field_type(cls, "y")) if "y" in value else None,
        )
    return converter.structure_attrs_fromdict(value, cls)

def _unstructure_feature(inst: FeatureSpec, converter: cattrs.Converter) -> object:
    cls = type(inst)
    custom = cls.__dict__.get("unstructure")
    if custom is not None and custom is not FeatureSpec.unstructure:
        if isinstance(custom, classmethod):
            return custom.__func__(cls, inst, converter)
        return inst.unstructure()
    return cls.unstructure(inst, converter)

def _all_feature_types() -> set[type[FeatureSpec]]:
    types: set[type[FeatureSpec]] = set(FeatureSpec.REGISTRY.values())
    queue = list(types)
    while queue:
        cls = queue.pop()
        for sub in cls.__subclasses__():
            if issubclass(sub, FeatureSpec) and sub not in types:
                types.add(sub)
                queue.append(sub)
    return types

def _register_hooks(converter: cattrs.Converter) -> None:
    for cls in (PaletteSpec,):
        converter.register_structure_hook(cls, cls.structure)
        converter.register_unstructure_hook(cls, cls.unstructure)

    converter.register_structure_hook_func(_is_range_type, Range.structure)
    converter.register_unstructure_hook_func(_is_range_type, lambda inst: inst.unstructure())

    converter.register_structure_hook_func(_is_sequence_type, Sequence.structure)
    converter.register_unstructure_hook_func(_is_sequence_type, lambda inst: inst.unstructure())

    converter.register_structure_hook(
        TransformationSpec,
        lambda value, typ: TransformationSpec.structure_step(value, typ, converter),
    )
    converter.register_unstructure_hook(
        TransformationSpec,
        lambda inst: TransformationSpec.unstructure_step(inst),
    )

    for cls in FeatureSlotSpec.__subclasses__():
        converter.register_structure_hook(cls, _input_spec_structure_hook(cls, converter))
        converter.register_unstructure_hook(cls, _input_spec_unstructure_hook(cls, converter))

    converter.register_structure_hook_func(
        lambda t: isinstance(t, type) and issubclass(t, FeatureSpec),
        lambda value, cls: _structure_feature(value, cls, converter),
    )

    for cls in _all_feature_types():
        if issubclass(cls, ScalarSpec):
            converter.register_unstructure_hook(cls, ScalarSpec.unstructure)
        else:
            converter.register_unstructure_hook(
                cls,
                lambda inst, conv=converter: _unstructure_feature(inst, conv),
            )

def _make_converter() -> cattrs.Converter:
    converter = cattrs.Converter(omit_if_default=True)
    _register_hooks(converter)
    return converter

@dataclass
class PuzzleSpecRepository:
    converter: ClassVar[cattrs.Converter] = _make_converter()
    puzzles: dict[str, PuzzleSpec] = field(default_factory=dict)

    @classmethod
    def load(cls, path: str | Path) -> Self:
        with Path(path).open() as file:
            puzzles = json.load(file)
        if not isinstance(puzzles, dict):
            raise ValueError("puzzle repository must be a JSON object")
        if not all(isinstance(key, str) and isinstance(value, dict) for key, value in puzzles.items()):
            raise ValueError("puzzle repository entries must be named JSON objects")
        return cls(cls.converter.structure(puzzles, dict[str, PuzzleSpec]))

    def save(self, path: str | Path) -> None:
        with Path(path).open("w") as file:
            json.dump(self.converter.unstructure(self.puzzles), file, indent=2)
            file.write("\n")
