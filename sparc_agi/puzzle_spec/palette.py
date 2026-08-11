import random
from dataclasses import dataclass, field
from typing import Any, Self

from sparc_agi.consts import MAX_COLOR

from sparc_agi.puzzle.palette import Palette

@dataclass(frozen=True)
class PaletteSpec:
    fixed: dict[int, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        values: set[int] = set()
        for key, value in self.fixed.items():
            if not isinstance(key, int) or not 0 <= key <= MAX_COLOR:
                raise ValueError(f"palette key must be an integer in 0..{MAX_COLOR}, got {key!r}")
            if not isinstance(value, int) or not 0 <= value <= MAX_COLOR:
                raise ValueError(f"palette value must be an integer in 0..{MAX_COLOR}, got {value!r}")
            if value in values:
                raise ValueError(f"palette colors must be unique, got {dict(self.fixed)!r}")
            values.add(value)

    @classmethod
    def structure(cls, value: Any, _: type) -> Self:
        if not isinstance(value, dict):
            raise ValueError(f"palette must be an object, got {value!r}")
        fixed: dict[int, int] = {}
        for key, color in value.items():
            try:
                logical = int(key)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"palette key must be an integer, got {key!r}") from exc
            if isinstance(color, bool) or not isinstance(color, int):
                raise ValueError(f"palette value must be an integer, got {color!r}")
            fixed[logical] = color
        return cls(fixed)

    def unstructure(self) -> dict[str, int]:
        return {str(key): value for key, value in self.fixed.items()}

    def instantiate(self, rng: random.Random) -> Palette:
        free = [color for color in range(MAX_COLOR + 1) if color not in self.fixed.values()]
        rng.shuffle(free)
        return tuple(
            self.fixed[key] if key in self.fixed else free.pop()
            for key in range(MAX_COLOR + 1)
        )
