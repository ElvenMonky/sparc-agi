import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import ClassVar, Self

import cattrs

from sparc_agi.puzzle_spec.cache import CacheItem
from sparc_agi.puzzle_spec.features.base import FeatureSpec
from sparc_agi.puzzle_spec.palette import PaletteSpec
from sparc_agi.puzzle_spec.range import Range
from sparc_agi.puzzle_spec.spec import PuzzleSpec

@dataclass
class PuzzleSpecRepository:
    converter: ClassVar[cattrs.Converter] = cattrs.Converter(omit_if_default=True)
    converter.register_structure_hook(Range, Range.structure)
    converter.register_unstructure_hook(Range, Range.unstructure)
    converter.register_structure_hook(PaletteSpec, PaletteSpec.structure)
    converter.register_unstructure_hook(PaletteSpec, PaletteSpec.unstructure)
    converter.register_structure_hook(CacheItem, CacheItem.structure)
    converter.register_unstructure_hook(CacheItem, CacheItem.unstructure)
    converter.register_structure_hook_func(
        lambda t: isinstance(t, type) and issubclass(t, FeatureSpec),
        FeatureSpec.structure,
    )
    converter.register_unstructure_hook_func(
        lambda t: isinstance(t, type) and issubclass(t, FeatureSpec),
        FeatureSpec.unstructure,
    )
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
