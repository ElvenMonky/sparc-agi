import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import ClassVar, Self

import cattrs

import sparc_agi.puzzle_spec.features  # noqa: F401
from sparc_agi.puzzle_spec.cache import InputSpec
from sparc_agi.puzzle_spec.features.base import FeatureSpec
from sparc_agi.puzzle_spec.palette import PaletteSpec
from sparc_agi.puzzle_spec.range import Range
from sparc_agi.puzzle_spec.spec import PuzzleSpec

def _subclasses(cls: type) -> set[type]:
    types = {cls}
    for sub in cls.__subclasses__():
        types |= _subclasses(sub)
    return types

def _input_spec_structure_hook(spec_cls: type, converter: cattrs.Converter):
    def hook(value: object, typ: type) -> object:
        return spec_cls.structure(value, typ, converter)
    return hook

def _input_spec_unstructure_hook(spec_cls: type, converter: cattrs.Converter):
    def hook(inst: object) -> object:
        return spec_cls.unstructure(inst, converter)
    return hook

def _register_hooks(converter: cattrs.Converter) -> None:
    for cls in (Range, PaletteSpec):
        converter.register_structure_hook(cls, cls.structure)
        converter.register_unstructure_hook(cls, cls.unstructure)

    for cls in _subclasses(InputSpec):
        converter.register_structure_hook(cls, _input_spec_structure_hook(cls, converter))
        converter.register_unstructure_hook(cls, _input_spec_unstructure_hook(cls, converter))

    for cls in set(FeatureSpec.REGISTRY.values()):
        if "structure" in cls.__dict__:
            converter.register_structure_hook(cls, cls.structure)
        if "unstructure" in cls.__dict__:
            converter.register_unstructure_hook(cls, cls.unstructure)

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
